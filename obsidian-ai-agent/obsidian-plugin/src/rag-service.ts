/**
 * RAG (Retrieval Augmented Generation) Service
 * Indexes vault notes and retrieves relevant context
 */

import { App, TFile, TFolder } from 'obsidian';

export class RAGService {
    private app: App;
    private settings: any;
    private isIndexing: boolean = false;
    private indexedCount: number = 0;

    constructor(app: App, settings: any) {
        this.app = app;
        this.settings = settings;
    }

    /**
     * Index all markdown files in the vault
     */
    async indexVault(): Promise<void> {
        if (this.isIndexing) {
            throw new Error('Indexing already in progress');
        }

        this.isIndexing = true;
        this.indexedCount = 0;

        try {
            const files = this.app.vault.getMarkdownFiles();
            const batchSize = 10;

            for (let i = 0; i < files.length; i += batchSize) {
                const batch = files.slice(i, i + batchSize);
                await this.indexBatch(batch);
                
                // Progress update
                console.log(`Indexed ${this.indexedCount}/${files.length} files`);
            }
        } finally {
            this.isIndexing = false;
        }
    }

    /**
     * Index a batch of files
     */
    private async indexBatch(files: TFile[]): Promise<void> {
        const documents = [];

        for (const file of files) {
            try {
                const content = await this.app.vault.read(file);
                const embedding = await this.getEmbedding(content);

                documents.push({
                    id: file.path,
                    content: content.substring(0, 5000), // Limit content size
                    metadata: {
                        path: file.path,
                        title: file.basename,
                        mtime: file.stat.mtime
                    },
                    embedding
                });

                this.indexedCount++;
            } catch (error) {
                console.error(`Failed to index ${file.path}:`, error);
            }
        }

        // Send to vector DB via AI client
        if (documents.length > 0) {
            // Import AI client dynamically to avoid circular dependencies
            const { LocalAIClient } = await import('./ai-client');
            const client = new LocalAIClient(this.settings);
            await client.addToVectorDB(documents);
        }
    }

    /**
     * Index a single file
     */
    async indexFile(file: TFile): Promise<void> {
        try {
            const content = await this.app.vault.read(file);
            const embedding = await this.getEmbedding(content);

            const { LocalAIClient } = await import('./ai-client');
            const client = new LocalAIClient(this.settings);
            
            await client.addToVectorDB([{
                id: file.path,
                content: content.substring(0, 5000),
                metadata: {
                    path: file.path,
                    title: file.basename,
                    mtime: file.stat.mtime
                },
                embedding
            }]);
        } catch (error) {
            console.error(`Failed to index ${file.path}:`, error);
            throw error;
        }
    }

    /**
     * Get embedding for text
     */
    private async getEmbedding(text: string): Promise<number[]> {
        const { LocalAIClient } = await import('./ai-client');
        const client = new LocalAIClient(this.settings);
        return await client.embed(text);
    }

    /**
     * Get relevant context for a query
     */
    async getRelevantContext(query: string, nResults: number = 5): Promise<string> {
        try {
            const embedding = await this.getEmbedding(query);
            
            const { LocalAIClient } = await import('./ai-client');
            const client = new LocalAIClient(this.settings);
            const results = await client.queryVectorDB(embedding, nResults);

            // Format context
            const contextParts = results.map((result: any) => {
                return `Note: ${result.metadata?.title || result.id}\n${result.content?.substring(0, 1000) || ''}`;
            });

            return contextParts.join('\n\n---\n\n');
        } catch (error) {
            console.error('Failed to get relevant context:', error);
            return '';
        }
    }

    /**
     * Find related notes
     */
    async findRelatedNotes(content: string, nResults: number = 5): Promise<TFile[]> {
        try {
            const embedding = await this.getEmbedding(content);
            
            const { LocalAIClient } = await import('./ai-client');
            const client = new LocalAIClient(this.settings);
            const results = await client.queryVectorDB(embedding, nResults);

            // Convert to TFile references
            const files: TFile[] = [];
            for (const result of results) {
                const file = this.app.vault.getAbstractFileByPath(result.id);
                if (file instanceof TFile) {
                    files.push(file);
                }
            }

            return files;
        } catch (error) {
            console.error('Failed to find related notes:', error);
            return [];
        }
    }

    /**
     * Search notes by semantic similarity
     */
    async semanticSearch(query: string, nResults: number = 10): Promise<Array<{file: TFile; score: number}>> {
        try {
            const embedding = await this.getEmbedding(query);
            
            const { LocalAIClient } = await import('./ai-client');
            const client = new LocalAIClient(this.settings);
            const results = await client.queryVectorDB(embedding, nResults);

            const matches: Array<{file: TFile; score: number}> = [];
            for (const result of results) {
                const file = this.app.vault.getAbstractFileByPath(result.id);
                if (file instanceof TFile) {
                    matches.push({
                        file,
                        score: 1 - (result.distance || 0) // Convert distance to similarity
                    });
                }
            }

            return matches;
        } catch (error) {
            console.error('Semantic search failed:', error);
            return [];
        }
    }
}
