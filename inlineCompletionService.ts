import { Editor, EditorPosition } from 'obsidian';
import { AIService } from './aiService';
import { CompletionConfig, DEFAULT_COMPLETION_CONFIG, ObsidianAgentSettings } from './settings';

/* Completion types: 
 * continue: Continue writing from cursor
 * complete-sentence: Complete current sentence
 * complete-paragraph: Complete current paragraph
 * complete-list-item: Add list item
 * answer-question: Answer a question
 * summarize-selection: Summarize selection
 * improve-selection: Improve selection text
 * expand-selection: Expand on selection text
 */
export type CompletionType = 
	| 'continue'
	| 'complete-sentence'
	| 'complete-paragraph'
	| 'complete-list-item'
	| 'answer-question'
	| 'summarize-selection'
	| 'improve-selection'
	| 'expand-selection';

export interface CompletionSuggestion {
	id: string;
	text: string;
	displayText: string;
	type: CompletionType;
	confidence: number;
	replacementRange?: [number, number];
}

interface CompletionContext {
	beforeCursor: string;
	currentLine: string;
	surroundingLines: string;
}

export class InlineCompletionService {
  private settings: ObsidianAgentSettings;
	private aiService: AIService;
	private config: CompletionConfig;
	private editor: Editor | null = null;
	private activeRequest: AbortController | null = null;
	private lastRequestTime: number = 0;
	private typingTimer: NodeJS.Timeout | null = null;
	private ghostTextEl: HTMLElement | null = null;
	private suggestions: CompletionSuggestion[] = [];
	private currentSuggestionIndex: number = 0;

	constructor(settings: ObsidianAgentSettings, aiService: AIService) {
		this.settings = settings;
		this.aiService = aiService;
		this.config = this.loadConfig();
	}

	private loadConfig(): CompletionConfig {
		if (!this.settings.completionConfig) {
			return { ...DEFAULT_COMPLETION_CONFIG };
		}
		return { ...DEFAULT_COMPLETION_CONFIG, ...this.settings.completionConfig };
	}

	updateConfig(config: Partial<CompletionConfig>): void {
		this.config = { ...this.config, ...config };
	}

	setEditor(editor: Editor): void {
		this.editor = editor;
		this.setupGhostText();
	}

	/**
	 * Setup ghost text element for preview
	 */
	private setupGhostText(): void {
		if (this.ghostTextEl) {
			this.ghostTextEl.remove();
		}

		this.ghostTextEl = document.createElement('span');
		this.ghostTextEl.className = 'oa-ghost-text';
		this.ghostTextEl.style.cssText = `
			pointer-events: none;
			user-select: none;
			opacity: 0.5;
			white-space: pre-wrap;
			font-family: var(--font-monospace);
		`;
	}

	/**
	 * Handle typing - cancel pending completions on new keystrokes
	 */
	onType(): void {
		if (this.typingTimer) {
			clearTimeout(this.typingTimer);
		}

		this.typingTimer = setTimeout(() => {
			this.hideCompletions();
		}, this.config.autoTriggerDelay);

		this.hideGhostText();
	}

	/**
	 * Trigger completion manually
	 */
	async triggerCompletion(): Promise<void> {
		if (!this.editor) return;

		const cursor = this.editor.getCursor();
		const context = this.getContext(cursor);

		this.showLoadingIndicator();

		try {
			const suggestions = await this.generateCompletions(context, cursor);
			this.suggestions = suggestions;
			this.currentSuggestionIndex = 0;

			if (suggestions.length > 0) {
				this.showCompletions(suggestions);
			} else {
				this.hideCompletions();
			}
		} catch (error) {
			console.error('Error generating completion:', error);
			this.hideCompletions();
		}
	}

