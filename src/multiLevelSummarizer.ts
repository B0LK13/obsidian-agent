/**
 * Multi-Level Content Summarization & Synthesis
 * Addresses Issue #50: Multi-Level Content Summarization & Synthesis
 * 
 * Provides multiple levels of summarization:
 * - Quick (TL;DR) - 1-2 sentences
 * - Standard - Paragraph summary
 * - Detailed - Multiple paragraphs with key points
 * - Academic - Structured with abstract, methods, findings
 * - Cross-Note Synthesis - Synthesize across multiple notes
 */

import { App, TFile, Vault } from 'obsidian';
import { AIService } from '../aiService';
import { Validators } from './validators';

export type SummaryLevel = 'quick' | 'standard' | 'detailed' | 'academic';
export type SynthesisMode = 'thematic' | 'chronological' | 'comparative' | 'argumentative';

export interface SummaryOptions {
	level: SummaryLevel;
	includeSections?: boolean;
	includeKeyPoints?: boolean;
	includeQuotes?: boolean;
	maxLength?: number;
	preserveStructure?: boolean;
}

export interface SynthesisOptions {
	mode: SynthesisMode;
	topic?: string;
	includeCitations?: boolean;
	identifyGaps?: boolean;
	findContradictions?: boolean;
}

export interface SummaryResult {
	summary: string;
	level: SummaryLevel;
	wordCount: number;
	keyPoints?: string[];
	quotes?: string[];
	sections?: Map<string, string>;
}

export interface SynthesisResult {
	synthesis: string;
	mode: SynthesisMode;
	sources: string[];
	themes?: string[];
	contradictions?: string[];
	gaps?: string[];
	citations: Map<string, string[]>;
}

const DEFAULT_SUMMARY_OPTIONS: SummaryOptions = {
	level: 'standard',
	includeSections: false,
	includeKeyPoints: true,
	includeQuotes: false,
	maxLength: 0,
	preserveStructure: false
};

const DEFAULT_SYNTHESIS_OPTIONS: SynthesisOptions = {
	mode: 'thematic',
	includeCitations: true,
	identifyGaps: true,
	findContradictions: true
};

export class MultiLevelSummarizer {
	private vault: Vault;
	private aiService: AIService;

	constructor(app: App, aiService: AIService) {
		Validators.required(app, 'app');
		Validators.required(aiService, 'aiService');
		this.vault = app.vault;
		this.aiService = aiService;
	}

	/**
	 * Summarize a single note at specified level
	 */
	async summarizeNote(
		file: TFile,
		options: Partial<SummaryOptions> = {}
	): Promise<SummaryResult> {
		const opts = { ...DEFAULT_SUMMARY_OPTIONS, ...options };
		const content = await this.vault.read(file);

		// Extract sections if needed
		const sections = opts.includeSections ? this.extractSections(content) : null;

		// Build appropriate prompt for level
		const prompt = this.buildSummaryPrompt(content, file.basename, opts, sections);

		// Get AI summary
		const result = await this.aiService.generateCompletion(prompt);
		const summary = result.text.trim();

		// Extract key points if requested
		const keyPoints = opts.includeKeyPoints ? await this.extractKeyPoints(content) : undefined;

		// Extract quotes if requested
		const quotes = opts.includeQuotes ? this.extractQuotes(content) : undefined;

		return {
			summary,
			level: opts.level,
			wordCount: summary.split(/\s+/).length,
			keyPoints,
			quotes,
			sections: sections || undefined
		};
	}

	/**
	 * Synthesize multiple notes
	 */
	async synthesizeNotes(
		files: TFile[],
		options: Partial<SynthesisOptions> = {}
	): Promise<SynthesisResult> {
		const opts = { ...DEFAULT_SYNTHESIS_OPTIONS, ...options };

		// Read all files
		const contents = await Promise.all(
			files.map(async file => ({
				file,
				content: await this.vault.read(file)
			}))
		);

		// Build synthesis prompt
		const prompt = this.buildSynthesisPrompt(contents, opts);

		// Get AI synthesis
		const result = await this.aiService.generateCompletion(prompt);
		const synthesis = result.text.trim();

		// Extract components
		const themes = opts.mode === 'thematic' ? await this.extractThemes(synthesis) : undefined;
		const contradictions = opts.findContradictions ? this.identifyContradictions(synthesis) : undefined;
		const gaps = opts.identifyGaps ? this.identifyGaps(synthesis) : undefined;
		const citations = opts.includeCitations ? this.extractCitations(synthesis, files) : new Map();

		return {
			synthesis,
			mode: opts.mode,
			sources: files.map(f => f.basename),
			themes,
			contradictions,
			gaps,
			citations
		};
	}

