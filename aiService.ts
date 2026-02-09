import { ObsidianAgentSettings } from './settings';
import { requestUrl, RequestUrlResponse } from 'obsidian';
import { CacheService, CacheEntry } from './cacheService';
import { ValidationError, APIError, NetworkError, ConfigurationError } from './src/errors';
import { Validators } from './src/validators';
import { logger } from './src/logger';

export interface CompletionResult {
	text: string;
	tokensUsed?: number;
	inputTokens?: number;
	outputTokens?: number;
	fromCache?: boolean;
	cacheEntry?: CacheEntry;
}

export interface StreamChunk {
	content: string;
	done: boolean;
	tokensUsed?: number;
	inputTokens?: number;
	outputTokens?: number;
}

export type StreamCallback = (chunk: StreamChunk) => void;
export type StreamProgressCallback = (progress: string) => void;

export interface CompletionOptions {
	prompt: string;
	context?: string;
	imageData?: string;
	stream?: boolean;
	onChunk?: StreamCallback;
	onProgress?: StreamProgressCallback;
}

export class AIService {
	private settings: ObsidianAgentSettings;
	private timeoutMs: number = 120000; // 120 seconds for local models
	private maxRetries: number = 1; // Reduce retries for faster feedback
	private initialRetryDelayMs: number = 1000;
	private retryDelayMultiplier: number = 2;
	private currentAbortController: AbortController | null = null;
	private cacheService: CacheService;
	private bypassCache: boolean = false;

	constructor(settings: ObsidianAgentSettings) {
		// Validate settings
		if (!settings) {
			throw new ValidationError('Settings are required');
		}
		
		this.settings = settings;
		this.cacheService = new CacheService(settings.cacheConfig);
		
		// Import persisted cache data if available (with safety checks)
		if (settings.cacheData?.entries && Array.isArray(settings.cacheData.entries) && settings.cacheData.entries.length > 0) {
			try {
				this.cacheService.importCache({
					entries: settings.cacheData.entries,
					stats: settings.cacheData.stats || { hits: 0, misses: 0, evictions: 0 },
					settings: settings.cacheConfig
				});
			} catch (error) {
				logger.error('Failed to import cache data', error as Error, { component: 'AIService' });
				// Continue without cached data
			}
		}
	}

	/**
	 * Get the cache service instance
	 */
	getCacheService(): CacheService {
		return this.cacheService;
	}

	/**
	 * Set bypass cache flag for next request
	 */
	setBypassCache(bypass: boolean): void {
		this.bypassCache = bypass;
	}

	/**
	 * Update cache settings
	 */
	updateCacheSettings(settings: ObsidianAgentSettings): void {
		this.cacheService.updateSettings(settings.cacheConfig);
	}

	cancelCurrentRequest(): void {
		if (this.currentAbortController) {
			this.currentAbortController.abort();
			this.currentAbortController = null;
		}
	}

	async testConnection(): Promise<{ success: boolean; message: string; responseTime?: number }> {
		// Validate API key for non-Ollama providers
		if (this.settings.apiProvider !== 'ollama' && !this.settings.apiKey) {
			return {
				success: false,
				message: 'API key not configured'
			};
		}

		const startTime = Date.now();
		
		try {
			const result = await this.callAPIWithRetry([{
				role: 'user',
				content: 'Test connection. Please respond with "OK" only.'
			}], undefined, 1);
			
			const responseTime = Date.now() - startTime;
			
			// Validate result
			if (!result || typeof result.text !== 'string') {
				return {
					success: false,
					message: 'Connection succeeded but received invalid response'
				};
			}
			
			if (result.text.trim().toLowerCase() === 'ok' || result.text.length > 0) {
				return {
					success: true,
					message: `Connection successful! Response time: ${responseTime}ms`,
					responseTime
				};
			} else {
				return {
					success: false,
					message: 'Connection succeeded but returned unexpected response'
				};
			}
		} catch (error: any) {
			const responseTime = Date.now() - startTime;
			return {
				success: false,
				message: this.getErrorMessage(error),
				responseTime
			};
		}
	}

