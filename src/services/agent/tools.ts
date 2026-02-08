import { App, TFile } from 'obsidian';
import { VectorStore } from '../vectorStore';
import { EmbeddingService } from '../embeddingService';
import { MemoryService, MemoryLayer } from '../memoryService';

export interface Tool {
    name: string;
    description: string;
    schema?: any;
    execute(input: string): Promise<string>;
}

export class SearchVaultTool implements Tool {
    name = 'search_vault';
    description = 'Search the vault for notes relevant to a query. Returns a list of note paths and relevance scores.';
    schema = {
        type: 'object',
        properties: {
            query: {
                type: 'string',
                description: 'A search query string to find relevant notes.'
            }
        },
        required: ['query']
    };

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
    description = 'Read the content of a specific note.';
    schema = {
        type: 'object',
        properties: {
            path: {
                type: 'string',
                description: 'The exact file path of the note to read (e.g., "Folder/My Note.md").'
            }
        },
        required: ['path']
    };

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
    description = 'List all files in a specific folder.';
    schema = {
        type: 'object',
        properties: {
            path: {
                type: 'string',
                description: 'The folder path to list (e.g., "Projects"). Leave empty for root.'
            }
        }
    };

    constructor(private app: App) {}

    async execute(input: string): Promise<string> {
        const folderPath = input.trim() || '/';
        const folder = this.app.vault.getAbstractFileByPath(folderPath);

        if (folderPath === '/' || folderPath === '') {
             const files = this.app.vault.getRoot().children;
             return files.map(f => f.path).join('\n');
        }

        if (folder && 'children' in folder) {
             const children = (folder as any).children;
             return children.map((f: any) => f.path).join('\n');
        }

        return `Error: Folder not found at "${folderPath}".`;
    }
}

export class RememberFactTool implements Tool {
    name = 'remember';
    description = 'Save information to memory.';
    schema = {
        type: 'object',
        properties: {
            text: {
                type: 'string',
                description: 'The information to save.'
            },
            layer: {
                type: 'string',
                enum: ['user', 'session', 'long_term'],
                description: 'The memory layer to save to. "user" (preferences), "session" (current task), "long_term" (facts).'
            }
        },
        required: ['text']
    };

    constructor(private memoryService: MemoryService) {}

    async execute(input: string): Promise<string> {
        try {
            let layer = MemoryLayer.LONG_TERM;
            let text = input;

            if (input.includes('|')) {
                const parts = input.split('|');
                const layerInput = parts[0].trim().toLowerCase();
                text = parts.slice(1).join('|').trim();

                if (layerInput === 'user') layer = MemoryLayer.USER;
                else if (layerInput === 'session') layer = MemoryLayer.SESSION;
            }

            await this.memoryService.addMemory(text, layer);
            return `Information saved to ${layer} memory: "${text}"`;
        } catch (e: any) {
            return `Error saving to memory: ${e.message}`;
        }
    }
}
