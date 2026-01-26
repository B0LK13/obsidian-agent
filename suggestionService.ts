import { App, TFile } from 'obsidian';
import { DEFAULT_SUGGESTION_CONFIG, ObsidianAgentSettings, SuggestionConfig } from './settings';
import { AIService } from './aiService';

export interface Suggestion {
	id: string;
	type: 'link' | 'tag' | 'summarize' | 'extract-todos' | 'improve' | 'expand' | 'organize' | 'custom';
	title: string;
	description: string;
	priority: 'low' | 'medium' | 'high';
	confidence: number; // 0-1
	action?: () => Promise<void>;
}

export class SuggestionService {
	private app: App;
	private settings: ObsidianAgentSettings;
	private aiService: AIService;
	private config: SuggestionConfig;
	private currentSuggestions: Suggestion[] = [];
	private currentNote: TFile | null = null;
	private lastAnalysisTime: number = 0;
	private analysisCooldown: number = 30000; // 30 seconds in ms
	private tagIndexCache: { tags: Set<string>; timestamp: number } | null = null;
	private tagIndexTtlMs = 60000;

	constructor(app: App, settings: ObsidianAgentSettings, aiService: AIService, config?: SuggestionConfig) {
		this.app = app;
		this.settings = settings;
		this.aiService = aiService;
		this.config = config || this.loadConfigFromSettings();
	}

	private loadConfigFromSettings(): SuggestionConfig {
		if (!this.settings.suggestionConfig) {
			return { ...DEFAULT_SUGGESTION_CONFIG };
		}
		return {
			...DEFAULT_SUGGESTION_CONFIG,
			...this.settings.suggestionConfig,
			suggestionTypes: {
				...DEFAULT_SUGGESTION_CONFIG.suggestionTypes,
				...this.settings.suggestionConfig.suggestionTypes
			}
		};
	}

	updateConfig(config: Partial<SuggestionConfig>): void {
		this.config = { ...this.config, ...config };
	}

	/**
	 * Analyze current note and generate suggestions
	 */
	async analyzeNote(file: TFile | null, content: string): Promise<Suggestion[]> {
		const now = Date.now();
		
		// Check cooldown
		if (now - this.lastAnalysisTime < this.analysisCooldown) {
			return this.currentSuggestions;
		}

		if (!this.config.enabled || !this.config.autoAnalyze) {
			return [];
		}

		this.currentNote = file;
		this.lastAnalysisTime = now;
		this.currentSuggestions = [];

		try {
			// Generate suggestions in parallel
			const suggestions: Suggestion[] = [];

			if (this.config.suggestionTypes.links) {
				suggestions.push(...await this.generateLinkSuggestions(content));
			}

			if (this.config.suggestionTypes.tags) {
				suggestions.push(...await this.generateTagSuggestions(content));
			}

			if (this.config.suggestionTypes.summaries) {
				suggestions.push(await this.generateSummarySuggestion(content));
			}

			if (this.config.suggestionTypes.todos) {
				suggestions.push(...await this.generateTodoSuggestions(content));
			}

			if (this.config.suggestionTypes.improvements) {
				suggestions.push(...await this.generateImprovementSuggestions(content));
			}

			if (this.config.suggestionTypes.expansions) {
				suggestions.push(...await this.generateExpansionSuggestions(content));
			}

			if (this.config.suggestionTypes.organization) {
				suggestions.push(...await this.generateOrganizationSuggestions(content));
			}

			// Sort by priority and confidence
			this.currentSuggestions = suggestions
				.sort((a, b) => {
					const priorityOrder = { high: 3, medium: 2, low: 1 } as const;
					if (a.priority !== b.priority) {
						return priorityOrder[b.priority] - priorityOrder[a.priority];
					}
					return b.confidence - a.confidence;
				})
				.slice(0, this.config.maxSuggestions);

			return this.currentSuggestions;
		} catch (error) {
			console.error('Error analyzing note:', error);
			return [];
		}
	}

	/**
	 * Generate link suggestions based on [[wikilink]] syntax
	 */
	private async generateLinkSuggestions(content: string): Promise<Suggestion[]> {
		const suggestions: Suggestion[] = [];
		
		// Extract wikilinks from content
		const wikiLinkRegex = /\[\[([^\]]+)\]\]/g;
		const links: string[] = [];
		let match;

		while ((match = wikiLinkRegex.exec(content)) !== null) {
			links.push(match[1]);
		}

		// Check if linked notes exist
		for (const link of links) {
			const linkedFiles = this.app.vault.getMarkdownFiles().filter(f => 
				f.path.toLowerCase().includes(link.toLowerCase())
			);

			if (linkedFiles.length === 0) {
				suggestions.push({
					id: `link_${Date.now()}_${Math.random()}`,
					type: 'link',
					title: `Create missing note: ${link}`,
					description: `Note references "${link}" but doesn't exist`,
					priority: 'high',
					confidence: 0.9
				});
			}
		}

