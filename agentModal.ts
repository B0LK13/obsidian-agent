import { App, Modal, Notice, TextAreaComponent, setTooltip, MarkdownRenderer, DropdownComponent } from 'obsidian';
import { AIService } from './aiService';
import { ChatMessage, Conversation, ObsidianAgentSettings } from './settings';
import { PromptTemplate, BUILT_IN_TEMPLATES, getTemplateCategories, filterTemplates, applyTemplate, generateTemplateId } from './promptTemplates';
import { calculateTokenCount, getUsageLevel, getUsageColor, formatTokenCount, TokenCount } from './tokenCounter';

export class AgentModal extends Modal {
	private aiService: AIService;
	private settings: ObsidianAgentSettings;
	private saveSettings: () => Promise<void>;
	private onSubmit: (result: string) => void;
	private prompt: string = '';
	private context: string = '';
	private chatHistory: ChatMessage[] = [];
	private chatHistoryContainer?: HTMLElement;
	private promptContainer?: HTMLElement;
	private submitButton?: HTMLButtonElement;
	private textAreaElement?: HTMLTextAreaElement;
	private stopButton?: HTMLButtonElement;
	private isStreaming: boolean = false;
	private currentResponse: string = '';
	private currentConversationId: string | null = null;
	private conversationSelector?: HTMLSelectElement;
	private tokenCounterContainer?: HTMLElement;
	private tokenCounterBar?: HTMLElement;
	private tokenCounterText?: HTMLElement;

	constructor(
		app: App, 
		aiService: AIService, 
		settings: ObsidianAgentSettings,
		saveSettings: () => Promise<void>,
		context: string, 
		onSubmit: (result: string) => void
	) {
		super(app);
		this.aiService = aiService;
		this.settings = settings;
		this.saveSettings = saveSettings;
		this.context = context;
		this.onSubmit = onSubmit;
		
		// Load active conversation if persistence is enabled
		if (this.settings.enableConversationPersistence && this.settings.activeConversationId) {
			const activeConv = this.settings.conversations.find(c => c.id === this.settings.activeConversationId);
			if (activeConv) {
				this.currentConversationId = activeConv.id;
				this.chatHistory = [...activeConv.messages];
			}
		}
	}

