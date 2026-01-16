export interface PromptTemplate {
	id: string;
	name: string;
	description: string;
	category: string;
	prompt: string;
	variables?: string[];
	isBuiltIn: boolean;
}

export const BUILT_IN_TEMPLATES: PromptTemplate[] = [
	// Writing category
	{
		id: 'summarize',
		name: 'Summarize',
		description: 'Create a concise summary of the text',
		category: 'Writing',
		prompt: 'Please provide a concise summary of the following text, capturing the main points and key takeaways:\n\n{text}',
		variables: ['text'],
		isBuiltIn: true
	},
	{
		id: 'expand',
		name: 'Expand Ideas',
		description: 'Elaborate on ideas with more detail',
		category: 'Writing',
		prompt: 'Please expand on the following ideas with more detail, examples, and context:\n\n{text}',
		variables: ['text'],
		isBuiltIn: true
	},
	{
		id: 'rewrite-formal',
		name: 'Rewrite (Formal)',
		description: 'Rewrite text in a more formal tone',
		category: 'Writing',
		prompt: 'Please rewrite the following text in a more formal, professional tone while preserving the original meaning:\n\n{text}',
		variables: ['text'],
		isBuiltIn: true
	},
	{
		id: 'rewrite-casual',
		name: 'Rewrite (Casual)',
		description: 'Rewrite text in a more casual tone',
		category: 'Writing',
		prompt: 'Please rewrite the following text in a more casual, conversational tone while preserving the original meaning:\n\n{text}',
		variables: ['text'],
		isBuiltIn: true
	},
	{
		id: 'proofread',
		name: 'Proofread',
		description: 'Check for grammar, spelling, and style',
		category: 'Writing',
		prompt: 'Please proofread the following text for grammar, spelling, punctuation, and style issues. Provide the corrected version and list the changes made:\n\n{text}',
		variables: ['text'],
		isBuiltIn: true
	},
	{
		id: 'shorten',
		name: 'Make Concise',
		description: 'Shorten text while keeping key points',
		category: 'Writing',
		prompt: 'Please make the following text more concise while preserving all key information and meaning:\n\n{text}',
		variables: ['text'],
		isBuiltIn: true
	},

	// Research category
	{
		id: 'explain',
		name: 'Explain Simply',
		description: 'Explain a topic in simple terms',
		category: 'Research',
		prompt: 'Please explain the following topic in simple terms that anyone can understand. Use analogies and examples where helpful:\n\n{topic}',
		variables: ['topic'],
		isBuiltIn: true
	},
	{
		id: 'compare',
		name: 'Compare & Contrast',
		description: 'Compare two or more items',
		category: 'Research',
		prompt: 'Please compare and contrast the following items, highlighting their similarities, differences, advantages, and disadvantages:\n\n{items}',
		variables: ['items'],
		isBuiltIn: true
	},
	{
		id: 'analyze',
		name: 'Analyze',
		description: 'Provide in-depth analysis',
		category: 'Research',
		prompt: 'Please provide an in-depth analysis of the following, including key insights, implications, and considerations:\n\n{subject}',
		variables: ['subject'],
		isBuiltIn: true
	},
	{
		id: 'pros-cons',
		name: 'Pros & Cons',
		description: 'List advantages and disadvantages',
		category: 'Research',
		prompt: 'Please list the pros and cons of the following, with explanations for each point:\n\n{subject}',
		variables: ['subject'],
		isBuiltIn: true
	},

	// Note-taking category
	{
		id: 'key-points',
		name: 'Extract Key Points',
		description: 'Extract main points as bullet points',
		category: 'Note-taking',
		prompt: 'Please extract the key points from the following text as a bulleted list:\n\n{text}',
		variables: ['text'],
		isBuiltIn: true
	},
	{
		id: 'questions',
		name: 'Generate Questions',
		description: 'Create thought-provoking questions',
		category: 'Note-taking',
		prompt: 'Please generate thought-provoking questions about the following topic that would help deepen understanding:\n\n{topic}',
		variables: ['topic'],
		isBuiltIn: true
	},
	{
		id: 'outline',
		name: 'Create Outline',
		description: 'Generate a structured outline',
		category: 'Note-taking',
		prompt: 'Please create a detailed, structured outline for the following topic:\n\n{topic}',
		variables: ['topic'],
		isBuiltIn: true
	},
	{
		id: 'flashcards',
		name: 'Create Flashcards',
		description: 'Generate Q&A flashcards for studying',
		category: 'Note-taking',
		prompt: 'Please create flashcards (question and answer pairs) from the following content for studying:\n\n{content}',
		variables: ['content'],
		isBuiltIn: true
	},
	{
		id: 'action-items',
		name: 'Extract Action Items',
		description: 'Find and list action items/todos',
		category: 'Note-taking',
		prompt: 'Please extract all action items, tasks, and todos from the following text:\n\n{text}',
		variables: ['text'],
		isBuiltIn: true
	},

	// Coding category
	{
		id: 'explain-code',
		name: 'Explain Code',
		description: 'Explain what code does',
		category: 'Coding',
		prompt: 'Please explain what the following code does, including its purpose, how it works, and any notable patterns or techniques used:\n\n```\n{code}\n```',
		variables: ['code'],
		isBuiltIn: true
	},
	{
		id: 'debug',
		name: 'Debug Code',
		description: 'Find potential bugs and issues',
		category: 'Coding',
		prompt: 'Please analyze the following code for potential bugs, issues, edge cases, and improvements:\n\n```\n{code}\n```',
		variables: ['code'],
		isBuiltIn: true
	},
	{
		id: 'refactor',
		name: 'Refactor Code',
		description: 'Suggest code improvements',
		category: 'Coding',
		prompt: 'Please suggest improvements and refactoring for the following code to make it cleaner, more efficient, or more maintainable:\n\n```\n{code}\n```',
		variables: ['code'],
		isBuiltIn: true
	},
	{
		id: 'document-code',
		name: 'Document Code',
		description: 'Add documentation and comments',
		category: 'Coding',
		prompt: 'Please add comprehensive documentation and comments to the following code:\n\n```\n{code}\n```',
		variables: ['code'],
		isBuiltIn: true
	},

	// Creative category
	{
		id: 'brainstorm',
		name: 'Brainstorm Ideas',
		description: 'Generate creative ideas',
		category: 'Creative',
		prompt: 'Please brainstorm creative ideas related to the following topic. Think outside the box and provide diverse suggestions:\n\n{topic}',
		variables: ['topic'],
		isBuiltIn: true
	},
	{
		id: 'write-intro',
		name: 'Write Introduction',
		description: 'Create an engaging introduction',
		category: 'Creative',
		prompt: 'Please write an engaging introduction for a piece about the following topic:\n\n{topic}',
		variables: ['topic'],
		isBuiltIn: true
	},
	{
		id: 'write-conclusion',
		name: 'Write Conclusion',
		description: 'Create a strong conclusion',
		category: 'Creative',
		prompt: 'Please write a strong, memorable conclusion for a piece about the following topic, summarizing key points:\n\n{topic}',
		variables: ['topic'],
		isBuiltIn: true
	}
];

export function getTemplateCategories(templates: PromptTemplate[]): string[] {
	const categories = new Set<string>();
	templates.forEach(t => categories.add(t.category));
	return Array.from(categories).sort();
}

export function filterTemplates(templates: PromptTemplate[], category?: string, search?: string): PromptTemplate[] {
	let filtered = templates;
	
	if (category && category !== 'All') {
		filtered = filtered.filter(t => t.category === category);
	}
	
	if (search) {
		const searchLower = search.toLowerCase();
		filtered = filtered.filter(t => 
			t.name.toLowerCase().includes(searchLower) ||
			t.description.toLowerCase().includes(searchLower) ||
			t.prompt.toLowerCase().includes(searchLower)
		);
	}
	
	return filtered;
}

export function applyTemplate(template: PromptTemplate, variables: Record<string, string>): string {
	let prompt = template.prompt;
	
	for (const [key, value] of Object.entries(variables)) {
		prompt = prompt.replace(new RegExp(`\\{${key}\\}`, 'g'), value);
	}
	
	return prompt;
}

export function generateTemplateId(): string {
	return `template_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}
