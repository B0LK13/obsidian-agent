/**
 * AI Chat View
 */

import { ItemView, WorkspaceLeaf, Notice } from 'obsidian';
import { AIService } from '../services/ai-service';

export const VIEW_TYPE_AI_CHAT = 'ai-chat-view';

interface ChatMessage {
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
}

export class AIChatView extends ItemView {
    private aiService: AIService;
    private messages: ChatMessage[] = [];
    private inputEl: HTMLTextAreaElement;
    private messagesContainer: HTMLElement;

    constructor(leaf: WorkspaceLeaf, settings: any) {
        super(leaf);
        this.aiService = new AIService({
            llmEndpoint: settings.llmEndpoint,
            embedEndpoint: settings.embedEndpoint,
            vectorEndpoint: settings.vectorEndpoint,
            defaultModel: settings.defaultModel || 'llama3.2',
            useMemoryRAG: false,
            useHallucinationGuard: false,
            enableEvaluation: false
        });
    }

    getViewType(): string {
        return VIEW_TYPE_AI_CHAT;
    }

    getDisplayText(): string {
        return 'AI Chat';
    }

    async onOpen(): Promise<void> {
        const container = this.containerEl.children[1];
        container.empty();
        
        container.createEl('h4', { text: 'AI Agent Chat' });

        // Initialize
        const initialized = await this.aiService.initialize();
        if (initialized) {
            container.createEl('div', { 
                text: 'Connected to local AI',
                cls: 'ai-status-connected'
            });
        }

        // Messages
        this.messagesContainer = container.createEl('div', { 
            cls: 'ai-messages-container' 
        });

        this.addMessage({
            role: 'system',
            content: 'Hello! I am your local AI assistant with access to your knowledge base.',
            timestamp: new Date()
        });

        // Input
        const inputContainer = container.createEl('div', { cls: 'ai-input-container' });
        
        this.inputEl = inputContainer.createEl('textarea', {
            cls: 'ai-input',
            attr: { 
                placeholder: 'Ask about your notes...',
                rows: '3'
            }
        });

        const sendBtn = inputContainer.createEl('button', {
            text: 'Send',
            cls: 'ai-send-btn'
        });
        sendBtn.addEventListener('click', () => this.sendMessage());
    }

    private async sendMessage(): Promise<void> {
        const text = this.inputEl.value.trim();
        if (!text) return;

        this.addMessage({
            role: 'user',
            content: text,
            timestamp: new Date()
        });

        this.inputEl.value = '';
        this.inputEl.disabled = true;

        try {
            const result = await this.aiService.queryWithContext(text);

            this.addMessage({
                role: 'assistant',
                content: result.response,
                timestamp: new Date()
            });

        } catch (error) {
            new Notice('Error: ' + error.message);
        } finally {
            this.inputEl.disabled = false;
        }
    }

    private addMessage(message: ChatMessage): void {
        this.messages.push(message);

        const msgEl = this.messagesContainer.createEl('div', {
            cls: `ai-message ai-message-${message.role}`
        });

        const header = msgEl.createEl('div', { cls: 'ai-message-header' });
        header.createEl('span', { 
            text: message.role === 'assistant' ? 'AI' : 
                  message.role === 'user' ? 'You' : 'System'
        });

        const content = msgEl.createEl('div', { cls: 'ai-message-content' });
        content.textContent = message.content;

        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    async onClose(): Promise<void> {}
}
