#!/usr/bin/env ts-node
/**
 * Benchmark Summary Schema Validator
 *
 * Fails fast with clear errors if the artifact is missing or invalid.
 */

import * as fs from 'node:fs';
import * as path from 'node:path';

const SUMMARY_PATH = process.env.BENCHMARK_SUMMARY_PATH ?? 'artifacts/latest/benchmark-summary.json';

type Summary = {
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

function fail(message: string): never {
  throw new Error(`Benchmark summary invalid: ${message}`);
}

function isNumber(value: unknown): value is number {
  return typeof value === 'number' && Number.isFinite(value);
}

function isString(value: unknown): value is string {
  return typeof value === 'string' && value.trim().length > 0;
}

function validate(summary: Summary): void {
  if (summary.mode !== 'deterministic' && summary.mode !== 'real') {
    fail(`mode must be 'deterministic' or 'real' (got ${String(summary.mode)})`);
  }
  if (!isString(summary.commit_sha)) {
    fail('commit_sha must be a non-empty string');
  }
  if (!isString(summary.runner_os)) {
    fail('runner_os must be a non-empty string');
  }
  if (!isString(summary.node_version)) {
    fail('node_version must be a non-empty string');
  }
  if (!isString(summary.seed)) {
    fail('seed must be a non-empty string');
  }
  if (!isNumber(summary.warmup_runs) || summary.warmup_runs < 0) {
    fail('warmup_runs must be a non-negative number');
  }
  if (!isString(summary.generated_at)) {
    fail('generated_at must be a non-empty string');
  }
  if (!isNumber(summary.query_count) || summary.query_count <= 0) {
    fail('query_count must be a positive number');
  }
  if (!isNumber(summary.p50_ms)) {
    fail('p50_ms must be a number');
  }
  if (!isNumber(summary.p95_ms)) {
    fail('p95_ms must be a number');
  }
  if (!isNumber(summary.total_runtime_ms_50q)) {
    fail('total_runtime_ms_50q must be a number');
  }
  if (!isNumber(summary.error_rate_pct) || summary.error_rate_pct < 0) {
    fail('error_rate_pct must be a non-negative number');
  }
  if (summary.cost_per_query_usd != null && !isNumber(summary.cost_per_query_usd)) {
    fail('cost_per_query_usd must be a number when provided');
  }
  if (!Array.isArray(summary.latency_samples_ms) || summary.latency_samples_ms.length === 0) {
    fail('latency_samples_ms must be a non-empty array');
  }
  const invalidLatency = summary.latency_samples_ms.find(v => !isNumber(v));
  if (invalidLatency != null) {
    fail('latency_samples_ms must contain only numbers');
  }
  if (typeof summary.metadata !== 'object' || summary.metadata == null) {
    fail('metadata must be an object');
  }
}

function main(): void {
  const abs = path.resolve(process.cwd(), SUMMARY_PATH);
  if (!fs.existsSync(abs)) {
    fail(`summary file not found at ${abs}`);
  }

  const raw = fs.readFileSync(abs, 'utf8');
  let parsed: Summary;
  try {
    parsed = JSON.parse(raw) as Summary;
  } catch (error) {
    fail(`summary file is not valid JSON (${String(error)})`);
  }

  validate(parsed);
  console.log('✅ Benchmark summary schema validated');
}

main();
