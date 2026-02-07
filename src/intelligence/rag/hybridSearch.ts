/**
 * Hybrid Search - Combines keyword, semantic, and graph-based retrieval
 */

export interface SearchResult {
note_path: string;
content: string;
score: number;
match_type: 'keyword' | 'semantic' | 'graph' | 'hybrid';
metadata?: {
created?: number;
modified?: number;
links?: number;
backlinks?: number;
};
}

export interface HybridSearchConfig {
keyword_weight: number;      // 0-1: Weight for keyword matches
semantic_weight: number;      // 0-1: Weight for semantic similarity
graph_weight: number;         // 0-1: Weight for graph connections
freshness_boost: number;      // Boost factor for recent content
authority_boost: number;      // Boost factor for highly linked content
max_results: number;          // Maximum results to return
}

export class HybridSearch {
private config: HybridSearchConfig;

constructor(config?: Partial<HybridSearchConfig>) {
this.config = {
keyword_weight: 0.3,
semantic_weight: 0.5,
graph_weight: 0.2,
freshness_boost: 0.1,
authority_boost: 0.15,
max_results: 10,
...config
};
}

/**
 * Perform hybrid search combining multiple strategies
 */
async search(
query: string,
keywordSearch: (q: string) => Promise<SearchResult[]>,
semanticSearch: (q: string) => Promise<SearchResult[]>,
graphSearch?: (q: string) => Promise<SearchResult[]>
): Promise<SearchResult[]> {
// Run all search strategies in parallel
const [keywordResults, semanticResults, graphResults] = await Promise.all([
keywordSearch(query),
semanticSearch(query),
graphSearch ? graphSearch(query) : Promise.resolve([])
]);

// Combine and rerank results
const combined = this.combineResults(keywordResults, semanticResults, graphResults);
const reranked = this.rerank(combined, query);
const boosted = this.applyBoosts(reranked);

// Return top results
return boosted.slice(0, this.config.max_results);
}

/**
 * Combine results from different search strategies
 */
private combineResults(
keyword: SearchResult[],
semantic: SearchResult[],
graph: SearchResult[]
): SearchResult[] {
const resultMap = new Map<string, SearchResult>();

// Add keyword results
for (const result of keyword) {
resultMap.set(result.note_path, {
...result,
score: result.score * this.config.keyword_weight,
match_type: 'keyword'
});
}

// Add semantic results (merge if exists)
for (const result of semantic) {
const existing = resultMap.get(result.note_path);
if (existing) {
existing.score += result.score * this.config.semantic_weight;
existing.match_type = 'hybrid';
} else {
resultMap.set(result.note_path, {
...result,
score: result.score * this.config.semantic_weight,
match_type: 'semantic'
});
}
}

// Add graph results (merge if exists)
for (const result of graph) {
const existing = resultMap.get(result.note_path);
if (existing) {
existing.score += result.score * this.config.graph_weight;
existing.match_type = 'hybrid';
} else {
resultMap.set(result.note_path, {
...result,
score: result.score * this.config.graph_weight,
match_type: 'graph'
});
}
}

return Array.from(resultMap.values());
}

/**
 * Rerank results for better relevance
 */
private rerank(results: SearchResult[], query: string): SearchResult[] {
const queryTerms = query.toLowerCase().split(/\s+/);

return results.map(result => {
let rerankScore = result.score;

// Boost if query terms appear in note path
const pathLower = result.note_path.toLowerCase();
for (const term of queryTerms) {
if (pathLower.includes(term)) {
rerankScore *= 1.2;
}
}

// Boost if content has high keyword density
const contentLower = result.content.toLowerCase();
let termMatches = 0;
for (const term of queryTerms) {
const matches = (contentLower.match(new RegExp(term, 'g')) || []).length;
termMatches += matches;
}

if (termMatches > 5) {
rerankScore *= 1.15;
}

return {
...result,
score: rerankScore
};
}).sort((a, b) => b.score - a.score);
}

/**
 * Apply freshness and authority boosts
 */
private applyBoosts(results: SearchResult[]): SearchResult[] {
const now = Date.now();
const oneMonth = 30 * 24 * 60 * 60 * 1000;

return results.map(result => {
let boostedScore = result.score;

// Freshness boost
if (result.metadata?.modified) {
const age = now - result.metadata.modified;
if (age < oneMonth) {
const freshnessMultiplier = 1 + (this.config.freshness_boost * (1 - age / oneMonth));
boostedScore *= freshnessMultiplier;
}
}

// Authority boost (based on link count)
if (result.metadata?.links || result.metadata?.backlinks) {
const linkCount = (result.metadata.links || 0) + (result.metadata.backlinks || 0);
if (linkCount > 5) {
const authorityMultiplier = 1 + (this.config.authority_boost * Math.min(linkCount / 10, 1));
boostedScore *= authorityMultiplier;
}
}

return {
...result,
score: boostedScore
};
}).sort((a, b) => b.score - a.score);
}

/**
 * Extract context around match
 */
extractContext(content: string, query: string, contextSize: number = 200): string {
const queryTerms = query.toLowerCase().split(/\s+/);
const contentLower = content.toLowerCase();

// Find best match position
let bestPosition = 0;
let maxMatches = 0;

for (let i = 0; i < content.length - contextSize; i += 50) {
const window = contentLower.substring(i, i + contextSize);
let matches = 0;
for (const term of queryTerms) {
if (window.includes(term)) matches++;
}
if (matches > maxMatches) {
maxMatches = matches;
bestPosition = i;
}
}

// Extract context
let start = Math.max(0, bestPosition - contextSize / 2);
let end = Math.min(content.length, bestPosition + contextSize * 1.5);

let context = content.substring(start, end);

// Add ellipsis if truncated
if (start > 0) context = '...' + context;
if (end < content.length) context = context + '...';

return context.trim();
}

/**
 * Highlight query terms in result
 */
highlightTerms(text: string, query: string): string {
const queryTerms = query.toLowerCase().split(/\s+/);
let highlighted = text;

for (const term of queryTerms) {
if (term.length < 3) continue; // Skip very short terms
const regex = new RegExp(`\\b(${term})\\b`, 'gi');
highlighted = highlighted.replace(regex, '**$1**');
}

return highlighted;
}
}