	private generateConversationId(): string {
		return `conv_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
	}

	private generateConversationTitle(): string {
		if (this.chatHistory.length > 0) {
			const firstUserMessage = this.chatHistory.find(m => m.role === 'user');
			if (firstUserMessage) {
				const title = firstUserMessage.content.substring(0, 50);
				return title.length < firstUserMessage.content.length ? `${title}...` : title;
			}
		}
		return `Conversation ${new Date().toLocaleDateString()}`;
	}

	private async saveCurrentConversation(): Promise<void> {
		if (!this.settings.enableConversationPersistence || this.chatHistory.length === 0) {
			return;
		}

		const now = Date.now();
		
		if (this.currentConversationId) {
			// Update existing conversation
			const convIndex = this.settings.conversations.findIndex(c => c.id === this.currentConversationId);
			if (convIndex >= 0) {
				this.settings.conversations[convIndex].messages = [...this.chatHistory];
				this.settings.conversations[convIndex].updatedAt = now;
				this.settings.conversations[convIndex].title = this.generateConversationTitle();
			}
		} else {
			// Create new conversation
			this.currentConversationId = this.generateConversationId();
			const newConversation: Conversation = {
				id: this.currentConversationId,
				title: this.generateConversationTitle(),
				messages: [...this.chatHistory],
				createdAt: now,
				updatedAt: now
			};
			this.settings.conversations.unshift(newConversation);
			
			// Limit to maxConversations
			if (this.settings.conversations.length > this.settings.maxConversations) {
				this.settings.conversations = this.settings.conversations.slice(0, this.settings.maxConversations);
			}
		}

		this.settings.activeConversationId = this.currentConversationId;
		await this.saveSettings();
		this.updateConversationSelector();
	}

	private loadConversation(conversationId: string): void {
		const conversation = this.settings.conversations.find(c => c.id === conversationId);
		if (conversation) {
			this.currentConversationId = conversationId;
			this.chatHistory = [...conversation.messages];
			this.settings.activeConversationId = conversationId;
			this.renderChatHistory();
		}
	}

	private async startNewConversation(): Promise<void> {
		this.currentConversationId = null;
		this.chatHistory = [];
		this.settings.activeConversationId = undefined;
		await this.saveSettings();
		this.renderChatHistory();
		this.updateConversationSelector();
		new Notice('Started new conversation');
	}

	private updateConversationSelector(): void {
		if (!this.conversationSelector) return;
		
		// Clear existing options
		this.conversationSelector.innerHTML = '';
		
		// Add "New Conversation" option
		const newOption = document.createElement('option');
		newOption.value = '';
		newOption.text = '+ New Conversation';
		this.conversationSelector.appendChild(newOption);
		
		// Add existing conversations
		this.settings.conversations.forEach(conv => {
			const option = document.createElement('option');
			option.value = conv.id;
			option.text = conv.title;
			if (conv.id === this.currentConversationId) {
				option.selected = true;
			}
			this.conversationSelector!.appendChild(option);
		});
	}

	private async deleteConversation(conversationId: string): Promise<void> {
		const convIndex = this.settings.conversations.findIndex(c => c.id === conversationId);
		if (convIndex >= 0) {
			this.settings.conversations.splice(convIndex, 1);
			if (this.currentConversationId === conversationId) {
				this.currentConversationId = null;
				this.chatHistory = [];
				this.settings.activeConversationId = undefined;
			}
			await this.saveSettings();
			this.updateConversationSelector();
			this.renderChatHistory();
			new Notice('Conversation deleted');
		}
	}

	private exportConversationAsMarkdown(): string {
		if (this.chatHistory.length === 0) {
			return '';
		}
		
		let markdown = `# AI Conversation\n\n`;
		markdown += `*Exported on ${new Date().toLocaleString()}*\n\n---\n\n`;
		
		this.chatHistory.forEach(message => {
			const role = message.role === 'user' ? '**You**' : '**AI Agent**';
			const time = new Date(message.timestamp).toLocaleTimeString();
			markdown += `${role} *(${time})*:\n\n${message.content}\n\n---\n\n`;
		});
		
		return markdown;
	}

	private getAllTemplates(): PromptTemplate[] {
		const customTemplates = (this.settings.customTemplates || []).map(t => ({
			...t,
			isBuiltIn: false
		}));
		return [...BUILT_IN_TEMPLATES, ...customTemplates];
	}

	private openTemplatesPicker(): void {
		const modal = new TemplatesPickerModal(
			this.app,
			this.getAllTemplates(),
			this.context,
			(appliedPrompt) => {
				if (this.textAreaElement) {
					this.textAreaElement.value = appliedPrompt;
					this.prompt = appliedPrompt;
					this.textAreaElement.focus();
					this.updateTokenCounter();
				}
			}
		);
		modal.open();
	}

	private updateTokenCounter(): void {
		if (!this.tokenCounterBar || !this.tokenCounterText) return;

		const tokenCount = calculateTokenCount(
			this.settings.systemPrompt,
			this.settings.enableContextAwareness ? this.context : '',
			this.chatHistory,
			this.prompt,
			this.settings.model,
			this.settings.apiProvider
		);

		const level = getUsageLevel(tokenCount.percentage);
		const color = getUsageColor(level);

		// Update bar
		this.tokenCounterBar.style.width = `${Math.min(100, tokenCount.percentage)}%`;
		this.tokenCounterBar.style.backgroundColor = color;

		// Update text
		this.tokenCounterText.empty();
		
		const leftText = this.tokenCounterText.createDiv();
		leftText.innerHTML = `<strong>${formatTokenCount(tokenCount.total)}</strong> / ${formatTokenCount(tokenCount.limit)} tokens`;
		
		const rightText = this.tokenCounterText.createDiv();
		rightText.style.cursor = 'pointer';
		rightText.textContent = 'Details';
		setTooltip(rightText, this.getTokenBreakdown(tokenCount));

		// Warning for high usage
		if (level === 'critical') {
			leftText.style.color = color;
			new Notice('Warning: Approaching token limit. Consider shortening context.', 3000);
		} else if (level === 'high') {
			leftText.style.color = color;
		}
	}

