import { TFile, Vault } from 'obsidian';
import AIChatNotesPlugin from '../../main';

interface NoteEmbedding {
	path: string;
	embedding: number[];
	lastModified: number;
}

export class SearchService {
	plugin: AIChatNotesPlugin;
	vault: Vault;
	embeddings: Map<string, NoteEmbedding> = new Map();
	isSyncing: boolean = false;
	
	constructor(plugin: AIChatNotesPlugin) {
		this.plugin = plugin;
		this.vault = plugin.app.vault;
		
		// Load embeddings from database
		this.loadEmbeddings();
	}
	
	async loadEmbeddings() {
		const data = await this.plugin.dbManager.getEmbeddings();
		for (const item of data) {
			this.embeddings.set(item.path, item);
		}
	}
	
	async syncEmbeddings() {
		if (this.isSyncing) return;
		this.isSyncing = true;
		
		try {
			const files = this.vault.getMarkdownFiles();
			
			for (const file of files) {
				const existing = this.embeddings.get(file.path);
				
				// Only re-embed if file has changed
				if (!existing || existing.lastModified !== file.stat.mtime) {
					const content = await this.vault.read(file);
					const embedding = await this.plugin.aiService.generateEmbedding(content);
					
					const noteEmbedding: NoteEmbedding = {
						path: file.path,
						embedding,
						lastModified: file.stat.mtime
					};
					
					this.embeddings.set(file.path, noteEmbedding);
					await this.plugin.dbManager.saveEmbedding(noteEmbedding);
				}
			}
			
			// Clean up deleted files
			for (const [path, _] of this.embeddings) {
				const file = this.vault.getAbstractFileByPath(path);
				if (!file) {
					this.embeddings.delete(path);
					await this.plugin.dbManager.deleteEmbedding(path);
				}
			}
		} finally {
			this.isSyncing = false;
		}
	}
	
	async semanticSearch(query: string): Promise<TFile[]> {
		if (!this.plugin.settings.enableSemanticSearch) {
			// Fall back to basic text search
			return this.basicSearch(query);
		}
		
		// Generate query embedding
		const queryEmbedding = await this.plugin.aiService.generateEmbedding(query);
		
		// Calculate similarities
		const similarities: { file: TFile; similarity: number }[] = [];
		
		for (const [path, noteEmbedding] of this.embeddings) {
			const file = this.vault.getAbstractFileByPath(path);
			if (file instanceof TFile) {
				const similarity = this.cosineSimilarity(queryEmbedding, noteEmbedding.embedding);
				similarities.push({ file, similarity });
			}
		}
		
		// Sort by similarity and return top results
		similarities.sort((a, b) => b.similarity - a.similarity);
		return similarities
			.filter(s => s.similarity > 0.7)
			.map(s => s.file);
	}
	
	basicSearch(query: string): TFile[] {
		const files = this.vault.getMarkdownFiles();
		const lowerQuery = query.toLowerCase();
		
		return files.filter(file => {
			return file.basename.toLowerCase().includes(lowerQuery) ||
				   file.path.toLowerCase().includes(lowerQuery);
		});
	}
	
	async findRelevantNotes(query: string, limit: number = 5): Promise<TFile[]> {
		return this.semanticSearch(query).then(files => files.slice(0, limit));
	}
	
	cosineSimilarity(a: number[], b: number[]): number {
		let dotProduct = 0;
		let normA = 0;
		let normB = 0;
		
		for (let i = 0; i < a.length; i++) {
			dotProduct += a[i] * b[i];
			normA += a[i] * a[i];
			normB += b[i] * b[i];
		}
		
		return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
	}
	
	async searchWithFilters(
		query: string,
		filters: {
			tags?: string[];
			folder?: string;
			dateRange?: { start: Date; end: Date };
		}
	): Promise<TFile[]> {
		let results = await this.semanticSearch(query);
		
		if (filters.folder) {
			results = results.filter(file => file.path.startsWith(filters.folder!));
		}
		
		if (filters.dateRange) {
			results = results.filter(file => {
				const mtime = new Date(file.stat.mtime);
				return mtime >= filters.dateRange!.start && mtime <= filters.dateRange!.end;
			});
		}
		
		// Tag filtering would require reading file content
		if (filters.tags && filters.tags.length > 0) {
			const filteredResults: TFile[] = [];
			for (const file of results) {
				const content = await this.vault.read(file);
				const hasTag = filters.tags!.some(tag => 
					content.includes(`#${tag}`) || 
					content.includes(`tag: ${tag}`)
				);
				if (hasTag) {
					filteredResults.push(file);
				}
			}
			results = filteredResults;
		}
		
		return results;
	}
	
	async getRelatedNotes(file: TFile, limit: number = 5): Promise<TFile[]> {
		const fileEmbedding = this.embeddings.get(file.path);
		if (!fileEmbedding) {
			// Generate embedding if not exists
			const content = await this.vault.read(file);
			const embedding = await this.plugin.aiService.generateEmbedding(content);
			
			const noteEmbedding: NoteEmbedding = {
				path: file.path,
				embedding,
				lastModified: file.stat.mtime
			};
			
			this.embeddings.set(file.path, noteEmbedding);
			await this.plugin.dbManager.saveEmbedding(noteEmbedding);
			
			return this.getRelatedNotes(file, limit);
		}
		
		// Find similar notes
		const similarities: { file: TFile; similarity: number }[] = [];
		
		for (const [path, noteEmbedding] of this.embeddings) {
			if (path === file.path) continue;
			
			const otherFile = this.vault.getAbstractFileByPath(path);
			if (otherFile instanceof TFile) {
				const similarity = this.cosineSimilarity(
					fileEmbedding.embedding,
					noteEmbedding.embedding
				);
				similarities.push({ file: otherFile, similarity });
			}
		}
		
		similarities.sort((a, b) => b.similarity - a.similarity);
		return similarities
			.filter(s => s.similarity > 0.75)
			.slice(0, limit)
			.map(s => s.file);
	}
}
