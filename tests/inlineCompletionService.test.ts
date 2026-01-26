import { describe, it, expect, vi } from 'vitest';
import { InlineCompletionService } from '../inlineCompletionService';
import { DEFAULT_SETTINGS } from '../settings';
import type { AIService } from '../aiService';

vi.mock('obsidian', () => ({
	Editor: class {}
}));

describe('InlineCompletionService', () => {
	it('inserts completions at the cursor without wiping the entire line', async () => {
		const settings = JSON.parse(JSON.stringify(DEFAULT_SETTINGS));
		const mockAi = { generateCompletion: vi.fn() } as unknown as AIService;
		const service = new InlineCompletionService(settings, mockAi);

		const replaceRange = vi.fn();
		const setCursor = vi.fn();
		const editor = {
			getCursor: () => ({ line: 0, ch: 5 }),
			getLine: () => 'Hello',
			replaceRange,
			setCursor
		} as any;

		(service as any).editor = editor;

		await (service as any).applyCompletion({
			id: 'test',
			text: ' world',
			displayText: ' world',
			type: 'continue',
			confidence: 1
		});

		expect(replaceRange).toHaveBeenCalledWith(' world', { line: 0, ch: 5 });
		expect(setCursor).toHaveBeenCalledWith({ line: 0, ch: 11 });
	});
});
