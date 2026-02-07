import {
	App,
	Editor,
	MarkdownView,
	Modal,
	Notice,
	Plugin,
	PluginSettingTab,
	Setting,
	WorkspaceLeaf,
	TFile,
	TFolder,
	addIcon,
	ItemView,
} from 'obsidian';
import { AIChatView, VIEW_TYPE_AI_CHAT } from './src/views/AIChatView';
import { NoteBrowserView, VIEW_TYPE_NOTE_BROWSER } from './src/views/NoteBrowserView';
import { HandwritingView, VIEW_TYPE_HANDWRITING } from './src/views/HandwritingView';
import { KnowledgeGraphView, VIEW_TYPE_KNOWLEDGE_GRAPH } from './src/views/KnowledgeGraphView';
import { AIService } from './src/services/AIService';
import { SearchService } from './src/services/SearchService';
import { ChatService } from './src/services/ChatService';
import { DatabaseManager } from './src/db/DatabaseManager';
import { PluginAPI } from './src/services/PluginAPI';
import { VoiceService } from './src/services/VoiceService';

// Plugin settings interface
export interface AIChatNotesSettings {
	// AI Provider Settings
	aiProvider: 'openai' | 'anthropic' | 'ollama' | 'local';
	openaiApiKey: string;
	anthropicApiKey: string;
	ollamaUrl: string;
	localModelPath: string;
	defaultModel: string;
	
	// UI Settings
	enableLiquidGlass: boolean;
	messageBubbleStyle: 'modern' | 'classic' | 'minimal';
	chatFontSize: number;
	enableTypingIndicators: boolean;
	enableReadReceipts: boolean;
	
	// Feature Settings
	enableSemanticSearch: boolean;
	embeddingModel: string;
	autoSyncInterval: number;
	maxContextNotes: number;
	
	// Privacy Settings
	enableLocalMode: boolean;
	storeChatHistory: boolean;
	encryptData: boolean;
	
	// Appearance
	theme: 'system' | 'light' | 'dark';
	accentColor: string;
	borderRadius: number;
	
	// Advanced
	debugMode: boolean;
	maxTokens: number;
	temperature: number;
}

const DEFAULT_SETTINGS: AIChatNotesSettings = {
	aiProvider: 'ollama',
	openaiApiKey: '',
	anthropicApiKey: '',
	ollamaUrl: 'http://localhost:11434',
	localModelPath: '',
	defaultModel: 'llama3.2',
	
	enableLiquidGlass: true,
	messageBubbleStyle: 'modern',
	chatFontSize: 16,
	enableTypingIndicators: true,
	enableReadReceipts: true,
	
	enableSemanticSearch: true,
	embeddingModel: 'nomic-embed-text',
	autoSyncInterval: 300000, // 5 minutes
	maxContextNotes: 5,
	
	enableLocalMode: true,
	storeChatHistory: true,
	encryptData: false,
	
	theme: 'system',
	accentColor: '#667eea',
	borderRadius: 16,
	
	debugMode: false,
	maxTokens: 2048,
	temperature: 0.7,
};

export default class AIChatNotesPlugin extends Plugin {
	settings: AIChatNotesSettings;
	aiService: AIService;
	searchService: SearchService;
	chatService: ChatService;
	dbManager: DatabaseManager;
	api: PluginAPI;
	voiceService: VoiceService;

