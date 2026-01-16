import { App, PluginSettingTab, Setting, Notice } from 'obsidian';
import ObsidianAgentPlugin from './main';
import { AIService } from './aiService';

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

	display(): void {
		const {containerEl} = this;

		containerEl.empty();
		this.errorElements.clear();

		containerEl.createEl('h2', {text: 'Obsidian Agent Settings'});

		this.addSettingsActions(containerEl);

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
		this.addConversationPersistenceSetting(containerEl);
		this.addTokenTrackingSetting(containerEl);
		this.addReconnectButton(containerEl);
		this.addTestConnectionButton(containerEl);
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
