#!/usr/bin/env ts-node
/**
 * Benchmark Budget Checker
 * 
 * Validates that benchmark metrics stay within budget vs baseline.
 * Hard fail on regression beyond threshold - blocks CI/CD.
 */

import * as fs from 'node:fs';
import * as path from 'node:path';
import { createAgentEvent, emitAgentEvent } from '../src/observability/emit-agent-event.ts';

type Budget = {
  version: string;
  metrics: {
    p50_ms: number;
    p95_ms: number;
    total_runtime_ms_50q: number;
    error_rate_pct?: number;
    cost_per_query_usd?: number;
  };
  thresholds: {
    max_regression_pct: number;      // latency/runtime regression ceiling
    max_error_rate_pct?: number;     // absolute cap
    max_cost_regression_pct?: number;// cost regression ceiling
  };
};

type Current = {
  p50_ms: number;
  p95_ms: number;
  total_runtime_ms_50q: number;
  error_rate_pct?: number;
  cost_per_query_usd?: number;
};

const BUDGET_PATH = process.env.BUDGET_PATH ?? 'artifacts/budgets/phase3b-baseline.json';
const CURRENT_PATH = process.env.BENCHMARK_SUMMARY_PATH ?? 'artifacts/latest/benchmark-summary.json';

function readJson<T>(p: string): T {
  const abs = path.resolve(process.cwd(), p);
  if (!fs.existsSync(abs)) {
    throw new Error(`File not found: ${abs}`);
  }
  return JSON.parse(fs.readFileSync(abs, 'utf8')) as T;
}

// tolerant extractor for evolving summary formats
function extractCurrent(summary: any): Current {
  const pick = (obj: any, keys: string[], fallback?: number): number | undefined => {
    for (const k of keys) {
      const v = k.split('.').reduce((acc: any, part: string) => (acc ? acc[part] : undefined), obj);
      if (typeof v === 'number' && Number.isFinite(v)) return v;
    }
    return fallback;
  };

  const p50 = pick(summary, ['p50_ms', 'latency.p50_ms', 'timings.p50_ms']);
  const p95 = pick(summary, ['p95_ms', 'latency.p95_ms', 'timings.p95_ms']);
  const total = pick(summary, ['total_runtime_ms_50q', 'runtime.total_ms', 'total_ms']);
  const err = pick(summary, ['error_rate_pct', 'quality.error_rate_pct']);
  const cost = pick(summary, ['cost_per_query_usd', 'cost.per_query_usd']);

  if (p50 == null || p95 == null || total == null) {
    throw new Error('Missing required metrics in benchmark summary (p50/p95/total runtime).');
  }

  return {
    p50_ms: p50,
    p95_ms: p95,
    total_runtime_ms_50q: total,
    error_rate_pct: err,
    cost_per_query_usd: cost
  };
}

function regressionPct(current: number, baseline: number): number {
  return ((current - baseline) / baseline) * 100;
}

function formatDuration(ms: number): string {
  if (ms < 1000) return `${ms}ms`;
  if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
  const mins = Math.floor(ms / 60000);
  const secs = ((ms % 60000) / 1000).toFixed(0);
  return `${mins}m ${secs}s`;
}

function assertBudget(current: Current, budget: Budget): string[] {
  const failures: string[] = [];
  const maxReg = budget.thresholds.max_regression_pct;

  const checks: Array<{ name: keyof Current; cur?: number; base?: number; format?: (n: number) => string }> = [
    { 
      name: "p50_ms", 
      cur: current.p50_ms, 
      base: budget.metrics.p50_ms,
      format: formatDuration
    },
    { 
      name: "p95_ms", 
      cur: current.p95_ms, 
      base: budget.metrics.p95_ms,
      format: formatDuration
    },
    { 
      name: "total_runtime_ms_50q", 
      cur: current.total_runtime_ms_50q, 
      base: budget.metrics.total_runtime_ms_50q,
      format: formatDuration
    }
  ];

  for (const c of checks) {
    const r = regressionPct(c.cur!, c.base!);
    const formattedName = String(c.name).replace(/_/g, ' ').toUpperCase();
    const formattedCur = c.format ? c.format(c.cur!) : `${c.cur}`;
    const formattedBase = c.format ? c.format(c.base!) : `${c.base}`;
    
    if (r > maxReg) {
      failures.push(
        `${formattedName} regression +${r.toFixed(2)}% (${formattedCur} vs ${formattedBase}) > +${maxReg}%`
      );
    }
  }

  if (budget.thresholds.max_error_rate_pct != null && current.error_rate_pct != null) {
    if (current.error_rate_pct > budget.thresholds.max_error_rate_pct) {
      failures.push(
        `ERROR RATE ${current.error_rate_pct}% > ${budget.thresholds.max_error_rate_pct}% cap`
      );
    }
  }

  if (
    budget.thresholds.max_cost_regression_pct != null &&
    budget.metrics.cost_per_query_usd != null &&
    current.cost_per_query_usd != null
  ) {
    const r = regressionPct(current.cost_per_query_usd, budget.metrics.cost_per_query_usd);
    if (r > budget.thresholds.max_cost_regression_pct) {
      failures.push(
        `COST/QUERY regression +${r.toFixed(2)}% ($${current.cost_per_query_usd.toFixed(4)} vs $${budget.metrics.cost_per_query_usd.toFixed(4)}) > +${budget.thresholds.max_cost_regression_pct}%`
      );
    }
  }

  return failures;
}

