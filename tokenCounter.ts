// Simple token estimation utilities
// Note: This is an approximation. For accurate counts, use tiktoken library.

export interface TokenCount {
	systemPrompt: number;
	context: number;
	conversationHistory: number;
	currentPrompt: number;
	total: number;
	limit: number;
	percentage: number;
}

// Model context window limits
export const MODEL_LIMITS: Record<string, number> = {
	// OpenAI models
	'gpt-4': 8192,
	'gpt-4-32k': 32768,
	'gpt-4-turbo': 128000,
	'gpt-4-turbo-preview': 128000,
	'gpt-4o': 128000,
	'gpt-4o-mini': 128000,
	'gpt-3.5-turbo': 4096,
	'gpt-3.5-turbo-16k': 16384,
	// Anthropic models
	'claude-3-opus': 200000,
	'claude-3-sonnet': 200000,
	'claude-3-haiku': 200000,
	'claude-3-opus-20240229': 200000,
	'claude-3-sonnet-20240229': 200000,
	'claude-2': 100000,
	'claude-2.1': 200000,
	// Ollama/local models (common defaults)
	'llama2': 4096,
	'llama2:7b': 4096,
	'llama2:13b': 4096,
	'llama2:70b': 4096,
	'mistral': 8192,
	'mixtral': 32768,
	'codellama': 16384,
	'phi': 2048,
	'gemma': 8192,
	// Default fallback
	'default': 4096
};

/**
 * Estimate token count for a string
 * Uses a simple heuristic: ~4 characters per token for English text
 * This is an approximation - actual tokenization varies by model
 */
export function estimateTokens(text: string, provider: string = 'openai'): number {
	if (!text) return 0;
	
	// Different providers have slightly different tokenization
	let charsPerToken: number;
	switch (provider) {
		case 'anthropic':
			charsPerToken = 3.5; // Claude tends to use slightly fewer tokens
			break;
		case 'ollama':
			charsPerToken = 4; // Similar to OpenAI for most local models
			break;
		default:
			charsPerToken = 4; // OpenAI average
	}
	
	// Basic estimation
	let tokenCount = Math.ceil(text.length / charsPerToken);
	
	// Adjust for code blocks (tend to use more tokens)
	const codeBlockMatches = text.match(/```[\s\S]*?```/g);
	if (codeBlockMatches) {
		const codeLength = codeBlockMatches.reduce((sum, block) => sum + block.length, 0);
		// Code uses ~3 chars per token
		tokenCount += Math.ceil(codeLength * (1/3 - 1/charsPerToken));
	}
	
	return Math.max(1, tokenCount);
}

/**
 * Get the context window limit for a model
 */
export function getModelLimit(model: string): number {
	// Try exact match first
	if (MODEL_LIMITS[model]) {
		return MODEL_LIMITS[model];
	}
	
	// Try partial match (e.g., "gpt-4-0613" matches "gpt-4")
	for (const [key, limit] of Object.entries(MODEL_LIMITS)) {
		if (model.toLowerCase().includes(key.toLowerCase())) {
			return limit;
		}
	}
	
	// Default fallback
	return MODEL_LIMITS['default'];
}

/**
 * Calculate comprehensive token count breakdown
 */
export function calculateTokenCount(
	systemPrompt: string,
	context: string,
	conversationHistory: Array<{role: string, content: string}>,
	currentPrompt: string,
	model: string,
	provider: string
): TokenCount {
	const systemTokens = estimateTokens(systemPrompt, provider);
	const contextTokens = estimateTokens(context, provider);
	
	const historyTokens = conversationHistory.reduce((sum, msg) => {
		// Add overhead for role markers
		return sum + estimateTokens(msg.content, provider) + 4; // ~4 tokens for role/formatting
	}, 0);
	
	const promptTokens = estimateTokens(currentPrompt, provider);
	
	const total = systemTokens + contextTokens + historyTokens + promptTokens;
	const limit = getModelLimit(model);
	const percentage = Math.min(100, Math.round((total / limit) * 100));
	
	return {
		systemPrompt: systemTokens,
		context: contextTokens,
		conversationHistory: historyTokens,
		currentPrompt: promptTokens,
		total,
		limit,
		percentage
	};
}

/**
 * Get warning level based on usage percentage
 */
export function getUsageLevel(percentage: number): 'low' | 'medium' | 'high' | 'critical' {
	if (percentage >= 95) return 'critical';
	if (percentage >= 80) return 'high';
	if (percentage >= 60) return 'medium';
	return 'low';
}

/**
 * Get color for usage level
 */
export function getUsageColor(level: 'low' | 'medium' | 'high' | 'critical'): string {
	switch (level) {
		case 'critical': return 'var(--text-error)';
		case 'high': return 'var(--text-warning)';
		case 'medium': return 'var(--text-accent)';
		default: return 'var(--text-muted)';
	}
}

/**
 * Format token count for display
 */
export function formatTokenCount(count: number): string {
	if (count >= 1000) {
		return `${(count / 1000).toFixed(1)}k`;
	}
	return count.toString();
}

/**
 * Truncate text to fit within token limit
 * Keeps beginning and end, removes middle
 */
export function truncateToTokenLimit(text: string, maxTokens: number, provider: string = 'openai'): string {
	const currentTokens = estimateTokens(text, provider);
	if (currentTokens <= maxTokens) {
		return text;
	}
	
	// Calculate how much to keep
	const charsPerToken = provider === 'anthropic' ? 3.5 : 4;
	const maxChars = Math.floor(maxTokens * charsPerToken);
	
	if (maxChars <= 100) {
		return text.substring(0, maxChars);
	}
	
	// Keep 60% from beginning, 40% from end
	const beginChars = Math.floor(maxChars * 0.6);
	const endChars = maxChars - beginChars - 20; // 20 chars for separator
	
	const beginning = text.substring(0, beginChars);
	const end = text.substring(text.length - endChars);
	
	return `${beginning}\n\n[... content truncated ...]\n\n${end}`;
}
