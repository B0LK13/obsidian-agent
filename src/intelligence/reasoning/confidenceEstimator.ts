/**
 * Confidence Estimator - Quantifies uncertainty in agent responses
 */

export interface ConfidenceScore {
factual: number;      // 0-1: Confidence in facts stated
logical: number;      // 0-1: Confidence in reasoning
complete: number;     // 0-1: Confidence answer is complete
overall: number;      // 0-1: Combined confidence
level: 'high' | 'medium' | 'low';
disclaimers: string[];
}

export class ConfidenceEstimator {
/**
 * Estimate confidence in a response
 */
estimate(response: string, context: {
vaultSearchResults?: number;
toolsUsed?: string[];
reasoningSteps?: number;
}): ConfidenceScore {
const factual = this.estimateFactualConfidence(response, context);
const logical = this.estimateLogicalConfidence(response);
const complete = this.estimateCompleteness(response, context);

const overall = (factual * 0.4 + logical * 0.3 + complete * 0.3);

const level = overall >= 0.7 ? 'high' : overall >= 0.4 ? 'medium' : 'low';

const disclaimers = this.generateDisclaimers(factual, logical, complete, context);

return {
factual,
logical,
complete,
overall,
level,
disclaimers
};
}

/**
 * Estimate confidence in factual claims
 */
private estimateFactualConfidence(response: string, context: any): number {
let confidence = 0.5; // Start neutral

// Higher confidence if backed by vault content
if (context.vaultSearchResults > 0) {
confidence += 0.3;
}

// Higher confidence if citing specific notes
const citations = (response.match(/\[\[([^\]]+)\]\]/g) || []).length;
confidence += Math.min(citations * 0.05, 0.2);

// Lower confidence for hedging language
const hedges = [
/I think/gi,
/probably/gi,
/might be/gi,
/could be/gi,
/I'm not sure/gi,
/possibly/gi
];

for (const hedge of hedges) {
if (hedge.test(response)) {
confidence -= 0.1;
}
}

// Lower confidence for no evidence
if (!context.vaultSearchResults && !citations) {
confidence -= 0.2;
}

return Math.max(0, Math.min(1, confidence));
}

/**
 * Estimate confidence in logical reasoning
 */
private estimateLogicalConfidence(response: string): number {
let confidence = 0.6; // Start reasonably confident

// Higher if provides reasoning
const reasoningIndicators = [
/because/gi,
/therefore/gi,
/this means/gi,
/as a result/gi,
/consequently/gi
];

for (const indicator of reasoningIndicators) {
if (indicator.test(response)) {
confidence += 0.1;
}
}

// Lower for contradictions
const contradictions = [
/(?:but|however),?\s+(?:also|still)/gi,
/on the other hand/gi
];

for (const contradiction of contradictions) {
if (contradiction.test(response)) {
confidence -= 0.15;
}
}

// Lower for complex conditionals without resolution
const unresolvedConditionals = response.match(/if\s+.*?then/gi);
if (unresolvedConditionals && unresolvedConditionals.length > 2) {
confidence -= 0.1;
}

return Math.max(0, Math.min(1, confidence));
}

/**
 * Estimate completeness of answer
 */
private estimateCompleteness(response: string, _context: any): number {
let confidence = 0.5;

// Higher if response is substantial
if (response.length > 300) {
confidence += 0.2;
}

// Higher if includes next step (from momentum policy)
if (response.includes('NEXT STEP') || response.includes('🎯')) {
confidence += 0.2;
}

// Higher if alternatives provided
if (response.includes('Alternative') || response.includes('option')) {
confidence += 0.1;
}

// Lower if ends with questions
if (response.trim().endsWith('?')) {
confidence -= 0.2;
}

// Lower if explicitly incomplete
const incompleteMarkers = [
/I couldn't find/gi,
/I don't have enough information/gi,
/I need to know more about/gi,
/missing/gi
];

for (const marker of incompleteMarkers) {
if (marker.test(response)) {
confidence -= 0.15;
}
}

return Math.max(0, Math.min(1, confidence));
}

/**
 * Generate appropriate disclaimers
 */
private generateDisclaimers(factual: number, logical: number, complete: number, context: any): string[] {
const disclaimers: string[] = [];

if (factual < 0.5) {
if (!context.vaultSearchResults) {
disclaimers.push("I couldn't find this information in your vault, so I'm relying on general knowledge");
} else {
disclaimers.push("I have limited confidence in these facts - please verify");
}
}

if (logical < 0.5) {
disclaimers.push("This reasoning involves some assumptions that may not apply to your situation");
}

if (complete < 0.4) {
disclaimers.push("This answer may be incomplete - I may be missing important context");
}

if (factual < 0.3 && logical < 0.3) {
disclaimers.push("⚠️ Low confidence: This response is speculative and should be verified");
}

return disclaimers;
}

/**
 * Format confidence information for display
 */
formatConfidence(score: ConfidenceScore): string {
if (score.level === 'high') {
return ''; // Don't show for high confidence
}

let output = '\n---\n';

if (score.level === 'medium') {
output += '**📊 Confidence: Medium**\n';
} else {
output += '**⚠️ Confidence: Low**\n';
}

if (score.disclaimers.length > 0) {
output += score.disclaimers.map(d => `- ${d}`).join('\n');
output += '\n';
}

if (score.level === 'low') {
output += '\n*Please verify this information before relying on it.*\n';
}

return output;
}

/**
 * Check if response should include confidence warning
 */
shouldWarn(score: ConfidenceScore): boolean {
return score.level === 'low' || score.overall < 0.4;
}

/**
 * Get recommended next step based on low confidence
 */
getLowConfidenceNextStep(score: ConfidenceScore): string {
if (score.factual < 0.4) {
return "Verify facts against reliable sources or search your vault for related content";
}

if (score.logical < 0.4) {
return "Review the reasoning and consider alternative perspectives";
}

if (score.complete < 0.4) {
return "Provide additional context or clarify your question for a more complete answer";
}

return "Verify this information independently";
}
}