	/**
	 * Generate progressive summaries (quick → standard → detailed)
	 */
	async generateProgressiveSummary(file: TFile): Promise<Map<SummaryLevel, string>> {
		const summaries = new Map<SummaryLevel, string>();

		const levels: SummaryLevel[] = ['quick', 'standard', 'detailed'];

		for (const level of levels) {
			const result = await this.summarizeNote(file, { level });
			summaries.set(level, result.summary);
		}

		return summaries;
	}

	/**
	 * Build summary prompt based on level
	 */
	private buildSummaryPrompt(
		content: string,
		title: string,
		options: SummaryOptions,
		sections: Map<string, string> | null
	): string {
		const prompts: Record<SummaryLevel, string> = {
			quick: `Provide a TL;DR summary of "${title}" in 1-2 sentences. Focus on the single most important idea.

Content:
${content}

TL;DR:`,

			standard: `Summarize "${title}" in a concise paragraph (3-5 sentences). Include the main points and key takeaways.

Content:
${content}

Summary:`,

			detailed: `Create a detailed summary of "${title}" with the following structure:
1. Overview (2-3 sentences)
2. Key Points (bulleted list of 5-7 main ideas)
3. Important Details (2-3 paragraphs covering significant information)
4. Conclusion (1-2 sentences)

Content:
${content}

Detailed Summary:`,

			academic: `Provide an academic-style summary of "${title}" with this structure:

**Abstract:** (150-200 words summarizing the entire content)

**Main Arguments/Claims:** (Bulleted list of key arguments or claims made)

**Methods/Approach:** (If applicable, how the topic is explored or analyzed)

**Key Findings/Insights:** (Main discoveries, conclusions, or insights)

**Implications:** (Significance and potential applications)

**References:** (Key concepts, theories, or sources mentioned)

Content:
${content}

Academic Summary:`
		};

		let prompt = prompts[options.level];

		// Add section-by-section if requested
		if (options.includeSections && sections && sections.size > 0) {
			prompt += '\n\nSummarize each major section:\n';
			for (const [heading, sectionContent] of sections) {
				prompt += `\n## ${heading}\n${sectionContent.substring(0, 500)}...\n`;
			}
		}

		// Add length constraint if specified
		if (options.maxLength && options.maxLength > 0) {
			prompt += `\n\nKeep the summary under ${options.maxLength} words.`;
		}

		return prompt;
	}

	/**
	 * Build synthesis prompt based on mode
	 */
	private buildSynthesisPrompt(
		contents: Array<{ file: TFile; content: string }>,
		options: SynthesisOptions
	): string {
		const topic = options.topic || 'the provided notes';

		const basePrompt = `Synthesize insights across ${contents.length} notes about ${topic}.

Notes:
${contents.map((c) => `
### [[${c.file.basename}]]
${this.extractKeyContent(c.content)}
`).join('\n')}
`;

		const modeInstructions: Record<SynthesisMode, string> = {
			thematic: `Organize the synthesis by themes:
1. Identify 3-5 major themes across the notes
2. For each theme, synthesize what the notes say
3. Note where notes agree, differ, or complement each other
4. Include [[note references]] for all claims`,

			chronological: `Organize the synthesis chronologically:
1. Identify the timeline or progression of ideas
2. Show how concepts developed or evolved
3. Highlight turning points or key developments
4. Connect earlier and later ideas`,

			comparative: `Organize the synthesis as a comparison:
1. Identify areas of agreement between notes
2. Highlight differences in perspective or approach
3. Analyze why differences exist
4. Synthesize a balanced view incorporating all perspectives`,

			argumentative: `Organize the synthesis as an argument:
1. Identify the main claim or thesis supported by these notes
2. Present supporting evidence from across notes
3. Address counterarguments or limitations
4. Build a coherent, well-supported argument`
		};

		let prompt = basePrompt + '\n' + modeInstructions[options.mode];

		if (options.identifyGaps) {
			prompt += '\n\n**Knowledge Gaps:** Identify what information is missing or underexplored.';
		}

		if (options.findContradictions) {
			prompt += '\n\n**Contradictions:** Note any contradictions or tensions between the notes.';
		}

		if (options.includeCitations) {
			prompt += '\n\nUse [[note name]] format to cite sources for all claims.';
		}

		return prompt;
	}

