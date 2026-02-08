#!/usr/bin/env ts-node
/**
 * Reduce durability events into weekly trend metrics.
 */

import * as fs from 'node:fs';
import * as path from 'node:path';
import { validateAgentEvent } from '../src/observability/agent-event.schema.ts';
import type { AgentEvent } from '../src/observability/agent-event.schema.ts';

const EVENTS_DIR = 'artifacts/events';
const OUTPUT_PATH = 'artifacts/reports/weekly-durability.json';
const FALLBACK_TIME = new Date(0);
const STRICT = (process.env.WEEKLY_STRICT ?? 'false').toLowerCase() === 'true';

const MS_DAY = 24 * 60 * 60 * 1000;

type TrendWindow = {
  window_days: number;
  samples: number;
  average_p95_ms: number;
  latest_p95_ms: number | null;
  slope_ms_per_day: number;
};

function parseTimestamp(value: string): number {
  const time = Date.parse(value);
  return Number.isFinite(time) ? time : 0;
}

function ensureDir(filePath: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function readEvents(dir: string): AgentEvent[] {
  const absDir = path.resolve(process.cwd(), dir);
  if (!fs.existsSync(absDir)) {
    if (STRICT) {
      throw new Error(`Events directory not found: ${absDir}`);
    }
    console.warn(`⚠️ Events directory not found: ${absDir}`);
    return [];
  }

  const files = fs.readdirSync(absDir).filter(f => f.endsWith('.ndjson'));
  if (files.length === 0) {
    if (STRICT) {
      throw new Error(`No NDJSON event files found in ${absDir}`);
    }
    console.warn(`⚠️ No NDJSON event files found in ${absDir}`);
    return [];
  }

  const events: AgentEvent[] = [];
  const errors: string[] = [];

  for (const file of files) {
    const fullPath = path.join(absDir, file);
    const content = fs.readFileSync(fullPath, 'utf8');
    const lines = content.split(/\r?\n/).filter(Boolean);

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      try {
        const parsed = JSON.parse(line) as AgentEvent;
        const validation = validateAgentEvent(parsed);
        if (!validation.valid) {
          errors.push(`${file}:${i + 1} ${validation.errors.join('; ')}`);
          continue;
        }
        events.push(parsed);
      } catch (error) {
        errors.push(`${file}:${i + 1} JSON parse error: ${String(error)}`);
      }
    }
  }

  if (errors.length > 0) {
    const message = `Invalid events detected:\n${errors.join('\n')}`;
    if (STRICT) {
      throw new Error(message);
    }
    console.warn(message);
  }

  return events;
}

function filterByWindow(events: AgentEvent[], days: number, referenceTime: number): AgentEvent[] {
  const cutoff = referenceTime - days * MS_DAY;
  return events.filter(event => parseTimestamp(event.timestamp) >= cutoff);
}

function mean(values: number[]): number {
  if (values.length === 0) return 0;
  return values.reduce((sum, v) => sum + v, 0) / values.length;
}

function linearSlope(points: Array<{ x: number; y: number }>): number {
  if (points.length < 2) return 0;
  const avgX = mean(points.map(p => p.x));
  const avgY = mean(points.map(p => p.y));
  let numerator = 0;
  let denominator = 0;
  for (const p of points) {
    const dx = p.x - avgX;
    numerator += dx * (p.y - avgY);
    denominator += dx * dx;
  }
  if (denominator === 0) return 0;
  return numerator / denominator;
}

function buildP95Trend(events: AgentEvent[], days: number, referenceTime: number): TrendWindow {
  const benchmarks = events
    .filter(event => event.event_type === 'benchmark_run')
    .map(event => {
      const payload = event.payload as any;
      return {
        timestamp: parseTimestamp(event.timestamp),
        p95: Number(payload?.p95_ms)
      };
    })
    .filter(entry => Number.isFinite(entry.timestamp) && Number.isFinite(entry.p95));

  const points = benchmarks.map(entry => ({
    x: (entry.timestamp - (referenceTime - days * MS_DAY)) / MS_DAY,
    y: entry.p95
  }));

  const slope = linearSlope(points);
  const avg = mean(benchmarks.map(entry => entry.p95));
  const latest = benchmarks.length ? benchmarks[benchmarks.length - 1].p95 : null;

  return {
    window_days: days,
    samples: benchmarks.length,
    average_p95_ms: Math.round(avg),
    latest_p95_ms: latest == null ? null : Math.round(latest),
    slope_ms_per_day: Math.round(slope * 100) / 100
  };
}

function computePassRates(events: AgentEvent[]): Record<string, { pass: number; fail: number; pass_rate: number }> {
  const summary: Record<string, { pass: number; fail: number; pass_rate: number }> = {};
  for (const event of events) {
    if (!summary[event.event_type]) {
      summary[event.event_type] = { pass: 0, fail: 0, pass_rate: 0 };
    }
    summary[event.event_type][event.status] += 1;
  }

  for (const key of Object.keys(summary)) {
    const total = summary[key].pass + summary[key].fail;
    summary[key].pass_rate = total === 0 ? 0 : Math.round((summary[key].pass / total) * 1000) / 10;
  }

  return summary;
}

