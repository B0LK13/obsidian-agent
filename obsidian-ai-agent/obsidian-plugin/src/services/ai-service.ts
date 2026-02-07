/**
 * AI Service - Main integration point for optimized LLM features
 * Connects to memory RAG, hallucination guard, and evaluation systems
 */

import { Notice, TFile } from 'obsidian';
import { LocalAIClient } from '../ai-client';

export interface AIServiceConfig {
    llmEndpoint: string;
    embedEndpoint: string;
    vectorEndpoint: string;
    useMemoryRAG: boolean;
    useHallucinationGuard: boolean;
    enableEvaluation: boolean;
}

export interface QueryResult {
    response: string;
    context: string;
    sources: string[];
    confidence: number;
    hallucinationCheck?: {
        score: number;
        passed: boolean;
        suggestions: string[];
    };
    evaluation?: {
        overall: number;
        dimensions: Record<string, number>;
    };
}

export class AIService {
    private config: AIServiceConfig;
    private client: LocalAIClient;

    constructor(config: AIServiceConfig) {
        this.config = config;
        this.client = new LocalAIClient(config);
    }

    async initialize(): Promise<boolean> {
        try {
            const health = await this.client.checkHealth();
            
            if (!health.llm || !health.embeddings) {
                new Notice('AI Service: Cannot connect to local AI stack');
                return false;
            }

            new Notice('AI Service: Initialized successfully');
            return true;
        } catch (error) {
            console.error('AI Service initialization failed:', error);
            new Notice('AI Service: Initialization failed');
            return false;
        }
    }

    async queryWithContext(query: string, contextFiles?: TFile[]): Promise<QueryResult> {
        try {
            // Get embedding for query
            const embedding = await this.client.embed(query);
            
            // Get context from vector DB
            const vectorResults = await this.client.queryVectorDB(embedding, 5);
            
            const context = vectorResults.map((r: any) => r.content).join('\n\n');
            const sources = vectorResults.map((r: any) => r.id);

            // Generate response
            const prompt = this.buildPrompt(query, context);
            const response = await this.client.chat(prompt);

            // Calculate confidence based on context quality
            const confidence = vectorResults.length > 0 ? 0.7 : 0.3;

            return {
                response,
                context,
                sources,
                confidence
            };

        } catch (error) {
            console.error('Query failed:', error);
            return {
                response: `Error: ${error.message}`,
                context: '',
                sources: [],
                confidence: 0
            };
        }
    }

    private buildPrompt(query: string, context: string): string {
        return `Based on the following context from my knowledge base, please answer the question.

Context:
${context || 'No relevant context found.'}

Question: ${query}

Please provide a clear, accurate answer.`;
    }

    async getStats(): Promise<any> {
        try {
            const response = await fetch(`${this.config.llmEndpoint}/admin/stats`);
            return await response.json();
        } catch (error) {
            return { error: error.message };
        }
    }
}
