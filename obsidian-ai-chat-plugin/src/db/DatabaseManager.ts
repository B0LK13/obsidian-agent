import { Platform } from 'obsidian';
import AIChatNotesPlugin from '../../main';

interface StoredChatMessage {
	id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	timestamp: number;
	contextFile?: string;
}

interface StoredEmbedding {
	path: string;
	embedding: number[];
	lastModified: number;
}

interface StoredChatSession {
	id: string;
	title: string;
	messages: StoredChatMessage[];
	createdAt: number;
	updatedAt: number;
	contextNotes?: string[];
}

export class DatabaseManager {
	plugin: AIChatNotesPlugin;
	private db: any = null;
	private isInitialized: boolean = false;
	
	constructor(plugin: AIChatNotesPlugin) {
		this.plugin = plugin;
	}
	
	async initialize() {
		if (this.isInitialized) return;
		
		try {
			// Use LocalForage for cross-platform storage
			const localforage = await import('localforage');
			
			this.db = localforage.default.createInstance({
				name: 'AIChatNotes',
				version: 1.0,
				storeName: 'data',
				description: 'AI Chat & Notes database'
			});
			
			this.isInitialized = true;
		} catch (error) {
			console.error('Failed to initialize database:', error);
			// Fallback to simple in-memory storage
			this.db = {
				data: new Map(),
				async getItem(key: string) { return this.data.get(key); },
				async setItem(key: string, value: any) { this.data.set(key, value); },
				async removeItem(key: string) { this.data.delete(key); },
				async keys() { return Array.from(this.data.keys()); }
			};
			this.isInitialized = true;
		}
	}
	
	async close() {
		// LocalForage doesn't need explicit closing
		this.isInitialized = false;
	}
	
	// Chat History Methods
	async getChatHistory(): Promise<StoredChatMessage[]> {
		if (!this.isInitialized) return [];
		const history = await this.db.getItem('chatHistory');
		return history || [];
	}
	
	async saveChatHistory(messages: StoredChatMessage[]) {
		if (!this.isInitialized) return;
		await this.db.setItem('chatHistory', messages);
	}
	
	async clearChatHistory() {
		if (!this.isInitialized) return;
		await this.db.removeItem('chatHistory');
	}
	
	// Embeddings Methods
	async getEmbeddings(): Promise<StoredEmbedding[]> {
		if (!this.isInitialized) return [];
		const embeddings = await this.db.getItem('embeddings');
		return embeddings || [];
	}
	
	async saveEmbedding(embedding: StoredEmbedding) {
		if (!this.isInitialized) return;
		const embeddings = await this.getEmbeddings();
		const index = embeddings.findIndex(e => e.path === embedding.path);
		
		if (index >= 0) {
			embeddings[index] = embedding;
		} else {
			embeddings.push(embedding);
		}
		
		await this.db.setItem('embeddings', embeddings);
	}
	
	async deleteEmbedding(path: string) {
		if (!this.isInitialized) return;
		const embeddings = await this.getEmbeddings();
		const filtered = embeddings.filter(e => e.path !== path);
		await this.db.setItem('embeddings', filtered);
	}
	
	async clearEmbeddings() {
		if (!this.isInitialized) return;
		await this.db.removeItem('embeddings');
	}
	
	// Chat Sessions Methods
	async getChatSessions(): Promise<StoredChatSession[]> {
		if (!this.isInitialized) return [];
		const sessions = await this.db.getItem('chatSessions');
		return sessions || [];
	}
	
	async saveChatSession(session: StoredChatSession) {
		if (!this.isInitialized) return;
		const sessions = await this.getChatSessions();
		const index = sessions.findIndex(s => s.id === session.id);
		
		if (index >= 0) {
			sessions[index] = session;
		} else {
			sessions.push(session);
		}
		
		await this.db.setItem('chatSessions', sessions);
	}
	
	async deleteChatSession(sessionId: string) {
		if (!this.isInitialized) return;
		const sessions = await this.getChatSessions();
		const filtered = sessions.filter(s => s.id !== sessionId);
		await this.db.setItem('chatSessions', filtered);
	}
	
	// Settings Methods (for sync across devices)
	async getSyncedSettings(): Promise<Record<string, any> | null> {
		if (!this.isInitialized) return null;
		return await this.db.getItem('syncedSettings');
	}
	
	async saveSyncedSettings(settings: Record<string, any>) {
		if (!this.isInitialized) return;
		await this.db.setItem('syncedSettings', settings);
	}
	
	// General Storage Methods
	async getItem<T>(key: string): Promise<T | null> {
		if (!this.isInitialized) return null;
		return await this.db.getItem(key);
	}
	
	async setItem<T>(key: string, value: T) {
		if (!this.isInitialized) return;
		await this.db.setItem(key, value);
	}
	
	async removeItem(key: string) {
		if (!this.isInitialized) return;
		await this.db.removeItem(key);
	}
	
	// Export/Import Methods
	async exportAllData(): Promise<string> {
		const data = {
			chatHistory: await this.getChatHistory(),
			embeddings: await this.getEmbeddings(),
			chatSessions: await this.getChatSessions(),
			exportDate: new Date().toISOString(),
			version: '1.0.0'
		};
		
		return JSON.stringify(data, null, 2);
	}
	
	async importAllData(json: string): Promise<boolean> {
		try {
			const data = JSON.parse(json);
			
			if (data.chatHistory) {
				await this.saveChatHistory(data.chatHistory);
			}
			if (data.embeddings) {
				await this.db.setItem('embeddings', data.embeddings);
			}
			if (data.chatSessions) {
				await this.db.setItem('chatSessions', data.chatSessions);
			}
			
			return true;
		} catch (error) {
			console.error('Failed to import data:', error);
			return false;
		}
	}
	
	// Stats Methods
	async getStats(): Promise<{
		messageCount: number;
		sessionCount: number;
		embeddingCount: number;
		storageSize: string;
	}> {
		const history = await this.getChatHistory();
		const sessions = await this.getChatSessions();
		const embeddings = await this.getEmbeddings();
		
		// Estimate storage size
		const data = {
			history,
			sessions,
			embeddings
		};
		const json = JSON.stringify(data);
		const sizeInKB = (json.length / 1024).toFixed(2);
		
		return {
			messageCount: history.length,
			sessionCount: sessions.length,
			embeddingCount: embeddings.length,
			storageSize: `${sizeInKB} KB`
		};
	}
	
	// Maintenance Methods
	async cleanup() {
		// Remove embeddings for files that no longer exist
		const embeddings = await this.getEmbeddings();
		const vault = this.plugin.app.vault;
		
		const validEmbeddings = embeddings.filter(e => {
			const file = vault.getAbstractFileByPath(e.path);
			return file !== null;
		});
		
		if (validEmbeddings.length !== embeddings.length) {
			await this.db.setItem('embeddings', validEmbeddings);
		}
	}
	
	async clearAllData() {
		if (!this.isInitialized) return;
		
		const keys = await this.db.keys();
		for (const key of keys) {
			await this.db.removeItem(key);
		}
	}
}
