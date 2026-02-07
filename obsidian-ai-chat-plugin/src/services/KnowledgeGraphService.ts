import { TFile, TFolder, Vault } from 'obsidian';
import AIChatNotesPlugin from '../../main';

export interface GraphNode {
	id: string;
	label: string;
	type: 'note' | 'tag' | 'link' | 'concept';
	size: number;
	color: string;
	x?: number;
	y?: number;
	metadata?: {
		path?: string;
		created?: number;
		modified?: number;
		tags?: string[];
	};
}

export interface GraphEdge {
	source: string;
	target: string;
	type: 'link' | 'tag' | 'similarity' | 'reference';
	weight: number;
}

export interface KnowledgeGraph {
	nodes: GraphNode[];
	edges: GraphEdge[];
}

export interface GraphCluster {
	id: string;
	label: string;
	nodeIds: string[];
	color: string;
}

export class KnowledgeGraphService {
	plugin: AIChatNotesPlugin;
	graph: KnowledgeGraph = { nodes: [], edges: [] };
	clusters: GraphCluster[] = [];

	// Color palette for different node types
	colors = {
		note: '#667eea',
		tag: '#10b981',
		link: '#f59e0b',
		concept: '#ec4899'
	};

	constructor(plugin: AIChatNotesPlugin) {
		this.plugin = plugin;
	}

	async buildGraph(): Promise<KnowledgeGraph> {
		const nodes: GraphNode[] = [];
		const edges: GraphEdge[] = [];
		const nodeMap = new Map<string, GraphNode>();

		// Get all markdown files
		const files = this.plugin.app.vault.getMarkdownFiles();

		// Create nodes for each note
		for (const file of files) {
			const node: GraphNode = {
				id: file.path,
				label: file.basename,
				type: 'note',
				size: 10,
				color: this.colors.note,
				metadata: {
					path: file.path,
					created: file.stat.ctime,
					modified: file.stat.mtime,
					tags: []
				}
			};
			nodes.push(node);
			nodeMap.set(file.path, node);
		}

		// Process each file for links and tags
		for (const file of files) {
			const content = await this.plugin.app.vault.read(file);
			const sourceNode = nodeMap.get(file.path);

			if (!sourceNode) continue;

			// Extract internal links [[link]]
			const linkMatches = content.matchAll(/\[\[([^\]]+)\]\]/g);
			for (const match of linkMatches) {
				const linkText = match[1];
				const targetPath = this.resolveLink(linkText, file);

				if (targetPath && nodeMap.has(targetPath)) {
					edges.push({
						source: file.path,
						target: targetPath,
						type: 'link',
						weight: 1
					});

					// Increase node size based on connections
					sourceNode.size += 2;
					const targetNode = nodeMap.get(targetPath);
					if (targetNode) targetNode.size += 2;
				}
			}

			// Extract tags #tag
			const tagMatches = content.matchAll(/#(\w+)/g);
			const tags = new Set<string>();
			for (const match of tagMatches) {
				tags.add(match[1]);
			}

			// Create tag nodes and edges
			for (const tag of tags) {
				const tagId = `tag:${tag}`;
				
				if (!nodeMap.has(tagId)) {
					const tagNode: GraphNode = {
						id: tagId,
						label: `#${tag}`,
						type: 'tag',
						size: 8,
						color: this.colors.tag
					};
					nodes.push(tagNode);
					nodeMap.set(tagId, tagNode);
				}

				edges.push({
					source: file.path,
					target: tagId,
					type: 'tag',
					weight: 0.5
				});

				sourceNode.metadata?.tags?.push(tag);
			}

			// Extract external links/concept mentions
			const conceptMatches = content.matchAll(/\b(AI|machine learning|deep learning|neural network|data|algorithm|model|training)\b/gi);
			const concepts = new Set<string>();
			for (const match of conceptMatches) {
				concepts.add(match[0].toLowerCase());
			}

			for (const concept of concepts) {
				const conceptId = `concept:${concept}`;
				
				if (!nodeMap.has(conceptId)) {
					const conceptNode: GraphNode = {
						id: conceptId,
						label: concept,
						type: 'concept',
						size: 6,
						color: this.colors.concept
					};
					nodes.push(conceptNode);
					nodeMap.set(conceptId, conceptNode);
				}

				edges.push({
					source: file.path,
					target: conceptId,
					type: 'reference',
					weight: 0.3
				});
			}
		}

		this.graph = { nodes, edges };
		return this.graph;
	}

