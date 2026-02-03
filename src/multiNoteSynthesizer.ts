/**
 * Multi-Note Synthesizer
 * 
 * Advanced vault-wide intelligence for synthesizing insights across multiple notes,
 * research assistance, argument mapping, and knowledge gap detection.
 * 
 * Features:
 * - Cross-note synthesis with citations
 * - Research assistant mode
 * - Argument mapping and extraction
 * - Contradiction detection
 * - Knowledge gap identification
 * - Research direction suggestions
 */

import { TFile, Vault, MetadataCache } from 'obsidian';
import { IntelligentContextEngine, ContextScore } from './contextEngine';
import { AIService } from '../aiService';

interface SynthesisResult {
	summary: string;
	keyInsights: string[];
	contradictions: string[];
	knowledgeGaps: string[];
	citations: Map<string, string[]>; // note -> quoted passages
	notesAnalyzed: number;
}

interface ResearchQuery {
	query: string;
	tags?: string[];
	folders?: string[];
	dateRange?: { start: number; end: number };
	maxNotes?: number;
}

interface ArgumentMap {
	claims: Claim[];
	evidence: Evidence[];
	relationships: ArgumentRelation[];
	logicalGaps: string[];
}

interface Claim {
	id: string;
	text: string;
	sourceNote: string;
	confidence: 'high' | 'medium' | 'low';
	type: 'thesis' | 'supporting' | 'counter';
}

interface Evidence {
	id: string;
	text: string;
	sourceNote: string;
	supportsClaims: string[]; // Claim IDs
	type: 'empirical' | 'logical' | 'anecdotal' | 'expert';
}

interface ArgumentRelation {
	from: string; // Claim/Evidence ID
	to: string; // Claim ID
	type: 'supports' | 'contradicts' | 'qualifies';
}

interface ResearchSuggestion {
	direction: string;
	reasoning: string;
	suggestedSources: string[];
	priority: 'high' | 'medium' | 'low';
}

export class MultiNoteSynthesizer {
	private vault: Vault;
	private metadataCache: MetadataCache;
	private contextEngine: IntelligentContextEngine;
	private aiService: AIService;

	constructor(
		vault: Vault,
		metadataCache: MetadataCache,
		contextEngine: IntelligentContextEngine,
		aiService: AIService
	) {
		this.vault = vault;
		this.metadataCache = metadataCache;
		this.contextEngine = contextEngine;
		this.aiService = aiService;
	}

	/**
	 * Synthesize insights from multiple notes
	 */
	async synthesizeNotes(
		notes: TFile[],
		focusQuery?: string
	): Promise<SynthesisResult> {
		const citations = new Map<string, string[]>();
		const contents: string[] = [];

		// Gather all note contents
		for (const note of notes) {
			const content = await this.vault.read(note);
			contents.push(`# ${note.basename}\n${content}`);
			
			// Extract important passages
			const passages = this.extractKeyPassages(content);
			if (passages.length > 0) {
				citations.set(note.basename, passages);
			}
		}

		// Build synthesis prompt
		const combinedContent = contents.join('\n\n---\n\n');
		const prompt = this.buildSynthesisPrompt(combinedContent, focusQuery);

		// Get AI synthesis
		const result = await this.aiService.generateCompletion(prompt);
		const response = result.text;

		// Parse response into structured result
		const parsed = this.parseSynthesisResponse(response);

		return {
			...parsed,
			citations,
			notesAnalyzed: notes.length
		};
	}

	/**
	 * Research assistant: Find and synthesize notes matching query
	 */
	async researchQuery(query: ResearchQuery): Promise<SynthesisResult> {
		// Find matching notes
		const matchingNotes = await this.findMatchingNotes(query);

		if (matchingNotes.length === 0) {
			return {
				summary: 'No notes found matching your query.',
				keyInsights: [],
				contradictions: [],
				knowledgeGaps: ['No existing notes on this topic'],
				citations: new Map(),
				notesAnalyzed: 0
			};
		}

		// Synthesize the matching notes
		return await this.synthesizeNotes(matchingNotes, query.query);
	}

