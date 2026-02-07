import { App, Plugin, PluginSettingTab, Setting, ItemView, WorkspaceLeaf, Notice, MarkdownRenderer, Component, Menu, TFile } from 'obsidian';
import * as React from 'react';
import * as ReactDOM from 'react-dom/client';
import { VaultManager } from './src/VaultManager';
import { OpenAIService, AGENT_SYSTEM_PROMPT } from './src/OpenAIService';
import { ToolHandler } from './src/ToolHandler';
import { MemoryManager } from './src/MemoryManager';
import { KnowledgeGraph } from './src/KnowledgeGraph';
import { TaskPlanner } from './src/TaskPlanner';
import { ContextAwareness } from './src/ContextAwareness';
import { SyncClient, SyncEventType } from './src/SyncClient';

export const AGENT_VIEW_TYPE = 'pkm-agent-view';

// ============================================
// ICONS
// ============================================

const SendIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="22" y1="2" x2="11" y2="13"></line>
        <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
    </svg>
);

const BotIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="11" width="18" height="10" rx="2"/>
        <circle cx="12" cy="5" r="2"/>
        <path d="M12 7v4"/>
        <line x1="8" y1="16" x2="8" y2="16"/>
        <line x1="16" y1="16" x2="16" y2="16"/>
    </svg>
);

const ToolIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
    </svg>
);

const ChevronDownIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="6 9 12 15 18 9"></polyline>
    </svg>
);

const ChevronRightIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="9 18 15 12 9 6"></polyline>
    </svg>
);

const SparklesIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 3l1.5 4.5L18 9l-4.5 1.5L12 15l-1.5-4.5L6 9l4.5-1.5L12 3z"/>
        <path d="M5 19l1 3 1-3 3-1-3-1-1-3-1 3-3 1 3 1z"/>
        <path d="M19 12l1 2 1-2 2-1-2-1-1-2-1 2-2 1 2 1z"/>
    </svg>
);

const ContextIcon = () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="12" cy="12" r="10"/>
        <path d="M12 16v-4"/>
        <path d="M12 8h.01"/>
    </svg>
);

// ============================================
// COMPONENTS
// ============================================

const addCopyButtonsToCodeBlocks = (container: HTMLElement, app: App) => {
    const blocks = container.querySelectorAll('pre');

    blocks.forEach((block) => {
        if (block.querySelector('.code-copy-button')) return;

        const code = block.querySelector('code');
        const button = document.createElement('button');
        button.className = 'code-copy-button';
        button.type = 'button';
        button.textContent = 'Copy';
        button.setAttribute('aria-label', 'Copy code');

        button.onclick = async (event) => {
            event.preventDefault();
            event.stopPropagation();

            const textToCopy = code?.textContent ?? block.textContent ?? '';

            try {
                await navigator.clipboard.writeText(textToCopy);
                new Notice('Code copied to clipboard');
                button.textContent = 'Copied';
                window.setTimeout(() => {
                    button.textContent = 'Copy';
                }, 1500);
            } catch (error) {
                console.error('Failed to copy code', error);
                new Notice('Failed to copy code');
            }
        };

        block.classList.add('code-block');
        block.appendChild(button);
    });
};

const Markdown = ({ content, app }: { content: string; app: App }) => {
    const containerRef = React.useRef<HTMLDivElement>(null);

    React.useEffect(() => {
        if (containerRef.current) {
            containerRef.current.empty();
            MarkdownRenderer.render(app, content, containerRef.current, '/', new Component()).then(() => {
                if (containerRef.current) {
                    addCopyButtonsToCodeBlocks(containerRef.current, app);
                }
            });
        }
    }, [content, app]);

    return <div ref={containerRef} className="markdown-content markdown-rendered" />;
};

