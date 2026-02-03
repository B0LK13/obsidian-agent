/**
 * Dead Link Detection and Repair Service
 * Addresses Issue #98: Implement Dead Link Detection and Repair
 */

import { App, TFile, Vault } from 'obsidian';
import { Validators } from './validators';

export interface DeadLink {
	sourceFile: string;
	sourcePath: string;
	linkText: string;
	linkTarget: string;
	lineNumber: number;
	type: 'wikilink' | 'markdown' | 'embed';
	suggestions?: string[];
}

export interface LinkScanResult {
	totalLinks: number;
	deadLinks: DeadLink[];
	brokenCount: number;
	scanDuration: number;
	filesScanned: number;
}

export interface LinkRepairResult {
	repairedCount: number;
	failedCount: number;
	repairs: Array<{
		file: string;
		oldLink: string;
		newLink: string;
		success: boolean;
	}>;
}

export class DeadLinkDetector {
	private app: App;
	private vault: Vault;

	constructor(app: App) {
		Validators.required(app, 'app');
		this.app = app;
		this.vault = app.vault;
	}

	/**
	 * Scan the entire vault for dead links
	 */
	async scanVault(progressCallback?: (progress: number, total: number) => void): Promise<LinkScanResult> {
		const startTime = Date.now();
		const deadLinks: DeadLink[] = [];
		const files = this.vault.getMarkdownFiles();
		let totalLinks = 0;

		for (let i = 0; i < files.length; i++) {
			const file = files[i];
			if (progressCallback) {
				progressCallback(i + 1, files.length);
			}

			const fileDeadLinks = await this.scanFile(file);
			deadLinks.push(...fileDeadLinks);
			
			// Count total links
			const cache = this.app.metadataCache.getFileCache(file);
			if (cache) {
				totalLinks += (cache.links?.length || 0) + (cache.embeds?.length || 0);
			}
		}

		return {
			totalLinks,
			deadLinks,
			brokenCount: deadLinks.length,
			scanDuration: Date.now() - startTime,
			filesScanned: files.length
		};
	}

	/**
	 * Scan a single file for dead links
	 */
	async scanFile(file: TFile): Promise<DeadLink[]> {
		if (!file || !(file instanceof TFile)) {
			return [];
		}

		const deadLinks: DeadLink[] = [];
		const cache = this.app.metadataCache.getFileCache(file);
		
		if (!cache) {
			return deadLinks;
		}

		// Check regular links
		if (cache.links) {
			for (const link of cache.links) {
				const target = this.resolveLink(link.link, file.path);
				if (!target) {
					deadLinks.push({
						sourceFile: file.basename,
						sourcePath: file.path,
						linkText: link.displayText || link.link,
						linkTarget: link.link,
						lineNumber: link.position?.start.line || 0,
						type: 'wikilink',
						suggestions: await this.findSuggestions(link.link)
					});
				}
			}
		}

		// Check embeds
		if (cache.embeds) {
			for (const embed of cache.embeds) {
				const target = this.resolveLink(embed.link, file.path);
				if (!target) {
					deadLinks.push({
						sourceFile: file.basename,
						sourcePath: file.path,
						linkText: embed.displayText || embed.link,
						linkTarget: embed.link,
						lineNumber: embed.position?.start.line || 0,
						type: 'embed',
						suggestions: await this.findSuggestions(embed.link)
					});
				}
			}
		}

		return deadLinks;
	}

	/**
	 * Resolve a link to a file
	 */
	private resolveLink(linkText: string, sourcePath: string): TFile | null {
		try {
			// Remove heading/block references
			const cleanLink = linkText.split('#')[0].split('^')[0];
			if (!cleanLink) return null;

			// Try to resolve the link
			const file = this.app.metadataCache.getFirstLinkpathDest(cleanLink, sourcePath);
			return file;
		} catch (error) {
			console.error('Error resolving link:', linkText, error);
			return null;
		}
	}

	/**
	 * Find similar files that might be the intended target
	 */
	private async findSuggestions(brokenLink: string): Promise<string[]> {
		const files = this.vault.getMarkdownFiles();
		
		// Clean the broken link
		const cleanLink = brokenLink.split('#')[0].split('^')[0].toLowerCase();
		
		// Calculate similarity scores
		const scored = files
			.map(file => ({
				file,
				score: this.calculateSimilarity(cleanLink, file.basename.toLowerCase())
			}))
			.filter(item => item.score > 0.3) // Minimum threshold
			.sort((a, b) => b.score - a.score)
			.slice(0, 5); // Top 5 suggestions

		return scored.map(item => item.file.path);
	}

	/**
	 * Calculate similarity between two strings (simple Levenshtein-like)
	 */
	private calculateSimilarity(str1: string, str2: string): number {
		const longer = str1.length > str2.length ? str1 : str2;
		const shorter = str1.length > str2.length ? str2 : str1;
		
		if (longer.length === 0) return 1.0;
		
		// Check for substring match
		if (longer.includes(shorter)) return 0.8;
		
		// Calculate edit distance
		const editDistance = this.levenshteinDistance(str1, str2);
		return (longer.length - editDistance) / longer.length;
	}

