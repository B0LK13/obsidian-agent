import { describe, it, expect, beforeEach, vi } from 'vitest';
import { PipelineService, IngestResult, IndexResult } from '../src/services/pipelineService';
import { VectorStore } from '../src/services/vectorStore';
import { AuditLogger } from '../src/services/auditLogger';
import { AIService } from '../aiService';
import { TFile, Vault } from 'obsidian';

// Mocks
class MockVault {
  private files: Map<string, { content: string; stat: any }> = new Map();

  addFile(path: string, content: string, mtime: number = Date.now()) {
    this.files.set(path, {
      content,
      stat: { mtime },
    });
  }

  async cachedRead(file: TFile): Promise<string> {
    const data = this.files.get(file.path);
    return data?.content || '';
  }

  get adapter() {
    return {
      exists: async () => true,
      read: async () => '{}',
      write: async () => {},
      mkdir: async () => {},
    };
  }
}

class MockVectorStore {
  private data: Map<string, any> = new Map();

  async add(doc: any) {
    this.data.set(doc.id, doc);
  }

  async remove(id: string) {
    this.data.delete(id);
  }

  get(id: string) {
    return this.data.get(id) || null;
  }

  async search(query: string, topK: number = 5) {
    return Array.from(this.data.values()).slice(0, topK).map((doc) => ({
      id: doc.id,
      score: 0.85,
      content: doc.content,
      metadata: doc.metadata,
    }));
  }

  async save() {}
  async load() {}
  size() {
    return this.data.size;
  }
}

class MockAuditLogger {
  private logs: any[] = [];

  createOperationId() {
    return 'op-' + Date.now() + '-' + Math.random();
  }

  async logOperation(op: string, details: any, rollbackMetadata?: any): Promise<string> {
    const opId = this.createOperationId();
    this.logs.push({ opId, op, status: 'logged', details, rollbackMetadata });
    return opId;
  }

  async startOperation(opId: string, op: string, details: any) {
    this.logs.push({ opId, op, status: 'started', details });
  }

  async completeOperation(opId: string, op: string, details: any, rollback?: any) {
    this.logs.push({ opId, op, status: 'completed', details, rollback });
  }

  async failOperation(opId: string, op: string, details: any, error: string) {
    this.logs.push({ opId, op, status: 'failed', details, error });
  }

  async getRollbackMetadata(opId: string): Promise<any> {
    const log = this.logs.find(l => l.opId === opId && l.rollbackMetadata);
    return log?.rollbackMetadata || null;
  }

  async query(filters: any) {
    return this.logs;
  }

  getOperationHistory(opId: string) {
    return this.logs.filter((l) => l.opId === opId);
  }

  getStats() {
    return { totalOperations: this.logs.length };
  }
}

class MockAIService {
  async generateEmbedding(text: string): Promise<number[]> {
    return new Array(384).fill(0).map(() => Math.random());
  }

  async generateCompletion(prompt: string, options?: any): Promise<string> {
    return 'Mock AI response';
  }
}

class MockEmbeddingService {
  async generateEmbedding(text: string): Promise<{ vector: number[]; tokensUsed: number }> {
    return {
      vector: new Array(384).fill(0).map(() => Math.random()),
      tokensUsed: 10
    };
  }
}

