/**
 * Intelligent Context Engine (Vector Enhanced)
 * 
 * Provides advanced context understanding for AI interactions by analyzing
 * note relationships via Vector Embeddings.
 * 
 * Features:
 * - Semantic Search (Vector-based)
 * - Smart context window selection
 * - Temporal context awareness
 * - Adaptive context sizing
 * - Project boundary detection
 */

import { TFile, Vault, MetadataCache } from 'obsidian';
import { VectorStore } from './services/vectorStore';
import { EmbeddingService } from './services/embeddingService';

interface NoteCluster {
	id: string;
	notes: TFile[];
	theme: string; 
	keywords: string[];
}

export interface ContextScore {
	file: TFile;
	score: number;
	reasons: string[]; // Why this note is relevant
	recencyScore: number;
	linkScore: number;
	semanticScore: number;
}

interface ProjectBoundary {
	name: string;
	notes: TFile[];
	startDate: number;
	lastModified: number;
	isActive: boolean;
	tags: string[];
}

interface AdaptiveContext {
	primaryNote: TFile;
	relatedNotes: TFile[];
	contextText: string;
	tokenEstimate: number;
	includedClusters: string[];
}

export class IntelligentContextEngine {
	private vault: Vault;
	private metadataCache: MetadataCache;
	private vectorStore: VectorStore;
    private embeddingService?: EmbeddingService; // Optional for now, passed if needed for on-the-fly embedding
	
	// Caches
	private linkGraphCache: Map<string, Set<string>> | null = null;
	
	// Configuration
	private readonly RECENCY_DECAY_DAYS = 30;
	private readonly MAX_LINK_DISTANCE = 3;

	constructor(vault: Vault, metadataCache: MetadataCache, vectorStore: VectorStore, embeddingService?: EmbeddingService) {
		this.vault = vault;
		this.metadataCache = metadataCache;
		this.vectorStore = vectorStore;
        this.embeddingService = embeddingService;
	}

	/**
	 * Build semantic clusters of related notes (Mock implementation for now using Vector Neighbors)
     * In a real vector system, we'd use K-Means or DBSCAN on the vectors.
     * For now, we will return empty or simple groups based on folder/tags to not break contract.
	 */
	async buildSemanticClusters(): Promise<Map<string, NoteCluster>> {
		// TODO: Implement K-Means on vectors
        return new Map();
	}

	/**
	 * Score note relevance for a given query/context using Vector Search
	 */
	async scoreNoteRelevance(
		note: TFile,
		_query: string,
		currentNote?: TFile // Used for link distance, not embedding comparison (yet)
	): Promise<ContextScore> {
        // If we have an embedding service, we could embed the query.
        // However, this function signature expects to return a score for a SPECIFIC note against a query.
        // This is inefficient for vectors (O(N)). 
        // Vector stores are designed for "Find top K".
        
        // For backwards compatibility, we will fall back to a simpler heuristic if we can't do vector search 
        // or if this is called in a loop.
        
        // IDEAL FLOW: The caller should call `vectorStore.search(query)` once, get results, then map those to files.
        // But to keep this method working for legacy calls:
        
        // 1. Recency
		const recencyScore = this.computeRecencyScore(note);

		// 2. Link Score
		let linkScore = 0;
		if (currentNote) {
			linkScore = this.computeLinkScore(currentNote, note);
		}

        // 3. Semantic Score via Vector
        // We can check if the note is in the vector store.
        // If we have the query vector (we don't here easily), we could dot product.
        // Without query vector, we can't compute semantic score efficiently here.
        // So we will assume 0 unless we change the architecture.
        
        // HACK: Return 0 semantic score here, relying on the caller to use `getAdaptiveContext` which DOES use vector search.
        const semanticScore = 0; 

		// Weighted total score (without semantic)
		const score = (recencyScore * 0.3) + (linkScore * 0.2);

		const reasons: string[] = [];
		if (recencyScore > 70) reasons.push('Recently modified');
		if (linkScore > 50) reasons.push('Connected via links');

		return {
			file: note,
			score,
			reasons,
			recencyScore,
			linkScore,
			semanticScore
		};
	}

