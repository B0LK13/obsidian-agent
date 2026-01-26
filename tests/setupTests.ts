import { vi } from 'vitest';

vi.mock('obsidian', () => ({
	Editor: class {},
	App: class {},
	TFile: class {},
	Notice: class {
		constructor(public message: string) {}
	},
	Modal: class {
		constructor(public app: any) {}
		open() {}
		close() {}
	},
	PluginSettingTab: class {
		constructor(public app: any, public plugin: any) {}
	},
	Setting: class {
		constructor(public container: HTMLElement) {}
	}
}));
