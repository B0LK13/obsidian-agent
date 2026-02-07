import { Notice, TFile } from 'obsidian';
import AIChatNotesPlugin from '../../main';

export interface ChatSession {
	id: string;
	title: string;
	messages: ChatMessage[];
	createdAt: number;
	updatedAt: number;
	contextNotes?: string[];
}

export interface ChatMessage {
	id: string;
	role: 'user' | 'assistant' | 'system';
	content: string;
	timestamp: number;
	attachments?: string[];
}

export class ChatService {
	plugin: AIChatNotesPlugin;
	currentSession: ChatSession | null = null;
	sessions: ChatSession[] = [];
	
	constructor(plugin: AIChatNotesPlugin) {
		this.plugin = plugin;
		this.loadSessions();
	}
	
	async loadSessions() {
		this.sessions = await this.plugin.dbManager.getChatSessions();
	}
	
	createSession(title?: string): ChatSession {
		const session: ChatSession = {
			id: crypto.randomUUID(),
			title: title || 'New Chat',
			messages: [],
			createdAt: Date.now(),
			updatedAt: Date.now()
		};
		
		this.sessions.unshift(session);
		this.currentSession = session;
		this.saveSession(session);
		
		return session;
	}
	
	async saveSession(session: ChatSession) {
		await this.plugin.dbManager.saveChatSession(session);
	}
	
	async deleteSession(sessionId: string) {
		this.sessions = this.sessions.filter(s => s.id !== sessionId);
		await this.plugin.dbManager.deleteChatSession(sessionId);
		
		if (this.currentSession?.id === sessionId) {
			this.currentSession = null;
		}
	}
	
	getSession(sessionId: string): ChatSession | undefined {
		return this.sessions.find(s => s.id === sessionId);
	}
	
	setCurrentSession(session: ChatSession) {
		this.currentSession = session;
	}
	
	async addMessage(sessionId: string, message: ChatMessage) {
		const session = this.getSession(sessionId);
		if (!session) return;
		
		session.messages.push(message);
		session.updatedAt = Date.now();
		
		await this.saveSession(session);
	}
	
	async convertToNote(sessionId?: string): Promise<TFile | null> {
		const session = sessionId 
			? this.getSession(sessionId) 
			: this.currentSession;
		
		if (!session || session.messages.length === 0) {
			new Notice('No chat to convert');
			return null;
		}
		
		// Generate note content
		let content = `# ${session.title}\n\n`;
		content += `*Created: ${new Date(session.createdAt).toLocaleString()}*\n\n`;
		content += `---\n\n`;
		
		for (const message of session.messages) {
			const role = message.role === 'user' ? '**You**' : '**AI**';
			content += `${role} (${new Date(message.timestamp).toLocaleTimeString()}):\n`;
			content += `${message.content}\n\n`;
		}
		
		// Create file
		const fileName = `Chat-${session.title.replace(/[^a-zA-Z0-9]/g, '-')}-${Date.now()}.md`;
		const filePath = `AI-Chat/${fileName}`;
		
		// Ensure folder exists
		const folder = this.plugin.app.vault.getAbstractFileByPath('AI-Chat');
		if (!folder) {
			await this.plugin.app.vault.createFolder('AI-Chat');
		}
		
		const file = await this.plugin.app.vault.create(filePath, content);
		new Notice('Chat converted to note');
		
		return file;
	}
	
	async generateSessionTitle(sessionId: string): Promise<string> {
		const session = this.getSession(sessionId);
		if (!session || session.messages.length === 0) {
			return 'New Chat';
		}
		
		// Get first user message or first few messages
		const firstMessage = session.messages.find(m => m.role === 'user');
		if (!firstMessage) return 'New Chat';
		
		// Generate title using AI
		const prompt = `Based on this message, generate a short (3-5 words) chat title:\n\n${firstMessage.content.substring(0, 200)}`;
		
		try {
			const title = await this.plugin.aiService.generateResponse(prompt);
			return title.trim().replace(/["']/g, '');
		} catch (error) {
			// Fallback to first few words
			return firstMessage.content.substring(0, 30).trim() + '...';
		}
	}
	
	async autoGenerateTitle(sessionId: string) {
		const title = await this.generateSessionTitle(sessionId);
		const session = this.getSession(sessionId);
		if (session) {
			session.title = title;
			await this.saveSession(session);
		}
	}
	
	searchSessions(query: string): ChatSession[] {
		const lowerQuery = query.toLowerCase();
		return this.sessions.filter(session => {
			// Search in title
			if (session.title.toLowerCase().includes(lowerQuery)) return true;
			
			// Search in messages
			return session.messages.some(m => 
				m.content.toLowerCase().includes(lowerQuery)
			);
		});
	}
	
	exportSession(sessionId: string): string {
		const session = this.getSession(sessionId);
		if (!session) return '';
		
		return JSON.stringify(session, null, 2);
	}
	
	importSession(json: string): ChatSession | null {
		try {
			const session: ChatSession = JSON.parse(json);
			session.id = crypto.randomUUID(); // New ID
			session.createdAt = Date.now();
			session.updatedAt = Date.now();
			
			this.sessions.unshift(session);
			this.saveSession(session);
			
			return session;
		} catch (error) {
			new Notice('Failed to import chat session');
			return null;
		}
	}
}