	private resolveLink(linkText: string, sourceFile: TFile): string | null {
		// Try to find the file by name
		const files = this.plugin.app.vault.getMarkdownFiles();
		
		// Check for exact match or basename match
		for (const file of files) {
			if (file.basename === linkText || file.path === linkText) {
				return file.path;
			}
		}

		// Check for partial match
		for (const file of files) {
			if (file.basename.toLowerCase().includes(linkText.toLowerCase())) {
				return file.path;
			}
		}

		return null;
	}

	async findSimilarNotes(file: TFile, limit: number = 5): Promise<TFile[]> {
		// Use the search service to find semantically similar notes
		const content = await this.plugin.app.vault.read(file);
		const similar = await this.plugin.searchService.semanticSearch(content.substring(0, 500));
		
		return similar.filter(f => f.path !== file.path).slice(0, limit);
	}

	calculateGraphStats(): {
		totalNodes: number;
		totalEdges: number;
		avgConnectivity: number;
		isolatedNodes: number;
		clusters: number;
	} {
		const { nodes, edges } = this.graph;
		
		// Calculate connectivity for each node
		const connectivity = new Map<string, number>();
		nodes.forEach(n => connectivity.set(n.id, 0));
		edges.forEach(e => {
			connectivity.set(e.source, (connectivity.get(e.source) || 0) + 1);
			connectivity.set(e.target, (connectivity.get(e.target) || 0) + 1);
		});

		const isolatedNodes = nodes.filter(n => (connectivity.get(n.id) || 0) === 0).length;
		const avgConnectivity = nodes.length > 0 
			? Array.from(connectivity.values()).reduce((a, b) => a + b, 0) / nodes.length 
			: 0;

		return {
			totalNodes: nodes.length,
			totalEdges: edges.length,
			avgConnectivity: Math.round(avgConnectivity * 100) / 100,
			isolatedNodes,
			clusters: this.clusters.length
		};
	}

	findPath(startId: string, endId: string): GraphNode[] | null {
		// BFS to find shortest path
		const queue: string[] = [startId];
		const visited = new Set<string>([startId]);
		const parent = new Map<string, string>();

		while (queue.length > 0) {
			const current = queue.shift()!;

			if (current === endId) {
				// Reconstruct path
				const path: GraphNode[] = [];
				let nodeId: string | undefined = endId;
				while (nodeId) {
					const node = this.graph.nodes.find(n => n.id === nodeId);
					if (node) path.unshift(node);
					nodeId = parent.get(nodeId);
				}
				return path;
			}

			// Find neighbors
			const neighbors = this.graph.edges
				.filter(e => e.source === current || e.target === current)
				.map(e => e.source === current ? e.target : e.source);

			for (const neighbor of neighbors) {
				if (!visited.has(neighbor)) {
					visited.add(neighbor);
					parent.set(neighbor, current);
					queue.push(neighbor);
				}
			}
		}

		return null;
	}

	getConnectedNodes(nodeId: string): GraphNode[] {
		const connectedIds = new Set<string>();
		
		this.graph.edges.forEach(edge => {
			if (edge.source === nodeId) connectedIds.add(edge.target);
			if (edge.target === nodeId) connectedIds.add(edge.source);
		});

		return this.graph.nodes.filter(n => connectedIds.has(n.id));
	}