	async generateCompletion(options: string | CompletionOptions): Promise<CompletionResult> {
        // Handle both simple string prompt and options object
        const opt: CompletionOptions = typeof options === 'string' ? { prompt: options } : options;
        const { prompt, context, imageData, stream, onChunk, onProgress } = opt;

		// Input validation
		try {
			Validators.notEmpty(prompt, 'prompt');
		} catch (error) {
			throw new ValidationError('Prompt cannot be empty');
		}

		// Validate API key (skip for Ollama and localhost providers)		
		const isLocalOllama = 
			this.settings.apiProvider === 'ollama' || 
			this.settings.customApiUrl?.includes('localhost') ||
			this.settings.customApiUrl?.includes('127.0.0.1');
			
		if (!isLocalOllama && !this.settings.apiKey) {
			throw new ConfigurationError('API key not configured. Please set it in settings.', 'apiKey');
		}

		// Validate model is set
		if (!this.settings.model || this.settings.model.trim().length === 0) {
			throw new ConfigurationError('Model not configured. Please select a model in settings.', 'model');
		}

		// Check cache first (only for non-streaming requests)
		if (!stream && !this.bypassCache && this.cacheService.isEnabled()) {
			try {
				const cachedEntry = this.cacheService.get(
					prompt,
					context || '',
					this.settings.model,
					this.settings.temperature
				);

				if (cachedEntry) {
					return {
						text: cachedEntry.response,
						tokensUsed: cachedEntry.tokensUsed,
						inputTokens: cachedEntry.inputTokens,
						outputTokens: cachedEntry.outputTokens,
						fromCache: true,
						cacheEntry: cachedEntry
					};
				}
			} catch (error) {
				logger.warn('Cache lookup failed, continuing with API call', { component: 'AIService', operation: 'cache-lookup' });
			}
		}

		// Reset bypass flag after checking
		this.bypassCache = false;

		const messages = [];
		
		if (this.settings.systemPrompt && this.settings.systemPrompt.trim().length > 0) {
			messages.push({
				role: 'system',
				content: this.settings.systemPrompt
			});
		}

		if (context && this.settings.enableContextAwareness && context.trim().length > 0) {
			messages.push({
				role: 'system',
				content: `Context from current note:\n${context}`
			});
		}

		messages.push({
			role: 'user',
			content: prompt
		});

		try {
			let result: CompletionResult;
			
			if (stream && onChunk) {
				result = await this.streamAPI(messages, imageData, onChunk, onProgress);
			} else {
				result = await this.callAPIWithRetry(messages, imageData);
			}

			// Validate result
			if (!result || typeof result.text !== 'string') {
				throw new APIError('Received invalid response from API');
			}

			// Store in cache (for non-streaming or after streaming completes)
			if (this.cacheService.isEnabled() && result.text && result.text.length > 0) {
				try {
					const cacheEntry = this.cacheService.set(
						prompt,
						context || '',
						this.settings.model,
						this.settings.temperature,
						result.text,
						result.tokensUsed || 0,
						result.inputTokens || 0,
						result.outputTokens || 0
					);
					result.cacheEntry = cacheEntry;
				} catch (error) {
					logger.warn('Failed to cache result', { component: 'AIService', operation: 'cache-write' });
					// Continue without caching
				}
			}

			result.fromCache = false;
			return result;
		} catch (error: any) {
			logger.error('AI Service Error', error, { component: 'AIService', operation: 'generate' });
			
			// Re-throw known error types
			if (error instanceof ValidationError || 
				error instanceof APIError || 
				error instanceof ConfigurationError ||
				error instanceof NetworkError) {
				throw error;
			}
			
			// Wrap unknown errors
			throw new APIError(this.getErrorMessage(error));
		}
	}

