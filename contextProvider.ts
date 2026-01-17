import { App, TFile, CachedMetadata } from 'obsidian';
import { estimateTokens, truncateToTokenLimit } from './tokenCounter';

export interface ContextSource {
	type: 'current' | 'linked' | 'backlinks' | 'tags' | 'folder';
	enabled: boolean;
}

export interface ContextConfig {
	sources: ContextSource[];
	maxNotesPerSource: number;
	maxTokensPerNote: number;
	linkDepth: number;
	excludeFolders: string[];
}

export interface GatheredContext {
	source: string;
	notePath: string;
	noteTitle: string;
	content: string;
	tokens: number;
}

export const DEFAULT_CONTEXT_CONFIG: ContextConfig = {
	sources: [
		{ type: 'current', enabled: true },
		{ type: 'linked', enabled: false },
		{ type: 'backlinks', enabled: false },
		{ type: 'tags', enabled: false },
		{ type: 'folder', enabled: false }
	],
	maxNotesPerSource: 5,
	maxTokensPerNote: 1000,
	linkDepth: 1,
	excludeFolders: ['templates', '.obsidian']
};

export class ContextProvider {
	private app: App;

	constructor(app: App) {
		this.app = app;
	}

	/**
	 * Gather context from multiple sources based on configuration
	 */
	async gatherContext(
		currentFile: TFile | null,
		currentContent: string,
		config: ContextConfig,
		provider: string = 'openai'
	): Promise<GatheredContext[]> {
		const contexts: GatheredContext[] = [];
		
		// Always include current note if enabled
		if (config.sources.find(s => s.type === 'current' && s.enabled)) {
			const truncated = truncateToTokenLimit(currentContent, config.maxTokensPerNote, provider);
			contexts.push({
				source: 'current',
				notePath: currentFile?.path || 'current',
				noteTitle: currentFile?.basename || 'Current Note',
				content: truncated,
				tokens: estimateTokens(truncated, provider)
			});
		}

		if (!currentFile) {
			return contexts;
		}

		// Gather linked notes
		if (config.sources.find(s => s.type === 'linked' && s.enabled)) {
			const linkedContexts = await this.getLinkedNotesContext(currentFile, config, provider);
			contexts.push(...linkedContexts);
		}

		// Gather backlinks
		if (config.sources.find(s => s.type === 'backlinks' && s.enabled)) {
			const backlinkContexts = await this.getBacklinksContext(currentFile, config, provider);
			contexts.push(...backlinkContexts);
		}

		// Gather same-tag notes
		if (config.sources.find(s => s.type === 'tags' && s.enabled)) {
			const tagContexts = await this.getTagContexts(currentFile, config, provider);
			contexts.push(...tagContexts);
		}

		// Gather same-folder notes
		if (config.sources.find(s => s.type === 'folder' && s.enabled)) {
			const folderContexts = await this.getFolderContexts(currentFile, config, provider);
			contexts.push(...folderContexts);
		}

		return contexts;
	}

	/**
	 * Get context from notes linked in the current note
	 */
	private async getLinkedNotesContext(
		file: TFile,
		config: ContextConfig,
		provider: string
	): Promise<GatheredContext[]> {
		const contexts: GatheredContext[] = [];
		const cache = this.app.metadataCache.getFileCache(file);
		
		if (!cache?.links) {
			return contexts;
		}

		const processedPaths = new Set<string>();
		const linksToProcess = [...cache.links];
		let depth = 0;

		while (linksToProcess.length > 0 && depth < config.linkDepth && contexts.length < config.maxNotesPerSource) {
			const currentLevelLinks = [...linksToProcess];
			linksToProcess.length = 0;

			for (const link of currentLevelLinks) {
				if (contexts.length >= config.maxNotesPerSource) break;

				const linkedFile = this.app.metadataCache.getFirstLinkpathDest(link.link, file.path);
				
				if (!linkedFile || processedPaths.has(linkedFile.path)) continue;
				if (this.isExcluded(linkedFile.path, config.excludeFolders)) continue;

				processedPaths.add(linkedFile.path);

				try {
					const content = await this.app.vault.read(linkedFile);
					const truncated = truncateToTokenLimit(content, config.maxTokensPerNote, provider);
					
					contexts.push({
						source: 'linked',
						notePath: linkedFile.path,
						noteTitle: linkedFile.basename,
						content: truncated,
						tokens: estimateTokens(truncated, provider)
					});

					// Add nested links for next depth level
					if (depth < config.linkDepth - 1) {
						const linkedCache = this.app.metadataCache.getFileCache(linkedFile);
						if (linkedCache?.links) {
							linksToProcess.push(...linkedCache.links);
						}
					}
				} catch (error) {
					console.error(`Failed to read linked note: ${linkedFile.path}`, error);
				}
			}

			depth++;
		}

		return contexts;
	}

