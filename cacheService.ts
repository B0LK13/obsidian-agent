
export interface CacheEntry {
	id: string;
	promptHash: string;
	contextHash: string;
	prompt: string;
	response: string;
	model: string;
	temperature: number;
	tokensUsed: number;
	inputTokens: number;
	outputTokens: number;
	createdAt: number;
	accessedAt: number;
	accessCount: number;
}

export interface CacheSettings {
	enabled: boolean;
	maxEntries: number;
	maxAgeDays: number;
	matchThreshold: number;  // 0-1 for fuzzy matching
}

export interface CacheStats {
	totalEntries: number;
	totalHits: number;
	totalMisses: number;
	estimatedSavings: number;  // in tokens
	cacheSize: number;  // approximate bytes
}

export const DEFAULT_CACHE_SETTINGS: CacheSettings = {
	enabled: true,
	maxEntries: 100,
	maxAgeDays: 30,
	matchThreshold: 1.0  // Exact match only by default
};

export class CacheService {
	private cache: Map<string, CacheEntry> = new Map();
	private stats: CacheStats = {
		totalEntries: 0,
		totalHits: 0,
		totalMisses: 0,
		estimatedSavings: 0,
		cacheSize: 0
	};
	private settings: CacheSettings;

	constructor(settings?: CacheSettings) {
		this.settings = settings || DEFAULT_CACHE_SETTINGS;
	}

	/**
	 * Generate a hash for a string using a simple but effective algorithm
	 */
	private hashString(str: string): string {
		let hash = 0;
		for (let i = 0; i < str.length; i++) {
			const char = str.charCodeAt(i);
			hash = ((hash << 5) - hash) + char;
			hash = hash & hash; // Convert to 32bit integer
		}
		return Math.abs(hash).toString(36);
	}

	/**
	 * Generate a unique cache key from prompt, context, model, and temperature
	 */
	generateCacheKey(prompt: string, context: string, model: string, temperature: number): string {
		const promptHash = this.hashString(prompt.trim().toLowerCase());
		const contextHash = this.hashString((context || '').trim().toLowerCase());
		const tempStr = temperature.toFixed(2);
		return `${promptHash}_${contextHash}_${model}_${tempStr}`;
	}

	private generateKeyFromEntry(entry: CacheEntry): string {
		const tempStr = entry.temperature?.toFixed(2) ?? '0.00';
		if (entry.promptHash && entry.contextHash) {
			return `${entry.promptHash}_${entry.contextHash}_${entry.model}_${tempStr}`;
		}
		return this.generateCacheKey(entry.prompt, '', entry.model, entry.temperature);
	}

	/**
	 * Check if a cached response exists for the given parameters
	 */
	get(prompt: string, context: string, model: string, temperature: number): CacheEntry | null {
		if (!this.settings.enabled) {
			return null;
		}

		const key = this.generateCacheKey(prompt, context, model, temperature);
		const entry = this.cache.get(key);

		if (!entry) {
			this.stats.totalMisses++;
			return null;
		}

		// Check if entry has expired
		const maxAgeMs = this.settings.maxAgeDays * 24 * 60 * 60 * 1000;
		if (Date.now() - entry.createdAt > maxAgeMs) {
			this.cache.delete(key);
			this.stats.totalMisses++;
			return null;
		}

		// Update access stats
		entry.accessedAt = Date.now();
		entry.accessCount++;
		this.cache.set(key, entry);

		this.stats.totalHits++;
		this.stats.estimatedSavings += entry.tokensUsed;

		return entry;
	}

	/**
	 * Store a response in the cache
	 */
	set(
		prompt: string,
		context: string,
		model: string,
		temperature: number,
		response: string,
		tokensUsed: number,
		inputTokens: number = 0,
		outputTokens: number = 0
	): CacheEntry {
		if (!this.settings.enabled) {
			return this.createEntry(prompt, context, model, temperature, response, tokensUsed, inputTokens, outputTokens);
		}

		// Enforce max entries limit (LRU eviction)
		if (this.cache.size >= this.settings.maxEntries) {
			this.evictOldest();
		}

		const key = this.generateCacheKey(prompt, context, model, temperature);
		const entry = this.createEntry(prompt, context, model, temperature, response, tokensUsed, inputTokens, outputTokens);
		
		this.cache.set(key, entry);
		this.stats.totalEntries = this.cache.size;
		this.updateCacheSize();

		return entry;
	}

