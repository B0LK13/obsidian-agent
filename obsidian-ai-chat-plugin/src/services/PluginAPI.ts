import { Notice, TFile } from 'obsidian';
import AIChatNotesPlugin from '../../main';
import { AIService } from './AIService';
import { SearchService } from './SearchService';
import { ChatService } from './ChatService';
import { VoiceService } from './VoiceService';
import { HandwritingService } from './HandwritingService';
import { KnowledgeGraphService } from './KnowledgeGraphService';

// Extension interface that plugins must implement
export interface AIChatExtension {
	id: string;
	name: string;
	version: string;
	author?: string;
	description?: string;
	
	// Lifecycle hooks
	onLoad(api: PluginAPI): void;
	onUnload(): void;
	
	// Optional hooks
	onMessage?(message: string, context: any): Promise<string | null>;
	onNoteOpen?(file: TFile): void;
	onSettingsChange?(settings: any): void;
}

// Command registration interface
export interface APICommand {
	id: string;
	name: string;
	callback: () => void | Promise<void>;
	hotkey?: string;
}

// Event types
export type APIEventType = 
	| 'message:received'
	| 'message:sent'
	| 'note:opened'
	| 'note:created'
	| 'note:modified'
	| 'chat:sessionChanged'
	| 'settings:changed'
	| 'graph:updated';

export type EventCallback = (data: any) => void;

export class PluginAPI {
	plugin: AIChatNotesPlugin;
	
	// Registered extensions
	private extensions: Map<string, AIChatExtension> = new Map();
	
	// Registered commands
	private commands: Map<string, APICommand> = new Map();
	
	// Event listeners
	private eventListeners: Map<APIEventType, Set<EventCallback>> = new Map();
	
	// Exposed services
	ai: AIService;
	search: SearchService;
	chat: ChatService;
	voice: VoiceService;
	handwriting: HandwritingService;
	graph: KnowledgeGraphService;

	constructor(plugin: AIChatNotesPlugin) {
		this.plugin = plugin;
		
		// Initialize services
		this.ai = plugin.aiService;
		this.search = plugin.searchService;
		this.chat = plugin.chatService;
		this.voice = new VoiceService(plugin);
		this.handwriting = new HandwritingService(plugin);
		this.graph = new KnowledgeGraphService(plugin);
	}

	// ==================== Extension Management ====================

	registerExtension(extension: AIChatExtension): boolean {
		if (this.extensions.has(extension.id)) {
			console.warn(`Extension ${extension.id} is already registered`);
			return false;
		}

		try {
			extension.onLoad(this);
			this.extensions.set(extension.id, extension);
			new Notice(`Extension "${extension.name}" loaded`);
			return true;
		} catch (error) {
			console.error(`Failed to load extension ${extension.id}:`, error);
			return false;
		}
	}

	unregisterExtension(extensionId: string): boolean {
		const extension = this.extensions.get(extensionId);
		if (!extension) return false;

		try {
			extension.onUnload();
			this.extensions.delete(extensionId);
			new Notice(`Extension "${extension.name}" unloaded`);
			return true;
		} catch (error) {
			console.error(`Failed to unload extension ${extensionId}:`, error);
			return false;
		}
	}

	getExtension(extensionId: string): AIChatExtension | undefined {
		return this.extensions.get(extensionId);
	}

	getAllExtensions(): AIChatExtension[] {
		return Array.from(this.extensions.values());
	}

	// ==================== Command Registration ====================

	registerCommand(command: APICommand): void {
		if (this.commands.has(command.id)) {
			console.warn(`Command ${command.id} is already registered`);
			return;
		}

		this.commands.set(command.id, command);

		// Register with Obsidian
		this.plugin.addCommand({
			id: `api-${command.id}`,
			name: command.name,
			callback: command.callback
		});
	}

	unregisterCommand(commandId: string): void {
		this.commands.delete(commandId);
		// Note: Obsidian doesn't support unregistering commands, 
		// but we can mark them as disabled
	}

	executeCommand(commandId: string): void {
		const command = this.commands.get(commandId);
		if (command) {
			command.callback();
		} else {
			console.warn(`Command ${commandId} not found`);
		}
	}

	// ==================== Event System ====================

	on(event: APIEventType, callback: EventCallback): () => void {
		if (!this.eventListeners.has(event)) {
			this.eventListeners.set(event, new Set());
		}
		
		this.eventListeners.get(event)!.add(callback);
		
		// Return unsubscribe function
		return () => {
			this.eventListeners.get(event)?.delete(callback);
		};
	}

	off(event: APIEventType, callback: EventCallback): void {
		this.eventListeners.get(event)?.delete(callback);
	}

	emit(event: APIEventType, data?: any): void {
		const listeners = this.eventListeners.get(event);
		if (listeners) {
			listeners.forEach(callback => {
				try {
					callback(data);
				} catch (error) {
					console.error(`Error in event listener for ${event}:`, error);
				}
			});
		}

		// Also notify extensions
		this.extensions.forEach(ext => {
			if (event === 'message:received' && ext.onMessage) {
				ext.onMessage(data?.message, data?.context);
			}
			if (event === 'note:opened' && ext.onNoteOpen) {
				ext.onNoteOpen(data);
			}
			if (event === 'settings:changed' && ext.onSettingsChange) {
				ext.onSettingsChange(data);
			}
		});
	}

