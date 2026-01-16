import { App, Modal, Notice, TextAreaComponent, setTooltip } from 'obsidian';
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

		headerContainer.createEl('p', {
			text: 'Enter your prompt below. The agent will use current note as context.',
			cls: 'setting-item-description'
		});

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
		textArea.inputEl.style.width = '100%';
		textArea.inputEl.style.minHeight = '100px';
		textArea.inputEl.placeholder = 'What would you like AI to help with?';
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

		const submitButton = buttonContainer.createEl('button', {
			text: 'Generate',
			cls: 'mod-cta'
		});
		submitButton.addEventListener('click', async () => {
			await this.handleSubmit(submitButton);
		});

		textArea.inputEl.focus();
	}

	private async handleSubmit(submitButton: HTMLElement): Promise<void> {
		if (!this.prompt.trim()) {
			new Notice('Please enter a prompt');
			return;
		}

		submitButton.setAttr('disabled', 'true');
		submitButton.textContent = 'Generating...';

		this.addMessageToHistory('user', this.prompt);
		this.renderChatHistory();

		try {
			const result = await this.aiService.generateCompletion(this.prompt, this.context);
			this.addMessageToHistory('assistant', result);
			this.renderChatHistory();
			
			this.onSubmit(result);
			this.prompt = '';
			this.updatePromptInput();
		} catch (error: any) {
			new Notice(`Error: ${error.message}`);
			console.error('Agent Modal Error:', error);
		} finally {
			submitButton.removeAttribute('disabled');
			submitButton.textContent = 'Generate';
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
			contentEl.textContent = message.content;
			contentEl.style.whiteSpace = 'pre-wrap';
			contentEl.style.wordBreak = 'break-word';
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
		const {contentEl} = this;
		contentEl.empty();
	}
}
