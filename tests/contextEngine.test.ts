/**
 * Test Suite for Intelligent Context Engine
 * Tests semantic clustering, context scoring, and adaptive context features
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { IntelligentContextEngine } from '../src/contextEngine';
import {
	createSampleResearchVault,
	createMockFile,
	assertTFIDFVector,
	assertClusterResults
} from './testUtils';

describe('IntelligentContextEngine', () => {
	let engine: IntelligentContextEngine;
	let vault: any;
	let metadataCache: any;

	beforeEach(() => {
		const sample = createSampleResearchVault();
		vault = sample.vault;
		metadataCache = sample.metadataCache;
		engine = new IntelligentContextEngine(vault, metadataCache);
	});

	describe('Semantic Clustering', () => {
		it('should build semantic clusters from vault', async () => {
			const clusters = await engine.buildSemanticClusters();
			
			assertClusterResults(clusters);
			
			// Should have multiple clusters
			expect(clusters.size).toBeGreaterThan(0);
			expect(clusters.size).toBeLessThanOrEqual(20); // MAX_CLUSTERS = 20
		});

		it('should assign notes to appropriate clusters', async () => {
			const clusters = await engine.buildSemanticClusters();
			
			// Find cluster containing AI-related notes
			let aiCluster = null;
			for (const cluster of clusters.values()) {
				const noteNames = cluster.notes.map((n: any) => n.basename);
				if (noteNames.some((name: string) => 
					name.includes('Neural') || name.includes('Machine')
				)) {
					aiCluster = cluster;
					break;
				}
			}
			
			expect(aiCluster).not.toBeNull();
			expect(aiCluster.notes.length).toBeGreaterThanOrEqual(3); // MIN_CLUSTER_SIZE
		});

		it('should extract meaningful keywords from clusters', async () => {
			const clusters = await engine.buildSemanticClusters();
			
			for (const cluster of clusters.values()) {
				expect(cluster.keywords).toBeDefined();
				expect(cluster.keywords.length).toBeGreaterThan(0);
				expect(cluster.keywords.length).toBeLessThanOrEqual(5);
				
				// Keywords should be lowercase strings
				for (const keyword of cluster.keywords) {
					expect(typeof keyword).toBe('string');
					expect(keyword).toBe(keyword.toLowerCase());
				}
			}
		});

		it('should detect cluster themes', async () => {
			const clusters = await engine.buildSemanticClusters();
			
			for (const cluster of clusters.values()) {
				expect(cluster.theme).toBeDefined();
				expect(typeof cluster.theme).toBe('string');
				expect(cluster.theme.length).toBeGreaterThan(0);
			}
		});
	});

	describe('Context Scoring', () => {
		it('should score note relevance for query', async () => {
			const files = vault.getMarkdownFiles();
			const testFile = files[0];
			
			const score = await engine.scoreNoteRelevance(
				testFile,
				'neural networks machine learning'
			);
			
			expect(score).toBeDefined();
			expect(score.file).toBe(testFile);
			expect(score.score).toBeGreaterThanOrEqual(0);
			expect(score.score).toBeLessThanOrEqual(100);
			expect(score.semanticScore).toBeGreaterThanOrEqual(0);
			expect(score.recencyScore).toBeGreaterThanOrEqual(0);
			expect(score.linkScore).toBeGreaterThanOrEqual(0);
		});

		it('should give higher semantic scores for relevant content', async () => {
			const files = vault.getMarkdownFiles();
			
			// Find neural networks note
			const nnFile = files.find((f: any) => f.basename === 'Neural Networks');
			expect(nnFile).toBeDefined();
			
			const relevantScore = await engine.scoreNoteRelevance(
				nnFile!,
				'neural networks deep learning'
			);
			
			// Should have high semantic relevance
			expect(relevantScore.semanticScore).toBeGreaterThan(30);
		});

		it('should give higher recency scores for recent notes', async () => {
			const now = Date.now();
			const recentFile = createMockFile('recent.md', 'content', { mtime: now - 1000 });
			const oldFile = createMockFile('old.md', 'content', { mtime: now - 86400000 * 60 });
			
			vault.getMarkdownFiles.mockReturnValue([recentFile, oldFile]);
			await engine['buildTFIDFCache']([recentFile, oldFile]);
			
			const recentScore = await engine.scoreNoteRelevance(recentFile, 'test');
			const oldScore = await engine.scoreNoteRelevance(oldFile, 'test');
			
			expect(recentScore.recencyScore).toBeGreaterThan(oldScore.recencyScore);
		});

		it('should provide reasoning for scores', async () => {
			const files = vault.getMarkdownFiles();
			const testFile = files[0];
			
			const score = await engine.scoreNoteRelevance(
				testFile,
				'neural networks'
			);
			
			expect(score.reasons).toBeDefined();
			expect(Array.isArray(score.reasons)).toBe(true);
		});
	});

	describe('Adaptive Context Windows', () => {
		it('should build adaptive context within token limits', async () => {
			const files = vault.getMarkdownFiles();
			const currentNote = files.find((f: any) => f.basename === 'Thesis Outline');
			expect(currentNote).toBeDefined();
			
			const context = await engine.getAdaptiveContext(
				currentNote!,
				'neural networks research',
				2000 // Max tokens
			);
			
			expect(context).toBeDefined();
			expect(context.primaryNote).toBe(currentNote);
			expect(context.relatedNotes).toBeDefined();
			expect(context.contextText).toBeDefined();
			expect(context.tokenEstimate).toBeLessThanOrEqual(2000);
		});

		it('should include most relevant notes in context', async () => {
			const files = vault.getMarkdownFiles();
			const currentNote = files[0];
			
			const context = await engine.getAdaptiveContext(
				currentNote,
				'neural networks',
				5000
			);
			
			expect(context.relatedNotes.length).toBeGreaterThan(0);
			
			// Related notes should be different from primary
			for (const note of context.relatedNotes) {
				expect(note.path).not.toBe(currentNote.path);
			}
		});

		it('should respect token limits strictly', async () => {
			const files = vault.getMarkdownFiles();
			const currentNote = files[0];
			
			const smallContext = await engine.getAdaptiveContext(
				currentNote,
				'machine learning',
				500 // Very small limit
			);
			
			expect(smallContext.tokenEstimate).toBeLessThanOrEqual(500);
		});

		it('should track which clusters are included', async () => {
			const files = vault.getMarkdownFiles();
			const currentNote = files[0];
			
			const context = await engine.getAdaptiveContext(
				currentNote,
				'neural networks',
				4000
			);
			
			expect(context.includedClusters).toBeDefined();
			expect(Array.isArray(context.includedClusters)).toBe(true);
		});
	});

	describe('Project Boundary Detection', () => {
		it('should detect projects from tags', async () => {
			const projects = await engine.detectProjectBoundaries();
			
			expect(projects).toBeDefined();
			expect(projects.size).toBeGreaterThan(0);
			
			// Should find project-thesis
			const thesisProject = Array.from(projects.values()).find(
				p => p.tags.includes('project-thesis')
			);
			expect(thesisProject).toBeDefined();
		});

		it('should detect projects from folders', async () => {
			const projects = await engine.detectProjectBoundaries();
			
			// Should have projects from folders with 5+ notes
			expect(projects.size).toBeGreaterThan(0);
		});

		it('should mark recent projects as active', async () => {
			const projects = await engine.detectProjectBoundaries();
			
			for (const project of projects.values()) {
				expect(project.isActive).toBeDefined();
				expect(typeof project.isActive).toBe('boolean');
			}
		});

		it('should track project metadata', async () => {
			const projects = await engine.detectProjectBoundaries();
			
			for (const project of projects.values()) {
				expect(project.name).toBeDefined();
				expect(project.notes).toBeDefined();
				expect(project.notes.length).toBeGreaterThan(0);
				expect(project.startDate).toBeDefined();
				expect(project.lastModified).toBeDefined();
			}
		});
	});

	describe('Cluster Relationships', () => {
		it('should find cluster mates for a note', async () => {
			const files = vault.getMarkdownFiles();
			const testNote = files.find((f: any) => f.basename === 'Neural Networks');
			expect(testNote).toBeDefined();
			
			const clusterMates = await engine.findClusterMates(testNote!);
			
			expect(clusterMates).toBeDefined();
			expect(Array.isArray(clusterMates)).toBe(true);
			
			// Should not include the test note itself
			for (const mate of clusterMates) {
				expect(mate.path).not.toBe(testNote!.path);
			}
		});

		it('should return empty array for unclustered notes', async () => {
			const isolatedFile = createMockFile('isolated.md', 'unique content xyz');
			vault.getMarkdownFiles.mockReturnValue([isolatedFile]);
			
			const clusterMates = await engine.findClusterMates(isolatedFile);
			
			expect(clusterMates).toBeDefined();
			expect(clusterMates.length).toBe(0);
		});

		it('should get cluster theme description', async () => {
			await engine.buildSemanticClusters();
			const clusters = await engine.buildSemanticClusters(); // Use cache
			
			const firstClusterId = Array.from(clusters.keys())[0];
			const theme = await engine.getClusterTheme(firstClusterId);
			
			expect(theme).toBeDefined();
			expect(typeof theme).toBe('string');
			expect(theme.length).toBeGreaterThan(0);
		});
	});

	describe('Cache Management', () => {
		it('should build and cache TF-IDF vectors', async () => {
			const files = vault.getMarkdownFiles();
			
			// First call builds cache
			await engine['buildTFIDFCache'](files);
			
			expect(engine['tfidfCache']).not.toBeNull();
			expect(engine['idfCache']).not.toBeNull();
			
			// Verify cache structure
			expect(engine['tfidfCache']!.size).toBeGreaterThan(0);
			expect(engine['idfCache']!.size).toBeGreaterThan(0);
		});

		it('should reuse cached clusters', async () => {
			// First call
			const clusters1 = await engine.buildSemanticClusters();
			
			// Second call should use cache
			const clusters2 = await engine.buildSemanticClusters();
			
			expect(clusters1).toBe(clusters2); // Same object reference
		});

		it('should clear all caches', async () => {
			const files = vault.getMarkdownFiles();
			await engine['buildTFIDFCache'](files);
			await engine.buildSemanticClusters();
			
			engine.clearCaches();
			
			expect(engine['tfidfCache']).toBeNull();
			expect(engine['idfCache']).toBeNull();
			expect(engine['clusterCache']).toBeNull();
			expect(engine['linkGraphCache']).toBeNull();
		});
	});

	describe('TF-IDF Implementation', () => {
		it('should compute valid TF-IDF vectors', async () => {
			const files = vault.getMarkdownFiles();
			await engine['buildTFIDFCache'](files);
			
			const firstFile = files[0];
			const vector = engine['tfidfCache']!.get(firstFile.path);
			
			assertTFIDFVector(vector);
		});

		it('should filter stop words', async () => {
			const testContent = 'this is a test with some common words that should be filtered';
			const terms = engine['extractTerms'](testContent);
			
			// Should not contain common stop words
			expect(terms).not.toContain('this');
			expect(terms).not.toContain('that');
			expect(terms).not.toContain('with');
		});

		it('should calculate cosine similarity correctly', () => {
			const vec1 = new Map([['neural', 2.5], ['network', 1.8]]);
			const vec2 = new Map([['neural', 2.0], ['network', 2.0]]);
			
			const similarity = engine['cosineSimilarity'](vec1, vec2);
			
			expect(similarity).toBeGreaterThan(0);
			expect(similarity).toBeLessThanOrEqual(1);
		});

		it('should return 0 similarity for empty vectors', () => {
			const vec1 = new Map();
			const vec2 = new Map([['test', 1]]);
			
			const similarity = engine['cosineSimilarity'](vec1, vec2);
			
			expect(similarity).toBe(0);
		});
	});

	describe('Link Graph Analysis', () => {
		it('should build link graph from metadata', () => {
			engine['buildLinkGraph']();
			
			expect(engine['linkGraphCache']).not.toBeNull();
			expect(engine['linkGraphCache']!.size).toBeGreaterThan(0);
		});

		it('should compute link distances via BFS', () => {
			const files = vault.getMarkdownFiles();
			const file1 = files.find((f: any) => f.basename === 'Thesis Outline');
			const file2 = files.find((f: any) => f.basename === 'Literature Review');
			
			if (file1 && file2) {
				const distance = engine['computeLinkDistance'](file1, file2);
				
				expect(distance).toBeGreaterThanOrEqual(0);
				expect(distance).toBeLessThanOrEqual(3); // MAX_LINK_DISTANCE
			}
		});
	});
});
