/**
 * Enhanced Agent Modal with 2025 Chat UI Design Patterns
 * Features: Liquid Glass design, reactions, voice messages, threading, typing indicators
 */

import { App, Modal, Notice, TextAreaComponent, setTooltip, setIcon } from 'obsidian';
import { AIService } from './aiService';
import { ChatMessage, ObsidianAgentSettings } from './settings';
import { AgentService } from './src/services/agent/agentService';
import { parseAgentResponse } from './src/types/agentResponse';
import { calculateTokenCount, getUsageLevel, getUsageColor, formatTokenCount } from './tokenCounter';
import { 
        TypingIndicator,
        MessageReactions,
        ScrollToBottomButton,
        SearchInterface,
        MessageActions,
        NextStepButton,
        slideUp
} from './uiComponents';

export class EnhancedAgentModal extends Modal {
        // Core services
        private aiService: AIService;
        private agentService: AgentService | null;
        private settings: ObsidianAgentSettings;
        private saveSettings: () => Promise<void>;
        private onSubmit: (result: string) => void;

        // State
        private prompt: string = '';
        private context: string = '';
        private chatHistory: ChatMessage[] = [];
        private currentConversationId: string | null = null;
        private isStreaming: boolean = false;
        private currentResponse: string = '';

        // UI Components
        private typingIndicator!: TypingIndicator;
        private scrollButton!: ScrollToBottomButton;
        private searchInterface?: SearchInterface;
        private messageListEl!: HTMLElement;
        private chatHistoryContainer!: HTMLElement;
        private textAreaElement!: HTMLTextAreaElement;
        private submitButton!: HTMLButtonElement;
        private stopButton!: HTMLButtonElement;
        private tokenCounterContainer!: HTMLElement;
        private tokenCounterBar!: HTMLElement;
        private tokenCounterText!: HTMLElement;

        // Message reactions map
        private messageReactions: Map<number, MessageReactions> = new Map();

        constructor(
                app: App,
                aiService: AIService,
                settings: ObsidianAgentSettings,
                saveSettings: () => Promise<void>,
                context: string,
                onSubmit: (result: string) => void,
                agentService: AgentService | null = null
        ) {
                super(app);
                this.aiService = aiService;
                this.agentService = agentService;
                this.settings = settings;
                this.saveSettings = saveSettings;
                this.context = context;
                this.onSubmit = onSubmit;

                // Load active conversation
                if (this.settings.enableConversationPersistence && this.settings.activeConversationId) {
                        const activeConv = this.settings.conversations.find(c => c.id === this.settings.activeConversationId);
                        if (activeConv) {
                                this.currentConversationId = activeConv.id;
                                this.chatHistory = [...activeConv.messages];
                        }
                }
        }

        onOpen() {
                const { contentEl } = this;

                this.modalEl.addClass('obsidian-agent-modal');
                contentEl.addClass('oa-modal-content');

                // Glass morphism header
                const header = contentEl.createDiv({ cls: 'oa-modal-header-glass' });
                this.renderHeader(header);

                // Search interface (hidden by default)
                const searchContainer = contentEl.createDiv({ cls: 'oa-search-wrapper' });
                searchContainer.style.display = 'none';
                this.searchInterface = new SearchInterface(
                        searchContainer,
                        (query) => this.searchMessages(query),
                        (result) => this.scrollToMessage(result.id)
                );

                // Chat history container with message list
                this.chatHistoryContainer = contentEl.createDiv({ cls: 'chat-history-container' });
                this.messageListEl = this.chatHistoryContainer.createDiv({ cls: 'oa-message-list' });

                // Typing indicator
                this.typingIndicator = new TypingIndicator(this.messageListEl);

                // Scroll to bottom button
                this.scrollButton = new ScrollToBottomButton(
                        contentEl,
                        this.chatHistoryContainer,
                        () => this.scrollToBottom()
                );

                // Initial render
                this.renderChatHistory();

                // Input area
                this.renderInputArea(contentEl);

                // Focus input
                setTimeout(() => this.textAreaElement?.focus(), 0);
        }

