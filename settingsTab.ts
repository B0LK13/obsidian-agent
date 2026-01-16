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

	display(): void {
		const {containerEl} = this;

		containerEl.empty();
		this.errorElements.clear();

		containerEl.createEl('h2', {text: 'Obsidian Agent Settings'});

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
		this.addReconnectButton(containerEl);
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
}
