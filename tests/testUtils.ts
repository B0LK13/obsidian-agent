/**
 * Test Utilities and Mocks
 * Shared utilities for testing Context Engine and Multi-Note features
 */

import { TFile, Vault, MetadataCache, CachedMetadata } from 'obsidian';
import { vi } from 'vitest';

/**
 * Create mock TFile
 */
export function createMockFile(
	path: string,
	content: string = '',
	options: {
		ctime?: number;
		mtime?: number;
		size?: number;
	} = {}
): TFile {
	const now = Date.now();
	const file = {
		path,
		name: path.split('/').pop() || path,
		basename: path.split('/').pop()?.replace(/\.md$/, '') || path,
		extension: 'md',
		parent: {
			path: path.split('/').slice(0, -1).join('/') || '',
			name: path.split('/').slice(0, -1).pop() || ''
		},
		stat: {
			ctime: options.ctime || now - 86400000, // 1 day ago
			mtime: options.mtime || now - 3600000, // 1 hour ago
			size: options.size || content.length
		},
		vault: null as any
	} as TFile;

	return file;
}

/**
 * Create mock Vault with test files
 */
export function createMockVault(files: Map<string, string>): Vault {
	const fileObjects = new Map<string, TFile>();
	
	for (const [path, content] of files) {
		fileObjects.set(path, createMockFile(path, content));
	}

	const vault = {
		getMarkdownFiles: vi.fn(() => Array.from(fileObjects.values())),
		read: vi.fn(async (file: TFile) => files.get(file.path) || ''),
		create: vi.fn(async (path: string, content: string) => {
			files.set(path, content);
			const file = createMockFile(path, content);
			fileObjects.set(path, file);
			return file;
		}),
		getAbstractFileByPath: vi.fn((path: string) => fileObjects.get(path) || null)
	} as unknown as Vault;

	return vault;
}

/**
 * Create mock MetadataCache
 */
export function createMockMetadataCache(
	metadata: Map<string, Partial<CachedMetadata>>
): MetadataCache {
	const cache = {
		getFileCache: vi.fn((file: TFile) => {
			return metadata.get(file.path) || null;
		}),
		getFirstLinkpathDest: vi.fn((linkpath: string, sourcePath: string) => {
			// Simple mock: return file if it exists in metadata
			for (const [path] of metadata) {
				if (path.includes(linkpath)) {
					return createMockFile(path);
				}
			}
			return null;
		})
	} as unknown as MetadataCache;

	return cache;
}

/**
 * Create sample research vault for testing
 */
export function createSampleResearchVault(): {
	files: Map<string, string>;
	vault: Vault;
	metadataCache: MetadataCache;
} {
	const files = new Map<string, string>([
		// AI Research Notes
		['AI Research/Neural Networks.md', `# Neural Networks

Neural networks are computational models inspired by biological neurons. They consist of interconnected nodes that process information through weighted connections.

## Key Concepts
- Backpropagation for training
- Activation functions (ReLU, sigmoid)
- Deep learning architectures

Recent research shows neural networks excel at pattern recognition tasks.`],

		['AI Research/Machine Learning.md', `# Machine Learning

Machine learning enables computers to learn from data without explicit programming.

## Types
- Supervised learning
- Unsupervised learning  
- Reinforcement learning

According to recent studies, machine learning is transforming industries worldwide.`],

		['AI Research/Deep Learning.md', `# Deep Learning

Deep learning uses multi-layer neural networks for complex pattern recognition.

## Applications
- Computer vision
- Natural language processing
- Speech recognition

Deep learning requires significant computational resources but produces state-of-the-art results.`],

		// Project Notes
		['Projects/Thesis Outline.md', `# Thesis Outline

## Research Question
How do neural networks improve natural language understanding?

## Chapters
1. Introduction
2. Literature Review
3. Methodology
4. Results
5. Conclusion

#project-thesis #research`],

		['Projects/Literature Review.md', `# Literature Review

## Key Papers
- Attention is All You Need (Vaswani et al., 2017)
- BERT: Pre-training of Deep Bidirectional Transformers (Devlin et al., 2018)

These papers demonstrate the power of transformer architectures.

#project-thesis #literature`],

		// Random Notes
		['Daily Notes/2026-01-15.md', `# Daily Notes 2026-01-15

Worked on neural network implementation today. Made good progress on backpropagation algorithm.

Need to review attention mechanisms tomorrow.`],

		['Daily Notes/2026-02-01.md', `# Daily Notes 2026-02-01

Started writing thesis introduction. Outlined key research questions about neural networks and NLP.

Meeting with advisor scheduled for next week.`],

		// Related but different topic
		['Misc/Quantum Computing.md', `# Quantum Computing

Quantum computers use quantum bits (qubits) for computation.

## Principles
- Superposition
- Entanglement
- Quantum gates

Quantum computing may revolutionize cryptography and optimization problems.`],

		// Similar content (for duplicate testing)
		['Duplicates/Neural Nets Copy.md', `# Neural Networks

Neural networks are computational models inspired by biological neurons. They consist of interconnected nodes that process information through weighted connections.

## Key Concepts
- Backpropagation for training
- Activation functions (ReLU, sigmoid)  
- Deep learning architectures

Recent research shows neural networks excel at pattern recognition tasks.`],

		['Duplicates/ML Overview.md', `# Machine Learning Overview

Machine learning allows computers to learn from data without being explicitly programmed.

Types include supervised, unsupervised, and reinforcement learning.

Studies show ML is transforming many industries.`]
	]);

	const metadata = new Map<string, Partial<CachedMetadata>>([
		['Projects/Thesis Outline.md', {
			frontmatter: { tags: ['project-thesis', 'research'] },
			links: [
				{ link: 'Literature Review', original: '[[Literature Review]]', position: { start: { line: 0, col: 0, offset: 0 }, end: { line: 0, col: 0, offset: 0 } } },
				{ link: 'Neural Networks', original: '[[Neural Networks]]', position: { start: { line: 0, col: 0, offset: 0 }, end: { line: 0, col: 0, offset: 0 } } }
			]
		}],
		['Projects/Literature Review.md', {
			frontmatter: { tags: ['project-thesis', 'literature'] },
			links: [
				{ link: 'Deep Learning', original: '[[Deep Learning]]', position: { start: { line: 0, col: 0, offset: 0 }, end: { line: 0, col: 0, offset: 0 } } }
			]
		}],
		['AI Research/Neural Networks.md', {
			tags: [{ tag: '#ai', position: { start: { line: 0, col: 0, offset: 0 }, end: { line: 0, col: 0, offset: 0 } } }]
		}]
	]);

	const vault = createMockVault(files);
	const metadataCache = createMockMetadataCache(metadata);

	return { files, vault, metadataCache };
}

