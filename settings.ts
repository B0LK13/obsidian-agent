export interface CustomTemplate {
	id: string;
	name: string;
	prompt: string;
	description: string;
}

export interface ConversationMessage {
	role: 'user' | 'assistant' | 'system';
	content: string;
	timestamp: number;
}

export interface ObsidianAgentSettings {
	apiKey: string;
	apiProvider: 'openai' | 'anthropic' | 'custom';
	customApiUrl: string;
	model: string;
	temperature: number;
	maxTokens: number;
	systemPrompt: string;
	enableContextAwareness: boolean;
	// Advanced features
	enableConversationHistory: boolean;
	maxConversationLength: number;
	enableCaching: boolean;
	cacheExpiration: number; // in minutes
	enableTokenTracking: boolean;
	customTemplates: CustomTemplate[];
	enableSmartSuggestions: boolean;
	enableAutoLinking: boolean;
	defaultLanguage: string;
	enableStreaming: boolean;
	showTokenCount: boolean;
	saveConversations: boolean;
	maxCachedResponses: number;
}

export const DEFAULT_SETTINGS: ObsidianAgentSettings = {
	apiKey: '',
	apiProvider: 'openai',
	customApiUrl: '',
	model: 'gpt-4',
	temperature: 0.7,
	maxTokens: 2000,
	systemPrompt: 'You are a helpful AI assistant integrated into Obsidian. Help users with note-taking, knowledge management, and content generation.',
	enableContextAwareness: true,
	// Advanced features defaults
	enableConversationHistory: true,
	maxConversationLength: 10,
	enableCaching: false,
	cacheExpiration: 60,
	enableTokenTracking: true,
	customTemplates: [],
	enableSmartSuggestions: true,
	enableAutoLinking: false,
	defaultLanguage: 'en',
	enableStreaming: false,
	showTokenCount: true,
	saveConversations: false,
	maxCachedResponses: 100
}
