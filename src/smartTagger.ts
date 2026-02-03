/**
 * Smart Auto-Tagging System
 * Addresses Issue #49: AI-Powered Auto-Organization & Tagging
 * 
 * Analyzes note content and suggests relevant tags based on:
 * - Existing tag patterns in vault
 * - Content analysis (TF-IDF)
 * - Machine learning from user's tagging history
 * - Semantic similarity to other notes
 */

import { App, TFile, Vault, MetadataCache } from 'obsidian';
import { Validators } from './validators';

export interface TagSuggestion {
	tag: string;
	confidence: number;
	reason: 'content_match' | 'pattern_learned' | 'similar_notes' | 'frequency';
	examples?: string[];
}

export interface TaggingConfig {
	minConfidence: number;
	maxSuggestions: number;
	learnFromHistory: boolean;
	useSemanticSimilarity: boolean;
}

const DEFAULT_CONFIG: TaggingConfig = {
	minConfidence: 0.4,
	maxSuggestions: 5,
	learnFromHistory: true,
	useSemanticSimilarity: true
};

interface TagPattern {
	tag: string;
	keywords: Set<string>;
	frequency: number;
	coOccurrences: Map<string, number>;
}

export class SmartTagger {
	private vault: Vault;
	private metadataCache: MetadataCache;
	private tagPatterns: Map<string, TagPattern> | null = null;
	private idfCache: Map<string, number> | null = null;

	constructor(app: App) {
		Validators.required(app, 'app');
		this.vault = app.vault;
		this.metadataCache = app.metadataCache;
	}

	/**
	 * Suggest tags for a note
	 */
	async suggestTags(
		file: TFile,
		config: Partial<TaggingConfig> = {}
	): Promise<TagSuggestion[]> {
		if (!file || !(file instanceof TFile)) {
			return [];
		}

		const cfg = { ...DEFAULT_CONFIG, ...config };
		const content = await this.vault.read(file);
		const existingTags = this.getExistingTags(file);
		const suggestions: TagSuggestion[] = [];

		// Build tag patterns if not cached
		if (!this.tagPatterns) {
			await this.buildTagPatterns();
		}

		// 1. Content-based suggestions
		const contentSuggestions = await this.suggestFromContent(
			content,
			existingTags
		);
		suggestions.push(...contentSuggestions);

		// 2. Pattern-based suggestions (learned from history)
		if (cfg.learnFromHistory) {
			const patternSuggestions = await this.suggestFromPatterns(
				content,
				existingTags
			);
			suggestions.push(...patternSuggestions);
		}

		// 3. Semantic similarity suggestions
		if (cfg.useSemanticSimilarity) {
			const semanticSuggestions = await this.suggestFromSimilarNotes(
				file,
				content,
				existingTags
			);
			suggestions.push(...semanticSuggestions);
		}

		// 4. Tag co-occurrence suggestions
		if (existingTags.length > 0) {
			const coOccurrenceSuggestions = this.suggestFromCoOccurrence(
				existingTags
			);
			suggestions.push(...coOccurrenceSuggestions);
		}

		// Merge and rank suggestions
		const merged = this.mergeSuggestions(suggestions);
		
		// Filter by confidence and limit
		return merged
			.filter(s => s.confidence >= cfg.minConfidence)
			.sort((a, b) => b.confidence - a.confidence)
			.slice(0, cfg.maxSuggestions);
	}

	/**
	 * Apply tags to a note
	 */
	async applyTags(file: TFile, tags: string[]): Promise<void> {
		if (!file || !(file instanceof TFile)) {
			throw new Error('Invalid file');
		}

		let content = await this.vault.read(file);
		const cache = this.metadataCache.getFileCache(file);
		
		// Check for YAML frontmatter
		if (cache?.frontmatter) {
			// Add to existing frontmatter
			content = this.addTagsToFrontmatter(content, tags);
		} else {
			// Add as inline tags at the top
			const tagLine = '\n' + tags.map(t => `#${t}`).join(' ') + '\n\n';
			content = tagLine + content;
		}

		await this.vault.modify(file, content);
	}

	/**
	 * Build tag patterns from vault
	 */
	private async buildTagPatterns(): Promise<void> {
		this.tagPatterns = new Map();
		const files = this.vault.getMarkdownFiles();
		const documentFrequency = new Map<string, number>();

		for (const file of files) {
			const cache = this.metadataCache.getFileCache(file);
			if (!cache?.tags) continue;

			const content = await this.vault.read(file);
			const words = this.extractKeywords(content);
			const fileTags = cache.tags.map(t => t.tag);

			// Build patterns for each tag
			for (const tag of fileTags) {
				if (!this.tagPatterns.has(tag)) {
					this.tagPatterns.set(tag, {
						tag,
						keywords: new Set(),
						frequency: 0,
						coOccurrences: new Map()
					});
				}

				const pattern = this.tagPatterns.get(tag)!;
				pattern.frequency++;

				// Add keywords
				words.forEach(word => pattern.keywords.add(word));

				// Track co-occurrences
				for (const otherTag of fileTags) {
					if (otherTag !== tag) {
						const count = pattern.coOccurrences.get(otherTag) || 0;
						pattern.coOccurrences.set(otherTag, count + 1);
					}
				}
			}

			// Build IDF cache
			words.forEach(word => {
				documentFrequency.set(word, (documentFrequency.get(word) || 0) + 1);
			});
		}

		// Calculate IDF
		this.idfCache = new Map();
		const totalDocs = files.length;
		for (const [word, df] of documentFrequency) {
			this.idfCache.set(word, Math.log(totalDocs / df));
		}
	}