	private getTokenBreakdown(tokenCount: TokenCount): string {
		return `Token Breakdown:
• System Prompt: ${formatTokenCount(tokenCount.systemPrompt)}
• Note Context: ${formatTokenCount(tokenCount.context)}
• Conversation: ${formatTokenCount(tokenCount.conversationHistory)}
• Current Prompt: ${formatTokenCount(tokenCount.currentPrompt)}
• Total: ${formatTokenCount(tokenCount.total)} / ${formatTokenCount(tokenCount.limit)} (${tokenCount.percentage}%)`;
	}

	onOpen() {
		const {contentEl} = this;

		contentEl.createEl('h2', {text: 'AI Agent Assistant'});

		// Conversation selector row
		if (this.settings.enableConversationPersistence) {
			const conversationRow = contentEl.createDiv({ cls: 'conversation-selector-row' });
			conversationRow.style.display = 'flex';
			conversationRow.style.alignItems = 'center';
			conversationRow.style.gap = '0.5rem';
			conversationRow.style.marginBottom = '0.75rem';

			const selectorLabel = conversationRow.createEl('span', { text: 'Conversation:' });
			selectorLabel.style.fontSize = 'var(--font-smaller)';
			selectorLabel.style.color = 'var(--text-muted)';

			this.conversationSelector = conversationRow.createEl('select') as HTMLSelectElement;
			this.conversationSelector.style.flex = '1';
			this.conversationSelector.style.padding = '0.25rem';
			this.conversationSelector.style.borderRadius = 'var(--radius-s)';
			this.conversationSelector.style.border = '1px solid var(--background-modifier-border)';
			this.conversationSelector.style.backgroundColor = 'var(--background-primary)';
			this.updateConversationSelector();
			
			this.conversationSelector.addEventListener('change', async (e) => {
				const selectedId = (e.target as HTMLSelectElement).value;
				if (selectedId === '') {
					await this.startNewConversation();
				} else {
					this.loadConversation(selectedId);
				}
			});

			const exportButton = conversationRow.createEl('button', { text: 'Export' });
			exportButton.style.fontSize = 'var(--font-smaller)';
			setTooltip(exportButton, 'Export conversation as markdown');
			exportButton.addEventListener('click', () => {
				const markdown = this.exportConversationAsMarkdown();
				if (markdown) {
					navigator.clipboard.writeText(markdown);
					new Notice('Conversation copied to clipboard as markdown');
				} else {
					new Notice('No conversation to export');
				}
			});

			if (this.currentConversationId) {
				const deleteButton = conversationRow.createEl('button', { text: 'Delete', cls: 'mod-warning' });
				deleteButton.style.fontSize = 'var(--font-smaller)';
				setTooltip(deleteButton, 'Delete this conversation');
				deleteButton.addEventListener('click', async () => {
					if (this.currentConversationId && confirm('Delete this conversation?')) {
						await this.deleteConversation(this.currentConversationId);
					}
				});
			}
		}

		const headerContainer = contentEl.createDiv({ cls: 'modal-header' });
		headerContainer.style.display = 'flex';
		headerContainer.style.justifyContent = 'space-between';
		headerContainer.style.alignItems = 'center';
		headerContainer.style.marginBottom = '1rem';

		const headerText = headerContainer.createDiv();
		headerText.createEl('p', {
			text: 'Enter your prompt below. The agent will use current note as context.',
			cls: 'setting-item-description'
		});

		const shortcutsHint = headerText.createEl('p', {
			text: 'Shortcuts: Enter to send, Ctrl/Cmd+K to clear, Escape to close',
			cls: 'setting-item-description'
		});
		shortcutsHint.style.fontSize = 'var(--font-smaller)';
		shortcutsHint.style.color = 'var(--text-muted)';
		shortcutsHint.style.marginTop = '0.25rem';

		const clearButton = headerContainer.createEl('button', {
			text: 'Clear Chat',
			cls: 'mod-warning'
		});
		clearButton.style.fontSize = 'var(--font-smaller)';
		setTooltip(clearButton, 'Clear all conversation history');
		clearButton.addEventListener('click', () => this.clearChatWithConfirmation());

		this.chatHistoryContainer = contentEl.createDiv({ cls: 'chat-history' });
		this.chatHistoryContainer.style.maxHeight = '300px';
		this.chatHistoryContainer.style.overflowY = 'auto';
		this.chatHistoryContainer.style.marginBottom = '1rem';
		this.chatHistoryContainer.style.border = '1px solid var(--background-modifier-border)';
		this.chatHistoryContainer.style.borderRadius = 'var(--radius-s)';
		this.chatHistoryContainer.style.padding = '0.5rem';
		this.chatHistoryContainer.style.display = 'none';

		this.promptContainer = contentEl.createDiv('prompt-container');
		
		const textArea = new TextAreaComponent(this.promptContainer);
		this.textAreaElement = textArea.inputEl as HTMLTextAreaElement;
		this.textAreaElement.style.width = '100%';
		this.textAreaElement.style.minHeight = '100px';
		this.textAreaElement.placeholder = 'What would you like AI to help with?';
		this.textAreaElement.addEventListener('keydown', (e) => this.handleKeyDown(e));
		textArea.onChange((value) => {
			this.prompt = value;
			this.updateTokenCounter();
		});

		// Token counter
		this.tokenCounterContainer = contentEl.createDiv({ cls: 'token-counter' });
		this.tokenCounterContainer.style.marginTop = '0.5rem';
		this.tokenCounterContainer.style.padding = '0.5rem';
		this.tokenCounterContainer.style.backgroundColor = 'var(--background-secondary)';
		this.tokenCounterContainer.style.borderRadius = 'var(--radius-s)';
		this.tokenCounterContainer.style.fontSize = 'var(--font-smaller)';

		// Token counter bar
		const barContainer = this.tokenCounterContainer.createDiv({ cls: 'token-bar-container' });
		barContainer.style.height = '4px';
		barContainer.style.backgroundColor = 'var(--background-modifier-border)';
		barContainer.style.borderRadius = '2px';
		barContainer.style.marginBottom = '0.5rem';
		barContainer.style.overflow = 'hidden';

		this.tokenCounterBar = barContainer.createDiv({ cls: 'token-bar' });
		this.tokenCounterBar.style.height = '100%';
		this.tokenCounterBar.style.width = '0%';
		this.tokenCounterBar.style.backgroundColor = 'var(--interactive-accent)';
		this.tokenCounterBar.style.transition = 'width 0.2s ease, background-color 0.2s ease';

		// Token counter text
		this.tokenCounterText = this.tokenCounterContainer.createDiv({ cls: 'token-text' });
		this.tokenCounterText.style.display = 'flex';
		this.tokenCounterText.style.justifyContent = 'space-between';
		this.tokenCounterText.style.color = 'var(--text-muted)';

		this.updateTokenCounter();

		// Templates button row
		const templatesRow = contentEl.createDiv({ cls: 'templates-row' });
		templatesRow.style.marginTop = '0.5rem';
		templatesRow.style.marginBottom = '0.5rem';

		const templatesButton = templatesRow.createEl('button', { text: 'Templates' });
		templatesButton.style.fontSize = 'var(--font-smaller)';
		setTooltip(templatesButton, 'Use a prompt template');
		templatesButton.addEventListener('click', () => this.openTemplatesPicker());

		const buttonContainer = contentEl.createDiv('button-container');
		buttonContainer.style.marginTop = '1rem';
		buttonContainer.style.display = 'flex';
		buttonContainer.style.justifyContent = 'flex-end';
		buttonContainer.style.gap = '0.5rem';

		const cancelButton = buttonContainer.createEl('button', {text: 'Cancel'});
		cancelButton.addEventListener('click', () => {
			this.close();
		});

		const refreshButton = buttonContainer.createEl('button', {text: 'Refresh'});
		refreshButton.style.fontSize = 'var(--font-smaller)';
		setTooltip(refreshButton, 'Regenerate response (bypass cache)');
		refreshButton.addEventListener('click', async () => {
			if (this.submitButton && !this.submitButton.disabled && this.prompt.trim()) {
				await this.handleSubmit(this.submitButton as HTMLElement, true);
			}
		});

		this.submitButton = buttonContainer.createEl('button', {
			text: 'Generate',
			cls: 'mod-cta'
		}) as HTMLButtonElement;
		this.submitButton.addEventListener('click', async () => {
			if (this.submitButton) {
				await this.handleSubmit(this.submitButton as HTMLElement, false);
			}
		});

		this.stopButton = buttonContainer.createEl('button', {
			text: 'Stop',
			cls: 'mod-warning'
		}) as HTMLButtonElement;
		this.stopButton.style.display = 'none';
		this.stopButton.addEventListener('click', () => this.stopGeneration());

		this.textAreaElement.focus();
	}

