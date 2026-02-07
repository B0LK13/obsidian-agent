import { App, TFile, normalizePath } from 'obsidian';

/**
 * Memory types for the agent
 */
interface ConversationMessage {
    role: 'user' | 'assistant' | 'system' | 'tool';
    content: string | null;
    timestamp: number;
    tool_calls?: any[];
    tool_call_id?: string;
    name?: string;
}

interface MemoryEntry {
    id: string;
    type: 'fact' | 'preference' | 'context' | 'task' | 'insight';
    content: string;
    source?: string;
    created: number;
    accessed: number;
    importance: number;
    tags: string[];
}

interface SessionSummary {
    id: string;
    startTime: number;
    endTime: number;
    messageCount: number;
    summary: string;
    keyTopics: string[];
    notesCreated: string[];
    notesModified: string[];
}

/**
 * MemoryManager - Handles conversation context, long-term memory, and learning
 * Enables the agent to remember user preferences, past interactions, and learn patterns.
 */
export class MemoryManager {
    private app: App;
    private conversationHistory: ConversationMessage[] = [];
    private longTermMemory: Map<string, MemoryEntry> = new Map();
    private sessionSummaries: SessionSummary[] = [];
    private currentSessionId: string;
    private memoryFilePath: string = 'pkm/_meta/_agent/memory.json';
    private maxConversationLength: number = 50;
    private maxContextTokens: number = 8000;

    constructor(app: App) {
        this.app = app;
        this.currentSessionId = this.generateId();
        this.loadMemory();
    }

    // ============================================
    // CONVERSATION HISTORY MANAGEMENT
    // ============================================

    /**
     * Adds a message to the conversation history.
     */
    addMessage(message: ConversationMessage): void {
        message.timestamp = Date.now();
        this.conversationHistory.push(message);
        
        // Prune if too long
        if (this.conversationHistory.length > this.maxConversationLength * 2) {
            this.pruneConversation();
        }
    }

    /**
     * Gets the full conversation history.
     */
    getConversation(): ConversationMessage[] {
        return [...this.conversationHistory];
    }

    /**
     * Gets a context-aware subset of the conversation for the LLM.
     */
    getContextWindow(maxMessages: number = 20): ConversationMessage[] {
        const systemMessage = this.conversationHistory.find(m => m.role === 'system');
        const recentMessages = this.conversationHistory
            .filter(m => m.role !== 'system')
            .slice(-maxMessages);
        
        if (systemMessage) {
            return [systemMessage, ...recentMessages];
        }
        return recentMessages;
    }

    /**
     * Clears the conversation history but preserves the system prompt.
     */
    clearConversation(): void {
        const systemMessage = this.conversationHistory.find(m => m.role === 'system');
        this.conversationHistory = systemMessage ? [systemMessage] : [];
    }

    /**
     * Prunes old conversation messages, keeping recent and important ones.
     */
    private pruneConversation(): void {
        const systemMessage = this.conversationHistory.find(m => m.role === 'system');
        const otherMessages = this.conversationHistory.filter(m => m.role !== 'system');
        
        // Keep last maxConversationLength messages
        const kept = otherMessages.slice(-this.maxConversationLength);
        
        this.conversationHistory = systemMessage ? [systemMessage, ...kept] : kept;
    }

    // ============================================
    // LONG-TERM MEMORY
    // ============================================

    /**
     * Stores a fact or piece of information in long-term memory.
     */
    remember(
        content: string, 
        type: MemoryEntry['type'] = 'fact',
        options?: { 
            source?: string; 
            importance?: number; 
            tags?: string[] 
        }
    ): string {
        const id = this.generateId();
        const entry: MemoryEntry = {
            id,
            type,
            content,
            source: options?.source,
            created: Date.now(),
            accessed: Date.now(),
            importance: options?.importance || 0.5,
            tags: options?.tags || []
        };
        
        this.longTermMemory.set(id, entry);
        this.saveMemory();
        return id;
    }

    /**
     * Recalls memories matching a query.
     */
    recall(query: string, options?: { 
        type?: MemoryEntry['type']; 
        limit?: number;
        minImportance?: number;
    }): MemoryEntry[] {
        const results: MemoryEntry[] = [];
        const queryLower = query.toLowerCase();
        const limit = options?.limit || 10;
        const minImportance = options?.minImportance || 0;

        for (const entry of this.longTermMemory.values()) {
            // Filter by type
            if (options?.type && entry.type !== options.type) continue;
            
            // Filter by importance
            if (entry.importance < minImportance) continue;

            // Simple relevance check
            const contentLower = entry.content.toLowerCase();
            const tagMatch = entry.tags.some(t => t.toLowerCase().includes(queryLower));
            const contentMatch = contentLower.includes(queryLower);
            
            if (tagMatch || contentMatch) {
                entry.accessed = Date.now();
                results.push(entry);
            }
        }

        // Sort by importance and recency
        return results
            .sort((a, b) => {
                const importanceDiff = b.importance - a.importance;
                if (Math.abs(importanceDiff) > 0.1) return importanceDiff;
                return b.accessed - a.accessed;
            })
            .slice(0, limit);
    }