	/**
	 * Suggest tags based on content analysis
	 */
	private async suggestFromContent(
		content: string,
		existingTags: string[]
	): Promise<TagSuggestion[]> {
		const suggestions: TagSuggestion[] = [];
		const keywords = this.extractKeywords(content);
		const existingSet = new Set(existingTags);

		if (!this.tagPatterns) return suggestions;

		for (const [tag, pattern] of this.tagPatterns) {
			if (existingSet.has(tag)) continue;

			// Calculate keyword overlap
			const overlap = keywords.filter(k => pattern.keywords.has(k));
			if (overlap.length === 0) continue;

			// Score based on TF-IDF weighted overlap
			let score = 0;
			for (const keyword of overlap) {
				const idf = this.idfCache?.get(keyword) || 1;
				score += idf;
			}

			// Normalize by pattern size
			const confidence = Math.min(1, score / (pattern.keywords.size * 0.5));

			if (confidence > 0.3) {
				suggestions.push({
					tag: tag.replace('#', ''),
					confidence,
					reason: 'content_match',
					examples: overlap.slice(0, 3)
				});
			}
		}

		return suggestions;
	}

	/**
	 * Suggest tags based on learned patterns
	 */
	private async suggestFromPatterns(
		content: string,
		existingTags: string[]
	): Promise<TagSuggestion[]> {
		const suggestions: TagSuggestion[] = [];
		const keywords = this.extractKeywords(content);
		const existingSet = new Set(existingTags);

		if (!this.tagPatterns) return suggestions;

		// Find tags with high keyword match
		for (const [tag, pattern] of this.tagPatterns) {
			if (existingSet.has(tag)) continue;

			const matchCount = keywords.filter(k => pattern.keywords.has(k)).length;
			if (matchCount < 2) continue;

			// Confidence based on frequency and match rate
			const matchRate = matchCount / pattern.keywords.size;
			const frequencyScore = Math.log(pattern.frequency + 1) / 10;
			const confidence = Math.min(1, matchRate * 0.7 + frequencyScore * 0.3);

			if (confidence > 0.35) {
				suggestions.push({
					tag: tag.replace('#', ''),
					confidence,
					reason: 'pattern_learned'
				});
			}
		}

		return suggestions;
	}

	/**
	 * Suggest tags from similar notes
	 */
	private async suggestFromSimilarNotes(
		file: TFile,
		content: string,
		existingTags: string[]
	): Promise<TagSuggestion[]> {
		const suggestions: TagSuggestion[] = [];
		const files = this.vault.getMarkdownFiles().filter(f => f.path !== file.path);
		const existingSet = new Set(existingTags);

		// Find similar notes (simple approach: keyword overlap)
		const targetKeywords = new Set(this.extractKeywords(content));
		const similarities: Array<{ file: TFile; score: number }> = [];

		for (const otherFile of files.slice(0, 100)) { // Limit for performance
			const otherContent = await this.vault.read(otherFile);
			const otherKeywords = new Set(this.extractKeywords(otherContent));

			// Jaccard similarity
			const intersection = [...targetKeywords].filter(k => otherKeywords.has(k));
			const union = new Set([...targetKeywords, ...otherKeywords]);
			const similarity = intersection.length / union.size;

			if (similarity > 0.3) {
				similarities.push({ file: otherFile, score: similarity });
			}
		}

		// Get tags from top similar notes
		similarities.sort((a, b) => b.score - a.score);
		const tagCounts = new Map<string, number>();
		const tagConfidence = new Map<string, number>();

		for (const { file: similarFile, score } of similarities.slice(0, 5)) {
			const cache = this.metadataCache.getFileCache(similarFile);
			if (!cache?.tags) continue;

			for (const tagObj of cache.tags) {
				const tag = tagObj.tag.replace('#', '');
				if (existingSet.has(tag)) continue;

				tagCounts.set(tag, (tagCounts.get(tag) || 0) + 1);
				tagConfidence.set(tag, Math.max(tagConfidence.get(tag) || 0, score));
			}
		}

		// Create suggestions
		for (const [tag, count] of tagCounts) {
			const confidence = (tagConfidence.get(tag) || 0) * (count / 5);
			if (confidence > 0.3) {
				suggestions.push({
					tag,
					confidence,
					reason: 'similar_notes'
				});
			}
		}

		return suggestions;
	}

