import { App, Editor, MarkdownView, Modal, Notice, Plugin, TFile } from 'obsidian';
import { ObsidianAgentSettings, DEFAULT_SETTINGS, AIProfile, createDefaultProfile } from './settings';
import { ObsidianAgentSettingTab } from './settingsTab';
import { AIService, CompletionResult } from './aiService';
import { EnhancedAgentModal } from './agentModalEnhanced';
import { ContextProvider, ContextConfig } from './contextProvider';
import { ValidationError, APIError, ConfigurationError } from './src/errors';
import { DeadLinkDetector } from './src/deadLinkDetector';
import { AutoLinkSuggester } from './src/autoLinkSuggester';
import { SmartTagger } from './src/smartTagger';
import { MultiLevelSummarizer } from './src/multiLevelSummarizer';
import { DuplicateDetector } from './src/duplicateDetector';
import { IntelligentContextEngine } from './src/contextEngine';
import { MultiNoteSynthesizer } from './src/multiNoteSynthesizer';

// Import enhanced UI styles
const ENHANCED_STYLES = `
/* Enhanced UI RGB Variables */
:root {
  --background-primary-rgb: 255, 255, 255;
  --background-secondary-rgb: 245, 245, 245;
  --text-muted-rgb: 128, 128, 128;
  --interactive-accent-rgb: 0, 122, 255;
}

.theme-dark {
  --background-primary-rgb: 30, 30, 30;
  --background-secondary-rgb: 45, 45, 45;
  --text-muted-rgb: 150, 150, 150;
  --interactive-accent-rgb: 100, 170, 255;
}
`;

class ProfileSwitcherModal extends Modal {
	private profiles: AIProfile[];
	private activeProfileId: string;
	private onSelect: (profileId: string) => void;

	constructor(app: App, profiles: AIProfile[], activeProfileId: string, onSelect: (profileId: string) => void) {
		super(app);
		this.profiles = profiles;
		this.activeProfileId = activeProfileId;
		this.onSelect = onSelect;
	}

	onOpen() {
		const { contentEl } = this;
		contentEl.createEl('h2', { text: 'Switch AI Profile' });
		
		const list = contentEl.createDiv({ cls: 'profile-list' });
		list.style.display = 'flex';
		list.style.flexDirection = 'column';
		list.style.gap = '0.5rem';

		this.profiles.forEach(profile => {
			const isActive = profile.id === this.activeProfileId;
			const item = list.createDiv({ cls: 'profile-item' });
			item.style.display = 'flex';
			item.style.alignItems = 'center';
			item.style.justifyContent = 'space-between';
			item.style.padding = '0.75rem';
			item.style.borderRadius = 'var(--radius-s)';
			item.style.border = '1px solid var(--background-modifier-border)';
			item.style.cursor = 'pointer';
			item.style.backgroundColor = isActive ? 'var(--interactive-accent)' : 'var(--background-secondary)';
			item.style.color = isActive ? 'var(--text-on-accent)' : 'var(--text-normal)';

			const info = item.createDiv();
			info.createEl('strong', { text: profile.name });
			const details = info.createDiv();
			details.style.fontSize = 'var(--font-smaller)';
			details.style.opacity = '0.8';
			details.textContent = `${profile.apiProvider} - ${profile.model}`;

			if (isActive) {
				item.createEl('span', { text: '(Active)' });
			}

			item.addEventListener('click', () => {
				if (!isActive) {
					this.onSelect(profile.id);
				}
				this.close();
			});
		});
	}

	onClose() {
		const { contentEl } = this;
		contentEl.empty();
	}
}

export default class ObsidianAgentPlugin extends Plugin {
	settings!: ObsidianAgentSettings;
	aiService!: AIService;
	contextProvider!: ContextProvider;
	contextEngine!: IntelligentContextEngine;
	multiNoteSynthesizer!: MultiNoteSynthesizer;

