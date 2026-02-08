#!/usr/bin/env ts-node
/**
 * Generate a weekly durability report from summary JSON.
 */

import * as fs from 'node:fs';
import * as path from 'node:path';

const SUMMARY_PATH = 'artifacts/reports/weekly-durability.json';
const OUTPUT_PATH = 'artifacts/reports/weekly-durability.md';

function ensureDir(filePath: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

function formatHours(value: number): string {
  return `${value.toFixed(2)}h`;
}

function main(): void {
  const abs = path.resolve(process.cwd(), SUMMARY_PATH);
  if (!fs.existsSync(abs)) {
    throw new Error(`Weekly summary not found at ${abs}`);
  }

  const summary = JSON.parse(fs.readFileSync(abs, 'utf8')) as any;

  const gateRows = Object.entries(summary.gate_pass_rates || {}).map(([gate, stats]: any) => {
    return `| ${gate} | ${stats.pass} | ${stats.fail} | ${formatPercent(stats.pass_rate)} |`;
  });

  const failureRows = (summary.top_failure_reasons || []).map((entry: any) => {
    return `- ${entry.reason} (${entry.count})`;
  });

  const driftRows = (summary.drift_hotspots_by_tool || []).map((entry: any) => {
    return `- ${entry.tool} (${entry.count})`;
  });

  const mttrRows = Object.entries(summary.mttr_hours_by_gate || {}).map(([gate, stats]: any) => {
    return `| ${gate} | ${stats.samples} | ${formatHours(stats.average_hours)} | ${formatHours(stats.max_hours)} |`;
  });

  const report = `# Weekly Durability Report

**Generated:** ${summary.generated_at}
**Window:** Last ${summary.window_days} days
**Events (7d / 30d):** ${summary.total_events_7d} / ${summary.total_events_30d}

## SLA Compliance (Budget Gate)

- Breaches (30d): ${summary.regression_breaches_30d?.breach_count ?? 0}
- Max regression: ${summary.regression_breaches_30d?.max_regression_pct ?? 0}%
- Avg regression: ${summary.regression_breaches_30d?.avg_regression_pct ?? 0}%

## Gate Pass Rates (7d)

| Gate | Pass | Fail | Pass Rate |
| --- | --- | --- | --- |
${gateRows.join('\n') || '| n/a | 0 | 0 | 0.0% |'}

## P95 Trend

- 7d average: ${summary.p95_trend_7d?.average_p95_ms ?? 0}ms
- 7d slope: ${summary.p95_trend_7d?.slope_ms_per_day ?? 0} ms/day
- 30d average: ${summary.p95_trend_30d?.average_p95_ms ?? 0}ms
- 30d slope: ${summary.p95_trend_30d?.slope_ms_per_day ?? 0} ms/day

## Top Failure Causes (30d)

${failureRows.join('\n') || '- None'}

## Drift Hotspots by Tool (30d)

${driftRows.join('\n') || '- None'}

## MTTR by Gate (30d)

| Gate | Samples | Avg MTTR | Max MTTR |
| --- | --- | --- | --- |
${mttrRows.join('\n') || '| n/a | 0 | 0.00h | 0.00h |'}
`;

  ensureDir(OUTPUT_PATH);
  fs.writeFileSync(OUTPUT_PATH, report);

  console.log('✅ Weekly durability report generated');
  console.log(`   Output: ${OUTPUT_PATH}`);
}

main();