	/**
	 * Get context from notes that link TO the current note
	 */
	private async getBacklinksContext(
		file: TFile,
		config: ContextConfig,
		provider: string
	): Promise<GatheredContext[]> {
		const contexts: GatheredContext[] = [];
		
		// Find all files that link to this file by scanning all files
		const allFiles = this.app.vault.getMarkdownFiles();
		const backlinkFiles: TFile[] = [];
		
		for (const otherFile of allFiles) {
			if (otherFile.path === file.path) continue;
			
			const cache = this.app.metadataCache.getFileCache(otherFile);
			if (!cache?.links) continue;
			
			// Check if any link points to our file
			const hasLinkToFile = cache.links.some(link => {
				const linkedFile = this.app.metadataCache.getFirstLinkpathDest(link.link, otherFile.path);
				return linkedFile?.path === file.path;
			});
			
			if (hasLinkToFile) {
				backlinkFiles.push(otherFile);
			}
		}
		
		for (const backlinkFile of backlinkFiles.slice(0, config.maxNotesPerSource)) {
			if (this.isExcluded(backlinkFile.path, config.excludeFolders)) continue;

			try {
				const content = await this.app.vault.read(backlinkFile);
				const truncated = truncateToTokenLimit(content, config.maxTokensPerNote, provider);
				
				contexts.push({
					source: 'backlink',
					notePath: backlinkFile.path,
					noteTitle: backlinkFile.basename,
					content: truncated,
					tokens: estimateTokens(truncated, provider)
				});
			} catch (error) {
				console.error(`Failed to read backlink: ${backlinkFile.path}`, error);
			}
		}

		return contexts;
	}

	/**
	 * Get context from notes with the same tags
	 */
	private async getTagContexts(
		file: TFile,
		config: ContextConfig,
		provider: string
	): Promise<GatheredContext[]> {
		const contexts: GatheredContext[] = [];
		const cache = this.app.metadataCache.getFileCache(file);
		
		if (!cache?.tags) {
			return contexts;
		}

		const currentTags = new Set(cache.tags.map(t => t.tag));
		const processedPaths = new Set<string>([file.path]);

		// Search all files for matching tags
		const allFiles = this.app.vault.getMarkdownFiles();
		
		for (const otherFile of allFiles) {
			if (contexts.length >= config.maxNotesPerSource) break;
			if (processedPaths.has(otherFile.path)) continue;
			if (this.isExcluded(otherFile.path, config.excludeFolders)) continue;

			const otherCache = this.app.metadataCache.getFileCache(otherFile);
			if (!otherCache?.tags) continue;

			const otherTags = otherCache.tags.map(t => t.tag);
			const hasMatchingTag = otherTags.some(tag => currentTags.has(tag));

			if (hasMatchingTag) {
				processedPaths.add(otherFile.path);
				
				try {
					const content = await this.app.vault.read(otherFile);
					const truncated = truncateToTokenLimit(content, config.maxTokensPerNote, provider);
					
					contexts.push({
						source: 'tag',
						notePath: otherFile.path,
						noteTitle: otherFile.basename,
						content: truncated,
						tokens: estimateTokens(truncated, provider)
					});
				} catch (error) {
					console.error(`Failed to read tagged note: ${otherFile.path}`, error);
				}
			}
		}

		return contexts;
	}

	/**
	 * Get context from notes in the same folder
	 */
	private async getFolderContexts(
		file: TFile,
		config: ContextConfig,
		provider: string
	): Promise<GatheredContext[]> {
		const contexts: GatheredContext[] = [];
		const folder = file.parent;
		
		if (!folder) {
			return contexts;
		}

		const folderFiles = this.app.vault.getMarkdownFiles().filter(f => 
			f.parent?.path === folder.path && f.path !== file.path
		);

		for (const folderFile of folderFiles.slice(0, config.maxNotesPerSource)) {
			if (this.isExcluded(folderFile.path, config.excludeFolders)) continue;

			try {
				const content = await this.app.vault.read(folderFile);
				const truncated = truncateToTokenLimit(content, config.maxTokensPerNote, provider);
				
				contexts.push({
					source: 'folder',
					notePath: folderFile.path,
					noteTitle: folderFile.basename,
					content: truncated,
					tokens: estimateTokens(truncated, provider)
				});
			} catch (error) {
				console.error(`Failed to read folder note: ${folderFile.path}`, error);
			}
		}

		return contexts;
	}

	/**
	 * Check if a path should be excluded
	 */
	private isExcluded(path: string, excludeFolders: string[]): boolean {
		const pathLower = path.toLowerCase();
		return excludeFolders.some(folder => pathLower.startsWith(folder.toLowerCase()));
	}

	/**
	 * Format gathered contexts into a single context string
	 */
	formatContextsForPrompt(contexts: GatheredContext[]): string {
		if (contexts.length === 0) {
			return '';
		}

		let formatted = '';
		
		// Group by source
		const bySource: Record<string, GatheredContext[]> = {};
		contexts.forEach(ctx => {
			if (!bySource[ctx.source]) {
				bySource[ctx.source] = [];
			}
			bySource[ctx.source].push(ctx);
		});

		for (const [source, ctxs] of Object.entries(bySource)) {
			const sourceLabel = this.getSourceLabel(source);
			formatted += `\n--- ${sourceLabel} ---\n`;
			
			ctxs.forEach(ctx => {
				if (source !== 'current') {
					formatted += `\n[${ctx.noteTitle}]\n`;
				}
				formatted += `${ctx.content}\n`;
			});
		}

		return formatted;
	}

	private getSourceLabel(source: string): string {
		const labels: Record<string, string> = {
			'current': 'Current Note',
			'linked': 'Linked Notes',
			'backlink': 'Notes Linking Here',
			'tag': 'Notes with Same Tags',
			'folder': 'Notes in Same Folder'
		};
		return labels[source] || source;
	}
}
