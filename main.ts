import { Editor, MarkdownView, Notice, Plugin, TFile, Menu } from 'obsidian';
import { ObsidianAgentSettings, DEFAULT_SETTINGS } from './settings';
import { ObsidianAgentSettingTab } from './settingsTab';
import { AIService } from './aiService';
import { AgentModal } from './agentModal';
import { ChatView, CHAT_VIEW_TYPE } from './chatView';
import { TemplateManager, DEFAULT_TEMPLATES } from './templateManager';
import { BatchProcessor } from './batchProcessor';

export default class ObsidianAgentPlugin extends Plugin {
	settings: ObsidianAgentSettings;
	aiService: AIService;
	templateManager: TemplateManager;
	batchProcessor: BatchProcessor;

	async onload() {
		await this.loadSettings();

		// Initialize services
		this.aiService = new AIService(this.settings);
		this.templateManager = new TemplateManager(this.settings.customTemplates.length > 0 
			? this.settings.customTemplates 
			: DEFAULT_TEMPLATES);
		this.batchProcessor = new BatchProcessor(this.app.vault, this.aiService);

		// Register chat view
		this.registerView(
			CHAT_VIEW_TYPE,
			(leaf) => new ChatView(leaf, this.aiService)
		);

		// Add ribbon icon for chat
		this.addRibbonIcon('message-square', 'Open AI Chat', () => {
			this.activateChatView();
		});

		// ORIGINAL COMMANDS
		this.registerOriginalCommands();

		// NEW ADVANCED COMMANDS
		this.registerAdvancedCommands();

		// Add settings tab
		this.addSettingTab(new ObsidianAgentSettingTab(this.app, this));

		console.log('Obsidian Agent plugin loaded with advanced features');
	}

