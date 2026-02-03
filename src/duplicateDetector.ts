/**
 * Semantic Duplicate & Similar Note Detection
 * Addresses Issue #48: Semantic Duplicate & Similar Note Detection
 * 
 * Detects duplicate and similar notes using:
 * - TF-IDF vectorization
 * - Cosine similarity
 * - Exact duplicate detection
 * - Near-duplicate detection (fuzzy matching)
 * - Content fingerprinting
 */

import { App, TFile, Vault, MetadataCache } from 'obsidian';
import { Validators } from './validators';

export interface DuplicateGroup {
	id: string;
	notes: TFile[];
	similarity: number;
	duplicateType: 'exact' | 'near-exact' | 'semantic';
	commonContent?: string;
	differences?: Map<string, string[]>;
}

export interface SimilarityResult {
	file1: TFile;
	file2: TFile;
	similarity: number;
	matchType: 'exact' | 'near-exact' | 'semantic' | 'title';
	commonSections?: string[];
	uniqueSections?: Map<string, string[]>;
}

export interface DuplicateDetectionConfig {
	exactMatchThreshold: number;      // 1.0 = exact match
	nearDuplicateThreshold: number;   // 0.95 = 95% similar
	semanticThreshold: number;         // 0.7 = 70% similar
	minContentLength: number;          // Ignore very short notes
	ignoreFrontmatter: boolean;
	compareTitle: boolean;
	compareTags: boolean;
}

const DEFAULT_CONFIG: DuplicateDetectionConfig = {
	exactMatchThreshold: 1.0,
	nearDuplicateThreshold: 0.95,
	semanticThreshold: 0.7,
	minContentLength: 50,
	ignoreFrontmatter: true,
	compareTitle: true,
	compareTags: true
};

export interface MergeStrategy {
	type: 'keep-first' | 'keep-longest' | 'merge-content' | 'manual';
	preserveTags: boolean;
	preserveLinks: boolean;
	createBackup: boolean;
}

export class DuplicateDetector {
	private vault: Vault;
	private metadataCache: MetadataCache;
	private tfidfCache: Map<string, Map<string, number>> | null = null;
	private idfCache: Map<string, number> | null = null;
	private contentHashes: Map<string, string> | null = null;

	constructor(app: App) {
		Validators.required(app, 'app');
		this.vault = app.vault;
		this.metadataCache = app.metadataCache;
	}

	/**
	 * Find all duplicates and similar notes in vault
	 */
	async findDuplicates(
		config: Partial<DuplicateDetectionConfig> = {}
	): Promise<DuplicateGroup[]> {
		const cfg = { ...DEFAULT_CONFIG, ...config };
		const files = this.vault.getMarkdownFiles();
		const groups: DuplicateGroup[] = [];
		const processed = new Set<string>();

		// Build caches
		await this.buildCaches(files, cfg);

		// 1. Find exact duplicates
		const exactGroups = await this.findExactDuplicates(files, cfg);
		groups.push(...exactGroups);
		exactGroups.forEach(g => g.notes.forEach(n => processed.add(n.path)));

		// 2. Find near-duplicates
		const nearGroups = await this.findNearDuplicates(
			files.filter(f => !processed.has(f.path)),
			cfg
		);
		groups.push(...nearGroups);
		nearGroups.forEach(g => g.notes.forEach(n => processed.add(n.path)));

		// 3. Find semantic duplicates
		const semanticGroups = await this.findSemanticDuplicates(
			files.filter(f => !processed.has(f.path)),
			cfg
		);
		groups.push(...semanticGroups);

		return groups;
	}

	/**
	 * Compare two specific notes
	 */
	async compareNotes(file1: TFile, file2: TFile): Promise<SimilarityResult> {
		const content1 = await this.vault.read(file1);
		const content2 = await this.vault.read(file2);

		// Calculate similarity
		const similarity = this.calculateSimilarity(content1, content2);

		// Determine match type
		let matchType: 'exact' | 'near-exact' | 'semantic' | 'title';
		if (similarity === 1.0) {
			matchType = 'exact';
		} else if (similarity >= 0.95) {
			matchType = 'near-exact';
		} else if (file1.basename.toLowerCase() === file2.basename.toLowerCase()) {
			matchType = 'title';
		} else {
			matchType = 'semantic';
		}

		// Find common and unique sections
		const sections1 = this.extractSections(content1);
		const sections2 = this.extractSections(content2);
		const commonSections: string[] = [];
		const uniqueSections = new Map<string, string[]>();

		for (const [heading1, _] of sections1) {
			if (sections2.has(heading1)) {
				commonSections.push(heading1);
			} else {
				if (!uniqueSections.has(file1.basename)) {
					uniqueSections.set(file1.basename, []);
				}
				uniqueSections.get(file1.basename)!.push(heading1);
			}
		}

		for (const [heading2, _] of sections2) {
			if (!sections1.has(heading2)) {
				if (!uniqueSections.has(file2.basename)) {
					uniqueSections.set(file2.basename, []);
				}
				uniqueSections.get(file2.basename)!.push(heading2);
			}
		}

		return {
			file1,
			file2,
			similarity,
			matchType,
			commonSections,
			uniqueSections
		};
	}