	private renderMarkdown(text: string): string {
		let html = text
			.replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
			.replace(/`([^`]+)`/g, '<code>$1</code>')
			.replace(/\*\*([^*]+)\*\*/g, '<em>$1</em>')
			.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
			.replace(/`([^`]+)`/g, '<code>$1</code>')
			.replace(/## (.+)/g, '<h3>$1</h3>')
			.replace(/# (.+)/g, '<h2>$1</h2>')
			.replace(/^- (.+)/gm, '<li>$1</li>')
			.replace(/\n/g, '<br>');
		
		const listWrap = html.replace(/<li>(.+?)<\/li>/g, (match, content) => {
			return `<ul style="margin: 0; padding-left: 1.5rem;">${content}</ul>`;
		});
		
		return listWrap;
	}

	private handleKeyDown(event: KeyboardEvent): void {
		if (event.key === 'Enter' && !event.shiftKey) {
			event.preventDefault();
			if (this.submitButton && !this.submitButton.disabled) {
				this.handleSubmit(this.submitButton as HTMLElement);
			}
		}

		if (event.key === 'Escape') {
			event.preventDefault();
			this.close();
		}

		if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
			event.preventDefault();
			this.clearChatWithConfirmation();
		}
	}

	private async handleSubmit(submitButton: HTMLElement, bypassCache: boolean = false): Promise<void> {
		if (!this.prompt.trim()) {
			new Notice('Please enter a prompt');
			return;
		}

		if (bypassCache) {
			this.aiService.setBypassCache(true);
		}

		submitButton.setAttr('disabled', 'true');
		submitButton.textContent = 'Generating...';
		if (this.stopButton) this.stopButton.style.display = 'none';
		this.isStreaming = true;
		this.currentResponse = '';

		this.addMessageToHistory('user', this.prompt);
		this.renderChatHistory();

		try {
			const result = await this.aiService.generateCompletion(
				this.prompt,
				this.context,
				true,
				(chunk) => {
					this.onStreamChunk(chunk);
					if (chunk.done) {
						this.isStreaming = false;
						if (this.stopButton) this.stopButton.style.display = 'none';
					}
				},
				(progress) => {
					if (this.isStreaming) {
						if (this.stopButton) this.stopButton.style.display = 'block';
						this.onStreamProgress(progress);
					}
				}
			);

			if (this.currentResponse) {
				this.addMessageToHistory('assistant', this.currentResponse, result.fromCache, result.tokensUsed);
				this.renderChatHistory();
				await this.saveCurrentConversation();

				if (result.fromCache) {
					new Notice('Response loaded from cache');
				}
			}

			this.onSubmit(this.currentResponse);
			this.prompt = '';
			this.updatePromptInput();
		} catch (error: any) {
			if (error.name !== 'AbortError') {
				new Notice(`Error: ${error.message}`);
				console.error('Agent Modal Error:', error);
			}
		} finally {
			this.isStreaming = false;
			if (this.stopButton) this.stopButton.style.display = 'none';
			submitButton.removeAttribute('disabled');
			submitButton.textContent = 'Generate';
		}
	}

	private onStreamChunk(chunk: any): void {
		if (chunk.done) {
			return;
		}

		if (chunk.content) {
			this.currentResponse += chunk.content;
			
			if (this.chatHistory.length > 0 && this.chatHistory[this.chatHistory.length - 1].role === 'assistant') {
				const lastMessage = this.chatHistory[this.chatHistory.length - 1];
				lastMessage.content = this.currentResponse;
			}
			
			this.renderChatHistory();
		}
	}

	private onStreamProgress(progress: string): void {
		if (progress && this.isStreaming) {
			if (this.chatHistory.length === 0 || this.chatHistory[this.chatHistory.length - 1].role !== 'assistant') {
				this.addMessageToHistory('assistant', '');
			}
			
			const lastMessage = this.chatHistory[this.chatHistory.length - 1];
			lastMessage.content = progress;
			this.renderChatHistory();
		}
	}

	private stopGeneration(): void {
		if (this.isStreaming) {
			this.aiService.cancelCurrentRequest();
			new Notice('Generation stopped');
		}
	}

	private addMessageToHistory(role: 'user' | 'assistant', content: string, fromCache?: boolean, tokensUsed?: number): void {
		this.chatHistory.push({
			role,
			content,
			timestamp: Date.now(),
			fromCache,
			tokensUsed
		});
		this.updateTokenCounter();
	}

	private renderChatHistory(): void {
		if (!this.chatHistoryContainer) return;

		this.chatHistoryContainer.empty();

		if (this.chatHistory.length === 0) {
			this.chatHistoryContainer.style.display = 'none';
			return;
		}

		this.chatHistoryContainer.style.display = 'block';

		const container = this.chatHistoryContainer;
		this.chatHistory.forEach(message => {
			const messageEl = container.createDiv({ cls: 'chat-message' });
			messageEl.style.marginBottom = '0.75rem';

			const headerEl = messageEl.createDiv({ cls: 'message-header' });
			headerEl.style.display = 'flex';
			headerEl.style.justifyContent = 'space-between';
			headerEl.style.fontSize = 'var(--font-smaller)';
			headerEl.style.color = 'var(--text-muted)';

			const headerLeft = headerEl.createDiv();
			headerLeft.style.display = 'flex';
			headerLeft.style.alignItems = 'center';
			headerLeft.style.gap = '0.5rem';

			const roleLabel = headerLeft.createEl('span', {
				text: message.role === 'user' ? 'You' : 'AI Agent',
				cls: message.role === 'user' ? 'user-label' : 'assistant-label'
			});
			roleLabel.style.fontWeight = 'bold';

			if (message.fromCache) {
				const cacheBadge = headerLeft.createEl('span', { text: 'Cached', cls: 'cache-badge' });
				cacheBadge.style.backgroundColor = 'var(--interactive-accent)';
				cacheBadge.style.color = 'var(--text-on-accent)';
				cacheBadge.style.padding = '0.125rem 0.5rem';
				cacheBadge.style.borderRadius = 'var(--radius-s)';
				cacheBadge.style.fontSize = 'var(--font-smaller)';
				cacheBadge.style.fontWeight = 'bold';
			}

			const headerRight = headerEl.createDiv();
			headerRight.style.display = 'flex';
			headerRight.style.alignItems = 'center';
			headerRight.style.gap = '0.5rem';

			const timestamp = new Date(message.timestamp).toLocaleTimeString();
			headerRight.createEl('span', { text: timestamp });

			if (message.tokensUsed) {
				headerRight.createEl('span', { text: `${message.tokensUsed} tokens` });
			}

			const contentEl = messageEl.createDiv({ cls: 'message-content' });
			contentEl.style.padding = '0.5rem';
			contentEl.style.borderRadius = 'var(--radius-s)';
			contentEl.style.backgroundColor = message.role === 'user' ? 'var(--background-secondary)' : 'var(--background-primary)';
			contentEl.style.whiteSpace = 'pre-wrap';
			contentEl.style.wordBreak = 'break-word';

			if (message.role === 'assistant') {
				contentEl.innerHTML = this.renderMarkdown(message.content);
			} else {
				contentEl.textContent = message.content;
			}
		});

		container.scrollTop = container.scrollHeight;
	}

	private async clearChatWithConfirmation(): Promise<void> {
		if (this.chatHistory.length === 0) {
			new Notice('Chat is already empty');
			return;
		}

		const confirmClear = confirm('Are you sure you want to clear the entire chat history? This action cannot be undone.');
		
		if (confirmClear) {
			this.chatHistory = [];
			
			// Also clear from saved conversation
			if (this.currentConversationId) {
				const convIndex = this.settings.conversations.findIndex(c => c.id === this.currentConversationId);
				if (convIndex >= 0) {
					this.settings.conversations[convIndex].messages = [];
					this.settings.conversations[convIndex].updatedAt = Date.now();
					await this.saveSettings();
				}
			}
			
			this.renderChatHistory();
			new Notice('Chat history cleared');
		}
	}

	private updatePromptInput(): void {
		if (!this.promptContainer) return;
		
		const textArea = this.promptContainer.querySelector('textarea');
		if (textArea instanceof HTMLTextAreaElement) {
			textArea.value = '';
		}
	}

	onClose() {
		this.aiService.cancelCurrentRequest();
		const {contentEl} = this;
		contentEl.empty();
	}
}

class TemplatesPickerModal extends Modal {
	private templates: PromptTemplate[];
	private context: string;
	private onApply: (prompt: string) => void;
	private selectedCategory: string = 'All';
	private searchQuery: string = '';
	private templatesContainer?: HTMLElement;