	/**
	 * Get adaptive context for AI interaction - NOW VECTOR POWERED
	 */
	async getAdaptiveContext(
		note: TFile,
		query: string,
		maxTokens: number = 4000
	): Promise<AdaptiveContext> {
        // 1. Generate Embedding for the Query
        if (!this.embeddingService) {
            throw new Error("Embedding service required for adaptive context");
        }

        const queryEmbedding = await this.embeddingService.generateEmbedding(query);
        
        // 2. Vector Search
        const searchResults = await this.vectorStore.search(queryEmbedding.vector, 20, 0.4); // Get top 20, min score 0.4
        
        const relatedNotes: TFile[] = [];
        const includedClusters = new Set<string>();

		// Build context text within token limit
		const primaryContent = await this.vault.read(note);
		let contextText = `# Current Note: ${note.basename}\n\n${primaryContent}\n\n`;
		let tokenEstimate = this.estimateTokens(contextText);
		
		contextText += '# Related Context (Semantic Search)\n\n';

		for (const result of searchResults) {
            if (result.id === note.path) continue; // Skip self

            const file = this.vault.getAbstractFileByPath(result.id);
            if (!(file instanceof TFile)) continue;

			const content = await this.vault.read(file);
			// Extract a relevant chunk or just the first X chars
            const preview = content.substring(0, 500).replace(/\n/g, ' ');
			
            const addition = `## ${file.basename} (Relevance: ${(result.score * 100).toFixed(0)}%)\n${preview}...\n\n`;
			
			const additionTokens = this.estimateTokens(addition);
			if (tokenEstimate + additionTokens > maxTokens) {
				break;
			}

			contextText += addition;
			tokenEstimate += additionTokens;
			relatedNotes.push(file);
		}

		return {
			primaryNote: note,
			relatedNotes,
			contextText,
			tokenEstimate,
			includedClusters: Array.from(includedClusters)
		};
	}

