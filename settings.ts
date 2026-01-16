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
	enableContextAwareness: true
}
