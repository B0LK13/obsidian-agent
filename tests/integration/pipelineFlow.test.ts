import { describe, it, expect, beforeEach } from 'vitest';
import { AgentRuntime } from '../../src/services/agentRuntime';
import { App, TFile } from 'obsidian';

// Full mock infrastructure
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

describe('Pipeline Flow - Integration', () => {
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

    // Inject mock AI service
    const mockAI = {
      generateEmbedding: async (text: string) => {
        return new Array(384).fill(0).map((_, i) => (text.charCodeAt(i % text.length) || 0) / 255);
      },
      generateCompletion: async (prompt: string) => {
        return `AI response: ${prompt.substring(0, 30)}`;
      },
    };

    runtime.replaceService('aiService', mockAI as any);
    await runtime.initialize();
  });

  it('should complete full pipeline flow', async () => {
    const services = runtime.getServices();

    mockVault.addFile('test.md', '# Test\n\nContent for testing the full pipeline flow with enough words to meet minimum requirements for document ingestion');

    const file = {
      path: 'test.md',
      basename: 'test',
      stat: { mtime: Date.now() },
    } as TFile;

    const ingestResult = await services.pipelineService.ingestNote(file);
    expect(ingestResult.success).toBe(true);

    const indexResult = await services.pipelineService.indexNote(file);
    expect(indexResult.success).toBe(true);

    const queryResult = await services.pipelineService.queryAgent('test query');
    expect(queryResult.success).toBe(true);
  });

  afterEach(async () => {
    await runtime.shutdown();
  });
});