        private renderHeader(header: HTMLElement) {
                const titleRow = header.createDiv({ cls: 'oa-header-row' });
                titleRow.style.display = 'flex';
                titleRow.style.justifyContent = 'space-between';
                titleRow.style.alignItems = 'center';

                // Title
                const titleGroup = titleRow.createDiv();
                titleGroup.createEl('h2', {
                        text: 'AI Agent Assistant',
                        cls: 'oa-modal-title'
                });
                titleGroup.createEl('p', {
                        text: 'Ask anything about your notes',
                        cls: 'oa-header-subtitle'
                });

                // Header actions
                const actions = titleRow.createDiv({ cls: 'oa-header-actions' });
                actions.style.display = 'flex';
                actions.style.gap = 'var(--oa-space-sm)';

                // Search button
                const searchBtn = actions.createEl('button', { cls: 'oa-input-action' });
                setIcon(searchBtn, 'search');
                setTooltip(searchBtn, 'Search conversation');
                searchBtn.addEventListener('click', () => {
                        const searchWrapper = this.contentEl.querySelector('.oa-search-wrapper') as HTMLElement;
                        if (searchWrapper) {
                                const isVisible = searchWrapper.style.display !== 'none';
                                searchWrapper.style.display = isVisible ? 'none' : 'block';
                                if (!isVisible) {
                                        this.searchInterface?.focus();
                                }
                        }
                });

                // Clear chat button
                const clearBtn = actions.createEl('button', { cls: 'oa-input-action' });
                setIcon(clearBtn, 'trash-2');
                setTooltip(clearBtn, 'Clear chat');
                clearBtn.addEventListener('click', () => this.clearChatWithConfirmation());

                // Export button
                const exportBtn = actions.createEl('button', { cls: 'oa-input-action' });
                setIcon(exportBtn, 'download');
                setTooltip(exportBtn, 'Export conversation');
                exportBtn.addEventListener('click', () => this.exportConversation());
        }

        private renderInputArea(container: HTMLElement) {
                const inputContainer = container.createDiv({ cls: 'oa-input-container' });

                // Token counter
                this.tokenCounterContainer = inputContainer.createDiv({ cls: 'token-counter-container' });
                const barContainer = this.tokenCounterContainer.createDiv({ cls: 'token-bar-container' });
                this.tokenCounterBar = barContainer.createDiv({ cls: 'token-bar-fill' });
                this.tokenCounterText = this.tokenCounterContainer.createDiv({ cls: 'token-text' });
                this.updateTokenCounter();

                // Input wrapper
                const inputWrapper = inputContainer.createDiv({ cls: 'oa-input-wrapper' });

                // Text area
                const textArea = new TextAreaComponent(inputWrapper);
                this.textAreaElement = textArea.inputEl as HTMLTextAreaElement;
                this.textAreaElement.addClass('oa-input');
                this.textAreaElement.placeholder = 'Type your message...';
                this.textAreaElement.addEventListener('keydown', (e) => this.handleKeyDown(e));
                textArea.onChange((value) => {
                        this.prompt = value;
                        this.updateTokenCounter();
                });

                // Input actions
                const inputActions = inputWrapper.createDiv({ cls: 'oa-input-actions' });

                // Voice input button
                const voiceBtn = inputActions.createEl('button', { cls: 'oa-input-action' });
                setIcon(voiceBtn, 'mic');
                setTooltip(voiceBtn, 'Voice input (coming soon)');
                voiceBtn.addEventListener('click', () => {
                        new Notice('Voice input feature coming soon!');
                });

                // Template button
                const templateBtn = inputActions.createEl('button', { cls: 'oa-input-action' });
                setIcon(templateBtn, 'layout-template');
                setTooltip(templateBtn, 'Use template');
                templateBtn.addEventListener('click', () => this.openTemplatesPicker());

                // Submit button
                this.submitButton = inputActions.createEl('button', {
                        cls: 'oa-input-action oa-input-action--primary'
                });
                setIcon(this.submitButton, 'send');
                setTooltip(this.submitButton, 'Send message (Enter)');
                this.submitButton.addEventListener('click', () => this.handleSubmit());

                // Stop button (for streaming)
                this.stopButton = inputActions.createEl('button', {
                        cls: 'oa-input-action oa-input-action--danger'
                });
                setIcon(this.stopButton, 'square');
                setTooltip(this.stopButton, 'Stop generation');
                this.stopButton.style.display = 'none';
                this.stopButton.addEventListener('click', () => this.stopGeneration());
        }

