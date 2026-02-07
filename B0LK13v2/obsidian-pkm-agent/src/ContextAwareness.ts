import { App, TFile, WorkspaceLeaf, MarkdownView } from 'obsidian';
import { VaultManager } from './VaultManager';
import { KnowledgeGraph } from './KnowledgeGraph';

/**
 * Current context snapshot
 */
interface ContextSnapshot {
    timestamp: number;
    activeFile: {
        path: string;
        title: string;
        content: string;
        frontmatter: Record<string, any> | null;
        tags: string[];
        wordCount: number;
    } | null;
    selectedText: string | null;
    cursorPosition: { line: number; ch: number } | null;
    currentHeading: string | null;
    recentFiles: string[];
    openTabs: string[];
    relatedNotes: string[];
}

/**
 * File change event
 */
interface FileChangeEvent {
    type: 'created' | 'modified' | 'deleted' | 'renamed';
    path: string;
    oldPath?: string;
    timestamp: number;
}

/**
 * ContextAwareness - Monitors and understands the user's current working context
 * Enables the agent to proactively assist based on what the user is doing.
 */
export class ContextAwareness {
    private app: App;
    private vaultManager: VaultManager;
    private knowledgeGraph: KnowledgeGraph;
    private currentContext: ContextSnapshot | null = null;
    private contextHistory: ContextSnapshot[] = [];
    private fileChanges: FileChangeEvent[] = [];
    private maxHistoryLength: number = 20;
    private onContextChangeCallbacks: ((context: ContextSnapshot) => void)[] = [];

    constructor(app: App, vaultManager: VaultManager, knowledgeGraph: KnowledgeGraph) {
        this.app = app;
        this.vaultManager = vaultManager;
        this.knowledgeGraph = knowledgeGraph;
        
        this.setupEventListeners();
    }

    // ============================================
    // EVENT LISTENERS
    // ============================================

    /**
     * Sets up event listeners for context changes.
     */
    private setupEventListeners(): void {
        // File opened
        this.app.workspace.on('file-open', (file) => {
            this.updateContext();
        });

        // Active leaf changed
        this.app.workspace.on('active-leaf-change', (leaf) => {
            this.updateContext();
        });

        // File modifications
        this.app.vault.on('create', (file) => {
            if (file instanceof TFile) {
                this.recordFileChange('created', file.path);
            }
        });

        this.app.vault.on('modify', (file) => {
            if (file instanceof TFile) {
                this.recordFileChange('modified', file.path);
            }
        });

        this.app.vault.on('delete', (file) => {
            if (file instanceof TFile) {
                this.recordFileChange('deleted', file.path);
            }
        });

        this.app.vault.on('rename', (file, oldPath) => {
            if (file instanceof TFile) {
                this.recordFileChange('renamed', file.path, oldPath);
            }
        });
    }

    /**
     * Records a file change event.
     */
    private recordFileChange(type: FileChangeEvent['type'], path: string, oldPath?: string): void {
        this.fileChanges.push({
            type,
            path,
            oldPath,
            timestamp: Date.now()
        });

        // Keep only recent changes
        if (this.fileChanges.length > 100) {
            this.fileChanges = this.fileChanges.slice(-50);
        }
    }

    // ============================================
    // CONTEXT MANAGEMENT
    // ============================================

    /**
     * Updates the current context snapshot.
     */
    async updateContext(): Promise<ContextSnapshot> {
        const activeFile = this.app.workspace.getActiveFile();
        const activeLeaf = this.app.workspace.activeLeaf;
        
        let fileContext: ContextSnapshot['activeFile'] = null;
        let selectedText: string | null = null;
        let cursorPosition: { line: number; ch: number } | null = null;
        let currentHeading: string | null = null;

        if (activeFile) {
            const content = await this.app.vault.cachedRead(activeFile);
            const cache = this.app.metadataCache.getFileCache(activeFile);
            
            // Extract tags
            const tags: string[] = [];
            if (cache?.frontmatter?.tags) {
                const fmTags = Array.isArray(cache.frontmatter.tags) 
                    ? cache.frontmatter.tags 
                    : [cache.frontmatter.tags];
                tags.push(...fmTags.map(t => String(t)));
            }
            if (cache?.tags) {
                tags.push(...cache.tags.map(t => t.tag.slice(1)));
            }

            fileContext = {
                path: activeFile.path,
                title: activeFile.basename,
                content: content.substring(0, 5000), // Limit for context
                frontmatter: cache?.frontmatter || null,
                tags: [...new Set(tags)],
                wordCount: content.split(/\s+/).length
            };

            // Get editor context if available
            if (activeLeaf?.view instanceof MarkdownView) {
                const editor = activeLeaf.view.editor;
                selectedText = editor.getSelection() || null;
                cursorPosition = editor.getCursor();
                
                // Find current heading
                if (cursorPosition && cache?.headings) {
                    for (let i = cache.headings.length - 1; i >= 0; i--) {
                        if (cache.headings[i].position.start.line <= cursorPosition.line) {
                            currentHeading = cache.headings[i].heading;
                            break;
                        }
                    }
                }
            }
        }

        // Get recent files
        const recentFiles = this.vaultManager.getRecentFiles(5).map(f => f.path);

        // Get open tabs
        const openTabs: string[] = [];
        this.app.workspace.iterateAllLeaves((leaf) => {
            if (leaf.view instanceof MarkdownView && leaf.view.file) {
                openTabs.push(leaf.view.file.path);
            }
        });

        // Get related notes
        let relatedNotes: string[] = [];
        if (activeFile) {
            try {
                const related = await this.knowledgeGraph.findRelated(activeFile.path, { limit: 5 });
                relatedNotes = related.map(r => r.path);
            } catch (e) {
                // Knowledge graph may not be built yet
            }
        }

        const context: ContextSnapshot = {
            timestamp: Date.now(),
            activeFile: fileContext,
            selectedText,
            cursorPosition,
            currentHeading,
            recentFiles,
            openTabs: [...new Set(openTabs)],
            relatedNotes
        };

        // Store in history
        if (this.currentContext) {
            this.contextHistory.push(this.currentContext);
            if (this.contextHistory.length > this.maxHistoryLength) {
                this.contextHistory.shift();
            }
        }

        this.currentContext = context;

        // Notify listeners
        for (const callback of this.onContextChangeCallbacks) {
            callback(context);
        }

        return context;
    }

