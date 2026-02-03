/**
 * Automated Link Suggestion Service
 * Addresses Issue #100: Implement Automated Link Suggestions
 * 
 * Suggests relevant internal links based on semantic similarity and context.
 */

import { App, TFile, Vault, CachedMetadata, MetadataCache } from 'obsidian';
import { Validators } from './validators';

export interface LinkSuggestion {
	targetFile: string;
	targetPath: string;
	relevanceScore: number;
	matchType: 'exact' | 'partial' | 'semantic' | 'tag';
	matchedPhrase?: string;
	context?: string;
	position?: {
		start: number;
		end: number;
	};
}

export interface SuggestionResult {
	suggestions: LinkSuggestion[];
	totalProcessed: number;
	duration: number;
}

export interface AutoLinkOptions {
	minRelevanceScore: number;
	maxSuggestionsPerNote: number;
	excludeTags: string[];
	includeTags: string[];
	semanticThreshold: number;
}

const DEFAULT_OPTIONS: AutoLinkOptions = {
	minRelevanceScore: 0.5,
	maxSuggestionsPerNote: 10,
	excludeTags: [],
	includeTags: [],
	semanticThreshold: 0.6
};

export class AutoLinkSuggester {
	private vault: Vault;
	private metadataCache: MetadataCache;

	constructor(app: App) {
		Validators.required(app, 'app');
		this.vault = app.vault;
		this.metadataCache = app.metadataCache;
	}

	/**
	 * Analyze a file and suggest relevant links
	 */
	async suggestLinks(file: TFile, options?: Partial<AutoLinkOptions>): Promise<LinkSuggestion[]> {
		if (!file || !(file instanceof TFile)) {
			return [];
		}

		const opts = { ...DEFAULT_OPTIONS, ...options };
		const content = await this.vault.read(file);
		const cache = this.metadataCache.getFileCache(file);
		
		const existingLinks = this.getExistingLinks(cache);
		const suggestions: LinkSuggestion[] = [];

		// Get all markdown files except current
		const allFiles = this.vault.getMarkdownFiles()
			.filter(f => f.path !== file.path);

		// Process each potential target file
		for (const targetFile of allFiles) {
			// Skip if already linked
			if (existingLinks.has(targetFile.path)) {
				continue;
			}

			const score = await this.calculateRelevance(
				file,
				targetFile,
				content,
				opts
			);

			if (score.relevanceScore >= opts.minRelevanceScore) {
				suggestions.push({
					targetFile: targetFile.basename,
					targetPath: targetFile.path,
					relevanceScore: score.relevanceScore,
					matchType: score.matchType,
					matchedPhrase: score.matchedPhrase,
					context: score.context
				});
			}
		}

		// Sort by relevance score
		suggestions.sort((a, b) => b.relevanceScore - a.relevanceScore);

		// Limit results
		return suggestions.slice(0, opts.maxSuggestionsPerNote);
	}

	/**
	 * Get existing links from file cache
	 */
	private getExistingLinks(cache: CachedMetadata | null): Set<string> {
		const links = new Set<string>();
		
		if (!cache) {
			return links;
		}

		// Add regular links
		if (cache.links) {
			for (const link of cache.links) {
				const resolved = this.metadataCache.getFirstLinkpathDest(link.link, '');
				if (resolved) {
					links.add(resolved.path);
				}
			}
		}

		// Add embeds
		if (cache.embeds) {
			for (const embed of cache.embeds) {
				const resolved = this.metadataCache.getFirstLinkpathDest(embed.link, '');
				if (resolved) {
					links.add(resolved.path);
				}
			}
		}

		return links;
	}

	/**
	 * Calculate relevance score between two files
	 */
	private async calculateRelevance(
		sourceFile: TFile,
		targetFile: TFile,
		sourceContent: string,
		options: AutoLinkOptions
	): Promise<{
		relevanceScore: number;
		matchType: 'exact' | 'partial' | 'semantic' | 'tag';
		matchedPhrase?: string;
		context?: string;
	}> {
		let bestScore = 0;
		let matchType: 'exact' | 'partial' | 'semantic' | 'tag' = 'semantic';
		let matchedPhrase: string | undefined;
		let context: string | undefined;

		const targetBasename = targetFile.basename;
		const targetContent = await this.vault.read(targetFile);
		const targetCache = this.metadataCache.getFileCache(targetFile);
		const sourceCache = this.metadataCache.getFileCache(sourceFile);

		// 1. Exact title match in content (highest score: 1.0)
		const exactMatch = new RegExp(`\\b${this.escapeRegex(targetBasename)}\\b`, 'i');
		if (exactMatch.test(sourceContent)) {
			bestScore = 1.0;
			matchType = 'exact';
			matchedPhrase = targetBasename;
			const match = sourceContent.match(exactMatch);
			if (match) {
				context = this.extractContext(sourceContent, match.index || 0);
			}
			return { relevanceScore: bestScore, matchType, matchedPhrase, context };
		}

		// 2. Partial title match (score: 0.8)
		const words = targetBasename.toLowerCase().split(/\s+/);
		for (const word of words) {
			if (word.length > 3) { // Ignore short words
				const wordMatch = new RegExp(`\\b${this.escapeRegex(word)}\\b`, 'i');
				if (wordMatch.test(sourceContent)) {
					const score = 0.8 * (word.length / targetBasename.length);
					if (score > bestScore) {
						bestScore = score;
						matchType = 'partial';
						matchedPhrase = word;
						const match = sourceContent.match(wordMatch);
						if (match) {
							context = this.extractContext(sourceContent, match.index || 0);
						}
					}
				}
			}
		}

		// 3. Tag overlap (score: 0.7)
		if (sourceCache?.tags && targetCache?.tags) {
			const sourceTags = new Set(sourceCache.tags.map(t => t.tag));
			const targetTags = new Set(targetCache.tags.map(t => t.tag));
			const overlap = [...sourceTags].filter(tag => targetTags.has(tag));
			
			if (overlap.length > 0) {
				const score = 0.7 * (overlap.length / Math.max(sourceTags.size, targetTags.size));
				if (score > bestScore) {
					bestScore = score;
					matchType = 'tag';
					matchedPhrase = overlap.join(', ');
				}
			}
		}

		// 4. Semantic similarity via shared vocabulary (score: 0.3-0.6)
		const semanticScore = this.calculateSemanticSimilarity(
			sourceContent,
			targetContent
		);
		
		if (semanticScore >= options.semanticThreshold && semanticScore > bestScore) {
			bestScore = semanticScore * 0.6; // Cap at 0.6 for semantic matches
			matchType = 'semantic';
		}

		// 5. Backlink bonus - if target links to source (score: +0.2)
		const targetLinks = this.getExistingLinks(targetCache);
		if (targetLinks.has(sourceFile.path)) {
			bestScore = Math.min(1.0, bestScore + 0.2);
		}

		return { relevanceScore: bestScore, matchType, matchedPhrase, context };
	}

