import { App, TFile } from 'obsidian';
import { VectorStore } from '../vectorStore';
import { EmbeddingService } from '../embeddingService';
import { MemoryService } from '../memoryService';

export interface Tool {
    name: string;
    description: string;
    execute(input: string): Promise<string>;
}

export class SearchVaultTool implements Tool {
    name = 'search_vault';
    description = 'Search the vault for notes relevant to a query. Returns a list of note paths and relevance scores. Input: A search query string.';

    constructor(
        private vectorStore: VectorStore, 
        private embeddingService: EmbeddingService
    ) {}

    async execute(input: string): Promise<string> {
        try {
            const embedding = await this.embeddingService.generateEmbedding(input);
            const results = await this.vectorStore.search(embedding.vector, 10, 0.4);
            
            if (results.length === 0) return "No relevant notes found.";

            return results.map(r => `- ${r.id} (Score: ${(r.score * 100).toFixed(0)}%)`).join('\n');
        } catch (e: any) {
            return `Error searching vault: ${e.message}`;
        }
    }
}

export class ReadNoteTool implements Tool {
    name = 'read_note';
    description = 'Read the content of a specific note. Input: The exact file path of the note (e.g., "Folder/My Note.md").';

    constructor(private app: App) {}

    async execute(input: string): Promise<string> {
        const file = this.app.vault.getAbstractFileByPath(input.trim());
        if (!file || !(file instanceof TFile)) {
            return `Error: Note not found at path "${input}".`;
        }
        
        try {
            const content = await this.app.vault.read(file);
            return `Content of "${file.path}":

${content}`;
        } catch (e: any) {
            return `Error reading note: ${e.message}`;
        }
    }
}

export class ListFilesTool implements Tool {
    name = 'list_files';
    description = 'List all files in a specific folder. Input: The folder path (e.g., "Projects"). Leave empty for root.';

    constructor(private app: App) {}

    async execute(input: string): Promise<string> {
        const folderPath = input.trim() || '/';
        const folder = this.app.vault.getAbstractFileByPath(folderPath);
        
        // Handle root special case or standard folders
        // Obsidian root is empty string path usually
        if (folderPath === '/' || folderPath === '') {
             const files = this.app.vault.getRoot().children;
             return files.map(f => f.path).join('\n');
        }

        // TODO: Type check for TFolder properly if needed, but for now we iterate children if it has them
        if (folder && 'children' in folder) {
             const children = (folder as any).children;
             return children.map((f: any) => f.path).join('\n');
        }

        return `Error: Folder not found at "${folderPath}".`;
    }
}

export class RememberFactTool implements Tool {
    name = 'remember_fact';
    description = 'Save a fact about the user or their preferences to long-term memory. Input: A clear, concise statement of the fact to remember.';

    constructor(private memoryService: MemoryService) {}

    async execute(input: string): Promise<string> {
        try {
            await this.memoryService.addMemory(input);
            return `Fact remembered: "${input}"`;
        } catch (e: any) {
            return `Error remembering fact: ${e.message}`;
        }
    }
}

// Export tool interface for external use
