/**
 * Quality Metrics - Measure agent performance objectively
 */

export interface QualityMetrics {
// Retrieval quality
precision_at_5: number;
precision_at_10: number;
ndcg_at_10: number;
mrr: number;

// Answer quality
faithfulness: number;
citation_correctness: number;
completeness: number;

// Intelligence features
context_carryover: number;
confidence_calibration: number;
ece: number;
}

export interface EvaluationResult {
query_id: string;
query: string;
response: string;
retrieved_notes: string[];
expected_notes: string[];
precision: number;
has_next_step: boolean;
confidence_level: string;
timestamp: number;
}

export class MetricsCalculator {
/**
 * Calculate Precision@K
 */
precisionAtK(retrieved: string[], expected: string[], k: number): number {
const topK = retrieved.slice(0, k);
const relevant = topK.filter(item => 
expected.some(exp => item.toLowerCase().includes(exp.toLowerCase()))
);
return topK.length > 0 ? relevant.length / topK.length : 0;
}

/**
 * Calculate Mean Reciprocal Rank
 */
mrr(retrieved: string[], expected: string[]): number {
for (let i = 0; i < retrieved.length; i++) {
if (expected.some(exp => retrieved[i].toLowerCase().includes(exp.toLowerCase()))) {
return 1 / (i + 1);
}
}
return 0;
}

/**
 * Calculate nDCG@K (Normalized Discounted Cumulative Gain)
 */
ndcgAtK(retrieved: string[], expected: string[], k: number): number {
const dcg = this.calculateDCG(retrieved, expected, k);
const idcg = this.calculateDCG(expected, expected, k);
return idcg > 0 ? dcg / idcg : 0;
}

private calculateDCG(retrieved: string[], expected: string[], k: number): number {
let dcg = 0;
for (let i = 0; i < Math.min(k, retrieved.length); i++) {
const relevance = expected.some(exp => 
retrieved[i].toLowerCase().includes(exp.toLowerCase())
) ? 1 : 0;
dcg += relevance / Math.log2(i + 2);
}
return dcg;
}

/**
 * Calculate Brier Score (confidence calibration)
 */
brierScore(predictions: Array<{predicted: number; actual: boolean}>): number {
const scores = predictions.map(p => 
Math.pow(p.predicted - (p.actual ? 1 : 0), 2)
);
return scores.reduce((a, b) => a + b, 0) / scores.length;
}

/**
 * Calculate Expected Calibration Error
 */
ece(predictions: Array<{predicted: number; actual: boolean}>, bins: number = 10): number {
const binSize = 1.0 / bins;
let ece = 0;

for (let i = 0; i < bins; i++) {
const lower = i * binSize;
const upper = (i + 1) * binSize;

const binPreds = predictions.filter(p => 
p.predicted >= lower && p.predicted < upper
);

if (binPreds.length === 0) continue;

const avgConfidence = binPreds.reduce((sum, p) => sum + p.predicted, 0) / binPreds.length;
const avgAccuracy = binPreds.filter(p => p.actual).length / binPreds.length;

ece += (binPreds.length / predictions.length) * Math.abs(avgConfidence - avgAccuracy);
}

return ece;
}

/**
 * Aggregate metrics across all evaluations
 */
aggregate(results: EvaluationResult[]): QualityMetrics {
const precision5 = results.map(r => 
this.precisionAtK(r.retrieved_notes, r.expected_notes, 5)
);
const precision10 = results.map(r => 
this.precisionAtK(r.retrieved_notes, r.expected_notes, 10)
);
const ndcg = results.map(r => 
this.ndcgAtK(r.retrieved_notes, r.expected_notes, 10)
);
const mrrs = results.map(r => 
this.mrr(r.retrieved_notes, r.expected_notes)
);

return {
precision_at_5: this.mean(precision5),
precision_at_10: this.mean(precision10),
ndcg_at_10: this.mean(ndcg),
mrr: this.mean(mrrs),
faithfulness: this.calculateFaithfulness(results),
citation_correctness: this.calculateCitationCorrectness(results),
completeness: this.calculateCompleteness(results),
context_carryover: 0, // TODO: Implement multi-turn eval
confidence_calibration: 0, // TODO: Implement with real data
ece: 0 // TODO: Implement with real data
};
}

private mean(values: number[]): number {
return values.length > 0 ? values.reduce((a, b) => a + b, 0) / values.length : 0;
}

private calculateFaithfulness(results: EvaluationResult[]): number {
// Placeholder: Check if response mentions retrieved notes
const faithful = results.filter(r => 
r.retrieved_notes.some(note => r.response.includes(note))
);
return faithful.length / results.length;
}

private calculateCitationCorrectness(results: EvaluationResult[]): number {
// Placeholder: Check if citations point to real notes
const withCitations = results.filter(r => r.response.includes('[['));
const correct = withCitations.filter(r => {
const citations = r.response.match(/\[\[([^\]]+)\]\]/g) || [];
return citations.every(c => 
r.retrieved_notes.some(note => c.includes(note))
);
});
return withCitations.length > 0 ? correct.length / withCitations.length : 1.0;
}

