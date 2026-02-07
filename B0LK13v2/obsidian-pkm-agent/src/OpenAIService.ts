import OpenAI from 'openai';
import { AGENT_TOOLS } from './ToolHandler';

/**
 * Model configuration
 */
interface ModelConfig {
    name: string;
    contextWindow: number;
    supportsVision: boolean;
    supportsTools: boolean;
}

/**
 * Available models
 */
const MODELS: Record<string, ModelConfig> = {
    'gpt-4o': { name: 'gpt-4o', contextWindow: 128000, supportsVision: true, supportsTools: true },
    'gpt-4o-mini': { name: 'gpt-4o-mini', contextWindow: 128000, supportsVision: true, supportsTools: true },
    'gpt-4-turbo': { name: 'gpt-4-turbo', contextWindow: 128000, supportsVision: true, supportsTools: true },
    'gpt-3.5-turbo': { name: 'gpt-3.5-turbo', contextWindow: 16385, supportsVision: false, supportsTools: true },
};

/**
 * The comprehensive system prompt for the autonomous agent
 */
export const AGENT_SYSTEM_PROMPT = `You are an advanced autonomous AI assistant embedded in Obsidian, a powerful personal knowledge management (PKM) system. Your purpose is to help users manage, organize, and enhance their knowledge base through intelligent interaction.

## Core Identity

You are **PKM Agent**, a sophisticated digital librarian and research assistant. You don't just respond to commands—you understand the user's knowledge management goals and proactively help them build a better second brain.

## Your Capabilities

### 1. **Note Management**
- Create, read, update, and delete notes
- Use templates for consistent note structure
- Apply frontmatter metadata intelligently
- Organize notes into appropriate folders

### 2. **Knowledge Organization**
- Add and manage tags systematically
- Create meaningful links between notes
- Build Maps of Content (MOCs) for topics
- Create Zettelkasten-style atomic notes
- Identify and suggest connections

### 3. **Search & Discovery**
- Full-text search across the vault
- Tag-based filtering
- Property/frontmatter queries
- Find orphan notes (unlinked)
- Discover related content

### 4. **Analysis & Insights**
- Analyze note relationships and connections
- Provide vault statistics
- Identify knowledge gaps
- Suggest organizational improvements
- Track writing patterns

### 5. **Daily Workflows**
- Create and manage daily notes
- Support journaling and reflection
- Track tasks and todos

## Knowledge Base Structure (PARA Method + Zettelkasten)

The vault follows this structure:
- \`pkm/_meta/\` - System files, daily notes, templates, changelogs
- \`pkm/01_projects/\` - Active time-bound projects
- \`pkm/02_areas/\` - Ongoing life areas (career, finance, health)
- \`pkm/03_resources/\` - Reference materials (programming, tools, books)
- \`pkm/04_archive/\` - Completed/inactive items
- \`pkm/99_zettelkasten/\` - Atomic notes with UIDs, indexes, and MOCs

## Behavioral Guidelines

### Be Proactive
- When a user mentions a topic, check if related notes exist
- Suggest linking new content to existing knowledge
- Offer to create templates for recurring note types
- Identify opportunities to improve organization

### Be Thorough
- When creating notes, consider appropriate location, tags, and links
- When searching, explore multiple approaches if initial results are poor
- Verify operations completed successfully

### Be Intelligent
- Infer intent from context (e.g., "add this to my project notes" → find the active project)
- Use the active file context when relevant
- Remember user preferences across the conversation
- Build on previous interactions

### Be Careful
- Always confirm before deleting
- Use trash instead of permanent delete
- Warn about potentially destructive batch operations
- Preserve existing content when updating (unless explicitly asked to replace)

## Response Style

- Be concise but informative
- Use markdown formatting appropriately
- Show relevant results (paths, content snippets)
- Explain what you did and why
- Offer follow-up actions when appropriate

## Tool Usage Strategy

1. **For simple queries**: Execute directly
2. **For complex tasks**: 
   - First gather context (search, read current state)
   - Then plan the steps
   - Execute with verification
3. **For batch operations**: Show what will be affected, then proceed
4. **When uncertain**: Ask clarifying questions rather than guessing

## Context Awareness

You have access to:
- The currently active/open file
- Recent file history
- The vault's folder structure
- Tag and link relationships
- User's working patterns

Use this context to provide relevant, personalized assistance.

## Example Interactions

**User**: "Create a meeting note for the project sync"
**You**: I'll create a meeting note using your meeting template. Let me check for active projects first to link it appropriately.
[Uses list_folder, then create_from_template with proper path and tags]

**User**: "What have I written about API design?"
**You**: [Searches vault, presents organized results with links]
I found 5 notes about API design:
- 03_resources/_programming/patterns/api-design-patterns.md (comprehensive guide)
- 99_zettelkasten/notes/20240115-rest-versioning.md (atomic note)
...

**User**: "This note feels disconnected"  
**You**: [Analyzes current note, finds related content, suggests links]
I see this note about "distributed caching" has no links. Based on tags and content, I'd suggest connecting it to:
1. [[redis-patterns]] - Related caching technology
2. [[microservices-architecture]] - Where caching is discussed
Would you like me to add these links?

Remember: You are not just a tool executor—you are a knowledge management partner helping the user build and maintain their personal knowledge system.`;