	/**
	 * Calculate semantic similarity using vocabulary overlap
	 */
	private calculateSemanticSimilarity(text1: string, text2: string): number {
		// Extract meaningful words (3+ chars, not markdown syntax)
		const getWords = (text: string): Set<string> => {
			const words = text
				.toLowerCase()
				.replace(/[#*_\[\]()]/g, ' ') // Remove markdown
				.split(/\s+/)
				.filter(w => w.length > 3 && !/^\d+$/.test(w)); // Filter short and numeric
			return new Set(words);
		};

		const words1 = getWords(text1);
		const words2 = getWords(text2);

		if (words1.size === 0 || words2.size === 0) {
			return 0;
		}

		// Calculate Jaccard similarity
		const intersection = [...words1].filter(w => words2.has(w)).length;
		const union = words1.size + words2.size - intersection;

		return intersection / union;
	}

	/**
	 * Extract context around a match
	 */
	private extractContext(text: string, position: number, radius: number = 100): string {
		const start = Math.max(0, position - radius);
		const end = Math.min(text.length, position + radius);
		let context = text.substring(start, end);

		// Trim to sentence boundaries if possible
		const sentenceStart = context.lastIndexOf('.', radius);
		const sentenceEnd = context.indexOf('.', radius);

		if (sentenceStart !== -1) {
			context = context.substring(sentenceStart + 1);
		}
		if (sentenceEnd !== -1) {
			context = context.substring(0, sentenceEnd + 1);
		}

		return context.trim();
	}

	/**
	 * Escape regex special characters
	 */
	private escapeRegex(str: string): string {
		return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
	}

	/**
	 * Apply suggested links automatically
	 */
	async applyLinks(
		file: TFile,
		suggestions: LinkSuggestion[],
		autoApply: boolean = false
	): Promise<number> {
		try {
			let content = await this.vault.read(file);
			let appliedCount = 0;

			for (const suggestion of suggestions) {
				if (!suggestion.matchedPhrase || suggestion.matchType === 'semantic') {
					continue; // Only apply exact and partial matches
				}

				// Create link pattern
				const pattern = new RegExp(
					`\\b(${this.escapeRegex(suggestion.matchedPhrase)})\\b(?!\\]\\])`,
					'gi'
				);

				// Check if pattern exists and not already linked
				if (pattern.test(content)) {
					// Replace first occurrence with link
					content = content.replace(
						pattern,
						`[[$1|${suggestion.matchedPhrase}]]`
					);
					appliedCount++;
				}
			}

			if (appliedCount > 0 && autoApply) {
				await this.vault.modify(file, content);
			}

			return appliedCount;
		} catch (error) {
			console.error('Error applying links:', error);
			return 0;
		}
	}

	/**
	 * Generate suggestions report
	 */
	generateReport(file: TFile, suggestions: LinkSuggestion[]): string {
		const lines: string[] = [];
		
		lines.push(`# Link Suggestions for [[${file.basename}]]\n`);
		lines.push(`**Generated:** ${new Date().toISOString()}\n`);
		lines.push(`**Suggestions Found:** ${suggestions.length}\n`);

		if (suggestions.length === 0) {
			lines.push('No link suggestions found.\n');
			return lines.join('\n');
		}

		lines.push('## Suggested Links\n');

		for (const suggestion of suggestions) {
			const score = (suggestion.relevanceScore * 100).toFixed(1);
			lines.push(`### [[${suggestion.targetPath}|${suggestion.targetFile}]]`);
			lines.push(`- **Relevance:** ${score}%`);
			lines.push(`- **Match Type:** ${suggestion.matchType}`);
			
			if (suggestion.matchedPhrase) {
				lines.push(`- **Matched:** "${suggestion.matchedPhrase}"`);
			}
			
			if (suggestion.context) {
				lines.push(`- **Context:** "${suggestion.context}"`);
			}
			
			lines.push('');
		}

		return lines.join('\n');
	}
}