	private getErrorMessage(error: any): string {
		if (error.name === 'AbortError' || error.message?.includes('timeout')) {
			return 'Request timed out. Please check your internet connection and try again.';
		}

		if (error.message?.includes('401') || error.message?.includes('authentication')) {
			return 'Invalid API key. Please check your API key in settings.';
		}

		if (error.message?.includes('429') || error.message?.includes('rate limit') || error.message?.includes('API limit')) {
			return 'API rate limit reached. Please wait a moment and try again. Tip: Consider using a local LLM like Ollama for unlimited usage.';
		}

		if (error.message?.includes('500') || error.message?.includes('502') || error.message?.includes('503')) {
			return 'API service is temporarily unavailable. Please try again later. Tip: Check https://status.openai.com or provider status page.';
		}

		if (error.message?.includes('404') || error.message?.includes('model not found')) {
			return 'Model not found. Please check the model name in settings.';
		}

		if (error.message?.includes('quota') || error.message?.includes('billing')) {
			return 'API quota exceeded or billing issue. Please check your provider dashboard. Tip: Consider using a local LLM like Ollama to avoid API costs.';
		}

		return `Failed to generate completion: ${error.message}`;
	}

	private async callAPIWithRetry(messages: Array<{role: string, content: any}>, imageData?: string, maxRetriesOverride?: number): Promise<CompletionResult> {
		const maxRetries = maxRetriesOverride ?? this.maxRetries;
		let lastError: any;

		for (let attempt = 0; attempt <= maxRetries; attempt++) {
			try {
				if (attempt > 0) {
					const delay = this.getRetryDelay(attempt);
					await this.sleep(delay);
				}

				return await this.callAPIWithTimeout(messages, imageData);
			} catch (error: any) {
				lastError = error;

				if (this.shouldNotRetry(error)) {
					throw error;
				}

				if (attempt < maxRetries) {
					const delay = this.getRetryDelay(attempt + 1);
					console.log(`Retry attempt ${attempt + 1}/${maxRetries} after ${delay}ms`);
				}
			}
		}

		throw lastError;
	}

	private shouldNotRetry(error: any): boolean {
		const message = error.message?.toLowerCase() || '';
		
		if (message.includes('401') || message.includes('authentication')) {
			return true;
		}
		
		if (message.includes('404') || message.includes('model not found')) {
			return true;
		}
		
		if (message.includes('429') || message.includes('rate limit') || message.includes('api limit')) {
			return true;
		}
		
		if (message.includes('quota') || message.includes('billing')) {
			return true;
		}

		return false;
	}

	private getRetryDelay(attempt: number): number {
		return this.initialRetryDelayMs * Math.pow(this.retryDelayMultiplier, attempt - 1);
	}

