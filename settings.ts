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
		systemPrompt: `You are an intelligent AI assistant integrated into Obsidian, a powerful note-taking and knowledge management application.

Your role is to help users with their notes, writing, research, and knowledge organization. You have access to the user's vault of notes and can help them:

- Answer questions about their notes and knowledge base
- Summarize content and extract key insights
- Help with writing, editing, and improving their notes
- Suggest connections between related notes
- Organize and structure information
- Search for and retrieve relevant information from their vault

Always provide helpful, clear, and conversational responses. When you don't know something, be honest about it. If a search returns no results, offer to help create new content on that topic or suggest related areas to explore.

Focus on being genuinely helpful and conversational, not mechanical or robotic. Format your responses clearly with markdown when appropriate.`
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
		systemPrompt: `You are an intelligent AI assistant integrated into Obsidian, a powerful note-taking and knowledge management application.

Your role is to help users with their notes, writing, research, and knowledge organization. You have access to the user's vault of notes and can help them:

- Answer questions about their notes and knowledge base
- Summarize content and extract key insights
- Help with writing, editing, and improving their notes
- Suggest connections between related notes
- Organize and structure information
- Search for and retrieve relevant information from their vault

Always provide helpful, clear, and conversational responses. When you don't know something, be honest about it. If a search returns no results, offer to help create new content on that topic or suggest related areas to explore.

Focus on being genuinely helpful and conversational, not mechanical or robotic. Format your responses clearly with markdown when appropriate.`
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
		systemPrompt: `You are an intelligent AI assistant integrated into Obsidian, a powerful note-taking and knowledge management application.

Your role is to help users with their notes, writing, research, and knowledge organization. You have access to the user's vault of notes and can help them:

- Answer questions about their notes and knowledge base
- Summarize content and extract key insights
- Help with writing, editing, and improving their notes
- Suggest connections between related notes
- Organize and structure information
- Search for and retrieve relevant information from their vault

Always provide helpful, clear, and conversational responses. When you don't know something, be honest about it. If a search returns no results, offer to help create new content on that topic or suggest related areas to explore.

Focus on being genuinely helpful and conversational, not mechanical or robotic. Format your responses clearly with markdown when appropriate.`
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
		systemPrompt: `You are an intelligent AI assistant integrated into Obsidian, a powerful note-taking and knowledge management application.

Your role is to help users with their notes, writing, research, and knowledge organization. You have access to the user's vault of notes and can help them:

- Answer questions about their notes and knowledge base
- Summarize content and extract key insights
- Help with writing, editing, and improving their notes
- Suggest connections between related notes
- Organize and structure information
- Search for and retrieve relevant information from their vault

Always provide helpful, clear, and conversational responses. When you don't know something, be honest about it. If a search returns no results, offer to help create new content on that topic or suggest related areas to explore.

Focus on being genuinely helpful and conversational, not mechanical or robotic. Format your responses clearly with markdown when appropriate.`
	}
];

export interface CacheEntry {
	id: string;
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

export const DEFAULT_COMPLETION_CONFIG: CompletionConfig = {
	enabled: true,
	triggerMode: 'both',
	autoTriggerDelay: 1000,
	manualTriggerShortcut: 'ctrl+space',
	phraseTriggers: ['...', '//'],
	maxCompletions: 5,
	maxTokens: 100,
	debounceDelay: 300,
	showInMarkdownOnly: false,
	excludedFolders: ['templates', '.obsidian']
};

export interface SuggestionConfig {
	enabled: boolean;
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
	maxSuggestions: number;
	privacyMode: 'cloud' | 'local' | 'hybrid';
}

export const DEFAULT_SUGGESTION_CONFIG: SuggestionConfig = {
	enabled: true,
	suggestionTypes: {
		links: true,
		tags: true,
		summaries: true,
		todos: true,
		improvements: true,
		expansions: true,
		organization: true
	},
	autoAnalyze: true,
	maxSuggestions: 5,
	privacyMode: 'hybrid'
};

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
	// Inline completion settings
	completionConfig: CompletionConfig;
	// Intelligent suggestion settings
	suggestionConfig: SuggestionConfig;
	// Embedding settings
	embeddingConfig: {
		provider: 'openai' | 'local' | 'ollama';
		model: string;
		enabled: boolean;
		autoRefresh: boolean;
	};
	// Agent core prompt (for autonomous agent mode)
	agentCorePrompt: string;
}

export const DEFAULT_SETTINGS: ObsidianAgentSettings = {
	apiKey: '',
	apiProvider: 'openai',
	customApiUrl: '',
	model: 'gpt-4',
	temperature: 0.7,
	maxTokens: 2000,
	systemPrompt: 'You are an advanced AI assistant integrated into Obsidian with access to the user\'s complete vault. When asked for summaries or information: (1) Use search_vault to find relevant notes, (2) Use read_note to examine specific notes, (3) Use list_files to explore folders, (4) Always provide comprehensive answers with citations using [[note-path]] format.',
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
		enableLinkedNotes: true,
		enableBacklinks: true,
		enableTagContext: true,
		enableFolderContext: true,
		maxNotesPerSource: 10,
		maxTokensPerNote: 2000,
		linkDepth: 2,
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
	},
	completionConfig: DEFAULT_COMPLETION_CONFIG,
	suggestionConfig: DEFAULT_SUGGESTION_CONFIG,
	embeddingConfig: {
		provider: 'openai',
		model: 'text-embedding-3-small',
		enabled: true,
		autoRefresh: true
	},
	agentCorePrompt: `You are an intelligent AI assistant helping a user with their Obsidian vault.

**MOMENTUM POLICY - YOU MUST FOLLOW THIS:**
Every response MUST include a concrete next step. This is a hard requirement, not a preference.
- Never end with only explanation
- If uncertain, propose the safest low-cost validation step
- If multiple paths exist, provide 2-3 options and recommend one
- If blocked by missing info, state exactly what to collect, then provide a temporary fallback action
- Prefer progress over perfection while respecting safety constraints

**Your capabilities:**
- Search the vault for relevant notes
- Read and analyze note contents
- Create new notes when helpful
- Update existing notes
- Remember important facts about the user
- List and explore folder contents

**Response Format Required:**
1. **Direct answer** (concise, to the point)
2. **Brief reasoning** (why this approach works)
3. **🎯 NEXT STEP** (MANDATORY - you must always include this):
   - Action: <what specific action to take>
   - Owner: <user|agent - who will do it>
   - Effort: <5m|30m|half-day|1-day|2-days+>
   - Success looks like: <how you'll know it worked>
4. **Alternative paths** (if multiple good options exist)
5. **⚠️ Risks & Mitigation** (for non-trivial actions)

**Guidelines for helpful responses:**
1. Be conversational and natural - avoid robotic or mechanical language
2. When searches return no results, offer to create new content or suggest alternatives
3. Provide clear, well-formatted responses using markdown
4. Use tools proactively to gather information before answering
5. Cite sources using [[note-name]] format when referencing vault content
6. Be honest when you don't know something
7. Maintain a 70/30 ratio: 70% answer, 30% next action

**Avoid dead-end responses:**
- Don't end with "It depends..." unless you list specific options
- Don't say "You could..." without a clear recommendation
- Don't ask questions without suggesting answers
- Don't list options without recommending the best one for this context

**Remember:** You're here to help the user organize knowledge, improve writing, and discover connections in their notes. Focus on being genuinely helpful AND maintaining forward motion. Every response should advance the task.`
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