	/**
	 * Extract and map arguments from notes
	 */
	async extractArgumentMap(notes: TFile[]): Promise<ArgumentMap> {
		const claims: Claim[] = [];
		const evidence: Evidence[] = [];
		const relationships: ArgumentRelation[] = [];

		for (const note of notes) {
			const content = await this.vault.read(note);
			
			// Extract claims from note
			const noteClaims = await this.extractClaims(content, note.basename);
			claims.push(...noteClaims);

			// Extract evidence from note
			const noteEvidence = await this.extractEvidence(content, note.basename);
			evidence.push(...noteEvidence);
		}

		// Identify relationships between claims and evidence
		for (const ev of evidence) {
			for (const claim of claims) {
				if (this.evidenceSupports(ev, claim)) {
					relationships.push({
						from: ev.id,
						to: claim.id,
						type: 'supports'
					});
					ev.supportsClaims.push(claim.id);
				}
			}
		}

		// Find contradictions
		for (let i = 0; i < claims.length; i++) {
			for (let j = i + 1; j < claims.length; j++) {
				if (this.claimsContradict(claims[i], claims[j])) {
					relationships.push({
						from: claims[i].id,
						to: claims[j].id,
						type: 'contradicts'
					});
				}
			}
		}

		// Identify logical gaps (claims without sufficient evidence)
		const logicalGaps: string[] = [];
		for (const claim of claims) {
			const supportingEvidence = relationships.filter(
				r => r.to === claim.id && r.type === 'supports'
			);
			
			if (supportingEvidence.length === 0) {
				logicalGaps.push(
					`Claim "${claim.text.substring(0, 50)}..." lacks supporting evidence`
				);
			}
		}

		return { claims, evidence, relationships, logicalGaps };
	}

	/**
	 * Identify contradictions across notes
	 */
	async findContradictions(notes: TFile[]): Promise<string[]> {
		const argumentMap = await this.extractArgumentMap(notes);
		
		const contradictions: string[] = [];
		for (const rel of argumentMap.relationships) {
			if (rel.type === 'contradicts') {
				const claim1 = argumentMap.claims.find(c => c.id === rel.from);
				const claim2 = argumentMap.claims.find(c => c.id === rel.to);
				
				if (claim1 && claim2) {
					contradictions.push(
						`"${claim1.text}" (${claim1.sourceNote}) contradicts "${claim2.text}" (${claim2.sourceNote})`
					);
				}
			}
		}

		return contradictions;
	}

	/**
	 * Identify knowledge gaps in research
	 */
	async identifyKnowledgeGaps(
		topic: string,
		relatedNotes: TFile[]
	): Promise<string[]> {
		const gaps: string[] = [];

		// Synthesize existing knowledge
		const synthesis = await this.synthesizeNotes(relatedNotes, topic);
		
		// Build gap detection prompt
		const prompt = `Based on the following research summary about "${topic}", identify key knowledge gaps and unanswered questions:

${synthesis.summary}

Key insights found:
${synthesis.keyInsights.map((k, i) => `${i + 1}. ${k}`).join('\n')}

Provide a list of 5-10 important questions or gaps that remain unanswered in this research. Focus on:
- Missing perspectives or viewpoints
- Unexplored connections
- Methodological limitations
- Areas needing more evidence
- Conflicting information that needs resolution

Format: One gap per line, as a question or statement.`;

		const result = await this.aiService.generateCompletion(prompt);
		const response = result.text;

		// Parse gaps from response
		const lines = response.split('\n').filter((l: string) => l.trim().length > 0);
		for (const line of lines) {
			const cleaned = line.replace(/^[\d.\-*\s]+/, '').trim();
			if (cleaned.length > 10) {
				gaps.push(cleaned);
			}
		}

		return gaps;
	}