	/**
	 * Create a cache entry object
	 */
	private createEntry(
		prompt: string,
		context: string,
		model: string,
		temperature: number,
		response: string,
		tokensUsed: number,
		inputTokens: number,
		outputTokens: number
	): CacheEntry {
		const now = Date.now();
		return {
			id: `cache_${now}_${Math.random().toString(36).substr(2, 9)}`,
			promptHash: this.hashString(prompt.trim().toLowerCase()),
			contextHash: this.hashString((context || '').trim().toLowerCase()),
			prompt: prompt,
			response: response,
			model: model,
			temperature: temperature,
			tokensUsed: tokensUsed,
			inputTokens: inputTokens,
			outputTokens: outputTokens,
			createdAt: now,
			accessedAt: now,
			accessCount: 1
		};
	}

	/**
	 * Evict the oldest/least recently used entry
	 */
	private evictOldest(): void {
		let oldestKey: string | null = null;
		let oldestTime = Infinity;

		for (const [key, entry] of this.cache.entries()) {
			if (entry.accessedAt < oldestTime) {
				oldestTime = entry.accessedAt;
				oldestKey = key;
			}
		}

		if (oldestKey) {
			this.cache.delete(oldestKey);
		}
	}

	/**
	 * Update the approximate cache size in bytes
	 */
	private updateCacheSize(): void {
		let size = 0;
		for (const entry of this.cache.values()) {
			size += entry.prompt.length + entry.response.length + 200; // 200 bytes for metadata
		}
		this.stats.cacheSize = size;
	}

	/**
	 * Delete a specific cache entry by its ID
	 */
	deleteEntry(entryId: string): boolean {
		for (const [key, entry] of this.cache.entries()) {
			if (entry.id === entryId) {
				this.cache.delete(key);
				this.stats.totalEntries = this.cache.size;
				this.updateCacheSize();
				return true;
			}
		}
		return false;
	}

	/**
	 * Clear all cache entries
	 */
	clearCache(): void {
		this.cache.clear();
		this.stats.totalEntries = 0;
		this.stats.cacheSize = 0;
	}

	/**
	 * Reset statistics
	 */
	resetStats(): void {
		this.stats.totalHits = 0;
		this.stats.totalMisses = 0;
		this.stats.estimatedSavings = 0;
	}

	/**
	 * Get current cache statistics
	 */
	getStats(): CacheStats {
		return { ...this.stats, totalEntries: this.cache.size };
	}

	/**
	 * Get all cache entries as an array
	 */
	getAllEntries(): CacheEntry[] {
		return Array.from(this.cache.values()).sort((a, b) => b.accessedAt - a.accessedAt);
	}

	/**
	 * Get cache hit rate as a percentage
	 */
	getHitRate(): number {
		const total = this.stats.totalHits + this.stats.totalMisses;
		if (total === 0) return 0;
		return (this.stats.totalHits / total) * 100;
	}

	/**
	 * Estimate cost savings based on tokens saved
	 * Assumes average cost of $0.002 per 1000 tokens (GPT-3.5 pricing)
	 */
	getEstimatedCostSavings(costPer1000Tokens: number = 0.002): number {
		return (this.stats.estimatedSavings / 1000) * costPer1000Tokens;
	}

	/**
	 * Update cache settings
	 */
	updateSettings(settings: Partial<CacheSettings>): void {
		this.settings = { ...this.settings, ...settings };
		
		// If max entries reduced, evict excess
		while (this.cache.size > this.settings.maxEntries) {
			this.evictOldest();
		}
		
		this.stats.totalEntries = this.cache.size;
	}

	/**
	 * Get current settings
	 */
	getSettings(): CacheSettings {
		return { ...this.settings };
	}

	/**
	 * Export cache data for persistence
	 */
	exportCache(): { entries: CacheEntry[], stats: CacheStats, settings: CacheSettings } {
		return {
			entries: this.getAllEntries(),
			stats: this.getStats(),
			settings: this.getSettings()
		};
	}