/**
 * OpenAIService - Enhanced LLM interaction with streaming and context management
 */
export class OpenAIService {
    private client: OpenAI | null = null;
    private model: string = 'gpt-4o';
    private temperature: number = 0.7;
    private maxTokens: number = 4096;
    private apiKey: string = '';
    private baseUrl: string = 'https://api.openai.com/v1';

    constructor(apiKey: string, model?: string, baseUrl?: string) {
        this.apiKey = apiKey;
        if (model && MODELS[model]) {
            this.model = model;
        } else if (model) {
            // Allow unknown models if using custom URL
            this.model = model;
        }
        
        if (baseUrl) {
            this.baseUrl = baseUrl;
        }
        
        if (this.isValidApiKey(apiKey)) {
            this.client = new OpenAI({
                apiKey: apiKey,
                baseURL: this.baseUrl,
                dangerouslyAllowBrowser: true
            });
        }
    }

    /**
     * Validates the API key format.
     */
    private isValidApiKey(key: string): boolean {
        return key && 
               key.trim() !== '' && 
               key !== 'default' &&
               (key.startsWith('sk-') || key.startsWith('sk-proj-'));
    }

    /**
     * Updates the API key.
     */
    setApiKey(apiKey: string): void {
        this.apiKey = apiKey;
        if (this.isValidApiKey(apiKey)) {
            this.client = new OpenAI({
                apiKey: apiKey,
                baseURL: this.baseUrl,
                dangerouslyAllowBrowser: true
            });
        } else {
            this.client = null;
        }
    }

    /**
     * Sets the model to use.
     */
    setModel(model: string): void {
        if (MODELS[model]) {
            this.model = model;
        }
    }

    /**
     * Gets available models.
     */
    getAvailableModels(): string[] {
        return Object.keys(MODELS);
    }

    /**
     * Checks if the service is configured with a valid API key.
     */
    isConfigured(): boolean {
        return this.client !== null;
    }

    /**
     * Main chat completion method with tool support.
     */
    async chat(
        messages: any[], 
        options?: {
            temperature?: number;
            maxTokens?: number;
            toolChoice?: 'auto' | 'none' | { type: 'function'; function: { name: string } };
        }
    ): Promise<any> {
        if (!this.client) {
            return this.handleOfflineChat(messages);
        }

        try {
            console.log(`[OpenAI] Sending request with model: ${this.model}`);
            const response = await this.client.chat.completions.create({
                model: this.model,
                messages: messages,
                tools: AGENT_TOOLS,
                tool_choice: options?.toolChoice || 'auto',
                temperature: options?.temperature || this.temperature,
                max_tokens: options?.maxTokens || this.maxTokens,
            });

            return response.choices[0].message;
        } catch (error: any) {
            console.error('[OpenAI] Error:', error);
            return this.handleError(error);
        }
    }

