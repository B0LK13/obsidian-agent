import { describe, it, expect, beforeEach } from 'vitest';
import { AuditLogger, AuditEntry } from '../src/services/auditLogger';
import { Vault } from 'obsidian';

// Mock Vault
class MockVault {
  private storage: Map<string, string> = new Map();

  get adapter() {
    return {
      exists: async (path: string) => this.storage.has(path),
      read: async (path: string) => this.storage.get(path) || '',
      write: async (path: string, content: string) => {
        this.storage.set(path, content);
      },
      mkdir: async (path: string) => {
        // no-op for mock
      },
    };
  }
}

describe('AuditLogger', () => {
  let logger: AuditLogger;
  let vault: Vault;

  beforeEach(async () => {
    vault = new MockVault() as any as Vault;
    logger = new AuditLogger(vault);
    await logger.initialize();
  });

  describe('createOperationId', () => {
    it('should create unique operation IDs', () => {
      const id1 = logger.createOperationId();
      const id2 = logger.createOperationId();
      expect(id1).toBeTruthy();
      expect(id2).toBeTruthy();
      expect(id1).not.toBe(id2);
    });
  });

  describe('logOperation', () => {
    it('should log a basic operation', async () => {
      const opId = logger.createOperationId();
      await logger.logOperation(opId, 'ingest', 'started', {
        filePath: 'test.md',
      });

      const history = logger.getOperationHistory(opId);
      expect(history).toHaveLength(1);
      expect(history[0].operation).toBe('ingest');
      expect(history[0].status).toBe('started');
      expect(history[0].details.filePath).toBe('test.md');
    });

    it('should generate checksums for tamper detection', async () => {
      const opId = logger.createOperationId();
      await logger.logOperation(opId, 'ingest', 'started', {});

      const history = logger.getOperationHistory(opId);
      expect(history[0].checksum).toBeTruthy();
      expect(typeof history[0].checksum).toBe('string');
    });
  });

  describe('Operation lifecycle', () => {
    it('should track start -> complete flow', async () => {
      const opId = logger.createOperationId();

      await logger.startOperation(opId, 'index', { file: 'note.md' });
      await logger.completeOperation(
        opId,
        'index',
        { vectorId: 'note.md' },
        { previousState: null, affectedIndices: ['note.md'] }
      );

      const history = logger.getOperationHistory(opId);
      expect(history).toHaveLength(2);
      expect(history[0].status).toBe('started');
      expect(history[1].status).toBe('completed');
      expect(history[1].rollbackMetadata).toBeTruthy();
    });

    it('should track start -> fail flow', async () => {
      const opId = logger.createOperationId();

      await logger.startOperation(opId, 'query', { query: 'test' });
      await logger.failOperation(opId, 'query', { query: 'test' }, 'Network error');

      const history = logger.getOperationHistory(opId);
      expect(history).toHaveLength(2);
      expect(history[1].status).toBe('failed');
      expect(history[1].error).toBe('Network error');
    });
  });

  describe('query', () => {
    beforeEach(async () => {
      const opId1 = logger.createOperationId();
      const opId2 = logger.createOperationId();

      await logger.logOperation(opId1, 'ingest', 'completed', { file: 'a.md' });
      await logger.logOperation(opId2, 'query', 'failed', { query: 'test' });
    });

    it('should query by operation type', () => {
      const results = logger.query({ operation: 'ingest' });
      expect(results).toHaveLength(1);
      expect(results[0].operation).toBe('ingest');
    });

    it('should query by status', () => {
      const results = logger.query({ status: 'failed' });
      expect(results).toHaveLength(1);
      expect(results[0].status).toBe('failed');
    });

    it('should limit results', () => {
      const results = logger.query({ limit: 1 });
      expect(results).toHaveLength(1);
    });
  });

  describe('verifyIntegrity', () => {
    it('should verify integrity of clean audit log', async () => {
      const opId = logger.createOperationId();
      await logger.logOperation(opId, 'ingest', 'completed', {});

      const result = await logger.verifyIntegrity();
      expect(result.valid).toBe(true);
      expect(result.tamperedEntries).toHaveLength(0);
    });
  });

  describe('getStats', () => {
    it('should return accurate stats', async () => {
      const opId1 = logger.createOperationId();
      const opId2 = logger.createOperationId();

      await logger.logOperation(opId1, 'ingest', 'completed', {});
      await logger.logOperation(opId2, 'query', 'failed', {});

      const stats = logger.getStats();
      expect(stats.totalOperations).toBe(2);
      expect(stats.completedOperations).toBe(1);
      expect(stats.failedOperations).toBe(1);
    });
  });

  describe('clear', () => {
    it('should clear all entries', async () => {
      const opId = logger.createOperationId();
      await logger.logOperation(opId, 'ingest', 'completed', {});

      await logger.clear();

      const stats = logger.getStats();
      expect(stats.totalOperations).toBe(0);
    });
  });
});
