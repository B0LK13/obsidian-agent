import { Notice } from 'obsidian';
import AIChatNotesPlugin from '../../main';

export interface HandwritingStroke {
	points: { x: number; y: number; pressure?: number }[];
	color: string;
	width: number;
}

export interface HandwritingCanvas {
	id: string;
	strokes: HandwritingStroke[];
	width: number;
	height: number;
	backgroundColor: string;
	timestamp: number;
}

export class HandwritingService {
	plugin: AIChatNotesPlugin;
	currentCanvas: HandwritingCanvas | null = null;
	isDrawing: boolean = false;
	currentStroke: HandwritingStroke | null = null;
	canvasElement: HTMLCanvasElement | null = null;
	ctx: CanvasRenderingContext2D | null = null;

	// Default settings
	strokeColor: string = '#1a1a1a';
	strokeWidth: number = 3;
	eraserMode: boolean = false;

	constructor(plugin: AIChatNotesPlugin) {
		this.plugin = plugin;
	}

	initializeCanvas(canvas: HTMLCanvasElement, width: number = 800, height: number = 600): HandwritingCanvas {
		this.canvasElement = canvas;
		canvas.width = width;
		canvas.height = height;

		const ctx = canvas.getContext('2d');
		if (!ctx) {
			throw new Error('Could not get canvas context');
		}
		this.ctx = ctx;

		// Set up canvas defaults
		ctx.lineCap = 'round';
		ctx.lineJoin = 'round';
		ctx.fillStyle = '#ffffff';
		ctx.fillRect(0, 0, width, height);

		this.currentCanvas = {
			id: crypto.randomUUID(),
			strokes: [],
			width,
			height,
			backgroundColor: '#ffffff',
			timestamp: Date.now()
		};

		this.attachEventListeners(canvas);
		return this.currentCanvas;
	}

	private attachEventListeners(canvas: HTMLCanvasElement) {
		// Mouse events
		canvas.addEventListener('mousedown', this.handleStart.bind(this));
		canvas.addEventListener('mousemove', this.handleMove.bind(this));
		canvas.addEventListener('mouseup', this.handleEnd.bind(this));
		canvas.addEventListener('mouseout', this.handleEnd.bind(this));

		// Touch events
		canvas.addEventListener('touchstart', (e) => {
			e.preventDefault();
			const touch = e.touches[0];
			const mouseEvent = new MouseEvent('mousedown', {
				clientX: touch.clientX,
				clientY: touch.clientY
			});
			canvas.dispatchEvent(mouseEvent);
		});

		canvas.addEventListener('touchmove', (e) => {
			e.preventDefault();
			const touch = e.touches[0];
			const mouseEvent = new MouseEvent('mousemove', {
				clientX: touch.clientX,
				clientY: touch.clientY
			});
			canvas.dispatchEvent(mouseEvent);
		});

		canvas.addEventListener('touchend', (e) => {
			e.preventDefault();
			const mouseEvent = new MouseEvent('mouseup', {});
			canvas.dispatchEvent(mouseEvent);
		});
	}

	private handleStart(e: MouseEvent) {
		if (!this.canvasElement || !this.ctx) return;

		this.isDrawing = true;
		const rect = this.canvasElement.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const y = e.clientY - rect.top;

		this.currentStroke = {
			points: [{ x, y }],
			color: this.eraserMode ? this.currentCanvas?.backgroundColor || '#ffffff' : this.strokeColor,
			width: this.eraserMode ? this.strokeWidth * 5 : this.strokeWidth
		};

		this.ctx.beginPath();
		this.ctx.moveTo(x, y);
		this.ctx.strokeStyle = this.currentStroke.color;
		this.ctx.lineWidth = this.currentStroke.width;
	}

	private handleMove(e: MouseEvent) {
		if (!this.isDrawing || !this.canvasElement || !this.ctx || !this.currentStroke) return;

		const rect = this.canvasElement.getBoundingClientRect();
		const x = e.clientX - rect.left;
		const y = e.clientY - rect.top;

		this.currentStroke.points.push({ x, y });

		this.ctx.lineTo(x, y);
		this.ctx.stroke();
	}

