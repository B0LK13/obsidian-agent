export interface CachedResponse {
	prompt: string;
	response: string;
	timestamp: number;
	hits: number;
}

export class ResponseCache {
	private cache: Map<string, CachedResponse>;
	private maxSize: number;
	private expirationMinutes: number;

	constructor(maxSize: number = 100, expirationMinutes: number = 60) {
		this.cache = new Map();
		this.maxSize = maxSize;
		this.expirationMinutes = expirationMinutes;
	}

	private hashPrompt(prompt: string): string {
		// Simple hash function for prompt (in production, use crypto.subtle.digest)
		let hash = 0;
		for (let i = 0; i < prompt.length; i++) {
			const char = prompt.charCodeAt(i);
			hash = ((hash << 5) - hash) + char;
			hash = hash & hash;
		}
		return hash.toString(36);
	}

	get(prompt: string): string | null {
		const key = this.hashPrompt(prompt);
		const cached = this.cache.get(key);

		if (!cached) {
			return null;
		}

		// Check if expired
		const age = Date.now() - cached.timestamp;
		const expirationMs = this.expirationMinutes * 60 * 1000;

		if (age > expirationMs) {
			this.cache.delete(key);
			return null;
		}

		// Increment hit counter
		cached.hits++;
		return cached.response;
	}

	set(prompt: string, response: string): void {
		const key = this.hashPrompt(prompt);

		// If cache is full, remove least recently used (oldest)
		if (this.cache.size >= this.maxSize && !this.cache.has(key)) {
			const oldestKey = this.findOldestEntry();
			if (oldestKey) {
				this.cache.delete(oldestKey);
			}
		}

		this.cache.set(key, {
			prompt,
			response,
			timestamp: Date.now(),
			hits: 0
		});
	}

	private findOldestEntry(): string | null {
		let oldestKey: string | null = null;
		let oldestTime = Infinity;

		for (const [key, value] of this.cache.entries()) {
			if (value.timestamp < oldestTime) {
				oldestTime = value.timestamp;
				oldestKey = key;
			}
		}

		return oldestKey;
	}

	clear(): void {
		this.cache.clear();
	}

	getStats(): {
		size: number;
		totalHits: number;
		hitRate: number;
	} {
		const totalHits = Array.from(this.cache.values()).reduce((sum, c) => sum + c.hits, 0);
		const totalRequests = this.cache.size + totalHits;
		const hitRate = totalRequests > 0 ? totalHits / totalRequests : 0;

		return {
			size: this.cache.size,
			totalHits,
			hitRate
		};
	}

	cleanExpired(): number {
		const expirationMs = this.expirationMinutes * 60 * 1000;
		const now = Date.now();
		let removed = 0;

		for (const [key, value] of this.cache.entries()) {
			if (now - value.timestamp > expirationMs) {
				this.cache.delete(key);
				removed++;
			}
		}

		return removed;
	}
}