    /**
     * Streaming chat completion.
     */
    async chatStream(
        messages: any[],
        onChunk: (content: string) => void,
        onToolCall?: (toolCall: any) => void,
        options?: {
            temperature?: number;
            maxTokens?: number;
        }
    ): Promise<any> {
        if (!this.client) {
            const response = this.handleOfflineChat(messages);
            if (response.content) {
                onChunk(response.content);
            }
            return response;
        }

        try {
            console.log(`[OpenAI] Starting stream with model: ${this.model}`);
            const stream = await this.client.chat.completions.create({
                model: this.model,
                messages: messages,
                tools: AGENT_TOOLS,
                tool_choice: 'auto',
                temperature: options?.temperature || this.temperature,
                max_tokens: options?.maxTokens || this.maxTokens,
                stream: true,
            });

            let fullContent = '';
            let toolCalls: any[] = [];

            for await (const chunk of stream) {
                const delta = chunk.choices[0]?.delta;
                
                if (delta?.content) {
                    fullContent += delta.content;
                    onChunk(delta.content);
                }

                if (delta?.tool_calls) {
                    for (const tc of delta.tool_calls) {
                        if (tc.index !== undefined) {
                            if (!toolCalls[tc.index]) {
                                toolCalls[tc.index] = {
                                    id: tc.id || '',
                                    type: 'function',
                                    function: { name: '', arguments: '' }
                                };
                            }
                            if (tc.id) toolCalls[tc.index].id = tc.id;
                            if (tc.function?.name) toolCalls[tc.index].function.name += tc.function.name;
                            if (tc.function?.arguments) toolCalls[tc.index].function.arguments += tc.function.arguments;
                        }
                    }
                }
            }

            // Notify about tool calls
            if (toolCalls.length > 0 && onToolCall) {
                for (const tc of toolCalls) {
                    if (tc.id && tc.function.name) {
                        onToolCall(tc);
                    }
                }
            }

            return {
                role: 'assistant',
                content: fullContent || null,
                tool_calls: toolCalls.length > 0 ? toolCalls.filter(tc => tc.id && tc.function.name) : undefined
            };
        } catch (error: any) {
            console.error('[OpenAI] Stream error:', error);
            return this.handleError(error);
        }
    }

    /**
     * Simple completion without tools (for summaries, etc).
     */
    async complete(prompt: string, systemPrompt?: string): Promise<string> {
        if (!this.client) {
            return 'API key not configured. Please add your OpenAI API key in settings.';
        }

        try {
            const messages: any[] = [
                { role: 'system', content: systemPrompt || 'You are a helpful assistant.' },
                { role: 'user', content: prompt }
            ];

            const response = await this.client.chat.completions.create({
                model: this.model,
                messages: messages,
                temperature: this.temperature,
                max_tokens: this.maxTokens,
            });

            return response.choices[0].message.content || '';
        } catch (error: any) {
            console.error('[OpenAI] Complete error:', error);
            return `Error: ${error.message}`;
        }
    }

    /**
     * Generates embeddings for text (useful for semantic search).
     */
    async getEmbedding(text: string): Promise<number[] | null> {
        if (!this.client) return null;

        try {
            const response = await this.client.embeddings.create({
                model: 'text-embedding-3-small',
                input: text,
            });

            return response.data[0].embedding;
        } catch (error: any) {
            console.error('[OpenAI] Embedding error:', error);
            return null;
        }
    }