    /**
     * Gets the current context.
     */
    getContext(): ContextSnapshot | null {
        return this.currentContext;
    }

    /**
     * Gets the current context, updating if stale.
     */
    async getOrUpdateContext(maxAge: number = 5000): Promise<ContextSnapshot> {
        if (!this.currentContext || (Date.now() - this.currentContext.timestamp) > maxAge) {
            return this.updateContext();
        }
        return this.currentContext;
    }

    /**
     * Registers a callback for context changes.
     */
    onContextChange(callback: (context: ContextSnapshot) => void): void {
        this.onContextChangeCallbacks.push(callback);
    }

    // ============================================
    // CONTEXT ANALYSIS
    // ============================================

    /**
     * Gets a text summary of the current context for the LLM.
     */
    async getContextSummary(): Promise<string> {
        const context = await this.getOrUpdateContext();
        const parts: string[] = [];

        if (context.activeFile) {
            parts.push(`**Currently viewing:** ${context.activeFile.path}`);
            parts.push(`**Title:** ${context.activeFile.title}`);
            
            if (context.activeFile.tags.length > 0) {
                parts.push(`**Tags:** ${context.activeFile.tags.map(t => `#${t}`).join(', ')}`);
            }

            if (context.currentHeading) {
                parts.push(`**Current section:** ${context.currentHeading}`);
            }

            if (context.selectedText) {
                parts.push(`**Selected text:** "${context.selectedText.substring(0, 200)}${context.selectedText.length > 200 ? '...' : ''}"`);
            }

            parts.push(`**Word count:** ${context.activeFile.wordCount}`);
        } else {
            parts.push('**No file currently open**');
        }

        if (context.recentFiles.length > 0) {
            parts.push(`\n**Recently edited:**`);
            for (const file of context.recentFiles) {
                parts.push(`- ${file}`);
            }
        }

        if (context.relatedNotes.length > 0) {
            parts.push(`\n**Related notes:**`);
            for (const note of context.relatedNotes) {
                parts.push(`- ${note}`);
            }
        }

        return parts.join('\n');
    }

    /**
     * Determines if the user appears to be writing.
     */
    isUserWriting(): boolean {
        if (!this.currentContext?.activeFile) return false;
        
        // Check recent modifications
        const recentMods = this.fileChanges.filter(
            c => c.type === 'modified' && 
                 c.path === this.currentContext?.activeFile?.path &&
                 (Date.now() - c.timestamp) < 30000
        );

        return recentMods.length >= 2;
    }

    /**
     * Gets the user's apparent focus area based on recent activity.
     */
    getFocusArea(): {
        folders: string[];
        tags: string[];
        topics: string[];
    } {
        const folders: Map<string, number> = new Map();
        const tags: Map<string, number> = new Map();

        // Analyze recent files
        for (const snapshot of [...this.contextHistory, this.currentContext].filter(Boolean) as ContextSnapshot[]) {
            if (!snapshot.activeFile) continue;

            // Count folder occurrences
            const folder = snapshot.activeFile.path.split('/').slice(0, -1).join('/');
            folders.set(folder, (folders.get(folder) || 0) + 1);

            // Count tag occurrences
            for (const tag of snapshot.activeFile.tags) {
                tags.set(tag, (tags.get(tag) || 0) + 1);
            }
        }

        // Sort by frequency
        const topFolders = Array.from(folders.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 3)
            .map(([folder]) => folder);

        const topTags = Array.from(tags.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([tag]) => tag);

        return {
            folders: topFolders,
            tags: topTags,
            topics: topTags // Could be enhanced with NLP
        };
    }

    /**
     * Gets suggestions based on current context.
     */
    async getContextualSuggestions(): Promise<string[]> {
        const suggestions: string[] = [];
        const context = await this.getOrUpdateContext();

        if (!context.activeFile) {
            suggestions.push('Create a new daily note');
            suggestions.push('Search your vault');
            return suggestions;
        }

        // Suggestions based on content
        const content = context.activeFile.content.toLowerCase();
        
        if (content.includes('todo') || content.includes('- [ ]')) {
            suggestions.push('Review and update tasks');
        }

        if (context.activeFile.tags.length === 0) {
            suggestions.push('Add tags to this note');
        }

        // Check for orphan status
        const backlinks = this.vaultManager.getBacklinks(context.activeFile.path);
        const outlinks = this.vaultManager.getOutgoingLinks(context.activeFile.path);
        
        if (backlinks.length === 0 && outlinks.length === 0) {
            suggestions.push('This note is isolated - consider linking it to related notes');
        }

        // Suggest related notes
        if (context.relatedNotes.length > 0) {
            suggestions.push(`Consider linking to: ${context.relatedNotes[0]}`);
        }

        // Check note length
        if (context.activeFile.wordCount > 2000) {
            suggestions.push('This note is quite long - consider splitting it');
        }

        if (context.activeFile.wordCount < 50 && !context.activeFile.path.includes('template')) {
            suggestions.push('This note is quite short - consider expanding it');
        }

        return suggestions;
    }

    // ============================================
    // FILE CHANGE ANALYSIS
    // ============================================

    /**
     * Gets recent file changes.
     */
    getRecentChanges(limit: number = 10): FileChangeEvent[] {
        return this.fileChanges.slice(-limit);
    }

    /**
     * Gets changes since a timestamp.
     */
    getChangesSince(timestamp: number): FileChangeEvent[] {
        return this.fileChanges.filter(c => c.timestamp > timestamp);
    }

    /**
     * Gets the most edited files.
     */
    getMostEditedFiles(limit: number = 5): { path: string; edits: number }[] {
        const editCounts: Map<string, number> = new Map();

        for (const change of this.fileChanges) {
            if (change.type === 'modified') {
                editCounts.set(change.path, (editCounts.get(change.path) || 0) + 1);
            }
        }

        return Array.from(editCounts.entries())
            .sort((a, b) => b[1] - a[1])
            .slice(0, limit)
            .map(([path, edits]) => ({ path, edits }));
    }

    // ============================================
    // PROACTIVE ASSISTANCE
    // ============================================

    /**
     * Determines if proactive assistance might be helpful.
     */
    async shouldOfferAssistance(): Promise<{
        shouldOffer: boolean;
        reason?: string;
        suggestion?: string;
    }> {
        const context = await this.getOrUpdateContext();

        // Don't interrupt if user is actively writing
        if (this.isUserWriting()) {
            return { shouldOffer: false };
        }

        // Check for orphan notes
        if (context.activeFile) {
            const backlinks = this.vaultManager.getBacklinks(context.activeFile.path);
            if (backlinks.length === 0) {
                const suggestions = await this.knowledgeGraph.suggestLinks(context.activeFile.path);
                if (suggestions.length > 0) {
                    return {
                        shouldOffer: true,
                        reason: 'orphan_note',
                        suggestion: `This note has no backlinks. Would you like me to suggest connections? I found ${suggestions.length} potentially related notes.`
                    };
                }
            }
        }

        // Check for missing daily note
        const today = new Date().toISOString().split('T')[0];
        const dailyNotePath = `pkm/_meta/_daily_notes/${today.split('-')[0]}`;
        const dailyNoteExists = this.app.vault.getAbstractFileByPath(dailyNotePath);
        
        if (!dailyNoteExists) {
            const hour = new Date().getHours();
            if (hour >= 8 && hour <= 10) {
                return {
                    shouldOffer: true,
                    reason: 'no_daily_note',
                    suggestion: "Good morning! Would you like me to create today's daily note?"
                };
            }
        }

        return { shouldOffer: false };
    }

    /**
     * Gets working session statistics.
     */
    getSessionStats(): {
        filesViewed: number;
        filesEdited: number;
        notesCreated: number;
        sessionDuration: number;
        focusScore: number;
    } {
        const sessionStart = this.contextHistory[0]?.timestamp || Date.now();
        const uniqueViewed = new Set(this.contextHistory.map(c => c.activeFile?.path).filter(Boolean));
        const edits = this.fileChanges.filter(c => c.type === 'modified').length;
        const creates = this.fileChanges.filter(c => c.type === 'created').length;

        // Calculate focus score (0-100) based on context switches
        const contextSwitches = this.contextHistory.filter((c, i) => 
            i > 0 && c.activeFile?.path !== this.contextHistory[i-1].activeFile?.path
        ).length;
        
        const focusScore = Math.max(0, 100 - (contextSwitches * 5));

        return {
            filesViewed: uniqueViewed.size,
            filesEdited: edits,
            notesCreated: creates,
            sessionDuration: Date.now() - sessionStart,
            focusScore
        };
    }
}
