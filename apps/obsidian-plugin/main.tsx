import { App, Plugin, PluginSettingTab, Setting, ItemView, WorkspaceLeaf, Notice, MarkdownRenderer, Component, TFile } from 'obsidian';
import * as React from 'react';
import * as ReactDOM from 'react-dom/client';
import { VaultManager } from './src/VaultManager';
import { OpenAIService, AGENT_SYSTEM_PROMPT, ChatMessage } from './src/OpenAIService';
import { ToolHandler } from './src/ToolHandler';
import { SyncClient, SyncEventType } from './src/SyncClient';

export const AGENT_VIEW_TYPE = 'pkm-agent-view';

// ============================================
// SETTINGS
// ============================================

interface PKMAgentSettings {
    openaiApiKey: string;
    model: string;
    baseUrl: string;
    temperature: number;
    enableContextAwareness: boolean;
}

const DEFAULT_SETTINGS: PKMAgentSettings = {
    openaiApiKey: '',
    model: 'gpt-4o',
    baseUrl: 'https://api.openai.com/v1',
    temperature: 0.7,
    enableContextAwareness: true,
};

// ============================================
// ICONS
// ============================================

const SendIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
    </svg>
);

const BotIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
        <rect x="3" y="11" width="18" height="10" rx="2"/>
        <circle cx="12" cy="5" r="2"/>
        <path d="M12 7v4"/>
    </svg>
);

// ============================================
// REACT COMPONENTS
// ============================================

const Markdown = ({ content, app }: { content: string; app: App }) => {
    const containerRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        if (containerRef.current) {
            containerRef.current.empty();
            MarkdownRenderer.render(app, content, containerRef.current, '/', new Component());
        }
    }, [content, app]);

    return <div ref={containerRef} className="markdown-content markdown-rendered" />;
};

const MessageBubble = ({ role, content, app, isStreaming }: { 
    role: string;
    content: string | null;
    app: App;
    isStreaming?: boolean;
}) => {
    if (role === 'system' || role === 'tool') return null;
    const isUser = role === 'user';

    return (
        <div className={`pkm-agent-message ${role} ${isStreaming ? 'streaming' : ''}`}>
            {!isUser && (
                <div className="message-avatar">
                    <BotIcon />
                </div>
            )}
            <div className="message-content">
                {content && (
                    <div className="message-bubble">
                        <Markdown content={content} app={app} />
                    </div>
                )}
            </div>
        </div>
    );
};

interface AgentViewProps {
    openAIService: OpenAIService;
    toolHandler: ToolHandler;
    app: App;
}

interface Message {
    id: string;
    role: string;
    content: string | null;
    tool_calls?: any[];
    timestamp: number;
}

