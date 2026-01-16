export interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
	timestamp: number;
}

export interface Conversation {
	id: string;
	title: string;
	messages: ChatMessage[];
	createdAt: number;
	updatedAt: number;
}

export interface ObsidianAgentSettings {
	apiKey: string;
	apiProvider: 'openai' | 'anthropic' | 'custom';
	customApiUrl: string;
	model: string;
	temperature: number;
	maxTokens: number;
	systemPrompt: string;
	enableAutoCompletion: boolean;
	enableContextAwareness: boolean;
	enableTokenTracking: boolean;
	costThreshold: number;
	totalRequests?: number;
	totalTokensUsed?: number;
	estimatedCost?: number;
	// Conversation persistence
	conversations: Conversation[];
	activeConversationId?: string;
	maxConversations: number;
	enableConversationPersistence: boolean;
}

export const DEFAULT_SETTINGS: ObsidianAgentSettings = {
	apiKey: '',
	apiProvider: 'openai',
	customApiUrl: '',
	model: 'gpt-4',
	temperature: 0.7,
	maxTokens: 2000,
	systemPrompt: 'You are a helpful AI assistant integrated into Obsidian. Help users with note-taking, knowledge management, and content generation.',
	enableAutoCompletion: false,
	enableContextAwareness: true,
	enableTokenTracking: true,
	costThreshold: 10,
	// Conversation persistence defaults
	conversations: [],
	maxConversations: 20,
	enableConversationPersistence: true
}
