import { ItemView, WorkspaceLeaf, Notice, TFile, Menu } from 'obsidian';
import AIChatNotesPlugin from '../../main';
import { GraphNode, GraphEdge } from '../services/KnowledgeGraphService';

export const VIEW_TYPE_KNOWLEDGE_GRAPH = 'knowledge-graph-view';

export class KnowledgeGraphView extends ItemView {
	plugin: AIChatNotesPlugin;
	canvas: HTMLCanvasElement | null = null;
	ctx: CanvasRenderingContext2D | null = null;
	animationId: number | null = null;
	
	// View state
	zoom: number = 1;
	panX: number = 0;
	panY: number = 0;
	isDragging: boolean = false;
	lastMouseX: number = 0;
	lastMouseY: number = 0;
	hoveredNode: GraphNode | null = null;
	selectedNode: GraphNode | null = null;
	
	// Filter state
	showNotes: boolean = true;
	showTags: boolean = true;
	showConcepts: boolean = true;
	minConnections: number = 0;

	constructor(leaf: WorkspaceLeaf, plugin: AIChatNotesPlugin) {
		super(leaf);
		this.plugin = plugin;
	}

	getViewType() {
		return VIEW_TYPE_KNOWLEDGE_GRAPH;
	}

	getDisplayText() {
		return 'Knowledge Graph';
	}

	getIcon() {
		return 'git-branch';
	}

	async onOpen() {
		const { containerEl } = this;
		containerEl.empty();
		containerEl.addClass('knowledge-graph-view');

		// Header with controls
		const header = containerEl.createDiv({ cls: 'graph-header' });
		header.createEl('h3', { text: '🕸️ Knowledge Graph' });

		// Toolbar
		const toolbar = containerEl.createDiv({ cls: 'graph-toolbar' });
		
		// Build graph button
		const buildBtn = toolbar.createEl('button', {
			cls: 'graph-btn primary',
			text: '🔄 Build Graph'
		});
		buildBtn.addEventListener('click', () => this.buildGraph());

		// Layout button
		const layoutBtn = toolbar.createEl('button', {
			cls: 'graph-btn',
			text: '📐 Auto Layout'
		});
		layoutBtn.addEventListener('click', () => this.autoLayout());

		// Filter controls
		const filterContainer = toolbar.createDiv({ cls: 'filter-container' });
		
		const notesToggle = this.createToggle(filterContainer, 'Notes', this.showNotes, (v) => {
			this.showNotes = v;
			this.render();
		});
		
		const tagsToggle = this.createToggle(filterContainer, 'Tags', this.showTags, (v) => {
			this.showTags = v;
			this.render();
		});
		
		const conceptsToggle = this.createToggle(filterContainer, 'Concepts', this.showConcepts, (v) => {
			this.showConcepts = v;
			this.render();
		});

		// Stats display
		const statsContainer = containerEl.createDiv({ cls: 'graph-stats' });
		statsContainer.id = 'graph-stats';

		// Canvas container
		const canvasContainer = containerEl.createDiv({ cls: 'graph-canvas-container' });
		this.canvas = canvasContainer.createEl('canvas', {
			cls: 'graph-canvas'
		});

		// Initialize canvas
		const rect = canvasContainer.getBoundingClientRect();
		this.canvas.width = rect.width || 800;
		this.canvas.height = rect.height || 600;
		
		this.ctx = this.canvas.getContext('2d');
		if (!this.ctx) {
			new Notice('Failed to initialize canvas');
			return;
		}

		// Set up interactions
		this.setupInteractions();

		// Initial build
		await this.buildGraph();
	}

	private createToggle(container: HTMLElement, label: string, initialValue: boolean, onChange: (value: boolean) => void): HTMLInputElement {
		const wrapper = container.createDiv({ cls: 'toggle-wrapper' });
		wrapper.createEl('span', { text: label, cls: 'toggle-label' });
		const checkbox = wrapper.createEl('input', {
			type: 'checkbox',
			cls: 'toggle-checkbox'
		});
		checkbox.checked = initialValue;
		checkbox.addEventListener('change', () => onChange(checkbox.checked));
		return checkbox;
	}

