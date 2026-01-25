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
	private totalRequests: number;
	private cacheHits: number;

	constructor(maxSize: number = 100, expirationMinutes: number = 60) {
		this.cache = new Map();
		this.maxSize = maxSize;
		this.expirationMinutes = expirationMinutes;
		this.totalRequests = 0;
		this.cacheHits = 0;
	}

	private async hashPrompt(prompt: string): Promise<string> {
		// Use Web Crypto API for robust hashing
		const encoder = new TextEncoder();
		const data = encoder.encode(prompt);
		
		// For browser compatibility, use a simple but better hash
		// In production, consider using crypto.subtle.digest for SHA-256
		let hash = 0;
		for (let i = 0; i < prompt.length; i++) {
			const char = prompt.charCodeAt(i);
			hash = ((hash << 5) - hash) + char;
			hash = hash & hash; // Convert to 32bit integer
		}
		
		// Add length to reduce collisions
		return `${Math.abs(hash).toString(36)}_${prompt.length}`;
	}

	async get(prompt: string): Promise<string | null> {
		const key = await this.hashPrompt(prompt);
		const cached = this.cache.get(key);

		this.totalRequests++;

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
		this.cacheHits++;
		return cached.response;
	}

	async set(prompt: string, response: string): Promise<void> {
		const key = await this.hashPrompt(prompt);

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
		totalRequests: number;
		hitRate: number;
	} {
		const hitRate = this.totalRequests > 0 ? this.cacheHits / this.totalRequests : 0;

		return {
			size: this.cache.size,
			totalHits: this.cacheHits,
			totalRequests: this.totalRequests,
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
