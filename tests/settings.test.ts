import { describe, it, expect } from 'vitest';
import { 
	DEFAULT_SETTINGS, 
	DEFAULT_COMPLETION_CONFIG,
	DEFAULT_SUGGESTION_CONFIG,
	DEFAULT_PROFILES,
	generateProfileId,
	createDefaultProfile,
	type AIProfile,
	type ObsidianAgentSettings,
	type CompletionConfig,
	type SuggestionConfig
} from '../settings';

describe('Settings', () => {
	describe('DEFAULT_SETTINGS', () => {
		it('should have correct default API settings', () => {
			expect(DEFAULT_SETTINGS.apiKey).toBe('');
			expect(DEFAULT_SETTINGS.apiProvider).toBe('openai');
			expect(DEFAULT_SETTINGS.customApiUrl).toBe('');
			expect(DEFAULT_SETTINGS.model).toBe('gpt-4');
		});

		it('should have correct default model parameters', () => {
			expect(DEFAULT_SETTINGS.temperature).toBe(0.7);
			expect(DEFAULT_SETTINGS.maxTokens).toBe(2000);
			expect(DEFAULT_SETTINGS.systemPrompt).toContain('helpful AI assistant');
		});

		it('should have correct default feature toggles', () => {
			expect(DEFAULT_SETTINGS.enableAutoCompletion).toBe(false);
			expect(DEFAULT_SETTINGS.enableContextAwareness).toBe(true);
			expect(DEFAULT_SETTINGS.enableTokenTracking).toBe(true);
		});

		it('should have correct conversation settings', () => {
			expect(DEFAULT_SETTINGS.conversations).toEqual([]);
			expect(DEFAULT_SETTINGS.maxConversations).toBe(20);
			expect(DEFAULT_SETTINGS.enableConversationPersistence).toBe(true);
		});

		it('should have correct profile settings', () => {
			expect(DEFAULT_SETTINGS.profiles).toEqual([]);
			expect(DEFAULT_SETTINGS.activeProfileId).toBe('default');
		});

		it('should have correct context config defaults', () => {
			const config = DEFAULT_SETTINGS.contextConfig;
			expect(config.enableLinkedNotes).toBe(false);
			expect(config.enableBacklinks).toBe(false);
			expect(config.enableTagContext).toBe(false);
			expect(config.enableFolderContext).toBe(false);
			expect(config.maxNotesPerSource).toBe(5);
			expect(config.maxTokensPerNote).toBe(1000);
			expect(config.linkDepth).toBe(1);
			expect(config.excludeFolders).toBe('templates, .obsidian');
		});

		it('should have correct cache config defaults', () => {
			const config = DEFAULT_SETTINGS.cacheConfig;
			expect(config.enabled).toBe(true);
			expect(config.maxEntries).toBe(100);
			expect(config.maxAgeDays).toBe(30);
			expect(config.matchThreshold).toBe(1.0);
		});

		it('should have correct accessibility config defaults', () => {
			const config = DEFAULT_SETTINGS.accessibilityConfig;
			expect(config.enableHighContrast).toBe(false);
			expect(config.enableReducedMotion).toBe(false);
		});

		it('should have cost threshold set', () => {
			expect(DEFAULT_SETTINGS.costThreshold).toBe(10);
		});
	});

	describe('DEFAULT_COMPLETION_CONFIG', () => {
		it('should have correct default completion settings', () => {
			expect(DEFAULT_COMPLETION_CONFIG.enabled).toBe(true);
			expect(DEFAULT_COMPLETION_CONFIG.triggerMode).toBe('both');
			expect(DEFAULT_COMPLETION_CONFIG.autoTriggerDelay).toBe(1000);
			expect(DEFAULT_COMPLETION_CONFIG.manualTriggerShortcut).toBe('ctrl+space');
		});

		it('should have correct phrase triggers', () => {
			expect(DEFAULT_COMPLETION_CONFIG.phraseTriggers).toEqual(['...', '//']);
		});

		it('should have correct limits', () => {
			expect(DEFAULT_COMPLETION_CONFIG.maxCompletions).toBe(5);
			expect(DEFAULT_COMPLETION_CONFIG.maxTokens).toBe(100);
			expect(DEFAULT_COMPLETION_CONFIG.debounceDelay).toBe(300);
		});

		it('should have correct filter settings', () => {
			expect(DEFAULT_COMPLETION_CONFIG.showInMarkdownOnly).toBe(false);
			expect(DEFAULT_COMPLETION_CONFIG.excludedFolders).toEqual(['templates', '.obsidian']);
		});
	});

	describe('DEFAULT_SUGGESTION_CONFIG', () => {
		it('should have enabled by default', () => {
			expect(DEFAULT_SUGGESTION_CONFIG.enabled).toBe(true);
		});

		it('should have all suggestion types enabled', () => {
			const types = DEFAULT_SUGGESTION_CONFIG.suggestionTypes;
			expect(types.links).toBe(true);
			expect(types.tags).toBe(true);
			expect(types.summaries).toBe(true);
			expect(types.todos).toBe(true);
			expect(types.improvements).toBe(true);
			expect(types.expansions).toBe(true);
			expect(types.organization).toBe(true);
		});

		it('should have correct analysis settings', () => {
			expect(DEFAULT_SUGGESTION_CONFIG.autoAnalyze).toBe(true);
			expect(DEFAULT_SUGGESTION_CONFIG.maxSuggestions).toBe(5);
			expect(DEFAULT_SUGGESTION_CONFIG.privacyMode).toBe('hybrid');
		});
	});

	describe('DEFAULT_PROFILES', () => {
		it('should have 4 default profiles', () => {
			expect(DEFAULT_PROFILES).toHaveLength(4);
		});

		it('should have OpenAI GPT-4 profile', () => {
			const profile = DEFAULT_PROFILES.find(p => p.id === 'openai-gpt4');
			expect(profile).toBeDefined();
			expect(profile?.apiProvider).toBe('openai');
			expect(profile?.model).toBe('gpt-4');
		});

		it('should have OpenAI GPT-3.5 profile', () => {
			const profile = DEFAULT_PROFILES.find(p => p.id === 'openai-gpt35');
			expect(profile).toBeDefined();
			expect(profile?.apiProvider).toBe('openai');
			expect(profile?.model).toBe('gpt-3.5-turbo');
		});

		it('should have Anthropic Claude profile', () => {
			const profile = DEFAULT_PROFILES.find(p => p.id === 'anthropic-claude');
			expect(profile).toBeDefined();
			expect(profile?.apiProvider).toBe('anthropic');
			expect(profile?.model).toContain('claude');
		});

		it('should have Ollama local profile', () => {
			const profile = DEFAULT_PROFILES.find(p => p.id === 'ollama-local');
			expect(profile).toBeDefined();
			expect(profile?.apiProvider).toBe('ollama');
			expect(profile?.customApiUrl).toBe('http://localhost:11434');
		});

		it('should have consistent settings across profiles', () => {
			for (const profile of DEFAULT_PROFILES) {
				expect(profile.temperature).toBe(0.7);
				expect(profile.maxTokens).toBe(2000);
				expect(profile.systemPrompt).toContain('helpful AI assistant');
				expect(profile.apiKey).toBe('');
			}
		});
	});

	describe('generateProfileId', () => {
		it('should generate unique IDs', () => {
			const id1 = generateProfileId();
			const id2 = generateProfileId();
			expect(id1).not.toBe(id2);
		});

		it('should start with "profile_"', () => {
			const id = generateProfileId();
			expect(id.startsWith('profile_')).toBe(true);
		});

		it('should contain timestamp', () => {
			const before = Date.now();
			const id = generateProfileId();
			const after = Date.now();
			
			// Extract the timestamp part (between first and second underscore)
			const parts = id.split('_');
			const timestamp = parseInt(parts[1], 10);
			
			expect(timestamp).toBeGreaterThanOrEqual(before);
			expect(timestamp).toBeLessThanOrEqual(after);
		});

		it('should include random component', () => {
			const id = generateProfileId();
			const parts = id.split('_');
			expect(parts[2]).toBeDefined();
			expect(parts[2].length).toBeGreaterThan(0);
		});
	});

	describe('createDefaultProfile', () => {
		it('should create profile from settings', () => {
			const settings: ObsidianAgentSettings = {
				...DEFAULT_SETTINGS,
				apiProvider: 'anthropic',
				apiKey: 'test-key',
				model: 'claude-3-opus',
				temperature: 0.5,
				maxTokens: 4000,
				systemPrompt: 'Custom prompt',
				customApiUrl: 'https://custom.api'
			};

			const profile = createDefaultProfile(settings);

			expect(profile.id).toBe('default');
			expect(profile.name).toBe('Default');
			expect(profile.apiProvider).toBe('anthropic');
			expect(profile.apiKey).toBe('test-key');
			expect(profile.model).toBe('claude-3-opus');
			expect(profile.temperature).toBe(0.5);
			expect(profile.maxTokens).toBe(4000);
			expect(profile.systemPrompt).toBe('Custom prompt');
			expect(profile.customApiUrl).toBe('https://custom.api');
		});

		it('should copy all necessary fields', () => {
			const profile = createDefaultProfile(DEFAULT_SETTINGS);

			expect(profile).toHaveProperty('id');
			expect(profile).toHaveProperty('name');
			expect(profile).toHaveProperty('apiProvider');
			expect(profile).toHaveProperty('apiKey');
			expect(profile).toHaveProperty('customApiUrl');
			expect(profile).toHaveProperty('model');
			expect(profile).toHaveProperty('temperature');
			expect(profile).toHaveProperty('maxTokens');
			expect(profile).toHaveProperty('systemPrompt');
		});
	});

	describe('Type definitions', () => {
		it('should accept valid AIProfile', () => {
			const profile: AIProfile = {
				id: 'test',
				name: 'Test Profile',
				apiProvider: 'openai',
				apiKey: 'sk-test',
				customApiUrl: '',
				model: 'gpt-4',
				temperature: 0.7,
				maxTokens: 2000,
				systemPrompt: 'You are a test assistant'
			};

			expect(profile.apiProvider).toBe('openai');
		});

		it('should accept valid CompletionConfig', () => {
			const config: CompletionConfig = {
				enabled: true,
				triggerMode: 'manual',
				autoTriggerDelay: 500,
				manualTriggerShortcut: 'ctrl+enter',
				phraseTriggers: ['>>>'],
				maxCompletions: 3,
				maxTokens: 50,
				debounceDelay: 200,
				showInMarkdownOnly: true,
				excludedFolders: ['private']
			};

			expect(config.triggerMode).toBe('manual');
		});

		it('should accept valid SuggestionConfig', () => {
			const config: SuggestionConfig = {
				enabled: false,
				suggestionTypes: {
					links: true,
					tags: false,
					summaries: true,
					todos: false,
					improvements: true,
					expansions: false,
					organization: true
				},
				autoAnalyze: false,
				maxSuggestions: 10,
				privacyMode: 'local'
			};

			expect(config.privacyMode).toBe('local');
		});
	});
});
