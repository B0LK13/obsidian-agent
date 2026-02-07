import { describe, it, expect, beforeEach } from 'vitest';
import { AgentRuntime } from '../../src/services/agentRuntime';
import { App, TFile } from 'obsidian';

class MockVault {
  private files: Map<string, string> = new Map();

  addFile(path: string, content: string) {
    this.files.set(path, content);
  }

  async cachedRead(file: TFile): Promise<string> {
    return this.files.get(file.path) || '';
  }

  getAbstractFileByPath(path: string) {
    if (this.files.has(path)) {
      return { path, basename: path.split('/').pop() || path };
    }
    return null;
  }

  get adapter() {
    return {
      basePath: '/test/vault',
      exists: async () => true,
      read: async () => '{}',
      write: async () => {},
      mkdir: async () => {},
    };
  }
}

class MockApp {
  vault: MockVault;
  constructor() {
    this.vault = new MockVault();
  }
}

describe('End-to-End Agent Tests', () => {
  let runtime: AgentRuntime;
  let app: App;
  let mockVault: MockVault;

  beforeEach(async () => {
    app = new MockApp() as any;
    mockVault = (app as any).vault;
    
    runtime = new AgentRuntime(app, {
      settings: {
        apiProvider: 'openai',
        apiKey: 'mock-key',
        model: 'gpt-4',
        temperature: 0.7,
        maxTokens: 1000,
        embeddingModel: 'text-embedding-ada-002',
      } as any
    });

    const mockAI = {
      generateEmbedding: async (text: string) => {
        return new Array(384).fill(0).map(() => Math.random());
      },
      generateCompletion: async (prompt: string) => {
        return 'E2E AI response';
      },
    };

    runtime.replaceService('aiService', mockAI as any);
    await runtime.initialize();
  });

  it('should handle normal query flow', async () => {
    const services = runtime.getServices();

    mockVault.addFile('note.md', '# Note\n\nSample content for E2E testing with enough words to meet minimum requirements.');

    const file = {
      path: 'note.md',
      basename: 'note',
      stat: { mtime: Date.now() },
    } as TFile;

    const indexResult = await services.pipelineService.indexNote(file);
    if (!indexResult.success) {
      console.error('E2E normal query: Index failed:', indexResult.error);
    }
    
    const result = await services.pipelineService.queryAgent('test');
    if (!result.success) {
      console.error('E2E normal query: Query failed:', result.error);
    }

    expect(result.success).toBe(true);
  });

  it('should handle rollback integrity', async () => {
    const services = runtime.getServices();

    mockVault.addFile('rollback.md', '# Rollback\n\nTesting rollback integrity with sufficient content for proper processing.');

    const file = {
      path: 'rollback.md',
      basename: 'rollback',
      stat: { mtime: Date.now() },
    } as TFile;

    const indexResult = await services.pipelineService.indexNote(file);
    if (!indexResult.success) {
      console.error('E2E rollback: Index failed:', indexResult.error);
    }
    
    const rollbackResult = await services.pipelineService.rollbackOperation(
      indexResult.operationId
    );
    if (!rollbackResult.success) {
      console.error('E2E rollback: Rollback failed:', rollbackResult.error);
    }

    expect(rollbackResult.success).toBe(true);
  });

  afterEach(async () => {
    await runtime.shutdown();
  });
});