function computeBudgetBreaches(events: AgentEvent[]): {
  breach_count: number;
  max_regression_pct: number;
  avg_regression_pct: number;
} {
  const breaches = events
    .filter(event => event.event_type === 'budget_gate' && event.status === 'fail')
    .map(event => {
      const payload = event.payload as any;
      return Number(payload?.regression_pct ?? 0);
    })
    .filter(value => Number.isFinite(value));

  return {
    breach_count: breaches.length,
    max_regression_pct: breaches.length ? Math.max(...breaches) : 0,
    avg_regression_pct: breaches.length ? Math.round(mean(breaches) * 100) / 100 : 0
  };
}

function computeTopFailures(events: AgentEvent[], limit: number): Array<{ reason: string; count: number }> {
  const failures = events.filter(event => event.status === 'fail');
  const counts: Record<string, number> = {};
  for (const event of failures) {
    const payload = event.payload as Record<string, unknown>;
    const reason = typeof payload?.failure_reason === 'string' && payload.failure_reason.trim()
      ? payload.failure_reason
      : event.event_type;
    counts[reason] = (counts[reason] || 0) + 1;
  }

  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([reason, count]) => ({ reason, count }));
}

function computeMttr(events: AgentEvent[]): Record<string, { samples: number; average_hours: number; max_hours: number }> {
  const byType: Record<string, AgentEvent[]> = {};
  for (const event of events) {
    if (!byType[event.event_type]) byType[event.event_type] = [];
    byType[event.event_type].push(event);
  }

  const result: Record<string, { samples: number; average_hours: number; max_hours: number }> = {};

  for (const [eventType, list] of Object.entries(byType)) {
    const sorted = [...list].sort((a, b) => parseTimestamp(a.timestamp) - parseTimestamp(b.timestamp));
    let openFail: number | null = null;
    const durations: number[] = [];

    for (const event of sorted) {
      const time = parseTimestamp(event.timestamp);
      if (event.status === 'fail' && openFail == null) {
        openFail = time;
      }
      if (event.status === 'pass' && openFail != null) {
        durations.push(time - openFail);
        openFail = null;
      }
    }

    const averageHours = durations.length ? mean(durations) / (60 * 60 * 1000) : 0;
    const maxHours = durations.length ? Math.max(...durations) / (60 * 60 * 1000) : 0;

    result[eventType] = {
      samples: durations.length,
      average_hours: Math.round(averageHours * 100) / 100,
      max_hours: Math.round(maxHours * 100) / 100
    };
  }

  return result;
}

function computeDriftHotspots(events: AgentEvent[]): Array<{ tool: string; count: number }> {
  const counts: Record<string, number> = {};
  const schemaFailures = events.filter(event => event.event_type === 'schema_contract_check' && event.status === 'fail');

  for (const event of schemaFailures) {
    const payload = event.payload as any;
    const tools: string[] = [
      ...(payload?.drifted_tools ?? []),
      ...(payload?.missing_tools ?? []),
      ...(payload?.orphaned_tools ?? [])
    ];

    for (const tool of tools) {
      if (!tool) continue;
      counts[tool] = (counts[tool] || 0) + 1;
    }
  }

  return Object.entries(counts)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([tool, count]) => ({ tool, count }));
}

function main(): void {
  const allEvents = readEvents(EVENTS_DIR);
  const latestEventTime = allEvents.length
    ? Math.max(...allEvents.map(event => parseTimestamp(event.timestamp)))
    : FALLBACK_TIME.getTime();
  const events7d = filterByWindow(allEvents, 7, latestEventTime);
  const events30d = filterByWindow(allEvents, 30, latestEventTime);

  const summary = {
    generated_at: new Date(latestEventTime).toISOString(),
    window_days: 7,
    total_events_7d: events7d.length,
    total_events_30d: events30d.length,
    gate_pass_rates: computePassRates(events7d),
    p95_trend_7d: buildP95Trend(events7d, 7, latestEventTime),
    p95_trend_30d: buildP95Trend(events30d, 30, latestEventTime),
    regression_breaches_30d: computeBudgetBreaches(events30d),
    top_failure_reasons: computeTopFailures(events30d, 3),
    mttr_hours_by_gate: computeMttr(events30d),
    drift_hotspots_by_tool: computeDriftHotspots(events30d)
  };

  ensureDir(OUTPUT_PATH);
  fs.writeFileSync(OUTPUT_PATH, JSON.stringify(summary, null, 2));

  console.log('✅ Weekly durability summary generated');
  console.log(`   Output: ${OUTPUT_PATH}`);
}

main();
