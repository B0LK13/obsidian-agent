import { CustomTemplate } from './settings';

export class TemplateManager {
	private templates: Map<string, CustomTemplate>;

	constructor(templates: CustomTemplate[] = []) {
		this.templates = new Map();
		templates.forEach(t => this.templates.set(t.id, t));
	}

	addTemplate(template: CustomTemplate): void {
		this.templates.set(template.id, template);
	}

	getTemplate(id: string): CustomTemplate | undefined {
		return this.templates.get(id);
	}

	getAllTemplates(): CustomTemplate[] {
		return Array.from(this.templates.values());
	}

	deleteTemplate(id: string): boolean {
		return this.templates.delete(id);
	}

	updateTemplate(id: string, updates: Partial<CustomTemplate>): void {
		const existing = this.templates.get(id);
		if (existing) {
			this.templates.set(id, { ...existing, ...updates });
		}
	}

	applyTemplate(templateId: string, variables: Record<string, string>): string {
		const template = this.templates.get(templateId);
		if (!template) {
			throw new Error(`Template ${templateId} not found`);
		}

		let result = template.prompt;
		for (const [key, value] of Object.entries(variables)) {
			result = result.replace(new RegExp(`{{${key}}}`, 'g'), value);
		}
		return result;
	}

	exportTemplates(): string {
		return JSON.stringify(this.getAllTemplates(), null, 2);
	}

	importTemplates(jsonData: string): void {
		try {
			const templates = JSON.parse(jsonData) as CustomTemplate[];
			templates.forEach(t => this.addTemplate(t));
		} catch (error) {
			throw new Error(`Failed to import templates: ${error.message}`);
		}
	}
}

export const DEFAULT_TEMPLATES: CustomTemplate[] = [
	{
		id: 'meeting-notes',
		name: 'Meeting Notes Formatter',
		description: 'Format raw meeting notes into structured format',
		prompt: 'Format the following meeting notes into a structured format with sections for attendees, agenda, discussion points, action items, and next steps:\n\n{{notes}}'
	},
	{
		id: 'code-explain',
		name: 'Explain Code',
		description: 'Explain what a code snippet does',
		prompt: 'Explain the following code in simple terms, including what it does and how it works:\n\n```\n{{code}}\n```'
	},
	{
		id: 'blog-post',
		name: 'Blog Post Generator',
		description: 'Generate a blog post from topic and key points',
		prompt: 'Write a comprehensive blog post about {{topic}}. Include an engaging introduction, main points covering {{keyPoints}}, and a strong conclusion. Target audience: {{audience}}'
	},
	{
		id: 'translate',
		name: 'Translate Text',
		description: 'Translate text to another language',
		prompt: 'Translate the following text to {{language}}. Maintain the original tone and meaning:\n\n{{text}}'
	},
	{
		id: 'brainstorm',
		name: 'Brainstorm Ideas',
		description: 'Generate creative ideas for a topic',
		prompt: 'Generate 10 creative and unique ideas for: {{topic}}. For each idea, provide a brief description and potential applications.'
	},
	{
		id: 'grammar-check',
		name: 'Grammar and Style Check',
		description: 'Check and improve grammar and style',
		prompt: 'Review the following text for grammar, spelling, punctuation, and style issues. Provide the corrected version and list the changes made:\n\n{{text}}'
	},
	{
		id: 'email-draft',
		name: 'Email Composer',
		description: 'Compose a professional email',
		prompt: 'Compose a professional email with the following details:\nRecipient: {{recipient}}\nSubject: {{subject}}\nKey points to cover: {{points}}\nTone: {{tone}}'
	},
	{
		id: 'study-notes',
		name: 'Study Notes Generator',
		description: 'Create study notes from content',
		prompt: 'Create comprehensive study notes from the following content. Include key concepts, important terms, and summary points:\n\n{{content}}'
	}
];