	/**
	 * Merge duplicate notes
	 */
	async mergeDuplicates(
		group: DuplicateGroup,
		strategy: MergeStrategy
	): Promise<TFile> {
		if (group.notes.length < 2) {
			throw new Error('Need at least 2 notes to merge');
		}

		// Determine primary note
		let primary: TFile;
		switch (strategy.type) {
			case 'keep-first':
				primary = group.notes[0];
				break;
			case 'keep-longest':
				primary = await this.getLongestNote(group.notes);
				break;
			case 'merge-content':
				primary = await this.mergeContent(group.notes, strategy);
				break;
			default:
				primary = group.notes[0];
		}

		// Create backups if requested
		if (strategy.createBackup) {
			await this.createBackups(group.notes);
		}

		// Collect tags and links if preserving
		const allTags = new Set<string>();
		const allLinks = new Set<string>();

		if (strategy.preserveTags || strategy.preserveLinks) {
			for (const note of group.notes) {
				const cache = this.metadataCache.getFileCache(note);
				
				if (strategy.preserveTags && cache?.tags) {
					cache.tags.forEach(t => allTags.add(t.tag));
				}

				if (strategy.preserveLinks && cache?.links) {
					cache.links.forEach(l => allLinks.add(l.link));
				}
			}
		}

		// Update primary note
		let primaryContent = await this.vault.read(primary);

		if (strategy.preserveTags && allTags.size > 0) {
			primaryContent = this.addTagsToContent(primaryContent, [...allTags]);
		}

		if (strategy.preserveLinks && allLinks.size > 0) {
			primaryContent = this.addLinksSection(primaryContent, [...allLinks]);
		}

		await this.vault.modify(primary, primaryContent);

		// Delete other notes
		for (const note of group.notes) {
			if (note.path !== primary.path) {
				await this.vault.delete(note);
			}
		}

		return primary;
	}

	/**
	 * Build TF-IDF and hash caches
	 */
	private async buildCaches(
		files: TFile[],
		config: DuplicateDetectionConfig
	): Promise<void> {
		this.tfidfCache = new Map();
		this.idfCache = new Map();
		this.contentHashes = new Map();

		const documentFrequency = new Map<string, number>();
		const totalDocs = files.length;

		for (const file of files) {
			const content = await this.vault.read(file);
			const cleaned = this.cleanContent(content, config);

			// Skip if too short
			if (cleaned.length < config.minContentLength) {
				continue;
			}

			// Store hash for exact duplicate detection
			this.contentHashes.set(file.path, this.hashContent(cleaned));

			// Extract terms for TF-IDF
			const terms = this.extractTerms(cleaned);
			
			// Calculate term frequency
			const tf = new Map<string, number>();
			for (const term of terms) {
				tf.set(term, (tf.get(term) || 0) + 1);
			}

			// Normalize TF
			const maxFreq = Math.max(...tf.values());
			for (const [term, freq] of tf) {
				tf.set(term, freq / maxFreq);
			}

			this.tfidfCache.set(file.path, tf);

			// Track document frequency
			const uniqueTerms = new Set(terms);
			for (const term of uniqueTerms) {
				documentFrequency.set(term, (documentFrequency.get(term) || 0) + 1);
			}
		}

		// Calculate IDF
		for (const [term, df] of documentFrequency) {
			this.idfCache.set(term, Math.log(totalDocs / df));
		}

		// Update TF-IDF with IDF
		for (const [filePath, tf] of this.tfidfCache) {
			const tfidf = new Map<string, number>();
			for (const [term, termFreq] of tf) {
				const idf = this.idfCache.get(term) || 0;
				tfidf.set(term, termFreq * idf);
			}
			this.tfidfCache.set(filePath, tfidf);
		}
	}