function main() {
  console.log('📊 Benchmark Budget Check\n');

  const startTime = Date.now();
  let status: 'pass' | 'fail' = 'pass';
  let errorMessage = '';
  let exitCode = 0;
  let payload: any = {
    mode: 'deterministic',
    p50_ms: 0,
    p95_ms: 0,
    error_rate: 0,
    baseline_p95_ms: 0,
    threshold_p95_ms: 0,
    regression_pct: 0,
    seed: 'unknown',
    node_version: process.version,
    runner_os: process.platform
  };

  try {
    const budget = readJson<Budget>(BUDGET_PATH);
    const summary = readJson<any>(CURRENT_PATH);
    const current = extractCurrent(summary);

    const failures = assertBudget(current, budget);

    console.log(`Budget Version: ${budget.version}\n`);

    console.log('Baseline Metrics:');
    console.log(`  p50:        ${formatDuration(budget.metrics.p50_ms)}`);
    console.log(`  p95:        ${formatDuration(budget.metrics.p95_ms)}`);
    console.log(`  Total (50q): ${formatDuration(budget.metrics.total_runtime_ms_50q)}`);

    console.log('\nCurrent Metrics:');
    console.log(`  p50:        ${formatDuration(current.p50_ms)}`);
    console.log(`  p95:        ${formatDuration(current.p95_ms)}`);
    console.log(`  Total (50q): ${formatDuration(current.total_runtime_ms_50q)}`);

    if (current.error_rate_pct != null) {
      console.log(`  Error Rate: ${current.error_rate_pct}%`);
    }
    if (current.cost_per_query_usd != null) {
      console.log(`  Cost/Query: $${current.cost_per_query_usd.toFixed(4)}`);
    }

    const baselineP95 = budget.metrics.p95_ms;
    const thresholdP95 = baselineP95 * (1 + budget.thresholds.max_regression_pct / 100);
    const regression = regressionPct(current.p95_ms, baselineP95);

    payload = {
      mode: summary?.mode === 'real' ? 'real' : 'deterministic',
      p50_ms: current.p50_ms,
      p95_ms: current.p95_ms,
      error_rate: current.error_rate_pct ?? 0,
      baseline_p95_ms: baselineP95,
      threshold_p95_ms: thresholdP95,
      regression_pct: regression,
      seed: summary?.seed ?? 'unknown',
      node_version: summary?.node_version ?? process.version,
      runner_os: summary?.runner_os ?? process.platform
    };

    if (failures.length) {
      status = 'fail';
      exitCode = 1;
      console.error('\n❌ BUDGET GATE FAILED');
      console.error('\nRegressions detected:');
      for (const f of failures) {
        console.error(`  • ${f}`);
      }
      console.error(`\nMax allowed regression: +${budget.thresholds.max_regression_pct}%`);
      return;
    }

    console.log('\n✅ BUDGET GATE PASSED');
    console.log(`   All metrics within +${budget.thresholds.max_regression_pct}% regression threshold`);
  } catch (error) {
    status = 'fail';
    errorMessage = String(error);
    exitCode = 1;
    console.error(`\n❌ Budget check failed: ${errorMessage}`);
  } finally {
    const durationMs = Date.now() - startTime;
    if (errorMessage) {
      payload.failure_reason = errorMessage;
    }
    emitAgentEvent(
      createAgentEvent({
        event_type: 'budget_gate',
        status,
        duration_ms: durationMs,
        payload
      }),
      { strict: false }
    );
  }

  if (exitCode !== 0) {
    process.exit(exitCode);
  }
}

main();
