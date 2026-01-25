import { ObsidianAgentSettings, ConversationMessage } from './settings';
import { requestUrl, RequestUrlResponse } from 'obsidian';
import { ConversationHistory } from './conversationHistory';
import { TokenTracker } from './tokenTracker';
import { ResponseCache } from './responseCache';

export class AIService {
	private settings: ObsidianAgentSettings;
	private conversationHistory: ConversationHistory;
	private tokenTracker: TokenTracker;
	private responseCache: ResponseCache;

	constructor(settings: ObsidianAgentSettings) {
		this.settings = settings;
		this.conversationHistory = new ConversationHistory(settings.maxConversationLength);
		this.tokenTracker = new TokenTracker();
		this.responseCache = new ResponseCache(settings.maxCachedResponses, settings.cacheExpiration);
	}

	getConversationHistory(): ConversationHistory {
		return this.conversationHistory;
	}

	getTokenTracker(): TokenTracker {
		return this.tokenTracker;
	}

	getResponseCache(): ResponseCache {
		return this.responseCache;
	}

	async generateCompletion(prompt: string, context?: string, conversationId?: string): Promise<string> {
		if (!this.settings.apiKey) {
			throw new Error('API key not configured. Please set it in settings.');
		}

		// Check cache if enabled
		if (this.settings.enableCaching && !conversationId) {
			const cached = this.responseCache.get(prompt);
			if (cached) {
				return cached;
			}
		}

		const messages = [];
		
		if (this.settings.systemPrompt) {
			messages.push({
				role: 'system',
				content: this.settings.systemPrompt
			});
		}

		if (context && this.settings.enableContextAwareness) {
			messages.push({
				role: 'system',
				content: `Context from current note:\n${context}`
			});
		}

		// Add conversation history if enabled
		if (this.settings.enableConversationHistory && conversationId) {
			const history = this.conversationHistory.getHistory(conversationId);
			messages.push(...history.map(m => ({ role: m.role, content: m.content })));
		}

		messages.push({
			role: 'user',
			content: prompt
		});

		try {
			const response = await this.callAPI(messages);
			
			// Track token usage
			if (this.settings.enableTokenTracking) {
				const fullPrompt = messages.map(m => m.content).join('\n');
				this.tokenTracker.trackRequest(this.settings.model, fullPrompt, response);
			}

			// Save to conversation history
			if (this.settings.enableConversationHistory && conversationId) {
				this.conversationHistory.addMessage(conversationId, {
					role: 'user',
					content: prompt,
					timestamp: Date.now()
				});
				this.conversationHistory.addMessage(conversationId, {
					role: 'assistant',
					content: response,
					timestamp: Date.now()
				});
			}

			// Cache response
			if (this.settings.enableCaching && !conversationId) {
				this.responseCache.set(prompt, response);
			}

			return response;
		} catch (error) {
			console.error('AI Service Error:', error);
			throw new Error(`Failed to generate completion: ${error.message}`);
		}
	}

	private async callAPI(messages: Array<{role: string, content: string}>): Promise<string> {
		let url: string;
		let headers: Record<string, string>;
		let body: any;

		switch (this.settings.apiProvider) {
			case 'openai':
				url = 'https://api.openai.com/v1/chat/completions';
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

			case 'anthropic':
				url = 'https://api.anthropic.com/v1/messages';
				headers = {
					'Content-Type': 'application/json',
					'x-api-key': this.settings.apiKey,
					'anthropic-version': '2023-06-01'
				};
				// Convert messages format for Anthropic (only user messages, system handled separately)
				const systemMsg = messages.find(m => m.role === 'system');
				const userMessages = messages.filter(m => m.role === 'user');
				body = {
					model: this.settings.model,
					max_tokens: this.settings.maxTokens,
					temperature: this.settings.temperature,
					system: systemMsg?.content,
					messages: userMessages
				};
				break;

			case 'custom':
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

		if (response.status < 200 || response.status >= 300) {
			throw new Error(`API request failed with status ${response.status}: ${response.text}`);
		}

		// Parse response based on provider with validation
		try {
			if (this.settings.apiProvider === 'anthropic') {
				if (!response.json.content || !Array.isArray(response.json.content) || response.json.content.length === 0) {
					throw new Error('Invalid response format: missing or empty content array');
				}
				return response.json.content[0].text;
			} else {
				if (!response.json.choices || !Array.isArray(response.json.choices) || response.json.choices.length === 0) {
					throw new Error('Invalid response format: missing or empty choices array');
				}
				if (!response.json.choices[0].message || !response.json.choices[0].message.content) {
					throw new Error('Invalid response format: missing message content');
				}
				return response.json.choices[0].message.content;
			}
		} catch (error) {
			throw new Error(`Failed to parse API response: ${error.message}`);
		}
	}
}
