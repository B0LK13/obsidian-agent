import { ItemView, WorkspaceLeaf, TextAreaComponent, ButtonComponent } from 'obsidian';
import { AIService } from './aiService';

export const CHAT_VIEW_TYPE = 'obsidian-agent-chat-view';

export class ChatView extends ItemView {
	private aiService: AIService;
	private conversationId: string;
	private chatContainer: HTMLElement;
	private inputArea: TextAreaComponent;

	constructor(leaf: WorkspaceLeaf, aiService: AIService) {
		super(leaf);
		this.aiService = aiService;
		this.conversationId = 'sidebar-chat-' + Date.now();
	}

	getViewType(): string {
		return CHAT_VIEW_TYPE;
	}

	getDisplayText(): string {
		return 'AI Chat';
	}

	getIcon(): string {
		return 'message-square';
	}

	async onOpen(): Promise<void> {
		const container = this.containerEl.children[1];
		container.empty();
		container.addClass('obsidian-agent-chat-view');

		// Create header
		const header = container.createEl('div', { cls: 'chat-header' });
		header.createEl('h4', { text: 'AI Assistant Chat' });

		const clearBtn = new ButtonComponent(header);
		clearBtn.setButtonText('Clear Chat')
			.setClass('mod-cta')
			.onClick(() => this.clearChat());

		// Create chat messages container
		this.chatContainer = container.createEl('div', { cls: 'chat-messages' });

		// Create input area
		const inputContainer = container.createEl('div', { cls: 'chat-input-container' });
		
		this.inputArea = new TextAreaComponent(inputContainer);
		this.inputArea.inputEl.placeholder = 'Type your message...';
		this.inputArea.inputEl.rows = 3;
		this.inputArea.inputEl.addEventListener('keydown', (e) => {
			if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
				e.preventDefault();
				this.sendMessage();
			}
		});

		const sendBtn = new ButtonComponent(inputContainer);
		sendBtn.setButtonText('Send (Ctrl+Enter)')
			.setClass('mod-cta')
			.onClick(() => this.sendMessage());

		// Load conversation history
		this.loadHistory();
	}

	private loadHistory(): void {
		const history = this.aiService.getConversationHistory().getHistory(this.conversationId);
		history.forEach(msg => {
			this.addMessageToUI(msg.role, msg.content);
		});
	}

	private async sendMessage(): Promise<void> {
		const message = this.inputArea.getValue().trim();
		if (!message) return;

		// Add user message to UI
		this.addMessageToUI('user', message);
		this.inputArea.setValue('');

		// Add loading indicator
		const loadingEl = this.chatContainer.createEl('div', { cls: 'chat-message assistant loading' });
		loadingEl.createEl('div', { cls: 'message-content', text: 'Thinking...' });

		try {
			const response = await this.aiService.generateCompletion(
				message,
				undefined,
				this.conversationId
			);

			// Remove loading indicator
			loadingEl.remove();

			// Add assistant response
			this.addMessageToUI('assistant', response);
		} catch (error) {
			loadingEl.remove();
			this.addMessageToUI('system', `Error: ${error.message}`);
		}

		// Scroll to bottom
		this.chatContainer.scrollTop = this.chatContainer.scrollHeight;
	}

	private addMessageToUI(role: string, content: string): void {
		const messageEl = this.chatContainer.createEl('div', { cls: `chat-message ${role}` });
		
		const roleLabel = messageEl.createEl('div', { cls: 'message-role' });
		roleLabel.textContent = role === 'user' ? 'You' : role === 'assistant' ? 'AI' : 'System';
		
		const contentEl = messageEl.createEl('div', { cls: 'message-content' });
		contentEl.textContent = content;
		
		const timestamp = messageEl.createEl('div', { cls: 'message-timestamp' });
		timestamp.textContent = new Date().toLocaleTimeString();
	}

	private clearChat(): void {
		this.aiService.getConversationHistory().clearHistory(this.conversationId);
		this.chatContainer.empty();
		this.conversationId = 'sidebar-chat-' + Date.now();
	}

	async onClose(): Promise<void> {
		// Cleanup if needed
	}
}