	constructor(app: App, templates: PromptTemplate[], context: string, onApply: (prompt: string) => void) {
		super(app);
		this.templates = templates;
		this.context = context;
		this.onApply = onApply;
	}

	onOpen() {
		const { contentEl } = this;
		contentEl.createEl('h2', { text: 'Prompt Templates' });

		// Search and filter row
		const filterRow = contentEl.createDiv({ cls: 'filter-row' });
		filterRow.style.display = 'flex';
		filterRow.style.gap = '0.5rem';
		filterRow.style.marginBottom = '1rem';

		// Search input
		const searchInput = filterRow.createEl('input', { type: 'text' });
		searchInput.placeholder = 'Search templates...';
		searchInput.style.flex = '1';
		searchInput.style.padding = '0.5rem';
		searchInput.style.borderRadius = 'var(--radius-s)';
		searchInput.style.border = '1px solid var(--background-modifier-border)';
		searchInput.addEventListener('input', (e) => {
			this.searchQuery = (e.target as HTMLInputElement).value;
			this.renderTemplates();
		});

		// Category filter
		const categorySelect = filterRow.createEl('select');
		categorySelect.style.padding = '0.5rem';
		categorySelect.style.borderRadius = 'var(--radius-s)';
		categorySelect.style.border = '1px solid var(--background-modifier-border)';
		
		const allOption = categorySelect.createEl('option', { text: 'All Categories', value: 'All' });
		const categories = getTemplateCategories(this.templates);
		categories.forEach(cat => {
			categorySelect.createEl('option', { text: cat, value: cat });
		});
		
		categorySelect.addEventListener('change', (e) => {
			this.selectedCategory = (e.target as HTMLSelectElement).value;
			this.renderTemplates();
		});

		// Templates container
		this.templatesContainer = contentEl.createDiv({ cls: 'templates-container' });
		this.templatesContainer.style.maxHeight = '400px';
		this.templatesContainer.style.overflowY = 'auto';

		this.renderTemplates();
	}