	// ==================== Utility Methods ====================

	async createNote(title: string, content: string, folder?: string): Promise<TFile | null> {
		const folderPath = folder || '';
		const fileName = `${folderPath}${title}.md`;
		
		try {
			// Ensure folder exists
			if (folder) {
				const existingFolder = this.plugin.app.vault.getAbstractFileByPath(folder);
				if (!existingFolder) {
					await this.plugin.app.vault.createFolder(folder);
				}
			}
			
			return await this.plugin.app.vault.create(fileName, content);
		} catch (error) {
			console.error('Failed to create note:', error);
			return null;
		}
	}

	async readNote(file: TFile | string): Promise<string> {
		const targetFile = typeof file === 'string' 
			? this.plugin.app.vault.getAbstractFileByPath(file)
			: file;
		
		if (targetFile instanceof TFile) {
			return await this.plugin.app.vault.read(targetFile);
		}
		
		throw new Error('File not found');
	}

	async updateNote(file: TFile | string, content: string): Promise<void> {
		const targetFile = typeof file === 'string'
			? this.plugin.app.vault.getAbstractFileByPath(file)
			: file;
		
		if (targetFile instanceof TFile) {
			await this.plugin.app.vault.modify(targetFile, content);
		} else {
			throw new Error('File not found');
		}
	}

	getAllNotes(): TFile[] {
		return this.plugin.app.vault.getMarkdownFiles();
	}

	async searchNotes(query: string): Promise<TFile[]> {
		return await this.search.semanticSearch(query);
	}

	showNotice(message: string, duration?: number): void {
		new Notice(message, duration);
	}

	// ==================== AI Enhancement Methods ====================

	async enhanceWithAI(text: string, enhancement: 'summarize' | 'expand' | 'rewrite' | 'translate'): Promise<string> {
		const prompts = {
			summarize: `Summarize the following text concisely:\n\n${text}`,
			expand: `Expand on the following text with more detail:\n\n${text}`,
			rewrite: `Rewrite the following text to improve clarity and flow:\n\n${text}`,
			translate: `Translate the following text to English (if not already) or maintain the current language:\n\n${text}`
		};

		return this.ai.generateResponse(prompts[enhancement]);
	}

	async suggestConnections(file: TFile): Promise<TFile[]> {
		const content = await this.readNote(file);
		return await this.search.semanticSearch(content.substring(0, 1000));
	}

	async generateTags(content: string): Promise<string[]> {
		const prompt = `Generate 3-5 relevant tags for the following content. Return only the tags separated by commas, without the # symbol:\n\n${content.substring(0, 500)}`;
		const response = await this.ai.generateResponse(prompt);
		return response.split(',').map(t => t.trim()).filter(t => t);
	}

	// ==================== Settings Access ====================

	getSettings() {
		return { ...this.plugin.settings };
	}

	async updateSettings(partialSettings: Partial<typeof this.plugin.settings>): Promise<void> {
		Object.assign(this.plugin.settings, partialSettings);
		await this.plugin.saveSettings();
		this.emit('settings:changed', this.plugin.settings);
	}

	// ==================== UI Methods ====================

	openChatView(): void {
		this.plugin.activateChatView();
	}

	openNoteBrowserView(): void {
		this.plugin.activateNoteBrowserView();
	}

	openSemanticSearch(): void {
		this.plugin.openSemanticSearch();
	}

	// ==================== Extension Helper Methods ====================

	/**
	 * Helper to create a simple extension
	 */
	createExtension(config: {
		id: string;
		name: string;
		version: string;
		onLoad?: (api: PluginAPI) => void;
		onUnload?: () => void;
		onMessage?: (message: string, context: any) => Promise<string | null>;
	}): AIChatExtension {
		return {
			id: config.id,
			name: config.name,
			version: config.version,
			onLoad: config.onLoad || (() => {}),
			onUnload: config.onUnload || (() => {}),
			onMessage: config.onMessage
		};
	}

	/**
	 * Example extension for documentation
	 */
	getExampleExtension(): string {
		return `
// Example Extension
const myExtension = {
	id: 'my-custom-extension',
	name: 'My Custom Extension',
	version: '1.0.0',
	author: 'Your Name',
	
	onLoad(api) {
		// Register a command
		api.registerCommand({
			id: 'say-hello',
			name: 'Say Hello',
			callback: () => {
				api.showNotice('Hello from my extension!');
			}
		});
		
		// Listen for events
		api.on('message:received', (data) => {
			console.log('New message:', data.message);
		});
	},
	
	onUnload() {
		console.log('Extension unloaded');
	},
	
	async onMessage(message, context) {
		// Process messages
		if (message.includes('hello')) {
			return 'Hello there!';
		}
		return null;
	}
};

// Register the extension
app.plugins.plugins['ai-chat-notes'].api.registerExtension(myExtension);
		`.trim();
	}
}