	async onload() {
		await this.loadSettings();
		
		// Initialize services
		this.dbManager = new DatabaseManager(this);
		await this.dbManager.initialize();
		
		this.aiService = new AIService(this.settings);
		this.searchService = new SearchService(this);
		this.chatService = new ChatService(this);
		
		// Initialize Phase 3 services
		this.api = new PluginAPI(this);
		this.voiceService = new VoiceService(this);

		// Register custom icons
		this.registerIcons();

		// Register views
		this.registerView(
			VIEW_TYPE_AI_CHAT,
			(leaf) => new AIChatView(leaf, this)
		);
		
		this.registerView(
			VIEW_TYPE_NOTE_BROWSER,
			(leaf) => new NoteBrowserView(leaf, this)
		);
		
		// Phase 3 views
		this.registerView(
			VIEW_TYPE_HANDWRITING,
			(leaf) => new HandwritingView(leaf, this)
		);
		
		this.registerView(
			VIEW_TYPE_KNOWLEDGE_GRAPH,
			(leaf) => new KnowledgeGraphView(leaf, this)
		);

		// Add ribbon icons
		this.addRibbonIcon('message-circle', 'Open AI Chat', () => {
			this.activateChatView();
		});
		
		this.addRibbonIcon('book-open', 'Note Browser', () => {
			this.activateNoteBrowserView();
		});
		
		// Phase 3 ribbon icons
		this.addRibbonIcon('pen-tool', 'Handwriting Canvas', () => {
			this.activateHandwritingView();
		});
		
		this.addRibbonIcon('git-branch', 'Knowledge Graph', () => {
			this.activateKnowledgeGraphView();
		});

		// Add commands
		this.addCommand({
			id: 'open-ai-chat',
			name: 'Open AI Chat',
			callback: () => this.activateChatView(),
		});

		this.addCommand({
			id: 'open-note-browser',
			name: 'Open Note Browser',
			callback: () => this.activateNoteBrowserView(),
		});

		this.addCommand({
			id: 'ask-ai-about-note',
			name: 'Ask AI about current note',
			editorCallback: (editor: Editor, view: MarkdownView) => {
				this.askAIAboutNote(view.file);
			}
		});

		this.addCommand({
			id: 'semantic-search',
			name: 'Semantic Search',
			callback: () => this.openSemanticSearch(),
		});

		this.addCommand({
			id: 'convert-chat-to-note',
			name: 'Convert chat to note',
			callback: () => this.convertChatToNote(),
		});
		
		// Phase 3 commands
		this.addCommand({
			id: 'open-handwriting-canvas',
			name: 'Open Handwriting Canvas',
			callback: () => this.activateHandwritingView(),
		});
		
		this.addCommand({
			id: 'open-knowledge-graph',
			name: 'Open Knowledge Graph',
			callback: () => this.activateKnowledgeGraphView(),
		});
		
		this.addCommand({
			id: 'start-voice-recording',
			name: 'Start Voice Recording',
			callback: () => this.startVoiceRecording(),
		});

		// Add settings tab
		this.addSettingTab(new AIChatNotesSettingTab(this.app, this));

		// Inject styles
		this.injectStyles();

		// Initialize auto-sync
		this.initializeAutoSync();

		console.log('AI Chat & Notes plugin loaded');
	}