const AgentViewComponent: React.FC<AgentViewProps> = ({ openAIService, toolHandler, app }) => {
    const [input, setInput] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const [streamingContent, setStreamingContent] = React.useState('');
    const [messages, setMessages] = React.useState<Message[]>([]);
    const messagesEndRef = React.useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    React.useEffect(() => {
        scrollToBottom();
    }, [messages, streamingContent]);

    const handleSend = async () => {
        if (!input.trim() || loading) return;

        const userMessage: Message = {
            id: crypto.randomUUID(),
            role: 'user',
            content: input,
            timestamp: Date.now(),
        };

        setMessages(prev => [...prev, userMessage]);
        setInput('');
        setLoading(true);
        setStreamingContent('');

        try {
            const chatMessages: ChatMessage[] = [
                { role: 'system', content: AGENT_SYSTEM_PROMPT },
                ...messages.map(m => ({ role: m.role as any, content: m.content })),
                { role: 'user', content: input },
            ];

            const response = await openAIService.chat(
                chatMessages,
                toolHandler.getTools(),
                (chunk) => setStreamingContent(prev => prev + chunk)
            );

            // Handle tool calls
            if (response.tool_calls && response.tool_calls.length > 0) {
                for (const tc of response.tool_calls) {
                    const args = JSON.parse(tc.function.arguments);
                    const result = await toolHandler.executeTool(tc.function.name, args);
                    new Notice(`Tool ${tc.function.name}: ${result.substring(0, 100)}`);
                }
            }

            const assistantMessage: Message = {
                id: crypto.randomUUID(),
                role: 'assistant',
                content: response.content || streamingContent,
                tool_calls: response.tool_calls,
                timestamp: Date.now(),
            };

            setMessages(prev => [...prev, assistantMessage]);
            setStreamingContent('');
        } catch (error) {
            new Notice(`Error: ${error}`);
            console.error('Chat error:', error);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="pkm-agent-view">
            <div className="pkm-agent-messages">
                {messages.map(msg => (
                    <MessageBubble
                        key={msg.id}
                        role={msg.role}
                        content={msg.content}
                        app={app}
                    />
                ))}
                {streamingContent && (
                    <MessageBubble
                        role="assistant"
                        content={streamingContent}
                        app={app}
                        isStreaming={true}
                    />
                )}
                <div ref={messagesEndRef} />
            </div>
            <div className="pkm-agent-input-area">
                <textarea
                    className="pkm-agent-input"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask me anything about your vault..."
                    disabled={loading}
                    rows={1}
                />
                <button
                    className="pkm-agent-send-btn"
                    onClick={handleSend}
                    disabled={loading || !input.trim()}
                >
                    <SendIcon />
                </button>
            </div>
        </div>
    );
};

// ============================================
// OBSIDIAN VIEW
// ============================================

class AgentView extends ItemView {
    private root: ReactDOM.Root | null = null;
    private plugin: PKMAgentPlugin;

    constructor(leaf: WorkspaceLeaf, plugin: PKMAgentPlugin) {
        super(leaf);
        this.plugin = plugin;
    }

    getViewType(): string {
        return AGENT_VIEW_TYPE;
    }

    getDisplayText(): string {
        return 'PKM Agent';
    }

    getIcon(): string {
        return 'bot';
    }

    async onOpen(): Promise<void> {
        const container = this.containerEl.children[1];
        container.empty();

        const openAIService = new OpenAIService({
            apiKey: this.plugin.settings.openaiApiKey,
            model: this.plugin.settings.model,
            baseUrl: this.plugin.settings.baseUrl,
            temperature: this.plugin.settings.temperature,
        });

        const toolHandler = new ToolHandler(this.app);

        this.root = ReactDOM.createRoot(container);
        this.root.render(
            <AgentViewComponent
                openAIService={openAIService}
                toolHandler={toolHandler}
                app={this.app}
            />
        );
    }

    async onClose(): Promise<void> {
        this.root?.unmount();
    }
}

// ============================================
// MAIN PLUGIN
// ============================================

export default class PKMAgentPlugin extends Plugin {
    settings: PKMAgentSettings;
    syncClient: SyncClient;

    async onload() {
        await this.loadSettings();

        // Register view
        this.registerView(AGENT_VIEW_TYPE, (leaf) => new AgentView(leaf, this));

        // Ribbon icon
        this.addRibbonIcon('bot', 'PKM Agent', () => this.activateView());

        // Commands
        this.addCommand({
            id: 'open-pkm-agent',
            name: 'Open PKM Agent Chat',
            callback: () => this.activateView(),
        });

        this.addCommand({
            id: 'quick-daily-note',
            name: 'Quick: Create Daily Note',
            callback: async () => {
                const vm = new VaultManager(this.app);
                const result = await vm.getDailyNote();
                if (result.success) {
                    new Notice(result.created ? 'Created daily note' : 'Opened daily note');
                    if (result.path) {
                        await this.app.workspace.openLinkText(result.path, '', false);
                    }
                }
            },
        });

        // Settings tab
        this.addSettingTab(new AgentSettingTab(this.app, this));

        // Initialize sync client
        this.syncClient = new SyncClient({ url: 'ws://127.0.0.1:27125' });
        await this.initializeSync();

        console.log('PKM Agent loaded');
    }

    async initializeSync() {
        try {
            this.syncClient.connect();

            this.syncClient.on(SyncEventType.FILE_CREATED, (event) => {
                console.log('Remote file created:', event.data?.path);
            });

            this.syncClient.on(SyncEventType.NOTE_INDEXED, (event) => {
                console.log('Note indexed:', event.data);
            });

            // Register vault events
            this.registerEvent(
                this.app.vault.on('create', async (file) => {
                    if (file instanceof TFile && file.extension === 'md') {
                        await this.syncClient.sendEvent({
                            event_type: SyncEventType.FILE_CREATED,
                            data: { path: file.path, name: file.name },
                        });
                    }
                })
            );

            this.registerEvent(
                this.app.vault.on('modify', async (file) => {
                    if (file instanceof TFile && file.extension === 'md') {
                        await this.syncClient.sendEvent({
                            event_type: SyncEventType.FILE_MODIFIED,
                            data: { path: file.path, name: file.name },
                        });
                    }
                })
            );

            this.registerEvent(
                this.app.vault.on('delete', async (file) => {
                    if (file instanceof TFile && file.extension === 'md') {
                        await this.syncClient.sendEvent({
                            event_type: SyncEventType.FILE_DELETED,
                            data: { path: file.path, name: file.name },
                        });
                    }
                })
            );
        } catch (error) {
            console.error('Failed to initialize sync:', error);
        }
    }

    async activateView() {
        const { workspace } = this.app;
        let leaf = workspace.getLeavesOfType(AGENT_VIEW_TYPE)[0];

        if (!leaf) {
            const rightLeaf = workspace.getRightLeaf(false);
            if (rightLeaf) {
                leaf = rightLeaf;
                await leaf.setViewState({ type: AGENT_VIEW_TYPE, active: true });
            }
        }

        if (leaf) {
            workspace.revealLeaf(leaf);
        }
    }

    async onunload() {
        this.syncClient?.disconnect();
        console.log('PKM Agent unloaded');
    }

    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }

    async saveSettings() {
        await this.saveData(this.settings);
    }
}