	async onload() {
		try {
			await this.loadSettings();
			await this.migrateToProfiles();

			this.registerStyles();

			// Validate settings before creating services
			if (!this.settings) {
				throw new ConfigurationError('Failed to load plugin settings');
			}

			this.aiService = new AIService(this.settings);
			this.contextProvider = new ContextProvider(this.app);
			this.contextEngine = new IntelligentContextEngine(
				this.app.vault,
				this.app.metadataCache
			);
			this.multiNoteSynthesizer = new MultiNoteSynthesizer(
				this.app.vault,
				this.app.metadataCache,
				this.contextEngine,
				this.aiService
			);

			// Initialize usage stats with defaults
			if (!this.settings.totalRequests) {
				this.settings.totalRequests = 0;
			}
			if (!this.settings.totalTokensUsed) {
				this.settings.totalTokensUsed = 0;
			}
			if (!this.settings.estimatedCost) {
				this.settings.estimatedCost = 0;
			}

		// Command: Ask AI Agent
		this.addCommand({
			id: 'ask-ai-agent',
			name: 'Ask AI Agent',
			editorCallback: async (editor: Editor, ctx) => {
				try {
					const view = ctx as MarkdownView;
					if (!view || !view.file) {
						new Notice('No active file found');
						return;
					}

					const currentContent = editor.getValue();
					const context = await this.gatherFullContext(view.file, currentContent);
					new EnhancedAgentModal(
						this.app, 
						this.aiService, 
						this.settings,
						() => this.saveSettings(),
						context, 
						(result) => {
							if (result && typeof result === 'string') {
								editor.replaceSelection(result);
							}
						}
					).open();
				} catch (error: any) {
					this.handleError(error, 'Failed to open AI Agent');
				}
			}
		});

		// Command: Ask AI Agent (with vault context)
		this.addCommand({
			id: 'ask-ai-agent-vault-context',
			name: 'Ask AI Agent (with Linked Notes)',
			editorCallback: async (editor: Editor, ctx) => {
				try {
					const view = ctx as MarkdownView;
					if (!view || !view.file) {
						new Notice('No active file found');
						return;
					}

					const currentContent = editor.getValue();
					const context = await this.gatherFullContext(view.file, currentContent, true);
					new EnhancedAgentModal(
						this.app, 
						this.aiService, 
						this.settings,
						() => this.saveSettings(),
						context, 
						(result) => {
							if (result && typeof result === 'string') {
								editor.replaceSelection(result);
							}
						}
					).open();
				} catch (error: any) {
					this.handleError(error, 'Failed to open AI Agent with vault context');
				}
			}
		});

		// Command: Generate Summary
		this.addCommand({
			id: 'generate-summary',
			name: 'Generate Summary',
			editorCallback: async (editor: Editor) => {
				const selection = editor.getSelection();
				const textToSummarize = selection || editor.getValue();

				if (!textToSummarize.trim()) {
					new Notice('No text to summarize');
					return;
				}

				new Notice('Generating summary...');

				try {
					const summaryResult = await this.aiService.generateCompletion(
						`Please provide a concise summary of the following text:\n\n${textToSummarize}`
					);
					await this.trackTokenUsage(summaryResult);
					editor.replaceSelection(`\n\n## Summary\n${summaryResult.text}\n`);
					new Notice('Summary generated!');
				} catch (error: any) {
					new Notice(`Error: ${error.message}`);
					console.error('Summary Error:', error);
				}
			}
		});

		// Command: Multi-Level Summary
		this.addCommand({
			id: 'multi-level-summary',
			name: 'Multi-Level Summary (Quick/Standard/Detailed)',
			callback: async () => {
				try {
					const file = this.app.workspace.getActiveFile();
					if (!file) {
						new Notice('No active file');
						return;
					}

					new Notice('Generating multi-level summaries...');
					const summarizer = new MultiLevelSummarizer(this.app, this.aiService);
					
					const summaries = await summarizer.generateProgressiveSummary(file);
					
					// Create summary note
					const summaryNote = `# Summaries: ${file.basename}

## 🚀 Quick Summary (TL;DR)
${summaries.get('quick') || 'N/A'}

## 📋 Standard Summary  
${summaries.get('standard') || 'N/A'}

## 📚 Detailed Summary
${summaries.get('detailed') || 'N/A'}

---
*Generated on ${new Date().toLocaleString()}*
*Source: [[${file.basename}]]*
`;

					const summaryFile = await this.app.vault.create(
						`Summaries - ${file.basename} - ${new Date().toISOString().split('T')[0]}.md`,
						summaryNote
					);
					
					await this.app.workspace.getLeaf().openFile(summaryFile);
					new Notice('Multi-level summaries generated!');
				} catch (error: any) {
					this.handleError(error, 'Failed to generate multi-level summary');
				}
			}
		});

		// Command: Academic Summary
		this.addCommand({
			id: 'academic-summary',
			name: 'Generate Academic Summary',
			callback: async () => {
				try {
					const file = this.app.workspace.getActiveFile();
					if (!file) {
						new Notice('No active file');
						return;
					}

					new Notice('Generating academic summary...');
					const summarizer = new MultiLevelSummarizer(this.app, this.aiService);
					
					const result = await summarizer.summarizeNote(file, {
						level: 'academic',
						includeSections: true,
						includeKeyPoints: true
					});
					
					// Insert at top of file
					const content = await this.app.vault.read(file);
					const newContent = `# Academic Summary

${result.summary}

---

${content}`;
					
					await this.app.vault.modify(file, newContent);
					new Notice('Academic summary added to note!');
				} catch (error: any) {
					this.handleError(error, 'Failed to generate academic summary');
				}
			}
		});

		// Command: Expand Ideas
		this.addCommand({
			id: 'expand-ideas',
			name: 'Expand Ideas',
			editorCallback: async (editor: Editor) => {
				const selection = editor.getSelection();

				if (!selection.trim()) {
					new Notice('Please select text to expand');
					return;
				}

				new Notice('Expanding ideas...');

				try {
					const expansionResult = await this.aiService.generateCompletion(
						`Please expand on following ideas with more detail and context:\n\n${selection}`
					);
					await this.trackTokenUsage(expansionResult);
					editor.replaceSelection(expansionResult.text);
					new Notice('Ideas expanded!');
				} catch (error: any) {
					new Notice(`Error: ${error.message}`);
					console.error('Expand Error:', error);
				}
			}
		});

		// Command: Improve Writing
		this.addCommand({
			id: 'improve-writing',
			name: 'Improve Writing',
			editorCallback: async (editor: Editor) => {
				const selection = editor.getSelection();

				if (!selection.trim()) {
					new Notice('Please select text to improve');
					return;
				}

				new Notice('Improving writing...');

				try {
					const improvedResult = await this.aiService.generateCompletion(
						`Please improve following text for clarity, grammar, and style:\n\n${selection}`
					);
					await this.trackTokenUsage(improvedResult);
					editor.replaceSelection(improvedResult.text);
					new Notice('Writing improved!');
				} catch (error: any) {
					new Notice(`Error: ${error.message}`);
					console.error('Improve Writing Error:', error);
				}
			}
		});

		// Command: Generate Outline
		this.addCommand({
			id: 'generate-outline',
			name: 'Generate Outline',
			editorCallback: async (editor: Editor) => {
				const topic = editor.getSelection();

				if (!topic.trim()) {
					new Notice('Please select a topic for the outline');
					return;
				}

				new Notice('Generating outline...');

				try {
					const outlineResult = await this.aiService.generateCompletion(
						`Please create a detailed outline for the following topic:\n\n${topic}`
					);
					await this.trackTokenUsage(outlineResult);
					editor.replaceSelection(`\n\n${outlineResult.text}\n`);
					new Notice('Outline generated!');
				} catch (error: any) {
					new Notice(`Error: ${error.message}`);
					console.error('Outline Error:', error);
				}
			}
		});

		// Command: Answer Question
		this.addCommand({
			id: 'answer-question',
			name: 'Answer Question Based on Note',
			editorCallback: (editor: Editor) => {
				const noteContent = editor.getValue();
				new EnhancedAgentModal(
					this.app, 
					this.aiService, 
					this.settings,
					() => this.saveSettings(),
					noteContent, 
					(result) => {
						const cursor = editor.getCursor();
						editor.replaceRange(`\n\n**Q:** ${result}\n`, cursor);
					}
				).open();
			}
		});

		// Command: Switch AI Profile
		this.addCommand({
			id: 'switch-ai-profile',
			name: 'Switch AI Profile',
			callback: () => {
				const profiles = this.settings.profiles;
				if (profiles.length <= 1) {
					new Notice('No other profiles available. Create profiles in settings.');
					return;
				}
				
				// Create a simple modal for profile selection
				const modal = new ProfileSwitcherModal(this.app, profiles, this.settings.activeProfileId, async (profileId) => {
					await this.switchProfile(profileId);
				});
				modal.open();
			}
		});

		// Command: Scan for Dead Links
		this.addCommand({
			id: 'scan-dead-links',
			name: 'Scan Vault for Dead Links',
			callback: async () => {
				try {
					new Notice('Scanning vault for dead links...');
					const detector = new DeadLinkDetector(this.app);
					
					const result = await detector.scanVault((progress, total) => {
						if (progress % 10 === 0) {
							new Notice(`Scanning... ${progress}/${total} files`);
						}
					});

					// Generate and display report
					const report = detector.generateReport(result);
					const reportFile = await this.app.vault.create(
						`Dead Links Report ${new Date().toISOString().split('T')[0]}.md`,
						report
					);
					
					// Open the report
					await this.app.workspace.getLeaf().openFile(reportFile);
					
					new Notice(`Scan complete: ${result.brokenCount} dead links found`);
				} catch (error: any) {
					this.handleError(error, 'Failed to scan for dead links');
				}
			}
		});

		// Command: Scan Current File for Dead Links
		this.addCommand({
			id: 'scan-file-dead-links',
			name: 'Scan Current File for Dead Links',
			callback: async () => {
				try {
					const file = this.app.workspace.getActiveFile();
					if (!file) {
						new Notice('No active file');
						return;
					}

					new Notice('Scanning file for dead links...');
					const detector = new DeadLinkDetector(this.app);
					const deadLinks = await detector.scanFile(file);

					if (deadLinks.length === 0) {
						new Notice('✅ No dead links found in this file!');
					} else {
						const message = `Found ${deadLinks.length} dead link${deadLinks.length > 1 ? 's' : ''} in ${file.basename}`;
						new Notice(message);
						
						// Show detailed list in console
						console.log('Dead links:', deadLinks);
					}
				} catch (error: any) {
					this.handleError(error, 'Failed to scan file for dead links');
				}
			}
		});

		// Command: Suggest Links for Current File
		this.addCommand({
			id: 'suggest-links',
			name: 'Suggest Internal Links for Current File',
			callback: async () => {
				try {
					const file = this.app.workspace.getActiveFile();
					if (!file) {
						new Notice('No active file');
						return;
					}

					new Notice('Analyzing file for link suggestions...');
					const suggester = new AutoLinkSuggester(this.app);
					const suggestions = await suggester.suggestLinks(file);

					if (suggestions.length === 0) {
						new Notice('No link suggestions found');
					} else {
						// Generate and display report
						const report = suggester.generateReport(file, suggestions);
						const reportFile = await this.app.vault.create(
							`Link Suggestions - ${file.basename} - ${new Date().toISOString().split('T')[0]}.md`,
							report
						);
						
						await this.app.workspace.getLeaf().openFile(reportFile);
						new Notice(`Found ${suggestions.length} link suggestions`);
					}
				} catch (error: any) {
					this.handleError(error, 'Failed to suggest links');
				}
			}
		});

		// Command: Suggest Tags for Current Note
		this.addCommand({
			id: 'suggest-tags',
			name: 'Suggest Tags for Current Note',
			callback: async () => {
				try {
					const file = this.app.workspace.getActiveFile();
					if (!file) {
						new Notice('No active file');
						return;
					}

					new Notice('Analyzing note for tag suggestions...');
					const tagger = new SmartTagger(this.app);
					const suggestions = await tagger.suggestTags(file);

					if (suggestions.length === 0) {
						new Notice('No tag suggestions found');
						return;
					}

					// Show suggestions in a modal
					new TagSuggestionModal(
						this.app,
						suggestions,
						async (selectedTags) => {
							if (selectedTags.length > 0) {
								await tagger.applyTags(file, selectedTags);
								new Notice(`Applied ${selectedTags.length} tags`);
							}
						}
					).open();
				} catch (error: any) {
					this.handleError(error, 'Failed to suggest tags');
				}
			}
		});

		// Command: Auto-Tag Current Note (apply top suggestions automatically)
		this.addCommand({
			id: 'auto-tag-note',
			name: 'Auto-Tag Current Note (Top Suggestions)',
			callback: async () => {
				try {
					const file = this.app.workspace.getActiveFile();
					if (!file) {
						new Notice('No active file');
						return;
					}

					new Notice('Auto-tagging note...');
					const tagger = new SmartTagger(this.app);
					const suggestions = await tagger.suggestTags(file, {
						minConfidence: 0.6, // Higher threshold for auto-apply
						maxSuggestions: 3
					});

					if (suggestions.length === 0) {
						new Notice('No confident tag suggestions found');
						return;
					}

					const tags = suggestions.map(s => s.tag);
					await tagger.applyTags(file, tags);
					new Notice(`Auto-tagged with: ${tags.join(', ')}`);
				} catch (error: any) {
					this.handleError(error, 'Failed to auto-tag note');
				}
			}
		});

		// Command: Find Duplicate Notes
		this.addCommand({
			id: 'find-duplicates',
			name: 'Find Duplicate & Similar Notes',
			callback: async () => {
				try {
					new Notice('Scanning vault for duplicates...');
					const detector = new DuplicateDetector(this.app);
					
					const groups = await detector.findDuplicates({
						exactMatchThreshold: 1.0,
						nearDuplicateThreshold: 0.95,
						semanticThreshold: 0.7,
						minContentLength: 50
					});

					if (groups.length === 0) {
						new Notice('✅ No duplicates found!');
						return;
					}

					// Generate report
					const report = this.generateDuplicateReport(groups);
					const reportFile = await this.app.vault.create(
						`Duplicate Notes Report - ${new Date().toISOString().split('T')[0]}.md`,
						report
					);
					
					await this.app.workspace.getLeaf().openFile(reportFile);
					new Notice(`Found ${groups.length} duplicate groups`);
				} catch (error: any) {
					this.handleError(error, 'Failed to find duplicates');
				}
			}
		});

		// Command: Compare Two Notes
		this.addCommand({
			id: 'compare-notes',
			name: 'Compare Current Note with Another',
			callback: async () => {
				try {
					const currentFile = this.app.workspace.getActiveFile();
					if (!currentFile) {
						new Notice('No active file');
						return;
					}

					// Show file suggester modal
					new Notice('Select a note to compare with...');
					// TODO: Implement file selector modal
					// For now, show message
					new Notice('File comparison feature coming soon!');
				} catch (error: any) {
					this.handleError(error, 'Failed to compare notes');
				}
			}
		});

		// Command: Synthesize Insights from Multiple Notes
		this.addCommand({
			id: 'synthesize-notes',
			name: 'Synthesize Insights from Multiple Notes',
			callback: async () => {
				try {
					const files = this.app.vault.getMarkdownFiles();
					
					// Prompt user for tag/folder filter
					const input = await this.promptUser(
						'Enter tag (with #) or folder path to synthesize, or leave empty for all notes:'
					);
					
					let notesToSynthesize: TFile[] = [];
					
					if (input && input.startsWith('#')) {
						// Filter by tag
						const tag = input.substring(1);
						for (const file of files) {
							const metadata = this.app.metadataCache.getFileCache(file);
							const tags = metadata?.frontmatter?.tags || [];
							const tagArray = Array.isArray(tags) ? tags : [tags];
							if (tagArray.includes(tag)) {
								notesToSynthesize.push(file);
							}
						}
					} else if (input) {
						// Filter by folder
						notesToSynthesize = files.filter(f => 
							f.parent?.path.includes(input)
						);
					} else {
						// Limit to recent 20 notes for performance
						notesToSynthesize = files
							.sort((a, b) => b.stat.mtime - a.stat.mtime)
							.slice(0, 20);
					}
					
					if (notesToSynthesize.length === 0) {
						new Notice('No notes found matching criteria');
						return;
					}
					
					new Notice(`Synthesizing ${notesToSynthesize.length} notes...`);
					
					const result = await this.multiNoteSynthesizer.synthesizeNotes(
						notesToSynthesize
					);
					
					// Create synthesis report
					const report = this.generateSynthesisReport(result);
					
					// Create new note with synthesis
					const fileName = `Synthesis - ${new Date().toISOString().split('T')[0]}.md`;
					await this.app.vault.create(fileName, report);
					
					// Open the new note
					const newFile = this.app.vault.getAbstractFileByPath(fileName);
					if (newFile instanceof TFile) {
						await this.app.workspace.getLeaf().openFile(newFile);
					}
					
					new Notice(`✓ Synthesis complete! (${notesToSynthesize.length} notes)`);
				} catch (error: any) {
					this.handleError(error, 'Failed to synthesize notes');
				}
			}
		});

		// Command: Research Assistant - Answer Question
		this.addCommand({
			id: 'research-assistant',
			name: 'Research Assistant - Answer from Vault',
			callback: async () => {
				try {
					const question = await this.promptUser(
						'What would you like to research in your vault?'
					);
					
					if (!question) {
						return;
					}
					
					new Notice('Researching across your vault...');
					
					const answer = await this.multiNoteSynthesizer.answerResearchQuestion(
						question,
						15 // Max 15 notes
					);
					
					// Insert answer into current note or create new one
					const activeFile = this.app.workspace.getActiveFile();
					const view = this.app.workspace.getActiveViewOfType(MarkdownView);
					
					const report = `## Research Question\n\n${question}\n\n## Answer\n\n${answer}\n\n---\n*Generated by Research Assistant on ${new Date().toLocaleString()}*\n\n`;
					
					if (view && activeFile) {
						const editor = view.editor;
						editor.replaceRange(report, editor.getCursor());
					} else {
						// Create new note
						const fileName = `Research - ${question.substring(0, 50)}.md`;
						await this.app.vault.create(fileName, report);
						const newFile = this.app.vault.getAbstractFileByPath(fileName);
						if (newFile instanceof TFile) {
							await this.app.workspace.getLeaf().openFile(newFile);
						}
					}
					
					new Notice('✓ Research complete!');
				} catch (error: any) {
					this.handleError(error, 'Research failed');
				}
			}
		});

		// Command: Find Knowledge Gaps
		this.addCommand({
			id: 'find-knowledge-gaps',
			name: 'Identify Knowledge Gaps in Research',
			callback: async () => {
				try {
					const topic = await this.promptUser(
						'What topic would you like to analyze for knowledge gaps?'
					);
					
					if (!topic) return;
					
					new Notice('Analyzing knowledge gaps...');
					
					// Find relevant notes
					const files = this.app.vault.getMarkdownFiles();
					const scored = [];
					
					for (const file of files) {
						const score = await this.contextEngine.scoreNoteRelevance(file, topic);
						if (score.score > 30) {
							scored.push({ file, score: score.score });
						}
					}
					
					scored.sort((a, b) => b.score - a.score);
					const relevantNotes = scored.slice(0, 10).map(s => s.file);
					
					if (relevantNotes.length === 0) {
						new Notice('No relevant notes found');
						return;
					}
					
					const gaps = await this.multiNoteSynthesizer.identifyKnowledgeGaps(
						topic,
						relevantNotes
					);
					
					// Create gap analysis report
					const report = `# Knowledge Gap Analysis: ${topic}\n\n` +
						`*Based on ${relevantNotes.length} relevant notes*\n\n` +
						`## Identified Gaps\n\n` +
						gaps.map((gap, i) => `${i + 1}. ${gap}`).join('\n') +
						`\n\n## Related Notes\n\n` +
						relevantNotes.map(n => `- [[${n.basename}]]`).join('\n') +
						`\n\n---\n*Generated ${new Date().toLocaleString()}*`;
					
					const fileName = `Gap Analysis - ${topic}.md`;
					await this.app.vault.create(fileName, report);
					
					const newFile = this.app.vault.getAbstractFileByPath(fileName);
					if (newFile instanceof TFile) {
						await this.app.workspace.getLeaf().openFile(newFile);
					}
					
					new Notice(`✓ Found ${gaps.length} knowledge gaps`);
				} catch (error: any) {
					this.handleError(error, 'Gap analysis failed');
				}
			}
		});

		// Command: Suggest Research Directions
		this.addCommand({
			id: 'suggest-research-directions',
			name: 'Suggest Next Research Directions',
			callback: async () => {
				try {
					const topic = await this.promptUser(
						'What research topic would you like suggestions for?'
					);
					
					if (!topic) return;
					
					new Notice('Analyzing research directions...');
					
					// Find relevant notes
					const files = this.app.vault.getMarkdownFiles();
					const scored = [];
					
					for (const file of files) {
						const score = await this.contextEngine.scoreNoteRelevance(file, topic);
						if (score.score > 30) {
							scored.push({ file, score: score.score });
						}
					}
					
					scored.sort((a, b) => b.score - a.score);
					const relevantNotes = scored.slice(0, 10).map(s => s.file);
					
					if (relevantNotes.length === 0) {
						new Notice('No relevant notes found');
						return;
					}
					
					const suggestions = await this.multiNoteSynthesizer.suggestResearchDirections(
						topic,
						relevantNotes
					);
					
					// Create suggestions report
					let report = `# Research Direction Suggestions: ${topic}\n\n`;
					report += `*Based on analysis of ${relevantNotes.length} notes*\n\n`;
					
					for (const suggestion of suggestions) {
						const priority = suggestion.priority === 'high' ? '🔴' : 
						                suggestion.priority === 'medium' ? '🟡' : '🟢';
						report += `## ${priority} ${suggestion.direction}\n\n`;
						report += `**Why this matters:** ${suggestion.reasoning}\n\n`;
						if (suggestion.suggestedSources.length > 0) {
							report += `**Suggested sources:**\n`;
							report += suggestion.suggestedSources.map(s => `- ${s}`).join('\n');
							report += '\n\n';
						}
					}
					
					report += `## Source Notes\n\n`;
					report += relevantNotes.map(n => `- [[${n.basename}]]`).join('\n');
					report += `\n\n---\n*Generated ${new Date().toLocaleString()}*`;
					
					const fileName = `Research Directions - ${topic}.md`;
					await this.app.vault.create(fileName, report);
					
					const newFile = this.app.vault.getAbstractFileByPath(fileName);
					if (newFile instanceof TFile) {
						await this.app.workspace.getLeaf().openFile(newFile);
					}
					
					new Notice(`✓ Generated ${suggestions.length} research suggestions`);
				} catch (error: any) {
					this.handleError(error, 'Failed to generate suggestions');
				}
			}
		});

		// Command: Find Related Notes (using Context Engine)
		this.addCommand({
			id: 'find-related-notes',
			name: 'Find Semantically Related Notes',
			callback: async () => {
				try {
					const currentFile = this.app.workspace.getActiveFile();
					if (!currentFile) {
						new Notice('No active file');
						return;
					}
					
					new Notice('Finding related notes...');
					
					const clusterMates = await this.contextEngine.findClusterMates(currentFile);
					
					if (clusterMates.length === 0) {
						new Notice('No semantically related notes found');
						return;
					}
					
					// Create report
					let report = `# Notes Related to ${currentFile.basename}\n\n`;
					report += `Found ${clusterMates.length} semantically similar notes:\n\n`;
					report += clusterMates.map(n => `- [[${n.basename}]]`).join('\n');
					report += `\n\n---\n*Generated by Context Engine on ${new Date().toLocaleString()}*`;
					
					// Insert at cursor or create new note
					const view = this.app.workspace.getActiveViewOfType(MarkdownView);
					if (view) {
						const editor = view.editor;
						editor.replaceRange(report, editor.getCursor());
					} else {
						const fileName = `Related to ${currentFile.basename}.md`;
						await this.app.vault.create(fileName, report);
					}
					
					new Notice(`✓ Found ${clusterMates.length} related notes`);
				} catch (error: any) {
					this.handleError(error, 'Failed to find related notes');
				}
			}
		});

		// Command: Build Semantic Clusters
		this.addCommand({
			id: 'build-semantic-clusters',
			name: 'Discover Semantic Note Clusters',
			callback: async () => {
				try {
					new Notice('Building semantic clusters... This may take a moment.');
					
					const clusters = await this.contextEngine.buildSemanticClusters();
					
					// Create cluster report
					let report = `# Semantic Note Clusters\n\n`;
					report += `Discovered ${clusters.size} thematic clusters in your vault:\n\n`;
					
					for (const [_id, cluster] of clusters) {
						report += `## ${cluster.theme}\n\n`;
						report += `*Keywords: ${cluster.keywords.join(', ')}*\n\n`;
						report += `**Notes (${cluster.notes.length}):**\n`;
						report += cluster.notes.map(n => `- [[${n.basename}]]`).join('\n');
						report += '\n\n';
					}
					
					report += `---\n*Generated ${new Date().toLocaleString()}*`;
					
					const fileName = `Semantic Clusters - ${new Date().toISOString().split('T')[0]}.md`;
					await this.app.vault.create(fileName, report);
					
					const newFile = this.app.vault.getAbstractFileByPath(fileName);
					if (newFile instanceof TFile) {
						await this.app.workspace.getLeaf().openFile(newFile);
					}
					
					new Notice(`✓ Found ${clusters.size} clusters`);
				} catch (error: any) {
					this.handleError(error, 'Clustering failed');
				}
			}
		});

		// Add settings tab
		this.addSettingTab(new ObsidianAgentSettingTab(this.app, this));

		console.log('Obsidian Agent plugin loaded');
	} catch (error: any) {
		this.handleError(error, 'Failed to load plugin');
	}
}