    /**
     * Gets all memories of a specific type.
     */
    getMemoriesByType(type: MemoryEntry['type']): MemoryEntry[] {
        return Array.from(this.longTermMemory.values())
            .filter(m => m.type === type)
            .sort((a, b) => b.accessed - a.accessed);
    }

    /**
     * Updates the importance of a memory.
     */
    updateImportance(id: string, importance: number): boolean {
        const entry = this.longTermMemory.get(id);
        if (entry) {
            entry.importance = Math.max(0, Math.min(1, importance));
            entry.accessed = Date.now();
            this.saveMemory();
            return true;
        }
        return false;
    }

    /**
     * Forgets (removes) a specific memory.
     */
    forget(id: string): boolean {
        const deleted = this.longTermMemory.delete(id);
        if (deleted) {
            this.saveMemory();
        }
        return deleted;
    }

    /**
     * Gets user preferences from memory.
     */
    getPreferences(): MemoryEntry[] {
        return this.getMemoriesByType('preference');
    }

    /**
     * Stores a user preference.
     */
    setPreference(preference: string, tags?: string[]): string {
        // Check if similar preference exists
        const existing = this.recall(preference, { type: 'preference', limit: 1 });
        if (existing.length > 0 && existing[0].content.toLowerCase() === preference.toLowerCase()) {
            existing[0].accessed = Date.now();
            existing[0].importance = Math.min(1, existing[0].importance + 0.1);
            this.saveMemory();
            return existing[0].id;
        }

        return this.remember(preference, 'preference', { 
            importance: 0.8,
            tags: tags || ['user-preference']
        });
    }

    // ============================================
    // SESSION MANAGEMENT
    // ============================================

    /**
     * Starts a new session.
     */
    startNewSession(): string {
        this.currentSessionId = this.generateId();
        return this.currentSessionId;
    }

    /**
     * Ends the current session and creates a summary.
     */
    async endSession(summary?: string): Promise<void> {
        const messageCount = this.conversationHistory.filter(m => m.role !== 'system').length;
        
        if (messageCount > 0) {
            const sessionSummary: SessionSummary = {
                id: this.currentSessionId,
                startTime: this.conversationHistory[1]?.timestamp || Date.now(),
                endTime: Date.now(),
                messageCount,
                summary: summary || this.generateSessionSummary(),
                keyTopics: this.extractKeyTopics(),
                notesCreated: [],
                notesModified: []
            };

            this.sessionSummaries.push(sessionSummary);
            this.saveMemory();
        }
    }

    /**
     * Gets recent session summaries.
     */
    getRecentSessions(limit: number = 5): SessionSummary[] {
        return this.sessionSummaries.slice(-limit);
    }

    /**
     * Generates a simple session summary from the conversation.
     */
    private generateSessionSummary(): string {
        const userMessages = this.conversationHistory
            .filter(m => m.role === 'user' && m.content)
            .slice(-5);
        
        if (userMessages.length === 0) {
            return 'Empty session';
        }

        const topics = userMessages
            .map(m => m.content!.substring(0, 50))
            .join('; ');
        
        return `Discussed: ${topics}`;
    }