        private renderChatHistory() {
                this.messageListEl.empty();

                if (this.chatHistory.length === 0) {
                        this.showWelcomeMessage();
                        return;
                }

                this.chatHistory.forEach((message, index) => {
                        this.renderMessage(message, index);
                });

                this.scrollToBottom();
        }

        private renderMessage(message: ChatMessage, index: number) {
                const isUser = message.role === 'user';
                const messageEl = this.messageListEl.createDiv({
                        cls: `oa-message oa-message--${isUser ? 'user' : 'assistant'}`
                });

                // Animate new messages
                if (index === this.chatHistory.length - 1) {
                        slideUp(messageEl, 300);
                }

                // Message bubble
                const bubble = messageEl.createDiv({ cls: 'oa-message__bubble' });

                // Content
                const contentEl = bubble.createDiv({ cls: 'message-content' });
                if (isUser) {
                        contentEl.textContent = message.content;
                } else {
                        contentEl.innerHTML = this.renderMarkdown(message.content);
                        
                        // Parse for Next Step
                        const parsed = parseAgentResponse(message.content);
                        if (parsed.next_step) {
                            new NextStepButton(bubble, parsed.next_step.action, parsed.next_step.type as any, () => {
                                this.handleNextStepClick(parsed.next_step!);
                            });
                        }
                }

                // Streaming cursor for assistant
                if (!isUser && this.isStreaming && index === this.chatHistory.length - 1) {
                        contentEl.createSpan({ cls: 'oa-streaming-cursor' });
                }

                // Message metadata
                const metaEl = bubble.createDiv({ cls: 'message-meta' });
                metaEl.style.fontSize = 'var(--font-smallest)';
                metaEl.style.color = 'var(--text-muted)';
                metaEl.style.marginTop = 'var(--oa-space-xs)';

                const time = new Date(message.timestamp).toLocaleTimeString([], {
                        hour: '2-digit', 
                        minute: '2-digit'
                });
                metaEl.textContent = time;

                if (message.tokensUsed) {
                        metaEl.textContent += ` · ${message.tokensUsed} tokens`;
                }
                if (message.fromCache) {
                        metaEl.textContent += ' · cached';
                }

                // Message actions
                new MessageActions(messageEl, [
                        {
                                icon: 'copy',
                                label: 'Copy message',
                                onClick: () => {
                                        navigator.clipboard.writeText(message.content);
                                        new Notice('Message copied to clipboard');
                                }
                        },
                        {
                                icon: 'quote',
                                label: 'Reply',
                                onClick: () => this.quoteMessage(message)
                        },
                        {
                                icon: 'trash-2',
                                label: 'Delete',
                                onClick: () => this.deleteMessage(index)
                        }
                ]);

                // Reactions for assistant messages
                if (!isUser) {
                        const reactions = new MessageReactions(messageEl, (emoji) => {
                                new Notice(`Reacted with ${emoji}`);
                        });
                        this.messageReactions.set(index, reactions);
                }

                // Insert before typing indicator
                const typingEl = this.messageListEl.querySelector('.oa-typing-indicator');
                if (typingEl) {
                        this.messageListEl.insertBefore(messageEl, typingEl);
                } else {
                        this.messageListEl.appendChild(messageEl);
                }
        }

        private handleNextStepClick(nextStep: any) {
            const action = nextStep.action;
            const type = nextStep.type || 'do_now';

            if (type === 'unblock') {
                this.prompt = `Here is the info you needed: `;
            } else if (type === 'choose_path') {
                this.prompt = `I'd like to proceed with path: ${action}`;
            } else {
                this.prompt = `Please proceed with: ${action}`;
            }

            this.textAreaElement.value = this.prompt;
            this.textAreaElement.focus();
            this.updateTokenCounter();
            new Notice('Next step selected. Press Enter to confirm.');
        }

