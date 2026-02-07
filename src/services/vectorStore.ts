import { Vault } from 'obsidian';

export interface VectorDocument {
    id: string; // usually file path
    vector: number[];
    metadata: Record<string, any>;
    content: string; // Optional: store chunk text
}

export interface SearchResult {
    id: string;
    score: number;
    metadata: Record<string, any>;
    content?: string;
}

export class VectorStore {
    private vectors: Map<string, number[]> = new Map();
    private metadata: Map<string, Record<string, any>> = new Map();
    private vault: Vault;
    private readonly STORAGE_FILE: string;

    constructor(vault: Vault, storageFile: string = '.obsidian/plugins/obsidian-agent/vector_store.json') {
        this.vault = vault;
        this.STORAGE_FILE = storageFile;
    }

    async add(doc: VectorDocument): Promise<void> {
        this.vectors.set(doc.id, doc.vector);
        this.metadata.set(doc.id, doc.metadata);
    }

    async remove(id: string): Promise<void> {
        this.vectors.delete(id);
        this.metadata.delete(id);
    }

    get(id: string): VectorDocument | null {
        const vector = this.vectors.get(id);
        const meta = this.metadata.get(id);
        if (!vector || !meta) return null;
        
        return {
            id,
            vector,
            metadata: meta,
            content: meta.content || ''
        };
    }

    async search(queryVector: number[], limit: number = 10, minScore: number = 0.0): Promise<SearchResult[]> {
        const results: SearchResult[] = [];

        for (const [id, vector] of this.vectors) {
            const score = this.cosineSimilarity(queryVector, vector);
            if (score >= minScore) {
                results.push({
                    id,
                    score,
                    metadata: this.metadata.get(id) || {}
                });
            }
        }

        return results
            .sort((a, b) => b.score - a.score)
            .slice(0, limit);
    }

    async save(): Promise<void> {
        const data = {
            version: 1,
            vectors: Object.fromEntries(this.vectors),
            metadata: Object.fromEntries(this.metadata)
        };
        
        await this.vault.adapter.write(this.STORAGE_FILE, JSON.stringify(data));
    }

    async load(): Promise<void> {
        if (!(await this.vault.adapter.exists(this.STORAGE_FILE))) {
            return;
        }

        try {
            const content = await this.vault.adapter.read(this.STORAGE_FILE);
            const data = JSON.parse(content);
            
            this.vectors = new Map(Object.entries(data.vectors));
            this.metadata = new Map(Object.entries(data.metadata));
            
            console.log(`VectorStore loaded: ${this.vectors.size} documents.`);
        } catch (e) {
            console.error('Failed to load VectorStore:', e);
        }
    }

    async clear(): Promise<void> {
        this.vectors.clear();
        this.metadata.clear();
        await this.save();
    }

    size(): number {
        return this.vectors.size;
    }

    private cosineSimilarity(a: number[], b: number[]): number {
        let dotProduct = 0;
        let normA = 0;
        let normB = 0;

        for (let i = 0; i < a.length; i++) {
            dotProduct += a[i] * b[i];
            normA += a[i] * a[i];
            normB += b[i] * b[i];
        }

        if (normA === 0 || normB === 0) return 0;
        return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
    }
}