		// Find potential links (keywords that look like they should be linked)
		const potentialLinkKeywords = this.findPotentialLinks(content);
		for (const keyword of potentialLinkKeywords) {
			if (!links.includes(keyword)) {
				suggestions.push({
					id: `link_pot_${Date.now()}_${Math.random()}`,
					type: 'link',
					title: `Consider linking: ${keyword}`,
					description: `Keyword "${keyword}" appears but isn't linked`,
					priority: 'medium',
					confidence: 0.7
				});
			}
		}

		return suggestions;
	}

	/**
	 * Find potential keywords that should be linked
	 */
	private findPotentialLinks(content: string): string[] {
		const keywords = new Set<string>();
		
		// Extract proper nouns (capitalized words)
		const properNounRegex = /\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b/g;
		let match;
		
		while ((match = properNounRegex.exec(content)) !== null) {
			keywords.add(match[0]);
		}

		// Extract terms in quotes (often important concepts)
		const quotedTermsRegex = /"([^"]+)"/g;
		while ((match = quotedTermsRegex.exec(content)) !== null) {
			keywords.add(match[1]);
		}

		return Array.from(keywords);
	}

	/**
	 * Generate tag suggestions based on content
	 */
	private async generateTagSuggestions(content: string): Promise<Suggestion[]> {
		const suggestions: Suggestion[] = [];
		const existingTags = this.getExistingTags();
		const words = content
			.toLowerCase()
			.split(/\W+/)
			.filter(Boolean);
		const commonWords = new Set(['the', 'a', 'an', 'is', 'of', 'to', 'for', 'in', 'on', 'at', 'by']);
		const seen = new Set<string>();

		for (const word of words) {
			if (seen.has(word)) continue;
			seen.add(word);
			if (word.length <= 3 || commonWords.has(word) || existingTags.has(word)) continue;
			suggestions.push({
				id: `tag_${Date.now()}_${Math.random()}`,
				type: 'tag',
				title: `Consider adding tag: #${word}`,
				description: `"${word}" appears as a key concept`,
				priority: 'low',
				confidence: 0.5
			});
			if (suggestions.length >= 3) {
				break;
			}
		}

		return suggestions;
	}

	private getExistingTags(): Set<string> {
		const now = Date.now();
		if (this.tagIndexCache && now - this.tagIndexCache.timestamp < this.tagIndexTtlMs) {
			return this.tagIndexCache.tags;
		}

		const tags = new Set<string>();
		const metadataTags = (this.app.metadataCache as any)?.getTags?.();
		if (metadataTags) {
			Object.keys(metadataTags).forEach(tag => {
				const normalized = tag.replace(/^#/, '').toLowerCase();
				if (normalized) {
					tags.add(normalized);
				}
			});
		}
		this.tagIndexCache = { tags, timestamp: now };
		return tags;
	}

	/**
	 * Generate summary suggestion
	 */
	private async generateSummarySuggestion(content: string): Promise<Suggestion> {
		const wordCount = content.split(/\s+/).length;
		
		if (wordCount < 200) {
			return {
				id: `summary_${Date.now()}_${Math.random()}`,
				type: 'summarize',
				title: 'Generate summary',
				description: 'This note could benefit from a brief summary',
				priority: 'low',
				confidence: 0.3
			};
		}

		return {
			id: `summary_${Date.now()}_${Math.random()}`,
			type: 'summarize',
			title: 'Generate summary',
			description: 'Note is long enough to warrant a summary',
			priority: 'medium',
			confidence: 0.6
		};
	}

	/**
	 * Generate TODO extraction suggestions
	 */
	private async generateTodoSuggestions(content: string): Promise<Suggestion[]> {
		const suggestions: Suggestion[] = [];
		
		// Look for TODO-like patterns
		const todoKeywords = ['todo:', 'fixme:', 'hack:', 'note:', 'question:', 'idea:'];
		const hasExistingTodos = /[-*]\s*(todo|fixme|hack|note|question|idea):/i.test(content);
		
		if (!hasExistingTodos) {
			const hasActionItems = /should|need|want|plan|remember/gi.test(content);
			if (hasActionItems) {
				suggestions.push({
					id: `todo_${Date.now()}_${Math.random()}`,
					type: 'extract-todos',
					title: 'Extract TODO items',
					description: 'Found actionable items that could be TODOs',
					priority: 'medium',
					confidence: 0.7
				});
			}
		}

		// Check for incomplete sentences
		const ellipsisCount = (content.match(/\.\.\./g) || []).length;
		if (ellipsisCount > 0) {
			suggestions.push({
				id: `todo_${Date.now()}_${Math.random()}`,
				type: 'extract-todos',
				title: 'Complete incomplete thoughts',
				description: `Found ${ellipsisCount} incomplete sentence(s) ending with ...`,
				priority: 'low',
				confidence: 0.6
			});
		}

		return suggestions;
	}

	/**
	 * Generate improvement suggestions
	 */
	private async generateImprovementSuggestions(content: string): Promise<Suggestion[]> {
		const suggestions: Suggestion[] = [];
		
		// Check for long paragraphs
		const paragraphs = content.split(/\n\n+/);
		for (const para of paragraphs) {
			if (para.length > 500) {
				suggestions.push({
					id: `improve_${Date.now()}_${Math.random()}`,
					type: 'improve',
					title: 'Consider splitting long section',
					description: 'This section could be more readable if broken down',
					priority: 'low',
					confidence: 0.5
				});
			}
		}

		// Check for passive voice
		const passiveVoicePatterns = [/is \w+ed by/gi, /was \w+ed by/gi, /can be \w+ed/gi];
		for (const pattern of passiveVoicePatterns) {
			if (pattern.test(content)) {
				suggestions.push({
					id: `improve_${Date.now()}_${Math.random()}`,
					type: 'improve',
					title: 'Consider active voice',
					description: 'Some sentences use passive voice - active may be clearer',
					priority: 'low',
					confidence: 0.4
				});
				break;
			}
		}

		// Check for unclear structure
		const hasHeadings = /^#+\s/.test(content);
		if (!hasHeadings && content.length > 300) {
			suggestions.push({
				id: `improve_${Date.now()}_${Math.random()}`,
				type: 'improve',
				title: 'Add headings',
				description: 'Long notes benefit from clear headings for structure',
				priority: 'medium',
				confidence: 0.6
			});
		}

		return suggestions;
	}

	/**
	 * Generate expansion suggestions
	 */
	private async generateExpansionSuggestions(content: string): Promise<Suggestion[]> {
		const suggestions: Suggestion[] = [];
		
		// Find mentions without explanations
		const mentionRegex = /\b([A-Za-z]{5,})\b/g;
		let match;
		const mentionedTerms = new Set<string>();
		
		while ((match = mentionRegex.exec(content)) !== null) {
			mentionedTerms.add(match[1]);
		}

		for (const term of mentionedTerms) {
			suggestions.push({
				id: `expand_${Date.now()}_${Math.random()}`,
				type: 'expand',
				title: `Expand on: ${term}`,
				description: `"${term}" is mentioned but not explained`,
				priority: 'medium',
				confidence: 0.7
			});
		}

		return suggestions.slice(0, 5);
	}

	/**
	 * Generate organization suggestions
	 */
	private async generateOrganizationSuggestions(content: string): Promise<Suggestion[]> {
		const suggestions: Suggestion[] = [];
		
		// Check for mixed topics
		const sentences = content.split(/[.!?]+/);
		const topics = new Set<string>();
		
		for (const sentence of sentences) {
			const words = sentence.toLowerCase().split(/\s+/);
			for (const word of words) {
				if (word.length > 5 && /[aeiou]/.test(word)) {
					topics.add(word);
				}
			}
		}

		if (topics.size > 3) {
			suggestions.push({
				id: `organize_${Date.now()}_${Math.random()}`,
				type: 'organize',
				title: 'Consider splitting into multiple notes',
				description: `Note covers multiple topics: ${Array.from(topics).slice(0, 4).join(', ')}`,
				priority: 'medium',
				confidence: 0.6
			});
		}

		// Check for orphaned code blocks
		const codeBlocks = content.match(/```[\s\S]*?```/g) || [];
		if (codeBlocks.length > 0 && content.replace(/```[\s\S]*?```/g, '').length > 500) {
			suggestions.push({
				id: `organize_${Date.now()}_${Math.random()}`,
				type: 'organize',
				title: 'Extract code snippets',
				description: 'Code blocks mixed with text - consider extracting',
				priority: 'low',
				confidence: 0.5
			});
		}

		return suggestions;
	}

	/**
	 * Get current suggestions
	 */
	getCurrentSuggestions(): Suggestion[] {
		return this.currentSuggestions;
	}

	/**
	 * Clear suggestions
	 */
	clearSuggestions(): void {
		this.currentSuggestions = [];
		this.currentNote = null;
	}

	/**
	 * Check if suggestion should use local LLM based on privacy mode
	 */
	shouldUseLocalLLM(): boolean {
		return this.config.privacyMode === 'local';
	}
}
