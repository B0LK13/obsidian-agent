#!/usr/bin/env ts-node
/**
 * Reduce durability events into a summary JSON artifact.
 */

import * as fs from 'node:fs';
import * as path from 'node:path';
import { validateAgentEvent } from '../src/observability/agent-event.schema.ts';
import type { AgentEvent } from '../src/observability/agent-event.schema.ts';

const EVENTS_DIR = 'artifacts/events';
const SUMMARY_PATH = 'artifacts/latest/observability-summary.json';
const P95_TREND_LIMIT = Number(process.env.OBSERVABILITY_P95_TREND_N ?? 10);

function readNdjsonFiles(dir: string): AgentEvent[] {
  const absDir = path.resolve(process.cwd(), dir);
  if (!fs.existsSync(absDir)) {
    throw new Error(`Events directory not found: ${absDir}`);
  }

  const files = fs.readdirSync(absDir).filter(f => f.endsWith('.ndjson'));
  if (files.length === 0) {
    throw new Error(`No NDJSON event files found in ${absDir}`);
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
    throw new Error(`Invalid events detected:\n${errors.join('\n')}`);
  }

  return events;
}

function ensureDir(filePath: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function extractFailureReason(event: AgentEvent): string {
  const payload = event.payload as Record<string, unknown>;
  const reason = payload?.failure_reason;
  if (typeof reason === 'string' && reason.trim().length > 0) {
    return reason;
  }
  return event.event_type;
}

function main(): void {
  const events = readNdjsonFiles(EVENTS_DIR);

  const eventsByType: Record<string, number> = {};
  const passFailByType: Record<string, { pass: number; fail: number }> = {};
  const failureReasons: Record<string, number> = {};

  for (const event of events) {
    eventsByType[event.event_type] = (eventsByType[event.event_type] || 0) + 1;
    if (!passFailByType[event.event_type]) {
      passFailByType[event.event_type] = { pass: 0, fail: 0 };
    }
    passFailByType[event.event_type][event.status] += 1;

    if (event.status === 'fail') {
      const reason = extractFailureReason(event);
      failureReasons[reason] = (failureReasons[reason] || 0) + 1;
    }
  }

  const benchmarkRuns = events
    .filter(e => e.event_type === 'benchmark_run')
    .sort((a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime());

  const p95Trend = benchmarkRuns
    .slice(-P95_TREND_LIMIT)
    .map(event => {
      const payload = event.payload as any;
      return {
        timestamp: event.timestamp,
        p95_ms: payload.p95_ms,
        mode: payload.mode,
        status: event.status,
        correlation_id: event.correlation_id
      };
    });

  const topFailureReasons = Object.entries(failureReasons)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5)
    .map(([reason, count]) => ({ reason, count }));

  const summary = {
    generated_at: new Date().toISOString(),
    total_events: events.length,
    events_by_type: eventsByType,
    pass_fail_by_type: passFailByType,
    p95_trend: p95Trend,
    top_failure_reasons: topFailureReasons
  };

  ensureDir(SUMMARY_PATH);
  fs.writeFileSync(SUMMARY_PATH, JSON.stringify(summary, null, 2));

  console.log('✅ Observability summary generated');
  console.log(`   Output: ${SUMMARY_PATH}`);
}

main();