const ToolExecution = ({ name, input, output, isExpanded }: { 
    name: string; 
    input: any; 
    output: string;
    isExpanded?: boolean;
}) => {
    const [isOpen, setIsOpen] = React.useState(isExpanded || false);
    const isSuccess = !output.startsWith('Error');
    const isLoading = output === 'Executing...';

    return (
        <div className={`tool-execution ${isSuccess ? 'success' : 'error'} ${isLoading ? 'loading' : ''}`}>
            <div className="tool-header" onClick={() => setIsOpen(!isOpen)}>
                <span className="tool-chevron">{isOpen ? <ChevronDownIcon /> : <ChevronRightIcon />}</span>
                <span className="tool-icon"><ToolIcon /></span>
                <span className="tool-name">{name.replace(/_/g, ' ')}</span>
                <span className={`tool-status ${isSuccess ? 'success' : 'error'} ${isLoading ? 'loading' : ''}`}>
                    {isLoading ? 'Running...' : (isSuccess ? 'Done' : 'Failed')}
                </span>
            </div>
            {isOpen && (
                <div className="tool-details">
                    <div className="tool-section">
                        <div className="tool-label">Input:</div>
                        <pre className="tool-code">{JSON.stringify(input, null, 2)}</pre>
                    </div>
                    <div className="tool-section">
                        <div className="tool-label">Output:</div>
                        <pre className="tool-code">{output}</pre>
                    </div>
                </div>
            )}
        </div>
    );
};

const MessageBubble = ({ 
    role, 
    content, 
    toolCalls, 
    toolOutputs, 
    app,
    isStreaming 
}: { 
    role: string;
    content: string | null;
    toolCalls?: any[];
    toolOutputs?: Map<string, string>;
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
                
                {toolCalls && toolCalls.map((tc) => {
                    const output = toolOutputs?.get(tc.id) || 'Executing...';
                    let args = {};
                    try { args = JSON.parse(tc.function.arguments); } catch {}

                    return (
                        <ToolExecution 
                            key={tc.id} 
                            name={tc.function.name} 
                            input={args} 
                            output={output}
                        />
                    );
                })}
            </div>
        </div>
    );
};

const ContextPanel = ({ contextSummary, onClose }: { contextSummary: string; onClose: () => void }) => {
    return (
        <div className="context-panel">
            <div className="context-panel-header">
                <span><ContextIcon /> Current Context</span>
                <button className="context-close" onClick={onClose}>×</button>
            </div>
            <div className="context-panel-content">
                <pre>{contextSummary}</pre>
            </div>
        </div>
    );
};

const QuickActions = ({ onAction }: { onAction: (action: string) => void }) => {
    const actions = [
        { label: 'Daily Note', action: 'get daily note' },
        { label: 'Recent Files', action: 'show recent files' },
        { label: 'Vault Stats', action: 'show vault statistics' },
        { label: 'Orphan Notes', action: 'find orphan notes' },
    ];

    return (
        <div className="quick-actions">
            {actions.map(({ label, action }) => (
                <button key={action} onClick={() => onAction(action)} className="quick-action-btn">
                    {label}
                </button>
            ))}
        </div>
    );
};

// ============================================
// MAIN VIEW COMPONENT
// ============================================

interface AgentServices {
    openAIService: OpenAIService;
    toolHandler: ToolHandler;
    memoryManager: MemoryManager;
    knowledgeGraph: KnowledgeGraph;
    taskPlanner: TaskPlanner;
    contextAwareness: ContextAwareness;
    app: App;
}

interface ChatMessage {
    id: string;
    role: string;
    content: string | null;
    tool_calls?: any[];
    tool_call_id?: string;
    name?: string;
    timestamp: number;
}

