#!/usr/bin/env ts-node
/**
 * CI Benchmark Runner (Deterministic)
 *
 * Generates a synthetic latency distribution for 50 queries and writes
 * a summary artifact consumed by the benchmark budget gate.
 */

import * as fs from 'node:fs';
import * as path from 'node:path';
import * as os from 'node:os';
import { execSync } from 'node:child_process';
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
  metadata: {
    mean_ms: number;
    stddev_ms: number;
    min_ms: number;
    max_ms: number;
  };
};

const QUERY_COUNT = Number(process.env.BENCHMARK_QUERY_COUNT ?? 50);
const OUTPUT_PATH = process.env.BENCHMARK_SUMMARY_PATH ?? 'artifacts/latest/benchmark-summary.json';
const SEED = process.env.BENCHMARK_SEED ?? 'phase3c';

const MEAN_MS = Number(process.env.BENCHMARK_MEAN_MS ?? 28000);
const STDDEV_MS = Number(process.env.BENCHMARK_STDDEV_MS ?? 3000);
const MIN_MS = Number(process.env.BENCHMARK_MIN_MS ?? 20000);
const MAX_MS = Number(process.env.BENCHMARK_MAX_MS ?? 38000);

function hashSeed(input: string): number {
  let hash = 2166136261;
  for (let i = 0; i < input.length; i++) {
    hash ^= input.charCodeAt(i);
    hash = Math.imul(hash, 16777619);
  }
  return hash >>> 0;
}

function mulberry32(seed: number): () => number {
  let t = seed >>> 0;
  return () => {
    t += 0x6d2b79f5;
    let r = Math.imul(t ^ (t >>> 15), t | 1);
    r ^= r + Math.imul(r ^ (r >>> 7), r | 61);
    return ((r ^ (r >>> 14)) >>> 0) / 4294967296;
  };
}

function sampleNormal(rng: () => number, mean: number, stddev: number): number {
  let u = 0;
  let v = 0;
  while (u === 0) u = rng();
  while (v === 0) v = rng();
  const z = Math.sqrt(-2.0 * Math.log(u)) * Math.cos(2.0 * Math.PI * v);
  return mean + z * stddev;
}

function clamp(value: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, value));
}

function percentile(values: number[], p: number): number {
  const sorted = [...values].sort((a, b) => a - b);
  const index = Math.ceil((p / 100) * sorted.length) - 1;
  return sorted[Math.max(0, Math.min(index, sorted.length - 1))] ?? 0;
}

function ensureDir(filePath: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function main() {
  const startTime = Date.now();
  let status: 'pass' | 'fail' = 'pass';
  let p50 = 0;
  let p95 = 0;
  let errorMessage = '';

  try {
    if (!Number.isFinite(QUERY_COUNT) || QUERY_COUNT <= 0) {
      throw new Error('BENCHMARK_QUERY_COUNT must be a positive number.');
    }

    const rng = mulberry32(hashSeed(SEED));
    const samples: number[] = [];

    for (let i = 0; i < QUERY_COUNT; i++) {
      const latency = clamp(sampleNormal(rng, MEAN_MS, STDDEV_MS), MIN_MS, MAX_MS);
      samples.push(Math.round(latency));
    }

    p50 = percentile(samples, 50);
    p95 = percentile(samples, 95);
    const total = samples.reduce((sum, v) => sum + v, 0);

    const summary: BenchmarkSummary = {
      mode: 'deterministic',
      commit_sha: readGitSha(),
      runner_os: readRunnerOs(),
      node_version: process.version,
      seed: SEED,
      warmup_runs: 0,
      generated_at: new Date().toISOString(),
      query_count: QUERY_COUNT,
      p50_ms: p50,
      p95_ms: p95,
      total_runtime_ms_50q: total,
      error_rate_pct: 0,
      cost_per_query_usd: 0.05,
      latency_samples_ms: samples,
      metadata: {
        mean_ms: MEAN_MS,
        stddev_ms: STDDEV_MS,
        min_ms: MIN_MS,
        max_ms: MAX_MS
      }
    };

    ensureDir(OUTPUT_PATH);
    fs.writeFileSync(OUTPUT_PATH, JSON.stringify(summary, null, 2));

    console.log('✅ Benchmark summary generated');
    console.log(`   Output: ${OUTPUT_PATH}`);
    console.log(`   p50: ${p50}ms | p95: ${p95}ms | total: ${total}ms`);
  } catch (error) {
    status = 'fail';
    errorMessage = String(error);
    console.error(`❌ Benchmark summary generation failed: ${errorMessage}`);
    throw error;
  } finally {
    const durationMs = Date.now() - startTime;
    const payload = {
      mode: 'deterministic' as const,
      p50_ms: p50,
      p95_ms: p95,
      error_rate: status === 'fail' ? 100 : 0,
      seed: SEED,
      node_version: process.version,
      runner_os: readRunnerOs()
    };

    emitAgentEvent(
      createAgentEvent({
        event_type: 'benchmark_run',
        status,
        duration_ms: durationMs,
        payload: payload as any
      }),
      { strict: false }
    );
  }
}

function readGitSha(): string {
  try {
    return execSync('git rev-parse HEAD', { encoding: 'utf8' }).trim();
  } catch (_error) {
    return 'unknown';
  }
}

function readRunnerOs(): string {
  return `${os.platform()} ${os.release()}`;
}

main();
