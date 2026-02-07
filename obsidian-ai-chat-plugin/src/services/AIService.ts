import { Notice, requestUrl, RequestUrlParam, RequestUrlResponse } from 'obsidian';
import { AIChatNotesSettings } from '../../main';

export interface AIRequest {
prompt: string;
model?: string;
context?: string[];
temperature?: number;
maxTokens?: number;
}

export interface AIResponse {
content: string;
tokensUsed?: number;
model: string;
}

const DEFAULT_EMBEDDING_DIMENSION = 384;
const DEFAULT_TIMEOUT_MS = 30000;
const DEFAULT_RETRIES = 3;

const DEFAULT_MODELS = {
openai: 'gpt-4',
anthropic: 'claude-3-sonnet-20240229',
ollama: 'llama3.2',
openaiEmbedding: 'text-embedding-3-small',
ollamaEmbedding: 'nomic-embed-text',
} as const;

function isRetryableError(error: unknown): boolean {
if (error instanceof Error) {
const message = error.message.toLowerCase();
if (message.includes('network') || message.includes('timeout') || message.includes('econnreset')) {
return true;
}
}
if (typeof error === 'object' && error !== null && 'status' in error) {
const status = (error as { status: number }).status;
return status === 0 || status === 429 || (status >= 500 && status < 600);
}
return false;
}

function delay(ms: number): Promise<void> {
return new Promise(resolve => setTimeout(resolve, ms));
}

async function requestWithRetry(
params: RequestUrlParam,
options: { timeout?: number; retries?: number; operation?: string } = {}
): Promise<RequestUrlResponse> {
const timeout = options.timeout ?? DEFAULT_TIMEOUT_MS;
const maxRetries = options.retries ?? DEFAULT_RETRIES;
const operation = options.operation ?? 'API request';
let lastError: unknown;

for (let attempt = 0; attempt < maxRetries; attempt++) {
try {
const timeoutPromise = new Promise<never>((_, reject) => {
setTimeout(() => reject(new Error(operation + ' timed out after ' + timeout + 'ms')), timeout);
});
const response = await Promise.race([requestUrl(params), timeoutPromise]);
return response;
} catch (error) {
lastError = error;
if (!isRetryableError(error)) throw error;
if (attempt === maxRetries - 1) break;
const backoffMs = Math.min(1000 * Math.pow(2, attempt), 10000);
console.log(operation + ' failed (attempt ' + (attempt + 1) + '/' + maxRetries + '), retrying in ' + backoffMs + 'ms...');
await delay(backoffMs);
}
}
throw lastError;
}