	private setupInteractions() {
		if (!this.canvas) return;

		// Mouse wheel for zoom
		this.canvas.addEventListener('wheel', (e) => {
			e.preventDefault();
			const delta = e.deltaY > 0 ? 0.9 : 1.1;
			this.zoom = Math.max(0.1, Math.min(5, this.zoom * delta));
			this.render();
		});

		// Mouse down for pan
		this.canvas.addEventListener('mousedown', (e) => {
			const rect = this.canvas!.getBoundingClientRect();
			const x = e.clientX - rect.left;
			const y = e.clientY - rect.top;

			// Check if clicked on a node
			const clickedNode = this.getNodeAt(x, y);
			if (clickedNode) {
				this.selectedNode = clickedNode;
				if (e.button === 2) { // Right click
					this.showNodeContextMenu(clickedNode, e.clientX, e.clientY);
				} else {
					this.openNode(clickedNode);
				}
				this.render();
				return;
			}

			this.isDragging = true;
			this.lastMouseX = e.clientX;
			this.lastMouseY = e.clientY;
		});

		// Mouse move for pan and hover
		this.canvas.addEventListener('mousemove', (e) => {
			const rect = this.canvas!.getBoundingClientRect();
			const x = e.clientX - rect.left;
			const y = e.clientY - rect.top;

			if (this.isDragging) {
				const dx = e.clientX - this.lastMouseX;
				const dy = e.clientY - this.lastMouseY;
				this.panX += dx;
				this.panY += dy;
				this.lastMouseX = e.clientX;
				this.lastMouseY = e.clientY;
				this.render();
			} else {
				// Check for hover
				const hovered = this.getNodeAt(x, y);
				if (hovered !== this.hoveredNode) {
					this.hoveredNode = hovered;
					this.canvas!.style.cursor = hovered ? 'pointer' : 'default';
					this.render();
				}
			}
		});

		// Mouse up
		window.addEventListener('mouseup', () => {
			this.isDragging = false;
		});

		// Context menu
		this.canvas.addEventListener('contextmenu', (e) => {
			e.preventDefault();
			this.showCanvasContextMenu(e.clientX, e.clientY);
		});
	}

	private getNodeAt(x: number, y: number): GraphNode | null {
		const graph = this.plugin.api.graph.graph;
		const clickRadius = 15;

		for (const node of graph.nodes) {
			if (!this.shouldShowNode(node)) continue;
			
			const screenX = (node.x || 0) * this.zoom + this.panX;
			const screenY = (node.y || 0) * this.zoom + this.panY;
			
			const dx = x - screenX;
			const dy = y - screenY;
			const distance = Math.sqrt(dx * dx + dy * dy);
			
			if (distance <= (node.size || 10) + clickRadius) {
				return node;
			}
		}
		return null;
	}

	private shouldShowNode(node: GraphNode): boolean {
		if (node.type === 'note' && !this.showNotes) return false;
		if (node.type === 'tag' && !this.showTags) return false;
		if (node.type === 'concept' && !this.showConcepts) return false;
		
		// Check minimum connections
		if (this.minConnections > 0) {
			const connectionCount = this.plugin.api.graph.graph.edges.filter(
				e => e.source === node.id || e.target === node.id
			).length;
			if (connectionCount < this.minConnections) return false;
		}
		
		return true;
	}

	private openNode(node: GraphNode) {
		if (node.type === 'note' && node.metadata?.path) {
			this.app.workspace.openLinkText(node.metadata.path, '', true);
		}
	}

	private showNodeContextMenu(node: GraphNode, x: number, y: number) {
		const menu = new Menu();
		
		menu.addItem((item) => {
			item.setTitle('Open Note');
			item.setIcon('file');
			item.onClick(() => this.openNode(node));
		});

		menu.addItem((item) => {
			item.setTitle('Find Connections');
			item.setIcon('link');
			item.onClick(() => this.highlightConnections(node));
		});

		menu.addItem((item) => {
			item.setTitle('Find Path From...');
			item.setIcon('git-commit');
			item.onClick(() => this.startPathFinding(node));
		});

		menu.showAtPosition({ x, y });
	}

	private showCanvasContextMenu(x: number, y: number) {
		const menu = new Menu();
		
		menu.addItem((item) => {
			item.setTitle('Reset View');
			item.setIcon('maximize');
			item.onClick(() => {
				this.zoom = 1;
				this.panX = 0;
				this.panY = 0;
				this.render();
			});
		});

		menu.addItem((item) => {
			item.setTitle('Export Graph');
			item.setIcon('download');
			item.onClick(() => this.exportGraph());
		});

		menu.showAtPosition({ x, y });
	}

	private highlightConnections(node: GraphNode) {
		const connected = this.plugin.api.graph.getConnectedNodes(node.id);
		new Notice(`Found ${connected.length} connected nodes`);
		// Could visually highlight these nodes
	}

	private startPathFinding(fromNode: GraphNode) {
		// Simple implementation - would need UI for selecting target
		new Notice('Select target node to find path...');
	}

	async buildGraph() {
		new Notice('Building knowledge graph...');
		await this.plugin.api.graph.buildGraph();
		await this.plugin.api.graph.calculateLayout(100);
		this.updateStats();
		this.render();
		new Notice('Graph built successfully!');
	}