    /**
     * Extracts key topics from the conversation.
     */
    private extractKeyTopics(): string[] {
        const topics: string[] = [];
        const wordCounts: Record<string, number> = {};

        for (const msg of this.conversationHistory) {
            if (!msg.content) continue;
            
            // Simple word extraction (could be enhanced with NLP)
            const words = msg.content
                .toLowerCase()
                .replace(/[^a-z0-9\s]/g, '')
                .split(/\s+/)
                .filter(w => w.length > 4);
            
            for (const word of words) {
                wordCounts[word] = (wordCounts[word] || 0) + 1;
            }
        }

        // Get top words
        return Object.entries(wordCounts)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 5)
            .map(([word]) => word);
    }

    // ============================================
    // CONTEXT BUILDING
    // ============================================

    /**
     * Builds enriched context for the LLM including relevant memories.
     */
    buildEnrichedContext(currentQuery: string): string {
        const parts: string[] = [];

        // Add relevant memories
        const relevantMemories = this.recall(currentQuery, { limit: 5 });
        if (relevantMemories.length > 0) {
            parts.push('**Relevant Memories:**');
            for (const mem of relevantMemories) {
                parts.push(`- [${mem.type}] ${mem.content}`);
            }
        }

        // Add user preferences
        const preferences = this.getPreferences().slice(0, 3);
        if (preferences.length > 0) {
            parts.push('\n**User Preferences:**');
            for (const pref of preferences) {
                parts.push(`- ${pref.content}`);
            }
        }

        // Add recent session context
        const recentSessions = this.getRecentSessions(2);
        if (recentSessions.length > 0) {
            parts.push('\n**Recent Sessions:**');
            for (const session of recentSessions) {
                parts.push(`- ${session.summary}`);
            }
        }

        return parts.join('\n');
    }

    /**
     * Gets working memory (current context + recent actions).
     */
    getWorkingMemory(): {
        currentContext: string;
        recentActions: string[];
        pendingTasks: string[];
    } {
        const recentMessages = this.conversationHistory.slice(-10);
        const actions: string[] = [];

        for (const msg of recentMessages) {
            if (msg.tool_calls) {
                for (const tc of msg.tool_calls) {
                    actions.push(`${tc.function.name}()`);
                }
            }
        }

        const pendingTasks = this.getMemoriesByType('task')
            .filter(t => t.importance > 0.5)
            .map(t => t.content);

        return {
            currentContext: recentMessages.map(m => 
                m.content?.substring(0, 100) || ''
            ).join(' | '),
            recentActions: actions.slice(-5),
            pendingTasks: pendingTasks.slice(0, 5)
        };
    }

    // ============================================
    // PERSISTENCE
    // ============================================

    /**
     * Saves memory to the vault.
     */
    private async saveMemory(): Promise<void> {
        try {
            const data = {
                longTermMemory: Array.from(this.longTermMemory.entries()),
                sessionSummaries: this.sessionSummaries.slice(-20), // Keep last 20 sessions
                lastSaved: Date.now()
            };

            const content = JSON.stringify(data, null, 2);
            const filePath = normalizePath(this.memoryFilePath);
            
            // Ensure directory exists
            const dirPath = filePath.substring(0, filePath.lastIndexOf('/'));
            await this.ensureFolder(dirPath);

            const existingFile = this.app.vault.getAbstractFileByPath(filePath);
            if (existingFile instanceof TFile) {
                await this.app.vault.modify(existingFile, content);
            } else {
                await this.app.vault.create(filePath, content);
            }
        } catch (error) {
            console.error('[MemoryManager] Failed to save memory:', error);
        }
    }

    /**
     * Loads memory from the vault.
     */
    private async loadMemory(): Promise<void> {
        try {
            const filePath = normalizePath(this.memoryFilePath);
            const file = this.app.vault.getAbstractFileByPath(filePath);
            
            if (file instanceof TFile) {
                const content = await this.app.vault.read(file);
                const data = JSON.parse(content);
                
                // Restore long-term memory
                if (data.longTermMemory) {
                    this.longTermMemory = new Map(data.longTermMemory);
                }
                
                // Restore session summaries
                if (data.sessionSummaries) {
                    this.sessionSummaries = data.sessionSummaries;
                }
                
                console.log('[MemoryManager] Loaded memory:', {
                    memories: this.longTermMemory.size,
                    sessions: this.sessionSummaries.length
                });
            }
        } catch (error) {
            console.log('[MemoryManager] No existing memory found or error loading:', error.message);
        }
    }

    /**
     * Ensures a folder path exists.
     */
    private async ensureFolder(path: string): Promise<void> {
        const parts = path.split('/');
        let current = '';
        
        for (const part of parts) {
            current = current ? `${current}/${part}` : part;
            const existing = this.app.vault.getAbstractFileByPath(current);
            
            if (!existing) {
                try {
                    await this.app.vault.createFolder(current);
                } catch (e) {
                    // Folder might already exist
                }
            }
        }
    }

    // ============================================
    // UTILITIES
    // ============================================

    /**
     * Generates a unique ID.
     */
    private generateId(): string {
        return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
    }

    /**
     * Gets memory statistics.
     */
    getStats(): {
        conversationLength: number;
        totalMemories: number;
        memoriesByType: Record<string, number>;
        totalSessions: number;
    } {
        const memoriesByType: Record<string, number> = {};
        
        for (const entry of this.longTermMemory.values()) {
            memoriesByType[entry.type] = (memoriesByType[entry.type] || 0) + 1;
        }

        return {
            conversationLength: this.conversationHistory.length,
            totalMemories: this.longTermMemory.size,
            memoriesByType,
            totalSessions: this.sessionSummaries.length
        };
    }

    /**
     * Exports all memory data.
     */
    exportMemory(): string {
        return JSON.stringify({
            longTermMemory: Array.from(this.longTermMemory.entries()),
            sessionSummaries: this.sessionSummaries,
            stats: this.getStats()
        }, null, 2);
    }

    /**
     * Clears all memory (use with caution).
     */
    clearAllMemory(): void {
        this.conversationHistory = [];
        this.longTermMemory.clear();
        this.sessionSummaries = [];
        this.saveMemory();
    }
}
