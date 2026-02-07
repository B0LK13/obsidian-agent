import { ItemView, WorkspaceLeaf, Notice } from 'obsidian';
import AIChatNotesPlugin from '../../main';

export const VIEW_TYPE_HANDWRITING = 'handwriting-view';

export class HandwritingView extends ItemView {
	plugin: AIChatNotesPlugin;
	canvas: HTMLCanvasElement | null = null;

	constructor(leaf: WorkspaceLeaf, plugin: AIChatNotesPlugin) {
		super(leaf);
		this.plugin = plugin;
	}

	getViewType() {
		return VIEW_TYPE_HANDWRITING;
	}

	getDisplayText() {
		return 'Handwriting Canvas';
	}

	getIcon() {
		return 'pen-tool';
	}

	async onOpen() {
		const { containerEl } = this;
		containerEl.empty();
		containerEl.addClass('handwriting-view');

		// Header
		const header = containerEl.createDiv({ cls: 'handwriting-header' });
		header.createEl('h3', { text: '📝 Handwriting Canvas' });

		// Toolbar
		const toolbar = containerEl.createDiv({ cls: 'handwriting-toolbar' });
		
		// Color picker
		const colors = this.plugin.api.handwriting.getPresetColors();
		const colorContainer = toolbar.createDiv({ cls: 'toolbar-group' });
		colorContainer.createEl('span', { text: 'Color:', cls: 'toolbar-label' });
		
		colors.forEach(color => {
			const colorBtn = colorContainer.createEl('button', {
				cls: 'color-btn',
				attr: { style: `background-color: ${color}` }
			});
			colorBtn.addEventListener('click', () => {
				this.plugin.api.handwriting.setStrokeColor(color);
				this.updateActiveColor(colorBtn);
			});
		});

		// Brush size
		const sizeContainer = toolbar.createDiv({ cls: 'toolbar-group' });
		sizeContainer.createEl('span', { text: 'Size:', cls: 'toolbar-label' });
		const sizeSlider = sizeContainer.createEl('input', {
			type: 'range',
			cls: 'brush-size-slider',
			attr: { min: '1', max: '20', value: '3' }
		});
		sizeSlider.addEventListener('input', (e) => {
			const size = parseInt((e.target as HTMLInputElement).value);
			this.plugin.api.handwriting.setStrokeWidth(size);
		});

		// Tools
		const toolsContainer = toolbar.createDiv({ cls: 'toolbar-group' });
		
		const eraserBtn = toolsContainer.createEl('button', {
			cls: 'tool-btn',
			text: '🧹 Eraser'
		});
		eraserBtn.addEventListener('click', () => {
			const isEraser = this.plugin.api.handwriting.toggleEraser();
			eraserBtn.toggleClass('active', isEraser);
		});

		const undoBtn = toolsContainer.createEl('button', {
			cls: 'tool-btn',
			text: '↩️ Undo'
		});
		undoBtn.addEventListener('click', () => {
			this.plugin.api.handwriting.undo();
		});

		const clearBtn = toolsContainer.createEl('button', {
			cls: 'tool-btn danger',
			text: '🗑️ Clear'
		});
		clearBtn.addEventListener('click', () => {
			if (confirm('Clear the canvas?')) {
				this.plugin.api.handwriting.clear();
			}
		});

		// Canvas container
		const canvasContainer = containerEl.createDiv({ cls: 'canvas-container' });
		this.canvas = canvasContainer.createEl('canvas', {
			cls: 'handwriting-canvas'
		});

		// Initialize canvas
		const containerWidth = canvasContainer.clientWidth || 800;
		const containerHeight = canvasContainer.clientHeight || 600;
		this.plugin.api.handwriting.initializeCanvas(this.canvas, containerWidth - 40, containerHeight - 40);

		// Footer actions
		const footer = containerEl.createDiv({ cls: 'handwriting-footer' });
		
		const saveBtn = footer.createEl('button', {
			cls: 'action-btn primary',
			text: '💾 Save as Note'
		});
		saveBtn.addEventListener('click', () => this.saveAsNote());

		const downloadBtn = footer.createEl('button', {
			cls: 'action-btn',
			text: '📥 Download Image'
		});
		downloadBtn.addEventListener('click', () => {
			this.plugin.api.handwriting.downloadAsImage();
		});

		const exportBtn = footer.createEl('button', {
			cls: 'action-btn',
			text: '📤 Export Strokes'
		});
		exportBtn.addEventListener('click', () => this.exportStrokes());
	}

	private updateActiveColor(activeBtn: HTMLElement) {
		const container = this.containerEl.querySelector('.toolbar-group');
		container?.querySelectorAll('.color-btn').forEach(btn => {
			btn.removeClass('active');
		});
		activeBtn.addClass('active');
	}

	private async saveAsNote() {
		try {
			const content = await this.plugin.api.handwriting.convertToNote();
			const timestamp = Date.now();
			const fileName = `Handwriting-${timestamp}`;
			const filePath = `AI-Chat/${fileName}.md`;

			// Ensure folder exists
			const folder = this.app.vault.getAbstractFileByPath('AI-Chat');
			if (!folder) {
				await this.app.vault.createFolder('AI-Chat');
			}

			await this.app.vault.create(filePath, content);
			new Notice(`Saved to ${filePath}`);
		} catch (error) {
			console.error('Failed to save note:', error);
			new Notice('Failed to save note');
		}
	}

	private exportStrokes() {
		const json = this.plugin.api.handwriting.exportStrokes();
		if (json) {
			const blob = new Blob([json], { type: 'application/json' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `handwriting-strokes-${Date.now()}.json`;
			a.click();
			URL.revokeObjectURL(url);
			new Notice('Strokes exported');
		}
	}

	async onClose() {
		// Cleanup if needed
	}
}
