/**
 * Intelligent Context Engine
 * 
 * Provides advanced context understanding for AI interactions by analyzing
 * note relationships, semantic clustering, and temporal patterns.
 * 
 * Features:
 * - Semantic note clustering (HDBSCAN-style)
 * - Smart context window selection
 * - Temporal context awareness
 * - Adaptive context sizing
 * - Project boundary detection
 */

import { TFile, Vault, MetadataCache } from 'obsidian';

interface NoteCluster {
	id: string;
	notes: TFile[];
	centroid: Map<string, number>; // TF-IDF centroid
	theme: string; // Automatically detected theme
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
	
	// Caches
	private tfidfCache: Map<string, Map<string, number>> | null = null;
	private idfCache: Map<string, number> | null = null;
	private clusterCache: Map<string, NoteCluster> | null = null;
	private linkGraphCache: Map<string, Set<string>> | null = null;
	
	// Configuration
	private readonly MIN_CLUSTER_SIZE = 2; // Lowered to work with small vaults
	private readonly MAX_CLUSTERS = 20;
	private readonly RECENCY_DECAY_DAYS = 30;
	private readonly MAX_LINK_DISTANCE = 3;

	constructor(vault: Vault, metadataCache: MetadataCache) {
		this.vault = vault;
		this.metadataCache = metadataCache;
	}

	/**
	 * Build semantic clusters of related notes
	 */
	async buildSemanticClusters(): Promise<Map<string, NoteCluster>> {
		if (this.clusterCache) {
			return this.clusterCache;
		}

		const files = this.vault.getMarkdownFiles();
		await this.buildTFIDFCache(files);

		const clusters = new Map<string, NoteCluster>();
		const assigned = new Set<string>();
		
		// Simple agglomerative clustering
		for (let i = 0; i < files.length; i++) {
			const file = files[i];
			if (assigned.has(file.path)) continue;

			const cluster: NoteCluster = {
				id: `cluster-${i}`,
				notes: [file],
				centroid: this.tfidfCache?.get(file.path) || new Map(),
				theme: '',
				keywords: []
			};

			assigned.add(file.path);

			// Find similar notes
			for (let j = i + 1; j < files.length && cluster.notes.length < 15; j++) {
				const candidate = files[j];
				if (assigned.has(candidate.path)) continue;

				const similarity = this.cosineSimilarity(
					this.tfidfCache?.get(file.path),
					this.tfidfCache?.get(candidate.path)
				);

				if (similarity > 0.3) { // Threshold for clustering
					cluster.notes.push(candidate);
					assigned.add(candidate.path);
				}
			}

			// Only keep clusters with multiple notes
			if (cluster.notes.length >= this.MIN_CLUSTER_SIZE) {
				// Update centroid
				cluster.centroid = this.computeCentroid(cluster.notes);
				cluster.keywords = this.extractTopKeywords(cluster.centroid, 5);
				cluster.theme = this.inferTheme(cluster.keywords);
				
				clusters.set(cluster.id, cluster);
			}

			if (clusters.size >= this.MAX_CLUSTERS) break;
		}

		this.clusterCache = clusters;
		return clusters;
	}

