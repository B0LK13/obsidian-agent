import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { AIService } from '../aiService';
import { DEFAULT_SETTINGS, ObsidianAgentSettings } from '../settings';

// Mock the obsidian module
vi.mock('obsidian', () => ({
	requestUrl: vi.fn()
}));

import { requestUrl } from 'obsidian';

const mockRequestUrl = requestUrl as ReturnType<typeof vi.fn>;

describe('AIService', () => {
	let aiService: AIService;
	let settings: ObsidianAgentSettings;

	beforeEach(() => {
		settings = {
			...DEFAULT_SETTINGS,
			apiKey: 'test-api-key',
			apiProvider: 'openai',
			model: 'gpt-4',
			temperature: 0.7,
			maxTokens: 2000
		};
		aiService = new AIService(settings);
		vi.clearAllMocks();
	});

	afterEach(() => {
		vi.restoreAllMocks();
	});

	describe('initialization', () => {
		it('should initialize with settings', () => {
			expect(aiService).toBeDefined();
		});

		it('should create cache service', () => {
			const cacheService = aiService.getCacheService();
			expect(cacheService).toBeDefined();
		});

		it('should import persisted cache data', () => {
			const settingsWithCache: ObsidianAgentSettings = {
				...settings,
				cacheData: {
					entries: [
						{
							id: 'test_id',
							promptHash: 'hash1',
							contextHash: 'hash2',
							prompt: 'test prompt',
							response: 'test response',
							model: 'gpt-4',
							temperature: 0.7,
							tokensUsed: 100,
							inputTokens: 50,
							outputTokens: 50,
							createdAt: Date.now(),
							accessedAt: Date.now(),
							accessCount: 1
						}
					],
					stats: {
						totalEntries: 1,
						totalHits: 0,
						totalMisses: 0,
						estimatedSavings: 0,
						cacheSize: 100
					}
				}
			};
			
			const service = new AIService(settingsWithCache);
			const entries = service.getCacheService().getAllEntries();
			expect(entries.length).toBeGreaterThan(0);
		});
	});

	describe('testConnection', () => {
		it('should return error if API key not configured', async () => {
			const noKeySettings = { ...settings, apiKey: '' };
			const service = new AIService(noKeySettings);
			
			const result = await service.testConnection();
			
			expect(result.success).toBe(false);
			expect(result.message).toContain('API key not configured');
		});

		it('should return success on valid response', async () => {
			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					choices: [{ message: { content: 'OK' } }],
					usage: { prompt_tokens: 10, completion_tokens: 5 }
				}
			});

			const result = await aiService.testConnection();

			expect(result.success).toBe(true);
			expect(result.message).toContain('Connection successful');
			expect(result.responseTime).toBeDefined();
		});

		it('should return failure on API error', async () => {
			mockRequestUrl.mockRejectedValue(new Error('Network error'));

			const result = await aiService.testConnection();

			expect(result.success).toBe(false);
			expect(result.responseTime).toBeDefined();
		});
	});

	describe('generateCompletion', () => {
		it('should throw error if no API key (non-Ollama)', async () => {
			const noKeySettings = { ...settings, apiKey: '' };
			const service = new AIService(noKeySettings);

			await expect(service.generateCompletion('test prompt'))
				.rejects.toThrow('API key not configured');
		});

		it('should not require API key for Ollama', async () => {
			const ollamaSettings = { 
				...settings, 
				apiKey: '', 
				apiProvider: 'ollama' as const 
			};
			const service = new AIService(ollamaSettings);

			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					message: { content: 'Ollama response' },
					eval_count: 50,
					prompt_eval_count: 30
				}
			});

			const result = await service.generateCompletion('test prompt');
			expect(result.text).toBe('Ollama response');
		});

		it('should return cached response when available', async () => {
			// First call - cache miss
			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					choices: [{ message: { content: 'API response' } }],
					usage: { prompt_tokens: 50, completion_tokens: 30 }
				}
			});

			const result1 = await aiService.generateCompletion('test prompt');
			expect(result1.fromCache).toBe(false);
			expect(mockRequestUrl).toHaveBeenCalledTimes(1);

			// Second call - cache hit
			const result2 = await aiService.generateCompletion('test prompt');
			expect(result2.fromCache).toBe(true);
			expect(result2.text).toBe('API response');
			expect(mockRequestUrl).toHaveBeenCalledTimes(1); // No additional API call
		});

		it('should bypass cache when flag is set', async () => {
			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					choices: [{ message: { content: 'Fresh response' } }],
					usage: { prompt_tokens: 50, completion_tokens: 30 }
				}
			});

			// First call
			await aiService.generateCompletion('test prompt');

			// Set bypass flag and make second call
			aiService.setBypassCache(true);
			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					choices: [{ message: { content: 'New response' } }],
					usage: { prompt_tokens: 50, completion_tokens: 30 }
				}
			});

			const result = await aiService.generateCompletion('test prompt');
			expect(result.fromCache).toBe(false);
			expect(mockRequestUrl).toHaveBeenCalledTimes(2);
		});

		it('should include system prompt when configured', async () => {
			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					choices: [{ message: { content: 'response' } }],
					usage: { prompt_tokens: 50, completion_tokens: 30 }
				}
			});

			await aiService.generateCompletion('test prompt');

			expect(mockRequestUrl).toHaveBeenCalledWith(
				expect.objectContaining({
					body: expect.stringContaining('system')
				})
			);
		});

		it('should include context when enabled', async () => {
			settings.enableContextAwareness = true;
			aiService = new AIService(settings);

			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					choices: [{ message: { content: 'response' } }],
					usage: { prompt_tokens: 50, completion_tokens: 30 }
				}
			});

			await aiService.generateCompletion('test prompt', 'note context');

			const callBody = mockRequestUrl.mock.calls[0][0].body;
			expect(callBody).toContain('Context from current note');
		});
	});

	describe('API provider handling', () => {
		it('should call OpenAI API with correct format', async () => {
			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					choices: [{ message: { content: 'response' } }],
					usage: { prompt_tokens: 50, completion_tokens: 30, total_tokens: 80 }
				}
			});

			await aiService.generateCompletion('test');

			expect(mockRequestUrl).toHaveBeenCalledWith(
				expect.objectContaining({
					url: 'https://api.openai.com/v1/chat/completions',
					method: 'POST'
				})
			);
		});

		it('should call Anthropic API with correct format', async () => {
			const anthropicSettings = { 
				...settings, 
				apiProvider: 'anthropic' as const,
				model: 'claude-3-sonnet'
			};
			const service = new AIService(anthropicSettings);

			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					content: [{ text: 'Anthropic response' }],
					usage: { output_tokens: 50 }
				}
			});

			const result = await service.generateCompletion('test');

			expect(mockRequestUrl).toHaveBeenCalledWith(
				expect.objectContaining({
					url: 'https://api.anthropic.com/v1/messages'
				})
			);
			expect(result.text).toBe('Anthropic response');
		});

		it('should call Ollama API with correct format', async () => {
			const ollamaSettings = { 
				...settings, 
				apiProvider: 'ollama' as const,
				customApiUrl: 'http://localhost:11434'
			};
			const service = new AIService(ollamaSettings);

			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					message: { content: 'Ollama response' },
					eval_count: 50,
					prompt_eval_count: 30
				}
			});

			const result = await service.generateCompletion('test');

			expect(mockRequestUrl).toHaveBeenCalledWith(
				expect.objectContaining({
					url: 'http://localhost:11434/api/chat'
				})
			);
			expect(result.text).toBe('Ollama response');
		});

		it('should call custom API with correct format', async () => {
			const customSettings = { 
				...settings, 
				apiProvider: 'custom' as const,
				customApiUrl: 'https://custom.api.com/v1/chat'
			};
			const service = new AIService(customSettings);

			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					choices: [{ message: { content: 'Custom response' } }],
					usage: { prompt_tokens: 50, completion_tokens: 30 }
				}
			});

			const result = await service.generateCompletion('test');

			expect(mockRequestUrl).toHaveBeenCalledWith(
				expect.objectContaining({
					url: 'https://custom.api.com/v1/chat'
				})
			);
			expect(result.text).toBe('Custom response');
		});

		it('should throw error for custom provider without URL', async () => {
			const customSettings = { 
				...settings, 
				apiProvider: 'custom' as const,
				customApiUrl: ''
			};
			const service = new AIService(customSettings);

			await expect(service.generateCompletion('test'))
				.rejects.toThrow(/Custom API URL not configured/);
		}, 15000);
	});

	describe('error handling', () => {
		it('should handle 401 authentication error with user-friendly message', async () => {
			mockRequestUrl.mockResolvedValue({
				status: 401,
				text: 'Unauthorized'
			});

			await expect(aiService.generateCompletion('test'))
				.rejects.toThrow(/Invalid API key/);
		});

		it('should handle 429 rate limit error with user-friendly message', async () => {
			mockRequestUrl.mockResolvedValue({
				status: 429,
				text: 'Rate limit exceeded'
			});

			await expect(aiService.generateCompletion('test'))
				.rejects.toThrow(/rate limit/i);
		});

		it('should handle 500 server error with user-friendly message', async () => {
			mockRequestUrl.mockResolvedValue({
				status: 500,
				text: 'Internal server error'
			});

			await expect(aiService.generateCompletion('test'))
				.rejects.toThrow(/API/i);
		}, 15000);
	});

	describe('cache service management', () => {
		it('should update cache settings', () => {
			const newSettings: ObsidianAgentSettings = {
				...settings,
				cacheConfig: {
					enabled: false,
					maxEntries: 50,
					maxAgeDays: 7,
					matchThreshold: 0.9
				}
			};

			aiService.updateCacheSettings(newSettings);
			const cacheSettings = aiService.getCacheService().getSettings();

			expect(cacheSettings.enabled).toBe(false);
			expect(cacheSettings.maxEntries).toBe(50);
		});
	});

	describe('request cancellation', () => {
		it('should have cancel method', () => {
			expect(aiService.cancelCurrentRequest).toBeDefined();
			expect(typeof aiService.cancelCurrentRequest).toBe('function');
		});
	});

	describe('token counting', () => {
		it('should return token counts from OpenAI response', async () => {
			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					choices: [{ message: { content: 'response' } }],
					usage: { prompt_tokens: 50, completion_tokens: 30, total_tokens: 80 }
				}
			});

			const result = await aiService.generateCompletion('test');

			expect(result.inputTokens).toBe(50);
			expect(result.outputTokens).toBe(30);
			expect(result.tokensUsed).toBe(80);
		});

		it('should return token counts from Anthropic response', async () => {
			const anthropicSettings = { 
				...settings, 
				apiProvider: 'anthropic' as const 
			};
			const service = new AIService(anthropicSettings);

			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					content: [{ text: 'response' }],
					usage: { output_tokens: 40 }
				}
			});

			const result = await service.generateCompletion('test');

			expect(result.tokensUsed).toBe(40);
		});

		it('should return token counts from Ollama response', async () => {
			const ollamaSettings = { 
				...settings, 
				apiProvider: 'ollama' as const 
			};
			const service = new AIService(ollamaSettings);

			mockRequestUrl.mockResolvedValue({
				status: 200,
				json: {
					message: { content: 'response' },
					eval_count: 45,
					prompt_eval_count: 25
				}
			});

			const result = await service.generateCompletion('test');

			expect(result.inputTokens).toBe(25);
			expect(result.outputTokens).toBe(45);
			expect(result.tokensUsed).toBe(45);
		});
	});
});
