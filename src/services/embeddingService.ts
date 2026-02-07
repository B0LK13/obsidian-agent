import { requestUrl } from 'obsidian';
import { ObsidianAgentSettings } from '../../settings';

export interface EmbeddingResult {
    vector: number[];
    tokensUsed: number;
}

export class EmbeddingService {
    private settings: ObsidianAgentSettings;

    constructor(settings: ObsidianAgentSettings) {
        this.settings = settings;
    }

    async generateEmbedding(text: string): Promise<EmbeddingResult> {
        // Validation
        if (!text || text.trim().length === 0) {
            throw new Error('Text is empty');
        }

        const provider = this.settings.embeddingConfig?.provider || 'openai';

        if (provider === 'local') {
             throw new Error('Local (Transformers.js) embeddings not yet implemented');
        }

        if (provider === 'ollama') {
            return this.generateOllamaEmbedding(text);
        }

        // Default to OpenAI
        return this.generateOpenAIEmbedding(text);
    }

    private async generateOllamaEmbedding(text: string): Promise<EmbeddingResult> {
        const ollamaUrl = this.settings.customApiUrl || 'http://localhost:11434';
        const model = this.settings.embeddingConfig?.model || 'llama2';

        const response = await requestUrl({
            url: `${ollamaUrl}/api/embeddings`,
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                model: model,
                prompt: text
            })
        });

        if (response.status !== 200) {
            throw new Error(`Ollama Embedding failed: ${response.status} - ${response.text}`);
        }

        const data = response.json;
        // Ollama returns { "embedding": [ ... ] }
        return {
            vector: data.embedding,
            tokensUsed: 0 // Ollama doesn't typically report tokens for embeddings
        };
    }

    private async generateOpenAIEmbedding(text: string): Promise<EmbeddingResult> {
        if (!this.settings.apiKey) {
            throw new Error('OpenAI API key is required for embeddings');
        }

        const response = await requestUrl({
            url: 'https://api.openai.com/v1/embeddings',
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${this.settings.apiKey}`
            },
            body: JSON.stringify({
                input: text,
                model: this.settings.embeddingConfig?.model || 'text-embedding-3-small'
            })
        });

        if (response.status !== 200) {
            throw new Error(`Embedding request failed: ${response.status} - ${response.text}`);
        }

        const data = response.json;
        return {
            vector: data.data[0].embedding,
            tokensUsed: data.usage.total_tokens
        };
    }
}
