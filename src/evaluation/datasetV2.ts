/**
 * Dataset V2 Loader - 200 Query Expansion
 * JSONL format with label governance fields
 */

import * as fs from 'fs';
import * as path from 'path';

export enum QueryType {
  TECHNICAL = 'technical',
  PROJECT = 'project',
  RESEARCH = 'research',
  MAINTENANCE = 'maintenance'
}

export enum Difficulty {
  EASY = 'easy',
  MEDIUM = 'medium',
  HARD = 'hard'
}

export enum Confidence {
  HIGH = 'high',
  MEDIUM = 'medium',
  LOW = 'low'
}

export enum SourceScope {
  PROJECT = 'project',
  VAULT = 'vault',
  GLOBAL = 'global'
}

export interface GoldenQueryV2 {
  // Core identification
  id: string;
  query: string;
  type: QueryType;
  difficulty: Difficulty;
  
  // Expected outcomes
  expected_notes: string[];
  expected_confidence: Confidence;
  expected_next_step: string;
  
  // Label governance (optional)
  expected_answer_outline?: string;
  required_evidence_count?: number;
  allowed_source_scope?: SourceScope;
  
  // Metadata
  context?: string;
  notes?: string;
}

export interface DatasetMetadata {
  version: string;
  created: string;
  total_queries: number;
  by_type: Record<QueryType, number>;
  by_difficulty: Record<Difficulty, number>;
  special_categories: {
    no_answer_queries: number;
    conflicting_evidence_queries: number;
  };
}

/**
 * Load dataset from JSONL file
 */
export function loadDatasetV2(filepath?: string): GoldenQueryV2[] {
  const datasetPath = filepath || path.join(__dirname, 'datasets', 'dataset_v2.jsonl');
  
  if (!fs.existsSync(datasetPath)) {
    throw new Error(`Dataset not found: ${datasetPath}`);
  }
  
  const content = fs.readFileSync(datasetPath, 'utf8');
  const lines = content.trim().split('\n');
  
  const queries: GoldenQueryV2[] = lines.map((line, index) => {
    try {
      const query = JSON.parse(line) as GoldenQueryV2;
      validateQuery(query, index + 1);
      return query;
    } catch (error) {
      throw new Error(`Failed to parse line ${index + 1}: ${error}`);
    }
  });
  
  return queries;
}

/**
 * Validate query structure
 */
function validateQuery(query: GoldenQueryV2, lineNumber: number): void {
  const required = ['id', 'query', 'type', 'difficulty', 'expected_notes', 'expected_confidence', 'expected_next_step'];
  
  for (const field of required) {
    if (!(field in query)) {
      throw new Error(`Line ${lineNumber}: Missing required field "${field}"`);
    }
  }
  
  // Validate enums
  if (!Object.values(QueryType).includes(query.type)) {
    throw new Error(`Line ${lineNumber}: Invalid type "${query.type}"`);
  }
  
  if (!Object.values(Difficulty).includes(query.difficulty)) {
    throw new Error(`Line ${lineNumber}: Invalid difficulty "${query.difficulty}"`);
  }
  
  if (!Object.values(Confidence).includes(query.expected_confidence)) {
    throw new Error(`Line ${lineNumber}: Invalid confidence "${query.expected_confidence}"`);
  }
  
  if (query.allowed_source_scope && !Object.values(SourceScope).includes(query.allowed_source_scope)) {
    throw new Error(`Line ${lineNumber}: Invalid source scope "${query.allowed_source_scope}"`);
  }
}

/**
 * Get dataset metadata
 */
export function getDatasetMetadata(queries: GoldenQueryV2[]): DatasetMetadata {
  const byType: Record<QueryType, number> = {
    [QueryType.TECHNICAL]: 0,
    [QueryType.PROJECT]: 0,
    [QueryType.RESEARCH]: 0,
    [QueryType.MAINTENANCE]: 0
  };
  
  const byDifficulty: Record<Difficulty, number> = {
    [Difficulty.EASY]: 0,
    [Difficulty.MEDIUM]: 0,
    [Difficulty.HARD]: 0
  };
  
  let noAnswerCount = 0;
  let conflictingCount = 0;
  
  queries.forEach(q => {
    byType[q.type]++;
    byDifficulty[q.difficulty]++;
    
    // Detect no-answer queries
    if (q.expected_confidence === Confidence.LOW && q.expected_notes.length === 0) {
      noAnswerCount++;
    }
    
    // Detect conflicting evidence (heuristic: "conflict" in answer outline)
    if (q.expected_answer_outline?.toLowerCase().includes('conflict')) {
      conflictingCount++;
    }
  });
  
  return {
    version: '2.0',
    created: new Date().toISOString(),
    total_queries: queries.length,
    by_type: byType,
    by_difficulty: byDifficulty,
    special_categories: {
      no_answer_queries: noAnswerCount,
      conflicting_evidence_queries: conflictingCount
    }
  };
}