	private async streamAPI(messages: Array<{role: string, content: any}>, imageData?: string, onChunk?: StreamCallback, onProgress?: StreamProgressCallback): Promise<CompletionResult> {
		let url: string;
		let headers: Record<string, string>;
		let body: any;

		switch (this.settings.apiProvider) {
			case 'openai': {
				url = 'https://api.openai.com/v1/chat/completions';
				headers = {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${this.settings.apiKey}`
				};

                // Handle vision if imageData provided
                const finalMessages = [...messages];
                if (imageData) {
                    const lastUserMsgIndex = finalMessages.map(m => m.role).lastIndexOf('user');
                    if (lastUserMsgIndex !== -1) {
                        const originalContent = finalMessages[lastUserMsgIndex].content;
                        finalMessages[lastUserMsgIndex].content = [
                            { type: "text", text: originalContent },
                            {
                                type: "image_url",
                                image_url: {
                                    url: imageData.startsWith('data:') ? imageData : `data:image/jpeg;base64,${imageData}`
                                }
                            }
                        ];
                    }
                }

				body = {
					model: imageData ? (this.settings.model.includes('vision') ? this.settings.model : 'gpt-4o') : this.settings.model,
					messages: finalMessages,
					temperature: this.settings.temperature,
					max_tokens: this.settings.maxTokens,
					stream: true
				};
				break;
			}

			case 'anthropic': {
				url = 'https://api.anthropic.com/v1/messages';
				headers = {
					'Content-Type': 'application/json',
					'x-api-key': this.settings.apiKey,
					'anthropic-version': '2023-06-01'
				};
				const systemMsg = messages.find(m => m.role === 'system');
				const userMessages = messages.filter(m => m.role !== 'system');
				body = {
					model: this.settings.model,
					max_tokens: this.settings.maxTokens,
					temperature: this.settings.temperature,
					system: systemMsg?.content,
					messages: userMessages,
					stream: true
				};
				break;
			}

			case 'ollama': {
				const ollamaStreamUrl = this.settings.customApiUrl || 'http://localhost:11434';
				url = `${ollamaStreamUrl}/api/chat`;
				headers = {
					'Content-Type': 'application/json'
				};
				body = {
					model: this.settings.model,
					messages: messages,
					options: {
						temperature: this.settings.temperature,
						num_predict: this.settings.maxTokens
					},
					stream: true
				};
				break;
			}

			case 'custom': {
				if (!this.settings.customApiUrl) {
					throw new Error('Custom API URL not configured');
				}
				url = this.settings.customApiUrl;
				headers = {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${this.settings.apiKey}`
				};
				body = {
					model: this.settings.model,
					messages: messages,
					temperature: this.settings.temperature,
					max_tokens: this.settings.maxTokens,
					stream: true
				};
				break;
			}

			default:
				throw new Error(`Unknown API provider: ${this.settings.apiProvider}`);
		}

		let fullText = '';
		let tokensUsed = 0;
		let inputTokens = 0;
		let outputTokens = 0;

		const response = await requestUrl({
			url: url,
			method: 'POST',
			headers: headers,
			body: JSON.stringify(body),
			throw: false
		});

		if (response.status !== 200) {
			const errorText = response.text || '';
			throw new Error(`API request failed with status ${response.status}: ${errorText}`);
		}

		const responseText = response.text || '';
		if (this.settings.apiProvider === 'ollama') {
			const chunks = responseText.split('\n').filter(Boolean);
			for (const chunk of chunks) {
				try {
					const json = JSON.parse(chunk);
					if (json.message?.content) {
						fullText += json.message.content;
						if (onProgress) {
							onProgress(fullText);
						}
					}
					if (json.eval_count) {
						outputTokens = json.eval_count;
					}
					if (json.prompt_eval_count) {
						inputTokens = json.prompt_eval_count;
					}
					if (json.done) {
						tokensUsed = (json.eval_count || 0) + (json.prompt_eval_count || 0);
						if (onChunk) {
							onChunk({
								content: fullText,
								done: true,
								tokensUsed,
								inputTokens,
								outputTokens
							});
						}
					}
				} catch (err) {
					console.error('Failed to parse Ollama chunk:', chunk);
				}
			}
		} else {
			const lines = responseText.split('\n');
			for (const line of lines) {
				if (line.startsWith('data: ')) {
					const data = line.slice(6);
					if (data.trim() === '[DONE]') {
						if (onChunk) {
							onChunk({
								content: fullText,
								done: true,
								tokensUsed: tokensUsed,
								inputTokens,
								outputTokens
							});
						}
						break;
					}

					try {
						const json = JSON.parse(data);
						let content = '';

						if (json.choices?.[0]?.delta?.content) {
							content = json.choices[0].delta.content || '';
						}

						if (json.usage) {
							tokensUsed = (json.usage.total_tokens || 0);
							if (json.usage.prompt_tokens) {
								inputTokens = json.usage.prompt_tokens;
							}
							if (json.usage.completion_tokens) {
								outputTokens = json.usage.completion_tokens;
							}
						}

						if (content) {
							fullText += content;
							if (onProgress) {
								onProgress(fullText);
							}
						}
					} catch (e) {
						console.error('Failed to parse SSE data:', data);
					}
				}
			}
		}

		return {
			text: fullText,
			tokensUsed: tokensUsed || 0,
			inputTokens,
			outputTokens
		};
	}

	private sleep(ms: number): Promise<void> {
		return new Promise(resolve => setTimeout(resolve, ms));
	}

	private async callAPIWithTimeout(messages: Array<{role: string, content: any}>, imageData?: string): Promise<CompletionResult> {
		return Promise.race([
			this.callAPI(messages, imageData),
			this.timeoutPromise(this.timeoutMs)
		]);
	}

