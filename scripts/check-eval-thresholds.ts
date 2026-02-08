#!/usr/bin/env ts-node
/**
 * Check eval pass rate thresholds.
 */

import * as fs from 'node:fs';
import * as path from 'node:path';

type Summary = {
  mode: 'smoke' | 'full';
  pass_rate_pct: number;
  total: number;
  passed: number;
  failed: number;
};

const SUMMARY_PATH = process.env.EVAL_SUMMARY_PATH ?? 'artifacts/latest/evals-note-centric-summary.json';

function readSummary(): Summary {
  const abs = path.resolve(process.cwd(), SUMMARY_PATH);
  if (!fs.existsSync(abs)) {
    throw new Error(`Eval summary not found at ${abs}`);
  }
  return JSON.parse(fs.readFileSync(abs, 'utf8')) as Summary;
}

function getThreshold(summary: Summary): number {
  const env = process.env.EVAL_MIN_PASS_RATE_PCT;
  if (env && Number.isFinite(Number(env))) {
    return Number(env);
  }
  return summary.mode === 'smoke' ? 95 : 90;
}

function main(): void {
  const summary = readSummary();
  const threshold = getThreshold(summary);

  console.log('📊 Eval Threshold Check\n');
  console.log(`Mode: ${summary.mode}`);
  console.log(`Pass rate: ${summary.pass_rate_pct}% (${summary.passed}/${summary.total})`);
  console.log(`Threshold: ${threshold}%`);

  if (summary.pass_rate_pct < threshold) {
    console.error('\n❌ EVAL THRESHOLD FAILED');
    console.error(`Pass rate ${summary.pass_rate_pct}% < ${threshold}%`);
    process.exit(1);
  }

  console.log('\n✅ EVAL THRESHOLD PASSED');
}

main();
