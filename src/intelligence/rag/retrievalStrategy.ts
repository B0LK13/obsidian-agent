/**
 * Retrieval Strategy Types and Configuration
 * Supports keyword, semantic, graph, and hybrid strategies
 */

export type RetrievalStrategy = 
  | 'keyword_only'
  | 'semantic_only'
  | 'graph_only'
  | 'hybrid_current'
  | 'hybrid_learned';

export interface StrategyWeights {
  keyword: number;
  semantic: number;
  graph: number;
}

export interface FallbackConfig {
  enabled: boolean;
  fallbackStrategy: RetrievalStrategy;
  triggers: {
    timeout: boolean;
    lowEvidence: boolean;
    lowConfidence: boolean;
  };
  evidenceThreshold: number;
  confidenceThreshold: number;
}

export interface RetrievalConfig {
  strategy: RetrievalStrategy;
  weights?: StrategyWeights;
  fallback?: FallbackConfig;
  topK: number;
  minScore: number;
}

// Strategy weight configurations (from ablation results)
export const STRATEGY_WEIGHTS: Record<RetrievalStrategy, StrategyWeights> = {
  keyword_only: { keyword: 1.0, semantic: 0.0, graph: 0.0 },
  semantic_only: { keyword: 0.0, semantic: 1.0, graph: 0.0 },
  graph_only: { keyword: 0.0, semantic: 0.0, graph: 1.0 },
  hybrid_current: { keyword: 0.3, semantic: 0.5, graph: 0.2 },
  hybrid_learned: { keyword: 0.24, semantic: 0.58, graph: 0.18 } // Optimized from ablation
};

// Default fallback configuration
export const DEFAULT_FALLBACK: FallbackConfig = {
  enabled: true,
  fallbackStrategy: 'semantic_only',
  triggers: {
    timeout: true,
    lowEvidence: true,
    lowConfidence: false
  },
  evidenceThreshold: 2, // Fall back if < 2 results
  confidenceThreshold: 0.3
};

// Default retrieval configuration (Phase 3B)
export const DEFAULT_RETRIEVAL_CONFIG: RetrievalConfig = {
  strategy: 'hybrid_learned', // Phase 3B: promoted to default
  weights: STRATEGY_WEIGHTS.hybrid_learned,
  fallback: DEFAULT_FALLBACK,
  topK: 10,
  minScore: 0.4
};

export type FallbackReason = 
  | 'timeout'
  | 'low_evidence'
  | 'low_confidence'
  | 'retrieval_error'
  | 'none';

export interface RetrievalResult {
  id: string;
  score: number;
  source: 'keyword' | 'semantic' | 'graph' | 'hybrid';
}

export interface RetrievalMetadata {
  strategy: RetrievalStrategy;
  fallbackTriggered: boolean;
  fallbackReason: FallbackReason;
  resultsCount: number;
  executionTimeMs: number;
}
