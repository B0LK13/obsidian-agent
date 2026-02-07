import { App, Notice, TFile } from 'obsidian';
import { Tool } from './tools';

export class CreateNoteTool implements Tool {
    name = 'create_note';
    description = 'Create a new note in the vault. Input format: "path:Title of Note|content:Content here" or just the title.';

    constructor(private app: App) {}

    async execute(input: string): Promise<string> {
        try {
            let path = '';
            let content = '';
            
            // Parse input
            if (input.includes('path:') && input.includes('|content:')) {
                const parts = input.split('|content:');
                path = parts[0].replace('path:', '').trim();
                content = parts[1].trim();
            } else if (input.includes('|')) {
                // Format: title|content
                const [title, contentPart] = input.split('|');
                path = `${title.trim()}.md`;
                content = contentPart.trim();
            } else {
                // Just a title
                path = `${input.trim()}.md`;
                content = `# ${input.trim()}\n\nCreated by Obsidian Agent\n`;
            }
            
            // Ensure .md extension
            if (!path.endsWith('.md')) {
                path += '.md';
            }
            
            // Check if file exists
            const existing = this.app.vault.getAbstractFileByPath(path);
            if (existing instanceof TFile) {
                return `Error: Note "${path}" already exists. Use read_note to view it.`;
            }
            
            // Create the file
            const file = await this.app.vault.create(path, content);
            
            new Notice(`Created note: ${file.path}`);
            
            return `Successfully created note "${file.path}" with ${content.length} characters.`;
        } catch (e: any) {
            return `Error creating note: ${e.message}`;
        }
    }
}
