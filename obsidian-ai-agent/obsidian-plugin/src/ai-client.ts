/**
 * Local AI Client - Platform Independent
 * Connects to local LLM, Embeddings, and Vector DB servers
 * Enforces localhost-only connections
 */

export interface AIHealthStatus {
    llm: boolean;
    embeddings: boolean;
    vector: boolean;
}

export interface ChatMessage {
    role: 'system' | 'user' | 'assistant';
    content: string;
}

export interface ChatRequest {
    model: string;
    messages: ChatMessage[];
    temperature?: number;
    max_tokens?: number;
    stream?: boolean;
}

export class LocalAIClient {
    private settings: {
        llmEndpoint: string;
        embedEndpoint: string;
        vectorEndpoint: string;
        defaultModel: string;
    };

    constructor(settings: LocalAIClient['settings']) {
        this.settings = settings;
        this.validateEndpoints();
    }

    /**
     * Validate that all endpoints are localhost
     * This enforces the local-only security requirement
     */
    private validateEndpoints(): void {
        const endpoints = [
            { name: 'LLM', url: this.settings.llmEndpoint },
            { name: 'Embeddings', url: this.settings.embedEndpoint },
            { name: 'Vector DB', url: this.settings.vectorEndpoint }
        ];

        for (const endpoint of endpoints) {
            const url = new URL(endpoint.url);
            if (url.hostname !== '127.0.0.1' && url.hostname !== 'localhost' && url.hostname !== '::1') {
                throw new Error(
                    `Security violation: ${endpoint.name} endpoint must be localhost. ` +
                    `Got: ${endpoint.url}. External connections are blocked.`
                );
            }
        }
    }

    /**
     * Check health of all AI services
     */
    async checkHealth(): Promise<AIHealthStatus> {
        const status: AIHealthStatus = {
            llm: false,
            embeddings: false,
            vector: false
        };

        try {
            const llmResponse = await fetch(`${this.settings.llmEndpoint}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
            status.llm = llmResponse.ok;
        } catch {
            status.llm = false;
        }

        try {
            const embedResponse = await fetch(`${this.settings.embedEndpoint}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
            status.embeddings = embedResponse.ok;
        } catch {
            status.embeddings = false;
        }

        try {
            const vectorResponse = await fetch(`${this.settings.vectorEndpoint}/health`, {
                method: 'GET',
                signal: AbortSignal.timeout(5000)
            });
            status.vector = vectorResponse.ok;
        } catch {
            status.vector = false;
        }

        return status;
    }

    /**
     * Send chat completion request to local LLM
     */
    async chat(prompt: string, context?: string): Promise<string> {
        const messages: ChatMessage[] = [];

        if (context) {
            messages.push({
                role: 'system',
                content: `You are a helpful AI assistant with access to the user's knowledge base. Context: ${context}`
            });
        }

        messages.push({
            role: 'user',
            content: prompt
        });

        const request: ChatRequest = {
            model: this.settings.defaultModel,
            messages,
            temperature: 0.7,
            max_tokens: 2048,
            stream: false
        };

        try {
            const response = await fetch(`${this.settings.llmEndpoint}/v1/chat/completions`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request),
                signal: AbortSignal.timeout(60000) // 60 second timeout
            });

            if (!response.ok) {
                const error = await response.text();
                throw new Error(`LLM request failed: ${error}`);
            }

            const data = await response.json();
            return data.choices[0]?.message?.content || 'No response from AI';
        } catch (error) {
            console.error('AI chat error:', error);
            return `Error: ${error.message}. Make sure the local AI stack is running.`;
        }
    }

    /**
     * Generate embeddings for text
     */
    async embed(text: string): Promise<number[]> {
        try {
            const response = await fetch(`${this.settings.embedEndpoint}/embed`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ input: text }),
                signal: AbortSignal.timeout(10000)
            });

            if (!response.ok) {
                throw new Error(`Embedding request failed: ${await response.text()}`);
            }

            const data = await response.json();
            return data.data[0]?.embedding || [];
        } catch (error) {
            console.error('Embedding error:', error);
            throw error;
        }
    }

    /**
     * Query the vector database
     */
    async queryVectorDB(embedding: number[], nResults: number = 5): Promise<any[]> {
        try {
            const response = await fetch(`${this.settings.vectorEndpoint}/query`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    embedding,
                    n_results: nResults
                }),
                signal: AbortSignal.timeout(10000)
            });

            if (!response.ok) {
                throw new Error(`Vector query failed: ${await response.text()}`);
            }

            const data = await response.json();
            return data.results || [];
        } catch (error) {
            console.error('Vector DB error:', error);
            return [];
        }
    }

    /**
     * Add documents to vector database
     */
    async addToVectorDB(documents: { id: string; content: string; metadata: any; embedding: number[] }[]): Promise<void> {
        try {
            const response = await fetch(`${this.settings.vectorEndpoint}/add`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ documents }),
                signal: AbortSignal.timeout(30000)
            });

            if (!response.ok) {
                throw new Error(`Add to vector DB failed: ${await response.text()}`);
            }
        } catch (error) {
            console.error('Add to vector DB error:', error);
            throw error;
        }
    }
}