/**
 * Filter queries by type
 */
export function getQueriesByType(queries: GoldenQueryV2[], type: QueryType): GoldenQueryV2[] {
  return queries.filter(q => q.type === type);
}

/**
 * Filter queries by difficulty
 */
export function getQueriesByDifficulty(queries: GoldenQueryV2[], difficulty: Difficulty): GoldenQueryV2[] {
  return queries.filter(q => q.difficulty === difficulty);
}

/**
 * Get no-answer queries
 */
export function getNoAnswerQueries(queries: GoldenQueryV2[]): GoldenQueryV2[] {
  return queries.filter(q => 
    q.expected_confidence === Confidence.LOW && 
    q.expected_notes.length === 0
  );
}

/**
 * Deduplicate queries using semantic similarity (placeholder)
 * In production, use actual embedding similarity
 */
export function deduplicateQueries(queries: GoldenQueryV2[], _threshold: number = 0.9): GoldenQueryV2[] {
  // Placeholder: Simple string similarity (threshold reserved for future use)
  const seen = new Set<string>();
  const unique: GoldenQueryV2[] = [];
  
  for (const query of queries) {
    const normalized = query.query.toLowerCase().trim();
    
    // Simple exact match check (in production, use embeddings)
    if (!seen.has(normalized)) {
      seen.add(normalized);
      unique.push(query);
    }
  }
  
  if (unique.length < queries.length) {
    console.warn(`⚠️ Removed ${queries.length - unique.length} duplicate queries`);
  }
  
  return unique;
}

/**
 * Check dataset balance
 */
export function checkDatasetBalance(queries: GoldenQueryV2[]): { balanced: boolean; issues: string[] } {
  const metadata = getDatasetMetadata(queries);
  const issues: string[] = [];
  
  // Check type balance (should be ~50 each for 200 total)
  const typeCounts = Object.values(metadata.by_type);
  const avgTypeCount = queries.length / 4;
  const typeVariance = Math.max(...typeCounts) - Math.min(...typeCounts);
  
  if (typeVariance > avgTypeCount * 0.3) {
    issues.push(`Unbalanced query types: ${JSON.stringify(metadata.by_type)}`);
  }
  
  // Check difficulty balance (should be ~30% easy, 45% medium, 25% hard)
  const easyPct = (metadata.by_difficulty[Difficulty.EASY] / queries.length) * 100;
  const mediumPct = (metadata.by_difficulty[Difficulty.MEDIUM] / queries.length) * 100;
  const hardPct = (metadata.by_difficulty[Difficulty.HARD] / queries.length) * 100;
  
  if (easyPct < 20 || easyPct > 45) {
    issues.push(`Easy queries out of range: ${easyPct.toFixed(1)}% (target 25-40%)`);
  }
  
  if (mediumPct < 35 || mediumPct > 60) {
    issues.push(`Medium queries out of range: ${mediumPct.toFixed(1)}% (target 40-55%)`);
  }
  
  if (hardPct < 15 || hardPct > 35) {
    issues.push(`Hard queries out of range: ${hardPct.toFixed(1)}% (target 20-30%)`);
  }
  
  // Check special categories
  if (metadata.special_categories.no_answer_queries < 15) {
    issues.push(`Insufficient no-answer queries: ${metadata.special_categories.no_answer_queries} (target >= 20)`);
  }
  
  return {
    balanced: issues.length === 0,
    issues
  };
}

// For backwards compatibility with old code
export type { GoldenQueryV2 as GoldenQuery };
export const GOLDEN_DATASET = loadDatasetV2();
