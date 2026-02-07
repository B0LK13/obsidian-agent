import { Plugin, PluginSettingTab, App, Setting, Notice, TFile, TFolder, ItemView, WorkspaceLeaf } from 'obsidian';
import { LocalAIClient } from './ai-client';
import { RAGService } from './rag-service';
import { CanvasIntegration } from './canvas-integration';
import { DataviewIntegration } from './dataview-integration';

interface ObsidianAIAgentSettings {
    llmEndpoint: string;
    embedEndpoint: string;
    vectorEndpoint: string;
    autoIndex: boolean;
    indexOnStartup: boolean;
    maxContextLength: number;
    defaultModel: string;
}

const DEFAULT_SETTINGS: ObsidianAIAgentSettings = {
    llmEndpoint: 'http://127.0.0.1:8000',
    embedEndpoint: 'http://127.0.0.1:8001',
    vectorEndpoint: 'http://127.0.0.1:8002',
    autoIndex: true,
    indexOnStartup: false,
    maxContextLength: 4096,
    defaultModel: 'local-llm'
};

export default class ObsidianAIAgent extends Plugin {
    settings: ObsidianAIAgentSettings;
    aiClient: LocalAIClient;
    ragService: RAGService;
    canvasIntegration: CanvasIntegration;
    dataviewIntegration: DataviewIntegration;

    async onload() {
        await this.loadSettings();

        // Initialize services
        this.aiClient = new LocalAIClient(this.settings);
        this.ragService = new RAGService(this.app, this.settings);
        this.canvasIntegration = new CanvasIntegration(this.app);
        this.dataviewIntegration = new DataviewIntegration(this.app);

        // Add ribbon icon
        this.addRibbonIcon('bot', 'AI Agent', () => {
            this.openAIChatView();
        });

        // Add commands
        this.addCommand({
            id: 'open-ai-chat',
            name: 'Open AI Chat',
            callback: () => this.openAIChatView()
        });

        this.addCommand({
            id: 'index-vault',
            name: 'Index Vault for RAG',
            callback: () => this.indexVault()
        });

        this.addCommand({
            id: 'ask-ai-about-note',
            name: 'Ask AI about current note',
            editorCallback: (editor, view) => {
                const content = editor.getValue();
                this.askAIAboutContent(content);
            }
        });

        this.addCommand({
            id: 'generate-canvas-from-notes',
            name: 'Generate Canvas from selected notes',
            callback: () => this.generateCanvas()
        });

        this.addCommand({
            id: 'search-with-ai',
            name: 'Semantic search with AI',
            callback: () => this.semanticSearch()
        });

        // Add settings tab
        this.addSettingTab(new ObsidianAIAgentSettingTab(this.app, this));

        // Check connection on startup
        this.checkConnection();

        // Index on startup if enabled
        if (this.settings.indexOnStartup) {
            this.indexVault();
        }

        console.log('Obsidian AI Agent loaded');
    }

