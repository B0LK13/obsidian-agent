import { ObsidianAgentSettings } from './settings';
import { requestUrl, RequestUrlResponse, Notice } from 'obsidian';

export class AIService {
	private settings: ObsidianAgentSettings;
	private timeoutMs: number = 30000;

	constructor(settings: ObsidianAgentSettings) {
		this.settings = settings;
	}

	async generateCompletion(prompt: string, context?: string): Promise<string> {
		if (!this.settings.apiKey) {
			throw new Error('API key not configured. Please set it in settings.');
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

		messages.push({
			role: 'user',
			content: prompt
		});

		try {
			const response = await this.callAPIWithTimeout(messages);
			return response;
		} catch (error: any) {
			console.error('AI Service Error:', error);
			throw this.handleError(error);
		}
	}

	private handleError(error: any): Error {
		if (error.name === 'AbortError' || error.message?.includes('timeout')) {
			return new Error('Request timed out. Please check your internet connection and try again.');
		}

		if (error.message?.includes('401') || error.message?.includes('authentication')) {
			return new Error('Invalid API key. Please check your API key in settings.');
		}

		if (error.message?.includes('429') || error.message?.includes('rate limit') || error.message?.includes('API limit')) {
			return new Error(
				'API rate limit reached. Please wait a moment and try again. ' +
				'Tip: Consider using a local LLM like Ollama for unlimited usage.'
			);
		}

		if (error.message?.includes('500') || error.message?.includes('502') || error.message?.includes('503')) {
			return new Error(
				'API service is temporarily unavailable. Please try again later. ' +
				'Tip: Check https://status.openai.com or provider status page.'
			);
		}

		if (error.message?.includes('404') || error.message?.includes('model not found')) {
			return new Error('Model not found. Please check the model name in settings.');
		}

		if (error.message?.includes('quota') || error.message?.includes('billing')) {
			return new Error(
				'API quota exceeded or billing issue. Please check your provider dashboard. ' +
				'Tip: Consider using a local LLM like Ollama to avoid API costs.'
			);
		}

		return new Error(`Failed to generate completion: ${error.message}`);
	}

	private async callAPIWithTimeout(messages: Array<{role: string, content: string}>): Promise<string> {
		return Promise.race([
			this.callAPI(messages),
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

		if (response.status !== 200) {
			const errorText = response.text || '';
			throw new Error(`API request failed with status ${response.status}: ${errorText}`);
		}

		if (this.settings.apiProvider === 'anthropic') {
			return response.json.content[0].text;
		} else {
			return response.json.choices[0].message.content;
		}
	}
}