	/**
	 * Import cache data from persistence
	 */
	importCache(data: { entries?: CacheEntry[], stats?: CacheStats, settings?: CacheSettings }): void {
		if (data.settings) {
			this.settings = { ...DEFAULT_CACHE_SETTINGS, ...data.settings };
		}

		if (data.stats) {
			this.stats = { ...this.stats, ...data.stats };
		}

		if (data.entries) {
			this.cache.clear();
			const now = Date.now();
			const maxAgeMs = this.settings.maxAgeDays * 24 * 60 * 60 * 1000;

			for (const entry of data.entries) {
				// Skip expired entries
				if (now - entry.createdAt > maxAgeMs) {
					continue;
				}

				const key = this.generateKeyFromEntry(entry);
				this.cache.set(key, entry);

				// Stop if we've reached max entries
				if (this.cache.size >= this.settings.maxEntries) {
					break;
				}
			}

			this.stats.totalEntries = this.cache.size;
			this.updateCacheSize();
		}
	}

	/**
	 * Check if caching is enabled
	 */
	isEnabled(): boolean {
		return this.settings.enabled;
	}

	/**
	 * Enable or disable caching
	 */
	setEnabled(enabled: boolean): void {
		this.settings.enabled = enabled;
	}

	/**
	 * Invalidate cache entries that match a specific context
	 * Useful when note content changes significantly
	 */
	invalidateByContext(contextSubstring: string): number {
		let count = 0;
		const keysToDelete: string[] = [];

		for (const [key, entry] of this.cache.entries()) {
			if (entry.prompt.includes(contextSubstring)) {
				keysToDelete.push(key);
				count++;
			}
		}

		for (const key of keysToDelete) {
			this.cache.delete(key);
		}

		this.stats.totalEntries = this.cache.size;
		this.updateCacheSize();
		return count;
	}

	/**
	 * Clean up expired entries
	 */
	cleanExpired(): number {
		const now = Date.now();
		const maxAgeMs = this.settings.maxAgeDays * 24 * 60 * 60 * 1000;
		let count = 0;
		const keysToDelete: string[] = [];

		for (const [key, entry] of this.cache.entries()) {
			if (now - entry.createdAt > maxAgeMs) {
				keysToDelete.push(key);
				count++;
			}
		}

		for (const key of keysToDelete) {
			this.cache.delete(key);
		}

		this.stats.totalEntries = this.cache.size;
		this.updateCacheSize();
		return count;
	}

	/**
	 * Format cache size for display
	 */
	getFormattedCacheSize(): string {
		const bytes = this.stats.cacheSize;
		if (bytes < 1024) return `${bytes} B`;
		if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
		return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
	}

	/**
	 * Get most frequently accessed entries (top N)
	 * Useful for prefetching optimization
	 */
	getMostFrequentEntries(limit: number = 10): CacheEntry[] {
		return Array.from(this.cache.values())
			.sort((a, b) => b.accessCount - a.accessCount)
			.slice(0, limit);
	}

	/**
	 * Get recently accessed entries (top N)
	 * Useful for LRU-based optimizations
	 */
	getRecentlyAccessedEntries(limit: number = 10): CacheEntry[] {
		return Array.from(this.cache.values())
			.sort((a, b) => b.accessedAt - a.accessedAt)
			.slice(0, limit);
	}

	/**
	 * Prefetch predictions for likely next queries
	 * Returns cache entries that might be needed soon based on access patterns
	 */
	getPrefetchCandidates(currentPrompt: string, limit: number = 5): CacheEntry[] {
		const currentWords = new Set(currentPrompt.toLowerCase().split(/\s+/));
		const candidates: Array<{ entry: CacheEntry; score: number }> = [];

		for (const entry of this.cache.values()) {
			const entryWords = new Set(entry.prompt.toLowerCase().split(/\s+/));
			
			// Calculate word overlap score
			let overlap = 0;
			for (const word of currentWords) {
				if (entryWords.has(word)) overlap++;
			}
			
			const score = (overlap / Math.max(currentWords.size, 1)) * 
				(entry.accessCount / 10); // Weight by popularity
			
			if (score > 0.3) {  // Minimum threshold
				candidates.push({ entry, score });
			}
		}

		return candidates
			.sort((a, b) => b.score - a.score)
			.slice(0, limit)
			.map(c => c.entry);
	}