	/**
	 * Score note relevance for a given query/context
	 */
	async scoreNoteRelevance(
		note: TFile,
		query: string,
		currentNote?: TFile
	): Promise<ContextScore> {
		// Auto-initialize TF-IDF cache if not built
		if (!this.tfidfCache || !this.idfCache) {
			await this.buildTFIDFCache(this.vault.getMarkdownFiles());
		}

		// Semantic score
		const queryVector = this.computeQueryVector(query);
		const noteVector = this.tfidfCache?.get(note.path);
		const semanticScore = this.cosineSimilarity(queryVector, noteVector) * 100;

		// Recency score
		const recencyScore = this.computeRecencyScore(note);

		// Link score (if currentNote provided)
		let linkScore = 0;
		if (currentNote) {
			linkScore = this.computeLinkScore(currentNote, note);
		}

		// Weighted total score
		const score = (semanticScore * 0.5) + (recencyScore * 0.3) + (linkScore * 0.2);

		const reasons: string[] = [];
		if (semanticScore > 50) reasons.push('Semantically relevant');
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
	 * Get adaptive context for AI interaction
	 */
	async getAdaptiveContext(
		note: TFile,
		query: string,
		maxTokens: number = 4000
	): Promise<AdaptiveContext> {
		const files = this.vault.getMarkdownFiles();
		
		// Score all notes
		const scores: ContextScore[] = [];
		for (const file of files) {
			if (file.path === note.path) continue; // Skip current note
			const score = await this.scoreNoteRelevance(file, query, note);
			if (score.score > 20) { // Minimum relevance threshold
				scores.push(score);
			}
		}

		// Sort by score
		scores.sort((a, b) => b.score - a.score);

		// Build context text within token limit
		const primaryContent = await this.vault.read(note);
		let contextText = `# Current Note: ${note.basename}\n\n${primaryContent}\n\n`;
		let tokenEstimate = this.estimateTokens(contextText);
		
		const relatedNotes: TFile[] = [];
		const includedClusters = new Set<string>();

		contextText += '# Related Context\n\n';

		for (const score of scores) {
			const content = await this.vault.read(score.file);
			const preview = this.extractRelevantExcerpt(content, query, 300);
			const addition = `## ${score.file.basename} (Relevance: ${score.score.toFixed(0)}%)\n${preview}\n\n`;
			
			const additionTokens = this.estimateTokens(addition);
			if (tokenEstimate + additionTokens > maxTokens) {
				break;
			}

			contextText += addition;
			tokenEstimate += additionTokens;
			relatedNotes.push(score.file);

			// Track which clusters we included
			if (this.clusterCache) {
				for (const [clusterId, cluster] of this.clusterCache) {
					if (cluster.notes.includes(score.file)) {
						includedClusters.add(clusterId);
					}
				}
			}
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
		const clusters = await this.buildSemanticClusters();
		
		for (const cluster of clusters.values()) {
			if (cluster.notes.includes(note)) {
				return cluster.notes.filter(n => n.path !== note.path);
			}
		}

		return [];
	}

	/**
	 * Get cluster theme/summary
	 */
	async getClusterTheme(clusterId: string): Promise<string> {
		const clusters = await this.buildSemanticClusters();
		const cluster = clusters.get(clusterId);
		
		if (!cluster) return 'Unknown cluster';
		
		return `${cluster.theme} (${cluster.notes.length} notes, keywords: ${cluster.keywords.join(', ')})`;
	}

	// ========== Private Helper Methods ==========

	private async buildTFIDFCache(files: TFile[]): Promise<void> {
		if (this.tfidfCache && this.idfCache) return;

		this.tfidfCache = new Map();
		this.idfCache = new Map();

		const documentFrequency = new Map<string, number>();
		const totalDocs = files.length;

		// First pass: compute document frequencies
		for (const file of files) {
			const content = await this.vault.read(file);
			const terms = this.extractTerms(content);
			const uniqueTerms = new Set(terms);

			for (const term of uniqueTerms) {
				documentFrequency.set(term, (documentFrequency.get(term) || 0) + 1);
			}
		}

		// Compute IDF values
		for (const [term, df] of documentFrequency) {
			this.idfCache.set(term, Math.log(totalDocs / df));
		}

		// Second pass: compute TF-IDF vectors
		for (const file of files) {
			const content = await this.vault.read(file);
			const terms = this.extractTerms(content);
			const termFreq = new Map<string, number>();
			
			for (const term of terms) {
				termFreq.set(term, (termFreq.get(term) || 0) + 1);
			}

			const tfidf = new Map<string, number>();
			for (const [term, tf] of termFreq) {
				const idf = this.idfCache.get(term) || 0;
				tfidf.set(term, tf * idf);
			}

			this.tfidfCache.set(file.path, tfidf);
		}
	}

	private extractTerms(content: string): string[] {
		// Clean content
		const cleaned = content
			.toLowerCase()
			.replace(/```[\s\S]*?```/g, '') // Remove code blocks
			.replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // Extract link text
			.replace(/[^a-z0-9\s]/g, ' ');

		const words = cleaned.split(/\s+/).filter(w => w.length > 3);
		
		// Remove stop words
		const stopWords = new Set([
			'this', 'that', 'with', 'from', 'have', 'been', 'were', 'will',
			'would', 'could', 'should', 'about', 'which', 'their', 'there',
			'when', 'where', 'what', 'whom', 'these', 'those', 'then', 'than'
		]);

		return words.filter(w => !stopWords.has(w));
	}

	private cosineSimilarity(
		vec1: Map<string, number> | undefined,
		vec2: Map<string, number> | undefined
	): number {
		if (!vec1 || !vec2 || vec1.size === 0 || vec2.size === 0) return 0;

		let dotProduct = 0;
		let mag1 = 0;
		let mag2 = 0;

		for (const [term, val1] of vec1) {
			mag1 += val1 * val1;
			const val2 = vec2.get(term) || 0;
			dotProduct += val1 * val2;
		}

		for (const val2 of vec2.values()) {
			mag2 += val2 * val2;
		}

		const magnitude = Math.sqrt(mag1) * Math.sqrt(mag2);
		return magnitude === 0 ? 0 : dotProduct / magnitude;
	}

	private computeCentroid(notes: TFile[]): Map<string, number> {
		const centroid = new Map<string, number>();
		
		for (const note of notes) {
			const vector = this.tfidfCache?.get(note.path);
			if (!vector) continue;

			for (const [term, value] of vector) {
				centroid.set(term, (centroid.get(term) || 0) + value);
			}
		}

		// Average
		for (const [term, sum] of centroid) {
			centroid.set(term, sum / notes.length);
		}

		return centroid;
	}

	private extractTopKeywords(vector: Map<string, number>, count: number): string[] {
		const sorted = Array.from(vector.entries())
			.sort((a, b) => b[1] - a[1])
			.slice(0, count);
		
		return sorted.map(([term]) => term);
	}

	private inferTheme(keywords: string[]): string {
		// Simple theme inference from top keywords
		if (keywords.length === 0) return 'Miscellaneous';
		
		// Capitalize first keyword as theme
		return keywords[0].charAt(0).toUpperCase() + keywords[0].slice(1);
	}

	private computeQueryVector(query: string): Map<string, number> {
		const terms = this.extractTerms(query);
		const termFreq = new Map<string, number>();
		
		for (const term of terms) {
			termFreq.set(term, (termFreq.get(term) || 0) + 1);
		}

		const vector = new Map<string, number>();
		for (const [term, tf] of termFreq) {
			const idf = this.idfCache?.get(term) || 1;
			vector.set(term, tf * idf);
		}

		return vector;
	}

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

	private extractRelevantExcerpt(content: string, query: string, maxLength: number): string {
		const queryTerms = this.extractTerms(query);
		const lines = content.split('\n');
		
		// Find most relevant line
		let bestLine = lines[0] || '';
		let bestScore = 0;

		for (const line of lines) {
			if (line.trim().length < 20) continue;
			
			const lineTerms = new Set(this.extractTerms(line));
			let score = 0;
			for (const term of queryTerms) {
				if (lineTerms.has(term)) score++;
			}

			if (score > bestScore) {
				bestScore = score;
				bestLine = line;
			}
		}

		// Expand to include context
		const idx = lines.indexOf(bestLine);
		const start = Math.max(0, idx - 1);
		const end = Math.min(lines.length, idx + 3);
		const excerpt = lines.slice(start, end).join('\n');

		if (excerpt.length <= maxLength) {
			return excerpt;
		}

		return excerpt.substring(0, maxLength) + '...';
	}

	private estimateTokens(text: string): number {
		// Rough estimate: 1 token ≈ 4 characters
		return Math.ceil(text.length / 4);
	}

	/**
	 * Clear all caches (call when vault changes significantly)
	 */
	clearCaches(): void {
		this.tfidfCache = null;
		this.idfCache = null;
		this.clusterCache = null;
		this.linkGraphCache = null;
	}
}