	autoLayout() {
		this.plugin.api.graph.calculateLayout(50);
		this.render();
		new Notice('Layout updated');
	}

	updateStats() {
		const stats = this.plugin.api.graph.calculateGraphStats();
		const statsEl = this.containerEl.querySelector('#graph-stats');
		if (statsEl) {
			statsEl.innerHTML = `
				<span>📊 Nodes: ${stats.totalNodes}</span>
				<span>🔗 Edges: ${stats.totalEdges}</span>
				<span>📈 Avg Connect: ${stats.avgConnectivity}</span>
				<span>🔌 Isolated: ${stats.isolatedNodes}</span>
			`;
		}
	}

	render() {
		if (!this.ctx || !this.canvas) return;

		const ctx = this.ctx;
		const width = this.canvas.width;
		const height = this.canvas.height;

		// Clear canvas
		ctx.fillStyle = getComputedStyle(this.containerEl).getPropertyValue('--background-primary') || '#ffffff';
		ctx.fillRect(0, 0, width, height);

		// Save context for transformations
		ctx.save();

		const graph = this.plugin.api.graph.graph;

		// Draw edges first (behind nodes)
		ctx.strokeStyle = getComputedStyle(this.containerEl).getPropertyValue('--text-muted') || '#999999';
		ctx.lineWidth = 1;
		
		graph.edges.forEach(edge => {
			const source = graph.nodes.find(n => n.id === edge.source);
			const target = graph.nodes.find(n => n.id === edge.target);
			
			if (source && target && this.shouldShowNode(source) && this.shouldShowNode(target)) {
				const x1 = (source.x || 0) * this.zoom + this.panX;
				const y1 = (source.y || 0) * this.zoom + this.panY;
				const x2 = (target.x || 0) * this.zoom + this.panX;
				const y2 = (target.y || 0) * this.zoom + this.panY;

				// Edge color based on type
				switch (edge.type) {
					case 'link':
						ctx.strokeStyle = '#667eea';
						break;
					case 'tag':
						ctx.strokeStyle = '#10b981';
						break;
					case 'reference':
						ctx.strokeStyle = '#f59e0b';
						break;
					default:
						ctx.strokeStyle = '#999999';
				}

				ctx.globalAlpha = edge.weight;
				ctx.beginPath();
				ctx.moveTo(x1, y1);
				ctx.lineTo(x2, y2);
				ctx.stroke();
				ctx.globalAlpha = 1;
			}
		});

		// Draw nodes
		graph.nodes.forEach(node => {
			if (!this.shouldShowNode(node)) return;

			const x = (node.x || 0) * this.zoom + this.panX;
			const y = (node.y || 0) * this.zoom + this.panY;
			const size = (node.size || 10) * this.zoom;

			// Node shadow
			ctx.shadowColor = 'rgba(0, 0, 0, 0.2)';
			ctx.shadowBlur = 10;
			ctx.shadowOffsetX = 2;
			ctx.shadowOffsetY = 2;

			// Node circle
			ctx.beginPath();
			ctx.arc(x, y, size, 0, Math.PI * 2);
			ctx.fillStyle = node.color;
			ctx.fill();

			// Reset shadow
			ctx.shadowColor = 'transparent';
			ctx.shadowBlur = 0;
			ctx.shadowOffsetX = 0;
			ctx.shadowOffsetY = 0;

			// Selection/hover highlight
			if (node === this.selectedNode) {
				ctx.strokeStyle = '#ff6b6b';
				ctx.lineWidth = 3;
				ctx.stroke();
			} else if (node === this.hoveredNode) {
				ctx.strokeStyle = '#ffffff';
				ctx.lineWidth = 2;
				ctx.stroke();
			}

			// Node label (only if zoomed in enough)
			if (this.zoom > 0.5) {
				ctx.fillStyle = getComputedStyle(this.containerEl).getPropertyValue('--text-normal') || '#000000';
				ctx.font = `${12 * this.zoom}px sans-serif`;
				ctx.textAlign = 'center';
				ctx.textBaseline = 'middle';
				
				// Draw label below node
				const label = node.label.length > 20 ? node.label.substring(0, 20) + '...' : node.label;
				ctx.fillText(label, x, y + size + (15 * this.zoom));
			}
		});

		ctx.restore();
	}

	private exportGraph() {
		const json = this.plugin.api.graph.exportGraph();
		const blob = new Blob([json], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `knowledge-graph-${Date.now()}.json`;
		a.click();
		URL.revokeObjectURL(url);
		new Notice('Graph exported');
	}

	async onClose() {
		if (this.animationId) {
			cancelAnimationFrame(this.animationId);
		}
	}
}