	private renderTemplates(): void {
		if (!this.templatesContainer) return;
		this.templatesContainer.empty();

		const filtered = filterTemplates(this.templates, this.selectedCategory, this.searchQuery);

		if (filtered.length === 0) {
			const empty = this.templatesContainer.createDiv({ cls: 'empty-state' });
			empty.style.textAlign = 'center';
			empty.style.padding = '2rem';
			empty.style.color = 'var(--text-muted)';
			empty.textContent = 'No templates found';
			return;
		}

		// Group by category
		const byCategory: Record<string, PromptTemplate[]> = {};
		filtered.forEach(t => {
			if (!byCategory[t.category]) {
				byCategory[t.category] = [];
			}
			byCategory[t.category].push(t);
		});

		Object.entries(byCategory).forEach(([category, templates]) => {
			const categoryHeader = this.templatesContainer!.createEl('h4', { text: category });
			categoryHeader.style.marginTop = '1rem';
			categoryHeader.style.marginBottom = '0.5rem';
			categoryHeader.style.color = 'var(--text-muted)';

			templates.forEach(template => {
				const item = this.templatesContainer!.createDiv({ cls: 'template-item' });
				item.style.padding = '0.75rem';
				item.style.marginBottom = '0.5rem';
				item.style.borderRadius = 'var(--radius-s)';
				item.style.border = '1px solid var(--background-modifier-border)';
				item.style.cursor = 'pointer';
				item.style.backgroundColor = 'var(--background-secondary)';

				item.addEventListener('mouseenter', () => {
					item.style.backgroundColor = 'var(--background-modifier-hover)';
				});
				item.addEventListener('mouseleave', () => {
					item.style.backgroundColor = 'var(--background-secondary)';
				});

				const header = item.createDiv({ cls: 'template-header' });
				header.style.display = 'flex';
				header.style.justifyContent = 'space-between';
				header.style.alignItems = 'center';

				header.createEl('strong', { text: template.name });
				if (!template.isBuiltIn) {
					const badge = header.createEl('span', { text: 'Custom' });
					badge.style.fontSize = 'var(--font-smallest)';
					badge.style.padding = '0.1rem 0.3rem';
					badge.style.borderRadius = 'var(--radius-s)';
					badge.style.backgroundColor = 'var(--interactive-accent)';
					badge.style.color = 'var(--text-on-accent)';
				}

				const desc = item.createDiv({ cls: 'template-desc' });
				desc.style.fontSize = 'var(--font-smaller)';
				desc.style.color = 'var(--text-muted)';
				desc.style.marginTop = '0.25rem';
				desc.textContent = template.description;

				item.addEventListener('click', () => {
					this.applyTemplate(template);
				});
			});
		});
	}

	private applyTemplate(template: PromptTemplate): void {
		// If template has variables, try to use context
		let appliedPrompt = template.prompt;
		
		// Replace common variables with context if available
		if (this.context) {
			appliedPrompt = appliedPrompt.replace(/\{text\}/g, this.context);
			appliedPrompt = appliedPrompt.replace(/\{content\}/g, this.context);
			appliedPrompt = appliedPrompt.replace(/\{code\}/g, this.context);
		}
		
		// For other variables, leave placeholder hints
		appliedPrompt = appliedPrompt.replace(/\{(\w+)\}/g, '[Enter $1 here]');
		
		this.onApply(appliedPrompt);
		this.close();
		new Notice(`Template "${template.name}" applied`);
	}

	onClose() {
		const { contentEl } = this;
		contentEl.empty();
	}
}