/**
 * Mock AIService for testing
 */
export function createMockAIService() {
	return {
		generateCompletion: vi.fn(async (prompt: string) => {
			// Return mock responses based on prompt content
			if (prompt.includes('SUMMARY')) {
				return {
					text: `SUMMARY: This research covers neural networks, machine learning, and deep learning.

KEY INSIGHTS:
- Neural networks excel at pattern recognition
- Deep learning requires significant resources
- Transformer architectures are state-of-the-art

CONTRADICTIONS:
None found.

KNOWLEDGE GAPS:
- What are the computational costs of large models?
- How do transformers compare to CNNs for vision tasks?`,
					tokensUsed: 150
				};
			}

			if (prompt.includes('knowledge gaps')) {
				return {
					text: `1. What are the limitations of current neural network architectures?
2. How can we reduce the computational costs of deep learning?
3. What ethical considerations arise from AI deployment?
4. How do different activation functions affect performance?
5. What is the future of quantum machine learning?`,
					tokensUsed: 100
				};
			}

			if (prompt.includes('research directions')) {
				return {
					text: `DIRECTION: Efficient Neural Architectures
REASONING: Reducing computational costs while maintaining performance is crucial for widespread adoption
SOURCES: Recent papers on MobileNet, EfficientNet, and neural architecture search
PRIORITY: high
---
DIRECTION: Explainable AI
REASONING: Understanding how neural networks make decisions is important for trust and safety
SOURCES: LIME, SHAP, attention visualization research
PRIORITY: high`,
					tokensUsed: 120
				};
			}

			// Default response
			return {
				text: 'Neural networks are powerful machine learning models that can learn complex patterns from data.',
				tokensUsed: 50
			};
		})
	};
}

/**
 * Wait for async operations
 */
export function wait(ms: number): Promise<void> {
	return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * Assert TF-IDF vector properties
 */
export function assertTFIDFVector(vector: Map<string, number> | undefined) {
	expect(vector).toBeDefined();
	expect(vector?.size).toBeGreaterThan(0);
	
	// All values should be numbers
	for (const [_term, value] of vector!) {
		expect(typeof value).toBe('number');
		expect(value).toBeGreaterThanOrEqual(0);
	}
}

/**
 * Assert clustering results
 */
export function assertClusterResults(clusters: Map<string, any>) {
	expect(clusters).toBeDefined();
	expect(clusters.size).toBeGreaterThan(0);
	
	for (const [_id, cluster] of clusters) {
		expect(cluster.notes).toBeDefined();
		expect(cluster.notes.length).toBeGreaterThan(0);
		expect(cluster.theme).toBeDefined();
		expect(cluster.keywords).toBeDefined();
		expect(Array.isArray(cluster.keywords)).toBe(true);
	}
}
