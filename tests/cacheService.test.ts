import { describe, it, expect, beforeEach } from 'vitest';
import { CacheService, DEFAULT_CACHE_SETTINGS, CacheEntry } from '../cacheService';

describe('CacheService', () => {
	let cacheService: CacheService;

	beforeEach(() => {
		cacheService = new CacheService();
	});

	describe('initialization', () => {
		it('should initialize with default settings', () => {
			const settings = cacheService.getSettings();
			expect(settings.enabled).toBe(true);
			expect(settings.maxEntries).toBe(100);
			expect(settings.maxAgeDays).toBe(30);
			expect(settings.matchThreshold).toBe(1.0);
		});

		it('should initialize with custom settings', () => {
			const customSettings = {
				enabled: false,
				maxEntries: 50,
				maxAgeDays: 7,
				matchThreshold: 0.8
			};
			const service = new CacheService(customSettings);
			const settings = service.getSettings();
			expect(settings.enabled).toBe(false);
			expect(settings.maxEntries).toBe(50);
			expect(settings.maxAgeDays).toBe(7);
		});

		it('should initialize with empty stats', () => {
			const stats = cacheService.getStats();
			expect(stats.totalEntries).toBe(0);
			expect(stats.totalHits).toBe(0);
			expect(stats.totalMisses).toBe(0);
			expect(stats.estimatedSavings).toBe(0);
		});
	});

	describe('cache key generation', () => {
		it('should generate consistent cache keys', () => {
			const key1 = cacheService.generateCacheKey('hello', 'context', 'gpt-4', 0.7);
			const key2 = cacheService.generateCacheKey('hello', 'context', 'gpt-4', 0.7);
			expect(key1).toBe(key2);
		});

		it('should generate different keys for different prompts', () => {
			const key1 = cacheService.generateCacheKey('hello', 'context', 'gpt-4', 0.7);
			const key2 = cacheService.generateCacheKey('world', 'context', 'gpt-4', 0.7);
			expect(key1).not.toBe(key2);
		});

		it('should generate different keys for different models', () => {
			const key1 = cacheService.generateCacheKey('hello', 'context', 'gpt-4', 0.7);
			const key2 = cacheService.generateCacheKey('hello', 'context', 'gpt-3.5-turbo', 0.7);
			expect(key1).not.toBe(key2);
		});

		it('should generate different keys for different temperatures', () => {
			const key1 = cacheService.generateCacheKey('hello', 'context', 'gpt-4', 0.7);
			const key2 = cacheService.generateCacheKey('hello', 'context', 'gpt-4', 0.9);
			expect(key1).not.toBe(key2);
		});

		it('should normalize prompt case for key generation', () => {
			const key1 = cacheService.generateCacheKey('Hello World', 'context', 'gpt-4', 0.7);
			const key2 = cacheService.generateCacheKey('hello world', 'context', 'gpt-4', 0.7);
			expect(key1).toBe(key2);
		});
	});

	describe('set and get operations', () => {
		it('should store and retrieve cache entries', () => {
			cacheService.set('prompt', 'context', 'gpt-4', 0.7, 'response', 100, 50, 50);
			const entry = cacheService.get('prompt', 'context', 'gpt-4', 0.7);
			
			expect(entry).not.toBeNull();
			expect(entry?.prompt).toBe('prompt');
			expect(entry?.response).toBe('response');
			expect(entry?.model).toBe('gpt-4');
		});

		it('should return null for cache miss', () => {
			const entry = cacheService.get('nonexistent', 'context', 'gpt-4', 0.7);
			expect(entry).toBeNull();
		});

		it('should track cache hits and misses', () => {
			cacheService.set('prompt', 'context', 'gpt-4', 0.7, 'response', 100, 50, 50);
			
			cacheService.get('prompt', 'context', 'gpt-4', 0.7); // hit
			cacheService.get('nonexistent', 'context', 'gpt-4', 0.7); // miss
			
			const stats = cacheService.getStats();
			expect(stats.totalHits).toBe(1);
			expect(stats.totalMisses).toBe(1);
		});

		it('should update access count on cache hits', () => {
			cacheService.set('prompt', 'context', 'gpt-4', 0.7, 'response', 100, 50, 50);
			
			cacheService.get('prompt', 'context', 'gpt-4', 0.7);
			cacheService.get('prompt', 'context', 'gpt-4', 0.7);
			const entry = cacheService.get('prompt', 'context', 'gpt-4', 0.7);
			
			expect(entry?.accessCount).toBe(4); // 1 initial + 3 gets
		});

		it('should track estimated savings', () => {
			cacheService.set('prompt', 'context', 'gpt-4', 0.7, 'response', 100, 50, 50);
			
			cacheService.get('prompt', 'context', 'gpt-4', 0.7);
			cacheService.get('prompt', 'context', 'gpt-4', 0.7);
			
			const stats = cacheService.getStats();
			expect(stats.estimatedSavings).toBe(200); // 100 tokens * 2 hits
		});
	});

	describe('cache entry expiration', () => {
		it('should expire entries older than maxAgeDays', () => {
			const service = new CacheService({ ...DEFAULT_CACHE_SETTINGS, maxAgeDays: 1 });
			
			// Mock an old entry
			const entry = service.set('prompt', 'context', 'gpt-4', 0.7, 'response', 100, 50, 50);
			
			// Manually set createdAt to 2 days ago
			const twoDaysAgo = Date.now() - (2 * 24 * 60 * 60 * 1000);
			(entry as any).createdAt = twoDaysAgo;
			
			const result = service.get('prompt', 'context', 'gpt-4', 0.7);
			expect(result).toBeNull();
		});
	});

	describe('LRU eviction', () => {
		it('should evict oldest entry when max entries reached', () => {
			const service = new CacheService({ ...DEFAULT_CACHE_SETTINGS, maxEntries: 2 });
			
			service.set('prompt1', '', 'gpt-4', 0.7, 'response1', 100, 50, 50);
			service.set('prompt2', '', 'gpt-4', 0.7, 'response2', 100, 50, 50);
			service.set('prompt3', '', 'gpt-4', 0.7, 'response3', 100, 50, 50);
			
			const stats = service.getStats();
			expect(stats.totalEntries).toBe(2);
		});

		it('should maintain max entries limit', () => {
			const service = new CacheService({ ...DEFAULT_CACHE_SETTINGS, maxEntries: 3 });
			
			service.set('prompt1', '', 'gpt-4', 0.7, 'response1', 100, 50, 50);
			service.set('prompt2', '', 'gpt-4', 0.7, 'response2', 100, 50, 50);
			service.set('prompt3', '', 'gpt-4', 0.7, 'response3', 100, 50, 50);
			service.set('prompt4', '', 'gpt-4', 0.7, 'response4', 100, 50, 50);
			service.set('prompt5', '', 'gpt-4', 0.7, 'response5', 100, 50, 50);
			
			const stats = service.getStats();
			expect(stats.totalEntries).toBe(3);
		});
	});

	describe('cache operations', () => {
		it('should clear all cache entries', () => {
			cacheService.set('prompt1', '', 'gpt-4', 0.7, 'response1', 100, 50, 50);
			cacheService.set('prompt2', '', 'gpt-4', 0.7, 'response2', 100, 50, 50);
			
			cacheService.clearCache();
			
			const stats = cacheService.getStats();
			expect(stats.totalEntries).toBe(0);
			expect(cacheService.getAllEntries()).toHaveLength(0);
		});

		it('should reset statistics', () => {
			cacheService.set('prompt', '', 'gpt-4', 0.7, 'response', 100, 50, 50);
			cacheService.get('prompt', '', 'gpt-4', 0.7);
			cacheService.get('nonexistent', '', 'gpt-4', 0.7);
			
			cacheService.resetStats();
			
			const stats = cacheService.getStats();
			expect(stats.totalHits).toBe(0);
			expect(stats.totalMisses).toBe(0);
			expect(stats.estimatedSavings).toBe(0);
		});

		it('should delete specific entry by ID', () => {
			const entry = cacheService.set('prompt', '', 'gpt-4', 0.7, 'response', 100, 50, 50);
			
			const deleted = cacheService.deleteEntry(entry.id);
			expect(deleted).toBe(true);
			
			const result = cacheService.get('prompt', '', 'gpt-4', 0.7);
			expect(result).toBeNull();
		});

		it('should return false when deleting non-existent entry', () => {
			const deleted = cacheService.deleteEntry('nonexistent');
			expect(deleted).toBe(false);
		});
	});

	describe('cache settings', () => {
		it('should update settings', () => {
			cacheService.updateSettings({ maxEntries: 50, maxAgeDays: 7 });
			
			const settings = cacheService.getSettings();
			expect(settings.maxEntries).toBe(50);
			expect(settings.maxAgeDays).toBe(7);
		});

		it('should evict excess entries when maxEntries is reduced', () => {
			cacheService.set('prompt1', '', 'gpt-4', 0.7, 'response1', 100, 50, 50);
			cacheService.set('prompt2', '', 'gpt-4', 0.7, 'response2', 100, 50, 50);
			cacheService.set('prompt3', '', 'gpt-4', 0.7, 'response3', 100, 50, 50);
			
			cacheService.updateSettings({ maxEntries: 1 });
			
			const stats = cacheService.getStats();
			expect(stats.totalEntries).toBe(1);
		});

		it('should enable and disable caching', () => {
			cacheService.setEnabled(false);
			expect(cacheService.isEnabled()).toBe(false);
			
			cacheService.setEnabled(true);
			expect(cacheService.isEnabled()).toBe(true);
		});

		it('should not cache when disabled', () => {
			cacheService.setEnabled(false);
			cacheService.set('prompt', '', 'gpt-4', 0.7, 'response', 100, 50, 50);
			
			const stats = cacheService.getStats();
			expect(stats.totalEntries).toBe(0);
		});

		it('should not return cached values when disabled', () => {
			cacheService.set('prompt', '', 'gpt-4', 0.7, 'response', 100, 50, 50);
			cacheService.setEnabled(false);
			
			const entry = cacheService.get('prompt', '', 'gpt-4', 0.7);
			expect(entry).toBeNull();
		});
	});

	describe('hit rate calculation', () => {
		it('should return 0 for empty cache', () => {
			expect(cacheService.getHitRate()).toBe(0);
		});

		it('should return 0 with no requests', () => {
			const service = new CacheService();
			expect(service.getHitRate()).toBe(0);
		});
	});

	describe('cost savings calculation', () => {
		it('should return 0 for new cache', () => {
			const service = new CacheService();
			const savings = service.getEstimatedCostSavings();
			expect(savings).toBe(0);
		});

		it('should calculate savings with custom rate', () => {
			const service = new CacheService();
			expect(service.getEstimatedCostSavings(0.01)).toBe(0);
		});
	});

	describe('cache size formatting', () => {
		it('should format bytes correctly', () => {
			cacheService.set('a', '', 'gpt-4', 0.7, 'b', 100, 50, 50);
			const formatted = cacheService.getFormattedCacheSize();
			expect(formatted).toMatch(/\d+(\.\d+)?\s*(B|KB|MB)/);
		});
	});

	describe('context invalidation', () => {
		it('should return 0 when no matches found', () => {
			const count = cacheService.invalidateByContext('nonexistent');
			expect(count).toBe(0);
		});
	});

	describe('export and import', () => {
		it('should export empty cache entries', () => {
			const service = new CacheService();
			const exported = service.exportCache();
			
			expect(exported.entries).toHaveLength(0);
			expect(exported.settings).toBeDefined();
		});

		it('should import cache data', () => {
			const entry: CacheEntry = {
				id: 'test_id',
				promptHash: 'hash1',
				contextHash: 'hash2',
				prompt: 'prompt',
				response: 'response',
				model: 'gpt-4',
				temperature: 0.7,
				tokensUsed: 100,
				inputTokens: 50,
				outputTokens: 50,
				createdAt: Date.now(),
				accessedAt: Date.now(),
				accessCount: 1
			};
			
			cacheService.importCache({
				entries: [entry],
				stats: { totalEntries: 1, totalHits: 5, totalMisses: 2, estimatedSavings: 500, cacheSize: 1000 }
			});
			
			expect(cacheService.getAllEntries()).toHaveLength(1);
			const stats = cacheService.getStats();
			expect(stats.totalHits).toBe(5);
		});

		it('should skip expired entries on import', () => {
			const oldEntry: CacheEntry = {
				id: 'old_id',
				promptHash: 'hash1',
				contextHash: 'hash2',
				prompt: 'old prompt',
				response: 'old response',
				model: 'gpt-4',
				temperature: 0.7,
				tokensUsed: 100,
				inputTokens: 50,
				outputTokens: 50,
				createdAt: Date.now() - (60 * 24 * 60 * 60 * 1000), // 60 days ago
				accessedAt: Date.now() - (60 * 24 * 60 * 60 * 1000),
				accessCount: 1
			};
			
			cacheService.importCache({ entries: [oldEntry] });
			
			expect(cacheService.getAllEntries()).toHaveLength(0);
		});
	});

	describe('clean expired', () => {
		it('should return 0 when no expired entries', () => {
			const service = new CacheService();
			const count = service.cleanExpired();
			expect(count).toBe(0);
		});
	});
});