    /**
     * Handles offline/fallback mode.
     */
    private handleOfflineChat(messages: any[]): any {
        const lastMsg = messages[messages.length - 1];
        const content = lastMsg.content?.toLowerCase() || '';

        // Pattern matching for basic commands in offline mode
        const patterns: { pattern: RegExp; tool: string; argsExtractor?: (match: RegExpMatchArray) => any }[] = [
            {
                pattern: /list\s+(files|notes|all)/i,
                tool: 'list_folder',
                argsExtractor: () => ({ path: 'pkm', recursive: false })
            },
            {
                pattern: /search\s+(?:for\s+)?["']?(.+?)["']?$/i,
                tool: 'search_vault',
                argsExtractor: (m) => ({ query: m[1], limit: 10 })
            },
            {
                pattern: /(?:show|get|open)\s+daily\s*note/i,
                tool: 'get_daily_note',
                argsExtractor: () => ({})
            },
            {
                pattern: /(?:what|which)\s+tags/i,
                tool: 'get_all_tags',
                argsExtractor: () => ({})
            },
            {
                pattern: /vault\s+(?:stats|statistics)/i,
                tool: 'get_vault_stats',
                argsExtractor: () => ({})
            },
            {
                pattern: /recent\s+(?:files|notes)/i,
                tool: 'get_recent_files',
                argsExtractor: () => ({ limit: 10 })
            }
        ];

        for (const { pattern, tool, argsExtractor } of patterns) {
            const match = content.match(pattern);
            if (match) {
                return {
                    role: 'assistant',
                    content: null,
                    tool_calls: [{
                        id: `offline_${Date.now()}`,
                        type: 'function',
                        function: {
                            name: tool,
                            arguments: JSON.stringify(argsExtractor ? argsExtractor(match) : {})
                        }
                    }]
                };
            }
        }

        return {
            role: 'assistant',
            content: `**Offline Mode** - No API key configured.

I can still help with basic commands:
- "list files" - Show vault contents
- "search for [query]" - Search notes
- "get daily note" - Today's daily note
- "what tags" - List all tags
- "vault stats" - Show statistics
- "recent files" - Recently modified

For full autonomous capabilities, please add your OpenAI API key in the plugin settings.`
        };
    }

    /**
     * Handles API errors gracefully.
     */
    private handleError(error: any): any {
        console.error('[OpenAI] FULL API ERROR:', JSON.stringify(error, null, 2));
        if (error.response) {
             console.error('[OpenAI] Response Data:', JSON.stringify(error.response.data, null, 2));
             console.error('[OpenAI] Response Headers:', JSON.stringify(error.response.headers, null, 2));
        }

        let message = 'An error occurred while processing your request.';

        if (error.status === 401) {
            message = `**Authentication Failed**

The API key is invalid. Please check your API key in Settings.

To get an API key:
1. Go to [platform.openai.com](https://platform.openai.com)
2. Navigate to API Keys
3. Create a new key
4. Paste it in the plugin settings`;
        } else if (error.status === 429) {
            message = `**Rate Limited**

You've hit the API rate limit. Please wait a moment and try again.

If this persists, check your OpenAI usage limits.`;
        } else if (error.status === 500 || error.status === 503) {
            message = `**Service Unavailable**

OpenAI's servers are currently experiencing issues. Please try again in a few minutes.`;
        } else if (error.code === 'ENOTFOUND' || error.code === 'ECONNREFUSED') {
            message = `**Connection Error**

Unable to connect to OpenAI. Please check your internet connection.`;
        } else if (error.message) {
            message = `**Error**: ${error.message}`;
        }

        return {
            role: 'assistant',
            content: message
        };
    }

    /**
     * Estimates token count for a string (rough approximation).
     */
    estimateTokens(text: string): number {
        // Rough estimate: ~4 characters per token for English
        return Math.ceil(text.length / 4);
    }

    /**
     * Truncates messages to fit within context window.
     */
    truncateToFit(messages: any[], maxTokens?: number): any[] {
        const limit = maxTokens || MODELS[this.model]?.contextWindow || 8000;
        const systemMessage = messages.find(m => m.role === 'system');
        const otherMessages = messages.filter(m => m.role !== 'system');

        let totalTokens = systemMessage ? this.estimateTokens(systemMessage.content || '') : 0;
        const result: any[] = systemMessage ? [systemMessage] : [];

        // Add messages from most recent, stopping when limit approached
        for (let i = otherMessages.length - 1; i >= 0; i--) {
            const msg = otherMessages[i];
            const msgTokens = this.estimateTokens(JSON.stringify(msg));
            
            if (totalTokens + msgTokens > limit * 0.9) { // Leave 10% buffer
                break;
            }

            result.splice(systemMessage ? 1 : 0, 0, msg);
            totalTokens += msgTokens;
        }

        return result;
    }
}