	onunload() {
		console.log('Obsidian Agent plugin unloaded');
	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	private async gatherFullContext(file: TFile | null, currentContent: string, forceVaultContext: boolean = false): Promise<string> {
		// Validate inputs
		if (!currentContent) {
			currentContent = '';
		}

		const config = this.settings.contextConfig;
		
		// Check if any vault context is enabled
		const hasVaultContext = forceVaultContext || 
			config?.enableLinkedNotes || 
			config?.enableBacklinks || 
			config?.enableTagContext || 
			config?.enableFolderContext;

		if (!hasVaultContext || !file) {
			return currentContent;
		}

		// Build context config with defaults
		const contextConfig: ContextConfig = {
			sources: [
				{ type: 'current', enabled: true },
				{ type: 'linked', enabled: forceVaultContext || config?.enableLinkedNotes || false },
				{ type: 'backlinks', enabled: config?.enableBacklinks || false },
				{ type: 'tags', enabled: config?.enableTagContext || false },
				{ type: 'folder', enabled: config?.enableFolderContext || false }
			],
			maxNotesPerSource: Math.max(1, config?.maxNotesPerSource || 5),
			maxTokensPerNote: Math.max(100, config?.maxTokensPerNote || 1000),
			linkDepth: Math.max(1, Math.min(3, config?.linkDepth || 1)),
			excludeFolders: (config?.excludeFolders || 'templates, .obsidian').split(',').map(s => s.trim()).filter(s => s.length > 0)
		};

		try {
			const contexts = await this.contextProvider.gatherContext(
				file,
				currentContent,
				contextConfig,
				this.settings.apiProvider
			);

			if (!contexts || contexts.length === 0) {
				return currentContent;
			}

			const formattedContext = this.contextProvider.formatContextsForPrompt(contexts);
			
			if (contexts.length > 1) {
				const additionalNotes = contexts.length - 1;
				new Notice(`Loaded context from ${additionalNotes} additional note(s)`);
			}

			return formattedContext || currentContent;
		} catch (error) {
			console.error('Failed to gather vault context:', error);
			new Notice('Warning: Could not load vault context, using current note only');
			return currentContent;
		}
	}

	private async migrateToProfiles(): Promise<void> {
		// Migrate existing settings to profile system if not already done
		if (!this.settings.profiles || this.settings.profiles.length === 0) {
			const defaultProfile = createDefaultProfile(this.settings);
			this.settings.profiles = [defaultProfile];
			this.settings.activeProfileId = 'default';
			await this.saveSettings();
			console.log('Migrated settings to profile system');
		}
	}

	getActiveProfile(): AIProfile | undefined {
		return this.settings.profiles.find(p => p.id === this.settings.activeProfileId);
	}

	async switchProfile(profileId: string): Promise<void> {
		const profile = this.settings.profiles.find(p => p.id === profileId);
		if (!profile) {
			new Notice('Profile not found');
			return;
		}

		// Apply profile settings to main settings
		this.settings.activeProfileId = profileId;
		this.settings.apiProvider = profile.apiProvider;
		this.settings.apiKey = profile.apiKey;
		this.settings.customApiUrl = profile.customApiUrl;
		this.settings.model = profile.model;
		this.settings.temperature = profile.temperature;
		this.settings.maxTokens = profile.maxTokens;
		this.settings.systemPrompt = profile.systemPrompt;

		await this.saveSettings();
		new Notice(`Switched to profile: ${profile.name}`);
	}

	async createProfile(profile: AIProfile): Promise<void> {
		this.settings.profiles.push(profile);
		await this.saveSettings();
		new Notice(`Profile created: ${profile.name}`);
	}

	async updateProfile(profile: AIProfile): Promise<void> {
		const index = this.settings.profiles.findIndex(p => p.id === profile.id);
		if (index >= 0) {
			this.settings.profiles[index] = profile;
			// If updating active profile, also update main settings
			if (profile.id === this.settings.activeProfileId) {
				this.settings.apiProvider = profile.apiProvider;
				this.settings.apiKey = profile.apiKey;
				this.settings.customApiUrl = profile.customApiUrl;
				this.settings.model = profile.model;
				this.settings.temperature = profile.temperature;
				this.settings.maxTokens = profile.maxTokens;
				this.settings.systemPrompt = profile.systemPrompt;
			}
			await this.saveSettings();
		}
	}

	async deleteProfile(profileId: string): Promise<void> {
		if (profileId === 'default') {
			new Notice('Cannot delete the default profile');
			return;
		}
		
		const index = this.settings.profiles.findIndex(p => p.id === profileId);
		if (index >= 0) {
			const profileName = this.settings.profiles[index].name;
			this.settings.profiles.splice(index, 1);
			
			// If deleting active profile, switch to default
			if (this.settings.activeProfileId === profileId) {
				await this.switchProfile('default');
			} else {
				await this.saveSettings();
			}
			new Notice(`Profile deleted: ${profileName}`);
		}
	}

	/**
	 * Generate duplicate detection report
	 */
	private generateDuplicateReport(groups: any[]): string {
		const lines: string[] = [];
		
		lines.push('# Duplicate & Similar Notes Report\n');
		lines.push(`**Scan Date:** ${new Date().toISOString()}\n`);
		lines.push(`**Groups Found:** ${groups.length}\n`);

		// Group by type
		const exact = groups.filter(g => g.duplicateType === 'exact');
		const nearExact = groups.filter(g => g.duplicateType === 'near-exact');
		const semantic = groups.filter(g => g.duplicateType === 'semantic');

		lines.push(`- Exact Duplicates: ${exact.length}`);
		lines.push(`- Near-Exact Duplicates: ${nearExact.length}`);
		lines.push(`- Semantic Duplicates: ${semantic.length}\n`);

		// Exact duplicates
		if (exact.length > 0) {
			lines.push('## 🔴 Exact Duplicates\n');
			lines.push('These notes have identical content and should be merged.\n');
			
			exact.forEach((group, idx) => {
				lines.push(`### Group ${idx + 1} (${group.notes.length} notes)`);
				lines.push(`**Similarity:** 100%\n`);
				group.notes.forEach((note: any) => {
					lines.push(`- [[${note.path}]]`);
				});
				if (group.commonContent) {
					lines.push(`\n**Preview:**\n> ${group.commonContent}\n`);
				}
				lines.push('');
			});
		}

		// Near-exact duplicates
		if (nearExact.length > 0) {
			lines.push('## 🟡 Near-Exact Duplicates\n');
			lines.push('These notes are 95%+ similar with minor differences.\n');
			
			nearExact.forEach((group, idx) => {
				lines.push(`### Group ${idx + 1} (${group.notes.length} notes)`);
				const similarity = Math.round(group.similarity * 100);
				lines.push(`**Similarity:** ${similarity}%\n`);
				group.notes.forEach((note: any) => {
					lines.push(`- [[${note.path}]]`);
				});
				lines.push('');
			});
		}

		// Semantic duplicates
		if (semantic.length > 0) {
			lines.push('## 🟢 Semantic Duplicates\n');
			lines.push('These notes cover similar topics or themes.\n');
			
			semantic.forEach((group, idx) => {
				lines.push(`### Group ${idx + 1} (${group.notes.length} notes)`);
				const similarity = Math.round(group.similarity * 100);
				lines.push(`**Similarity:** ${similarity}%\n`);
				group.notes.forEach((note: any) => {
					lines.push(`- [[${note.path}]]`);
				});
				lines.push('');
			});
		}

		lines.push('---\n');
		lines.push('## 💡 Recommendations\n');
		lines.push('- **Exact Duplicates:** Delete all but one copy');
		lines.push('- **Near-Exact:** Review differences and merge if appropriate');
		lines.push('- **Semantic:** Consider linking or consolidating related content\n');

		return lines.join('\n');
	}

	private generateSynthesisReport(result: any): string {
		const lines: string[] = [];
		
		lines.push('# Multi-Note Synthesis Report\n');
		lines.push(`**Generated:** ${new Date().toLocaleString()}`);
		lines.push(`**Notes Analyzed:** ${result.notesAnalyzed}\n`);
		
		lines.push('## Summary\n');
		lines.push(result.summary + '\n');
		
		if (result.keyInsights && result.keyInsights.length > 0) {
			lines.push('## Key Insights\n');
			result.keyInsights.forEach((insight: string, i: number) => {
				lines.push(`${i + 1}. ${insight}`);
			});
			lines.push('');
		}
		
		if (result.contradictions && result.contradictions.length > 0) {
			lines.push('## ⚠️ Contradictions Found\n');
			result.contradictions.forEach((contradiction: string) => {
				lines.push(`- ${contradiction}`);
			});
			lines.push('');
		}
		
		if (result.knowledgeGaps && result.knowledgeGaps.length > 0) {
			lines.push('## 🔍 Knowledge Gaps\n');
			result.knowledgeGaps.forEach((gap: string) => {
				lines.push(`- ${gap}`);
			});
			lines.push('');
		}
		
		if (result.citations && result.citations.size > 0) {
			lines.push('## 📚 Source Citations\n');
			for (const [note, passages] of result.citations) {
				lines.push(`### [[${note}]]`);
				passages.forEach((passage: string) => {
					lines.push(`> ${passage}`);
				});
				lines.push('');
			}
		}
		
		lines.push('---');
		lines.push('*Generated by Multi-Note Synthesizer*');
		
		return lines.join('\n');
	}

	private async promptUser(message: string): Promise<string | null> {
		return new Promise((resolve) => {
			const modal = new class extends Modal {
				result: string | null = null;

				onOpen() {
					const { contentEl } = this;
					contentEl.createEl('h3', { text: message });
					
					const input = contentEl.createEl('input', {
						type: 'text',
						attr: { style: 'width: 100%; padding: 8px; margin: 10px 0;' }
					});
					
					const buttonContainer = contentEl.createDiv({ attr: { style: 'display: flex; gap: 10px; justify-content: flex-end;' } });
					
					const submitBtn = buttonContainer.createEl('button', { text: 'Submit' });
					submitBtn.addEventListener('click', () => {
						this.result = input.value || null;
						this.close();
					});
					
					const cancelBtn = buttonContainer.createEl('button', { text: 'Cancel' });
					cancelBtn.addEventListener('click', () => {
						this.result = null;
						this.close();
					});
					
					input.addEventListener('keypress', (e) => {
						if (e.key === 'Enter') {
							this.result = input.value || null;
							this.close();
						}
					});
					
					input.focus();
				}

				onClose() {
					const { contentEl } = this;
					contentEl.empty();
					resolve(this.result);
				}
			}(this.app);
			
			modal.open();
		});
	}

	private async trackTokenUsage(result: CompletionResult): Promise<void> {
		try {
			if (!this.settings.enableTokenTracking || !result.tokensUsed) {
				return;
			}

			// Initialize with defaults if not set
			this.settings.totalRequests = (this.settings.totalRequests || 0) + 1;
			this.settings.totalTokensUsed = (this.settings.totalTokensUsed || 0) + result.tokensUsed;

			const cost = this.estimateCost(result);
			this.settings.estimatedCost = (this.settings.estimatedCost || 0) + cost;

			// Cost threshold warning
			const threshold = this.settings.costThreshold || 10;
			if (this.settings.estimatedCost > threshold) {
				new Notice(`Cost warning: You've spent approximately $${this.settings.estimatedCost.toFixed(2)} this session`, 5000);
			}

			await this.saveSettings();
		} catch (error) {
			console.error('Failed to track token usage:', error);
			// Don't throw - token tracking is not critical
		}
	}

	/**
	 * Centralized error handler for better error messages
	 */
	private handleError(error: any, context: string): void {
		let message = context;

		if (error instanceof ValidationError) {
			message = `Validation error: ${error.message}`;
		} else if (error instanceof APIError) {
			message = `API error: ${error.message}`;
		} else if (error instanceof ConfigurationError) {
			message = `Configuration error: ${error.message}`;
		} else if (error.message) {
			message = `${context}: ${error.message}`;
		}

		console.error(context, error);
		new Notice(message, 5000);
	}

	private registerStyles(): void {
		// Load original styles
		const styleContent = this.app.vault.adapter.read('styles.css');
		styleContent.then((content) => {
			if (content) {
				const styleEl = document.createElement('style');
				styleEl.textContent = content;
				styleEl.className = 'obsidian-agent-styles';
				document.head.appendChild(styleEl);
			}
		});
		
		// Load enhanced styles
		const enhancedStyleContent = this.app.vault.adapter.read('styles-enhanced.css');
		enhancedStyleContent.then((content) => {
			if (content) {
				const styleEl = document.createElement('style');
				styleEl.textContent = ENHANCED_STYLES + '\n' + content;
				styleEl.className = 'obsidian-agent-styles-enhanced';
				document.head.appendChild(styleEl);
			}
		});
		
		this.applyAccessibilitySettings();
	}

	applyAccessibilitySettings(): void {
		document.body.classList.remove('oa-high-contrast', 'oa-reduced-motion');

		if (this.settings.accessibilityConfig?.enableHighContrast) {
			document.body.classList.add('oa-high-contrast');
		}

		if (this.settings.accessibilityConfig?.enableReducedMotion) {
			document.body.classList.add('oa-reduced-motion');
		}
	}

	private estimateCost(result: CompletionResult): number {
		if (this.settings.apiProvider === 'openai') {
			const inputCost = ((result.inputTokens || 0) / 1000) * 0.03;
			const outputCost = ((result.outputTokens || 0) / 1000) * 0.06;
			return inputCost + outputCost;
		} else if (this.settings.apiProvider === 'anthropic') {
			return ((result.tokensUsed || 0) / 1000) * 0.075;
		}
		return 0;
	}

	async saveSettings() {
		// Persist cache data before saving
		const cacheService = this.aiService?.getCacheService();
		if (cacheService && this.settings.cacheConfig?.enabled) {
			const cacheData = cacheService.exportCache();
			this.settings.cacheData = {
				entries: cacheData.entries,
				stats: cacheData.stats
			};
		}

		await this.saveData(this.settings);
		
		// Update AI service with new settings (preserves cache)
		const newService = new AIService(this.settings);
		const oldCache = this.aiService?.getCacheService();
		if (oldCache && cacheService) {
			newService.getCacheService().importCache({
				entries: oldCache.exportCache().entries,
				stats: oldCache.getStats(),
				settings: this.settings.cacheConfig
			});
		}
		this.aiService = newService;
	}
}

// Tag Suggestion Modal
class TagSuggestionModal extends Modal {
private suggestions: any[];
private onSelect: (tags: string[]) => void;
private selectedTags: Set<string> = new Set();

constructor(app: App, suggestions: any[], onSelect: (tags: string[]) => void) {
super(app);
this.suggestions = suggestions;
this.onSelect = onSelect;
}

onOpen() {
const { contentEl } = this;
contentEl.empty();

contentEl.createEl('h2', { text: 'Suggested Tags' });
contentEl.createEl('p', {
text: 'Select tags to apply to this note:',
cls: 'setting-item-description'
});

const list = contentEl.createEl('div', { cls: 'tag-suggestion-list' });

this.suggestions.forEach((suggestion) => {
const item = list.createEl('div', {
cls: 'tag-suggestion-item',
attr: { 'data-tag': suggestion.tag }
});

const checkbox = item.createEl('input', {
type: 'checkbox',
cls: 'tag-checkbox'
});

const label = item.createEl('label', { cls: 'tag-label' });

label.createEl('span', {
text: `#${suggestion.tag}`,
cls: 'tag-name'
});

const confidence = Math.round(suggestion.confidence * 100);
label.createEl('span', {
text: `% `,
cls: 'tag-confidence'
});

const reason = label.createEl('span', {
text: this.getReasonText(suggestion.reason),
cls: 'tag-reason'
});

if (suggestion.examples && suggestion.examples.length > 0) {
reason.createEl('span', {
text: ` ()`,
cls: 'tag-examples'
});
}

checkbox.addEventListener('change', () => {
if (checkbox.checked) {
this.selectedTags.add(suggestion.tag);
item.addClass('selected');
} else {
this.selectedTags.delete(suggestion.tag);
item.removeClass('selected');
}
});

// Select high-confidence tags by default
if (confidence >= 70) {
checkbox.checked = true;
this.selectedTags.add(suggestion.tag);
item.addClass('selected');
}
});

// Buttons
const buttonContainer = contentEl.createEl('div', { cls: 'modal-button-container' });

const applyButton = buttonContainer.createEl('button', {
text: 'Apply Selected Tags',
cls: 'mod-cta'
});
applyButton.addEventListener('click', () => {
this.onSelect([...this.selectedTags]);
this.close();
});

const cancelButton = buttonContainer.createEl('button', {
text: 'Cancel'
});
cancelButton.addEventListener('click', () => {
this.close();
});

// Add styles
const style = contentEl.createEl('style');
style.textContent = `
.tag-suggestion-list {
margin: 20px 0;
max-height: 400px;
overflow-y: auto;
}
.tag-suggestion-item {
padding: 10px;
margin: 5px 0;
border: 1px solid var(--background-modifier-border);
border-radius: 5px;
display: flex;
align-items: center;
cursor: pointer;
transition: all 0.2s;
}
.tag-suggestion-item:hover {
background-color: var(--background-modifier-hover);
}
.tag-suggestion-item.selected {
background-color: var(--interactive-accent);
color: var(--text-on-accent);
border-color: var(--interactive-accent);
}
.tag-checkbox {
margin-right: 10px;
}
.tag-label {
flex: 1;
display: flex;
flex-wrap: wrap;
align-items: center;
gap: 5px;
}
.tag-name {
font-weight: 600;
margin-right: 10px;
}
.tag-confidence {
color: var(--text-accent);
font-size: 0.9em;
}
.tag-reason {
color: var(--text-muted);
font-size: 0.85em;
}
.tag-examples {
font-style: italic;
}
.modal-button-container {
display: flex;
justify-content: flex-end;
gap: 10px;
margin-top: 20px;
}
`;
}

private getReasonText(reason: string): string {
const reasons: Record<string, string> = {
'content_match': 'content match',
'pattern_learned': 'learned pattern',
'similar_notes': 'similar notes',
'frequency': 'frequently co-occurs'
};
return reasons[reason] || reason;
}

onClose() {
const { contentEl } = this;
contentEl.empty();
}
}