	exportGraph(): string {
		return JSON.stringify(this.graph, null, 2);
	}

	importGraph(json: string): boolean {
		try {
			this.graph = JSON.parse(json);
			return true;
		} catch (error) {
			return false;
		}
	}

	// Force-directed layout calculation
	calculateLayout(iterations: number = 100): void {
		const { nodes, edges } = this.graph;
		const width = 1000;
		const height = 800;
		const k = Math.sqrt((width * height) / nodes.length) * 0.5; // Optimal distance

		// Initialize random positions if not set
		nodes.forEach(node => {
			if (node.x === undefined) node.x = Math.random() * width;
			if (node.y === undefined) node.y = Math.random() * height;
		});

		// Force-directed algorithm
		for (let i = 0; i < iterations; i++) {
			// Repulsion forces
			for (let a = 0; a < nodes.length; a++) {
				for (let b = a + 1; b < nodes.length; b++) {
					const nodeA = nodes[a];
					const nodeB = nodes[b];
					
					const dx = nodeA.x! - nodeB.x!;
					const dy = nodeA.y! - nodeB.y!;
					const distance = Math.sqrt(dx * dx + dy * dy) || 1;
					
					const force = (k * k) / distance;
					const fx = (dx / distance) * force;
					const fy = (dy / distance) * force;
					
					nodeA.x! += fx * 0.1;
					nodeA.y! += fy * 0.1;
					nodeB.x! -= fx * 0.1;
					nodeB.y! -= fy * 0.1;
				}
			}

			// Attraction forces along edges
			edges.forEach(edge => {
				const source = nodes.find(n => n.id === edge.source);
				const target = nodes.find(n => n.id === edge.target);
				
				if (source && target) {
					const dx = target.x! - source.x!;
					const dy = target.y! - source.y!;
					const distance = Math.sqrt(dx * dx + dy * dy) || 1;
					
					const force = (distance * distance) / k;
					const fx = (dx / distance) * force * 0.1 * edge.weight;
					const fy = (dy / distance) * force * 0.1 * edge.weight;
					
					source.x! += fx;
					source.y! += fy;
					target.x! -= fx;
					target.y! -= fy;
				}
			});

			// Center gravity
			nodes.forEach(node => {
				const dx = node.x! - width / 2;
				const dy = node.y! - height / 2;
				node.x! -= dx * 0.01;
				node.y! -= dy * 0.01;
			});
		}

		// Keep within bounds
		nodes.forEach(node => {
			node.x = Math.max(50, Math.min(width - 50, node.x!));
			node.y = Math.max(50, Math.min(height - 50, node.y!));
		});
	}

	filterGraph(options: {
		nodeTypes?: string[];
		minConnections?: number;
		searchQuery?: string;
	}): KnowledgeGraph {
		let filteredNodes = [...this.graph.nodes];

		if (options.nodeTypes) {
			filteredNodes = filteredNodes.filter(n => options.nodeTypes!.includes(n.type));
		}

		if (options.minConnections !== undefined) {
			const connectivity = new Map<string, number>();
			this.graph.edges.forEach(e => {
				connectivity.set(e.source, (connectivity.get(e.source) || 0) + 1);
				connectivity.set(e.target, (connectivity.get(e.target) || 0) + 1);
			});
			filteredNodes = filteredNodes.filter(n => (connectivity.get(n.id) || 0) >= options.minConnections!);
		}

		if (options.searchQuery) {
			const query = options.searchQuery.toLowerCase();
			filteredNodes = filteredNodes.filter(n => 
				n.label.toLowerCase().includes(query) ||
				n.id.toLowerCase().includes(query)
			);
		}

		const nodeIds = new Set(filteredNodes.map(n => n.id));
		const filteredEdges = this.graph.edges.filter(e => 
			nodeIds.has(e.source) && nodeIds.has(e.target)
		);

		return { nodes: filteredNodes, edges: filteredEdges };
	}
}
