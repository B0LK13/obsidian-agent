import { App, Notice, TFile } from 'obsidian';
import { Tool } from './tools';

export class UpdateNoteTool implements Tool {
    name = 'update_note';
    description = 'Update or append content to an existing note. Input format: "path:Note.md|content:New content to append" or "path:Note.md|replace:Old text|with:New text"';

    constructor(private app: App) {}

    async execute(input: string): Promise<string> {
        try {
            // Parse input
            const pathMatch = input.match(/path:([^|]+)/);
            const contentMatch = input.match(/\|content:(.+)/);
            const replaceMatch = input.match(/\|replace:([^|]+)\|with:(.+)/);
            
            if (!pathMatch) {
                return 'Error: Must specify path (e.g., path:MyNote.md)';
            }
            
            let path = pathMatch[1].trim();
            if (!path.endsWith('.md')) {
                path += '.md';
            }
            
            const file = this.app.vault.getAbstractFileByPath(path);
            if (!(file instanceof TFile)) {
                return `Error: Note "${path}" not found. Use create_note to create it.`;
            }
            
            const currentContent = await this.app.vault.read(file);
            
            let newContent: string;
            
            if (replaceMatch) {
                // Replace mode
                const oldText = replaceMatch[1].trim();
                const newText = replaceMatch[2].trim();
                newContent = currentContent.replace(oldText, newText);
                
                if (newContent === currentContent) {
                    return `Warning: Text "${oldText}" not found in note. No changes made.`;
                }
            } else if (contentMatch) {
                // Append mode
                const contentToAdd = contentMatch[1].trim();
                newContent = currentContent + '\n\n' + contentToAdd;
            } else {
                return 'Error: Must specify either |content: or |replace:|with:';
            }
            
            await this.app.vault.modify(file, newContent);
            
            new Notice(`Updated: ${file.path}`);
            
            return `Successfully updated "${file.path}". Content now has ${newContent.length} characters.`;
        } catch (e: any) {
            return `Error updating note: ${e.message}`;
        }
    }
}