	/**
	 * Suggest next research directions
	 */
	async suggestResearchDirections(
		currentTopic: string,
		existingNotes: TFile[]
	): Promise<ResearchSuggestion[]> {
		const suggestions: ResearchSuggestion[] = [];

		// Analyze current state
		const synthesis = await this.synthesizeNotes(existingNotes, currentTopic);
		const gaps = await this.identifyKnowledgeGaps(currentTopic, existingNotes);

		// Build suggestion prompt
		const prompt = `Based on this research about "${currentTopic}":

Summary: ${synthesis.summary}

Knowledge Gaps:
${gaps.map((g, i) => `${i + 1}. ${g}`).join('\n')}

Suggest 3-5 promising research directions to pursue next. For each direction:
1. Describe the research direction
2. Explain why it's valuable
3. Suggest specific sources or methods to explore

Format each suggestion as:
DIRECTION: [brief title]
REASONING: [why this matters]
SOURCES: [specific suggestions]
PRIORITY: [high/medium/low]
---`;

		const result = await this.aiService.generateCompletion(prompt);
		const response = result.text;

		// Parse suggestions
		const sections = response.split('---').filter((s: string) => s.trim());
		for (const section of sections) {
			const direction = this.extractField(section, 'DIRECTION');
			const reasoning = this.extractField(section, 'REASONING');
			const sources = this.extractField(section, 'SOURCES');
			const priority = this.extractField(section, 'PRIORITY') as 'high' | 'medium' | 'low';

			if (direction && reasoning) {
				suggestions.push({
					direction,
					reasoning,
					suggestedSources: sources ? [sources] : [],
					priority: priority || 'medium'
				});
			}
		}

		return suggestions;
	}

	/**
	 * Answer research question using all relevant notes
	 */
	async answerResearchQuestion(
		question: string,
		maxNotes: number = 20
	): Promise<string> {
		// Find relevant notes
		const allNotes = this.vault.getMarkdownFiles();
		const scored: ContextScore[] = [];

		for (const note of allNotes) {
			const score = await this.contextEngine.scoreNoteRelevance(note, question);
			if (score.score > 30) {
				scored.push(score);
			}
		}

		// Sort by relevance
		scored.sort((a, b) => b.score - a.score);
		const topNotes = scored.slice(0, maxNotes).map(s => s.file);

		// Build research context
		const contexts: string[] = [];
		for (const note of topNotes) {
			const content = await this.vault.read(note);
			const excerpt = this.extractRelevantExcerpt(content, question, 500);
			contexts.push(`[${note.basename}]\n${excerpt}`);
		}

		const combinedContext = contexts.join('\n\n---\n\n');

		// Build answer prompt
		const prompt = `Answer the following research question based on the provided notes from my knowledge base:

QUESTION: ${question}

KNOWLEDGE BASE EXCERPTS:
${combinedContext}

Provide a comprehensive answer that:
1. Synthesizes information from multiple sources
2. Cites specific notes in the format [[Note Name]]
3. Acknowledges any contradictions or uncertainties
4. Identifies gaps in available information
5. Provides a clear, well-reasoned conclusion

ANSWER:`;

		const result = await this.aiService.generateCompletion(prompt);
		const answer = result.text;

		return answer;
	}

	// ========== Private Helper Methods ==========

	private async findMatchingNotes(query: ResearchQuery): Promise<TFile[]> {
		let candidates = this.vault.getMarkdownFiles();

		// Filter by tags
		if (query.tags && query.tags.length > 0) {
			candidates = candidates.filter(file => {
				const metadata = this.metadataCache.getFileCache(file);
				const fileTags = this.extractTags(metadata);
				return query.tags!.some(tag => fileTags.includes(tag));
			});
		}

		// Filter by folder
		if (query.folders && query.folders.length > 0) {
			candidates = candidates.filter(file => {
				const folder = file.parent?.path || '';
				return query.folders!.some(f => folder.startsWith(f));
			});
		}

		// Filter by date range
		if (query.dateRange) {
			candidates = candidates.filter(file => {
				const mtime = file.stat.mtime;
				return mtime >= query.dateRange!.start && mtime <= query.dateRange!.end;
			});
		}

		// Score by semantic relevance
		const scored: ContextScore[] = [];
		for (const file of candidates) {
			const score = await this.contextEngine.scoreNoteRelevance(file, query.query);
			if (score.score > 20) {
				scored.push(score);
			}
		}

		// Sort and limit
		scored.sort((a, b) => b.score - a.score);
		const maxNotes = query.maxNotes || 10;
		return scored.slice(0, maxNotes).map(s => s.file);
	}

