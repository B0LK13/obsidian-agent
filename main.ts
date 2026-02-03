import { App, Editor, MarkdownView, Modal, Notice, Plugin, TFile } from 'obsidian';
import { ObsidianAgentSettings, DEFAULT_SETTINGS, AIProfile, createDefaultProfile } from './settings';
import { ObsidianAgentSettingTab } from './settingsTab';
import { AIService, CompletionResult } from './aiService';
import { EnhancedAgentModal } from './agentModalEnhanced';
import { ContextProvider, ContextConfig } from './contextProvider';
import { ValidationError, APIError, ConfigurationError } from './src/errors';
import { DeadLinkDetector } from './src/deadLinkDetector';

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
