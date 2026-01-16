import { App, PluginSettingTab, Setting } from 'obsidian';
import ObsidianAgentPlugin from './main';

export class ObsidianAgentSettingTab extends PluginSettingTab {
	plugin: ObsidianAgentPlugin;

	constructor(app: App, plugin: ObsidianAgentPlugin) {
		super(app, plugin);
		this.plugin = plugin;
	}

	display(): void {
		const {containerEl} = this;

		containerEl.empty();

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
					this.display(); // Refresh to show/hide custom URL field
				}));

		new Setting(containerEl)
			.setName('API Key')
			.setDesc('Enter your API key for the selected provider')
			.addText(text => text
				.setPlaceholder('Enter your API key')
				.setValue(this.plugin.settings.apiKey)
				.onChange(async (value) => {
					this.plugin.settings.apiKey = value;
					await this.plugin.saveSettings();
				}));

		if (this.plugin.settings.apiProvider === 'custom') {
			new Setting(containerEl)
				.setName('Custom API URL')
				.setDesc('Enter the URL for your custom API endpoint')
				.addText(text => text
					.setPlaceholder('https://api.example.com/v1/chat')
					.setValue(this.plugin.settings.customApiUrl)
					.onChange(async (value) => {
						this.plugin.settings.customApiUrl = value;
						await this.plugin.saveSettings();
					}));
		}

		new Setting(containerEl)
			.setName('Model')
			.setDesc('AI model to use')
			.addText(text => text
				.setPlaceholder('gpt-4')
				.setValue(this.plugin.settings.model)
				.onChange(async (value) => {
					this.plugin.settings.model = value;
					await this.plugin.saveSettings();
				}));

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

		new Setting(containerEl)
			.setName('Max Tokens')
			.setDesc('Maximum number of tokens to generate')
			.addText(text => text
				.setPlaceholder('2000')
				.setValue(String(this.plugin.settings.maxTokens))
				.onChange(async (value) => {
					this.plugin.settings.maxTokens = parseInt(value) || 2000;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('System Prompt')
			.setDesc('The system prompt that defines the AI assistant behavior')
			.addTextArea(text => text
				.setPlaceholder('You are a helpful assistant...')
				.setValue(this.plugin.settings.systemPrompt)
				.onChange(async (value) => {
					this.plugin.settings.systemPrompt = value;
					await this.plugin.saveSettings();
				}));

		new Setting(containerEl)
			.setName('Enable Context Awareness')
			.setDesc('Allow the agent to access current note context')
			.addToggle(toggle => toggle
				.setValue(this.plugin.settings.enableContextAwareness)
				.onChange(async (value) => {
					this.plugin.settings.enableContextAwareness = value;
					await this.plugin.saveSettings();
				}));
	}
}
