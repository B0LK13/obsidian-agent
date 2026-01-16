import { App, Modal, Notice, TextAreaComponent } from 'obsidian';
import { AIService } from './aiService';

export class AgentModal extends Modal {
	private aiService: AIService;
	private onSubmit: (result: string) => void;
	private prompt: string = '';
	private context: string = '';

	constructor(app: App, aiService: AIService, context: string, onSubmit: (result: string) => void) {
		super(app);
		this.aiService = aiService;
		this.context = context;
		this.onSubmit = onSubmit;
	}

	onOpen() {
		const {contentEl} = this;

		contentEl.createEl('h2', {text: 'AI Agent Assistant'});

		contentEl.createEl('p', {
			text: 'Enter your prompt below. The agent will use the current note as context.',
			cls: 'setting-item-description'
		});

		const promptContainer = contentEl.createDiv('prompt-container');
		
		const textArea = new TextAreaComponent(promptContainer);
		textArea.inputEl.style.width = '100%';
		textArea.inputEl.style.minHeight = '100px';
		textArea.inputEl.placeholder = 'What would you like the AI to help with?';
		textArea.onChange((value) => {
			this.prompt = value;
		});

		const buttonContainer = contentEl.createDiv('button-container');
		buttonContainer.style.marginTop = '1rem';
		buttonContainer.style.display = 'flex';
		buttonContainer.style.justifyContent = 'flex-end';
		buttonContainer.style.gap = '0.5rem';

		const cancelButton = buttonContainer.createEl('button', {text: 'Cancel'});
		cancelButton.addEventListener('click', () => {
			this.close();
		});

		const submitButton = buttonContainer.createEl('button', {
			text: 'Generate',
			cls: 'mod-cta'
		});
		submitButton.addEventListener('click', async () => {
			if (!this.prompt.trim()) {
				new Notice('Please enter a prompt');
				return;
			}

			submitButton.disabled = true;
			submitButton.textContent = 'Generating...';

			try {
				const result = await this.aiService.generateCompletion(this.prompt, this.context);
				this.onSubmit(result);
				this.close();
			} catch (error) {
				new Notice(`Error: ${error.message}`);
				console.error('Agent Modal Error:', error);
			} finally {
				submitButton.disabled = false;
				submitButton.textContent = 'Generate';
			}
		});

		// Focus on text area
		textArea.inputEl.focus();
	}

	onClose() {
		const {contentEl} = this;
		contentEl.empty();
	}
}
