import { Editor, MarkdownView, Notice, Plugin } from 'obsidian';
import { ObsidianAgentSettings, DEFAULT_SETTINGS } from './settings';
import { ObsidianAgentSettingTab } from './settingsTab';
import { AIService, CompletionResult } from './aiService';
import { AgentModal } from './agentModal';

export default class ObsidianAgentPlugin extends Plugin {
	settings: ObsidianAgentSettings;
	aiService: AIService;

	async onload() {
		await this.loadSettings();

		this.aiService = new AIService(this.settings);

		if (!this.settings.totalRequests) {
			this.settings.totalRequests = 0;
			this.settings.totalTokensUsed = 0;
			this.settings.estimatedCost = 0;
		}

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
					const summaryResult = await this.aiService.generateCompletion(
						`Please provide a concise summary of the following text:\n\n${textToSummarize}`
					);
					await this.trackTokenUsage(summaryResult);
					editor.replaceSelection(`\n\n## Summary\n${summaryResult.text}\n`);
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
					const expansionResult = await this.aiService.generateCompletion(
						`Please expand on following ideas with more detail and context:\n\n${selection}`
					);
					await this.trackTokenUsage(expansionResult);
					editor.replaceSelection(expansionResult.text);
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
					const improvedResult = await this.aiService.generateCompletion(
						`Please improve following text for clarity, grammar, and style:\n\n${selection}`
					);
					await this.trackTokenUsage(improvedResult);
					editor.replaceSelection(improvedResult.text);
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
					const outlineResult = await this.aiService.generateCompletion(
						`Please create a detailed outline for the following topic:\n\n${topic}`
					);
					await this.trackTokenUsage(outlineResult);
					editor.replaceSelection(`\n\n${outlineResult.text}\n`);
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

	private async trackTokenUsage(result: CompletionResult): Promise<void> {
		if (!this.settings.enableTokenTracking || !result.tokensUsed) {
			return;
		}

		this.settings.totalRequests = (this.settings.totalRequests || 0) + 1;
		this.settings.totalTokensUsed = (this.settings.totalTokensUsed || 0) + result.tokensUsed;

		const cost = this.estimateCost(result);
		this.settings.estimatedCost = (this.settings.estimatedCost || 0) + cost;

		if (this.settings.estimatedCost > this.settings.costThreshold) {
			new Notice(`Cost warning: You've spent approximately $${this.settings.estimatedCost.toFixed(2)} this session`, 5000);
		}

		await this.saveSettings();
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
		await this.saveData(this.settings);
		// Update AI service with new settings
		this.aiService = new AIService(this.settings);
	}
}
