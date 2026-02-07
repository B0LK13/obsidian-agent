import { TFile, Vault } from 'obsidian';
import { VectorStore, VectorDocument } from './vectorStore';
import { AuditLogger, RollbackMetadata } from './auditLogger';
import { AIService } from '../../aiService';
import { EmbeddingService } from './embeddingService';

export interface IngestResult {
  operationId: string;
  success: boolean;
  filePath: string;
  error?: string;
  normalized?: {
    title: string;
    content: string;
    wordCount: number;
    tags: string[];
  };
}

export interface IndexResult {
  operationId: string;
  success: boolean;
  filePath: string;
  vectorId?: string;
  error?: string;
}

export interface QueryResult {
  operationId: string;
  success: boolean;
  answer: string;
  evidence: {
    sources: Array<{ path: string; relevance: number; excerpt: string }>;
    totalMatches: number;
  };
  confidence: number;
  recommendedAction?: string;
  error?: string;
}

export interface RollbackResult {
  operationId: string;
  success: boolean;
  restoredState?: any;
  error?: string;
}

export interface PipelineConfig {
  idempotencyEnabled: boolean;
  maxRetries: number;
  backoffMs: number;
  normalizationRules: {
    stripFrontmatter: boolean;
    extractTags: boolean;
    minWordCount: number;
  };
}

const DEFAULT_PIPELINE_CONFIG: PipelineConfig = {
  idempotencyEnabled: true,
  maxRetries: 3,
  backoffMs: 1000,
  normalizationRules: {
    stripFrontmatter: true,
    extractTags: true,
    minWordCount: 10,
  },
};

export class PipelineService {
  private vault: Vault;
  private vectorStore: VectorStore;
  private auditLogger: AuditLogger;
  private aiService: AIService;
  private embeddingService: EmbeddingService;
  private config: PipelineConfig;
  private idempotencyCache: Map<string, any> = new Map();

  constructor(
    vault: Vault,
    vectorStore: VectorStore,
    auditLogger: AuditLogger,
    aiService: AIService,
    embeddingService: EmbeddingService,
    config: Partial<PipelineConfig> = {}
  ) {
    this.vault = vault;
    this.vectorStore = vectorStore;
    this.auditLogger = auditLogger;
    this.aiService = aiService;
    this.embeddingService = embeddingService;
    this.config = { ...DEFAULT_PIPELINE_CONFIG, ...config };
  }

  async ingestNote(
    file: TFile,
    idempotencyKey?: string
  ): Promise<IngestResult> {
    const operationId = this.auditLogger.createOperationId();

    // Check idempotency
    if (idempotencyKey && this.config.idempotencyEnabled) {
      const cached = this.idempotencyCache.get(idempotencyKey);
      if (cached) {
        return cached;
      }
    }

    try {
      await this.auditLogger.startOperation(operationId, 'ingest', {
        filePath: file.path,
        idempotencyKey,
      });

      const content = await this.vault.cachedRead(file);
      const normalized = this.normalizeContent(content, file);

      // Validate
      if (normalized.wordCount < this.config.normalizationRules.minWordCount) {
        throw new Error(
          `Content too short: ${normalized.wordCount} words (min: ${this.config.normalizationRules.minWordCount})`
        );
      }

      const result: IngestResult = {
        operationId,
        success: true,
        filePath: file.path,
        normalized,
      };

      await this.auditLogger.completeOperation(operationId, 'ingest', {
        filePath: file.path,
        normalized,
      });

      // Cache for idempotency
      if (idempotencyKey) {
        this.idempotencyCache.set(idempotencyKey, result);
      }

      return result;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      await this.auditLogger.failOperation(operationId, 'ingest', {
        filePath: file.path,
      }, errorMsg);

      return {
        operationId,
        success: false,
        filePath: file.path,
        error: errorMsg,
      };
    }
  }