	private handleEnd() {
		if (!this.isDrawing || !this.currentStroke) return;

		this.isDrawing = false;
		this.currentCanvas?.strokes.push(this.currentStroke);
		this.currentStroke = null;
	}

	setStrokeColor(color: string) {
		this.strokeColor = color;
		this.eraserMode = false;
	}

	setStrokeWidth(width: number) {
		this.strokeWidth = width;
	}

	toggleEraser() {
		this.eraserMode = !this.eraserMode;
		return this.eraserMode;
	}

	undo() {
		if (!this.currentCanvas || this.currentCanvas.strokes.length === 0 || !this.ctx || !this.canvasElement) {
			new Notice('Nothing to undo');
			return;
		}

		this.currentCanvas.strokes.pop();
		this.redrawCanvas();
		new Notice('Undo successful');
	}

	clear() {
		if (!this.ctx || !this.canvasElement || !this.currentCanvas) return;

		this.ctx.fillStyle = this.currentCanvas.backgroundColor;
		this.ctx.fillRect(0, 0, this.canvasElement.width, this.canvasElement.height);
		this.currentCanvas.strokes = [];
		new Notice('Canvas cleared');
	}

	private redrawCanvas() {
		if (!this.ctx || !this.canvasElement || !this.currentCanvas) return;

		// Clear canvas
		this.ctx.fillStyle = this.currentCanvas.backgroundColor;
		this.ctx.fillRect(0, 0, this.canvasElement.width, this.canvasElement.height);

		// Redraw all strokes
		this.currentCanvas.strokes.forEach(stroke => {
			if (stroke.points.length < 2) return;

			this.ctx!.beginPath();
			this.ctx!.strokeStyle = stroke.color;
			this.ctx!.lineWidth = stroke.width;
			this.ctx!.moveTo(stroke.points[0].x, stroke.points[0].y);

			for (let i = 1; i < stroke.points.length; i++) {
				this.ctx!.lineTo(stroke.points[i].x, stroke.points[i].y);
			}

			this.ctx!.stroke();
		});
	}

	async convertToImage(): Promise<string> {
		if (!this.canvasElement) {
			throw new Error('Canvas not initialized');
		}

		return this.canvasElement.toDataURL('image/png');
	}

	async convertToNote(filename?: string): Promise<string> {
		const imageData = await this.convertToImage();
		const timestamp = new Date().toISOString();
		const title = filename || `Handwriting-${Date.now()}`;

		let content = `# ${title}\n\n`;
		content += `*Created: ${timestamp}*\n\n`;
		content += `## Handwriting Canvas\n\n`;
		content += `![Handwriting](${imageData})\n\n`;

		// Try to OCR if possible (placeholder for future implementation)
		content += `## Transcription\n\n`;
		content += `*[OCR transcription would appear here - feature coming soon]*\n`;

		return content;
	}

	downloadAsImage(filename?: string) {
		if (!this.canvasElement) return;

		const link = document.createElement('a');
		link.download = filename || `handwriting-${Date.now()}.png`;
		link.href = this.canvasElement.toDataURL('image/png');
		link.click();
	}

	exportStrokes(): string {
		if (!this.currentCanvas) return '';
		return JSON.stringify(this.currentCanvas, null, 2);
	}

	importStrokes(json: string): boolean {
		try {
			const canvas: HandwritingCanvas = JSON.parse(json);
			this.currentCanvas = canvas;
			this.redrawCanvas();
			new Notice('Handwriting imported successfully');
			return true;
		} catch (error) {
			new Notice('Failed to import handwriting');
			return false;
		}
	}

	getPresetColors(): string[] {
		return [
			'#1a1a1a', // Black
			'#dc2626', // Red
			'#16a34a', // Green
			'#2563eb', // Blue
			'#9333ea', // Purple
			'#ea580c', // Orange
			'#0891b2', // Cyan
			'#db2777'  // Pink
		];
	}
}