	private extractTags(metadata: any): string[] {
		const tags: string[] = [];
		
		if (metadata?.frontmatter?.tags) {
			const fmTags = Array.isArray(metadata.frontmatter.tags)
				? metadata.frontmatter.tags
				: [metadata.frontmatter.tags];
			tags.push(...fmTags.map(String));
		}

		if (metadata?.tags) {
			tags.push(...metadata.tags.map((t: any) => t.tag));
		}

		return tags;
	}

	private extractKeyPassages(content: string, maxPassages: number = 5): string[] {
		const passages: string[] = [];
		const lines = content.split('\n');

		// Look for important markers
		const importantMarkers = ['**', '==', '- [ ]', '> ', '# '];
		
		for (const line of lines) {
			if (passages.length >= maxPassages) break;
			
			const trimmed = line.trim();
			if (trimmed.length < 20) continue;

			// Check if line has important markers
			if (importantMarkers.some(marker => trimmed.includes(marker))) {
				passages.push(trimmed);
			}
		}

		return passages;
	}

	private buildSynthesisPrompt(content: string, focusQuery?: string): string {
		const focus = focusQuery 
			? `with particular focus on: "${focusQuery}"`
			: 'across all topics covered';

		return `Synthesize the following notes ${focus}.

${content}

Provide:
1. SUMMARY: A comprehensive synthesis (2-3 paragraphs)
2. KEY INSIGHTS: 5-7 most important insights (bullet points)
3. CONTRADICTIONS: Any conflicting information found (if any)
4. KNOWLEDGE GAPS: What important questions remain unanswered

Format your response with clear section headers.`;
	}

	private parseSynthesisResponse(response: string): Omit<SynthesisResult, 'citations' | 'notesAnalyzed'> {
		const summary = this.extractSection(response, 'SUMMARY') || response;
		const insights = this.extractBulletPoints(response, 'KEY INSIGHTS');
		const contradictions = this.extractBulletPoints(response, 'CONTRADICTIONS');
		const gaps = this.extractBulletPoints(response, 'KNOWLEDGE GAPS');

		return {
			summary,
			keyInsights: insights,
			contradictions,
			knowledgeGaps: gaps
		};
	}

	private extractSection(text: string, sectionName: string): string | null {
		const regex = new RegExp(`${sectionName}:?\\s*([\\s\\S]*?)(?=\\n\\n[A-Z]|$)`, 'i');
		const match = text.match(regex);
		return match ? match[1].trim() : null;
	}

	private extractBulletPoints(text: string, sectionName: string): string[] {
		const section = this.extractSection(text, sectionName);
		if (!section) return [];

		const points = section
			.split('\n')
			.map(line => line.replace(/^[\d.\-*\s]+/, '').trim())
			.filter(line => line.length > 0);

		return points;
	}

	private async extractClaims(content: string, sourceNote: string): Promise<Claim[]> {
		const claims: Claim[] = [];
		
		// Simple heuristic: sentences with strong assertions
		const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 20);
		
		const assertionWords = ['is', 'are', 'must', 'will', 'should', 'proves', 'demonstrates'];
		