private calculateCompleteness(results: EvaluationResult[]): number {
// Placeholder: Check if response has next step
const complete = results.filter(r => r.has_next_step);
return complete.length / results.length;
}
}

export class BenchmarkRunner {
private calculator: MetricsCalculator;

constructor() {
this.calculator = new MetricsCalculator();
}

/**
 * Run benchmark and generate report
 */
async runBenchmark(
queries: any[],
agentFn: (query: string) => Promise<any>
): Promise<{ metrics: QualityMetrics; results: EvaluationResult[] }> {
const results: EvaluationResult[] = [];

for (const query of queries) {
const response = await agentFn(query.query);

results.push({
query_id: query.id,
query: query.query,
response: response.text || response,
retrieved_notes: response.notes || [],
expected_notes: query.expected_notes,
precision: this.calculator.precisionAtK(
response.notes || [],
query.expected_notes,
5
),
has_next_step: (response.text || response).includes('NEXT STEP'),
confidence_level: response.confidence || 'unknown',
timestamp: Date.now()
});
}

const metrics = this.calculator.aggregate(results);

return { metrics, results };
}

/**
 * Generate markdown report
 */
generateReport(metrics: QualityMetrics, baseline?: QualityMetrics): string {
let report = '# Agent Quality Benchmark Report\n\n';
report += `**Generated**: ${new Date().toISOString()}\n\n`;

report += '## Retrieval Quality\n';
report += `- **Precision@5**: ${(metrics.precision_at_5 * 100).toFixed(1)}%`;
if (baseline) report += ` (baseline: ${(baseline.precision_at_5 * 100).toFixed(1)}%)`;
report += '\n';

report += `- **Precision@10**: ${(metrics.precision_at_10 * 100).toFixed(1)}%`;
if (baseline) report += ` (baseline: ${(baseline.precision_at_10 * 100).toFixed(1)}%)`;
report += '\n';

report += `- **nDCG@10**: ${(metrics.ndcg_at_10 * 100).toFixed(1)}%`;
if (baseline) report += ` (baseline: ${(baseline.ndcg_at_10 * 100).toFixed(1)}%)`;
report += '\n';

report += `- **MRR**: ${metrics.mrr.toFixed(3)}`;
if (baseline) report += ` (baseline: ${baseline.mrr.toFixed(3)})`;
report += '\n\n';

report += '## Answer Quality\n';
report += `- **Faithfulness**: ${(metrics.faithfulness * 100).toFixed(1)}%\n`;
report += `- **Citation Correctness**: ${(metrics.citation_correctness * 100).toFixed(1)}%\n`;
report += `- **Completeness**: ${(metrics.completeness * 100).toFixed(1)}%\n\n`;

report += '## Confidence Calibration\n';
report += `- **ECE**: ${metrics.ece.toFixed(3)} (target: <0.15)\n\n`;

report += '## Quality Gates\n';
const gates = this.checkQualityGates(metrics, baseline);
gates.forEach(gate => {
const icon = gate.passed ? '✅' : '❌';
report += `${icon} ${gate.name}: ${gate.message}\n`;
});

return report;
}

/**
 * Check quality gates
 */
checkQualityGates(metrics: QualityMetrics, baseline?: QualityMetrics): Array<{name: string; passed: boolean; message: string}> {
const gates = [];

if (baseline) {
gates.push({
name: 'Precision@5',
passed: metrics.precision_at_5 >= baseline.precision_at_5,
message: `${(metrics.precision_at_5 * 100).toFixed(1)}% >= ${(baseline.precision_at_5 * 100).toFixed(1)}%`
});
}

gates.push({
name: 'Citation Correctness',
passed: metrics.citation_correctness >= 0.98,
message: `${(metrics.citation_correctness * 100).toFixed(1)}% >= 98%`
});

gates.push({
name: 'Completeness',
passed: metrics.completeness >= 0.95,
message: `${(metrics.completeness * 100).toFixed(1)}% >= 95% (next step required)`
});

gates.push({
name: 'ECE',
passed: metrics.ece <= 0.15,
message: `${metrics.ece.toFixed(3)} <= 0.15 (well-calibrated)`
});

return gates;
}
}
