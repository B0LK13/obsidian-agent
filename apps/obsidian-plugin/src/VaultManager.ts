/**
 * Vault management utilities for PKM Agent plugin.
 */

import { App, TFile, TFolder } from 'obsidian';

export interface VaultResult {
    success: boolean;
    message?: string;
    path?: string;
    content?: string;
    created?: boolean;
    files?: string[];
}

export class VaultManager {
    private app: App;

    constructor(app: App) {
        this.app = app;
    }

    async createNote(path: string, content: string): Promise<VaultResult> {
        try {
            const folderPath = path.substring(0, path.lastIndexOf('/'));
            if (folderPath) {
                await this.ensureFolder(folderPath);
            }

            const existing = this.app.vault.getAbstractFileByPath(path);
            if (existing) {
                return { success: false, message: `File already exists: ${path}` };
            }

            await this.app.vault.create(path, content);
            return { success: true, path, created: true };
        } catch (error) {
            return { success: false, message: `Failed to create note: ${error}` };
        }
    }

    async readNote(path: string): Promise<VaultResult> {
        try {
            const file = this.app.vault.getAbstractFileByPath(path);
            if (!file || !(file instanceof TFile)) {
                return { success: false, message: `File not found: ${path}` };
            }

            const content = await this.app.vault.read(file);
            return { success: true, path, content };
        } catch (error) {
            return { success: false, message: `Failed to read note: ${error}` };
        }
    }

    async updateNote(path: string, content: string): Promise<VaultResult> {
        try {
            const file = this.app.vault.getAbstractFileByPath(path);
            if (!file || !(file instanceof TFile)) {
                return { success: false, message: `File not found: ${path}` };
            }

            await this.app.vault.modify(file, content);
            return { success: true, path };
        } catch (error) {
            return { success: false, message: `Failed to update note: ${error}` };
        }
    }

    async deleteNote(path: string): Promise<VaultResult> {
        try {
            const file = this.app.vault.getAbstractFileByPath(path);
            if (!file || !(file instanceof TFile)) {
                return { success: false, message: `File not found: ${path}` };
            }

            await this.app.vault.delete(file);
            return { success: true, path };
        } catch (error) {
            return { success: false, message: `Failed to delete note: ${error}` };
        }
    }

    async searchNotes(query: string): Promise<VaultResult> {
        try {
            const files = this.app.vault.getMarkdownFiles();
            const results: string[] = [];

            for (const file of files) {
                const content = await this.app.vault.cachedRead(file);
                if (content.toLowerCase().includes(query.toLowerCase()) ||
                    file.basename.toLowerCase().includes(query.toLowerCase())) {
                    results.push(file.path);
                }
            }

            return { success: true, files: results };
        } catch (error) {
            return { success: false, message: `Search failed: ${error}` };
        }
    }

    async getDailyNote(): Promise<VaultResult> {
        try {
            const today = new Date();
            const dateStr = today.toISOString().split('T')[0];
            const path = `Daily Notes/${dateStr}.md`;

            const existing = this.app.vault.getAbstractFileByPath(path);
            if (existing) {
                return { success: true, path, created: false };
            }

            const content = `# ${dateStr}\n\n## Tasks\n- [ ] \n\n## Notes\n\n## Journal\n`;
            await this.ensureFolder('Daily Notes');
            await this.app.vault.create(path, content);

            return { success: true, path, created: true };
        } catch (error) {
            return { success: false, message: `Failed to get daily note: ${error}` };
        }
    }

    async getVaultStats(): Promise<Record<string, any>> {
        const files = this.app.vault.getMarkdownFiles();
        const folders = this.app.vault.getAllLoadedFiles().filter(f => f instanceof TFolder);

        let totalWords = 0;
        const tags = new Set<string>();

        for (const file of files) {
            const cache = this.app.metadataCache.getFileCache(file);
            if (cache?.tags) {
                cache.tags.forEach(t => tags.add(t.tag));
            }
            const content = await this.app.vault.cachedRead(file);
            totalWords += content.split(/\s+/).length;
        }

        return {
            totalNotes: files.length,
            totalFolders: folders.length,
            totalWords,
            uniqueTags: tags.size,
        };
    }

    private async ensureFolder(path: string): Promise<void> {
        const existing = this.app.vault.getAbstractFileByPath(path);
        if (!existing) {
            await this.app.vault.createFolder(path);
        }
    }
}
