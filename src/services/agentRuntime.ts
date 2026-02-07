import { App, Vault } from 'obsidian';
import { VectorStore } from './vectorStore';
import { AuditLogger } from './auditLogger';
import { PipelineService } from './pipelineService';
import { AgentService } from './agent/agentService';
import { CacheService } from '../../cacheService';
import { AIService } from '../../aiService';
import { EmbeddingService } from './embeddingService';
import { IndexingService } from './indexingService';
import { MemoryService } from './memoryService';
import { 
  SearchVaultTool, 
  ReadNoteTool, 
  ListFilesTool, 
  RememberFactTool 
} from './agent/tools';
import { CreateNoteTool } from './agent/createNoteTool';
import { UpdateNoteTool } from './agent/updateNoteTool';

export interface RuntimeConfig {
  vaultPath: string;
  dataPath: string;
  enableAudit: boolean;
  enableCache: boolean;
  settings?: any; // ObsidianAgentSettings - optional for DI
  pipelineConfig?: {
    idempotencyEnabled?: boolean;
    maxRetries?: number;
    backoffMs?: number;
  };
}

export interface RuntimeServices {
  vault: Vault;
  aiService: AIService;
  embeddingService: EmbeddingService;
  vectorStore: VectorStore;
  auditLogger: AuditLogger;
  cacheService: CacheService;
  memoryService: MemoryService;
  indexingService: IndexingService;
  pipelineService: PipelineService;
  agentService: AgentService;
}

/**
 * AgentRuntime - Dependency Injection Container
 * 
 * Centralizes service initialization and wiring for the entire plugin.
 * Provides factory methods for creating services with proper dependencies.
 * Supports test mocking by allowing service replacement.
 */
export class AgentRuntime {
  private services: Partial<RuntimeServices> = {};
  private config: RuntimeConfig;
  private initialized = false;

  constructor(private app: App, config: Partial<RuntimeConfig> = {}) {
    this.config = {
      vaultPath: (app.vault.adapter as any).basePath || '/vault',
      dataPath: '.obsidian/plugins/obsidian-agent',
      enableAudit: true,
      enableCache: true,
      ...config,
    };
  }

  /**
   * Initialize all services in dependency order
   */
  async initialize(): Promise<RuntimeServices> {
    if (this.initialized) {
      return this.services as RuntimeServices;
    }

    const vault = this.app.vault;
    this.services.vault = vault;

    // Core services (no dependencies)
    this.services.auditLogger = await this.createAuditLogger();
    this.services.cacheService = this.createCacheService();

    // AI services
    this.services.aiService = this.getOrCreateAIService();
    this.services.embeddingService = this.createEmbeddingService();

    // Storage services
    this.services.vectorStore = await this.createVectorStore();
    this.services.memoryService = this.createMemoryService();

    // Indexing service
    this.services.indexingService = this.createIndexingService();

    // Pipeline service (depends on most services)
    this.services.pipelineService = this.createPipelineService();

    // Agent service (top-level orchestrator)
    this.services.agentService = this.createAgentService();

    this.initialized = true;
    return this.services as RuntimeServices;
  }

  /**
   * Get initialized services (throws if not initialized)
   */
  getServices(): RuntimeServices {
    if (!this.initialized) {
      throw new Error('AgentRuntime not initialized. Call initialize() first.');
    }
    return this.services as RuntimeServices;
  }

  /**
   * Replace a service (useful for testing with mocks)
   */
  replaceService<K extends keyof RuntimeServices>(
    key: K,
    service: RuntimeServices[K]
  ): void {
    this.services[key] = service;
  }

  /**
   * Factory: AuditLogger
   */
  private async createAuditLogger(): Promise<AuditLogger> {
    if (this.services.auditLogger) return this.services.auditLogger;

    const logger = new AuditLogger(this.app.vault);
    if (this.config.enableAudit) {
      await logger.initialize();
    }
    return logger;
  }

  /**
   * Factory: CacheService
   */
  private createCacheService(): CacheService {
    if (this.services.cacheService) return this.services.cacheService;

    return new CacheService({
      enabled: this.config.enableCache,
      maxEntries: 100,
      maxAgeDays: 30,
      matchThreshold: 1.0,
    });
  }

  /**
   * Factory: AIService (expects external injection)
   */
  private getOrCreateAIService(): AIService {
    if (!this.services.aiService) {
      throw new Error(
        'AIService must be injected before initialization. Use runtime.replaceService("aiService", service)'
      );
    }
    return this.services.aiService;
  }