	private registerOriginalCommands(): void {
		// Command: Ask AI Agent
		this.addCommand({
			id: 'ask-ai-agent',
			name: 'Ask AI Agent',
			editorCallback: (editor: Editor, view: MarkdownView) => {
				const context = editor.getValue();
				new AgentModal(this.app, this.aiService, context, (result) => {
					editor.replaceSelection(result);
				}).open();
			}
		});

		// Command: Generate Summary
		this.addCommand({
			id: 'generate-summary',
			name: 'Generate Summary',
			editorCallback: async (editor: Editor, view: MarkdownView) => {
				const selection = editor.getSelection();
				const textToSummarize = selection || editor.getValue();

				if (!textToSummarize.trim()) {
					new Notice('No text to summarize');
					return;
				}

				new Notice('Generating summary...');

				try {
					const summary = await this.aiService.generateCompletion(
						`Please provide a concise summary of the following text:\n\n${textToSummarize}`
					);
					editor.replaceSelection(`\n\n## Summary\n${summary}\n`);
					new Notice('Summary generated!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
					console.error('Summary Error:', error);
				}
			}
		});

		// Command: Expand Ideas
		this.addCommand({
			id: 'expand-ideas',
			name: 'Expand Ideas',
			editorCallback: async (editor: Editor, view: MarkdownView) => {
				const selection = editor.getSelection();

				if (!selection.trim()) {
					new Notice('Please select text to expand');
					return;
				}

				new Notice('Expanding ideas...');

				try {
					const expansion = await this.aiService.generateCompletion(
						`Please expand on the following ideas with more detail and context:\n\n${selection}`
					);
					editor.replaceSelection(expansion);
					new Notice('Ideas expanded!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
					console.error('Expand Error:', error);
				}
			}
		});

		// Command: Improve Writing
		this.addCommand({
			id: 'improve-writing',
			name: 'Improve Writing',
			editorCallback: async (editor: Editor, view: MarkdownView) => {
				const selection = editor.getSelection();

				if (!selection.trim()) {
					new Notice('Please select text to improve');
					return;
				}

				new Notice('Improving writing...');

				try {
					const improved = await this.aiService.generateCompletion(
						`Please improve the following text for clarity, grammar, and style:\n\n${selection}`
					);
					editor.replaceSelection(improved);
					new Notice('Writing improved!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
					console.error('Improve Writing Error:', error);
				}
			}
		});

		// Command: Generate Outline
		this.addCommand({
			id: 'generate-outline',
			name: 'Generate Outline',
			editorCallback: async (editor: Editor, view: MarkdownView) => {
				const topic = editor.getSelection();

				if (!topic.trim()) {
					new Notice('Please select a topic for the outline');
					return;
				}

				new Notice('Generating outline...');

				try {
					const outline = await this.aiService.generateCompletion(
						`Please create a detailed outline for the following topic:\n\n${topic}`
					);
					editor.replaceSelection(`\n\n${outline}\n`);
					new Notice('Outline generated!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
					console.error('Outline Error:', error);
				}
			}
		});

		// Command: Answer Question
		this.addCommand({
			id: 'answer-question',
			name: 'Answer Question Based on Note',
			editorCallback: (editor: Editor, view: MarkdownView) => {
				const noteContent = editor.getValue();
				new AgentModal(this.app, this.aiService, noteContent, (result) => {
					const cursor = editor.getCursor();
					editor.replaceRange(`\n\n**Q:** ${result}\n`, cursor);
				}).open();
			}
		});
	}

	private registerAdvancedCommands(): void {
		// Command: Translate Text
		this.addCommand({
			id: 'translate-text',
			name: 'Translate Text',
			editorCallback: async (editor: Editor) => {
				const selection = editor.getSelection();
				if (!selection.trim()) {
					new Notice('Please select text to translate');
					return;
				}

				const language = this.settings.defaultLanguage || 'Spanish';
				new Notice(`Translating to ${language}...`);

				try {
					const translated = await this.aiService.generateCompletion(
						`Translate the following text to ${language}. Maintain the original tone and meaning:\n\n${selection}`
					);
					editor.replaceSelection(translated);
					new Notice('Translation completed!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Generate Code
		this.addCommand({
			id: 'generate-code',
			name: 'Generate Code from Description',
			editorCallback: async (editor: Editor) => {
				const description = editor.getSelection();
				if (!description.trim()) {
					new Notice('Please select a code description');
					return;
				}

				new Notice('Generating code...');

				try {
					const code = await this.aiService.generateCompletion(
						`Generate clean, well-commented code for the following description. Include the programming language in a code block:\n\n${description}`
					);
					editor.replaceSelection(`\n\n${code}\n`);
					new Notice('Code generated!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Explain Code
		this.addCommand({
			id: 'explain-code',
			name: 'Explain Selected Code',
			editorCallback: async (editor: Editor) => {
				const code = editor.getSelection();
				if (!code.trim()) {
					new Notice('Please select code to explain');
					return;
				}

				new Notice('Analyzing code...');

				try {
					const explanation = await this.aiService.generateCompletion(
						`Explain the following code in simple terms, including what it does and how it works:\n\n\`\`\`\n${code}\n\`\`\``
					);
					editor.replaceSelection(`${code}\n\n**Explanation:**\n${explanation}\n`);
					new Notice('Explanation added!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Find and Fix Errors
		this.addCommand({
			id: 'find-fix-errors',
			name: 'Find and Fix Errors in Code',
			editorCallback: async (editor: Editor) => {
				const code = editor.getSelection();
				if (!code.trim()) {
					new Notice('Please select code to review');
					return;
				}

				new Notice('Checking for errors...');

				try {
					const fixed = await this.aiService.generateCompletion(
						`Review the following code for errors, bugs, or improvements. Provide the corrected code and explain the changes:\n\n\`\`\`\n${code}\n\`\`\``
					);
					editor.replaceSelection(fixed);
					new Notice('Code reviewed!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Generate Table of Contents
		this.addCommand({
			id: 'generate-toc',
			name: 'Generate Table of Contents',
			editorCallback: async (editor: Editor) => {
				const content = editor.getValue();
				
				new Notice('Generating table of contents...');

				try {
					const toc = await this.aiService.generateCompletion(
						`Generate a table of contents for the following document. Use markdown links:\n\n${content}`
					);
					const cursor = editor.getCursor();
					editor.replaceRange(`\n\n## Table of Contents\n${toc}\n\n`, { line: 0, ch: 0 });
					new Notice('Table of contents generated!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Generate Tags
		this.addCommand({
			id: 'generate-tags',
			name: 'Generate Tags for Note',
			editorCallback: async (editor: Editor) => {
				const content = editor.getValue();
				
				new Notice('Generating tags...');

				try {
					const tags = await this.aiService.generateCompletion(
						`Suggest 5-10 relevant tags for the following note. Return only the tags in format: #tag1 #tag2 #tag3:\n\n${content}`
					);
					const cursor = editor.getCursor();
					editor.replaceRange(`\n\nTags: ${tags}\n`, cursor);
					new Notice('Tags generated!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Create Flashcards
		this.addCommand({
			id: 'create-flashcards',
			name: 'Create Flashcards from Note',
			editorCallback: async (editor: Editor) => {
				const content = editor.getValue();
				
				new Notice('Creating flashcards...');

				try {
					const flashcards = await this.aiService.generateCompletion(
						`Create flashcards from the following content. Format each as "Q: [question] A: [answer]":\n\n${content}`
					);
					editor.replaceSelection(`\n\n## Flashcards\n${flashcards}\n`);
					new Notice('Flashcards created!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Brainstorm Ideas
		this.addCommand({
			id: 'brainstorm-ideas',
			name: 'Brainstorm Ideas',
			editorCallback: async (editor: Editor) => {
				const topic = editor.getSelection() || 'general topic';
				
				new Notice('Brainstorming ideas...');

				try {
					const ideas = await this.aiService.generateCompletion(
						`Generate 10 creative and unique ideas for: ${topic}. For each idea, provide a brief description.`
					);
					editor.replaceSelection(`\n\n## Ideas for: ${topic}\n${ideas}\n`);
					new Notice('Ideas generated!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Generate Meeting Notes Template
		this.addCommand({
			id: 'meeting-notes-template',
			name: 'Generate Meeting Notes Template',
			editorCallback: async (editor: Editor) => {
				const topic = editor.getSelection() || 'Meeting';
				
				try {
					const template = await this.aiService.generateCompletion(
						`Create a professional meeting notes template for: ${topic}. Include sections for date, attendees, agenda, discussion points, decisions, and action items.`
					);
					editor.replaceRange(template, { line: 0, ch: 0 });
					new Notice('Template created!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Rephrase Text
		this.addCommand({
			id: 'rephrase-text',
			name: 'Rephrase Selected Text',
			editorCallback: async (editor: Editor) => {
				const selection = editor.getSelection();
				if (!selection.trim()) {
					new Notice('Please select text to rephrase');
					return;
				}

				new Notice('Rephrasing...');

				try {
					const rephrased = await this.aiService.generateCompletion(
						`Rephrase the following text while maintaining its meaning. Make it clearer and more engaging:\n\n${selection}`
					);
					editor.replaceSelection(rephrased);
					new Notice('Text rephrased!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Make Text Professional
		this.addCommand({
			id: 'make-professional',
			name: 'Make Text More Professional',
			editorCallback: async (editor: Editor) => {
				const selection = editor.getSelection();
				if (!selection.trim()) {
					new Notice('Please select text to professionalize');
					return;
				}

				new Notice('Professionalizing text...');

				try {
					const professional = await this.aiService.generateCompletion(
						`Rewrite the following text in a professional, formal tone suitable for business communication:\n\n${selection}`
					);
					editor.replaceSelection(professional);
					new Notice('Text professionalized!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Make Text Casual
		this.addCommand({
			id: 'make-casual',
			name: 'Make Text More Casual',
			editorCallback: async (editor: Editor) => {
				const selection = editor.getSelection();
				if (!selection.trim()) {
					new Notice('Please select text to casualize');
					return;
				}

				new Notice('Casualizing text...');

				try {
					const casual = await this.aiService.generateCompletion(
						`Rewrite the following text in a casual, friendly tone:\n\n${selection}`
					);
					editor.replaceSelection(casual);
					new Notice('Text casualized!');
				} catch (error) {
					new Notice(`Error: ${error.message}`);
				}
			}
		});

		// Command: Show Token Usage Stats
		this.addCommand({
			id: 'show-token-stats',
			name: 'Show Token Usage Statistics',
			callback: () => {
				if (!this.settings.enableTokenTracking) {
					new Notice('Token tracking is disabled. Enable it in settings.');
					return;
				}

				const stats = this.aiService.getTokenTracker().getUsageStats();
				const message = `
**Token Usage Statistics**

Total Requests: ${stats.requestCount}
Total Tokens: ${stats.total.tokens.toLocaleString()}
Estimated Cost: $${stats.total.cost.toFixed(4)}

**Last 24 Hours**
Tokens: ${stats.last24h.tokens.toLocaleString()}
Cost: $${stats.last24h.cost.toFixed(4)}

**Last 7 Days**
Tokens: ${stats.last7d.tokens.toLocaleString()}
Cost: $${stats.last7d.cost.toFixed(4)}
				`.trim();

				new Notice(message, 10000);
			}
		});

		// Command: Clear Cache
		this.addCommand({
			id: 'clear-cache',
			name: 'Clear Response Cache',
			callback: () => {
				if (!this.settings.enableCaching) {
					new Notice('Caching is disabled');
					return;
				}

				this.aiService.getResponseCache().clear();
				new Notice('Response cache cleared!');
			}
		});

		// Command: Open Chat Sidebar
		this.addCommand({
			id: 'open-chat-sidebar',
			name: 'Open AI Chat Sidebar',
			callback: () => {
				this.activateChatView();
			}
		});
	}

	async activateChatView() {
		const { workspace } = this.app;

		let leaf = workspace.getLeavesOfType(CHAT_VIEW_TYPE)[0];

		if (!leaf) {
			const rightLeaf = workspace.getRightLeaf(false);
			if (rightLeaf) {
				leaf = rightLeaf;
				await leaf.setViewState({ type: CHAT_VIEW_TYPE, active: true });
			}
		}

		if (leaf) {
			workspace.revealLeaf(leaf);
		}
	}

	onunload() {
		console.log('Obsidian Agent plugin unloaded');
	}

	async loadSettings() {
		this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
	}

	async saveSettings() {
		await this.saveData(this.settings);
		// Update AI service with new settings
		this.aiService = new AIService(this.settings);
	}
}