const AgentViewComponent: React.FC<AgentServices> = ({ 
    openAIService, 
    toolHandler, 
    memoryManager,
    knowledgeGraph,
    taskPlanner,
    contextAwareness,
    app 
}) => {
    const [input, setInput] = React.useState('');
    const [loading, setLoading] = React.useState(false);
    const [streamingContent, setStreamingContent] = React.useState('');
    const [messages, setMessages] = React.useState<ChatMessage[]>([]);
    const [toolOutputs, setToolOutputs] = React.useState<Map<string, string>>(new Map());
    const [showContext, setShowContext] = React.useState(false);
    const [contextSummary, setContextSummary] = React.useState('');
    const [showQuickActions, setShowQuickActions] = React.useState(true);

    const messagesEndRef = React.useRef<HTMLDivElement>(null);
    const textareaRef = React.useRef<HTMLTextAreaElement>(null);

    // Initialize system message
    React.useEffect(() => {
        setMessages([{
            id: 'system',
            role: 'system',
            content: AGENT_SYSTEM_PROMPT,
            timestamp: Date.now()
        }]);
    }, []);

    // Auto-scroll
    React.useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages, loading, streamingContent]);

    // Auto-resize textarea
    React.useEffect(() => {
        if (textareaRef.current) {
            textareaRef.current.style.height = 'auto';
            textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 150) + 'px';
        }
    }, [input]);

    // Build context-enriched messages for API
    const buildApiMessages = (history: ChatMessage[]): any[] => {
        return history.map(msg => {
            const apiMsg: any = { role: msg.role, content: msg.content };
            if (msg.tool_calls) apiMsg.tool_calls = msg.tool_calls;
            if (msg.tool_call_id) {
                apiMsg.tool_call_id = msg.tool_call_id;
                apiMsg.name = msg.name;
            }
            return apiMsg;
        });
    };

    const handleSend = async (text?: string) => {
        const messageText = text || input.trim();
        if (!messageText || loading) return;

        setShowQuickActions(false);
        const userMsg: ChatMessage = { 
            id: `user-${Date.now()}`,
            role: 'user', 
            content: messageText,
            timestamp: Date.now()
        };
        
        const newMessages = [...messages, userMsg];
        setMessages(newMessages);
        setInput('');
        setLoading(true);
        setStreamingContent('');

        // Add to memory
        memoryManager.addMessage({ role: 'user', content: messageText, timestamp: Date.now() });

        try {
            // Get context
            const context = await contextAwareness.getContextSummary();
            
            // Enrich user message with context if relevant
            let enrichedContent = messageText;
            if (context && !messageText.toLowerCase().includes('ignore context')) {
                enrichedContent = `[Context: ${context.substring(0, 500)}]\n\nUser request: ${messageText}`;
            }

            const enrichedUserMsg = { ...userMsg, content: enrichedContent };
            const apiMessages = buildApiMessages([...newMessages.slice(0, -1), enrichedUserMsg]);

            await processTurn(apiMessages, newMessages);
        } catch (error: any) {
            new Notice('Error: ' + error.message);
            setMessages(prev => [...prev, {
                id: `error-${Date.now()}`,
                role: 'assistant',
                content: `Error: ${error.message}`,
                timestamp: Date.now()
            }]);
        } finally {
            setLoading(false);
            setStreamingContent('');
        }
    };

    const processTurn = async (apiMessages: any[], displayMessages: ChatMessage[]) => {
        // Use streaming
        const response = await openAIService.chatStream(
            apiMessages,
            (chunk) => {
                setStreamingContent(prev => prev + chunk);
            }
        );

        const assistantMsg: ChatMessage = {
            id: `assistant-${Date.now()}`,
            role: response.role,
            content: response.content,
            tool_calls: response.tool_calls,
            timestamp: Date.now()
        };

        setStreamingContent('');
        const updatedMessages = [...displayMessages, assistantMsg];
        setMessages(updatedMessages);

        // Add to memory
        memoryManager.addMessage({ 
            role: 'assistant', 
            content: response.content, 
            timestamp: Date.now(),
            tool_calls: response.tool_calls
        });

        // Handle tool calls
        if (response.tool_calls && response.tool_calls.length > 0) {
            const newToolOutputs = new Map(toolOutputs);
            const toolMessages: ChatMessage[] = [];
            const apiToolMessages: any[] = [];

            for (const toolCall of response.tool_calls) {
                // Mark as executing
                newToolOutputs.set(toolCall.id, 'Executing...');
                setToolOutputs(new Map(newToolOutputs));

                // Execute tool
                const result = await toolHandler.executeTool(toolCall);
                
                // Update output
                newToolOutputs.set(toolCall.id, result);
                setToolOutputs(new Map(newToolOutputs));

                const toolMsg: ChatMessage = {
                    id: `tool-${toolCall.id}`,
                    role: 'tool',
                    tool_call_id: toolCall.id,
                    name: toolCall.function.name,
                    content: result,
                    timestamp: Date.now()
                };
                toolMessages.push(toolMsg);

                apiToolMessages.push({
                    role: 'tool',
                    tool_call_id: toolCall.id,
                    name: toolCall.function.name,
                    content: result
                });
            }

            const messagesWithTools = [...updatedMessages, ...toolMessages];
            setMessages(messagesWithTools);

            // Continue conversation with tool results
            const newApiMessages = [...apiMessages, {
                role: 'assistant',
                content: response.content,
                tool_calls: response.tool_calls
            }, ...apiToolMessages];

            await processTurn(newApiMessages, messagesWithTools);
        }
    };

    const handleClearChat = () => {
        setMessages([{
            id: 'system',
            role: 'system',
            content: AGENT_SYSTEM_PROMPT,
            timestamp: Date.now()
        }]);
        setToolOutputs(new Map());
        memoryManager.clearConversation();
        setShowQuickActions(true);
    };

    const handleShowContext = async () => {
        const summary = await contextAwareness.getContextSummary();
        setContextSummary(summary);
        setShowContext(true);
    };

    const renderMessages = () => {
        const rendered = [];
        
        for (let i = 0; i < messages.length; i++) {
            const msg = messages[i];
            if (msg.role === 'system' || msg.role === 'tool') continue;

            rendered.push(
                <MessageBubble 
                    key={msg.id} 
                    role={msg.role} 
                    content={msg.content} 
                    toolCalls={msg.tool_calls}
                    toolOutputs={toolOutputs}
                    app={app}
                />
            );
        }

        // Streaming message
        if (loading && streamingContent) {
            rendered.push(
                <MessageBubble 
                    key="streaming" 
                    role="assistant" 
                    content={streamingContent} 
                    app={app}
                    isStreaming={true}
                />
            );
        }

        return rendered;
    };

    return (
        <div className="pkm-agent-view">
            <div className="pkm-agent-header">
                <div className="pkm-agent-title">
                    <span className="pkm-agent-title-icon"><SparklesIcon /></span>
                    <span>PKM Agent</span>
                    {!openAIService.isConfigured() && (
                        <span className="offline-badge">Offline</span>
                    )}
                </div>
                <div className="pkm-agent-actions">
                    <button onClick={handleShowContext} title="Show Context" className="header-btn">
                        <ContextIcon />
                    </button>
                    <button onClick={handleClearChat} title="Clear Chat" className="header-btn">
                        <svg viewBox="0 0 24 24" width="16" height="16" stroke="currentColor" strokeWidth="2" fill="none">
                            <polyline points="3 6 5 6 21 6"></polyline>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                        </svg>
                    </button>
                </div>
            </div>

            {showContext && (
                <ContextPanel 
                    contextSummary={contextSummary} 
                    onClose={() => setShowContext(false)} 
                />
            )}

            <div className="pkm-agent-messages">
                {messages.length <= 1 && showQuickActions && (
                    <div className="welcome-section">
                        <div className="welcome-icon"><SparklesIcon /></div>
                        <h3>Welcome to PKM Agent</h3>
                        <p>Your intelligent knowledge management assistant</p>
                        <QuickActions onAction={handleSend} />
                    </div>
                )}
                
                {renderMessages()}
                
                {loading && !streamingContent && (
                    <div className="pkm-agent-message assistant">
                        <div className="message-avatar"><BotIcon /></div>
                        <div className="message-content">
                            <div className="message-bubble typing-indicator">
                                <div className="typing-dot"></div>
                                <div className="typing-dot"></div>
                                <div className="typing-dot"></div>
                            </div>
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="pkm-agent-input-container">
                <div className="pkm-agent-input-wrapper">
                    <textarea 
                        ref={textareaRef}
                        className="pkm-agent-input"
                        value={input} 
                        onChange={(e) => setInput(e.target.value)} 
                        onKeyDown={(e) => {
                            if (e.key === 'Enter' && !e.shiftKey) {
                                e.preventDefault();
                                handleSend();
                            }
                        }}
                        placeholder="Ask anything about your vault..."
                        disabled={loading}
                        rows={1}
                    />
                    <button 
                        className="pkm-agent-send-btn" 
                        onClick={() => handleSend()} 
                        disabled={loading || !input.trim()}
                    >
                        <SendIcon />
                    </button>
                </div>
                <div className="input-hint">
                    Press Enter to send, Shift+Enter for new line
                </div>
            </div>
        </div>
    );
};

// ============================================
// VIEW CLASS
// ============================================

export class AgentView extends ItemView {
    root: ReactDOM.Root | null = null;
    plugin: PKMAgentPlugin;

    constructor(leaf: WorkspaceLeaf, plugin: PKMAgentPlugin) {
        super(leaf);
        this.plugin = plugin;
    }

    getViewType() {
        return AGENT_VIEW_TYPE;
    }

    getDisplayText() {
        return "PKM Agent";
    }

    getIcon() {
        return "bot";
    }

    async onOpen() {
        const container = this.containerEl.children[1];
        container.empty();
        container.addClass('pkm-agent-container');
        
        const rootEl = container.createEl('div', { cls: 'pkm-agent-root' });
        
        // Initialize services
        const vaultManager = new VaultManager(this.app);
        const memoryManager = new MemoryManager(this.app);
        const knowledgeGraph = new KnowledgeGraph(this.app, vaultManager);
        const taskPlanner = new TaskPlanner(vaultManager, memoryManager, knowledgeGraph);
        const contextAwareness = new ContextAwareness(this.app, vaultManager, knowledgeGraph);
        const toolHandler = new ToolHandler(vaultManager);
        const openAIService = new OpenAIService(
            this.plugin.settings.openaiApiKey,
            this.plugin.settings.model,
            this.plugin.settings.baseUrl
        );

        // Build knowledge graph in background
        knowledgeGraph.buildGraph().catch(console.error);

        this.root = ReactDOM.createRoot(rootEl);
        this.root.render(
            React.createElement(AgentViewComponent, { 
                openAIService, 
                toolHandler,
                memoryManager,
                knowledgeGraph,
                taskPlanner,
                contextAwareness,
                app: this.app 
            })
        );
    }

    async onClose() {
        this.root?.unmount();
    }
}

// ============================================
// SETTINGS
// ============================================

interface AgentSettings {
    openaiApiKey: string;
    model: string;
    baseUrl: string;
    temperature: number;
    enableProactiveAssistance: boolean;
    enableContextAwareness: boolean;
}

const DEFAULT_SETTINGS: AgentSettings = {
    openaiApiKey: '',
    model: 'gpt-4o',
    baseUrl: 'https://api.openai.com/v1',
    temperature: 0.7,
    enableProactiveAssistance: false,
    enableContextAwareness: true
};

// ============================================
// MAIN PLUGIN
// ============================================

export default class PKMAgentPlugin extends Plugin {
    settings: AgentSettings;
    syncClient: SyncClient;

    async onload() {
        await this.loadSettings();

        // Register view
        this.registerView(
            AGENT_VIEW_TYPE,
            (leaf) => new AgentView(leaf, this)
        );

        // Ribbon icon
        this.addRibbonIcon('bot', 'PKM Agent', () => {
            this.activateView();
        });

        // Commands
        this.addCommand({
            id: 'open-pkm-agent',
            name: 'Open PKM Agent Chat',
            callback: () => this.activateView()
        });

        this.addCommand({
            id: 'quick-create-daily',
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
            }
        });

        this.addCommand({
            id: 'quick-create-zettel',
            name: 'Quick: Create Zettel Note',
            callback: () => {
                this.activateView();
                // Could open modal for quick zettel creation
            }
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
            // Connect to WebSocket server
            this.syncClient.connect();
            console.log('Connected to PKM Agent sync server');

            // Register event handlers
            this.syncClient.on(SyncEventType.FILE_CREATED, (event) => {
                console.log('Remote file created:', event.data?.path);
                // Refresh vault to show new file
                this.app.vault.adapter.exists(event.data?.path || '').then(exists => {
                    if (exists) {
                        new Notice(`File synced: ${event.data?.path}`);
                    }
                });
            });

            this.syncClient.on(SyncEventType.FILE_MODIFIED, (event) => {
                console.log('Remote file modified:', event.data?.path);
            });

            this.syncClient.on(SyncEventType.FILE_DELETED, (event) => {
                console.log('Remote file deleted:', event.data?.path);
                new Notice(`File deleted: ${event.data?.path}`);
            });

            this.syncClient.on(SyncEventType.NOTE_INDEXED, (event) => {
                console.log('Note indexed:', event.data);
            });

            // Register vault event handlers to send to server
            this.registerEvent(
                this.app.vault.on('create', async (file) => {
                    if (file instanceof TFile && file.extension === 'md') {
                        await this.syncClient.sendEvent({
                            event_type: SyncEventType.FILE_CREATED,
                            data: { path: file.path, name: file.name }
                        });
                    }
                })
            );

            this.registerEvent(
                this.app.vault.on('modify', async (file) => {
                    if (file instanceof TFile && file.extension === 'md') {
                        await this.syncClient.sendEvent({
                            event_type: SyncEventType.FILE_MODIFIED,
                            data: { path: file.path, name: file.name }
                        });
                    }
                })
            );

            this.registerEvent(
                this.app.vault.on('delete', async (file) => {
                    if (file instanceof TFile && file.extension === 'md') {
                        await this.syncClient.sendEvent({
                            event_type: SyncEventType.FILE_DELETED,
                            data: { path: file.path, name: file.name }
                        });
                    }
                })
            );

            this.registerEvent(
                this.app.vault.on('rename', async (file, oldPath) => {
                    if (file instanceof TFile && file.extension === 'md') {
                        await this.syncClient.sendEvent({
                            event_type: SyncEventType.FILE_RENAMED,
                            data: { path: file.path, oldPath: oldPath, name: file.name }
                        });
                    }
                })
            );

        } catch (error) {
            console.error('Failed to initialize sync:', error);
            new Notice('PKM Agent sync unavailable - continuing without real-time sync');
        }
    }

    async activateView() {
        const { workspace } = this.app;
        let leaf: WorkspaceLeaf | null = null;
        const leaves = workspace.getLeavesOfType(AGENT_VIEW_TYPE);

        if (leaves.length > 0) {
            leaf = leaves[0];
        } else {
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
        // Disconnect sync client
        if (this.syncClient) {
            this.syncClient.disconnect();
        }
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

        // API Key
        new Setting(containerEl)
            .setName('OpenAI API Key')
            .setDesc('Your OpenAI API key for GPT access. Get one at platform.openai.com')
            .addText(text => text
                .setPlaceholder('sk-...')
                .setValue(this.plugin.settings.openaiApiKey)
                .onChange(async (value) => {
                    this.plugin.settings.openaiApiKey = value;
                    await this.plugin.saveSettings();
                }));

        // Model selection
        new Setting(containerEl)
            .setName('Model')
            .setDesc('Choose the GPT model to use')
            .addDropdown(dropdown => dropdown
                .addOption('gpt-4o', 'GPT-4o (Recommended)')
                .addOption('gpt-4o-mini', 'GPT-4o Mini (Faster, cheaper)')
                .addOption('gpt-4-turbo', 'GPT-4 Turbo')
                .addOption('gpt-3.5-turbo', 'GPT-3.5 Turbo (Cheapest)')
                .setValue(this.plugin.settings.model)
                .onChange(async (value) => {
                    this.plugin.settings.model = value;
                    await this.plugin.saveSettings();
                }));

        // Base URL
        new Setting(containerEl)
            .setName('Base URL')
            .setDesc('API endpoint (default: https://api.openai.com/v1). Change this for local LLMs (e.g. http://localhost:1234/v1)')
            .addText(text => text
                .setPlaceholder('https://api.openai.com/v1')
                .setValue(this.plugin.settings.baseUrl)
                .onChange(async (value) => {
                    this.plugin.settings.baseUrl = value;
                    await this.plugin.saveSettings();
                }));

        // Temperature
        new Setting(containerEl)
            .setName('Temperature')
            .setDesc('Controls randomness (0 = focused, 1 = creative)')
            .addSlider(slider => slider
                .setLimits(0, 1, 0.1)
                .setValue(this.plugin.settings.temperature)
                .setDynamicTooltip()
                .onChange(async (value) => {
                    this.plugin.settings.temperature = value;
                    await this.plugin.saveSettings();
                }));

        containerEl.createEl('h3', { text: 'Features' });

        // Context awareness
        new Setting(containerEl)
            .setName('Context Awareness')
            .setDesc('Allow agent to see the currently active file for better responses')
            .addToggle(toggle => toggle
                .setValue(this.plugin.settings.enableContextAwareness)
                .onChange(async (value) => {
                    this.plugin.settings.enableContextAwareness = value;
                    await this.plugin.saveSettings();
                }));

        // Proactive assistance
        new Setting(containerEl)
            .setName('Proactive Assistance')
            .setDesc('Allow agent to suggest actions based on your activity (experimental)')
            .addToggle(toggle => toggle
                .setValue(this.plugin.settings.enableProactiveAssistance)
                .onChange(async (value) => {
                    this.plugin.settings.enableProactiveAssistance = value;
                    await this.plugin.saveSettings();
                }));

        // Info section
        containerEl.createEl('h3', { text: 'About' });
        const infoDiv = containerEl.createEl('div', { cls: 'setting-item-description' });
        infoDiv.innerHTML = `
            <p><strong>PKM Agent</strong> is an autonomous AI assistant for managing your Obsidian vault.</p>
            <p>Capabilities:</p>
            <ul>
                <li>Create, read, update, and organize notes</li>
                <li>Smart search and discovery</li>
                <li>Tag and link management</li>
                <li>Template support</li>
                <li>Knowledge graph analysis</li>
                <li>Daily note workflow</li>
            </ul>
            <p>Without an API key, basic offline commands are available.</p>
        `;
    }
}