  /**
   * Factory: EmbeddingService
   */
  private createEmbeddingService(): EmbeddingService {
    if (this.services.embeddingService) return this.services.embeddingService;

    // EmbeddingService requires settings - must be injected via replaceService or config
    if (!this.config.settings) {
      throw new Error(
        'EmbeddingService requires settings. Inject via config.settings or replaceService("embeddingService", ...)'
      );
    }

    return new EmbeddingService(this.config.settings);
  }

  /**
   * Factory: VectorStore
   */
  private async createVectorStore(): Promise<VectorStore> {
    if (this.services.vectorStore) return this.services.vectorStore;

    const store = new VectorStore(
      this.app.vault,
      `${this.config.dataPath}/vector_store.json`
    );
    await store.load();
    return store;
  }

  /**
   * Factory: MemoryService
   */
  private createMemoryService(): MemoryService {
    if (this.services.memoryService) return this.services.memoryService;

    // MemoryService expects (vault, embeddingService) based on its constructor
    return new MemoryService(
      this.app.vault,
      this.services.embeddingService!
    );
  }

  /**
   * Factory: IndexingService
   */
  private createIndexingService(): IndexingService {
    if (this.services.indexingService) return this.services.indexingService;

    return new IndexingService(
      this.app,
      this.services.embeddingService!,
      this.services.vectorStore!
    );
  }

  /**
   * Factory: PipelineService
   */
  private createPipelineService(): PipelineService {
    if (this.services.pipelineService) return this.services.pipelineService;

    return new PipelineService(
      this.app.vault,
      this.services.vectorStore!,
      this.services.auditLogger!,
      this.services.aiService!,
      this.services.embeddingService!,
      this.config.pipelineConfig
    );
  }

  /**
   * Factory: AgentService with all tools
   */
  private createAgentService(): AgentService {
    if (this.services.agentService) return this.services.agentService;

    const tools = [
      new SearchVaultTool(
        this.services.vectorStore!,
        this.services.embeddingService!
      ),
      new ReadNoteTool(this.app),
      new ListFilesTool(this.app),
      new RememberFactTool(this.services.memoryService!),
      new CreateNoteTool(this.app),
      new UpdateNoteTool(this.app),
    ];

    return new AgentService(
      this.services.aiService!,
      tools,
      this.config.settings || ({} as any),
      this.services.memoryService!
    );
  }

  /**
   * Health check - verify all services are operational
   */
  async healthCheck(): Promise<{
    healthy: boolean;
    services: Record<string, boolean>;
    errors: string[];
  }> {
    const results: Record<string, boolean> = {};
    const errors: string[] = [];

    try {
      // Check vector store
      const vectorSize = this.services.vectorStore?.size() || 0;
      results.vectorStore = vectorSize >= 0;
    } catch (error) {
      results.vectorStore = false;
      errors.push(`VectorStore: ${error}`);
    }

    try {
      // Check audit logger
      const auditStats = this.services.auditLogger?.getStats();
      results.auditLogger = !!auditStats;
    } catch (error) {
      results.auditLogger = false;
      errors.push(`AuditLogger: ${error}`);
    }

    try {
      // Check cache service
      const cacheStats = this.services.cacheService?.getStats();
      results.cacheService = !!cacheStats;
    } catch (error) {
      results.cacheService = false;
      errors.push(`CacheService: ${error}`);
    }

    try {
      // Check AI service (simple ping)
      results.aiService = !!this.services.aiService;
    } catch (error) {
      results.aiService = false;
      errors.push(`AIService: ${error}`);
    }

    const healthy = Object.values(results).every((v) => v === true);

    return { healthy, services: results, errors };
  }

  /**
   * Shutdown - cleanup resources
   */
  async shutdown(): Promise<void> {
    // Save persistent state
    if (this.services.vectorStore) {
      await this.services.vectorStore.save();
    }

    if (this.services.memoryService) {
      // MemoryService save is handled via vectorStore internally
    }

    // CacheService doesn't have save() method

    this.initialized = false;
  }

  /**
   * Get runtime stats
   */
  getStats() {
    return {
      initialized: this.initialized,
      config: this.config,
      services: {
        vectorStoreSize: this.services.vectorStore?.size() || 0,
        auditStats: this.services.auditLogger?.getStats(),
        cacheStats: this.services.cacheService?.getStats(),
        pipelineStats: this.services.pipelineService?.getStats(),
      },
    };
  }
}
