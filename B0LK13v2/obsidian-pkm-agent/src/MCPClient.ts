import { request } from 'obsidian';

export interface MCPTool {
    name: string;
    description: string;
    inputSchema: any;
}

export interface MCPMessage {
    jsonrpc: string;
    id?: string | number;
    method?: string;
    params?: any;
    result?: any;
    error?: any;
}

export class MCPClient {
    private baseUrl: string;
    private apiKey?: string;
    private sessionId: string;
    private timeout: number;

    constructor(config: { baseUrl: string; apiKey?: string; timeout?: number }) {
        this.baseUrl = config.baseUrl.replace(/\/$/, '');
        this.apiKey = config.apiKey;
        this.timeout = config.timeout || 30000;
        this.sessionId = Math.random().toString(36).substring(7);
    }

    async initialize(): Promise<void> {
        try {
            const result = await this.call('initialize', {});
            console.log('MCP client initialized:', result.serverInfo);
        } catch (error) {
            console.error('Failed to initialize MCP client:', error);
            throw error;
        }
    }

    async listTools(): Promise<MCPTool[]> {
        const result = await this.call('tools/list', {});
        return result.tools || [];
    }

    async callTool(toolName: string, toolArgs: any): Promise<any> {
        const result = await this.call('tools/call', {
            name: toolName,
            arguments: toolArgs
        });
        return result;
    }

    async listResources(): Promise<any[]> {
        const result = await this.call('resources/list', {});
        return result.resources || [];
    }

    async readResource(uri: string): Promise<string> {
        const result = await this.call('resources/read', { uri });
        const contents = result.contents || [];
        return contents.length > 0 ? contents[0].text : '';
    }

    async listPrompts(): Promise<any[]> {
        const result = await this.call('prompts/list', {});
        return result.prompts || [];
    }

    async getPrompt(promptName: string, promptArgs?: any): Promise<any[]> {
        const result = await this.call('prompts/get', {
            name: promptName,
            arguments: promptArgs || {}
        });
        return result.messages || [];
    }

    private async call(method: string, params: any): Promise<any> {
        const id = Date.now();
        const message: MCPMessage = {
            jsonrpc: '2.0',
            id,
            method,
            params
        };

        try {
            const headers: Record<string, string> = {
                'Content-Type': 'application/json'
            };
            if (this.apiKey) {
                headers['X-API-Key'] = this.apiKey;
            }

            const response = await request({
                url: `${this.baseUrl}/${this.sessionId}/${method}`,
                method: 'POST',
                headers,
                body: JSON.stringify(message)
            });

            const data = JSON.parse(response);

            if (data.error) {
                throw new MCPError(data.error.message || 'Unknown MCP error');
            }

            return data.result;
        } catch (error: any) {
            if (error instanceof MCPError) {
                throw error;
            }
            throw new MCPError(`MCP request failed: ${error.message || error}`);
        }
    }
}

export class MCPError extends Error {
    constructor(message: string) {
        super(message);
        this.name = 'MCPError';
    }
}

export class ObsidianMCPClient extends MCPClient {
    constructor(config: { baseUrl: string; apiKey: string }) {
        super(config);
    }

    async readNote(path: string, format: string = 'markdown'): Promise<any> {
        return await this.callTool('obsidian_read_note', {
            path,
            format
        });
    }

    async updateNote(path: string, content: string, mode: string = 'overwrite'): Promise<any> {
        return await this.callTool('obsidian_update_note', {
            path,
            content,
            mode
        });
    }

    async searchAndReplace(
        path: string,
        search: string,
        replace: string,
        options: {
            useRegex?: boolean;
            caseSensitive?: boolean;
            replaceAll?: boolean;
        } = {}
    ): Promise<any> {
        return await this.callTool('obsidian_search_replace', {
            path,
            search,
            replace,
            use_regex: options.useRegex || false,
            case_sensitive: options.caseSensitive || false,
            replace_all: options.replaceAll !== false
        });
    }

    async globalSearch(
        query: string,
        options: {
            useRegex?: boolean;
            pathFilter?: string;
            modifiedAfter?: string;
            limit?: number;
        } = {}
    ): Promise<any> {
        return await this.callTool('obsidian_global_search', {
            query,
            use_regex: options.useRegex || false,
            path_filter: options.pathFilter,
            modified_after: options.modifiedAfter,
            limit: options.limit || 20
        });
    }