	/**
	 * Get context around cursor
	 */
	private getContext(cursor: EditorPosition, content: string = ''): CompletionContext {
		if (this.editor) {
			const currentLine = this.editor.getLine(cursor.line) || '';
			const cursorCh = cursor.ch;
			const beforeCursor = currentLine.substring(0, cursorCh);

			const startLine = Math.max(0, cursor.line - 3);
			const endLine = Math.min(this.editor.lineCount() - 1, cursor.line + 3);
			const lines: string[] = [];

			for (let line = startLine; line <= endLine; line++) {
				lines.push(this.editor.getLine(line) || '');
			}

			const surroundingLines = lines.join('\n');
			return { beforeCursor, currentLine, surroundingLines };
		}

		const lines = content.split('\n');
		const currentLine = lines[cursor.line] || '';
		const cursorCh = cursor.ch;
		const beforeCursor = currentLine.substring(0, cursorCh);
		const startLine = Math.max(0, cursor.line - 3);
		const endLine = Math.min(lines.length - 1, cursor.line + 3);
		const surroundingLines = lines.slice(startLine, endLine + 1).join('\n');

		return { beforeCursor, currentLine, surroundingLines };
	}

	/**
	 * Generate completions using AI service
	 */
	private async generateCompletions(context: CompletionContext, _cursor: EditorPosition): Promise<CompletionSuggestion[]> {
		const { beforeCursor, currentLine, surroundingLines } = context;

		// Cancel any pending request
		if (this.activeRequest) {
			this.activeRequest.abort();
		}

		this.activeRequest = new AbortController();
		const now = Date.now();

		// Debounce rapid requests
		if (now - this.lastRequestTime < this.config.debounceDelay) {
			await new Promise(resolve => setTimeout(resolve, this.config.debounceDelay));
		}
		this.lastRequestTime = now;

		// Determine completion type based on context
		const completionType = this.detectCompletionType(currentLine, beforeCursor);

		const prompt = this.buildCompletionPrompt(completionType, context);

		try {
			const result = await this.aiService.generateCompletion({
				prompt,
				context: surroundingLines
			});

			// Parse AI response into completion suggestions
			return this.parseAIResponse(result.text, completionType);
		} catch (error: any) {
			console.error('AI completion error:', error);
			return [];
		} finally {
			this.activeRequest = null;
		}
	}

	/**
	 * Detect what type of completion would be most useful
	 */
	private detectCompletionType(line: string, beforeCursor: string): CompletionType {
		const trimmed = beforeCursor.trim();

		// End with question mark
		if (trimmed.endsWith('?')) {
			return 'answer-question';
		}

		// End with colon, hyphen, or dash
		if (/[:-]\s*$/.test(trimmed)) {
			return 'continue';
		}

		// In a list
		if (/^[\s*-]\s+/.test(line.trim())) {
			return 'complete-list-item';
		}

		// End with period and long
		if (trimmed.endsWith('.') && trimmed.length > 50) {
			return 'complete-paragraph';
		}

		// End with sentence terminator
		if (/[.!?]\s*$/.test(trimmed)) {
			return 'complete-sentence';
		}

		return 'continue';
	}

	/**
	 * Build prompt for completion
	 */
	private buildCompletionPrompt(type: CompletionType, context: CompletionContext): string {
		const { beforeCursor } = context;

		const trailing = (length: number) => beforeCursor.slice(Math.max(0, beforeCursor.length - length));

		const prompts: Record<CompletionType, string> = {
			'continue': `Continue the text from "${trailing(100)}":`,
			'complete-sentence': `Complete this sentence: "${trailing(50)}..."`,
			'complete-paragraph': `Write the next paragraph continuing from: "${trailing(100)}..."`,
			'complete-list-item': `Write the next list item continuing from: "${trailing(50)}..."`,
			'answer-question': `Answer this question: ${trailing(200)}`,
			'summarize-selection': '',  // Would need selection
			'improve-selection': '',
			'expand-selection': ''
		};

		return prompts[type] || prompts['continue'];
	}

	/**
	 * Parse AI response into completion suggestions
	 */
	private parseAIResponse(response: string, type: CompletionType): CompletionSuggestion[] {
		const suggestions: CompletionSuggestion[] = [];

		// Split response by lines or delimiters
		const lines = response.split('\n').filter(line => line.trim());

		lines.forEach((line, index) => {
			suggestions.push({
				id: `comp_${Date.now()}_${index}`,
				text: line,
				displayText: line,
				type: type,
				confidence: Math.max(0.1, 1 - (index * 0.15)) // Decrease confidence for later suggestions
			});
		});

		return suggestions.slice(0, this.config.maxCompletions);
	}

