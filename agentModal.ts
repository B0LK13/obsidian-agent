import { App, Modal, Notice, TextAreaComponent, setTooltip, MarkdownRenderer } from 'obsidian';
import { AIService } from './aiService';

interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
	timestamp: number;
}

export class AgentModal extends Modal {
	private aiService: AIService;
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

	constructor(app: App, aiService: AIService, context: string, onSubmit: (result: string) => void) {
		super(app);
		this.aiService = aiService;
		this.context = context;
		this.onSubmit = onSubmit;
	}

	onOpen() {
		const {contentEl} = this;

		contentEl.createEl('h2', {text: 'AI Agent Assistant'});

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
		});

		const buttonContainer = contentEl.createDiv('button-container');
		buttonContainer.style.marginTop = '1rem';
		buttonContainer.style.display = 'flex';
		buttonContainer.style.justifyContent = 'flex-end';
		buttonContainer.style.gap = '0.5rem';

		const cancelButton = buttonContainer.createEl('button', {text: 'Cancel'});
		cancelButton.addEventListener('click', () => {
			this.close();
		});

		this.submitButton = buttonContainer.createEl('button', {
			text: 'Generate',
			cls: 'mod-cta'
		}) as HTMLButtonElement;
		this.submitButton.addEventListener('click', async () => {
			if (this.submitButton) {
				await this.handleSubmit(this.submitButton as HTMLElement);
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

	private async handleSubmit(submitButton: HTMLElement): Promise<void> {
		if (!this.prompt.trim()) {
			new Notice('Please enter a prompt');
			return;
		}

		submitButton.setAttr('disabled', 'true');
		submitButton.textContent = 'Generating...';
		this.stopButton.style.display = 'none';
		this.isStreaming = true;
		this.currentResponse = '';

		this.addMessageToHistory('user', this.prompt);
		this.renderChatHistory();

		try {
			await this.aiService.generateCompletion(
				this.prompt,
				this.context,
				true,
				(chunk) => {
					this.onStreamChunk(chunk);
					if (chunk.done) {
						this.isStreaming = false;
						this.stopButton.style.display = 'none';
					}
				},
				(progress) => {
					if (this.isStreaming) {
						this.stopButton.style.display = 'block';
						this.onStreamProgress(progress);
					}
				}
			);
			
			if (this.currentResponse) {
				this.addMessageToHistory('assistant', this.currentResponse);
				this.renderChatHistory();
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
			this.stopButton.style.display = 'none';
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

	private onStreamChunk(chunk: any): void {
		if (chunk.done) {
			return;
		}

		if (chunk.content) {
			this.currentResponse += chunk.content;
			
			if (this.chatHistory.length > 0 && this.chatHistory[this.chatHistory.length - 1].role === 'assistant') {
				const lastMessage = this.chatHistory[this.chatHistory.length - 1];
				if (lastMessage) {
					lastMessage.content = this.currentResponse;
				}
			}
			
			this.renderChatHistory();
		}
	}

	private onStreamProgress(progress: string): void {
		if (progress && this.isStreaming) {
			if (this.chatHistory.length === 0 || this.chatHistory[this.chatHistory.length - 1]?.role !== 'assistant') {
				this.addMessageToHistory('assistant', '');
			}
			
			if (this.chatHistory.length > 0) {
				const lastMessage = this.chatHistory[this.chatHistory.length - 1];
				if (lastMessage) {
					lastMessage.content = progress;
				}
			}
			
			this.renderChatHistory();
		}
	}
	}

	private addMessageToHistory(role: 'user' | 'assistant', content: string): void {
		this.chatHistory.push({
			role,
			content,
			timestamp: Date.now()
		});
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

			const roleLabel = headerEl.createEl('span', { 
				text: message.role === 'user' ? 'You' : 'AI Agent',
				cls: message.role === 'user' ? 'user-label' : 'assistant-label'
			});
			roleLabel.style.fontWeight = 'bold';
			
			const timestamp = new Date(message.timestamp).toLocaleTimeString();
			headerEl.createEl('span', { text: timestamp });

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

	private clearChatWithConfirmation(): void {
		if (this.chatHistory.length === 0) {
			new Notice('Chat is already empty');
			return;
		}

		const confirmClear = confirm('Are you sure you want to clear the entire chat history? This action cannot be undone.');
		
		if (confirmClear) {
			this.chatHistory = [];
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