    async listNotes(
        directory: string = '/',
        options: {
            extensionFilter?: string;
            nameRegex?: string;
        } = {}
    ): Promise<any> {
        return await this.callTool('obsidian_list_notes', {
            directory,
            extension_filter: options.extensionFilter,
            name_regex: options.nameRegex
        });
    }

    async manageFrontmatter(
        path: string,
        action: 'get' | 'set' | 'delete',
        key?: string,
        value?: any
    ): Promise<any> {
        const params: any = { path, action };
        if (key) params.key = key;
        if (value !== undefined) params.value = value;

        return await this.callTool('obsidian_manage_frontmatter', params);
    }

    async manageTags(
        path: string,
        action: 'add' | 'remove' | 'list',
        tags?: string[]
    ): Promise<any> {
        const params: any = { path, action };
        if (tags) params.tags = tags;

        return await this.callTool('obsidian_manage_tags', params);
    }

    async deleteNote(path: string): Promise<any> {
        return await this.callTool('obsidian_delete_note', { path });
    }
}

export class PKMRAGMCPClient extends MCPClient {
    constructor(config: { baseUrl: string; apiKey?: string }) {
        super(config);
    }

    async search(
        query: string,
        options: {
            limit?: number;
            filters?: any;
        } = {}
    ): Promise<any[]> {
        const result = await this.callTool('pkm_search', {
            query,
            limit: options.limit || 10,
            filters: options.filters || {}
        });
        return result.results || [];
    }

    async ask(
        message: string,
        options: {
            conversationId?: string;
            useContext?: boolean;
        } = {}
    ): Promise<any> {
        return await this.callTool('pkm_ask', {
            message,
            conversation_id: options.conversationId,
            use_context: options.useContext !== false
        });
    }

    async getStats(): Promise<any> {
        return await this.callTool('pkm_get_stats', {});
    }

    async listConversations(): Promise<any[]> {
        const result = await this.callTool('pkm_list_conversations', {});
        return result.conversations || [];
    }

    async indexNotes(): Promise<any> {
        return await this.callTool('pkm_index_notes', {});
    }

    async getConversationHistory(conversationId: string, limit: number = 50): Promise<any[]> {
        const result = await this.callTool('pkm_get_conversation_history', {
            conversation_id: conversationId,
            limit
        });
        return result.history || [];
    }
}

export class UnifiedMCPClient {
    private obsidianClient: ObsidianMCPClient | null = null;
    private pkmRAGClient: PKMRAGMCPClient | null = null;

    constructor(config: {
        obsidian?: { baseUrl: string; apiKey: string };
        pkmRAG?: { baseUrl: string; apiKey?: string };
    }) {
        if (config.obsidian) {
            this.obsidianClient = new ObsidianMCPClient(config.obsidian);
        }
        if (config.pkmRAG) {
            this.pkmRAGClient = new PKMRAGMCPClient(config.pkmRAG);
        }
    }

    async initialize(): Promise<void> {
        const promises: Promise<void>[] = [];

        if (this.obsidianClient) {
            promises.push(this.obsidianClient.initialize().catch(err => {
                console.warn('Failed to initialize Obsidian MCP client:', err);
            }));
        }

        if (this.pkmRAGClient) {
            promises.push(this.pkmRAGClient.initialize().catch(err => {
                console.warn('Failed to initialize PKM RAG MCP client:', err);
            }));
        }

        await Promise.all(promises);
    }

    getObsidianClient(): ObsidianMCPClient | null {
        return this.obsidianClient;
    }

    getPKMRAGClient(): PKMRAGMCPClient | null {
        return this.pkmRAGClient;
    }

    async getAllTools(): Promise<{ obsidian?: MCPTool[]; pkmRAG?: MCPTool[] }> {
        const result: { obsidian?: MCPTool[]; pkmRAG?: MCPTool[] } = {};

        if (this.obsidianClient) {
            try {
                result.obsidian = await this.obsidianClient.listTools();
            } catch (err) {
                console.error('Failed to list Obsidian tools:', err);
            }
        }

        if (this.pkmRAGClient) {
            try {
                result.pkmRAG = await this.pkmRAGClient.listTools();
            } catch (err) {
                console.error('Failed to list PKM RAG tools:', err);
            }
        }

        return result;
    }
}
