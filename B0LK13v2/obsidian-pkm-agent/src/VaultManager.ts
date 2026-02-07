import { App, TFile, TFolder, TAbstractFile, normalizePath, Notice, CachedMetadata, FrontMatterCache, prepareSimpleSearch } from 'obsidian';

/**
 * Advanced VaultManager - Comprehensive Obsidian Vault Operations
 * Handles all file operations, metadata, search, templates, and more.
 */
export class VaultManager {
    app: App;
    private templateCache: Map<string, string> = new Map();

    constructor(app: App) {
        this.app = app;
    }

    // ============================================
    // NOTE CRUD OPERATIONS
    // ============================================

    /**
     * Creates a new note with optional frontmatter and template support.
     */
    async createNote(
        title: string, 
        content: string, 
        path: string = '', 
        frontmatter?: Record<string, any>,
        template?: string
    ): Promise<{ success: boolean; path?: string; error?: string }> {
        try {
            const fileName = `${this.sanitizeFileName(title)}.md`;
            const folderPath = normalizePath(path);
            const fullPath = path ? `${folderPath}/${fileName}` : fileName;

            // Ensure folder exists
            if (path) {
                await this.ensureFolder(folderPath);
            }

            // Check if file exists
            if (this.app.vault.getAbstractFileByPath(fullPath)) {
                return { success: false, error: `File "${fullPath}" already exists` };
            }

            // Build content with frontmatter
            let finalContent = content;
            
            // Apply template if specified
            if (template) {
                const templateContent = await this.getTemplate(template);
                if (templateContent) {
                    finalContent = this.processTemplate(templateContent, { title, content, ...frontmatter });
                }
            }

            // Add frontmatter
            if (frontmatter && Object.keys(frontmatter).length > 0) {
                const fm = this.buildFrontmatter(frontmatter);
                finalContent = fm + finalContent;
            }

            await this.app.vault.create(fullPath, finalContent);
            new Notice(`Created: ${title}`);
            return { success: true, path: fullPath };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Reads a note's content and metadata.
     */
    async readNote(nameOrPath: string): Promise<{ 
        success: boolean; 
        content?: string; 
        frontmatter?: FrontMatterCache;
        path?: string;
        error?: string 
    }> {
        const file = this.findFile(nameOrPath);
        if (!file) {
            return { success: false, error: `Note "${nameOrPath}" not found` };
        }

        const content = await this.app.vault.read(file);
        const metadata = this.app.metadataCache.getFileCache(file);
        
        return {
            success: true,
            content,
            frontmatter: metadata?.frontmatter,
            path: file.path
        };
    }

    /**
     * Updates a note with various modes: append, prepend, replace, or smart-merge.
     */
    async updateNote(
        nameOrPath: string, 
        content: string, 
        mode: 'append' | 'prepend' | 'replace' | 'insert-after-heading' = 'append',
        options?: { heading?: string; preserveFrontmatter?: boolean }
    ): Promise<{ success: boolean; path?: string; error?: string }> {
        const file = this.findFile(nameOrPath);
        if (!file) {
            return { success: false, error: `Note "${nameOrPath}" not found` };
        }

        try {
            const currentContent = await this.app.vault.read(file);
            let newContent: string;

            switch (mode) {
                case 'replace':
                    if (options?.preserveFrontmatter) {
                        const fm = this.extractFrontmatter(currentContent);
                        newContent = fm + content;
                    } else {
                        newContent = content;
                    }
                    break;
                case 'prepend':
                    const fm = this.extractFrontmatter(currentContent);
                    const bodyWithoutFm = currentContent.replace(/^---[\s\S]*?---\n?/, '');
                    newContent = fm + content + '\n' + bodyWithoutFm;
                    break;
                case 'insert-after-heading':
                    if (options?.heading) {
                        newContent = this.insertAfterHeading(currentContent, options.heading, content);
                    } else {
                        newContent = currentContent + '\n' + content;
                    }
                    break;
                case 'append':
                default:
                    newContent = currentContent + '\n' + content;
            }

            await this.app.vault.modify(file, newContent);
            new Notice(`Updated: ${file.basename}`);
            return { success: true, path: file.path };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Deletes or trashes a note safely.
     */
    async deleteNote(nameOrPath: string, permanent: boolean = false): Promise<{ success: boolean; error?: string }> {
        const file = this.findFile(nameOrPath);
        if (!file) {
            return { success: false, error: `Note "${nameOrPath}" not found` };
        }

        try {
            if (permanent) {
                await this.app.vault.delete(file);
            } else {
                await this.app.vault.trash(file, true);
            }
            new Notice(`Deleted: ${file.basename}`);
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Renames a note.
     */
    async renameNote(oldPath: string, newName: string): Promise<{ success: boolean; newPath?: string; error?: string }> {
        const file = this.findFile(oldPath);
        if (!file) {
            return { success: false, error: `Note "${oldPath}" not found` };
        }

        try {
            const dir = file.parent?.path || '';
            const newPath = dir ? `${dir}/${this.sanitizeFileName(newName)}.md` : `${this.sanitizeFileName(newName)}.md`;
            await this.app.fileManager.renameFile(file, newPath);
            new Notice(`Renamed to: ${newName}`);
            return { success: true, newPath };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Moves a note to a different folder.
     */
    async moveNote(nameOrPath: string, targetFolder: string): Promise<{ success: boolean; newPath?: string; error?: string }> {
        const file = this.findFile(nameOrPath);
        if (!file) {
            return { success: false, error: `Note "${nameOrPath}" not found` };
        }

        try {
            await this.ensureFolder(targetFolder);
            const newPath = `${targetFolder}/${file.name}`;
            await this.app.fileManager.renameFile(file, newPath);
            new Notice(`Moved to: ${targetFolder}`);
            return { success: true, newPath };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // ============================================
    // SEARCH & DISCOVERY
    // ============================================

    /**
     * Performs full-text search across the vault.
     */
    async searchContent(query: string, options?: { 
        limit?: number; 
        folder?: string;
        includeContent?: boolean 
    }): Promise<{ path: string; matches: string[]; score: number }[]> {
        const searchFn = prepareSimpleSearch(query);
        const files = this.app.vault.getMarkdownFiles();
        const results: { path: string; matches: string[]; score: number }[] = [];
        const limit = options?.limit || 20;

        for (const file of files) {
            if (options?.folder && !file.path.startsWith(options.folder)) {
                continue;
            }

            const content = await this.app.vault.cachedRead(file);
            const result = searchFn(content);
            
            if (result) {
                const matches: string[] = [];
                if (options?.includeContent) {
                    // Extract context around matches
                    const lines = content.split('\n');
                    for (const line of lines) {
                        if (searchFn(line)) {
                            matches.push(line.trim().substring(0, 200));
                        }
                    }
                }
                results.push({
                    path: file.path,
                    matches: matches.slice(0, 3),
                    score: result.score
                });
            }
        }

        // Sort by score (higher is better)
        return results.sort((a, b) => b.score - a.score).slice(0, limit);
    }

    /**
     * Searches by tags.
     */
    searchByTag(tag: string, limit: number = 50): { path: string; tags: string[] }[] {
        const results: { path: string; tags: string[] }[] = [];
        const normalizedTag = tag.startsWith('#') ? tag.slice(1) : tag;
        
        const files = this.app.vault.getMarkdownFiles();
        for (const file of files) {
            const cache = this.app.metadataCache.getFileCache(file);
            const tags = this.getAllTags(cache);
            
            if (tags.some(t => t.toLowerCase().includes(normalizedTag.toLowerCase()))) {
                results.push({ path: file.path, tags });
            }
        }

        return results.slice(0, limit);
    }

    /**
     * Searches by frontmatter properties.
     */
    searchByProperty(property: string, value?: string): { path: string; value: any }[] {
        const results: { path: string; value: any }[] = [];
        const files = this.app.vault.getMarkdownFiles();

        for (const file of files) {
            const cache = this.app.metadataCache.getFileCache(file);
            const fm = cache?.frontmatter;
            
            if (fm && property in fm) {
                if (!value || String(fm[property]).toLowerCase().includes(value.toLowerCase())) {
                    results.push({ path: file.path, value: fm[property] });
                }
            }
        }

        return results;
    }

    /**
     * Gets recently modified files.
     */
    getRecentFiles(limit: number = 10): { path: string; modified: number }[] {
        const files = this.app.vault.getMarkdownFiles();
        return files
            .map(f => ({ path: f.path, modified: f.stat.mtime }))
            .sort((a, b) => b.modified - a.modified)
            .slice(0, limit);
    }

    /**
     * Lists files in a specific folder with optional recursion.
     */
    listFolder(folderPath: string, recursive: boolean = false): { path: string; isFolder: boolean }[] {
        const results: { path: string; isFolder: boolean }[] = [];
        const folder = this.app.vault.getAbstractFileByPath(folderPath);
        
        if (!(folder instanceof TFolder)) {
            return results;
        }

        const traverse = (f: TFolder) => {
            for (const child of f.children) {
                if (child instanceof TFolder) {
                    results.push({ path: child.path, isFolder: true });
                    if (recursive) {
                        traverse(child);
                    }
                } else if (child instanceof TFile) {
                    results.push({ path: child.path, isFolder: false });
                }
            }
        };

        traverse(folder);
        return results;
    }

    /**
     * Gets vault structure as a tree.
     */
    getVaultStructure(maxDepth: number = 3): any {
        const root = this.app.vault.getRoot();
        
        const buildTree = (folder: TFolder, depth: number): any => {
            if (depth > maxDepth) return null;
            
            const node: any = {
                name: folder.name || 'root',
                type: 'folder',
                children: []
            };

            for (const child of folder.children) {
                if (child instanceof TFolder) {
                    const childTree = buildTree(child, depth + 1);
                    if (childTree) node.children.push(childTree);
                } else if (child instanceof TFile && child.extension === 'md') {
                    node.children.push({
                        name: child.basename,
                        type: 'file',
                        path: child.path
                    });
                }
            }

            return node;
        };

        return buildTree(root, 0);
    }

    // ============================================
    // METADATA & FRONTMATTER
    // ============================================

    /**
     * Gets frontmatter for a note.
     */
    getFrontmatter(nameOrPath: string): FrontMatterCache | null {
        const file = this.findFile(nameOrPath);
        if (!file) return null;
        
        const cache = this.app.metadataCache.getFileCache(file);
        return cache?.frontmatter || null;
    }

    /**
     * Updates frontmatter properties.
     */
    async updateFrontmatter(nameOrPath: string, properties: Record<string, any>): Promise<{ success: boolean; error?: string }> {
        const file = this.findFile(nameOrPath);
        if (!file) {
            return { success: false, error: `Note "${nameOrPath}" not found` };
        }

        try {
            await this.app.fileManager.processFrontMatter(file, (fm) => {
                Object.assign(fm, properties);
            });
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Adds tags to a note.
     */
    async addTags(nameOrPath: string, tags: string[]): Promise<{ success: boolean; error?: string }> {
        const file = this.findFile(nameOrPath);
        if (!file) {
            return { success: false, error: `Note "${nameOrPath}" not found` };
        }

        try {
            await this.app.fileManager.processFrontMatter(file, (fm) => {
                const existingTags = Array.isArray(fm.tags) ? fm.tags : (fm.tags ? [fm.tags] : []);
                const normalizedNewTags = tags.map(t => t.startsWith('#') ? t.slice(1) : t);
                fm.tags = [...new Set([...existingTags, ...normalizedNewTags])];
            });
            new Notice(`Added tags to: ${file.basename}`);
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Removes tags from a note.
     */
    async removeTags(nameOrPath: string, tags: string[]): Promise<{ success: boolean; error?: string }> {
        const file = this.findFile(nameOrPath);
        if (!file) {
            return { success: false, error: `Note "${nameOrPath}" not found` };
        }

        try {
            await this.app.fileManager.processFrontMatter(file, (fm) => {
                if (!fm.tags) return;
                const existingTags = Array.isArray(fm.tags) ? fm.tags : [fm.tags];
                const normalizedRemove = tags.map(t => t.startsWith('#') ? t.slice(1) : t);
                fm.tags = existingTags.filter((t: string) => !normalizedRemove.includes(t));
            });
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // ============================================
    // LINKS & RELATIONSHIPS
    // ============================================

    /**
     * Gets all links from a note (outgoing).
     */
    getOutgoingLinks(nameOrPath: string): { link: string; displayText?: string }[] {
        const file = this.findFile(nameOrPath);
        if (!file) return [];

        const cache = this.app.metadataCache.getFileCache(file);
        const links: { link: string; displayText?: string }[] = [];

        if (cache?.links) {
            for (const link of cache.links) {
                links.push({
                    link: link.link,
                    displayText: link.displayText
                });
            }
        }

        return links;
    }

    /**
     * Gets all backlinks to a note (incoming).
     */
    getBacklinks(nameOrPath: string): { path: string; context?: string }[] {
        const file = this.findFile(nameOrPath);
        if (!file) return [];

        const backlinks: { path: string; context?: string }[] = [];
        const allFiles = this.app.vault.getMarkdownFiles();

        for (const f of allFiles) {
            if (f.path === file.path) continue;
            
            const cache = this.app.metadataCache.getFileCache(f);
            if (cache?.links) {
                for (const link of cache.links) {
                    const resolved = this.app.metadataCache.getFirstLinkpathDest(link.link, f.path);
                    if (resolved?.path === file.path) {
                        backlinks.push({ path: f.path });
                        break;
                    }
                }
            }
        }

        return backlinks;
    }

    /**
     * Creates a link between two notes.
     */
    async createLink(fromNote: string, toNote: string, displayText?: string): Promise<{ success: boolean; error?: string }> {
        const sourceFile = this.findFile(fromNote);
        const targetFile = this.findFile(toNote);
        
        if (!sourceFile) {
            return { success: false, error: `Source note "${fromNote}" not found` };
        }
        if (!targetFile) {
            return { success: false, error: `Target note "${toNote}" not found` };
        }

        try {
            const link = this.app.fileManager.generateMarkdownLink(targetFile, sourceFile.path, undefined, displayText);
            const content = await this.app.vault.read(sourceFile);
            await this.app.vault.modify(sourceFile, content + '\n' + link);
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    /**
     * Gets orphan notes (no incoming or outgoing links).
     */
    getOrphanNotes(): string[] {
        const orphans: string[] = [];
        const files = this.app.vault.getMarkdownFiles();

        for (const file of files) {
            const cache = this.app.metadataCache.getFileCache(file);
            const hasOutgoing = (cache?.links?.length || 0) > 0;
            const backlinks = this.getBacklinks(file.path);
            
            if (!hasOutgoing && backlinks.length === 0) {
                orphans.push(file.path);
            }
        }

        return orphans;
    }

    // ============================================
    // TEMPLATES
    // ============================================

    /**
     * Gets a template by name.
     */
    async getTemplate(name: string): Promise<string | null> {
        // Check cache
        if (this.templateCache.has(name)) {
            return this.templateCache.get(name)!;
        }

        // Search in template folders
        const templatePaths = [
            `pkm/_meta/_templates/${name}.md`,
            `_meta/_templates/${name}.md`,
            `templates/${name}.md`,
            `${name}.md`
        ];

        for (const path of templatePaths) {
            const file = this.app.vault.getAbstractFileByPath(path);
            if (file instanceof TFile) {
                const content = await this.app.vault.read(file);
                this.templateCache.set(name, content);
                return content;
            }
        }

        return null;
    }

    /**
     * Lists available templates.
     */
    listTemplates(): string[] {
        const templates: string[] = [];
        const templateFolders = ['pkm/_meta/_templates', '_meta/_templates', 'templates'];

        for (const folderPath of templateFolders) {
            const folder = this.app.vault.getAbstractFileByPath(folderPath);
            if (folder instanceof TFolder) {
                for (const child of folder.children) {
                    if (child instanceof TFile && child.extension === 'md') {
                        templates.push(child.basename);
                    }
                }
            }
        }

        return [...new Set(templates)];
    }

    /**
     * Processes template variables.
     */
    processTemplate(template: string, variables: Record<string, any>): string {
        let result = template;
        const now = new Date();

        // Built-in variables
        const builtIn: Record<string, string> = {
            '{{date}}': now.toISOString().split('T')[0],
            '{{time}}': now.toTimeString().split(' ')[0],
            '{{datetime}}': now.toISOString(),
            '{{timestamp}}': now.toISOString().replace(/[-:]/g, '').split('.')[0],
            '{{year}}': String(now.getFullYear()),
            '{{month}}': String(now.getMonth() + 1).padStart(2, '0'),
            '{{day}}': String(now.getDate()).padStart(2, '0'),
        };

        // Replace built-in variables
        for (const [key, value] of Object.entries(builtIn)) {
            result = result.split(key).join(value);
        }

        // Replace custom variables
        for (const [key, value] of Object.entries(variables)) {
            result = result.split(`{{${key}}}`).join(String(value));
        }

        return result;
    }

    /**
     * Creates note from template.
     */
    async createFromTemplate(
        template: string, 
        title: string, 
        path: string = '', 
        variables?: Record<string, any>
    ): Promise<{ success: boolean; path?: string; error?: string }> {
        const templateContent = await this.getTemplate(template);
        if (!templateContent) {
            return { success: false, error: `Template "${template}" not found` };
        }

        const content = this.processTemplate(templateContent, { title, ...variables });
        return this.createNote(title, content, path);
    }

    // ============================================
    // STATISTICS & ANALYTICS
    // ============================================

    /**
     * Gets vault statistics.
     */
    getVaultStats(): {
        totalNotes: number;
        totalFolders: number;
        totalTags: number;
        totalLinks: number;
        avgNoteLength: number;
        notesPerFolder: Record<string, number>;
    } {
        const files = this.app.vault.getMarkdownFiles();
        const allTags = new Set<string>();
        let totalLinks = 0;
        let totalLength = 0;
        const notesPerFolder: Record<string, number> = {};

        for (const file of files) {
            const cache = this.app.metadataCache.getFileCache(file);
            
            // Tags
            const tags = this.getAllTags(cache);
            tags.forEach(t => allTags.add(t));
            
            // Links
            totalLinks += cache?.links?.length || 0;
            
            // Length
            totalLength += file.stat.size;
            
            // Folder count
            const folder = file.parent?.path || 'root';
            notesPerFolder[folder] = (notesPerFolder[folder] || 0) + 1;
        }

        // Count folders
        let folderCount = 0;
        const countFolders = (folder: TFolder) => {
            folderCount++;
            for (const child of folder.children) {
                if (child instanceof TFolder) {
                    countFolders(child);
                }
            }
        };
        countFolders(this.app.vault.getRoot());

        return {
            totalNotes: files.length,
            totalFolders: folderCount,
            totalTags: allTags.size,
            totalLinks,
            avgNoteLength: files.length > 0 ? Math.round(totalLength / files.length) : 0,
            notesPerFolder
        };
    }

    /**
     * Gets all unique tags in the vault.
     */
    getAllVaultTags(): { tag: string; count: number }[] {
        const tagCounts: Record<string, number> = {};
        const files = this.app.vault.getMarkdownFiles();

        for (const file of files) {
            const cache = this.app.metadataCache.getFileCache(file);
            const tags = this.getAllTags(cache);
            
            for (const tag of tags) {
                tagCounts[tag] = (tagCounts[tag] || 0) + 1;
            }
        }

        return Object.entries(tagCounts)
            .map(([tag, count]) => ({ tag, count }))
            .sort((a, b) => b.count - a.count);
    }

    // ============================================
    // DAILY NOTES
    // ============================================

    /**
     * Creates or gets today's daily note.
     */
    async getDailyNote(date?: Date): Promise<{ success: boolean; path?: string; content?: string; created?: boolean; error?: string }> {
        const d = date || new Date();
        const year = d.getFullYear();
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const monthName = d.toLocaleString('default', { month: 'long' }).toLowerCase();
        const day = String(d.getDate()).padStart(2, '0');
        
        const fileName = `${year}-${month}-${day}`;
        const folderPath = `pkm/_meta/_daily_notes/${year}/${month}-${monthName}`;
        const fullPath = `${folderPath}/${fileName}.md`;

        // Check if exists
        const existing = this.app.vault.getAbstractFileByPath(fullPath);
        if (existing instanceof TFile) {
            const content = await this.app.vault.read(existing);
            return { success: true, path: fullPath, content, created: false };
        }

        // Create from template
        const result = await this.createFromTemplate('daily-note', fileName, folderPath, {
            date: `${year}-${month}-${day}`,
            day_of_week: d.toLocaleString('default', { weekday: 'long' })
        });

        if (result.success) {
            return { success: true, path: result.path, created: true };
        }

        // Fallback: create basic daily note
        const content = `---
date: ${year}-${month}-${day}
type: daily-note
---

# ${year}-${month}-${day}

## Tasks
- [ ] 

## Notes

## Reflections

`;
        return this.createNote(fileName, content, folderPath);
    }

    // ============================================
    // HELPER METHODS
    // ============================================

    /**
     * Finds a file by name or path (with fuzzy matching).
     */
    findFile(nameOrPath: string): TFile | null {
        const normalized = normalizePath(nameOrPath);
        
        // Try exact path
        let file = this.app.vault.getAbstractFileByPath(normalized);
        if (file instanceof TFile) return file;
        
        // Try with .md extension
        file = this.app.vault.getAbstractFileByPath(normalized + '.md');
        if (file instanceof TFile) return file;

        // Search by basename (case-insensitive)
        const files = this.app.vault.getMarkdownFiles();
        const found = files.find(f => 
            f.basename.toLowerCase() === nameOrPath.toLowerCase() ||
            f.path.toLowerCase() === nameOrPath.toLowerCase()
        );
        
        return found || null;
    }

    /**
     * Ensures a folder path exists, creating intermediate folders as needed.
     */
    async ensureFolder(path: string): Promise<void> {
        const parts = normalizePath(path).split('/');
        let current = '';
        
        for (const part of parts) {
            current = current ? `${current}/${part}` : part;
            const existing = this.app.vault.getAbstractFileByPath(current);
            
            if (!existing) {
                await this.app.vault.createFolder(current);
            } else if (!(existing instanceof TFolder)) {
                throw new Error(`Path "${current}" exists but is not a folder`);
            }
        }
    }

    /**
     * Sanitizes a filename.
     */
    private sanitizeFileName(name: string): string {
        return name.replace(/[\\/:*?"<>|]/g, '-').trim();
    }

    /**
     * Extracts all tags from cache (frontmatter + inline).
     */
    private getAllTags(cache: CachedMetadata | null): string[] {
        if (!cache) return [];
        
        const tags: string[] = [];
        
        // Frontmatter tags
        if (cache.frontmatter?.tags) {
            const fmTags = Array.isArray(cache.frontmatter.tags) 
                ? cache.frontmatter.tags 
                : [cache.frontmatter.tags];
            tags.push(...fmTags.map(t => String(t)));
        }
        
        // Inline tags
        if (cache.tags) {
            tags.push(...cache.tags.map(t => t.tag.slice(1))); // Remove # prefix
        }

        return [...new Set(tags)];
    }

    /**
     * Builds frontmatter string from object.
     */
    private buildFrontmatter(properties: Record<string, any>): string {
        const lines = ['---'];
        
        for (const [key, value] of Object.entries(properties)) {
            if (Array.isArray(value)) {
                lines.push(`${key}:`);
                for (const item of value) {
                    lines.push(`  - ${item}`);
                }
            } else if (value !== undefined && value !== null) {
                lines.push(`${key}: ${value}`);
            }
        }
        
        lines.push('---', '');
        return lines.join('\n');
    }

    /**
     * Extracts frontmatter from content.
     */
    private extractFrontmatter(content: string): string {
        const match = content.match(/^---[\s\S]*?---\n?/);
        return match ? match[0] : '';
    }

    /**
     * Inserts content after a specific heading.
     */
    private insertAfterHeading(content: string, heading: string, newContent: string): string {
        const lines = content.split('\n');
        const headingPattern = new RegExp(`^#{1,6}\\s+${heading}\\s*$`, 'i');
        
        for (let i = 0; i < lines.length; i++) {
            if (headingPattern.test(lines[i])) {
                // Find next heading or end
                let insertIndex = i + 1;
                while (insertIndex < lines.length && !lines[insertIndex].match(/^#{1,6}\s/)) {
                    insertIndex++;
                }
                lines.splice(insertIndex, 0, '', newContent);
                return lines.join('\n');
            }
        }

        // Heading not found, append
        return content + '\n' + newContent;
    }

    /**
     * Gets current active file.
     */
    getActiveFile(): TFile | null {
        return this.app.workspace.getActiveFile();
    }

    /**
     * Opens a file in the editor.
     */
    async openFile(nameOrPath: string): Promise<{ success: boolean; error?: string }> {
        const file = this.findFile(nameOrPath);
        if (!file) {
            return { success: false, error: `Note "${nameOrPath}" not found` };
        }

        try {
            await this.app.workspace.openLinkText(file.path, '', false);
            return { success: true };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }
}