		for (let i = 0; i < sentences.length; i++) {
			const sentence = sentences[i].trim();
			
			// Check if sentence makes an assertion
			if (assertionWords.some(word => sentence.toLowerCase().includes(` ${word} `))) {
				claims.push({
					id: `claim-${sourceNote}-${i}`,
					text: sentence,
					sourceNote,
					confidence: 'medium',
					type: 'supporting'
				});
			}
		}

		return claims.slice(0, 10); // Limit to top 10 claims per note
	}

	private async extractEvidence(content: string, sourceNote: string): Promise<Evidence[]> {
		const evidence: Evidence[] = [];
		
		// Look for citations, data, quotes
		const evidenceMarkers = ['according to', 'research shows', 'data indicates', 'study found'];
		const sentences = content.split(/[.!?]+/).filter(s => s.trim().length > 20);
		
		for (let i = 0; i < sentences.length; i++) {
			const sentence = sentences[i].trim().toLowerCase();
			
			if (evidenceMarkers.some(marker => sentence.includes(marker))) {
				evidence.push({
					id: `evidence-${sourceNote}-${i}`,
					text: sentences[i].trim(),
					sourceNote,
					supportsClaims: [],
					type: 'empirical'
				});
			}
		}

		return evidence;
	}

	private evidenceSupports(evidence: Evidence, claim: Claim): boolean {
		// Simple heuristic: shared keywords
		const evidenceTerms = new Set(this.extractKeywords(evidence.text));
		const claimTerms = new Set(this.extractKeywords(claim.text));
		
		let sharedTerms = 0;
		for (const term of claimTerms) {
			if (evidenceTerms.has(term)) sharedTerms++;
		}

		return sharedTerms >= 2; // At least 2 shared keywords
	}

	private claimsContradict(claim1: Claim, claim2: Claim): boolean {
		// Simple heuristic: opposite verbs or negations
		const text1 = claim1.text.toLowerCase();
		const text2 = claim2.text.toLowerCase();

		const contradictionPairs = [
			['is', 'is not'],
			['must', 'must not'],
			['should', 'should not'],
			['increases', 'decreases'],
			['positive', 'negative']
		];

		for (const [word1, word2] of contradictionPairs) {
			if ((text1.includes(word1) && text2.includes(word2)) ||
			    (text1.includes(word2) && text2.includes(word1))) {
				// Also check if they're about the same subject
				const terms1 = new Set(this.extractKeywords(text1));
				const terms2 = new Set(this.extractKeywords(text2));
				let shared = 0;
				for (const term of terms1) {
					if (terms2.has(term)) shared++;
				}
				if (shared >= 2) return true;
			}
		}

		return false;
	}

	private extractKeywords(text: string): string[] {
		const words = text
			.toLowerCase()
			.replace(/[^a-z0-9\s]/g, ' ')
			.split(/\s+/)
			.filter(w => w.length > 3);

		const stopWords = new Set(['this', 'that', 'with', 'from', 'have', 'been', 'will', 'would']);
		return words.filter(w => !stopWords.has(w));
	}

	private extractRelevantExcerpt(content: string, query: string, maxLength: number): string {
		const queryTerms = new Set(this.extractKeywords(query));
		const paragraphs = content.split('\n\n');
		
		let bestParagraph = paragraphs[0] || '';
		let bestScore = 0;

		for (const para of paragraphs) {
			if (para.trim().length < 50) continue;
			
			const paraTerms = new Set(this.extractKeywords(para));
			let score = 0;
			for (const term of queryTerms) {
				if (paraTerms.has(term)) score++;
			}

			if (score > bestScore) {
				bestScore = score;
				bestParagraph = para;
			}
		}

		if (bestParagraph.length <= maxLength) {
			return bestParagraph;
		}

		return bestParagraph.substring(0, maxLength) + '...';
	}

	private extractField(text: string, fieldName: string): string {
		const regex = new RegExp(`${fieldName}:?\\s*(.+?)(?=\\n[A-Z]+:|$)`, 'i');
		const match = text.match(regex);
		return match ? match[1].trim() : '';
	}
}