	onunload() {
		this.dbManager?.close();
		console.log('AI Chat & Notes plugin unloaded');
	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings() {
		await this.saveData(this.settings);
		this.aiService.updateSettings(this.settings);
	}

	private registerIcons() {
		addIcon('message-circle', `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"/></svg>`);
		addIcon('brain', `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 5a3 3 0 1 0-5.997.125 4 4 0 0 0-2.526 5.77 4 4 0 0 0 .556 6.588A4 4 0 1 0 12 18Z"/><path d="M12 5a3 3 0 1 1 5.997.125 4 4 0 0 1 2.526 5.77 4 4 0 0 1-.556 6.588A4 4 0 1 1 12 18Z"/><path d="M15 13a4.5 4.5 0 0 1-3-4 4.5 4.5 0 0 1-3 4"/><path d="M17.599 6.5a3 3 0 0 0 .399-1.375"/><path d="M6.003 5.125A3 3 0 0 0 6.401 6.5"/><path d="M3.477 10.896a4 4 0 0 1 .585-.396"/><path d="M19.938 10.5a4 4 0 0 1 .585.396"/><path d="M6 18a4 4 0 0 1-1.967-.516"/><path d="M19.967 17.484A4 4 0 0 1 18 18"/></svg>`);
	}

	private injectStyles() {
		const styleEl = document.createElement('style');
		styleEl.id = 'ai-chat-notes-styles';
		styleEl.textContent = LIQUID_GLASS_STYLES;
		document.head.appendChild(styleEl);
	}

	private initializeAutoSync() {
		if (this.settings.autoSyncInterval > 0) {
			this.registerInterval(
				window.setInterval(() => {
					this.searchService.syncEmbeddings();
				}, this.settings.autoSyncInterval)
			);
		}
	}

	async activateChatView() {
		const { workspace } = this.app;
		
		let leaf: WorkspaceLeaf | null = workspace.getLeavesOfType(VIEW_TYPE_AI_CHAT)[0];
		if (!leaf) {
			leaf = workspace.getRightLeaf(false);
			if (!leaf) {
				new Notice('Failed to create AI Chat view');
				return;
			}
			await leaf.setViewState({ type: VIEW_TYPE_AI_CHAT, active: true });
		}
		workspace.revealLeaf(leaf);
	}

	async activateNoteBrowserView() {
		const { workspace } = this.app;
		
		let leaf: WorkspaceLeaf | null = workspace.getLeavesOfType(VIEW_TYPE_NOTE_BROWSER)[0];
		if (!leaf) {
			leaf = workspace.getLeftLeaf(false);
			if (!leaf) {
				new Notice('Failed to create Note Browser view');
				return;
			}
			await leaf.setViewState({ type: VIEW_TYPE_NOTE_BROWSER, active: true });
		}
		workspace.revealLeaf(leaf);
	}

	async askAIAboutNote(file: TFile | null) {
		if (!file) {
			new Notice('No note is currently open');
			return;
		}
		
		const content = await this.app.vault.read(file);
		await this.activateChatView();
		
		// Get the chat view and send context
		const leaf = this.app.workspace.getLeavesOfType(VIEW_TYPE_AI_CHAT)[0];
		if (leaf && leaf.view instanceof AIChatView) {
			leaf.view.setContextNote(file.name, content);
		}
	}

	async openSemanticSearch() {
		new SemanticSearchModal(this.app, this).open();
	}

	async convertChatToNote() {
		// Implementation for converting chat to note
		new ChatToNoteModal(this.app, this).open();
	}

	// Phase 3 methods
	async activateHandwritingView() {
		const { workspace } = this.app;
		
		let leaf: WorkspaceLeaf | null = workspace.getLeavesOfType(VIEW_TYPE_HANDWRITING)[0];
		if (!leaf) {
			leaf = workspace.getRightLeaf(false);
			if (!leaf) {
				new Notice('Failed to create Handwriting view');
				return;
			}
			await leaf.setViewState({ type: VIEW_TYPE_HANDWRITING, active: true });
		}
		workspace.revealLeaf(leaf);
	}

	async activateKnowledgeGraphView() {
		const { workspace } = this.app;
		
		let leaf: WorkspaceLeaf | null = workspace.getLeavesOfType(VIEW_TYPE_KNOWLEDGE_GRAPH)[0];
		if (!leaf) {
			leaf = workspace.getRightLeaf(false);
			if (!leaf) {
				new Notice('Failed to create Knowledge Graph view');
				return;
			}
			await leaf.setViewState({ type: VIEW_TYPE_KNOWLEDGE_GRAPH, active: true });
		}
		workspace.revealLeaf(leaf);
	}

	async startVoiceRecording() {
		if (this.voiceService.isRecording) {
			const recording = await this.voiceService.stopRecording();
			if (recording) {
				// Transcribe and add to chat
				const transcription = await this.voiceService.transcribeRecording(recording);
				
				// Open chat view and add transcription
				await this.activateChatView();
				const leaf = this.app.workspace.getLeavesOfType(VIEW_TYPE_AI_CHAT)[0];
				if (leaf && leaf.view instanceof AIChatView) {
					// Send the transcription as a message
					const textArea = leaf.view.containerEl.querySelector('.ai-chat-input') as HTMLTextAreaElement;
					if (textArea) {
						textArea.value = transcription;
					}
				}
			}
		} else {
			await this.voiceService.startRecording();
		}
	}
}

// Settings Tab
class AIChatNotesSettingTab extends PluginSettingTab {
	plugin: AIChatNotesPlugin;