	/**
	 * Detect project boundaries in vault
	 */
	async detectProjectBoundaries(): Promise<Map<string, ProjectBoundary>> {
		const projects = new Map<string, ProjectBoundary>();
		const files = this.vault.getMarkdownFiles();

		// Group by tags and folders
		const tagGroups = new Map<string, TFile[]>();
		const folderGroups = new Map<string, TFile[]>();

		for (const file of files) {
			const metadata = this.metadataCache.getFileCache(file);
			
			// Group by tags (both frontmatter and inline)
			const allTags: string[] = [];
			
			// Frontmatter tags
			if (metadata?.frontmatter?.tags) {
				const tags = Array.isArray(metadata.frontmatter.tags)
					? metadata.frontmatter.tags
					: [metadata.frontmatter.tags];
				allTags.push(...tags.map(String));
			}
			
			// Inline tags
			if (metadata?.tags) {
				allTags.push(...metadata.tags.map((t: any) => t.tag));
			}
			
			// Group by project-related tags
			for (const tag of allTags) {
				const tagStr = String(tag).replace(/^#/, ''); // Remove leading #
				if (tagStr.startsWith('project-') || tagStr.includes('project')) {
					if (!tagGroups.has(tagStr)) {
						tagGroups.set(tagStr, []);
					}
					tagGroups.get(tagStr)!.push(file);
				}
			}

			// Group by folder
			const folder = file.parent?.path || 'root';
			if (!folderGroups.has(folder)) {
				folderGroups.set(folder, []);
			}
			folderGroups.get(folder)!.push(file);
		}

		// Create project boundaries from tag groups (lowered threshold)
		for (const [tag, notes] of tagGroups) {
			if (notes.length < 2) continue; // Minimum project size (lowered from 3)

			const stats = this.computeProjectStats(notes);
			projects.set(`tag-${tag}`, {
				name: tag,
				notes,
				startDate: stats.startDate,
				lastModified: stats.lastModified,
				isActive: this.isProjectActive(stats.lastModified),
				tags: [tag]
			});
		}

		// Create project boundaries from folders (if substantial)
		for (const [folder, notes] of folderGroups) {
			if (notes.length < 3) continue; // Lower threshold for folders (was 5)
			if (projects.has(`folder-${folder}`)) continue;

			const stats = this.computeProjectStats(notes);
			projects.set(`folder-${folder}`, {
				name: folder,
				notes,
				startDate: stats.startDate,
				lastModified: stats.lastModified,
				isActive: this.isProjectActive(stats.lastModified),
				tags: []
			});
		}

		return projects;
	}

	/**
	 * Find notes in same cluster as given note
	 */
	async findClusterMates(note: TFile): Promise<TFile[]> {
        // Use Vector Nearest Neighbors as "Cluster Mates"
        if (!this.vectorStore) return [];

        const noteVectorDoc = this.vectorStore.get(note.path);
        if (!noteVectorDoc) return [];

        const results = await this.vectorStore.search(noteVectorDoc.vector, 5, 0.5);
        const mates: TFile[] = [];

        for (const res of results) {
            if (res.id === note.path) continue;
            const file = this.vault.getAbstractFileByPath(res.id);
            if (file instanceof TFile) mates.push(file);
        }
        
		return mates;
	}

	/**
	 * Get cluster theme/summary
	 */
	async getClusterTheme(_clusterId: string): Promise<string> {
		return "Semantic Cluster";
	}

	// ========== Private Helper Methods ==========

	private computeRecencyScore(file: TFile): number {
		const now = Date.now();
		const age = (now - file.stat.mtime) / (1000 * 60 * 60 * 24); // Days
		
		// Exponential decay
		return Math.max(0, 100 * Math.exp(-age / this.RECENCY_DECAY_DAYS));
	}

	private computeLinkScore(from: TFile, to: TFile): number {
		const distance = this.computeLinkDistance(from, to);
		
		if (distance === 0) return 0; // No connection
		if (distance === 1) return 100; // Direct link
		if (distance === 2) return 60; // 2 hops
		if (distance === 3) return 30; // 3 hops
		
		return 10; // Distant connection
	}

	private computeLinkDistance(from: TFile, to: TFile): number {
		// Build link graph if needed
		if (!this.linkGraphCache) {
			this.buildLinkGraph();
		}

		// BFS to find shortest path
		const queue: [string, number][] = [[from.path, 0]];
		const visited = new Set<string>([from.path]);

		while (queue.length > 0) {
			const [current, distance] = queue.shift()!;
			
			if (current === to.path) return distance;
			if (distance >= this.MAX_LINK_DISTANCE) continue;

			const neighbors = this.linkGraphCache?.get(current) || new Set();
			for (const neighbor of neighbors) {
				if (!visited.has(neighbor)) {
					visited.add(neighbor);
					queue.push([neighbor, distance + 1]);
				}
			}
		}

		return 0; // No connection found
	}

	private buildLinkGraph(): void {
		this.linkGraphCache = new Map();
		const files = this.vault.getMarkdownFiles();

		for (const file of files) {
			const metadata = this.metadataCache.getFileCache(file);
			const links = new Set<string>();

			if (metadata?.links) {
				for (const link of metadata.links) {
					const targetFile = this.metadataCache.getFirstLinkpathDest(
						link.link,
						file.path
					);
					if (targetFile) {
						links.add(targetFile.path);
					}
				}
			}

			this.linkGraphCache.set(file.path, links);
		}
	}

	private computeProjectStats(notes: TFile[]): {
		startDate: number;
		lastModified: number;
	} {
		let startDate = Infinity;
		let lastModified = 0;

		for (const note of notes) {
			if (note.stat.ctime < startDate) startDate = note.stat.ctime;
			if (note.stat.mtime > lastModified) lastModified = note.stat.mtime;
		}

		return { startDate, lastModified };
	}

	private isProjectActive(lastModified: number): boolean {
		const now = Date.now();
		const daysSinceUpdate = (now - lastModified) / (1000 * 60 * 60 * 24);
		
		return daysSinceUpdate < 7; // Active if modified in last week
	}

	private estimateTokens(text: string): number {
		// Rough estimate: 1 token ≈ 4 characters
		return Math.ceil(text.length / 4);
	}

	/**
	 * Clear all caches (call when vault changes significantly)
	 */
	clearCaches(): void {
		this.linkGraphCache = null;
	}
}