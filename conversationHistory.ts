import { ConversationMessage } from './settings';

export class ConversationHistory {
	private conversations: Map<string, ConversationMessage[]>;
	private maxLength: number;

	constructor(maxLength: number = 10) {
		this.conversations = new Map();
		this.maxLength = maxLength;
	}

	addMessage(conversationId: string, message: ConversationMessage): void {
		if (!this.conversations.has(conversationId)) {
			this.conversations.set(conversationId, []);
		}

		const history = this.conversations.get(conversationId)!;
		history.push(message);

		// Keep only the last N messages
		if (history.length > this.maxLength) {
			history.shift();
		}
	}

	getHistory(conversationId: string): ConversationMessage[] {
		return this.conversations.get(conversationId) || [];
	}

	clearHistory(conversationId: string): void {
		this.conversations.delete(conversationId);
	}

	clearAll(): void {
		this.conversations.clear();
	}

	exportHistory(conversationId: string): string {
		const history = this.getHistory(conversationId);
		return JSON.stringify(history, null, 2);
	}

	importHistory(conversationId: string, jsonData: string): void {
		try {
			const history = JSON.parse(jsonData) as ConversationMessage[];
			this.conversations.set(conversationId, history);
		} catch (error) {
			throw new Error(`Failed to import conversation history: ${error.message}`);
		}
	}

	getAllConversations(): string[] {
		return Array.from(this.conversations.keys());
	}

	getConversationSummary(conversationId: string): string {
		const history = this.getHistory(conversationId);
		if (history.length === 0) return 'No messages';
		
		const userMessages = history.filter(m => m.role === 'user').length;
		const assistantMessages = history.filter(m => m.role === 'assistant').length;
		return `${history.length} messages (${userMessages} from user, ${assistantMessages} from assistant)`;
	}
}