// ============================================
// SETTINGS TAB
// ============================================

class AgentSettingTab extends PluginSettingTab {
    plugin: PKMAgentPlugin;

    constructor(app: App, plugin: PKMAgentPlugin) {
        super(app, plugin);
        this.plugin = plugin;
    }

    display(): void {
        const { containerEl } = this;
        containerEl.empty();

        containerEl.createEl('h2', { text: 'PKM Agent Settings' });

        new Setting(containerEl)
            .setName('OpenAI API Key')
            .setDesc('Your OpenAI API key')
            .addText(text => text
                .setPlaceholder('sk-...')
                .setValue(this.plugin.settings.openaiApiKey)
                .onChange(async (value) => {
                    this.plugin.settings.openaiApiKey = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Model')
            .setDesc('GPT model to use')
            .addDropdown(dropdown => dropdown
                .addOption('gpt-4o', 'GPT-4o')
                .addOption('gpt-4o-mini', 'GPT-4o Mini')
                .addOption('gpt-4-turbo', 'GPT-4 Turbo')
                .addOption('gpt-3.5-turbo', 'GPT-3.5 Turbo')
                .setValue(this.plugin.settings.model)
                .onChange(async (value) => {
                    this.plugin.settings.model = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Base URL')
            .setDesc('API endpoint (for local LLMs)')
            .addText(text => text
                .setPlaceholder('https://api.openai.com/v1')
                .setValue(this.plugin.settings.baseUrl)
                .onChange(async (value) => {
                    this.plugin.settings.baseUrl = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Temperature')
            .setDesc('Response creativity (0-1)')
            .addSlider(slider => slider
                .setLimits(0, 1, 0.1)
                .setValue(this.plugin.settings.temperature)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    this.plugin.settings.temperature = value;
                    await this.plugin.saveSettings();
                }));
    }
}
