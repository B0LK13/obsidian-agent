import { Editor, MarkdownView, Notice, Plugin } from 'obsidian';
import { ObsidianAgentSettings, DEFAULT_SETTINGS } from './settings';
import { ObsidianAgentSettingTab } from './settingsTab';
import { AIService } from './aiService';
import { AgentModal } from './agentModal';

export default class ObsidianAgentPlugin extends Plugin {
	settings: ObsidianAgentSettings;
	aiService: AIService;

	async onload() {
		await this.loadSettings();

		this.aiService = new AIService(this.settings);

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

		// Add settings tab
		this.addSettingTab(new ObsidianAgentSettingTab(this.app, this));

		console.log('Obsidian Agent plugin loaded');
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