        private renderMarkdown(text: string): string {
                // Enhanced markdown rendering
                let html = text
                        .replace(/```yaml\n([\s\S]*?)```/g, '<div class="oa-yaml-block"><pre><code>$1</code></pre></div>')
                        .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code class="language-$1">$2</code></pre>')
                        .replace(/`([^`]+)`/g, '<code>$1</code>')
                        .replace(/\*\*\*([^*]+)\*\*\*/g, '<strong><em>$1</em></strong>')
                        .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
                        .replace(/\*([^*]+)\*/g, '<em>$1</em>')
                        .replace(/~~([^~]+)~~/g, '<del>$1</del>')
                        .replace(/### (.+)/g, '<h4>$1</h4>')
                        .replace(/## (.+)/g, '<h3>$1</h3>')
                        .replace(/# (.+)/g, '<h2>$1</h2>')
                        .replace(/^> (.+)/gm, '<blockquote>$1</blockquote>')
                        .replace(/^- \[ \] (.+)/gm, '<div class="oa-task oa-task--todo">$1</div>')
                        .replace(/^- \[x\] (.+)/gm, '<div class="oa-task oa-task--done">$1</div>')
                        .replace(/^[-*] (.+)/gm, '<li>$1</li>')
                        .replace(/\n/g, '<br>');

                html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
                return html;
        }

        private showWelcomeMessage() {
                const welcomeEl = this.messageListEl.createDiv({ cls: 'oa-welcome-message' });
                welcomeEl.style.textAlign = 'center';
                welcomeEl.style.padding = 'var(--oa-space-2xl)';
                welcomeEl.style.color = 'var(--text-muted)';

                const icon = welcomeEl.createDiv({ cls: 'oa-welcome-icon' });
                icon.style.fontSize = '3rem';
                icon.style.marginBottom = 'var(--oa-space-md)';
                icon.textContent = '✨';

                welcomeEl.createEl('h3', { text: 'Welcome to AI Agent' });
                welcomeEl.createEl('p', {
                        text: 'Ask me anything about your notes, or use templates for common tasks.'
                });
        }

        private async handleSubmit(bypassCache: boolean = false) {
                if (!this.prompt.trim()) {
                        new Notice('Please enter a message');
                        return;
                }

                const userPrompt = this.prompt;

                if (bypassCache) {
                        this.aiService.setBypassCache(true);
                }

                this.addMessage('user', this.prompt);
                this.prompt = '';
                this.textAreaElement.value = '';
                this.updateTokenCounter();
                this.typingIndicator.show();

                this.isStreaming = true;
                this.submitButton.style.display = 'none';
                this.stopButton.style.display = 'flex';

                try {
                        if (this.agentService) {
                                const agentResponse = await this.agentService.run(userPrompt);
                                this.currentResponse = agentResponse;
                                this.addMessage('assistant', agentResponse);
                                this.typingIndicator.hide();
                                this.isStreaming = false;
                                this.submitButton.style.display = 'flex';
                                this.stopButton.style.display = 'none';
                        } else {
                                const result = await this.aiService.generateCompletion({
                                        prompt: userPrompt,
                                        context: this.context,
                                        stream: true,
                                        onChunk: (chunk) => {
                                                this.onStreamChunk(chunk);
                                                if (chunk.done) {
                                                        this.finishStreaming(result);
                                                }
                                        },
                                        onProgress: (progress) => {
                                                if (this.isStreaming) {
                                                        this.onStreamProgress(progress);
                                                }
                                        }
                                });
                        }
                } catch (error: any) {
                        if (error.name !== 'AbortError') {
                                new Notice(`Error: ${error.message}`);
                                console.error('Agent Error:', error);
                        }
                        this.stopStreaming();
                }
        }

        private onStreamChunk(chunk: any) {
                if (chunk.done) return;
                if (chunk.content) {
                        this.currentResponse += chunk.content;
                        if (this.chatHistory.length > 0) {
                                const lastMsg = this.chatHistory[this.chatHistory.length - 1];
                                if (lastMsg.role === 'assistant') {
                                        lastMsg.content = this.currentResponse;
                                        this.updateLastMessage();
                                }
                        }
                }
        }

        private onStreamProgress(progress: string) {
                this.typingIndicator.hide();
                if (this.chatHistory.length === 0 ||
                        this.chatHistory[this.chatHistory.length - 1].role !== 'assistant') {
                        this.addMessage('assistant', progress, false);
                } else {
                        const lastMsg = this.chatHistory[this.chatHistory.length - 1];
                        lastMsg.content = progress;
                        this.updateLastMessage();
                }
                this.scrollToBottom();
        }

        private finishStreaming(result: any) {
                this.stopStreaming();
                if (this.currentResponse) {
                        if (this.chatHistory.length > 0) {
                                const lastMsg = this.chatHistory[this.chatHistory.length - 1];
                                if (lastMsg.role === 'assistant') {
                                        lastMsg.content = this.currentResponse;
                                        lastMsg.tokensUsed = result.tokensUsed;
                                        lastMsg.fromCache = result.fromCache;
                                }
                        }
                        this.renderChatHistory();
                        this.saveCurrentConversation();
                        if (result.fromCache) {
                                new Notice('Response loaded from cache');
                        }
                        this.onSubmit(this.currentResponse);
                }
                this.currentResponse = '';
        }

        private stopStreaming() {
                this.isStreaming = false;
                this.typingIndicator.hide();
                this.submitButton.style.display = 'flex';
                this.stopButton.style.display = 'none';
        }

        private stopGeneration() {
                this.aiService.cancelCurrentRequest();
                this.stopStreaming();
                new Notice('Generation stopped');
        }

        private addMessage(role: 'user' | 'assistant', content: string, fromCache?: boolean, tokensUsed?: number) {
                this.chatHistory.push({
                        role,
                        content,
                        timestamp: Date.now(),
                        fromCache,
                        tokensUsed
                });
                this.renderMessage(this.chatHistory[this.chatHistory.length - 1], this.chatHistory.length - 1);
                this.scrollToBottom();
        }

        private updateLastMessage() {
                const messages = this.messageListEl.querySelectorAll('.oa-message');
                if (messages.length > 0) {
                        const lastMsg = messages[messages.length - 1];
                        const contentEl = lastMsg.querySelector('.message-content');
                        if (contentEl) {
                                const lastChatMsg = this.chatHistory[this.chatHistory.length - 1];
                                contentEl.innerHTML = this.renderMarkdown(lastChatMsg.content);
                                if (this.isStreaming && lastChatMsg.role === 'assistant') {
                                        contentEl.createSpan({ cls: 'oa-streaming-cursor' });
                                }
                        }
                }
        }

        private updateTokenCounter() {
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
                this.tokenCounterBar.style.width = `${Math.min(100, tokenCount.percentage)}%`;
                this.tokenCounterBar.style.backgroundColor = color;
                this.tokenCounterText.empty();
                this.tokenCounterText.createSpan({
                        text: `${formatTokenCount(tokenCount.total)} / ${formatTokenCount(tokenCount.limit)} tokens`
                });
        }

        private handleKeyDown(event: KeyboardEvent) {
                if (event.key === 'Enter' && !event.shiftKey) {
                        event.preventDefault();
                        this.handleSubmit();
                }
                if (event.key === 'Escape') {
                        this.close();
                }
                if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
                        event.preventDefault();
                        this.clearChatWithConfirmation();
                }
        }

        private scrollToBottom() {
                this.chatHistoryContainer.scrollTop = this.chatHistoryContainer.scrollHeight;
        }

        private searchMessages(query: string): any[] {
                const results: any[] = [];
                const lowerQuery = query.toLowerCase();
                this.chatHistory.forEach((msg, index) => {
                        const content = msg.content.toLowerCase();
                        const matchIndex = content.indexOf(lowerQuery);
                        if (matchIndex !== -1) {
                                results.push({
                                        id: String(index),
                                        content: msg.content,
                                        timestamp: msg.timestamp,
                                        matchRanges: [[matchIndex, matchIndex + query.length]]
                                });
                        }
                });
                return results;
        }

        private scrollToMessage(id: string) {
                const messages = this.messageListEl.querySelectorAll('.oa-message');
                const index = parseInt(id);
                if (messages[index]) {
                        messages[index].scrollIntoView({ behavior: 'smooth', block: 'center' });
                        messages[index].classList.add('oa-message--highlighted');
                        setTimeout(() => {
                                messages[index].classList.remove('oa-message--highlighted');
                        }, 2000);
                }
        }

        private quoteMessage(message: ChatMessage) {
                const quote = message.content.split('\n').map(line => `> ${line}`).join('\n');
                this.prompt = `${quote}\n\n`;
                this.textAreaElement.value = this.prompt;
                this.textAreaElement.focus();
                this.updateTokenCounter();
        }

        private deleteMessage(index: number) {
                if (!confirm('Delete this message?')) return;
                this.chatHistory.splice(index, 1);
                this.renderChatHistory();
                this.saveCurrentConversation();
        }

        private clearChatWithConfirmation() {
                if (this.chatHistory.length === 0) return;
                if (confirm('Clear the entire conversation?')) {
                        this.chatHistory = [];
                        this.currentConversationId = null;
                        this.settings.activeConversationId = undefined;
                        this.renderChatHistory();
                        this.saveSettings();
                        new Notice('Conversation cleared');
                }
        }

        private exportConversation() {
                if (this.chatHistory.length === 0) {
                        new Notice('No conversation to export');
                        return;
                }
                let markdown = `# AI Conversation Export\n\n`;
                markdown += `*Exported on ${new Date().toLocaleString()}*\n\n---\n\n`;
                this.chatHistory.forEach(msg => {
                        const role = msg.role === 'user' ? '**You**' : '**AI**';
                        const time = new Date(msg.timestamp).toLocaleString();
                        markdown += `${role} *(${time})*:\n\n${msg.content}\n\n---\n\n`;
                });
                navigator.clipboard.writeText(markdown);
                new Notice('Conversation copied to clipboard');
        }

        private openTemplatesPicker() {
                new Notice('Template picker coming soon!');
        }

        private async saveCurrentConversation() {
                if (!this.settings.enableConversationPersistence) return;
                const now = Date.now();
                if (this.currentConversationId) {
                        const index = this.settings.conversations.findIndex(c => c.id === this.currentConversationId);
                        if (index >= 0) {
                                this.settings.conversations[index].messages = [...this.chatHistory];
                                this.settings.conversations[index].updatedAt = now;
                        }
                } else {
                        this.currentConversationId = `conv_${now}_${Math.random().toString(36).substr(2, 9)}`;
                        this.settings.conversations.unshift({
                                id: this.currentConversationId,
                                title: this.generateConversationTitle(),
                                messages: [...this.chatHistory],
                                createdAt: now,
                                updatedAt: now
                        });
                        if (this.settings.conversations.length > this.settings.maxConversations) {
                                this.settings.conversations = this.settings.conversations.slice(0, this.settings.maxConversations);
                        }
                }
                this.settings.activeConversationId = this.currentConversationId;
                await this.saveSettings();
        }

        private generateConversationTitle(): string {
                const firstUserMsg = this.chatHistory.find(m => m.role === 'user');
                if (firstUserMsg) {
                        return firstUserMsg.content.substring(0, 50) + (firstUserMsg.content.length > 50 ? '...' : '');
                }
                return `Conversation ${new Date().toLocaleDateString()}`;
        }

        onClose() {
                this.aiService.cancelCurrentRequest();
                this.typingIndicator.destroy();
                this.scrollButton.destroy();
                this.messageReactions.forEach(r => r.destroy());
                this.contentEl.empty();
        }
}
