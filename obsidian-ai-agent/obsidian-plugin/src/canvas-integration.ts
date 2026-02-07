/**
 * Canvas Integration
 * Creates and manipulates Obsidian Canvas files
 */

import { App, TFile, TFolder } from 'obsidian';

export interface CanvasNode {
    id: string;
    type: 'text' | 'file' | 'link';
    x: number;
    y: number;
    width: number;
    height: number;
    content?: string;
    file?: string;
}

export interface CanvasEdge {
    id: string;
    fromNode: string;
    toNode: string;
    label?: string;
}

export interface CanvasData {
    nodes: CanvasNode[];
    edges: CanvasEdge[];
}

export class CanvasIntegration {
    private app: App;

    constructor(app: App) {
        this.app = app;
    }

    /**
     * Create a new canvas file
     */
    async createCanvas(name: string, data: CanvasData): Promise<TFile> {
        const canvasContent = JSON.stringify(data, null, 2);
        const filePath = `Canvas/${name}.canvas`;

        // Ensure Canvas folder exists
        const canvasFolder = this.app.vault.getAbstractFileByPath('Canvas');
        if (!canvasFolder) {
            await this.app.vault.createFolder('Canvas');
        }

        // Check if file exists
        const existingFile = this.app.vault.getAbstractFileByPath(filePath);
        if (existingFile instanceof TFile) {
            await this.app.vault.modify(existingFile, canvasContent);
            return existingFile;
        }

        return await this.app.vault.create(filePath, canvasContent);
    }

    /**
     * Create a canvas from a set of notes
     */
    async createCanvasFromNotes(title: string, files: TFile[]): Promise<TFile> {
        const nodes: CanvasNode[] = [];
        const edges: CanvasEdge[] = [];

        // Create central node
        const centerX = 0;
        const centerY = 0;
        
        if (files.length > 0) {
            const centerFile = files[0];
            nodes.push({
                id: 'center',
                type: 'file',
                x: centerX,
                y: centerY,
                width: 400,
                height: 300,
                file: centerFile.path
            });
        }

        // Create surrounding nodes for related notes
        const radius = 600;
        const angleStep = (2 * Math.PI) / Math.max(files.length - 1, 1);

        for (let i = 1; i < files.length; i++) {
            const file = files[i];
            const angle = (i - 1) * angleStep;
            const x = centerX + radius * Math.cos(angle);
            const y = centerY + radius * Math.sin(angle);

            const nodeId = `node-${i}`;
            nodes.push({
                id: nodeId,
                type: 'file',
                x,
                y,
                width: 300,
                height: 200,
                file: file.path
            });

            // Connect to center
            edges.push({
                id: `edge-${i}`,
                fromNode: 'center',
                toNode: nodeId,
                label: 'related'
            });
        }

        return await this.createCanvas(title, { nodes, edges });
    }

    /**
     * Create a canvas from AI-generated structure
     */
    async createCanvasFromAI(title: string, structure: any): Promise<TFile> {
        const nodes: CanvasNode[] = [];
        const edges: CanvasEdge[] = [];

        // Parse AI structure and create nodes/edges
        // This is a simplified implementation
        if (structure.nodes) {
            for (const node of structure.nodes) {
                nodes.push({
                    id: node.id,
                    type: node.type || 'text',
                    x: node.x || 0,
                    y: node.y || 0,
                    width: node.width || 400,
                    height: node.height || 300,
                    content: node.content,
                    file: node.file
                });
            }
        }

        if (structure.edges) {
            for (const edge of structure.edges) {
                edges.push({
                    id: edge.id,
                    fromNode: edge.from,
                    toNode: edge.to,
                    label: edge.label
                });
            }
        }

        return await this.createCanvas(title, { nodes, edges });
    }

    /**
     * Add a node to an existing canvas
     */
    async addNodeToCanvas(canvasFile: TFile, node: CanvasNode): Promise<void> {
        const content = await this.app.vault.read(canvasFile);
        const data: CanvasData = JSON.parse(content);

        data.nodes.push(node);

        await this.app.vault.modify(canvasFile, JSON.stringify(data, null, 2));
    }

    /**
     * Generate a mind map canvas from content
     */
    async generateMindMap(title: string, centralTopic: string, subtopics: string[]): Promise<TFile> {
        const nodes: CanvasNode[] = [];
        const edges: CanvasEdge[] = [];

        // Central node
        nodes.push({
            id: 'center',
            type: 'text',
            x: 0,
            y: 0,
            width: 300,
            height: 150,
            content: centralTopic
        });

        // Subtopic nodes
        const radius = 500;
        const angleStep = (2 * Math.PI) / subtopics.length;

        subtopics.forEach((topic, index) => {
            const angle = index * angleStep;
            const x = radius * Math.cos(angle);
            const y = radius * Math.sin(angle);

            const nodeId = `subtopic-${index}`;
            nodes.push({
                id: nodeId,
                type: 'text',
                x,
                y,
                width: 250,
                height: 120,
                content: topic
            });

            edges.push({
                id: `edge-${index}`,
                fromNode: 'center',
                toNode: nodeId
            });
        });

        return await this.createCanvas(`${title}-mindmap`, { nodes, edges });
    }
}