    onunload() {
        console.log('Obsidian AI Agent unloaded');
    }

    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }

    async saveSettings() {
        await this.saveData(this.settings);
    }

    async checkConnection() {
        const status = await this.aiClient.checkHealth();
        if (status.llm && status.embeddings && status.vector) {
            new Notice('AI Agent: Connected to local AI stack');
        } else {
            new Notice('AI Agent: Cannot connect to local AI stack. Run: ./start-local-ai-stack.ps1');
        }
    }

    async openAIChatView() {
        const leaf = this.app.workspace.getRightLeaf(false);
        if (leaf) {
            await leaf.setViewState({
                type: 'ai-chat-view',
                active: true
            });
            this.app.workspace.revealLeaf(leaf);
        }
    }

    async indexVault() {
        new Notice('AI Agent: Starting vault indexing...');
        try {
            await this.ragService.indexVault();
            new Notice('AI Agent: Vault indexing complete');
        } catch (error) {
            new Notice(`AI Agent: Indexing failed - ${error.message}`);
        }
    }

    async askAIAboutContent(content: string) {
        // Get relevant context from RAG
        const context = await this.ragService.getRelevantContext(content);
        
        // Build prompt
        const prompt = `Based on the following context from my knowledge base, please analyze and provide insights:

Context:
${context}

Current Note:
${content}

Please provide a thoughtful analysis.`;

        // Send to AI
        const response = await this.aiClient.chat(prompt);
        
        // Display response
        this.displayResponse(response);
    }

    async generateCanvas() {
        const activeFile = this.app.workspace.getActiveFile();
        if (!activeFile) {
            new Notice('Please open a note first');
            return;
        }

        const content = await this.app.vault.read(activeFile);
        const title = activeFile.basename;

        // Get related notes
        const related = await this.ragService.findRelatedNotes(content, 5);

        // Generate canvas structure
        await this.canvasIntegration.createCanvasFromNotes(title, [activeFile, ...related]);
        new Notice('AI Agent: Canvas created');
    }

    async semanticSearch() {
        // This would open a modal for semantic search
        // Simplified implementation
        new Notice('AI Agent: Semantic search - use the chat view');
        this.openAIChatView();
    }

    displayResponse(response: string) {
        // Create a new note with the response or show in modal
        const modal = document.createElement('div');
        modal.addClass('ai-response-modal');
        modal.innerHTML = `
            <div class="ai-response-content">
                <h3>AI Response</h3>
                <div class="ai-response-text">${response}</div>
                <button class="ai-response-close">Close</button>
            </div>
        `;
        document.body.appendChild(modal);

        modal.querySelector('.ai-response-close')?.addEventListener('click', () => {
            modal.remove();
        });
    }
}

// Settings Tab
class ObsidianAIAgentSettingTab extends PluginSettingTab {
    plugin: ObsidianAIAgent;

    constructor(app: App, plugin: ObsidianAIAgent) {
        super(app, plugin);
        this.plugin = plugin;
    }

    display(): void {
        const { containerEl } = this;
        containerEl.empty();

        containerEl.createEl('h2', { text: 'Obsidian AI Agent Settings' });

        // Connection settings
        containerEl.createEl('h3', { text: 'Local AI Stack Connection' });

        new Setting(containerEl)
            .setName('LLM Endpoint')
            .setDesc('URL for the local LLM server (must be 127.0.0.1 or localhost)')
            .addText(text => text
                .setPlaceholder('http://127.0.0.1:8000')
                .setValue(this.plugin.settings.llmEndpoint)
                .onChange(async (value) => {
                    this.plugin.settings.llmEndpoint = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Embeddings Endpoint')
            .setDesc('URL for the local embeddings server')
            .addText(text => text
                .setPlaceholder('http://127.0.0.1:8001')
                .setValue(this.plugin.settings.embedEndpoint)
                .onChange(async (value) => {
                    this.plugin.settings.embedEndpoint = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Vector DB Endpoint')
            .setDesc('URL for the local vector database')
            .addText(text => text
                .setPlaceholder('http://127.0.0.1:8002')
                .setValue(this.plugin.settings.vectorEndpoint)
                .onChange(async (value) => {
                    this.plugin.settings.vectorEndpoint = value;
                    await this.plugin.saveSettings();
                }));

        // Indexing settings
        containerEl.createEl('h3', { text: 'Indexing Settings' });

        new Setting(containerEl)
            .setName('Auto-index on save')
            .setDesc('Automatically index notes when they are saved')
            .addToggle(toggle => toggle
                .setValue(this.plugin.settings.autoIndex)
                .onChange(async (value) => {
                    this.plugin.settings.autoIndex = value;
                    await this.plugin.saveSettings();
                }));

        new Setting(containerEl)
            .setName('Index on startup')
            .setDesc('Index the vault when Obsidian starts')
            .addToggle(toggle => toggle
                .setValue(this.plugin.settings.indexOnStartup)
                .onChange(async (value) => {
                    this.plugin.settings.indexOnStartup = value;
                    await this.plugin.saveSettings();
                }));

        // Security notice
        const securityDiv = containerEl.createEl('div', { cls: 'ai-agent-security-notice' });
        securityDiv.createEl('h3', { text: 'Security Notice' });
        securityDiv.createEl('p', { 
            text: 'This plugin is configured for LOCAL-ONLY operation. All AI services must be running on 127.0.0.1 (localhost). External connections are blocked by design.' 
        });
    }
}