	private timeoutPromise(ms: number): Promise<never> {
		return new Promise((_, reject) => {
			setTimeout(() => {
				const error = new Error(`Request timeout after ${ms}ms`);
				error.name = 'AbortError';
				reject(error);
			}, ms);
		});
	}

	private async callAPI(messages: Array<{role: string, content: any}>, imageData?: string): Promise<CompletionResult> {
		let url: string;
		let headers: Record<string, string>;
		let body: any;

		switch (this.settings.apiProvider) {
			case 'openai': {
				url = 'https://api.openai.com/v1/chat/completions';
				headers = {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${this.settings.apiKey}`
				};

                // Handle vision if imageData provided
                const finalMessages = [...messages];
                if (imageData) {
                    const lastUserMsgIndex = finalMessages.map(m => m.role).lastIndexOf('user');
                    if (lastUserMsgIndex !== -1) {
                        const originalContent = finalMessages[lastUserMsgIndex].content;
                        finalMessages[lastUserMsgIndex].content = [
                            { type: "text", text: originalContent },
                            {
                                type: "image_url",
                                image_url: {
                                    url: imageData.startsWith('data:') ? imageData : `data:image/jpeg;base64,${imageData}`
                                }
                            }
                        ];
                    }
                }

				body = {
					model: imageData ? (this.settings.model.includes('vision') ? this.settings.model : 'gpt-4o') : this.settings.model,
					messages: finalMessages,
					temperature: this.settings.temperature,
					max_tokens: this.settings.maxTokens
				};
				break;
			}

			case 'anthropic': {
				url = 'https://api.anthropic.com/v1/messages';
				headers = {
					'Content-Type': 'application/json',
					'x-api-key': this.settings.apiKey,
					'anthropic-version': '2023-06-01'
				};
				const systemMsg = messages.find(m => m.role === 'system');
				const userMessages = messages.filter(m => m.role !== 'system');
				body = {
					model: this.settings.model,
					max_tokens: this.settings.maxTokens,
					temperature: this.settings.temperature,
					system: systemMsg?.content,
					messages: userMessages
				};
				break;
			}

			case 'ollama': {
				const ollamaUrl = this.settings.customApiUrl || 'http://localhost:11434';
				url = `${ollamaUrl}/api/chat`;
				headers = {
					'Content-Type': 'application/json'
				};
				body = {
					model: this.settings.model,
					messages: messages,
					options: {
						temperature: this.settings.temperature,
						num_predict: this.settings.maxTokens
					},
					stream: false
				};
				break;
			}

			case 'custom': {
				if (!this.settings.customApiUrl) {
					throw new Error('Custom API URL not configured');
				}
				url = this.settings.customApiUrl;
				headers = {
					'Content-Type': 'application/json',
					'Authorization': `Bearer ${this.settings.apiKey}`
				};
				body = {
					model: this.settings.model,
					messages: messages,
					temperature: this.settings.temperature,
					max_tokens: this.settings.maxTokens
				};
				break;
			}

			default:
				throw new Error(`Unknown API provider: ${this.settings.apiProvider}`);
		}

		const response: RequestUrlResponse = await requestUrl({
			url: url,
			method: 'POST',
			headers: headers,
			body: JSON.stringify(body),
			throw: false
		});

		if (response.status !== 200) {
			const errorText = response.text || '';
			throw new Error(`API request failed with status ${response.status}: ${errorText}`);
		}

		const result: CompletionResult = { text: '' };

		if (this.settings.apiProvider === 'anthropic') {
			result.text = response.json.content[0].text;
			result.tokensUsed = response.json.usage?.output_tokens;
		} else if (this.settings.apiProvider === 'ollama') {
			result.text = response.json.message?.content || '';
			result.tokensUsed = response.json.eval_count || 0;
			result.inputTokens = response.json.prompt_eval_count || 0;
			result.outputTokens = response.json.eval_count || 0;
		} else {
			result.text = response.json.choices[0].message.content;
			result.inputTokens = response.json.usage?.prompt_tokens;
			result.outputTokens = response.json.usage?.completion_tokens;
			result.tokensUsed = (response.json.usage?.prompt_tokens || 0) + (response.json.usage?.completion_tokens || 0);
		}

		return result;
	}
}