	/**
	 * Suggest tags based on co-occurrence with existing tags
	 */
	private suggestFromCoOccurrence(existingTags: string[]): TagSuggestion[] {
		const suggestions: TagSuggestion[] = [];
		if (!this.tagPatterns) return suggestions;

		const existingSet = new Set(existingTags.map(t => t.startsWith('#') ? t : `#${t}`));
		const coOccurrences = new Map<string, number>();

		// Aggregate co-occurrences
		for (const existingTag of existingSet) {
			const pattern = this.tagPatterns.get(existingTag);
			if (!pattern) continue;

			for (const [tag, count] of pattern.coOccurrences) {
				if (!existingSet.has(tag)) {
					coOccurrences.set(tag, (coOccurrences.get(tag) || 0) + count);
				}
			}
		}

		// Create suggestions
		for (const [tag, count] of coOccurrences) {
			const confidence = Math.min(1, count / 10); // Max confidence at 10 co-occurrences
			if (confidence > 0.3) {
				suggestions.push({
					tag: tag.replace('#', ''),
					confidence,
					reason: 'frequency'
				});
			}
		}

		return suggestions;
	}

	/**
	 * Merge duplicate suggestions and combine confidence scores
	 */
	private mergeSuggestions(suggestions: TagSuggestion[]): TagSuggestion[] {
		const merged = new Map<string, TagSuggestion>();

		for (const suggestion of suggestions) {
			const existing = merged.get(suggestion.tag);
			if (!existing) {
				merged.set(suggestion.tag, { ...suggestion });
			} else {
				// Combine confidences (max + 30% of other)
				existing.confidence = Math.min(
					1,
					Math.max(existing.confidence, suggestion.confidence) +
					Math.min(existing.confidence, suggestion.confidence) * 0.3
				);
			}
		}

		return Array.from(merged.values());
	}

	/**
	 * Get existing tags from a file
	 */
	private getExistingTags(file: TFile): string[] {
		const cache = this.metadataCache.getFileCache(file);
		if (!cache?.tags) return [];

		return cache.tags.map(t => t.tag.replace('#', ''));
	}

	/**
	 * Extract keywords from content
	 */
	private extractKeywords(content: string): string[] {
		// Remove markdown syntax
		const cleaned = content
			.replace(/```[\s\S]*?```/g, '') // Code blocks
			.replace(/`[^`]+`/g, '') // Inline code
			.replace(/!\[\[.*?\]\]/g, '') // Embeds
			.replace(/\[\[(.*?)\]\]/g, '$1') // Links
			.replace(/[#*_\[\]()]/g, ' ') // Markdown chars
			.toLowerCase();

		// Extract words
		const words = cleaned
			.split(/\s+/)
			.filter(w => w.length > 3) // Minimum length
			.filter(w => !/^\d+$/.test(w)) // No pure numbers
			.filter(w => !this.isStopWord(w));

		// Remove duplicates
		return [...new Set(words)];
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
			'they', 'been', 'what', 'when', 'make', 'like', 'time',
			'just', 'know', 'take', 'into', 'year', 'your', 'some',
			'could', 'them', 'than', 'then', 'these', 'would', 'other'
		]);

		return stopWords.has(word);
	}

	/**
	 * Add tags to YAML frontmatter
	 */
	private addTagsToFrontmatter(content: string, tags: string[]): string {
		const frontmatterRegex = /^---\n([\s\S]*?)\n---/;
		const match = content.match(frontmatterRegex);

		if (match) {
			const frontmatter = match[1];
			const tagsLineRegex = /^tags:\s*(.*)$/m;
			const tagsMatch = frontmatter.match(tagsLineRegex);

			if (tagsMatch) {
				// Add to existing tags
				const existingTags = tagsMatch[1]
					.replace(/[\[\]]/g, '')
					.split(',')
					.map(t => t.trim())
					.filter(t => t);

				const allTags = [...new Set([...existingTags, ...tags])];
				const newTagsLine = `tags: [${allTags.join(', ')}]`;
				const newFrontmatter = frontmatter.replace(tagsLineRegex, newTagsLine);

				return content.replace(frontmatterRegex, `---\n${newFrontmatter}\n---`);
			} else {
				// Add tags field
				const newFrontmatter = `${frontmatter}\ntags: [${tags.join(', ')}]`;
				return content.replace(frontmatterRegex, `---\n${newFrontmatter}\n---`);
			}
		} else {
			// Create new frontmatter
			const newFrontmatter = `---\ntags: [${tags.join(', ')}]\n---\n\n`;
			return newFrontmatter + content;
		}
	}

	/**
	 * Clear cached patterns (call when vault changes significantly)
	 */
	clearCache(): void {
		this.tagPatterns = null;
		this.idfCache = null;
	}
}
