/**
 * Quality Gates Checker
 * Enforces minimum quality thresholds for CI
 */

import * as fs from 'fs';
import * as path from 'path';
import type { QualityMetrics } from '../src/evaluation/metrics';

interface QualityThresholds {
  citation_correctness: number;
  completeness: number;
  ece: number;
  precision_at_5_regression: number;  // Max allowed regression vs baseline
}

interface GateResult {
  metric: string;
  value: number;
  threshold: number;
  passed: boolean;
  message: string;
}

/**
 * Load evaluation results
 */
function loadResults(filepath: string): { metrics: QualityMetrics } {
  if (!fs.existsSync(filepath)) {
    throw new Error(`Results file not found: ${filepath}`);
  }
  
  const content = fs.readFileSync(filepath, 'utf8');
  return JSON.parse(content);
}

/**
 * Check quality gates
 */
function checkGates(
  metrics: QualityMetrics,
  thresholds: QualityThresholds,
  baselineMetrics?: QualityMetrics
): { passed: boolean; results: GateResult[] } {
  const results: GateResult[] = [];
  
  // Gate 1: Citation Correctness >= 0.98
  results.push({
    metric: 'citation_correctness',
    value: metrics.citation_correctness,
    threshold: thresholds.citation_correctness,
    passed: metrics.citation_correctness >= thresholds.citation_correctness,
    message: `Citation correctness: ${(metrics.citation_correctness * 100).toFixed(1)}% (threshold: ${(thresholds.citation_correctness * 100).toFixed(0)}%)`
  });
  
  // Gate 2: Completeness >= 0.95
  results.push({
    metric: 'completeness',
    value: metrics.completeness,
    threshold: thresholds.completeness,
    passed: metrics.completeness >= thresholds.completeness,
    message: `Completeness: ${(metrics.completeness * 100).toFixed(1)}% (threshold: ${(thresholds.completeness * 100).toFixed(0)}%)`
  });
  
  // Gate 3: ECE <= 0.15
  results.push({
    metric: 'ece',
    value: metrics.ece,
    threshold: thresholds.ece,
    passed: metrics.ece <= thresholds.ece,
    message: `ECE (calibration): ${metrics.ece.toFixed(3)} (threshold: ≤${thresholds.ece.toFixed(2)})`
  });
  
  // Gate 4: Precision@5 regression check (if baseline available)
  if (baselineMetrics) {
    const regression = baselineMetrics.precision_at_5 - metrics.precision_at_5;
    const regressionPct = (regression / baselineMetrics.precision_at_5) * 100;
    const allowedRegressionPct = thresholds.precision_at_5_regression * 100;
    
    results.push({
      metric: 'precision_at_5_regression',
      value: regression,
      threshold: thresholds.precision_at_5_regression,
      passed: regressionPct <= allowedRegressionPct,
      message: `Precision@5 regression: ${regressionPct >= 0 ? '+' : ''}${regressionPct.toFixed(1)}pp (max: ${allowedRegressionPct.toFixed(0)}pp)`
    });
  }
  
  const passed = results.every(r => r.passed);
  
  return { passed, results };
}

/**
 * Generate report
 */
function generateReport(gateResults: { passed: boolean; results: GateResult[] }): string {
  const status = gateResults.passed ? '✅ PASSED' : '❌ FAILED';
  
  let report = `# Quality Gates: ${status}\n\n`;
  report += `| Metric | Value | Threshold | Status |\n`;
  report += `|--------|-------|-----------|--------|\n`;
  
  gateResults.results.forEach(r => {
    const statusIcon = r.passed ? '✅' : '❌';
    const valueStr = r.metric === 'ece' || r.metric.includes('regression') 
      ? r.value.toFixed(3) 
      : `${(r.value * 100).toFixed(1)}%`;
    const thresholdStr = r.metric === 'ece' 
      ? `≤${r.threshold.toFixed(2)}`
      : r.metric.includes('regression')
      ? `≤${(r.threshold * 100).toFixed(0)}pp`
      : `≥${(r.threshold * 100).toFixed(0)}%`;
    
    report += `| ${r.metric.replace(/_/g, ' ')} | ${valueStr} | ${thresholdStr} | ${statusIcon} |\n`;
  });
  
  report += `\n---\n\n`;
  
  if (!gateResults.passed) {
    report += `## ⚠️ Failed Checks\n\n`;
    gateResults.results.filter(r => !r.passed).forEach(r => {
      report += `- **${r.metric}**: ${r.message}\n`;
    });
  } else {
    report += `All quality gates passed! 🎉\n`;
  }
  
  return report;
}

/**
 * Main execution
 */
async function main() {
  const resultsPath = path.join(__dirname, 'results', 'full-eval-latest.json');
  const baselinePath = path.join(__dirname, 'results', 'baseline-v1.json');
  
  console.log('🔍 Checking quality gates...\n');
  
  // Load current results
  let results;
  try {
    results = loadResults(resultsPath);
  } catch (error) {
    console.error(`❌ Failed to load results: ${error}`);
    process.exit(1);
  }
  
  // Load baseline (if exists)
  let baseline;
  try {
    baseline = loadResults(baselinePath);
    console.log('📊 Loaded baseline for regression check');
  } catch (error) {
    console.log('⚠️ No baseline found, skipping regression check');
  }
  
  // Define thresholds
  const thresholds: QualityThresholds = {
    citation_correctness: 0.98,
    completeness: 0.95,
    ece: 0.15,
    precision_at_5_regression: 0.03  // Max 3pp regression
  };
  
  // Check gates
  const gateResults = checkGates(results.metrics, thresholds, baseline?.metrics);
  
  // Generate report
  const report = generateReport(gateResults);
  console.log(report);
  
  // Save report
  const reportPath = path.join(__dirname, 'reports', 'quality-gates-latest.md');
  fs.writeFileSync(reportPath, report);
  console.log(`\n📄 Saved: ${reportPath}`);
  
  // Set GitHub Actions output (if running in CI)
  if (process.env.GITHUB_OUTPUT) {
    const output = `gates_passed=${gateResults.passed}\nfailed_metrics=${gateResults.results.filter(r => !r.passed).map(r => r.metric).join(', ')}`;
    fs.appendFileSync(process.env.GITHUB_OUTPUT, output);
  }
  
  // Exit with appropriate code
  process.exit(gateResults.passed ? 0 : 1);
}

if (require.main === module) {
  main();
}

export { checkGates, QualityThresholds, GateResult };