	/**
	 * Find exact duplicate notes
	 */
	private async findExactDuplicates(
		files: TFile[],
		_config: DuplicateDetectionConfig
	): Promise<DuplicateGroup[]> {
		const groups: DuplicateGroup[] = [];
		const hashToFiles = new Map<string, TFile[]>();

		if (!this.contentHashes) return groups;

		// Group by hash
		for (const file of files) {
			const hash = this.contentHashes.get(file.path);
			if (!hash) continue;

			if (!hashToFiles.has(hash)) {
				hashToFiles.set(hash, []);
			}
			hashToFiles.get(hash)!.push(file);
		}

		// Create groups for duplicates
		for (const [hash, duplicates] of hashToFiles) {
			if (duplicates.length > 1) {
				const content = await this.vault.read(duplicates[0]);
				groups.push({
					id: `exact-${hash}`,
					notes: duplicates,
					similarity: 1.0,
					duplicateType: 'exact',
					commonContent: content.substring(0, 200) + '...'
				});
			}
		}

		return groups;
	}

	/**
	 * Find near-duplicate notes (>95% similar)
	 */
	private async findNearDuplicates(
		files: TFile[],
		config: DuplicateDetectionConfig
	): Promise<DuplicateGroup[]> {
		const groups: DuplicateGroup[] = [];
		const processed = new Set<string>();

		for (let i = 0; i < files.length; i++) {
			if (processed.has(files[i].path)) continue;

			const similar: TFile[] = [files[i]];
			processed.add(files[i].path);

			for (let j = i + 1; j < files.length; j++) {
				if (processed.has(files[j].path)) continue;

				const similarity = await this.calculateNoteSimilarity(files[i], files[j]);

				if (similarity >= config.nearDuplicateThreshold) {
					similar.push(files[j]);
					processed.add(files[j].path);
				}
			}

			if (similar.length > 1) {
				groups.push({
					id: `near-${files[i].path}`,
					notes: similar,
					similarity: config.nearDuplicateThreshold,
					duplicateType: 'near-exact'
				});
			}
		}

		return groups;
	}

	/**
	 * Find semantically similar notes
	 */
	private async findSemanticDuplicates(
		files: TFile[],
		config: DuplicateDetectionConfig
	): Promise<DuplicateGroup[]> {
		const groups: DuplicateGroup[] = [];
		const processed = new Set<string>();

		for (let i = 0; i < files.length; i++) {
			if (processed.has(files[i].path)) continue;

			const similar: TFile[] = [files[i]];
			processed.add(files[i].path);

			for (let j = i + 1; j < files.length; j++) {
				if (processed.has(files[j].path)) continue;

				const similarity = await this.calculateNoteSimilarity(files[i], files[j]);

				if (similarity >= config.semanticThreshold && similarity < config.nearDuplicateThreshold) {
					similar.push(files[j]);
					processed.add(files[j].path);
				}
			}

			if (similar.length > 1) {
				groups.push({
					id: `semantic-${files[i].path}`,
					notes: similar,
					similarity: config.semanticThreshold,
					duplicateType: 'semantic'
				});
			}
		}

		return groups;
	}

	/**
	 * Calculate similarity between two notes
	 */
	private async calculateNoteSimilarity(file1: TFile, file2: TFile): Promise<number> {
		if (!this.tfidfCache) return 0;

		const vector1 = this.tfidfCache.get(file1.path);
		const vector2 = this.tfidfCache.get(file2.path);

		if (!vector1 || !vector2) return 0;

		return this.cosineSimilarity(vector1, vector2);
	}

	/**
	 * Calculate cosine similarity between two TF-IDF vectors
	 */
	private cosineSimilarity(v1: Map<string, number>, v2: Map<string, number>): number {
		let dotProduct = 0;
		let norm1 = 0;
		let norm2 = 0;

		// Calculate dot product
		for (const [term, val1] of v1) {
			const val2 = v2.get(term) || 0;
			dotProduct += val1 * val2;
			norm1 += val1 * val1;
		}

		// Calculate norm2
		for (const val2 of v2.values()) {
			norm2 += val2 * val2;
		}

		if (norm1 === 0 || norm2 === 0) return 0;

		return dotProduct / (Math.sqrt(norm1) * Math.sqrt(norm2));
	}

	/**
	 * Calculate simple text similarity
	 */
	private calculateSimilarity(text1: string, text2: string): number {
		const words1 = new Set(this.extractTerms(text1));
		const words2 = new Set(this.extractTerms(text2));

		const intersection = [...words1].filter(w => words2.has(w)).length;
		const union = new Set([...words1, ...words2]).size;

		return union === 0 ? 0 : intersection / union;
	}

