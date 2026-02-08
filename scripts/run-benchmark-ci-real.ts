#!/usr/bin/env ts-node
/**
 * CI Benchmark Runner (Real - Ollama)
 *
 * Runs the production benchmark and emits a summary artifact for observability.
 */

import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';
import { execSync } from 'node:child_process';
import { runProductionBenchmark } from '../eval/runProductionBenchmark';
import { createAgentEvent, emitAgentEvent } from '../src/observability/emit-agent-event.ts';

type BenchmarkSummary = {
  mode: 'deterministic' | 'real';
  commit_sha: string;
  runner_os: string;
  node_version: string;
  seed: string;
  warmup_runs: number;
  generated_at: string;
  query_count: number;
  p50_ms: number;
  p95_ms: number;
  total_runtime_ms_50q: number;
  error_rate_pct: number;
  cost_per_query_usd?: number;
  latency_samples_ms: number[];
  metadata: Record<string, unknown>;
};

const OUTPUT_PATH = process.env.BENCHMARK_SUMMARY_PATH ?? 'artifacts/latest/benchmark-summary.json';
const SEED = process.env.BENCHMARK_SEED ?? 'none';
const WARMUP_RUNS = Number(process.env.BENCHMARK_WARMUP_RUNS ?? 1);

function ensureDir(filePath: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function percentile(values: number[], p: number): number {
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, Math.min(index, sorted.length - 1))] ?? 0;
}

function readGitSha(): string {
  try {
    return execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
  } catch (_error) {
    return 'unknown';
  }
}

async function main(): Promise<void> {
  const startTime = Date.now();
  let status: 'pass' | 'fail' = 'pass';
  let p50 = 0;
  let p95 = 0;
  let errorRate = 0;

  if (process.env.BENCHMARK_MODE !== 'real') {
    throw new Error('BENCHMARK_MODE must be set to "real" to run the production benchmark.');
  }

  if (!Number.isFinite(WARMUP_RUNS) || WARMUP_RUNS < 0) {
    throw new Error('BENCHMARK_WARMUP_RUNS must be a non-negative number.');
  }

  const sampleSize = process.env.BENCHMARK_SAMPLE_SIZE
    ? Number(process.env.BENCHMARK_SAMPLE_SIZE)
    : undefined;

  try {
    const result = await runProductionBenchmark(sampleSize);
    const samples = result.traces.map(t => t.execution_time_ms).filter(v => Number.isFinite(v));

    if (samples.length === 0) {
      throw new Error('No execution_time_ms samples found in benchmark traces.');
    }

    p50 = percentile(samples, 50);
    p95 = percentile(samples, 95);
    const total50 = samples.slice(0, 50).reduce((sum, v) => sum + v, 0);
    errorRate = result.dataset_size > 0 ? (result.failed / result.dataset_size) * 100 : 0;

    const summary: BenchmarkSummary = {
      mode: 'real',
      commit_sha: result.metadata.git_commit || readGitSha(),
      runner_os: `${os.platform()} ${os.release()}`,
      node_version: process.version,
      seed: SEED,
      warmup_runs: WARMUP_RUNS,
      generated_at: new Date().toISOString(),
      query_count: samples.length,
      p50_ms: p50,
      p95_ms: p95,
      total_runtime_ms_50q: total50,
      error_rate_pct: errorRate,
      latency_samples_ms: samples,
      metadata: {
        dataset_size: result.dataset_size,
        completed: result.completed,
        failed: result.failed,
        strategy: result.metadata.strategy,
        total_benchmark_time_ms: (result.metadata as any).total_benchmark_time_ms,
        sample_size: sampleSize ?? 'full'
      }
    };

    ensureDir(OUTPUT_PATH);
    fs.writeFileSync(OUTPUT_PATH, JSON.stringify(summary, null, 2));

    console.log('✅ Real benchmark summary generated');
    console.log(`   Output: ${OUTPUT_PATH}`);
    console.log(`   p50: ${p50}ms | p95: ${p95}ms | total: ${total50}ms`);
  } catch (error) {
    status = 'fail';
    console.error(`❌ Real benchmark failed: ${String(error)}`);
    throw error;
  } finally {
    const durationMs = Date.now() - startTime;
    emitAgentEvent(
      createAgentEvent({
        event_type: 'benchmark_run',
        status,
        duration_ms: durationMs,
        payload: {
          mode: 'real',
          p50_ms: p50,
          p95_ms: p95,
          error_rate: errorRate,
          seed: SEED,
          node_version: process.version,
          runner_os: `${os.platform()} ${os.release()}`
        }
      }),
      { strict: false }
    );
  }
}

main().catch(error => {
  console.error(`❌ Real benchmark failed: ${String(error)}`);
  process.exit(1);
});
