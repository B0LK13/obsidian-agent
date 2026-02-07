/**
 * Failure Analysis - Task 5 & 7
 * Taxonomize failures and generate remediation backlog
 */

export type FailureMode = 
  | 'retrieval_miss'           // No relevant results found
  | 'wrong_strategy'           // Router selected suboptimal strategy
  | 'synthesis_drift'          // Answer doesn't align with evidence
  | 'citation_mismatch'        // Citations don't match expected sources
  | 'confidence_miscalibration' // Confidence doesn't match actual quality
  | 'timeout'                  // Execution exceeded time limit
  | 'tool_error'               // Tool execution failed
  | 'parse_error'              // Response parsing failed
  | 'incomplete_response'      // Missing required fields (e.g., next_step)
  | 'low_quality_synthesis';   // Response quality below threshold

export interface FailureInstance {
  queryId: string;
  query: string;
  type: string;
  difficulty: string;
  mode: FailureMode;
  severity: 'low' | 'medium' | 'high' | 'critical';
  rootCause: string;
  evidence: string;
  suggestedFix: string;
}

export interface FailureTaxonomy {
  totalFailures: number;
  byMode: Record<FailureMode, number>;
  bySeverity: Record<string, number>;
  byType: Record<string, number>;
  instances: FailureInstance[];
}

/**
 * Classify failure mode based on trace
 */
export function classifyFailure(trace: any, expected: any): FailureInstance | null {
  const queryId = trace.query_id;
  const query = trace.query;
  const type = trace.type;
  const difficulty = trace.difficulty;
  
  // Check for timeout
  if (trace.error?.includes('timeout') || trace.execution_time_ms > 120000) {
    return {
      queryId,
      query,
      type,
      difficulty,
      mode: 'timeout',
      severity: 'medium',
      rootCause: `Execution took ${(trace.execution_time_ms / 1000).toFixed(0)}s (limit: 120s)`,
      evidence: trace.error || 'Exceeded time limit',
      suggestedFix: 'Optimize retrieval or reduce max_tokens'
    };
  }
  
  // Check for tool errors
  if (trace.error?.includes('tool') || trace.error?.includes('Error')) {
    return {
      queryId,
      query,
      type,
      difficulty,
      mode: 'tool_error',
      severity: 'high',
      rootCause: 'Tool execution failed',
      evidence: trace.error || 'Unknown tool error',
      suggestedFix: 'Add error handling and fallback logic'
    };
  }
  
  // Check for missing next step
  if (!trace.has_next_step) {
    return {
      queryId,
      query,
      type,
      difficulty,
      mode: 'incomplete_response',
      severity: 'low',
      rootCause: 'Response missing required next_step field',
      evidence: `Answer: ${trace.answer?.substring(0, 100)}...`,
      suggestedFix: 'Strengthen momentum policy in agent prompt'
    };
  }
  
  // Check for retrieval miss (no evidence)
  if (trace.evidence.length === 0 && expected.expected_notes > 0) {
    return {
      queryId,
      query,
      type,
      difficulty,
      mode: 'retrieval_miss',
      severity: 'high',
      rootCause: 'No relevant notes retrieved',
      evidence: `Expected ${expected.expected_notes} notes, got 0`,
      suggestedFix: 'Tune retrieval weights or expand corpus'
    };
  }
  
  // Check for citation mismatch
  if (expected.expected_notes && trace.evidence.length !== expected.expected_notes) {
    const delta = Math.abs(trace.evidence.length - expected.expected_notes);
    if (delta > 2) {
      return {
        queryId,
        query,
        type,
        difficulty,
        mode: 'citation_mismatch',
        severity: delta > 5 ? 'high' : 'medium',
        rootCause: `Citation count mismatch: expected ${expected.expected_notes}, got ${trace.evidence.length}`,
        evidence: `Citations: ${trace.evidence.join(', ')}`,
        suggestedFix: 'Review retrieval strategy or adjust expected baseline'
      };
    }
  }
  
  // Check for confidence miscalibration
  const confidenceDelta = Math.abs(trace.confidence - (expected.expected_confidence || 0.5));
  if (confidenceDelta > 0.3) {
    return {
      queryId,
      query,
      type,
      difficulty,
      mode: 'confidence_miscalibration',
      severity: 'low',
      rootCause: `Confidence off by ${(confidenceDelta * 100).toFixed(0)}pp`,
      evidence: `Predicted ${(trace.confidence * 100).toFixed(0)}%, expected ${((expected.expected_confidence || 0.5) * 100).toFixed(0)}%`,
      suggestedFix: 'Recalibrate ConfidenceEstimator thresholds'
    };
  }
  
  return null; // No failure detected
}

/**
 * Analyze all failures and create taxonomy
 */
export function analyzeFail ures(traces: any[], expectedResults: any[]): FailureTaxonomy {
  const instances: FailureInstance[] = [];
  const byMode: Record<FailureMode, number> = {
    retrieval_miss: 0,
    wrong_strategy: 0,
    synthesis_drift: 0,
    citation_mismatch: 0,
    confidence_miscalibration: 0,
    timeout: 0,
    tool_error: 0,
    parse_error: 0,
    incomplete_response: 0,
    low_quality_synthesis: 0
  };
  const bySeverity: Record<string, number> = { low: 0, medium: 0, high: 0, critical: 0 };
  const byType: Record<string, number> = {};
  
  for (let i = 0; i < traces.length; i++) {
    const trace = traces[i];
    const expected = expectedResults.find((e: any) => e.id === trace.query_id) || {};
    
    const failure = classifyFailure(trace, expected);
    if (failure) {
      instances.push(failure);
      byMode[failure.mode]++;
      bySeverity[failure.severity]++;
      byType[failure.type] = (byType[failure.type] || 0) + 1;
    }
  }
  
  return {
    totalFailures: instances.length,
    byMode,
    bySeverity,
    byType,
    instances
  };
}

/**
 * Generate top-10 remediation backlog
 */
export function generateRemediationBacklog(taxonomy: FailureTaxonomy): string[] {
  // Sort by severity (critical > high > medium > low) and frequency
  const severityWeight = { critical: 4, high: 3, medium: 2, low: 1 };
  
  const sortedInstances = [...taxonomy.instances].sort((a, b) => {
    const aWeight = severityWeight[a.severity];
    const bWeight = severityWeight[b.severity];
    if (aWeight !== bWeight) return bWeight - aWeight;
    return 0; // Same severity, preserve order
  });
  
  // Generate backlog items
  const backlog: string[] = [];
  const seenFixes = new Set<string>();
  
  for (const instance of sortedInstances.slice(0, 10)) {
    const fixKey = `${instance.mode}:${instance.suggestedFix}`;
    if (!seenFixes.has(fixKey)) {
      backlog.push(
        `[${instance.severity.toUpperCase()}] ${instance.mode} - ${instance.suggestedFix} ` +
        `(Query: ${instance.queryId}, Type: ${instance.type})`
      );
      seenFixes.add(fixKey);
    }
  }
  
  return backlog.slice(0, 10);
}