describe('PipelineService', () => {
  let pipeline: PipelineService;
  let vault: Vault;
  let vectorStore: VectorStore;
  let auditLogger: AuditLogger;
  let aiService: AIService;

  beforeEach(() => {
    vault = new MockVault() as any;
    vectorStore = new MockVectorStore() as any;
    auditLogger = new MockAuditLogger() as any;
    aiService = new MockAIService() as any;
    const embeddingService = new MockEmbeddingService() as any;

    pipeline = new PipelineService(vault, vectorStore, auditLogger, aiService, embeddingService);
  });

  describe('ingestNote', () => {
    it('should ingest a valid note', async () => {
      const mockVault = vault as any as MockVault;
      mockVault.addFile('test.md', '# Test\n\nThis is a test note with enough words.');

      const file = { path: 'test.md', basename: 'test', stat: { mtime: Date.now() } } as TFile;

      const result = await pipeline.ingestNote(file);

      expect(result.success).toBe(true);
      expect(result.filePath).toBe('test.md');
      expect(result.normalized).toBeTruthy();
      expect(result.normalized!.title).toBe('test');
      expect(result.normalized!.wordCount).toBeGreaterThan(0);
    });

    it('should reject notes that are too short', async () => {
      const mockVault = vault as any as MockVault;
      mockVault.addFile('short.md', 'Hi');

      const file = { path: 'short.md', basename: 'short', stat: { mtime: Date.now() } } as TFile;

      const result = await pipeline.ingestNote(file);

      expect(result.success).toBe(false);
      expect(result.error).toContain('too short');
    });

    it('should extract tags from content', async () => {
      const mockVault = vault as any as MockVault;
      mockVault.addFile('tags.md', '# Tags Test\n\nThis note has #tag1 and #tag2 in it.');

      const file = { path: 'tags.md', basename: 'tags', stat: { mtime: Date.now() } } as TFile;

      const result = await pipeline.ingestNote(file);

      expect(result.success).toBe(true);
      expect(result.normalized!.tags).toContain('tag1');
      expect(result.normalized!.tags).toContain('tag2');
    });

    it('should support idempotency keys', async () => {
      const mockVault = vault as any as MockVault;
      mockVault.addFile('idem.md', '# Idempotency Test\n\nThis is a test note with content.');

      const file = { path: 'idem.md', basename: 'idem', stat: { mtime: Date.now() } } as TFile;

      const result1 = await pipeline.ingestNote(file, 'key-123');
      const result2 = await pipeline.ingestNote(file, 'key-123');

      expect(result1.operationId).toBe(result2.operationId);
      expect(result1).toEqual(result2);
    });
  });

  describe('indexNote', () => {
    it('should index a note and create vector', async () => {
      const mockVault = vault as any as MockVault;
      mockVault.addFile('index.md', '# Index Test\n\nThis note should be indexed properly with more than ten words in it.');

      const file = {
        path: 'index.md',
        basename: 'index',
        stat: { mtime: Date.now() },
      } as TFile;

      const result = await pipeline.indexNote(file);
      
      if (!result.success) {
        console.log('Index failed:', result.error);
      }

      expect(result.success).toBe(true);
      expect(result.vectorId).toBe('index.md');
      expect(vectorStore.get('index.md')).toBeTruthy();
    });

    it('should fail if ingest fails', async () => {
      const mockVault = vault as any as MockVault;
      mockVault.addFile('fail.md', 'x'); // Too short

      const file = { path: 'fail.md', basename: 'fail', stat: { mtime: Date.now() } } as TFile;

      const result = await pipeline.indexNote(file);

      expect(result.success).toBe(false);
      expect(result.error).toBeTruthy();
    });
  });

  describe('queryAgent', () => {
    beforeEach(async () => {
      // Pre-populate vector store
      const mockVault = vault as any as MockVault;
      mockVault.addFile('doc1.md', '# Document 1\n\nContent about artificial intelligence and machine learning models for data processing.');
      mockVault.addFile('doc2.md', '# Document 2\n\nMore content about machine learning algorithms and neural network architectures.');

      const file1 = {
        path: 'doc1.md',
        basename: 'doc1',
        stat: { mtime: Date.now() },
      } as TFile;
      const file2 = {
        path: 'doc2.md',
        basename: 'doc2',
        stat: { mtime: Date.now() },
      } as TFile;

      await pipeline.indexNote(file1);
      await pipeline.indexNote(file2);
    });

    it('should query and return results', async () => {
      const result = await pipeline.queryAgent('Tell me about AI');

      expect(result.success).toBe(true);
      expect(result.answer).toBeTruthy();
      expect(result.evidence.sources.length).toBeGreaterThan(0);
      expect(result.confidence).toBeGreaterThan(0);
    });

    it('should handle no results gracefully', async () => {
      // Clear vector store
      await pipeline.clearIdempotencyCache();

      const result = await pipeline.queryAgent('nonexistent topic xyz');

      expect(result.success).toBe(true);
      expect(result.answer).toContain('No relevant notes found');
      expect(result.recommendedAction).toBeTruthy();
    });
  });

  describe('rollbackOperation', () => {
    it('should rollback an index operation', async () => {
      const mockVault = vault as any as MockVault;
      mockVault.addFile('rollback.md', '# Rollback Test\n\nThis content will be indexed then rolled back with sufficient words for testing the rollback operation.');

      const file = {
        path: 'rollback.md',
        basename: 'rollback',
        stat: { mtime: Date.now() },
      } as TFile;

      const indexResult = await pipeline.indexNote(file);
      if (!indexResult.success) {
        console.log('Rollback test: Index failed:', indexResult.error);
      }
      expect(indexResult.success).toBe(true);
      expect(vectorStore.get('rollback.md')).toBeTruthy();

      const rollbackResult = await pipeline.rollbackOperation(indexResult.operationId);
      if (!rollbackResult.success) {
        console.log('Rollback failed:', rollbackResult.error);
      }
      expect(rollbackResult.success).toBe(true);
      expect(vectorStore.get('rollback.md')).toBeFalsy();
    });

    it('should fail rollback if operation not found', async () => {
      const result = await pipeline.rollbackOperation('nonexistent-op');
      expect(result.success).toBe(false);
      expect(result.error).toContain('No operation found');
    });
  });
});