	/**
	 * Calculate Levenshtein distance between two strings
	 */
	private levenshteinDistance(str1: string, str2: string): number {
		const matrix: number[][] = [];

		for (let i = 0; i <= str2.length; i++) {
			matrix[i] = [i];
		}

		for (let j = 0; j <= str1.length; j++) {
			matrix[0][j] = j;
		}

		for (let i = 1; i <= str2.length; i++) {
			for (let j = 1; j <= str1.length; j++) {
				if (str2.charAt(i - 1) === str1.charAt(j - 1)) {
					matrix[i][j] = matrix[i - 1][j - 1];
				} else {
					matrix[i][j] = Math.min(
						matrix[i - 1][j - 1] + 1,
						matrix[i][j - 1] + 1,
						matrix[i - 1][j] + 1
					);
				}
			}
		}

		return matrix[str2.length][str1.length];
	}

	/**
	 * Repair dead links by replacing with suggestions
	 */
	async repairLinks(deadLinks: DeadLink[], autoRepair: boolean = false): Promise<LinkRepairResult> {
		const repairs: LinkRepairResult['repairs'] = [];
		let repairedCount = 0;
		let failedCount = 0;

		for (const deadLink of deadLinks) {
			// Only auto-repair if there's a clear suggestion
			if (!autoRepair && (!deadLink.suggestions || deadLink.suggestions.length === 0)) {
				failedCount++;
				continue;
			}

			const suggestion = deadLink.suggestions?.[0];
			if (!suggestion) {
				failedCount++;
				continue;
			}

			try {
				const file = this.vault.getAbstractFileByPath(deadLink.sourcePath);
				if (!(file instanceof TFile)) {
					failedCount++;
					repairs.push({
						file: deadLink.sourcePath,
						oldLink: deadLink.linkTarget,
						newLink: suggestion,
						success: false
					});
					continue;
				}

				// Read file content
				let content = await this.vault.read(file);
				
				// Get the suggested file's basename for the link
				const suggestedFile = this.vault.getAbstractFileByPath(suggestion);
				const newLinkText = suggestedFile instanceof TFile ? suggestedFile.basename : suggestion;

				// Replace the dead link
				const oldLinkPattern = deadLink.type === 'embed' 
					? `![[${deadLink.linkTarget}]]`
					: `[[${deadLink.linkTarget}]]`;
				const newLinkPattern = deadLink.type === 'embed'
					? `![[${newLinkText}]]`
					: `[[${newLinkText}]]`;

				if (content.includes(oldLinkPattern)) {
					content = content.replace(oldLinkPattern, newLinkPattern);
					await this.vault.modify(file, content);
					
					repairedCount++;
					repairs.push({
						file: deadLink.sourcePath,
						oldLink: deadLink.linkTarget,
						newLink: newLinkText,
						success: true
					});
				} else {
					failedCount++;
					repairs.push({
						file: deadLink.sourcePath,
						oldLink: deadLink.linkTarget,
						newLink: newLinkText,
						success: false
					});
				}
			} catch (error) {
				console.error('Error repairing link:', deadLink, error);
				failedCount++;
				repairs.push({
					file: deadLink.sourcePath,
					oldLink: deadLink.linkTarget,
					newLink: suggestion,
					success: false
				});
			}
		}

		return {
			repairedCount,
			failedCount,
			repairs
		};
	}

	/**
	 * Remove dead links from a file
	 */
	async removeDeadLinks(file: TFile, deadLinks: DeadLink[]): Promise<number> {
		try {
			let content = await this.vault.read(file);
			let removedCount = 0;

			const fileDeadLinks = deadLinks.filter(link => link.sourcePath === file.path);

			for (const deadLink of fileDeadLinks) {
				const pattern = deadLink.type === 'embed'
					? `![[${deadLink.linkTarget}]]`
					: `[[${deadLink.linkTarget}]]`;

				if (content.includes(pattern)) {
					// Replace with just the display text or remove entirely
					content = content.replace(pattern, deadLink.linkText || '');
					removedCount++;
				}
			}

			if (removedCount > 0) {
				await this.vault.modify(file, content);
			}

			return removedCount;
		} catch (error) {
			console.error('Error removing dead links:', error);
			return 0;
		}
	}

	/**
	 * Export dead links report as markdown
	 */
	generateReport(result: LinkScanResult): string {
		const lines: string[] = [];
		
		lines.push('# Dead Links Report\n');
		lines.push(`**Scan Date:** ${new Date().toISOString()}\n`);
		lines.push(`**Files Scanned:** ${result.filesScanned}`);
		lines.push(`**Total Links:** ${result.totalLinks}`);
		lines.push(`**Broken Links:** ${result.brokenCount}`);
		lines.push(`**Scan Duration:** ${result.scanDuration}ms\n`);

		if (result.deadLinks.length === 0) {
			lines.push('✅ No dead links found!\n');
		} else {
			lines.push('## Broken Links\n');
			
			// Group by source file
			const byFile = new Map<string, DeadLink[]>();
			for (const link of result.deadLinks) {
				if (!byFile.has(link.sourcePath)) {
					byFile.set(link.sourcePath, []);
				}
				byFile.get(link.sourcePath)!.push(link);
			}

			for (const [filePath, links] of byFile) {
				lines.push(`### [[${filePath}]]\n`);
				for (const link of links) {
					lines.push(`- **Line ${link.lineNumber}:** \`[[${link.linkTarget}]]\` (${link.type})`);
					if (link.suggestions && link.suggestions.length > 0) {
						lines.push(`  - Suggestions: ${link.suggestions.slice(0, 3).map(s => `[[${s}]]`).join(', ')}`);
					}
				}
				lines.push('');
			}
		}

		return lines.join('\n');
	}
}
