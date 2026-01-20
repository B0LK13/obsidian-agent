export interface ChatMessage {
	role: 'user' | 'assistant';
	content: string;
	timestamp: number;
	fromCache?: boolean;
	tokensUsed?: number;
}

export interface Conversation {
	id: string;
	title: string;
	messages: ChatMessage[];
	createdAt: number;
	updatedAt: number;
}

export interface AIProfile {
	id: string;
	name: string;
	apiProvider: 'openai' | 'anthropic' | 'ollama' | 'custom';
	apiKey: string;
	customApiUrl: string;
	model: string;
	temperature: number;
	maxTokens: number;
	systemPrompt: string;
}

export const DEFAULT_PROFILES: AIProfile[] = [
	{
		id: 'openai-gpt4',
		name: 'OpenAI GPT-4',
		apiProvider: 'openai',
		apiKey: '',
		customApiUrl: '',
		model: 'gpt-4',
		temperature: 0.7,
		maxTokens: 2000,
		systemPrompt: 'You are a helpful AI assistant integrated into Obsidian.'
	},
	{
		id: 'openai-gpt35',
		name: 'OpenAI GPT-3.5 (Fast)',
		apiProvider: 'openai',
		apiKey: '',
		customApiUrl: '',
		model: 'gpt-3.5-turbo',
		temperature: 0.7,
		maxTokens: 2000,
		systemPrompt: 'You are a helpful AI assistant integrated into Obsidian.'
	},
	{
		id: 'anthropic-claude',
		name: 'Anthropic Claude',
		apiProvider: 'anthropic',
		apiKey: '',
		customApiUrl: '',
		model: 'claude-3-sonnet-20240229',
		temperature: 0.7,
		maxTokens: 2000,
		systemPrompt: 'You are a helpful AI assistant integrated into Obsidian.'
	},
	{
		id: 'ollama-local',
		name: 'Ollama (Local)',
		apiProvider: 'ollama',
		apiKey: '',
		customApiUrl: 'http://localhost:11434',
		model: 'llama2',
		temperature: 0.7,
		maxTokens: 2000,
		systemPrompt: 'You are a helpful AI assistant integrated into Obsidian.'
	}
];

export interface CacheEntry {
	id: string;
	cacheKey: string;
	promptHash: string;
	contextHash: string;
	prompt: string;
	response: string;
	model: string;
	temperature: number;
	tokensUsed: number;
	inputTokens: number;
	outputTokens: number;
	createdAt: number;
	accessedAt: number;
	accessCount: number;
}

export interface CacheStats {
	totalEntries: number;
	totalHits: number;
	totalMisses: number;
	estimatedSavings: number;
	cacheSize: number;
}

export interface CompletionConfig {
	enabled: boolean;
	triggerMode: 'manual' | 'auto' | 'both';
	autoTriggerDelay: number;
	manualTriggerShortcut: string;
	phraseTriggers: string[];
	maxCompletions: number;
	maxTokens: number;
	debounceDelay: number;
	showInMarkdownOnly: boolean;
	excludedFolders: string[];
}

export interface SuggestionConfig {
	enabled: boolean;
	triggerDelay: number;
	maxSuggestions: number;
	showInMarkdownOnly: boolean;
	suggestionTypes: {
		links: boolean;
		tags: boolean;
		summaries: boolean;
		todos: boolean;
		improvements: boolean;
		expansions: boolean;
		organization: boolean;
	};
	autoAnalyze: boolean;
	privacyMode: 'cloud' | 'local' | 'hybrid';
}

export interface ObsidianAgentSettings {
	// Active profile settings (for backward compatibility)
	apiKey: string;
	apiProvider: 'openai' | 'anthropic' | 'ollama' | 'custom';
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
	// AI Profiles
	profiles: AIProfile[];
	activeProfileId: string;
	// Custom prompt templates
	customTemplates: Array<{
		id: string;
		name: string;
		description: string;
		category: string;
		prompt: string;
		variables?: string[];
		isBuiltIn: boolean;
	}>;
	// Vault-wide context settings
	contextConfig: {
		enableLinkedNotes: boolean;
		enableBacklinks: boolean;
		enableTagContext: boolean;
		enableFolderContext: boolean;
		maxNotesPerSource: number;
		maxTokensPerNote: number;
		linkDepth: number;
		excludeFolders: string;
	};
	// Response caching settings
	cacheConfig: {
		enabled: boolean;
		maxEntries: number;
		maxAgeDays: number;
		matchThreshold: number;
	};
	// Persisted cache data
	cacheData: {
		entries: CacheEntry[];
		stats: CacheStats;
	};
	// Accessibility settings
	accessibilityConfig: {
		enableHighContrast: boolean;
		enableReducedMotion: boolean;
	};
	// Completion settings (optional)
	completionConfig?: CompletionConfig;
	// Suggestion settings (optional)
	suggestionConfig?: SuggestionConfig;
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
	enableConversationPersistence: true,
	// AI Profiles defaults
	profiles: [],
	activeProfileId: 'default',
	// Custom templates
	customTemplates: [],
	// Vault-wide context
	contextConfig: {
		enableLinkedNotes: false,
		enableBacklinks: false,
		enableTagContext: false,
		enableFolderContext: false,
		maxNotesPerSource: 5,
		maxTokensPerNote: 1000,
		linkDepth: 1,
		excludeFolders: 'templates, .obsidian'
	},
	// Response caching
	cacheConfig: {
		enabled: true,
		maxEntries: 100,
		maxAgeDays: 30,
		matchThreshold: 1.0
	},
	cacheData: {
		entries: [],
		stats: {
			totalEntries: 0,
			totalHits: 0,
			totalMisses: 0,
			estimatedSavings: 0,
			cacheSize: 0
		}
	},
	// Accessibility
	accessibilityConfig: {
		enableHighContrast: false,
		enableReducedMotion: false
	}
}

export function generateProfileId(): string {
	return `profile_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export function createDefaultProfile(settings: ObsidianAgentSettings): AIProfile {
	return {
		id: 'default',
		name: 'Default',
		apiProvider: settings.apiProvider,
		apiKey: settings.apiKey,
		customApiUrl: settings.customApiUrl,
		model: settings.model,
		temperature: settings.temperature,
		maxTokens: settings.maxTokens,
		systemPrompt: settings.systemPrompt
	};
}