	/**
	 * Show completions to user
	 */
	private showCompletions(suggestions: CompletionSuggestion[]): void {
		this.hideGhostText();
		this.hideLoadingIndicator();

		if (suggestions.length === 0) {
			return;
		}

		const suggestion = suggestions[0];
		this.showGhostText(suggestion.text);
	}

	/**
	 * Show ghost text preview
	 */
	private showGhostText(text: string): void {
		if (!this.editor) return;

		const cursor = this.editor.getCursor();
		this.editor.getLine(cursor.line);

		this.ghostTextEl = document.createElement('span');
		this.ghostTextEl.className = 'oa-ghost-text';
		this.ghostTextEl.textContent = text;

		// Insert after cursor position visually
		this.ghostTextEl.style.cssText = `
			pointer-events: none;
			user-select: none;
			opacity: 0.5;
			white-space: pre-wrap;
			font-family: var(--font-monospace);
		`;

		// Note: In a real implementation, this would need more complex rendering logic
		// to position the ghost text correctly at the cursor
	}

	/**
	 * Hide ghost text
	 */
	private hideGhostText(): void {
		if (this.ghostTextEl) {
			this.ghostTextEl.remove();
			this.ghostTextEl = null;
		}
	}

	/**
	 * Show loading indicator
	 */
	private showLoadingIndicator(): void {
		// Could show a spinner or status indicator
	}

	/**
	 * Hide loading indicator
	 */
	private hideLoadingIndicator(): void {
		// Hide any loading indicator
	}

	/**
	 * Hide completions
	 */
	private hideCompletions(): void {
		this.hideGhostText();
		this.suggestions = [];
		this.currentSuggestionIndex = 0;
		this.hideLoadingIndicator();
	}

	/**
	 * Handle tab key - cycle through suggestions
	 */
	handleTab(reverse: boolean = false): void {
		if (this.suggestions.length === 0) return;

		if (reverse) {
			this.currentSuggestionIndex = (this.currentSuggestionIndex - 1 + this.suggestions.length) % this.suggestions.length;
		} else {
			this.currentSuggestionIndex = (this.currentSuggestionIndex + 1) % this.suggestions.length;
		}

		const suggestion = this.suggestions[this.currentSuggestionIndex];
		this.showCompletions([suggestion]);
	}

	/**
	 * Handle enter key - accept completion
	 */
	async handleEnter(): Promise<void> {
		if (this.suggestions.length === 0 || !this.editor) return;

		const suggestion = this.suggestions[this.currentSuggestionIndex];
		if (suggestion) {
			await this.applyCompletion(suggestion);
		}

		this.hideCompletions();
	}

	/**
	 * Apply completion to editor
	 */
	private async applyCompletion(suggestion: CompletionSuggestion): Promise<void> {
		if (!this.editor) return;

		const cursor = this.editor.getCursor();
		this.editor.replaceRange(suggestion.text, cursor);

		const lines = suggestion.text.split('\n');
		const lastLine = lines[lines.length - 1];
		const newCursor: EditorPosition = {
			line: cursor.line + (lines.length - 1),
			ch: lines.length === 1 ? cursor.ch + lastLine.length : lastLine.length
		};
		this.editor.setCursor(newCursor);
	}

	/**
	 * Check if should trigger based on phrase
	 */
	checkPhraseTrigger(text: string): boolean {
		return this.config.phraseTriggers.some((trigger: string) => text.endsWith(trigger));
	}

	/**
	 * Dispose of resources
	 */
	dispose(): void {
		if (this.typingTimer) {
			clearTimeout(this.typingTimer);
		}
		if (this.activeRequest) {
			this.activeRequest.abort();
		}
		this.hideCompletions();
		this.editor = null;
	}

	/**
	 * Get current suggestions
	 */
	getCurrentSuggestions(): CompletionSuggestion[] {
		return this.suggestions;
	}

	/**
	 * Check if completions are enabled
	 */
	isEnabled(): boolean {
		return this.config.enabled;
	}

	/**
	 * Get current config
	 */
	getConfig(): CompletionConfig {
		return this.config;
	}
}