	constructor(app: App, plugin: AIChatNotesPlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const { containerEl } = this;
		containerEl.empty();

		containerEl.createEl('h2', { text: 'AI Chat & Notes Settings' });

		// AI Provider Section
		containerEl.createEl('h3', { text: 'AI Provider' });
		
		new Setting(containerEl)
			.setName('AI Provider')
			.setDesc('Select your preferred AI provider')
			.addDropdown(dropdown => dropdown
				.addOption('ollama', 'Ollama (Local)')
				.addOption('openai', 'OpenAI')
				.addOption('anthropic', 'Anthropic (Claude)')
				.addOption('local', 'Local Model')
				.setValue(this.plugin.settings.aiProvider)
				.onChange(async (value) => {
					this.plugin.settings.aiProvider = value as any;
					await this.plugin.saveSettings();
					this.display();
				}));

		if (this.plugin.settings.aiProvider === 'openai') {
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
		}

		if (this.plugin.settings.aiProvider === 'anthropic') {
			new Setting(containerEl)
				.setName('Anthropic API Key')
				.setDesc('Your Anthropic API key')
				.addText(text => text
					.setPlaceholder('sk-ant-...')
					.setValue(this.plugin.settings.anthropicApiKey)
					.onChange(async (value) => {
						this.plugin.settings.anthropicApiKey = value;
						await this.plugin.saveSettings();
					}));
		}

		if (this.plugin.settings.aiProvider === 'ollama') {
			new Setting(containerEl)
				.setName('Ollama URL')
				.setDesc('URL of your Ollama instance')
				.addText(text => text
					.setPlaceholder('http://localhost:11434')
					.setValue(this.plugin.settings.ollamaUrl)
					.onChange(async (value) => {
						this.plugin.settings.ollamaUrl = value;
						await this.plugin.saveSettings();
					}));
		}

		new Setting(containerEl)
			.setName('Default Model')
			.setDesc('Model to use for AI responses')
			.addText(text => text
				.setPlaceholder('llama3.2')
				.setValue(this.plugin.settings.defaultModel)
				.onChange(async (value) => {
					this.plugin.settings.defaultModel = value;
					await this.plugin.saveSettings();
				}));

		// UI Settings Section
		containerEl.createEl('h3', { text: 'UI Settings' });
		
		new Setting(containerEl)
			.setName('Enable Liquid Glass Design')
			.setDesc('Use modern glass-morphism design effects')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.enableLiquidGlass)
				.onChange(async (value) => {
					this.plugin.settings.enableLiquidGlass = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Message Bubble Style')
			.setDesc('Style of chat message bubbles')
			.addDropdown(dropdown => dropdown
				.addOption('modern', 'Modern (Liquid Glass)')
				.addOption('classic', 'Classic')
				.addOption('minimal', 'Minimal')
				.setValue(this.plugin.settings.messageBubbleStyle)
				.onChange(async (value) => {
					this.plugin.settings.messageBubbleStyle = value as any;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Chat Font Size')
			.setDesc('Font size for chat messages (px)')
			.addSlider(slider => slider
				.setLimits(12, 24, 1)
				.setValue(this.plugin.settings.chatFontSize)
				.setDynamicTooltip()
				.onChange(async (value) => {
					this.plugin.settings.chatFontSize = value;
					await this.plugin.saveSettings();
				}));

		// Feature Settings Section
		containerEl.createEl('h3', { text: 'Features' });
		
		new Setting(containerEl)
			.setName('Enable Semantic Search')
			.setDesc('Use AI embeddings for note search')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.enableSemanticSearch)
				.onChange(async (value) => {
					this.plugin.settings.enableSemanticSearch = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Max Context Notes')
			.setDesc('Maximum number of notes to include as context')
			.addSlider(slider => slider
				.setLimits(1, 10, 1)
				.setValue(this.plugin.settings.maxContextNotes)
				.setDynamicTooltip()
				.onChange(async (value) => {
					this.plugin.settings.maxContextNotes = value;
					await this.plugin.saveSettings();
				}));

		// Privacy Settings
		containerEl.createEl('h3', { text: 'Privacy' });
		
		new Setting(containerEl)
			.setName('Enable Local Mode')
			.setDesc('Process everything locally without cloud services')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.enableLocalMode)
				.onChange(async (value) => {
					this.plugin.settings.enableLocalMode = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Store Chat History')
			.setDesc('Save chat conversations to local database')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.storeChatHistory)
				.onChange(async (value) => {
					this.plugin.settings.storeChatHistory = value;
					await this.plugin.saveSettings();
				}));

		// Advanced Settings
		containerEl.createEl('h3', { text: 'Advanced' });
		
		new Setting(containerEl)
			.setName('Temperature')
			.setDesc('AI creativity level (0.0 - 1.0)')
			.addSlider(slider => slider
				.setLimits(0, 1, 0.1)
				.setValue(this.plugin.settings.temperature)
				.setDynamicTooltip()
				.onChange(async (value) => {
					this.plugin.settings.temperature = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Max Tokens')
			.setDesc('Maximum tokens per AI response')
			.addText(text => text
				.setPlaceholder('2048')
				.setValue(String(this.plugin.settings.maxTokens))
				.onChange(async (value) => {
					this.plugin.settings.maxTokens = parseInt(value) || 2048;
					await this.plugin.saveSettings();
				}));
	}
}

// Modals
class SemanticSearchModal extends Modal {
	plugin: AIChatNotesPlugin;
	results: TFile[] = [];

	constructor(app: App, plugin: AIChatNotesPlugin) {
		super(app);
		this.plugin = plugin;
	}

	onOpen() {
		const { contentEl } = this;
		contentEl.empty();
		contentEl.addClass('semantic-search-modal');
		
		contentEl.createEl('h2', { text: 'Semantic Search' });
		
		const inputContainer = contentEl.createDiv({ cls: 'search-input-container' });
		const input = inputContainer.createEl('input', {
			type: 'text',
			placeholder: 'Search your notes with natural language...',
			cls: 'semantic-search-input'
		});
		
		const resultsContainer = contentEl.createDiv({ cls: 'search-results' });
		
		input.addEventListener('input', async (e) => {
			const query = (e.target as HTMLInputElement).value;
			if (query.length > 2) {
				this.results = await this.plugin.searchService.semanticSearch(query);
				this.renderResults(resultsContainer);
			}
		});
		
		input.focus();
	}

	renderResults(container: HTMLElement) {
		container.empty();
		
		if (this.results.length === 0) {
			container.createEl('p', { text: 'No results found', cls: 'no-results' });
			return;
		}
		
		this.results.forEach(file => {
			const resultItem = container.createDiv({ cls: 'search-result-item' });
			resultItem.createEl('span', { text: file.basename, cls: 'result-title' });
			resultItem.createEl('span', { text: file.path, cls: 'result-path' });
			resultItem.addEventListener('click', () => {
				this.app.workspace.openLinkText(file.path, '', true);
				this.close();
			});
		});
	}

	onClose() {
		const { contentEl } = this;
		contentEl.empty();
	}
}

class ChatToNoteModal extends Modal {
	plugin: AIChatNotesPlugin;

	constructor(app: App, plugin: AIChatNotesPlugin) {
		super(app);
		this.plugin = plugin;
	}

	onOpen() {
		const { contentEl } = this;
		contentEl.empty();
		
		contentEl.createEl('h2', { text: 'Convert Chat to Note' });
		contentEl.createEl('p', { text: 'Select a chat conversation to convert to a note:' });
		
		// TODO: Implement chat selection and conversion
	}

	onClose() {
		const { contentEl } = this;
		contentEl.empty();
	}
}

// Liquid Glass Design System Styles
const LIQUID_GLASS_STYLES = `
/* Phase 3 - Handwriting Canvas Styles */
.handwriting-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.handwriting-header {
  padding: 16px;
  border-bottom: 1px solid var(--ai-glass-border);
  background: var(--ai-glass-bg);
  backdrop-filter: var(--ai-glass-blur);
}

.handwriting-header h3 {
  margin: 0;
  font-size: 18px;
}

.handwriting-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid var(--ai-glass-border);
  align-items: center;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-label {
  font-size: 12px;
  font-weight: 600;
  color: var(--text-muted);
  text-transform: uppercase;
}

.color-btn {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  border: 2px solid transparent;
  cursor: pointer;
  transition: transform 0.2s, border-color 0.2s;
}

.color-btn:hover {
  transform: scale(1.1);
}

.color-btn.active {
  border-color: var(--text-normal);
  box-shadow: 0 0 0 2px var(--background-primary);
}

.brush-size-slider {
  width: 100px;
}

.tool-btn {
  padding: 6px 12px;
  border-radius: 8px;
  border: 1px solid var(--ai-glass-border);
  background: var(--ai-glass-bg);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.tool-btn:hover {
  background: var(--ai-primary);
  color: white;
}

.tool-btn.active {
  background: var(--ai-primary);
  color: white;
}

.tool-btn.danger:hover {
  background: #dc2626;
}

.canvas-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  padding: 20px;
  overflow: auto;
}

.theme-dark .canvas-container {
  background: #1a1a1a;
}

.handwriting-canvas {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
  cursor: crosshair;
  touch-action: none;
}

.handwriting-footer {
  display: flex;
  gap: 12px;
  padding: 16px;
  border-top: 1px solid var(--ai-glass-border);
  background: var(--ai-glass-bg);
  backdrop-filter: var(--ai-glass-blur);
}

.action-btn {
  padding: 10px 20px;
  border-radius: 8px;
  border: 1px solid var(--ai-glass-border);
  background: var(--ai-glass-bg);
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.action-btn:hover {
  background: var(--ai-primary);
  color: white;
}

.action-btn.primary {
  background: var(--ai-primary-gradient);
  color: white;
  border: none;
}

/* Phase 3 - Knowledge Graph Styles */
.knowledge-graph-view {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.graph-header {
  padding: 16px;
  border-bottom: 1px solid var(--ai-glass-border);
  background: var(--ai-glass-bg);
  backdrop-filter: var(--ai-glass-blur);
}

.graph-header h3 {
  margin: 0;
  font-size: 18px;
}

.graph-toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  padding: 12px 16px;
  background: rgba(0, 0, 0, 0.03);
  border-bottom: 1px solid var(--ai-glass-border);
  align-items: center;
}

.graph-btn {
  padding: 8px 16px;
  border-radius: 8px;
  border: 1px solid var(--ai-glass-border);
  background: var(--ai-glass-bg);
  cursor: pointer;
  font-size: 13px;
  transition: all 0.2s;
}

.graph-btn:hover {
  background: var(--ai-primary);
  color: white;
}

.graph-btn.primary {
  background: var(--ai-primary-gradient);
  color: white;
  border: none;
}

.filter-container {
  display: flex;
  gap: 16px;
  margin-left: auto;
}

.toggle-wrapper {
  display: flex;
  align-items: center;
  gap: 6px;
}

.toggle-label {
  font-size: 12px;
  color: var(--text-muted);
}

.toggle-checkbox {
  cursor: pointer;
}

.graph-stats {
  display: flex;
  gap: 16px;
  padding: 8px 16px;
  background: var(--background-secondary);
  font-size: 12px;
  color: var(--text-muted);
}

.graph-stats span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.graph-canvas-container {
  flex: 1;
  position: relative;
  overflow: hidden;
  background: var(--background-primary);
}

.graph-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  cursor: grab;
}

.graph-canvas:active {
  cursor: grabbing;
}

/* Voice Recording Indicator */
.voice-recording-indicator {
  position: fixed;
  bottom: 80px;
  right: 20px;
  background: #dc2626;
  color: white;
  padding: 12px 20px;
  border-radius: 50px;
  display: flex;
  align-items: center;
  gap: 10px;
  box-shadow: 0 4px 20px rgba(220, 38, 38, 0.4);
  animation: pulse 1.5s ease-in-out infinite;
  z-index: 1000;
}

.voice-recording-indicator::before {
  content: '🎙️';
  font-size: 18px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.05); }
}

/* AI Chat & Notes - Liquid Glass Design System */

/* CSS Variables */
.ai-chat-notes-root {
  --ai-primary: #667eea;
  --ai-primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --ai-glass-bg: rgba(255, 255, 255, 0.7);
  --ai-glass-border: rgba(255, 255, 255, 0.3);
  --ai-glass-blur: blur(20px) saturate(180%);
  --ai-shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.1);
  --ai-shadow-md: 0 8px 32px rgba(0, 0, 0, 0.1);
  --ai-shadow-lg: 0 12px 24px rgba(0, 0, 0, 0.15);
  --ai-border-radius: 16px;
  --ai-transition: all 0.3s cubic-bezier(0.4, 0.0, 0.2, 1);
  
  /* Message bubble colors */
  --ai-message-sent: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  --ai-message-received: #f7fafc;
  --ai-message-text-sent: #ffffff;
  --ai-message-text-received: #1a1a1a;
}

.theme-dark .ai-chat-notes-root {
  --ai-glass-bg: rgba(30, 30, 30, 0.8);
  --ai-glass-border: rgba(255, 255, 255, 0.1);
  --ai-message-received: #2d2d2d;
  --ai-message-text-received: #e0e0e0;
}

/* Common Glass Effect */
.ai-glass {
  background: var(--ai-glass-bg);
  backdrop-filter: var(--ai-glass-blur);
  -webkit-backdrop-filter: var(--ai-glass-blur);
  border: 1px solid var(--ai-glass-border);
  border-radius: var(--ai-border-radius);
}

/* Message Bubbles */
.ai-message-bubble {
  max-width: 80%;
  padding: 12px 16px;
  border-radius: var(--ai-border-radius);
  box-shadow: var(--ai-shadow-sm);
  transition: var(--ai-transition);
  animation: messageAppear 0.3s ease-out;
  word-wrap: break-word;
}

@keyframes messageAppear {
  from {
    opacity: 0;
    transform: translateY(10px) scale(0.95);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

.ai-message-bubble:hover {
  box-shadow: var(--ai-shadow-md);
  transform: scale(1.02);
}

.ai-message-bubble.sent {
  background: var(--ai-message-sent);
  color: var(--ai-message-text-sent);
  margin-left: auto;
  border-bottom-right-radius: 4px;
}

.ai-message-bubble.received {
  background: var(--ai-message-received);
  color: var(--ai-message-text-received);
  border-bottom-left-radius: 4px;
}

.ai-message-bubble.ai {
  background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
  border: 1px solid rgba(102, 126, 234, 0.3);
  color: var(--ai-message-text-received);
}

/* Chat Input Area */
.ai-chat-input-container {
  position: sticky;
  bottom: 0;
  padding: 16px;
  background: var(--ai-glass-bg);
  backdrop-filter: var(--ai-glass-blur);
  -webkit-backdrop-filter: var(--ai-glass-blur);
  border-top: 1px solid var(--ai-glass-border);
  display: flex;
  gap: 12px;
  align-items: flex-end;
}

.ai-chat-input {
  flex: 1;
  min-height: 44px;
  max-height: 200px;
  padding: 12px 16px;
  border: 1px solid var(--ai-glass-border);
  border-radius: calc(var(--ai-border-radius) / 2);
  background: rgba(255, 255, 255, 0.5);
  resize: none;
  outline: none;
  font-size: 16px;
  transition: var(--ai-transition);
}

.ai-chat-input:focus {
  border-color: var(--ai-primary);
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
}

.ai-send-button {
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: var(--ai-primary-gradient);
  color: white;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: var(--ai-transition);
  box-shadow: var(--ai-shadow-sm);
}

.ai-send-button:hover {
  transform: scale(1.1);
  box-shadow: var(--ai-shadow-md);
}

/* Typing Indicator */
.ai-typing-indicator {
  display: flex;
  gap: 4px;
  padding: 16px;
  align-items: center;
}

.ai-typing-indicator span {
  width: 8px;
  height: 8px;
  background: var(--ai-primary);
  border-radius: 50%;
  animation: typingBounce 1.4s ease-in-out infinite both;
}

.ai-typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.ai-typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes typingBounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* Semantic Search Modal */
.semantic-search-modal {
  min-width: 600px;
}

.semantic-search-input {
  width: 100%;
  padding: 16px 20px;
  font-size: 18px;
  border: 2px solid var(--ai-glass-border);
  border-radius: var(--ai-border-radius);
  background: var(--ai-glass-bg);
  backdrop-filter: var(--ai-glass-blur);
  outline: none;
  transition: var(--ai-transition);
}

.semantic-search-input:focus {
  border-color: var(--ai-primary);
  box-shadow: 0 0 0 4px rgba(102, 126, 234, 0.15);
}

.search-results {
  margin-top: 20px;
  max-height: 400px;
  overflow-y: auto;
}

.search-result-item {
  padding: 16px;
  border-radius: 12px;
  cursor: pointer;
  transition: var(--ai-transition);
  border: 1px solid transparent;
}

.search-result-item:hover {
  background: rgba(102, 126, 234, 0.05);
  border-color: rgba(102, 126, 234, 0.2);
}

.result-title {
  display: block;
  font-weight: 600;
  color: var(--ai-primary);
}

.result-path {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  margin-top: 4px;
}

/* Note Browser */
.note-browser-container {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.note-browser-header {
  padding: 16px;
  border-bottom: 1px solid var(--ai-glass-border);
  background: var(--ai-glass-bg);
  backdrop-filter: var(--ai-glass-blur);
}

.note-browser-tree {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.note-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: var(--ai-transition);
  gap: 8px;
}

.note-item:hover {
  background: rgba(102, 126, 234, 0.1);
}

.note-item.active {
  background: var(--ai-primary-gradient);
  color: white;
}

/* AI Suggestions Panel */
.ai-suggestions-panel {
  position: absolute;
  bottom: 80px;
  left: 16px;
  right: 16px;
  background: var(--ai-glass-bg);
  backdrop-filter: var(--ai-glass-blur);
  border: 1px solid var(--ai-glass-border);
  border-radius: var(--ai-border-radius);
  padding: 12px;
  box-shadow: var(--ai-shadow-lg);
  z-index: 100;
}

.ai-suggestion-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  transition: var(--ai-transition);
  display: flex;
  align-items: center;
  gap: 8px;
}

.ai-suggestion-item:hover {
  background: rgba(102, 126, 234, 0.1);
}

/* Context Panel */
.ai-context-panel {
  background: rgba(102, 126, 234, 0.05);
  border: 1px solid rgba(102, 126, 234, 0.2);
  border-radius: var(--ai-border-radius);
  padding: 12px 16px;
  margin: 8px 0;
  font-size: 13px;
}

.ai-context-panel .context-title {
  font-weight: 600;
  color: var(--ai-primary);
  margin-bottom: 4px;
}

/* Responsive Layout */
@media (max-width: 768px) {
  .ai-message-bubble {
    max-width: 90%;
  }
  
  .semantic-search-modal {
    min-width: 100%;
    width: 100%;
  }
}

/* Scrollbar Styling */
.ai-chat-notes-root ::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.ai-chat-notes-root ::-webkit-scrollbar-track {
  background: transparent;
}

.ai-chat-notes-root ::-webkit-scrollbar-thumb {
  background: rgba(102, 126, 234, 0.3);
  border-radius: 3px;
}

.ai-chat-notes-root ::-webkit-scrollbar-thumb:hover {
  background: rgba(102, 126, 234, 0.5);
}
`;
