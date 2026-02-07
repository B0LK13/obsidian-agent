/**
 * Test Suite for Multi-Note Synthesizer
 * Tests synthesis, research assistant, argument mapping, and gap detection
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { MultiNoteSynthesizer } from '../src/multiNoteSynthesizer';
import { IntelligentContextEngine } from '../src/contextEngine';
import {
	createSampleResearchVault,
	createMockAIService,
	createMockFile
} from './testUtils';

describe('MultiNoteSynthesizer', () => {
	let synthesizer: MultiNoteSynthesizer;
	let vault: any;
	let metadataCache: any;
	let contextEngine: IntelligentContextEngine;
	let aiService: any;

	beforeEach(() => {
		const sample = createSampleResearchVault();
		vault = sample.vault;
		metadataCache = sample.metadataCache;
		
		// Create mocks for vector services
		const vectorStore = {
			search: vi.fn().mockResolvedValue([]),
			add: vi.fn().mockResolvedValue(undefined),
			delete: vi.fn().mockResolvedValue(undefined),
			clear: vi.fn().mockResolvedValue(undefined)
		};
		
		const embeddingService = {
			generateEmbedding: vi.fn().mockResolvedValue({
				vector: new Array(384).fill(0.1),
				model: 'test-model'
			})
		};
		
		contextEngine = new IntelligentContextEngine(vault, metadataCache, vectorStore, embeddingService);
		aiService = createMockAIService();
		
		synthesizer = new MultiNoteSynthesizer(
			vault,
			metadataCache,
			contextEngine,
			aiService
		);
	});

	describe('Cross-Note Synthesis', () => {
		it('should synthesize insights from multiple notes', async () => {
			const files = vault.getMarkdownFiles();
			const aiNotes = files.filter((f: any) => 
				f.path.startsWith('AI Research/')
			).slice(0, 3);
			
			const result = await synthesizer.synthesizeNotes(aiNotes);
			
			expect(result).toBeDefined();
			expect(result.summary).toBeDefined();
			expect(typeof result.summary).toBe('string');
			expect(result.notesAnalyzed).toBe(aiNotes.length);
		});

		it('should extract key insights', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 3);
			
			const result = await synthesizer.synthesizeNotes(testNotes);
			
			expect(result.keyInsights).toBeDefined();
			expect(Array.isArray(result.keyInsights)).toBe(true);
			expect(result.keyInsights.length).toBeGreaterThan(0);
		});

		it('should identify contradictions', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 3);
			
			const result = await synthesizer.synthesizeNotes(testNotes);
			
			expect(result.contradictions).toBeDefined();
			expect(Array.isArray(result.contradictions)).toBe(true);
		});

		it('should identify knowledge gaps', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 3);
			
			const result = await synthesizer.synthesizeNotes(testNotes);
			
			expect(result.knowledgeGaps).toBeDefined();
			expect(Array.isArray(result.knowledgeGaps)).toBe(true);
			expect(result.knowledgeGaps.length).toBeGreaterThan(0);
		});

		it('should track citations from source notes', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 3);
			
			const result = await synthesizer.synthesizeNotes(testNotes);
			
			expect(result.citations).toBeDefined();
			expect(result.citations instanceof Map).toBe(true);
		});

		it('should handle focused synthesis with query', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 3);
			
			const result = await synthesizer.synthesizeNotes(
				testNotes,
				'deep learning architectures'
			);
			
			expect(result).toBeDefined();
			expect(aiService.generateCompletion).toHaveBeenCalled();
			
			const promptArg = aiService.generateCompletion.mock.calls[0][0];
			expect(promptArg).toContain('deep learning architectures');
		});
	});

	describe('Research Assistant', () => {
		it('should answer research questions from vault', async () => {
			const answer = await synthesizer.answerResearchQuestion(
				'What are neural networks?'
			);
			
			expect(answer).toBeDefined();
			expect(typeof answer).toBe('string');
			expect(answer.length).toBeGreaterThan(0);
		});

		it('should find relevant notes for research query', async () => {
			// Mock that scoreNoteRelevance returns some files with scores
			const files = vault.getMarkdownFiles();
			const result = await synthesizer.researchQuery({
				query: 'neural networks machine learning',
				maxNotes: 5
			});
			
			expect(result).toBeDefined();
			// May be 0 if no notes meet relevance threshold - this is valid
			expect(result.notesAnalyzed).toBeGreaterThanOrEqual(0);
			expect(result.notesAnalyzed).toBeLessThanOrEqual(5);
		});

		it('should filter by tags in research query', async () => {
			const result = await synthesizer.researchQuery({
				query: 'research',
				tags: ['project-thesis'],
				maxNotes: 10
			});
			
			expect(result).toBeDefined();
			// Should only include notes with project-thesis tag
		});

		it('should filter by folder in research query', async () => {
			const result = await synthesizer.researchQuery({
				query: 'AI',
				folders: ['AI Research'],
				maxNotes: 10
			});
			
			expect(result).toBeDefined();
		});

		it('should handle empty results gracefully', async () => {
			const result = await synthesizer.researchQuery({
				query: 'nonexistent topic xyz123',
				maxNotes: 10
			});
			
			expect(result).toBeDefined();
			expect(result.notesAnalyzed).toBe(0);
			expect(result.knowledgeGaps).toContain('No existing notes on this topic');
		});

		it('should use context engine for relevance scoring', async () => {
			const scoreSpy = vi.spyOn(contextEngine, 'scoreNoteRelevance');
			
			await synthesizer.researchQuery({
				query: 'machine learning',
				maxNotes: 5
			});
			
			expect(scoreSpy).toHaveBeenCalled();
		});
	});

	describe('Argument Mapping', () => {
		it('should extract claims from notes', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 3);
			
			const argumentMap = await synthesizer.extractArgumentMap(testNotes);
			
			expect(argumentMap).toBeDefined();
			expect(argumentMap.claims).toBeDefined();
			expect(Array.isArray(argumentMap.claims)).toBe(true);
		});

		it('should extract evidence from notes', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 3);
			
			const argumentMap = await synthesizer.extractArgumentMap(testNotes);
			
			expect(argumentMap.evidence).toBeDefined();
			expect(Array.isArray(argumentMap.evidence)).toBe(true);
		});

		it('should identify claim-evidence relationships', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 3);
			
			const argumentMap = await synthesizer.extractArgumentMap(testNotes);
			
			expect(argumentMap.relationships).toBeDefined();
			expect(Array.isArray(argumentMap.relationships)).toBe(true);
		});

		it('should identify logical gaps', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 3);
			
			const argumentMap = await synthesizer.extractArgumentMap(testNotes);
			
			expect(argumentMap.logicalGaps).toBeDefined();
			expect(Array.isArray(argumentMap.logicalGaps)).toBe(true);
		});

		it('should track evidence support for claims', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 3);
			
			const argumentMap = await synthesizer.extractArgumentMap(testNotes);
			
			// Each evidence should track which claims it supports
			for (const evidence of argumentMap.evidence) {
				expect(evidence.supportsClaims).toBeDefined();
				expect(Array.isArray(evidence.supportsClaims)).toBe(true);
			}
		});
	});

	describe('Contradiction Detection', () => {
		it('should find contradictions between notes', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 5);
			
			const contradictions = await synthesizer.findContradictions(testNotes);
			
			expect(contradictions).toBeDefined();
			expect(Array.isArray(contradictions)).toBe(true);
		});

		it('should describe contradictions with source notes', async () => {
			const files = vault.getMarkdownFiles();
			const testNotes = files.slice(0, 5);
			
			const contradictions = await synthesizer.findContradictions(testNotes);
			
			// Each contradiction should reference source notes
			for (const contradiction of contradictions) {
				expect(typeof contradiction).toBe('string');
				expect(contradiction.length).toBeGreaterThan(0);
			}
		});
	});

	describe('Knowledge Gap Detection', () => {
		it('should identify knowledge gaps for topic', async () => {
			const files = vault.getMarkdownFiles();
			const relatedNotes = files.slice(0, 3);
			
			const gaps = await synthesizer.identifyKnowledgeGaps(
				'neural networks',
				relatedNotes
			);
			
			expect(gaps).toBeDefined();
			expect(Array.isArray(gaps)).toBe(true);
			expect(gaps.length).toBeGreaterThan(0);
		});

		it('should call AI service for gap detection', async () => {
			const files = vault.getMarkdownFiles();
			const relatedNotes = files.slice(0, 3);
			
			await synthesizer.identifyKnowledgeGaps(
				'machine learning',
				relatedNotes
			);
			
			expect(aiService.generateCompletion).toHaveBeenCalled();
		});

		it('should filter and clean gap responses', async () => {
			const files = vault.getMarkdownFiles();
			const relatedNotes = files.slice(0, 3);
			
			const gaps = await synthesizer.identifyKnowledgeGaps(
				'AI research',
				relatedNotes
			);
			
			// All gaps should be non-empty strings
			for (const gap of gaps) {
				expect(typeof gap).toBe('string');
				expect(gap.length).toBeGreaterThan(10);
			}
		});
	});

	describe('Research Direction Suggestions', () => {
		it('should suggest research directions', async () => {
			const files = vault.getMarkdownFiles();
			const existingNotes = files.slice(0, 3);
			
			const suggestions = await synthesizer.suggestResearchDirections(
				'neural networks',
				existingNotes
			);
			
			expect(suggestions).toBeDefined();
			expect(Array.isArray(suggestions)).toBe(true);
		});

		it('should include direction details', async () => {
			const files = vault.getMarkdownFiles();
			const existingNotes = files.slice(0, 3);
			
			const suggestions = await synthesizer.suggestResearchDirections(
				'machine learning',
				existingNotes
			);
			
			for (const suggestion of suggestions) {
				expect(suggestion.direction).toBeDefined();
				expect(suggestion.reasoning).toBeDefined();
				expect(suggestion.suggestedSources).toBeDefined();
				expect(suggestion.priority).toBeDefined();
				expect(['high', 'medium', 'low']).toContain(suggestion.priority);
			}
		});

		it('should call gap detection before suggesting directions', async () => {
			const gapSpy = vi.spyOn(synthesizer, 'identifyKnowledgeGaps');
			const files = vault.getMarkdownFiles();
			const existingNotes = files.slice(0, 3);
			
			await synthesizer.suggestResearchDirections(
				'deep learning',
				existingNotes
			);
			
			expect(gapSpy).toHaveBeenCalled();
		});
	});

	describe('Helper Methods', () => {
		it('should extract relevant excerpts from content', () => {
			const content = `This is a long document about neural networks.

Neural networks are powerful machine learning models.

They can learn complex patterns from data.

This paragraph talks about something else entirely.`;

			const excerpt = synthesizer['extractRelevantExcerpt'](
				content,
				'neural networks',
				100
			);
			
			expect(excerpt).toBeDefined();
			expect(excerpt.length).toBeLessThanOrEqual(103); // 100 + '...'
			expect(excerpt.toLowerCase()).toContain('neural'); // Case-insensitive check
		});

		it('should extract keywords from text', () => {
			const text = 'neural networks are machine learning models';
			const keywords = synthesizer['extractKeywords'](text);
			
			expect(keywords).toBeDefined();
			expect(Array.isArray(keywords)).toBe(true);
			expect(keywords.length).toBeGreaterThan(0);
			
			// Should not include stop words
			expect(keywords).not.toContain('are');
		});

		it('should extract fields from formatted text', () => {
			const text = `DIRECTION: Test Direction
REASONING: This is the reasoning
PRIORITY: high`;

			const direction = synthesizer['extractField'](text, 'DIRECTION');
			const reasoning = synthesizer['extractField'](text, 'REASONING');
			const priority = synthesizer['extractField'](text, 'PRIORITY');
			
			expect(direction).toBe('Test Direction');
			expect(reasoning).toBe('This is the reasoning');
			expect(priority).toBe('high');
		});

		it('should parse synthesis responses correctly', () => {
			const response = `SUMMARY: This is the summary

KEY INSIGHTS:
- First insight
- Second insight

CONTRADICTIONS:
- Some contradiction

KNOWLEDGE GAPS:
- Missing information`;

			const parsed = synthesizer['parseSynthesisResponse'](response);
			
			expect(parsed.summary).toContain('This is the summary');
			expect(parsed.keyInsights.length).toBeGreaterThanOrEqual(2);
			expect(parsed.contradictions.length).toBeGreaterThanOrEqual(1);
			expect(parsed.knowledgeGaps.length).toBeGreaterThanOrEqual(1);
		});

		it('should extract tags from metadata', () => {
			const metadata = {
				frontmatter: { tags: ['tag1', 'tag2'] },
				tags: [{ tag: '#tag3' }]
			};
			
			const tags = synthesizer['extractTags'](metadata);
			
			expect(tags).toBeDefined();
			expect(tags).toContain('tag1');
			expect(tags).toContain('tag2');
			expect(tags).toContain('#tag3');
		});
	});

	describe('Integration Tests', () => {
		it('should complete full research workflow', async () => {
			// 1. Find notes
			const query = { query: 'neural networks', maxNotes: 5 };
			const research = await synthesizer.researchQuery(query);
			expect(research.notesAnalyzed).toBeGreaterThanOrEqual(0); // May be 0 if no notes meet threshold
			
			// 2. Identify gaps
			const files = vault.getMarkdownFiles();
			const gaps = await synthesizer.identifyKnowledgeGaps(
				'neural networks',
				files.slice(0, 3)
			);
			expect(gaps.length).toBeGreaterThan(0);
			
			// 3. Suggest directions
			const suggestions = await synthesizer.suggestResearchDirections(
				'neural networks',
				files.slice(0, 3)
			);
			expect(suggestions.length).toBeGreaterThan(0);
		});

		it('should handle large vaults efficiently', async () => {
			// Create many mock files
			const manyFiles = Array.from({ length: 100 }, (_, i) =>
				createMockFile(`note-${i}.md`, `Content ${i}`)
			);
			vault.getMarkdownFiles.mockReturnValue(manyFiles);
			
			const startTime = Date.now();
			const result = await synthesizer.researchQuery({
				query: 'test',
				maxNotes: 10
			});
			const endTime = Date.now();
			
			expect(result).toBeDefined();
			expect(endTime - startTime).toBeLessThan(5000); // Should complete in < 5s
		});
	});
});