export class AIService {
settings: AIChatNotesSettings;

constructor(settings: AIChatNotesSettings) {
this.settings = settings;
}

updateSettings(settings: AIChatNotesSettings) {
this.settings = settings;
}

async generateResponse(prompt: string, model?: string): Promise<string> {
switch (this.settings.aiProvider) {
case 'openai':
return this.callOpenAI(prompt, model);
case 'anthropic':
return this.callAnthropic(prompt, model);
case 'ollama':
return this.callOllama(prompt, model);
case 'local':
return this.callLocalModel(prompt, model);
default:
throw new Error('Unknown AI provider');
}
}

async callOpenAI(prompt: string, model?: string): Promise<string> {
if (!this.settings.openaiApiKey) {
throw new Error('OpenAI API key not configured');
}

const response = await requestWithRetry({
url: 'https://api.openai.com/v1/chat/completions',
method: 'POST',
headers: {
'Authorization': 'Bearer ' + this.settings.openaiApiKey,
'Content-Type': 'application/json'
},
body: JSON.stringify({
model: model || this.settings.defaultModel || DEFAULT_MODELS.openai,
messages: [{ role: 'user', content: prompt }],
temperature: this.settings.temperature,
max_tokens: this.settings.maxTokens
})
}, { operation: 'OpenAI chat completion' });

const data = response.json;
if (data.error) {
throw new Error(data.error.message);
}
return data.choices[0].message.content;
}

async callAnthropic(prompt: string, model?: string): Promise<string> {
if (!this.settings.anthropicApiKey) {
throw new Error('Anthropic API key not configured');
}

const response = await requestWithRetry({
url: 'https://api.anthropic.com/v1/messages',
method: 'POST',
headers: {
'x-api-key': this.settings.anthropicApiKey,
'Content-Type': 'application/json',
'anthropic-version': '2023-06-01'
},
body: JSON.stringify({
model: model || this.settings.defaultModel || DEFAULT_MODELS.anthropic,
max_tokens: this.settings.maxTokens,
temperature: this.settings.temperature,
messages: [{ role: 'user', content: prompt }]
})
}, { operation: 'Anthropic messages' });

const data = response.json;
if (data.error) {
throw new Error(data.error.message);
}
return data.content[0].text;
}

async callOllama(prompt: string, model?: string): Promise<string> {
const ollamaUrl = this.settings.ollamaUrl || 'http://localhost:11434';

try {
const response = await requestWithRetry({
url: ollamaUrl + '/api/generate',
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({
model: model || this.settings.defaultModel || DEFAULT_MODELS.ollama,
prompt: prompt,
stream: false,
options: {
temperature: this.settings.temperature,
num_predict: this.settings.maxTokens
}
})
}, { timeout: 60000, operation: 'Ollama generate' });

const data = response.json;
if (data.error) throw new Error(data.error);
return data.response;
} catch (error) {
if (error instanceof Error && error.message.includes('timed out')) {
throw new Error('Ollama request timed out. The model might be loading or the server is slow.');
}
if (typeof error === 'object' && error !== null && 'status' in error && (error as { status: number }).status === 0) {
throw new Error('Cannot connect to Ollama. Make sure Ollama is running on ' + ollamaUrl);
}
throw error;
}
}

async callLocalModel(prompt: string, model?: string): Promise<string> {
throw new Error('Local model not yet implemented. Please use Ollama for local AI.');
}

async generateEmbedding(text: string): Promise<number[]> {
if (this.settings.aiProvider === 'ollama') {
return this.generateOllamaEmbedding(text);
} else if (this.settings.aiProvider === 'openai') {
return this.generateOpenAIEmbedding(text);
}
return new Array(DEFAULT_EMBEDDING_DIMENSION).fill(0);
}

async generateOllamaEmbedding(text: string): Promise<number[]> {
const ollamaUrl = this.settings.ollamaUrl || 'http://localhost:11434';
const model = this.settings.embeddingModel || DEFAULT_MODELS.ollamaEmbedding;

const response = await requestWithRetry({
url: ollamaUrl + '/api/embeddings',
method: 'POST',
headers: { 'Content-Type': 'application/json' },
body: JSON.stringify({ model: model, prompt: text })
}, { timeout: 30000, operation: 'Ollama embedding' });

const data = response.json;
return data.embedding;
}

async generateOpenAIEmbedding(text: string): Promise<number[]> {
if (!this.settings.openaiApiKey) {
throw new Error('OpenAI API key not configured');
}

const response = await requestWithRetry({
url: 'https://api.openai.com/v1/embeddings',
method: 'POST',
headers: {
'Authorization': 'Bearer ' + this.settings.openaiApiKey,
'Content-Type': 'application/json'
},
body: JSON.stringify({
model: this.settings.embeddingModel || DEFAULT_MODELS.openaiEmbedding,
input: text
})
}, { operation: 'OpenAI embedding' });

const data = response.json;
return data.data[0].embedding;
}

async summarizeText(text: string, maxLength: number = 200): Promise<string> {
const prompt = 'Summarize the following text in ' + maxLength + ' characters or less:\n\n' + text;
return this.generateResponse(prompt);
}

async extractKeyPoints(text: string): Promise<string[]> {
const prompt = 'Extract the key points from the following text. Format each point starting with a dash (-):\n\n' + text;
const response = await this.generateResponse(prompt);
return response.split('\n').filter(line => line.trim().startsWith('-') || line.trim().startsWith('•'));
}

async suggestTags(content: string, existingTags: string[]): Promise<string[]> {
const prompt = 'Suggest relevant tags for the following content. Return only the tags separated by commas. Existing tags: ' + existingTags.join(', ') + '\n\nContent:\n' + content;
const response = await this.generateResponse(prompt);
return response.split(',').map(tag => tag.trim()).filter(tag => tag);
}

async answerQuestion(question: string, context: string): Promise<string> {
const prompt = 'Based on the following context, answer the question.\n\nContext:\n' + context + '\n\nQuestion: ' + question;
return this.generateResponse(prompt);
}
}
