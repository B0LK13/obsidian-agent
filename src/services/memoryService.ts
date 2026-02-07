import { Vault } from 'obsidian';
import { VectorStore } from './vectorStore';
import { EmbeddingService } from './embeddingService';

export interface Memory {
    id: string;
    text: string;
    timestamp: number;
    metadata: Record<string, any>;
}

export class MemoryService {
    private vectorStore: VectorStore;
    private embeddingService: EmbeddingService;

    constructor(vault: Vault, embeddingService: EmbeddingService) {
        this.vectorStore = new VectorStore(vault, '.obsidian/plugins/obsidian-agent/memory_store.json');
        this.embeddingService = embeddingService;
    }

    async load(): Promise<void> {
        await this.vectorStore.load();
    }

    async addMemory(text: string, metadata: Record<string, any> = {}): Promise<void> {
        if (!text || text.trim().length === 0) return;

        const embedding = await this.embeddingService.generateEmbedding(text);
        const id = `memory_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

        await this.vectorStore.add({
            id,
            vector: embedding.vector,
            content: text,
            metadata: {
                ...metadata,
                text,
                timestamp: Date.now()
            }
        });

        await this.vectorStore.save();
    }

    async getRelevantMemories(query: string, limit: number = 5): Promise<string[]> {
        const embedding = await this.embeddingService.generateEmbedding(query);
        const results = await this.vectorStore.search(embedding.vector, limit, 0.6); // Higher threshold for memory

        return results.map(r => r.metadata.text);
    }

    async clear(): Promise<void> {
        await this.vectorStore.clear();
    }
}
