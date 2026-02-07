/**
 * OpenAI service for PKM Agent plugin.
 */

import OpenAI from 'openai';

export const AGENT_SYSTEM_PROMPT = `You are an AI assistant integrated into Obsidian, a personal knowledge management application.
You help users manage their notes, create content, search their vault, and organize information.

You have access to tools that can:
- Create, read, update, and delete notes
- Search the vault for specific content
- Manage tags and links
- Create daily notes
- Analyze vault statistics

Be concise, helpful, and proactive in suggesting ways to improve the user's knowledge management.`;

export interface ChatMessage {
    role: 'system' | 'user' | 'assistant' | 'tool';
    content: string | null;
    tool_calls?: any[];
    tool_call_id?: string;
    name?: string;
}

export interface OpenAIConfig {
    apiKey: string;
    model: string;
    baseUrl?: string;
    temperature?: number;
    maxTokens?: number;
}

export class OpenAIService {
    private client: OpenAI;
    private config: OpenAIConfig;

    constructor(config: OpenAIConfig) {
        this.config = config;
        this.client = new OpenAI({
            apiKey: config.apiKey,
            baseURL: config.baseUrl || 'https://api.openai.com/v1',
            dangerouslyAllowBrowser: true,
        });
    }

    async chat(
        messages: ChatMessage[],
        tools?: any[],
        onStream?: (chunk: string) => void
    ): Promise<ChatMessage> {
        const params: any = {
            model: this.config.model,
            messages,
            temperature: this.config.temperature ?? 0.7,
            max_tokens: this.config.maxTokens ?? 4096,
        };

        if (tools && tools.length > 0) {
            params.tools = tools;
            params.tool_choice = 'auto';
        }

        if (onStream) {
            params.stream = true;
            const stream = await this.client.chat.completions.create(params);

            let content = '';
            let toolCalls: any[] = [];

            for await (const chunk of stream as any) {
                const delta = chunk.choices[0]?.delta;

                if (delta?.content) {
                    content += delta.content;
                    onStream(delta.content);
                }

                if (delta?.tool_calls) {
                    for (const tc of delta.tool_calls) {
                        if (tc.index !== undefined) {
                            if (!toolCalls[tc.index]) {
                                toolCalls[tc.index] = {
                                    id: tc.id || '',
                                    type: 'function',
                                    function: { name: '', arguments: '' },
                                };
                            }
                            if (tc.id) toolCalls[tc.index].id = tc.id;
                            if (tc.function?.name) toolCalls[tc.index].function.name += tc.function.name;
                            if (tc.function?.arguments) toolCalls[tc.index].function.arguments += tc.function.arguments;
                        }
                    }
                }
            }

            return {
                role: 'assistant',
                content: content || null,
                tool_calls: toolCalls.length > 0 ? toolCalls : undefined,
            };
        } else {
            const response = await this.client.chat.completions.create(params);
            const choice = response.choices[0];

            return {
                role: 'assistant',
                content: choice.message.content,
                tool_calls: choice.message.tool_calls,
            };
        }
    }
}
