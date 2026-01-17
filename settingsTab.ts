import { App, PluginSettingTab, Setting, Notice, Modal, TextComponent, DropdownComponent, TextAreaComponent } from 'obsidian';
import ObsidianAgentPlugin from './main';
import { AIService } from './aiService';
import { AIProfile, generateProfileId, DEFAULT_PROFILES } from './settings';
import { PromptTemplate, BUILT_IN_TEMPLATES, generateTemplateId } from './promptTemplates';

export class ObsidianAgentSettingTab extends PluginSettingTab {
	plugin: ObsidianAgentPlugin;
	private errorElements: Map<string, HTMLElement> = new Map();

	constructor(app: App, plugin: ObsidianAgentPlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	private addSettingsActions(containerEl: HTMLElement): void {
		const actionsContainer = containerEl.createDiv({ cls: 'settings-actions' });
		actionsContainer.style.display = 'flex';
		actionsContainer.style.gap = '0.5rem';
		actionsContainer.style.marginBottom = '1rem';

		const exportButton = actionsContainer.createEl('button', {
			text: 'Export Settings',
			cls: 'mod-cta'
		});
		exportButton.addEventListener('click', () => this.exportSettings());

		const importButton = actionsContainer.createEl('button', {
			text: 'Import Settings',
			cls: 'mod-cta'
		});
		importButton.addEventListener('click', () => this.importSettings());

		const desc = actionsContainer.createDiv({ cls: 'setting-item-description' });
		desc.textContent = 'Backup or restore your configuration';
	}

	private addProfileSection(containerEl: HTMLElement): void {
		containerEl.createEl('h3', { text: 'AI Profiles' });

		const activeProfile = this.plugin.getActiveProfile();
		
		// Profile selector
		new Setting(containerEl)
			.setName('Active Profile')
			.setDesc('Switch between different AI configurations')
			.addDropdown(dropdown => {
				this.plugin.settings.profiles.forEach(profile => {
					dropdown.addOption(profile.id, profile.name);
				});
				dropdown.setValue(this.plugin.settings.activeProfileId);
				dropdown.onChange(async (value) => {
					await this.plugin.switchProfile(value);
					this.display();
				});
			});

		// Profile actions
		const actionsContainer = containerEl.createDiv({ cls: 'profile-actions' });
		actionsContainer.style.display = 'flex';
		actionsContainer.style.gap = '0.5rem';
		actionsContainer.style.marginBottom = '1rem';

		const createButton = actionsContainer.createEl('button', {
			text: 'Create Profile',
			cls: 'mod-cta'
		});
		createButton.addEventListener('click', () => this.openProfileEditor());

		const editButton = actionsContainer.createEl('button', {
			text: 'Edit Current'
		});
		editButton.addEventListener('click', () => {
			if (activeProfile) {
				this.openProfileEditor(activeProfile);
			}
		});

		const duplicateButton = actionsContainer.createEl('button', {
			text: 'Duplicate'
		});
		duplicateButton.addEventListener('click', async () => {
			if (activeProfile) {
				const newProfile: AIProfile = {
					...activeProfile,
					id: generateProfileId(),
					name: `${activeProfile.name} (Copy)`
				};
				await this.plugin.createProfile(newProfile);
				this.display();
			}
		});

		if (activeProfile && activeProfile.id !== 'default') {
			const deleteButton = actionsContainer.createEl('button', {
				text: 'Delete',
				cls: 'mod-warning'
			});
			deleteButton.addEventListener('click', async () => {
				if (confirm(`Delete profile "${activeProfile.name}"?`)) {
					await this.plugin.deleteProfile(activeProfile.id);
					this.display();
				}
			});
		}

		// Quick add from templates
		new Setting(containerEl)
			.setName('Add from Template')
			.setDesc('Quickly add a preconfigured profile')
			.addDropdown(dropdown => {
				dropdown.addOption('', 'Select template...');
				DEFAULT_PROFILES.forEach(template => {
					dropdown.addOption(template.id, template.name);
				});
				dropdown.onChange(async (templateId) => {
					if (!templateId) return;
					const template = DEFAULT_PROFILES.find(t => t.id === templateId);
					if (template) {
						const newProfile: AIProfile = {
							...template,
							id: generateProfileId()
						};
						await this.plugin.createProfile(newProfile);
						this.display();
					}
				});
			});

		// Show active profile info
		if (activeProfile) {
			const infoContainer = containerEl.createDiv({ cls: 'profile-info' });
			infoContainer.style.padding = '0.75rem';
			infoContainer.style.backgroundColor = 'var(--background-secondary)';
			infoContainer.style.borderRadius = 'var(--radius-s)';
			infoContainer.style.marginBottom = '1rem';

			infoContainer.createEl('strong', { text: `Active: ${activeProfile.name}` });
			const details = infoContainer.createDiv();
			details.style.fontSize = 'var(--font-smaller)';
			details.style.color = 'var(--text-muted)';
			details.style.marginTop = '0.25rem';
			details.textContent = `Provider: ${activeProfile.apiProvider} | Model: ${activeProfile.model} | Temp: ${activeProfile.temperature}`;
		}
	}

	private openProfileEditor(existingProfile?: AIProfile): void {
		const modal = new ProfileEditorModal(
			this.app,
			existingProfile || null,
			async (profile) => {
				if (existingProfile) {
					await this.plugin.updateProfile(profile);
				} else {
					await this.plugin.createProfile(profile);
				}
				this.display();
			}
		);
		modal.open();
	}

	private addTemplatesSection(containerEl: HTMLElement): void {
		containerEl.createEl('h3', { text: 'Prompt Templates' });

		const customCount = this.plugin.settings.customTemplates?.length || 0;
		const builtInCount = BUILT_IN_TEMPLATES.length;

		new Setting(containerEl)
			.setName('Templates')
			.setDesc(`${builtInCount} built-in templates, ${customCount} custom templates`)
			.addButton(button => button
				.setButtonText('Create Custom Template')
				.setCta()
				.onClick(() => this.openTemplateEditor()));

		// List custom templates
		if (customCount > 0) {
			const listContainer = containerEl.createDiv({ cls: 'custom-templates-list' });
			listContainer.style.marginTop = '0.5rem';
			listContainer.style.marginBottom = '1rem';

			this.plugin.settings.customTemplates.forEach(template => {
				const item = listContainer.createDiv({ cls: 'template-list-item' });
				item.style.display = 'flex';
				item.style.justifyContent = 'space-between';
				item.style.alignItems = 'center';
				item.style.padding = '0.5rem';
				item.style.marginBottom = '0.25rem';
				item.style.backgroundColor = 'var(--background-secondary)';
				item.style.borderRadius = 'var(--radius-s)';

				const info = item.createDiv();
				info.createEl('strong', { text: template.name });
				const meta = info.createDiv();
				meta.style.fontSize = 'var(--font-smaller)';
				meta.style.color = 'var(--text-muted)';
				meta.textContent = `${template.category} - ${template.description}`;

				const actions = item.createDiv({ cls: 'template-actions' });
				actions.style.display = 'flex';
				actions.style.gap = '0.25rem';

				const editBtn = actions.createEl('button', { text: 'Edit' });
				editBtn.style.fontSize = 'var(--font-smaller)';
				editBtn.addEventListener('click', () => this.openTemplateEditor(template));

				const deleteBtn = actions.createEl('button', { text: 'Delete', cls: 'mod-warning' });
				deleteBtn.style.fontSize = 'var(--font-smaller)';
				deleteBtn.addEventListener('click', async () => {
					if (confirm(`Delete template "${template.name}"?`)) {
						const index = this.plugin.settings.customTemplates.findIndex(t => t.id === template.id);
						if (index >= 0) {
							this.plugin.settings.customTemplates.splice(index, 1);
							await this.plugin.saveSettings();
							this.display();
							new Notice('Template deleted');
						}
					}
				});
			});
		}
	}

	private openTemplateEditor(existingTemplate?: PromptTemplate): void {
		const modal = new TemplateEditorModal(
			this.app,
			existingTemplate || null,
			async (template) => {
				if (!this.plugin.settings.customTemplates) {
					this.plugin.settings.customTemplates = [];
				}

				if (existingTemplate) {
					const index = this.plugin.settings.customTemplates.findIndex(t => t.id === template.id);
					if (index >= 0) {
						this.plugin.settings.customTemplates[index] = template;
					}
				} else {
					this.plugin.settings.customTemplates.push(template);
				}
				
				await this.plugin.saveSettings();
				this.display();
				new Notice(existingTemplate ? 'Template updated' : 'Template created');
			}
		);
		modal.open();
	}

	display(): void {
		const {containerEl} = this;

		containerEl.empty();
		this.errorElements.clear();

		containerEl.createEl('h2', {text: 'Obsidian Agent Settings'});

		this.addSettingsActions(containerEl);
		
		containerEl.createEl('hr');
		
		this.addProfileSection(containerEl);

		containerEl.createEl('hr');
		
		this.addTemplatesSection(containerEl);

		containerEl.createEl('hr');

		new Setting(containerEl)
			.setName('API Provider')
			.setDesc('Select your AI API provider')
			.addDropdown(dropdown => dropdown
				.addOption('openai', 'OpenAI')
				.addOption('anthropic', 'Anthropic')
				.addOption('custom', 'Custom API')
				.setValue(this.plugin.settings.apiProvider)
				.onChange(async (value: 'openai' | 'anthropic' | 'custom') => {
					this.plugin.settings.apiProvider = value;
					await this.plugin.saveSettings();
					this.display();
				}));

		this.addApiKeySetting(containerEl);

		if (this.plugin.settings.apiProvider === 'custom') {
			this.addCustomApiUrlSetting(containerEl);
		}

		this.addModelSetting(containerEl);
		this.addTemperatureSetting(containerEl);
		this.addMaxTokensSetting(containerEl);
		this.addSystemPromptSetting(containerEl);
		this.addContextAwarenessSetting(containerEl);
		this.addVaultContextSettings(containerEl);
		this.addConversationPersistenceSetting(containerEl);
		this.addTokenTrackingSetting(containerEl);
		this.addReconnectButton(containerEl);
		this.addTestConnectionButton(containerEl);
	}

	private addVaultContextSettings(containerEl: HTMLElement): void {
		containerEl.createEl('h3', { text: 'Vault-Wide Context' });
		
		const desc = containerEl.createEl('p', { cls: 'setting-item-description' });
		desc.textContent = 'Include content from related notes to give AI more context about your knowledge base.';
		desc.style.marginBottom = '1rem';

		new Setting(containerEl)
			.setName('Include Linked Notes')
			.setDesc('Add content from notes linked in the current note')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.contextConfig?.enableLinkedNotes || false)
				.onChange(async (value) => {
					if (!this.plugin.settings.contextConfig) {
						this.plugin.settings.contextConfig = {
							enableLinkedNotes: false,
							enableBacklinks: false,
							enableTagContext: false,
							enableFolderContext: false,
							maxNotesPerSource: 5,
							maxTokensPerNote: 1000,
							linkDepth: 1,
							excludeFolders: 'templates, .obsidian'
						};
					}
					this.plugin.settings.contextConfig.enableLinkedNotes = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Include Backlinks')
			.setDesc('Add content from notes that link TO the current note')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.contextConfig?.enableBacklinks || false)
				.onChange(async (value) => {
					if (!this.plugin.settings.contextConfig) {
						this.plugin.settings.contextConfig = {
							enableLinkedNotes: false,
							enableBacklinks: false,
							enableTagContext: false,
							enableFolderContext: false,
							maxNotesPerSource: 5,
							maxTokensPerNote: 1000,
							linkDepth: 1,
							excludeFolders: 'templates, .obsidian'
						};
					}
					this.plugin.settings.contextConfig.enableBacklinks = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Include Same-Tag Notes')
			.setDesc('Add content from notes with the same tags')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.contextConfig?.enableTagContext || false)
				.onChange(async (value) => {
					if (!this.plugin.settings.contextConfig) {
						this.plugin.settings.contextConfig = {
							enableLinkedNotes: false,
							enableBacklinks: false,
							enableTagContext: false,
							enableFolderContext: false,
							maxNotesPerSource: 5,
							maxTokensPerNote: 1000,
							linkDepth: 1,
							excludeFolders: 'templates, .obsidian'
						};
					}
					this.plugin.settings.contextConfig.enableTagContext = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Include Folder Notes')
			.setDesc('Add content from notes in the same folder')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.contextConfig?.enableFolderContext || false)
				.onChange(async (value) => {
					if (!this.plugin.settings.contextConfig) {
						this.plugin.settings.contextConfig = {
							enableLinkedNotes: false,
							enableBacklinks: false,
							enableTagContext: false,
							enableFolderContext: false,
							maxNotesPerSource: 5,
							maxTokensPerNote: 1000,
							linkDepth: 1,
							excludeFolders: 'templates, .obsidian'
						};
					}
					this.plugin.settings.contextConfig.enableFolderContext = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Max Notes Per Source')
			.setDesc('Maximum number of notes to include from each source')
			.addText(text => text
				.setPlaceholder('5')
				.setValue(String(this.plugin.settings.contextConfig?.maxNotesPerSource || 5))
				.onChange(async (value) => {
					const parsed = parseInt(value);
					if (!this.plugin.settings.contextConfig) {
						this.plugin.settings.contextConfig = {
							enableLinkedNotes: false,
							enableBacklinks: false,
							enableTagContext: false,
							enableFolderContext: false,
							maxNotesPerSource: 5,
							maxTokensPerNote: 1000,
							linkDepth: 1,
							excludeFolders: 'templates, .obsidian'
						};
					}
					this.plugin.settings.contextConfig.maxNotesPerSource = isNaN(parsed) ? 5 : Math.max(1, parsed);
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Max Tokens Per Note')
			.setDesc('Maximum tokens to include from each additional note')
			.addText(text => text
				.setPlaceholder('1000')
				.setValue(String(this.plugin.settings.contextConfig?.maxTokensPerNote || 1000))
				.onChange(async (value) => {
					const parsed = parseInt(value);
					if (!this.plugin.settings.contextConfig) {
						this.plugin.settings.contextConfig = {
							enableLinkedNotes: false,
							enableBacklinks: false,
							enableTagContext: false,
							enableFolderContext: false,
							maxNotesPerSource: 5,
							maxTokensPerNote: 1000,
							linkDepth: 1,
							excludeFolders: 'templates, .obsidian'
						};
					}
					this.plugin.settings.contextConfig.maxTokensPerNote = isNaN(parsed) ? 1000 : Math.max(100, parsed);
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Link Depth')
			.setDesc('How many levels of links to follow (1 = direct links only)')
			.addDropdown(dropdown => dropdown
				.addOption('1', '1 (Direct links)')
				.addOption('2', '2 (Links of links)')
				.setValue(String(this.plugin.settings.contextConfig?.linkDepth || 1))
				.onChange(async (value) => {
					if (!this.plugin.settings.contextConfig) {
						this.plugin.settings.contextConfig = {
							enableLinkedNotes: false,
							enableBacklinks: false,
							enableTagContext: false,
							enableFolderContext: false,
							maxNotesPerSource: 5,
							maxTokensPerNote: 1000,
							linkDepth: 1,
							excludeFolders: 'templates, .obsidian'
						};
					}
					this.plugin.settings.contextConfig.linkDepth = parseInt(value);
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Exclude Folders')
			.setDesc('Folders to exclude from context (comma-separated)')
			.addText(text => text
				.setPlaceholder('templates, .obsidian')
				.setValue(this.plugin.settings.contextConfig?.excludeFolders || 'templates, .obsidian')
				.onChange(async (value) => {
					if (!this.plugin.settings.contextConfig) {
						this.plugin.settings.contextConfig = {
							enableLinkedNotes: false,
							enableBacklinks: false,
							enableTagContext: false,
							enableFolderContext: false,
							maxNotesPerSource: 5,
							maxTokensPerNote: 1000,
							linkDepth: 1,
							excludeFolders: 'templates, .obsidian'
						};
					}
					this.plugin.settings.contextConfig.excludeFolders = value;
					await this.plugin.saveSettings();
				}));
	}

	private addConversationPersistenceSetting(containerEl: HTMLElement): void {
		containerEl.createEl('h3', { text: 'Conversation History' });

		new Setting(containerEl)
			.setName('Enable Conversation Persistence')
			.setDesc('Save conversations across sessions')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.enableConversationPersistence)
				.onChange(async (value) => {
					this.plugin.settings.enableConversationPersistence = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Max Saved Conversations')
			.setDesc('Maximum number of conversations to keep (oldest are deleted)')
			.addText(text => text
				.setPlaceholder('20')
				.setValue(String(this.plugin.settings.maxConversations))
				.onChange(async (value) => {
					const parsed = parseInt(value);
					this.plugin.settings.maxConversations = isNaN(parsed) || parsed < 1 ? 20 : parsed;
					await this.plugin.saveSettings();
				}));

		// Show saved conversations count
		const conversationCount = this.plugin.settings.conversations?.length || 0;
		const countSetting = new Setting(containerEl)
			.setName('Saved Conversations')
			.setDesc(`${conversationCount} conversation(s) saved`);

		if (conversationCount > 0) {
			countSetting.addButton(button => button
				.setButtonText('Clear All')
				.setWarning()
				.onClick(async () => {
					if (confirm('Delete all saved conversations? This cannot be undone.')) {
						this.plugin.settings.conversations = [];
						this.plugin.settings.activeConversationId = undefined;
						await this.plugin.saveSettings();
						this.display();
						new Notice('All conversations deleted');
					}
				}));
		}
	}

	private addTokenTrackingSetting(containerEl: HTMLElement): void {
		new Setting(containerEl)
			.setName('Enable Token Tracking')
			.setDesc('Track API token usage and estimate costs')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.enableTokenTracking)
				.onChange(async (value) => {
					this.plugin.settings.enableTokenTracking = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Cost Warning Threshold ($)')
			.setDesc('Show warning when estimated cost exceeds this amount')
			.addText(text => text
				.setPlaceholder('10')
				.setValue(String(this.plugin.settings.costThreshold))
				.onChange(async (value) => {
					const parsed = parseFloat(value);
					this.plugin.settings.costThreshold = isNaN(parsed) ? 10 : parsed;
					await this.plugin.saveSettings();
				}));

		this.addUsageSummary(containerEl);
	}

	private addUsageSummary(containerEl: HTMLElement): void {
		const summaryContainer = containerEl.createDiv({ cls: 'usage-summary' });
		summaryContainer.style.marginTop = '1.5rem';
		summaryContainer.style.padding = '1rem';
		summaryContainer.style.border = '1px solid var(--background-modifier-border)';
		summaryContainer.style.borderRadius = 'var(--radius-s)';
		summaryContainer.style.backgroundColor = 'var(--background-secondary)';

		const usage = this.plugin.settings as any;
		const tokensUsed = usage.totalTokensUsed || 0;
		const requestsMade = usage.totalRequests || 0;
		const estimatedCost = usage.estimatedCost || 0;

		summaryContainer.createEl('h3', { text: 'Usage Summary' });
		
		const statsGrid = summaryContainer.createDiv({ cls: 'stats-grid' });
		statsGrid.style.display = 'grid';
		statsGrid.style.gridTemplateColumns = 'repeat(2, 1fr)';
		statsGrid.style.gap = '0.5rem';
		statsGrid.style.marginTop = '0.5rem';

		this.createStatCard(statsGrid, 'Total Requests', String(requestsMade));
		this.createStatCard(statsGrid, 'Tokens Used', String(tokensUsed));
		this.createStatCard(statsGrid, 'Estimated Cost', `$${estimatedCost.toFixed(2)}`);

		if (tokensUsed > 0) {
			const avgPerRequest = (tokensUsed / requestsMade).toFixed(0);
			this.createStatCard(statsGrid, 'Avg Tokens/Request', avgPerRequest);
		}

		const exportButton = summaryContainer.createEl('button', {
			text: 'Export Usage Data (CSV)',
			cls: 'mod-cta'
		});
		exportButton.style.marginTop = '1rem';
		exportButton.addEventListener('click', () => this.exportUsageData());
	}

	private createStatCard(container: HTMLElement, label: string, value: string): void {
		const card = container.createDiv({ cls: 'stat-card' });
		card.style.padding = '0.5rem';
		card.style.borderRadius = 'var(--radius-s)';
		card.style.backgroundColor = 'var(--background-primary)';

		const labelEl = card.createDiv({ cls: 'stat-label' });
		labelEl.style.fontSize = 'var(--font-smaller)';
		labelEl.style.color = 'var(--text-muted)';
		labelEl.textContent = label;

		const valueEl = card.createDiv({ cls: 'stat-value' });
		valueEl.style.fontSize = 'var(--font-ui-large)';
		valueEl.style.fontWeight = 'bold';
		valueEl.textContent = value;
	}

	private exportUsageData(): void {
		const usage = this.plugin.settings as any;
		const csv = [
			'Metric,Value',
			`Total Requests,${usage.totalRequests || 0}`,
			`Total Tokens Used,${usage.totalTokensUsed || 0}`,
			`Estimated Cost ($),${(usage.estimatedCost || 0).toFixed(2)}`,
			`Export Date,${new Date().toISOString()}`
		].join('\n');

		const blob = new Blob([csv], {type: 'text/csv'});
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `obsidian-agent-usage-${new Date().toISOString().split('T')[0]}.csv`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);

		new Notice('Usage data exported');
	}

	private addApiKeySetting(containerEl: HTMLElement): void {
		new Setting(containerEl)
			.setName('API Key')
			.setDesc('Enter your API key for the selected provider')
			.addText(text => text
				.setPlaceholder('Enter your API key')
				.setValue(this.plugin.settings.apiKey)
				.onChange(async (value) => {
					this.plugin.settings.apiKey = value;
					await this.plugin.saveSettings();
					this.validateApiKeySetting(value, containerEl);
				}));
		this.validateApiKeySetting(this.plugin.settings.apiKey, containerEl);
	}

	private validateApiKeySetting(value: string, containerEl: HTMLElement): void {
		const allSettings = Array.from(containerEl.querySelectorAll('.setting-item'));
		const settingEl = allSettings.find(el => el.textContent?.includes('API Key')) as HTMLElement;
		if (!settingEl) return;

		this.clearError('apiKey', settingEl);

		if (this.plugin.settings.apiProvider !== 'custom' && !value.trim()) {
			this.showError('apiKey', settingEl, 'API Key is required for this provider');
		}
	}

	private addCustomApiUrlSetting(containerEl: HTMLElement): void {
		new Setting(containerEl)
			.setName('Custom API URL')
			.setDesc('Enter URL for your custom API endpoint')
			.addText(text => text
				.setPlaceholder('https://api.example.com/v1/chat')
				.setValue(this.plugin.settings.customApiUrl)
				.onChange(async (value) => {
					this.plugin.settings.customApiUrl = value;
					await this.plugin.saveSettings();
					this.validateCustomApiUrlSetting(value, containerEl);
				}));
		this.validateCustomApiUrlSetting(this.plugin.settings.customApiUrl, containerEl);
	}

	private validateCustomApiUrlSetting(value: string, containerEl: HTMLElement): void {
		const allSettings = Array.from(containerEl.querySelectorAll('.setting-item'));
		const settingEl = allSettings.find(el => el.textContent?.includes('Custom API URL')) as HTMLElement;
		
		if (!settingEl) return;

		this.clearError('customApiUrl', settingEl);

		if (!value.trim()) {
			this.showError('customApiUrl', settingEl, 'Custom API URL is required when using Custom API provider');
		} else if (!this.isValidUrl(value)) {
			this.showError('customApiUrl', settingEl, 'Please enter a valid URL (e.g., https://api.example.com/v1/chat)');
		}
	}

	private isValidUrl(string: string): boolean {
		try {
			new URL(string);
			return true;
		} catch (_) {
			return false;
		}
	}

	private addModelSetting(containerEl: HTMLElement): void {
		new Setting(containerEl)
			.setName('Model')
			.setDesc('AI model to use')
			.addText(text => text
				.setPlaceholder('gpt-4')
				.setValue(this.plugin.settings.model)
				.onChange(async (value) => {
					this.plugin.settings.model = value;
					await this.plugin.saveSettings();
					this.validateModelSetting(value, containerEl);
				}));
		this.validateModelSetting(this.plugin.settings.model, containerEl);
	}

	private validateModelSetting(value: string, containerEl: HTMLElement): void {
		const allSettings = Array.from(containerEl.querySelectorAll('.setting-item'));
		const settingEl = allSettings.find(el => el.textContent?.includes('Model') && !el.textContent?.includes('Temperature')) as HTMLElement;
		
		if (!settingEl) return;

		this.clearError('model', settingEl);

		if (!value.trim()) {
			this.showError('model', settingEl, 'Model name is required');
		}
	}

	private addTemperatureSetting(containerEl: HTMLElement): void {
		new Setting(containerEl)
			.setName('Temperature')
			.setDesc('Controls randomness (0-1). Higher values make output more random.')
			.addSlider(slider => slider
				.setLimits(0, 1, 0.1)
				.setValue(this.plugin.settings.temperature)
				.setDynamicTooltip()
				.onChange(async (value) => {
					this.plugin.settings.temperature = value;
					await this.plugin.saveSettings();
				}));
	}

	private addMaxTokensSetting(containerEl: HTMLElement): void {
		new Setting(containerEl)
			.setName('Max Tokens')
			.setDesc('Maximum number of tokens to generate')
			.addText(text => text
				.setPlaceholder('2000')
				.setValue(String(this.plugin.settings.maxTokens))
				.onChange(async (value) => {
					const parsed = parseInt(value);
					this.plugin.settings.maxTokens = isNaN(parsed) ? 2000 : parsed;
					await this.plugin.saveSettings();
					this.validateMaxTokensSetting(value, containerEl);
				}));
		this.validateMaxTokensSetting(String(this.plugin.settings.maxTokens), containerEl);
	}

	private validateMaxTokensSetting(value: string, containerEl: HTMLElement): void {
		const allSettings = Array.from(containerEl.querySelectorAll('.setting-item'));
		const settingEl = allSettings.find(el => el.textContent?.includes('Max Tokens')) as HTMLElement;
		
		if (!settingEl) return;

		this.clearError('maxTokens', settingEl);

		const parsed = parseInt(value);
		if (isNaN(parsed) || parsed < 1) {
			this.showError('maxTokens', settingEl, 'Max Tokens must be a positive integer (at least 1)');
		} else if (parsed > 100000) {
			this.showError('maxTokens', settingEl, 'Max Tokens value is too large. Please use a reasonable value (e.g., 2000-8000)');
		}
	}

	private addSystemPromptSetting(containerEl: HTMLElement): void {
		new Setting(containerEl)
			.setName('System Prompt')
			.setDesc('The system prompt that defines AI assistant behavior')
			.addTextArea(text => text
				.setPlaceholder('You are a helpful assistant...')
				.setValue(this.plugin.settings.systemPrompt)
				.onChange(async (value) => {
					this.plugin.settings.systemPrompt = value;
					await this.plugin.saveSettings();
				}));
	}

	private addContextAwarenessSetting(containerEl: HTMLElement): void {
		new Setting(containerEl)
			.setName('Enable Context Awareness')
			.setDesc('Allow agent to access current note context')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.enableContextAwareness)
				.onChange(async (value) => {
					this.plugin.settings.enableContextAwareness = value;
					await this.plugin.saveSettings();
				}));
	}

	private addReconnectButton(containerEl: HTMLElement): void {
		const buttonContainer = containerEl.createDiv({ cls: 'setting-item' });
		const button = buttonContainer.createEl('button', {
			text: 'Reconnect LLM',
			cls: 'mod-cta'
		});
		
		button.addEventListener('click', async () => {
			try {
				button.disabled = true;
				button.textContent = 'Connecting...';
				
				this.plugin.aiService = new AIService(this.plugin.settings);
				
				new Notice('LLM connection refreshed successfully');
			} catch (error: any) {
				new Notice(`Failed to reconnect: ${error.message}`);
				console.error('Reconnect Error:', error);
			} finally {
				button.disabled = false;
				button.textContent = 'Reconnect LLM';
			}
		});
		
		const desc = buttonContainer.createDiv({ cls: 'setting-item-description' });
		desc.textContent = 'Reinitialize LLM connection (useful after changing provider or API key)';
	}

	private addTestConnectionButton(containerEl: HTMLElement): void {
		const buttonContainer = containerEl.createDiv({ cls: 'setting-item' });
		const button = buttonContainer.createEl('button', {
			text: 'Test Connection',
			cls: 'mod-cta'
		});
		
		button.addEventListener('click', async () => {
			try {
				button.disabled = true;
				button.textContent = 'Testing...';
				
				const result = await this.plugin.aiService.testConnection();
				
				if (result.success) {
					new Notice(`Connection successful! Response time: ${result.responseTime}ms`);
				} else {
					new Notice(`Connection failed: ${result.message}`, 5000);
				}
			} catch (error: any) {
				new Notice(`Test failed: ${error.message}`, 5000);
				console.error('Test Connection Error:', error);
			} finally {
				button.disabled = false;
				button.textContent = 'Test Connection';
			}
		});
		
		const desc = buttonContainer.createDiv({ cls: 'setting-item-description' });
		desc.textContent = 'Verify your API configuration is working correctly';
	}

	private showError(key: string, settingEl: HTMLElement, message: string): void {
		let errorEl = this.errorElements.get(key);
		
		if (!errorEl) {
			errorEl = settingEl.createDiv({ cls: 'setting-error' });
			errorEl.style.color = 'var(--text-error)';
			errorEl.style.fontSize = 'var(--font-smaller)';
			errorEl.style.marginTop = '0.5rem';
			this.errorElements.set(key, errorEl);
		}
		
		errorEl.textContent = message;
	}

	private clearError(key: string, settingEl: HTMLElement): void {
		const errorEl = this.errorElements.get(key);
		if (errorEl) {
			errorEl.remove();
			this.errorElements.delete(key);
		}
	}

	private exportSettings(): void {
		const settingsToExport = {
			...this.plugin.settings,
			apiKey: this.plugin.settings.apiKey ? '***' : ''
		};

		const blob = new Blob([JSON.stringify(settingsToExport, null, 2)], {type: 'application/json'});
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `obsidian-agent-settings-${new Date().toISOString().split('T')[0]}.json`;
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
		URL.revokeObjectURL(url);

		new Notice('Settings exported successfully');
	}

	private async importSettings(): Promise<void> {
		const input = document.createElement('input');
		input.type = 'file';
		input.accept = 'application/json';
		input.onchange = async (e) => {
			const file = (e.target as HTMLInputElement).files?.[0];
			if (!file) return;

			try {
				const text = await file.text();
				const importedSettings = JSON.parse(text);

				const requiredKeys = ['apiProvider', 'model', 'temperature', 'maxTokens', 'systemPrompt', 'enableContextAwareness'];
				for (const key of requiredKeys) {
					if (!(key in importedSettings)) {
						new Notice('Invalid settings file: missing required fields', 3000);
						return;
					}
				}

				const confirmImport = confirm(
					'This will overwrite your current settings. Continue?'
				);

				if (!confirmImport) return;

				Object.assign(this.plugin.settings, importedSettings);
				
				if (importedSettings.apiKey === '***') {
					this.plugin.settings.apiKey = '';
				}

				await this.plugin.saveSettings();
				this.display();
				new Notice('Settings imported successfully');
			} catch (error: any) {
				new Notice(`Failed to import settings: ${error.message}`, 3000);
				console.error('Import Error:', error);
			}
		};

		document.body.appendChild(input);
		input.click();
		document.body.removeChild(input);
	}
}

class ProfileEditorModal extends Modal {
	private profile: AIProfile | null;
	private onSave: (profile: AIProfile) => void;
	private formData: AIProfile;

	constructor(app: App, profile: AIProfile | null, onSave: (profile: AIProfile) => void) {
		super(app);
		this.profile = profile;
		this.onSave = onSave;
		this.formData = profile ? { ...profile } : {
			id: generateProfileId(),
			name: '',
			apiProvider: 'openai',
			apiKey: '',
			customApiUrl: '',
			model: 'gpt-4',
			temperature: 0.7,
			maxTokens: 2000,
			systemPrompt: 'You are a helpful AI assistant integrated into Obsidian.'
		};
	}

	onOpen() {
		const { contentEl } = this;
		contentEl.createEl('h2', { text: this.profile ? 'Edit Profile' : 'Create Profile' });

		new Setting(contentEl)
			.setName('Profile Name')
			.addText(text => text
				.setPlaceholder('My Profile')
				.setValue(this.formData.name)
				.onChange(value => this.formData.name = value));

		new Setting(contentEl)
			.setName('API Provider')
			.addDropdown(dropdown => dropdown
				.addOption('openai', 'OpenAI')
				.addOption('anthropic', 'Anthropic')
				.addOption('ollama', 'Ollama (Local)')
				.addOption('custom', 'Custom API')
				.setValue(this.formData.apiProvider)
				.onChange((value: 'openai' | 'anthropic' | 'ollama' | 'custom') => {
					this.formData.apiProvider = value;
					if (value === 'ollama') {
						this.formData.customApiUrl = 'http://localhost:11434';
					}
				}));

		new Setting(contentEl)
			.setName('API Key')
			.setDesc('Leave empty for Ollama')
			.addText(text => text
				.setPlaceholder('sk-...')
				.setValue(this.formData.apiKey)
				.onChange(value => this.formData.apiKey = value));

		new Setting(contentEl)
			.setName('Custom API URL')
			.setDesc('Required for Custom/Ollama providers')
			.addText(text => text
				.setPlaceholder('http://localhost:11434')
				.setValue(this.formData.customApiUrl)
				.onChange(value => this.formData.customApiUrl = value));

		new Setting(contentEl)
			.setName('Model')
			.addText(text => text
				.setPlaceholder('gpt-4')
				.setValue(this.formData.model)
				.onChange(value => this.formData.model = value));

		new Setting(contentEl)
			.setName('Temperature')
			.addSlider(slider => slider
				.setLimits(0, 1, 0.1)
				.setValue(this.formData.temperature)
				.setDynamicTooltip()
				.onChange(value => this.formData.temperature = value));

		new Setting(contentEl)
			.setName('Max Tokens')
			.addText(text => text
				.setPlaceholder('2000')
				.setValue(String(this.formData.maxTokens))
				.onChange(value => {
					const parsed = parseInt(value);
					this.formData.maxTokens = isNaN(parsed) ? 2000 : parsed;
				}));

		new Setting(contentEl)
			.setName('System Prompt')
			.addTextArea(text => text
				.setPlaceholder('You are a helpful assistant...')
				.setValue(this.formData.systemPrompt)
				.onChange(value => this.formData.systemPrompt = value));

		const buttonContainer = contentEl.createDiv({ cls: 'button-container' });
		buttonContainer.style.display = 'flex';
		buttonContainer.style.justifyContent = 'flex-end';
		buttonContainer.style.gap = '0.5rem';
		buttonContainer.style.marginTop = '1rem';

		const cancelButton = buttonContainer.createEl('button', { text: 'Cancel' });
		cancelButton.addEventListener('click', () => this.close());

		const saveButton = buttonContainer.createEl('button', { text: 'Save', cls: 'mod-cta' });
		saveButton.addEventListener('click', () => {
			if (!this.formData.name.trim()) {
				new Notice('Profile name is required');
				return;
			}
			this.onSave(this.formData);
			this.close();
		});
	}

	onClose() {
		const { contentEl } = this;
		contentEl.empty();
	}
}

class TemplateEditorModal extends Modal {
	private template: PromptTemplate | null;
	private onSave: (template: PromptTemplate) => void;
	private formData: PromptTemplate;

	constructor(app: App, template: PromptTemplate | null, onSave: (template: PromptTemplate) => void) {
		super(app);
		this.template = template;
		this.onSave = onSave;
		this.formData = template ? { ...template } : {
			id: generateTemplateId(),
			name: '',
			description: '',
			category: 'Custom',
			prompt: '',
			variables: [],
			isBuiltIn: false
		};
	}

	onOpen() {
		const { contentEl } = this;
		contentEl.createEl('h2', { text: this.template ? 'Edit Template' : 'Create Template' });

		new Setting(contentEl)
			.setName('Template Name')
			.addText(text => text
				.setPlaceholder('My Template')
				.setValue(this.formData.name)
				.onChange(value => this.formData.name = value));

		new Setting(contentEl)
			.setName('Description')
			.addText(text => text
				.setPlaceholder('What this template does')
				.setValue(this.formData.description)
				.onChange(value => this.formData.description = value));

		new Setting(contentEl)
			.setName('Category')
			.addDropdown(dropdown => dropdown
				.addOption('Writing', 'Writing')
				.addOption('Research', 'Research')
				.addOption('Note-taking', 'Note-taking')
				.addOption('Coding', 'Coding')
				.addOption('Creative', 'Creative')
				.addOption('Custom', 'Custom')
				.setValue(this.formData.category)
				.onChange(value => this.formData.category = value));

		const promptSetting = new Setting(contentEl)
			.setName('Prompt Template')
			.setDesc('Use {text}, {topic}, {code}, etc. as placeholders');
		
		const promptTextArea = contentEl.createEl('textarea');
		promptTextArea.style.width = '100%';
		promptTextArea.style.minHeight = '150px';
		promptTextArea.style.marginBottom = '1rem';
		promptTextArea.style.padding = '0.5rem';
		promptTextArea.style.borderRadius = 'var(--radius-s)';
		promptTextArea.style.border = '1px solid var(--background-modifier-border)';
		promptTextArea.style.fontFamily = 'var(--font-monospace)';
		promptTextArea.placeholder = 'Please summarize the following:\n\n{text}';
		promptTextArea.value = this.formData.prompt;
		promptTextArea.addEventListener('input', (e) => {
			this.formData.prompt = (e.target as HTMLTextAreaElement).value;
		});

		const buttonContainer = contentEl.createDiv({ cls: 'button-container' });
		buttonContainer.style.display = 'flex';
		buttonContainer.style.justifyContent = 'flex-end';
		buttonContainer.style.gap = '0.5rem';

		const cancelButton = buttonContainer.createEl('button', { text: 'Cancel' });
		cancelButton.addEventListener('click', () => this.close());

		const saveButton = buttonContainer.createEl('button', { text: 'Save', cls: 'mod-cta' });
		saveButton.addEventListener('click', () => {
			if (!this.formData.name.trim()) {
				new Notice('Template name is required');
				return;
			}
			if (!this.formData.prompt.trim()) {
				new Notice('Prompt template is required');
				return;
			}
			this.onSave(this.formData);
			this.close();
		});
	}

	onClose() {
		const { contentEl } = this;
		contentEl.empty();
	}
}