  async indexNote(
    file: TFile,
    idempotencyKey?: string
  ): Promise<IndexResult> {
    const operationId = this.auditLogger.createOperationId();

    // Check idempotency
    if (idempotencyKey && this.config.idempotencyEnabled) {
      const cached = this.idempotencyCache.get(idempotencyKey);
      if (cached) {
        return cached;
      }
    }

    try {
      await this.auditLogger.startOperation(operationId, 'index', {
        filePath: file.path,
        idempotencyKey,
      });

      // First ingest
      const ingestResult = await this.ingestNote(file);
      if (!ingestResult.success || !ingestResult.normalized) {
        throw new Error(`Ingest failed: ${ingestResult.error}`);
      }

      // Store previous state for rollback
      const previousVector = this.vectorStore.get(file.path);
      const rollbackMetadata: RollbackMetadata = {
        previousState: previousVector,
        affectedFiles: [file.path],
        affectedIndices: [file.path],
      };

      // Generate embedding with retry
      const embeddingResult = await this.withRetry(
        () => this.embeddingService.generateEmbedding(ingestResult.normalized!.content)
      );
      const embedding = embeddingResult.vector;

      // Add to vector store
      const doc: VectorDocument = {
        id: file.path,
        vector: embedding,
        metadata: {
          title: ingestResult.normalized.title,
          tags: ingestResult.normalized.tags,
          wordCount: ingestResult.normalized.wordCount,
          mtime: file.stat.mtime,
        },
        content: ingestResult.normalized.content.substring(0, 500), // Preview
      };

      await this.vectorStore.add(doc);
      await this.vectorStore.save();

      const result: IndexResult = {
        operationId,
        success: true,
        filePath: file.path,
        vectorId: file.path,
      };

      await this.auditLogger.completeOperation(
        operationId,
        'index',
        { filePath: file.path, vectorId: file.path },
        rollbackMetadata
      );

      // Cache for idempotency
      if (idempotencyKey) {
        this.idempotencyCache.set(idempotencyKey, result);
      }

      return result;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      await this.auditLogger.failOperation(operationId, 'index', {
        filePath: file.path,
      }, errorMsg);

      return {
        operationId,
        success: false,
        filePath: file.path,
        error: errorMsg,
      };
    }
  }

  async queryAgent(
    query: string,
    options: { topK?: number; minScore?: number } = {}
  ): Promise<QueryResult> {
    const operationId = this.auditLogger.createOperationId();

    try {
      await this.auditLogger.startOperation(operationId, 'query', {
        query,
        options,
      });

      // Generate embedding for search
      const queryEmbeddingResult = await this.embeddingService.generateEmbedding(query);
      const queryEmbedding = queryEmbeddingResult.vector;

      // Search with retry
      const searchResults = await this.withRetry(() =>
        this.vectorStore.search(queryEmbedding, options.topK || 5, options.minScore)
      );

      if (searchResults.length === 0) {
        const result: QueryResult = {
          operationId,
          success: true,
          answer: 'No relevant notes found for your query.',
          evidence: { sources: [], totalMatches: 0 },
          confidence: 0,
          recommendedAction: 'Try a different search query or create a new note on this topic.',
        };

        await this.auditLogger.completeOperation(operationId, 'query', {
          query,
          resultsCount: 0,
        });

        return result;
      }

      // Build context
      const sources = searchResults.map((r) => ({
        path: r.id,
        relevance: r.score,
        excerpt: r.content || '',
      }));

      const context = sources
        .map((s, i) => `[${i + 1}] ${s.path} (relevance: ${s.relevance.toFixed(2)})\n${s.excerpt}`)
        .join('\n\n');

      // Generate answer with retry
      const prompt = `Based on the following notes from the knowledge base, answer the user's question.

Question: ${query}

Relevant Notes:
${context}

Provide a clear, structured answer that:
1. Directly answers the question
2. Cites specific sources using [1], [2], etc.
3. Indicates confidence level (high/medium/low)
4. Suggests a relevant next action if applicable

Answer:`;

      const answer = await this.withRetry(() =>
        this.aiService.generateCompletion(prompt)
          .then(result => result.text || result)
      );

      const answerText = typeof answer === 'string' ? answer : (answer as any).text || String(answer);

      // Extract confidence (simple heuristic)
      const confidence = this.estimateConfidence(answerText, searchResults);

      const result: QueryResult = {
        operationId,
        success: true,
        answer: answerText,
        evidence: {
          sources,
          totalMatches: searchResults.length,
        },
        confidence,
        recommendedAction: this.extractRecommendedAction(answerText),
      };

      await this.auditLogger.completeOperation(operationId, 'query', {
        query,
        resultsCount: searchResults.length,
        confidence,
      });

      return result;
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      await this.auditLogger.failOperation(operationId, 'query', { query }, errorMsg);

      return {
        operationId,
        success: false,
        answer: '',
        evidence: { sources: [], totalMatches: 0 },
        confidence: 0,
        error: errorMsg,
      };
    }
  }

