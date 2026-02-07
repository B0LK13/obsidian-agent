/**
 * Query Router - Classifies queries and selects optimal retrieval strategy
 * Task 3: Per-type strategy mapping for better performance
 */

import { RetrievalStrategy, StrategyWeights } from './retrievalStrategy';

export type QueryType = 'technical' | 'project' | 'research' | 'maintenance';

export interface QueryClassification {
  type: QueryType;
  confidence: number;
  signals: string[];
}

export interface RouterDecision {
  classification: QueryClassification;
  recommendedStrategy: RetrievalStrategy;
  recommendedWeights: StrategyWeights;
  rationale: string;
}

// Per-type strategy mapping (from Phase 3B directive)
const STRATEGY_MAP: Record<QueryType, { strategy: RetrievalStrategy; weights: StrategyWeights; rationale: string }> = {
  technical: {
    strategy: 'hybrid_learned',
    weights: { keyword: 0.2, semantic: 0.65, graph: 0.15 }, // Semantic-heavy for concepts
    rationale: 'Technical queries benefit from semantic understanding of concepts and terminology'
  },
  project: {
    strategy: 'hybrid_learned',
    weights: { keyword: 0.35, semantic: 0.45, graph: 0.20 }, // Balanced with graph for relationships
    rationale: 'Project queries need keyword precision + freshness + relationship context'
  },
  research: {
    strategy: 'hybrid_learned',
    weights: { keyword: 0.15, semantic: 0.55, graph: 0.30 }, // Graph-heavy for connections
    rationale: 'Research queries benefit from semantic similarity and graph-based discovery'
  },
  maintenance: {
    strategy: 'hybrid_current',
    weights: { keyword: 0.50, semantic: 0.30, graph: 0.20 }, // Keyword-heavy for exact matches
    rationale: 'Maintenance queries often need exact keyword matches and metadata filters'
  }
};

// Signal patterns for classification (simple keyword-based for now)
const CLASSIFICATION_SIGNALS: Record<QueryType, string[]> = {
  technical: [
    'how do i', 'implement', 'code', 'function', 'api', 'error', 'debug',
    'algorithm', 'data structure', 'pattern', 'architecture', 'framework',
    'library', 'method', 'class', 'typescript', 'javascript', 'python',
    'react', 'node', 'authentication', 'database', 'setup', 'configure'
  ],
  project: [
    'project', 'task', 'deadline', 'milestone', 'status', 'update',
    'progress', 'plan', 'meeting', 'decision', 'team', 'assignment',
    'sprint', 'release', 'roadmap', 'backlog', 'priority'
  ],
  research: [
    'research', 'study', 'paper', 'article', 'concept', 'theory',
    'literature', 'source', 'citation', 'reference', 'analysis',
    'comparison', 'overview', 'summary', 'topic', 'subject', 'field',
    'explore', 'investigate', 'understand', 'learn about'
  ],
  maintenance: [
    'find', 'where is', 'locate', 'list all', 'show me', 'get',
    'retrieve', 'fetch', 'search for', 'file', 'folder', 'note',
    'tag', 'link', 'broken', 'missing', 'duplicate', 'orphan'
  ]
};

/**
 * Classify query by type using signal matching
 */
export function classifyQuery(query: string): QueryClassification {
  const lowerQuery = query.toLowerCase();
  const scores: Record<QueryType, number> = {
    technical: 0,
    project: 0,
    research: 0,
    maintenance: 0
  };

  // Count signal matches for each type
  for (const [type, signals] of Object.entries(CLASSIFICATION_SIGNALS)) {
    for (const signal of signals) {
      if (lowerQuery.includes(signal)) {
        scores[type as QueryType]++;
      }
    }
  }

  // Find type with highest score
  const entries = Object.entries(scores) as [QueryType, number][];
  entries.sort((a, b) => b[1] - a[1]);
  
  const [topType, topScore] = entries[0];
  const totalSignals = Object.values(scores).reduce((sum, s) => sum + s, 0);
  
  // Default to technical if no clear match
  const finalType = totalSignals === 0 ? 'technical' : topType;
  const confidence = totalSignals === 0 ? 0.5 : Math.min(topScore / Math.max(totalSignals, 1), 1.0);
  
  // Get matched signals for transparency
  const matchedSignals = CLASSIFICATION_SIGNALS[finalType].filter(s => lowerQuery.includes(s));
  
  return {
    type: finalType,
    confidence,
    signals: matchedSignals.slice(0, 5) // Top 5 signals
  };
}

/**
 * Route query to optimal retrieval strategy
 */
export function routeQuery(query: string): RouterDecision {
  const classification = classifyQuery(query);
  const strategyConfig = STRATEGY_MAP[classification.type];
  
  return {
    classification,
    recommendedStrategy: strategyConfig.strategy,
    recommendedWeights: strategyConfig.weights,
    rationale: strategyConfig.rationale
  };
}

/**
 * Get strategy for a known query type (bypass classification)
 */
export function getStrategyForType(type: QueryType): { strategy: RetrievalStrategy; weights: StrategyWeights } {
  const config = STRATEGY_MAP[type];
  return {
    strategy: config.strategy,
    weights: config.weights
  };
}