	/**
	 * Clean content for comparison
	 */
	private cleanContent(content: string, config: DuplicateDetectionConfig): string {
		let cleaned = content;

		// Remove frontmatter if configured
		if (config.ignoreFrontmatter) {
			cleaned = cleaned.replace(/^---\n[\s\S]*?\n---\n/, '');
		}

		// Remove code blocks
		cleaned = cleaned.replace(/```[\s\S]*?```/g, '');

		// Remove inline code
		cleaned = cleaned.replace(/`[^`]+`/g, '');

		// Remove links
		cleaned = cleaned.replace(/\[\[([^\]]+)\]\]/g, '$1');
		cleaned = cleaned.replace(/\[([^\]]+)\]\([^\)]+\)/g, '$1');

		// Remove markdown formatting
		cleaned = cleaned.replace(/[#*_~]/g, '');

		// Normalize whitespace
		cleaned = cleaned.replace(/\s+/g, ' ').trim();

		return cleaned.toLowerCase();
	}

	/**
	 * Extract terms from content
	 */
	private extractTerms(content: string): string[] {
		const words = content
			.toLowerCase()
			.split(/\s+/)
			.filter(w => w.length > 2)
			.filter(w => !/^\d+$/.test(w))
			.filter(w => !this.isStopWord(w));

		return words;
	}

	/**
	 * Check if word is a stop word
	 */
	private isStopWord(word: string): boolean {
		const stopWords = new Set([
			'the', 'and', 'for', 'are', 'but', 'not', 'you', 'all',
			'can', 'her', 'was', 'one', 'our', 'out', 'day', 'get',
			'has', 'him', 'his', 'how', 'its', 'may', 'new', 'now',
			'old', 'see', 'two', 'who', 'boy', 'did', 'she', 'use',
			'way', 'will', 'with', 'this', 'that', 'have', 'from',
			'they', 'been', 'what', 'when', 'make', 'like', 'time'
		]);

		return stopWords.has(word);
	}

	/**
	 * Hash content for exact duplicate detection
	 */
	private hashContent(content: string): string {
		// Simple hash function
		let hash = 0;
		for (let i = 0; i < content.length; i++) {
			const char = content.charCodeAt(i);
			hash = ((hash << 5) - hash) + char;
			hash = hash & hash; // Convert to 32-bit integer
		}
		return hash.toString(36);
	}

	/**
	 * Extract sections from content
	 */
	private extractSections(content: string): Map<string, string> {
		const sections = new Map<string, string>();
		const headingRegex = /^#{1,6}\s+(.+)$/gm;
		
		const headings: Array<{ title: string; position: number }> = [];
		let match;

		while ((match = headingRegex.exec(content)) !== null) {
			headings.push({
				title: match[1],
				position: match.index
			});
		}

		for (let i = 0; i < headings.length; i++) {
			const start = headings[i].position;
			const end = i < headings.length - 1 ? headings[i + 1].position : content.length;
			sections.set(headings[i].title, content.substring(start, end));
		}

		return sections;
	}

	/**
	 * Get longest note from group
	 */
	private async getLongestNote(notes: TFile[]): Promise<TFile> {
		let longest = notes[0];
		let maxLength = 0;

		for (const note of notes) {
			const content = await this.vault.read(note);
			if (content.length > maxLength) {
				maxLength = content.length;
				longest = note;
			}
		}

		return longest;
	}

	/**
	 * Merge content from multiple notes
	 */
	private async mergeContent(notes: TFile[], _strategy: MergeStrategy): Promise<TFile> {
		// For now, just keep the longest
		// TODO: Implement intelligent merging
		return this.getLongestNote(notes);
	}

	/**
	 * Create backups before merging
	 */
	private async createBackups(notes: TFile[]): Promise<void> {
		const backupFolder = 'Backups/Duplicates';
		
		for (const note of notes) {
			const content = await this.vault.read(note);
			const backupPath = `${backupFolder}/${note.basename} - ${Date.now()}.md`;
			await this.vault.create(backupPath, content);
		}
	}

	/**
	 * Add tags to content
	 */
	private addTagsToContent(content: string, tags: string[]): string {
		// Check for frontmatter
		const frontmatterRegex = /^---\n([\s\S]*?)\n---/;
		const match = content.match(frontmatterRegex);

		if (match) {
			const frontmatter = match[1];
			const tagsLine = `tags: [${tags.join(', ')}]`;
			
			if (frontmatter.includes('tags:')) {
				return content; // Already has tags
			} else {
				const newFrontmatter = `${frontmatter}\n${tagsLine}`;
				return content.replace(frontmatterRegex, `---\n${newFrontmatter}\n---`);
			}
		} else {
			const tagLine = tags.map(t => t.startsWith('#') ? t : `#${t}`).join(' ');
			return `${tagLine}\n\n${content}`;
		}
	}

	/**
	 * Add links section to content
	 */
	private addLinksSection(content: string, links: string[]): string {
		const linksSection = `\n\n## Related Links\n${links.map(l => `- [[${l}]]`).join('\n')}`;
		return content + linksSection;
	}

	/**
	 * Clear caches
	 */
	clearCache(): void {
		this.tfidfCache = null;
		this.idfCache = null;
		this.contentHashes = null;
	}
}
