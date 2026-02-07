import { Vault } from 'obsidian';
import { VectorStore } from './vectorStore';
import { EmbeddingService } from './embeddingService';

export enum MemoryLayer {
    SESSION = 'session',     // current task state, temporary
    USER = 'user',           // preferences, constraints, identity
    LONG_TERM = 'long_term'  // docs, SOPs, decisions, archived facts
}

export interface Memory {
    id: string;
    text: string;
    timestamp: number;
    layer: MemoryLayer;
    metadata: Record<string, any>;
}

export class MemoryService {
    private vectorStore: VectorStore;
    private embeddingService: EmbeddingService;
    private sessionMemories: Memory[] = [];

    constructor(vault: Vault, embeddingService: EmbeddingService) {
        this.vectorStore = new VectorStore(vault, '.obsidian/plugins/obsidian-agent/memory_store.json');
        this.embeddingService = embeddingService;
    }

    async load(): Promise<void> {
        await this.vectorStore.load();
    }

    /**
     * Add a memory to a specific layer
     */
    async addMemory(text: string, layer: MemoryLayer = MemoryLayer.LONG_TERM, metadata: Record<string, any> = {}): Promise<void> {
        if (!text || text.trim().length === 0) return;

        const id = `memory_${layer}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
        const memory: Memory = {
            id,
            text,
            timestamp: Date.now(),
            layer,
            metadata: { ...metadata, text, layer }
        };

        if (layer === MemoryLayer.SESSION) {
            this.sessionMemories.push(memory);
            if (this.sessionMemories.length > 50) this.sessionMemories.shift(); // Prune session
        } else {
            const embedding = await this.embeddingService.generateEmbedding(text);
            await this.vectorStore.add({
                id,
                vector: embedding.vector,
                content: text,
                metadata: memory.metadata
            });
            await this.vectorStore.save();
        }
    }

    /**
     * Retrieve relevant memories as a flat list (legacy interface for backward compatibility)
     */
    async getRelevantMemories(query: string, limit: number = 10): Promise<string[]> {
        const contextual = await this.getContextualMemory(query, limit);
        return [...contextual.session, ...contextual.user, ...contextual.longTerm].slice(0, limit);
    }

    /**
     * Retrieve relevant memories across layers with priority weighting
     */
    async getContextualMemory(query: string, limit: number = 10): Promise<{
        session: string[];
        user: string[];
        longTerm: string[];
    }> {
        const embedding = await this.embeddingService.generateEmbedding(query);
        const results = await this.vectorStore.search(embedding.vector, limit, 0.5);

        const categorized = {
            session: this.sessionMemories
                .filter(m => this.isTextRelevant(m.text, query))
                .map(m => m.text),
            user: results
                .filter(r => r.metadata.layer === MemoryLayer.USER)
                .map(r => r.metadata.text),
            longTerm: results
                .filter(r => r.metadata.layer === MemoryLayer.LONG_TERM)
                .map(r => r.metadata.text)
        };

        return categorized;
    }

    private isTextRelevant(text: string, query: string): boolean {
        // Simple keyword check for session memories (since they aren't vectorized here for speed)
        const keywords = query.toLowerCase().split(/\s+/).filter(k => k.length > 3);
        const content = text.toLowerCase();
        return keywords.some(k => content.includes(k)) || keywords.length === 0;
    }

    /**
     * Specific helper for persistent user preferences
     */
    async learnUserPreference(preference: string): Promise<void> {
        await this.addMemory(preference, MemoryLayer.USER);
    }

    async clearSession(): Promise<void> {
        this.sessionMemories = [];
    }

    async clearAll(): Promise<void> {
        this.sessionMemories = [];
        await this.vectorStore.clear();
    }
}
