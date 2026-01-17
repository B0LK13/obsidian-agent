import { App, Editor, MarkdownView, Modal, Notice, Plugin, TFile } from 'obsidian';
import { ObsidianAgentSettings, DEFAULT_SETTINGS, AIProfile, createDefaultProfile, generateProfileId } from './settings';
import { ObsidianAgentSettingTab } from './settingsTab';
import { AIService, CompletionResult } from './aiService';
import { AgentModal } from './agentModal';
import { ContextProvider, ContextConfig, GatheredContext } from './contextProvider';

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
	settings: ObsidianAgentSettings;
	aiService: AIService;
	contextProvider: ContextProvider;

	async onload() {
		await this.loadSettings();
		await this.migrateToProfiles();

		this.aiService = new AIService(this.settings);
		this.contextProvider = new ContextProvider(this.app);

		if (!this.settings.totalRequests) {
			this.settings.totalRequests = 0;
			this.settings.totalTokensUsed = 0;
			this.settings.estimatedCost = 0;
		}

		// Command: Ask AI Agent
		this.addCommand({
			id: 'ask-ai-agent',
			name: 'Ask AI Agent',
			editorCallback: async (editor: Editor, view: MarkdownView) => {
				const currentContent = editor.getValue();
				const context = await this.gatherFullContext(view.file, currentContent);
				new AgentModal(
					this.app, 
					this.aiService, 
					this.settings,
					() => this.saveSettings(),
					context, 
					(result) => {
						editor.replaceSelection(result);
					}
				).open();
			}
		});

		// Command: Ask AI Agent (with vault context)
		this.addCommand({
			id: 'ask-ai-agent-vault-context',
			name: 'Ask AI Agent (with Linked Notes)',
			editorCallback: async (editor: Editor, view: MarkdownView) => {
				const currentContent = editor.getValue();
				const context = await this.gatherFullContext(view.file, currentContent, true);
				new AgentModal(
					this.app, 
					this.aiService, 
					this.settings,
					() => this.saveSettings(),
					context, 
					(result) => {
						editor.replaceSelection(result);
					}
				).open();
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
				new AgentModal(
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

	private async gatherFullContext(file: TFile | null, currentContent: string, forceVaultContext: boolean = false): Promise<string> {
		const config = this.settings.contextConfig;
		
		// Check if any vault context is enabled
		const hasVaultContext = forceVaultContext || 
			config?.enableLinkedNotes || 
			config?.enableBacklinks || 
			config?.enableTagContext || 
			config?.enableFolderContext;

		if (!hasVaultContext) {
			return currentContent;
		}

		// Build context config
		const contextConfig: ContextConfig = {
			sources: [
				{ type: 'current', enabled: true },
				{ type: 'linked', enabled: forceVaultContext || config?.enableLinkedNotes || false },
				{ type: 'backlinks', enabled: config?.enableBacklinks || false },
				{ type: 'tags', enabled: config?.enableTagContext || false },
				{ type: 'folder', enabled: config?.enableFolderContext || false }
			],
			maxNotesPerSource: config?.maxNotesPerSource || 5,
			maxTokensPerNote: config?.maxTokensPerNote || 1000,
			linkDepth: config?.linkDepth || 1,
			excludeFolders: (config?.excludeFolders || 'templates, .obsidian').split(',').map(s => s.trim())
		};

		try {
			const contexts = await this.contextProvider.gatherContext(
				file,
				currentContent,
				contextConfig,
				this.settings.apiProvider
			);

			const formattedContext = this.contextProvider.formatContextsForPrompt(contexts);
			
			if (contexts.length > 1) {
				const additionalNotes = contexts.length - 1;
				new Notice(`Loaded context from ${additionalNotes} additional note(s)`);
			}

			return formattedContext;
		} catch (error) {
			console.error('Failed to gather vault context:', error);
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