	/**
	 * Optimize cache by evicting low-value entries
	 * Considers access count, recency, and size
	 */
	optimize(): number {
		const entries = Array.from(this.cache.entries());
		const now = Date.now();
		let evictedCount = 0;

		// Calculate value score for each entry
		const scored = entries.map(([key, entry]) => {
			const ageScore = 1 / (1 + (now - entry.accessedAt) / (1000 * 60 * 60 * 24)); // Decay over days
			const popularityScore = Math.min(entry.accessCount / 100, 1); // Normalize
			const sizeScore = 1 / (1 + entry.response.length / 1000); // Prefer smaller entries
			
			const value = (ageScore * 0.4) + (popularityScore * 0.4) + (sizeScore * 0.2);
			
			return { key, entry, value };
		});

		// Sort by value (ascending) and evict bottom 20% if cache is near full
		const threshold = this.settings.maxEntries * 0.8;
		if (this.cache.size > threshold) {
			scored.sort((a, b) => a.value - b.value);
			const toEvict = Math.floor((this.cache.size - threshold) * 1.2);
			
			for (let i = 0; i < toEvict && i < scored.length; i++) {
				this.cache.delete(scored[i].key);
				evictedCount++;
			}

			this.stats.totalEntries = this.cache.size;
			this.updateCacheSize();
		}

		return evictedCount;
	}

	/**
	 * Batch get multiple cache entries
	 * Returns Map of key -> entry for found items
	 */
	batchGet(queries: Array<{ prompt: string; context: string; model: string; temperature: number }>): Map<string, CacheEntry> {
		const results = new Map<string, CacheEntry>();
		
		for (const query of queries) {
			const entry = this.get(query.prompt, query.context, query.model, query.temperature);
			if (entry) {
				const key = this.generateCacheKey(query.prompt, query.context, query.model, query.temperature);
				results.set(key, entry);
			}
		}

		return results;
	}

	/**
	 * Batch set multiple cache entries
	 * More efficient than multiple individual sets
	 */
	batchSet(entries: Array<{
		prompt: string;
		context: string;
		model: string;
		temperature: number;
		response: string;
		tokensUsed: number;
		inputTokens?: number;
		outputTokens?: number;
	}>): number {
		let addedCount = 0;

		for (const entry of entries) {
			this.set(
				entry.prompt,
				entry.context,
				entry.model,
				entry.temperature,
				entry.response,
				entry.tokensUsed,
				entry.inputTokens || 0,
				entry.outputTokens || 0
			);
			addedCount++;
		}

		return addedCount;
	}

	/**
	 * Get cache performance metrics
	 * Useful for monitoring and optimization
	 */
	getPerformanceMetrics(): {
		hitRate: number;
		avgAccessCount: number;
		medianAccessCount: number;
		totalSavings: number;
		estimatedCostSavings: number;
		cacheEfficiency: number;
	} {
		const entries = Array.from(this.cache.values());
		const total = this.stats.totalHits + this.stats.totalMisses;
		
		// Calculate hit rate
		const hitRate = total > 0 ? (this.stats.totalHits / total) * 100 : 0;
		
		// Calculate average and median access count
		const accessCounts = entries.map(e => e.accessCount).sort((a, b) => a - b);
		const avgAccessCount = accessCounts.length > 0
			? accessCounts.reduce((sum, count) => sum + count, 0) / accessCounts.length
			: 0;
		const medianAccessCount = accessCounts.length > 0
			? accessCounts[Math.floor(accessCounts.length / 2)]
			: 0;

		// Calculate cache efficiency (hits per entry)
		const cacheEfficiency = entries.length > 0
			? this.stats.totalHits / entries.length
			: 0;

		return {
			hitRate,
			avgAccessCount,
			medianAccessCount,
			totalSavings: this.stats.estimatedSavings,
			estimatedCostSavings: this.getEstimatedCostSavings(),
			cacheEfficiency
		};
	}
}
