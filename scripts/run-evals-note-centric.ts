#!/usr/bin/env ts-node
/**
 * Note-centric eval runner (scaffold).
 */

import * as fs from 'node:fs';
import * as path from 'node:path';

type EvalCase = {
  id: string;
  bucket: string;
  query: string;
  expected_keywords: string[];
};

type Dataset = {
  version: string;
  dataset: string;
  total_cases: number;
  buckets: string[];
  cases: EvalCase[];
};

type EvalResult = {
  id: string;
  bucket: string;
  status: 'pass' | 'fail';
  notes?: string;
};

type Summary = {
  dataset: string;
  version: string;
  mode: 'smoke' | 'full';
  total: number;
  passed: number;
  failed: number;
  pass_rate_pct: number;
  generated_at: string;
  sample_size: number;
  correlation_id: string;
};

const DATASET_PATH = process.env.EVAL_DATASET_PATH ?? 'tests/evals/note-centric.dataset.json';
const SUMMARY_PATH = process.env.EVAL_SUMMARY_PATH ?? 'artifacts/latest/evals-note-centric-summary.json';
const RESULTS_PATH = process.env.EVAL_RESULTS_PATH ?? 'artifacts/latest/evals-note-centric-results.json';

function ensureDir(filePath: string): void {
  const dir = path.dirname(filePath);
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
}

function readDataset(): Dataset {
  const abs = path.resolve(process.cwd(), DATASET_PATH);
  if (!fs.existsSync(abs)) {
    throw new Error(`Dataset not found at ${abs}`);
  }
  return JSON.parse(fs.readFileSync(abs, 'utf8')) as Dataset;
}

function selectSample(cases: EvalCase[], sampleSize: number): EvalCase[] {
  if (!Number.isFinite(sampleSize) || sampleSize <= 0) return cases;
  return cases.slice(0, sampleSize);
}

function evaluateCase(evalCase: EvalCase): EvalResult {
  if (!evalCase.query || evalCase.query.trim().length === 0) {
    return { id: evalCase.id, bucket: evalCase.bucket, status: 'fail', notes: 'Empty query' };
  }
  return { id: evalCase.id, bucket: evalCase.bucket, status: 'pass' };
}

function main(): void {
  const dataset = readDataset();
  const sampleSize = Number(process.env.EVAL_SAMPLE_SIZE ?? 0);
  const mode = (process.env.EVAL_MODE ?? (sampleSize ? 'smoke' : 'full')) as 'smoke' | 'full';
  const correlationId = process.env.CORRELATION_ID ?? `eval-${Date.now()}`;

  const selected = selectSample(dataset.cases, sampleSize);
  const results = selected.map(evaluateCase);
  const passed = results.filter(r => r.status === 'pass').length;
  const failed = results.filter(r => r.status === 'fail').length;
  const passRate = selected.length ? (passed / selected.length) * 100 : 0;

  const summary: Summary = {
    dataset: dataset.dataset,
    version: dataset.version,
    mode,
    total: selected.length,
    passed,
    failed,
    pass_rate_pct: Math.round(passRate * 100) / 100,
    generated_at: new Date().toISOString(),
    sample_size: selected.length,
    correlation_id: correlationId
  };

  ensureDir(SUMMARY_PATH);
  ensureDir(RESULTS_PATH);
  fs.writeFileSync(SUMMARY_PATH, JSON.stringify(summary, null, 2));
  fs.writeFileSync(RESULTS_PATH, JSON.stringify(results, null, 2));

  console.log('✅ Note-centric evals completed');
  console.log(`   Summary: ${SUMMARY_PATH}`);
  console.log(`   Results: ${RESULTS_PATH}`);
  console.log(`   Pass rate: ${summary.pass_rate_pct}% (${passed}/${selected.length})`);
}

main();
