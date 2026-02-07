import { App, Notice } from 'obsidian';
import { EmbeddingService } from './embeddingService';
import { VectorStore } from './vectorStore';

export class IndexingService {
    private app: App;
    private embeddingService: EmbeddingService;
    private vectorStore: VectorStore;

    constructor(app: App, embeddingService: EmbeddingService, vectorStore: VectorStore) {
        this.app = app;
        this.embeddingService = embeddingService;
        this.vectorStore = vectorStore;
    }

    async indexVault(forceRebuild: boolean = false): Promise<void> {
        const files = this.app.vault.getMarkdownFiles();
        const total = files.length;
        let processed = 0;
        let indexed = 0;
        let failed = 0;
        let skipped = 0;

        new Notice(`Starting vault index... (${total} files)`);

        for (const file of files) {
            processed++;
            
            // simple progress check
            if (processed % 10 === 0) {
                 new Notice(`Indexing: ${processed}/${total} files...`, 2000);
            }

            try {
                // Check if already indexed and up to date
                const existing = this.vectorStore.get(file.path);
                if (!forceRebuild && existing && existing.metadata.mtime === file.stat.mtime) {
                    skipped++;
                    continue;
                }

                const content = await this.app.vault.read(file);
                if (!content.trim()) {
                    skipped++;
                    continue;
                }

                // Chunking? For Phase 1, we just embed the whole note (truncated by API limit usually).
                // OpenAI text-embedding-3-small has 8191 token limit.
                // We should probably truncate content to ~8000 tokens (approx 32000 chars).
                const truncatedContent = content.substring(0, 30000); 

                const embedding = await this.embeddingService.generateEmbedding(truncatedContent);

                await this.vectorStore.add({
                    id: file.path,
                    vector: embedding.vector,
                    content: truncatedContent, 
                    metadata: {
                        mtime: file.stat.mtime,
                        basename: file.basename,
                        path: file.path
                    }
                });
                
                indexed++;
            } catch (e) {
                console.error(`Failed to index ${file.path}`, e);
                failed++;
            }
        }

        await this.vectorStore.save();
        new Notice(`Indexing complete!\nIndexed: ${indexed}\nSkipped: ${skipped}\nFailed: ${failed}`);
    }
}