	/**
	 * Extract sections from content
	 */
	private extractSections(content: string): Map<string, string> {
		const sections = new Map<string, string>();
		const headingRegex = /^(#{1,6})\s+(.+)$/gm;
		
		const headings: Array<{ level: number; title: string; position: number }> = [];
		let match;

		while ((match = headingRegex.exec(content)) !== null) {
			headings.push({
				level: match[1].length,
				title: match[2],
				position: match.index
			});
		}

		// Extract content for each section
		for (let i = 0; i < headings.length; i++) {
			const start = headings[i].position;
			const end = i < headings.length - 1 ? headings[i + 1].position : content.length;
			const sectionContent = content.substring(start, end).trim();
			
			sections.set(headings[i].title, sectionContent);
		}

		return sections;
	}

	/**
	 * Extract key points using simple heuristics
	 */
	private async extractKeyPoints(content: string): Promise<string[]> {
		const keyPoints: string[] = [];

		// Extract numbered or bulleted lists
		const listItems = content.match(/^[\s]*[-*•]\s+(.+)$/gm);
		if (listItems && listItems.length > 0) {
			keyPoints.push(...listItems.map(item => item.replace(/^[\s]*[-*•]\s+/, '').trim()).slice(0, 5));
		}

		// Extract first sentence of each paragraph (up to 5)
		const paragraphs = content.split(/\n\n+/);
		for (const para of paragraphs.slice(0, 5)) {
			const firstSentence = para.match(/^[^.!?]+[.!?]/);
			if (firstSentence) {
				const point = firstSentence[0].trim();
				if (point.length > 20 && !keyPoints.includes(point)) {
					keyPoints.push(point);
				}
			}
		}

		return keyPoints.slice(0, 7);
	}

	/**
	 * Extract notable quotes
	 */
	private extractQuotes(content: string): string[] {
		const quotes: string[] = [];

		// Extract blockquotes
		const blockquotes = content.match(/^>\s+(.+)$/gm);
		if (blockquotes) {
			quotes.push(...blockquotes.map(q => q.replace(/^>\s+/, '').trim()));
		}

		// Extract quoted text
		const quotedText = content.match(/"([^"]{20,200})"/g);
		if (quotedText) {
			quotes.push(...quotedText.slice(0, 3));
		}

		return quotes.slice(0, 5);
	}

	/**
	 * Extract key content (first part of each note)
	 */
	private extractKeyContent(content: string, maxChars: number = 1000): string {
		// Remove code blocks
		let cleaned = content.replace(/```[\s\S]*?```/g, '[code]');
		
		// Keep first part
		cleaned = cleaned.substring(0, maxChars);
		
		// Try to end at sentence boundary
		const lastPeriod = cleaned.lastIndexOf('.');
		if (lastPeriod > maxChars * 0.7) {
			cleaned = cleaned.substring(0, lastPeriod + 1);
		}

		return cleaned + '...';
	}

	/**
	 * Extract themes from synthesis
	 */
	private async extractThemes(synthesis: string): Promise<string[]> {
		const themes: string[] = [];
		
		// Look for theme headers
		const themeHeaders = synthesis.match(/^#{2,3}\s+(.+)$/gm);
		if (themeHeaders) {
			themes.push(...themeHeaders.map(h => h.replace(/^#{2,3}\s+/, '').trim()));
		}

		return themes;
	}

	/**
	 * Identify contradictions mentioned in synthesis
	 */
	private identifyContradictions(synthesis: string): string[] {
		const contradictions: string[] = [];
		
		// Look for contradiction indicators
		const indicators = [
			'however', 'contradicts', 'conflicts with', 'disagrees',
			'on the other hand', 'in contrast', 'while', 'whereas'
		];

		const sentences = synthesis.split(/[.!?]+/);
		for (const sentence of sentences) {
			const lower = sentence.toLowerCase();
			if (indicators.some(ind => lower.includes(ind))) {
				contradictions.push(sentence.trim());
			}
		}

		return contradictions.slice(0, 5);
	}

	/**
	 * Identify knowledge gaps mentioned in synthesis
	 */
	private identifyGaps(synthesis: string): string[] {
		const gaps: string[] = [];
		
		// Look for gap indicators
		const indicators = [
			'missing', 'unclear', 'not addressed', 'unexplored',
			'gap', 'unknown', 'needs further', 'requires more'
		];

		const sentences = synthesis.split(/[.!?]+/);
		for (const sentence of sentences) {
			const lower = sentence.toLowerCase();
			if (indicators.some(ind => lower.includes(ind))) {
				gaps.push(sentence.trim());
			}
		}

		return gaps.slice(0, 5);
	}

	/**
	 * Extract citations from synthesis
	 */
	private extractCitations(synthesis: string, sources: TFile[]): Map<string, string[]> {
		const citations = new Map<string, string[]>();

		// Find all [[note]] references
		const linkRegex = /\[\[([^\]]+)\]\]/g;
		let match;

		while ((match = linkRegex.exec(synthesis)) !== null) {
			const noteName = match[1].split('|')[0].trim();
			
			// Find matching source
			const source = sources.find(f => f.basename === noteName);
			if (source) {
				if (!citations.has(noteName)) {
					citations.set(noteName, []);
				}
				
				// Get surrounding context
				const start = Math.max(0, match.index - 100);
				const end = Math.min(synthesis.length, match.index + 100);
				const context = synthesis.substring(start, end).trim();
				
				citations.get(noteName)!.push(context);
			}
		}

		return citations;
	}
}
