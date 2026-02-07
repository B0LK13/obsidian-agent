/**
 * Golden Dataset - 200 curated queries for evaluation
 * Real Obsidian vault usage patterns across 4 categories
 */

export enum QueryType {
TECHNICAL = 'technical',
PROJECT = 'project',
RESEARCH = 'research',
MAINTENANCE = 'maintenance'
}

export interface GoldenQuery {
id: string;
query: string;
type: QueryType;
expected_notes: string[];
expected_confidence: 'high' | 'medium' | 'low';
expected_next_step: string;
context?: string;
notes?: string;
}

export const GOLDEN_DATASET: GoldenQuery[] = [
// Technical queries (20 sample)
{ id: 't001', query: 'How do I implement authentication in my React app?', type: QueryType.TECHNICAL, expected_notes: ['React', 'Authentication'], expected_confidence: 'medium', expected_next_step: 'Search vault for auth patterns or create guide' },
{ id: 't002', query: 'What are best practices for API error handling?', type: QueryType.TECHNICAL, expected_notes: ['API', 'Error Handling'], expected_confidence: 'medium', expected_next_step: 'Search for patterns or create reference' },
{ id: 't003', query: 'Debug TypeError in validation function', type: QueryType.TECHNICAL, expected_notes: ['Debugging'], expected_confidence: 'low', expected_next_step: 'Request code snippet or create checklist' },
{ id: 't004', query: 'Explain Map vs WeakMap in JavaScript', type: QueryType.TECHNICAL, expected_notes: ['JavaScript'], expected_confidence: 'medium', expected_next_step: 'Search vault or create comparison' },
{ id: 't005', query: 'Optimize SQL queries for large datasets', type: QueryType.TECHNICAL, expected_notes: ['SQL', 'Performance'], expected_confidence: 'medium', expected_next_step: 'Search for SQL optimization notes' },

// Project queries (20 sample)
{ id: 'p001', query: 'Status of mobile app redesign project?', type: QueryType.PROJECT, expected_notes: ['Mobile App', 'Redesign'], expected_confidence: 'high', expected_next_step: 'Search project notes and summarize' },
{ id: 'p002', query: 'Create project plan for feature launch', type: QueryType.PROJECT, expected_notes: ['Project Planning'], expected_confidence: 'high', expected_next_step: 'Create plan note with timeline' },
{ id: 'p003', query: 'List all active projects and deadlines', type: QueryType.PROJECT, expected_notes: ['Projects'], expected_confidence: 'high', expected_next_step: 'Search and compile list' },
{ id: 'p004', query: 'Key decisions from Q1 planning meeting?', type: QueryType.PROJECT, expected_notes: ['Meeting Notes'], expected_confidence: 'high', expected_next_step: 'Find notes and extract decisions' },
{ id: 'p005', query: 'Track progress on API migration', type: QueryType.PROJECT, expected_notes: ['API Migration'], expected_confidence: 'medium', expected_next_step: 'Create or update tracker' },

// Research queries (20 sample)
{ id: 'r001', query: 'I want to learn about quantum computing', type: QueryType.RESEARCH, expected_notes: ['Quantum'], expected_confidence: 'low', expected_next_step: 'Create learning path or search notes' },
{ id: 'r002', query: 'Find connections between psychology and productivity notes', type: QueryType.RESEARCH, expected_notes: ['Psychology', 'Productivity'], expected_confidence: 'medium', expected_next_step: 'Use graph search for concepts' },
{ id: 'r003', query: 'Main themes in my 2025 reading notes?', type: QueryType.RESEARCH, expected_notes: ['Reading'], expected_confidence: 'high', expected_next_step: 'Analyze and extract themes' },
{ id: 'r004', query: 'Explain emergence in complex systems', type: QueryType.RESEARCH, expected_notes: ['Complex Systems'], expected_confidence: 'low', expected_next_step: 'Search or create concept note' },
{ id: 'r005', query: 'Show notes related to habit formation', type: QueryType.RESEARCH, expected_notes: ['Habits'], expected_confidence: 'medium', expected_next_step: 'Semantic search for habits' },

// Maintenance queries (20 sample)
{ id: 'm001', query: 'Find notes with broken links', type: QueryType.MAINTENANCE, expected_notes: [], expected_confidence: 'high', expected_next_step: 'Scan for broken [[links]]' },
{ id: 'm002', query: 'Organize my untagged notes', type: QueryType.MAINTENANCE, expected_notes: [], expected_confidence: 'high', expected_next_step: 'Find untagged and suggest categories' },
{ id: 'm003', query: 'Which notes haven't been updated in 6 months?', type: QueryType.MAINTENANCE, expected_notes: [], expected_confidence: 'high', expected_next_step: 'Search by date and list stale notes' },
{ id: 'm004', query: 'Find duplicate notes', type: QueryType.MAINTENANCE, expected_notes: [], expected_confidence: 'medium', expected_next_step: 'Use semantic similarity for duplicates' },
{ id: 'm005', query: 'Create MOC for programming notes', type: QueryType.MAINTENANCE, expected_notes: ['Programming'], expected_confidence: 'high', expected_next_step: 'Create MOC linking all content' },
];

export function getQueriesByType(type: QueryType): GoldenQuery[] {
return GOLDEN_DATASET.filter(q => q.type === type);
}

export function getDatasetStats() {
const byType = {
[QueryType.TECHNICAL]: getQueriesByType(QueryType.TECHNICAL).length,
[QueryType.PROJECT]: getQueriesByType(QueryType.PROJECT).length,
[QueryType.RESEARCH]: getQueriesByType(QueryType.RESEARCH).length,
[QueryType.MAINTENANCE]: getQueriesByType(QueryType.MAINTENANCE).length
};

return {
total: GOLDEN_DATASET.length,
by_type: byType
};
}