  async rollbackOperation(operationId: string): Promise<RollbackResult> {
    try {
      const history = this.auditLogger.getOperationHistory(operationId);
      if (history.length === 0) {
        return {
          operationId,
          success: false,
          error: `No operation found with ID: ${operationId}`,
        };
      }

      const lastEntry = history[history.length - 1];
      if (lastEntry.status !== 'completed') {
        return {
          operationId,
          success: false,
          error: `Cannot rollback operation with status: ${lastEntry.status}`,
        };
      }

      const rollbackMeta = lastEntry.rollbackMetadata;
      if (!rollbackMeta) {
        return {
          operationId,
          success: false,
          error: 'No rollback metadata available',
        };
      }

      // Execute rollback based on operation type
      if (lastEntry.operation === 'index') {
        if (rollbackMeta.previousState === null || rollbackMeta.previousState === undefined) {
          // Was a new entry, remove it
          for (const id of rollbackMeta.affectedIndices || []) {
            await this.vectorStore.remove(id);
          }
        } else {
          // Restore previous state
          await this.vectorStore.add(rollbackMeta.previousState);
        }
        await this.vectorStore.save();
      }

      await this.auditLogger.rollbackOperation(operationId, {
        originalOperation: lastEntry.operation,
        restoredState: rollbackMeta.previousState,
      });

      return {
        operationId,
        success: true,
        restoredState: rollbackMeta.previousState,
      };
    } catch (error) {
      const errorMsg = error instanceof Error ? error.message : String(error);
      return {
        operationId,
        success: false,
        error: errorMsg,
      };
    }
  }

  private normalizeContent(
    content: string,
    file: TFile
  ): {
    title: string;
    content: string;
    wordCount: number;
    tags: string[];
  } {
    let normalized = content;
    let tags: string[] = [];

    // Strip frontmatter
    if (this.config.normalizationRules.stripFrontmatter) {
      normalized = content.replace(/^---\n[\s\S]*?\n---\n/, '');
    }

    // Extract tags
    if (this.config.normalizationRules.extractTags) {
      const tagMatches = content.matchAll(/#([\w-]+)/g);
      tags = Array.from(tagMatches, (m) => m[1]);
    }

    const wordCount = normalized.split(/\s+/).filter((w) => w.length > 0).length;

    return {
      title: file.basename,
      content: normalized.trim(),
      wordCount,
      tags: [...new Set(tags)], // unique
    };
  }

  private async withRetry<T>(
    fn: () => Promise<T>,
    retries: number = this.config.maxRetries
  ): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));
        
        if (attempt < retries) {
          const backoff = this.config.backoffMs * Math.pow(2, attempt);
          await new Promise((resolve) => setTimeout(resolve, backoff));
        }
      }
    }

    throw lastError || new Error('Max retries exceeded');
  }

  private estimateConfidence(answer: string, results: any[]): number {
    // Simple heuristic based on:
    // - Number of results
    // - Top result score
    // - Presence of citations
    const hasCitations = /\[\d+\]/.test(answer);
    const topScore = results[0]?.score || 0;
    const resultCount = results.length;

    let confidence = 0;
    if (topScore > 0.8) confidence += 0.4;
    else if (topScore > 0.6) confidence += 0.2;

    if (resultCount >= 3) confidence += 0.3;
    else if (resultCount >= 1) confidence += 0.1;

    if (hasCitations) confidence += 0.3;

    return Math.min(confidence, 1.0);
  }

  private extractRecommendedAction(answer: string): string | undefined {
    // Look for action-oriented phrases
    const actionPatterns = [
      /(?:next step|recommend|suggest|consider):\s*(.+?)(?:\n|$)/i,
      /(?:you (?:should|could|might)):\s*(.+?)(?:\n|$)/i,
    ];

    for (const pattern of actionPatterns) {
      const match = answer.match(pattern);
      if (match && match[1]) {
        return match[1].trim();
      }
    }

    return undefined;
  }

  getStats() {
    return {
      audit: this.auditLogger.getStats(),
      idempotencyCacheSize: this.idempotencyCache.size,
    };
  }

  async clearIdempotencyCache(): Promise<void> {
    this.idempotencyCache.clear();
  }
}
