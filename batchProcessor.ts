import { TFile, Vault } from 'obsidian';
import { AIService } from './aiService';

export interface BatchTask {
	file: TFile;
	operation: string;
	prompt: string;
	status: 'pending' | 'processing' | 'completed' | 'failed';
	result?: string;
	error?: string;
}

export class BatchProcessor {
	private vault: Vault;
	private aiService: AIService;
	private tasks: BatchTask[];
	private isProcessing: boolean;
	private delayMs: number;

	constructor(vault: Vault, aiService: AIService, delayMs: number = 1000) {
		this.vault = vault;
		this.aiService = aiService;
		this.tasks = [];
		this.isProcessing = false;
		this.delayMs = delayMs;
	}

	setDelay(delayMs: number): void {
		this.delayMs = delayMs;
	}

	addTask(task: BatchTask): void {
		this.tasks.push(task);
	}

	async processTasks(onProgress?: (current: number, total: number, task: BatchTask) => void): Promise<void> {
		if (this.isProcessing) {
			throw new Error('Batch processing already in progress');
		}

		this.isProcessing = true;
		const total = this.tasks.length;

		try {
			for (let i = 0; i < this.tasks.length; i++) {
				const task = this.tasks[i];
				task.status = 'processing';

				if (onProgress) {
					onProgress(i + 1, total, task);
				}

				try {
					const content = await this.vault.read(task.file);
					const result = await this.aiService.generateCompletion(
						task.prompt,
						content
					);

					task.result = result;
					task.status = 'completed';

					// Optionally update the file
					if (task.operation === 'append') {
						await this.vault.modify(task.file, content + '\n\n' + result);
					} else if (task.operation === 'replace') {
						await this.vault.modify(task.file, result);
					}
				} catch (error) {
					task.status = 'failed';
					task.error = error.message;
				}

				// Configurable delay to avoid rate limiting
				await new Promise(resolve => setTimeout(resolve, this.delayMs));
			}
		} finally {
			this.isProcessing = false;
		}
	}

	getTasks(): BatchTask[] {
		return this.tasks;
	}

	clearTasks(): void {
		this.tasks = [];
	}

	getStats(): {
		total: number;
		completed: number;
		failed: number;
		pending: number;
	} {
		return {
			total: this.tasks.length,
			completed: this.tasks.filter(t => t.status === 'completed').length,
			failed: this.tasks.filter(t => t.status === 'failed').length,
			pending: this.tasks.filter(t => t.status === 'pending').length
		};
	}
}
