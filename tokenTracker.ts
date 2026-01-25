export interface TokenUsage {
	promptTokens: number;
	completionTokens: number;
	totalTokens: number;
	estimatedCost: number;
	timestamp: number;
}

export class TokenTracker {
	private usage: TokenUsage[];
	private costPerToken: Map<string, { prompt: number; completion: number }>;
	private totalRequests: number;
	private cacheHits: number;

	constructor() {
		this.usage = [];
		this.totalRequests = 0;
		this.cacheHits = 0;
		this.costPerToken = new Map([
			['gpt-4', { prompt: 0.00003, completion: 0.00006 }],
			['gpt-4-turbo', { prompt: 0.00001, completion: 0.00003 }],
			['gpt-3.5-turbo', { prompt: 0.0000015, completion: 0.000002 }],
			['claude-3-opus', { prompt: 0.000015, completion: 0.000075 }],
			['claude-3-sonnet', { prompt: 0.000003, completion: 0.000015 }],
			['claude-3-haiku', { prompt: 0.00000025, completion: 0.00000125 }]
		]);
	}

	addUsage(usage: TokenUsage): void {
		this.usage.push(usage);
	}

	estimateTokens(text: string): number {
		// Improved estimation: ~3.5-4 characters per token for English
		// Adjust for different languages and special characters
		const baseEstimate = Math.ceil(text.length / 3.7);
		
		// Account for special tokens, whitespace, and punctuation
		const specialChars = (text.match(/[^\w\s]/g) || []).length;
		const whitespace = (text.match(/\s+/g) || []).length;
		
		return baseEstimate + Math.ceil(specialChars * 0.5) + Math.ceil(whitespace * 0.1);
	}

	calculateCost(model: string, promptTokens: number, completionTokens: number): number {
		const costs = this.costPerToken.get(model) || { prompt: 0.00001, completion: 0.00003 };
		return (promptTokens * costs.prompt) + (completionTokens * costs.completion);
	}

	trackRequest(model: string, prompt: string, completion: string): TokenUsage {
		const promptTokens = this.estimateTokens(prompt);
		const completionTokens = this.estimateTokens(completion);
		const totalTokens = promptTokens + completionTokens;
		const estimatedCost = this.calculateCost(model, promptTokens, completionTokens);

		const usage: TokenUsage = {
			promptTokens,
			completionTokens,
			totalTokens,
			estimatedCost,
			timestamp: Date.now()
		};

		this.addUsage(usage);
		return usage;
	}

	getTotalUsage(): { tokens: number; cost: number } {
		const tokens = this.usage.reduce((sum, u) => sum + u.totalTokens, 0);
		const cost = this.usage.reduce((sum, u) => sum + u.estimatedCost, 0);
		return { tokens, cost };
	}

	getUsageByPeriod(hours: number): { tokens: number; cost: number } {
		const cutoff = Date.now() - (hours * 60 * 60 * 1000);
		const recentUsage = this.usage.filter(u => u.timestamp >= cutoff);
		const tokens = recentUsage.reduce((sum, u) => sum + u.totalTokens, 0);
		const cost = recentUsage.reduce((sum, u) => sum + u.estimatedCost, 0);
		return { tokens, cost };
	}

	clearHistory(): void {
		this.usage = [];
	}

	exportUsage(): string {
		return JSON.stringify({
			usage: this.usage,
			summary: this.getTotalUsage()
		}, null, 2);
	}

	getUsageStats(): {
		total: { tokens: number; cost: number };
		last24h: { tokens: number; cost: number };
		last7d: { tokens: number; cost: number };
		requestCount: number;
	} {
		return {
			total: this.getTotalUsage(),
			last24h: this.getUsageByPeriod(24),
			last7d: this.getUsageByPeriod(24 * 7),
			requestCount: this.usage.length
		};
	}
}
