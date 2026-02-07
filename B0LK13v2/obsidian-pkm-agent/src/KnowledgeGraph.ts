import { App, TFile, CachedMetadata } from 'obsidian';
import { VaultManager } from './VaultManager';

/**
 * Node in the knowledge graph
 */
interface GraphNode {
    id: string;
    path: string;
    title: string;
    type: 'note' | 'tag' | 'folder';
    metadata?: {
        tags?: string[];
        frontmatter?: Record<string, any>;
        created?: number;
        modified?: number;
        wordCount?: number;
    };
}

/**
 * Edge (connection) in the knowledge graph
 */
interface GraphEdge {
    source: string;
    target: string;
    type: 'link' | 'tag' | 'folder' | 'semantic';
    weight: number;
    metadata?: Record<string, any>;
}

/**
 * Cluster of related nodes
 */
interface Cluster {
    id: string;
    name: string;
    nodes: string[];
    centroid?: string;
    cohesion: number;
}

/**
 * KnowledgeGraph - Maps relationships and semantic connections in the vault
 * Enables intelligent navigation, suggestions, and understanding of knowledge structure.
 */
export class KnowledgeGraph {
    private app: App;
    private vaultManager: VaultManager;
    private nodes: Map<string, GraphNode> = new Map();
    private edges: Map<string, GraphEdge> = new Map();
    private clusters: Map<string, Cluster> = new Map();
    private lastUpdated: number = 0;
    private updateThreshold: number = 60000; // 1 minute

    constructor(app: App, vaultManager: VaultManager) {
        this.app = app;
        this.vaultManager = vaultManager;
    }

    // ============================================
    // GRAPH BUILDING
    // ============================================

    /**
     * Builds or updates the knowledge graph from the vault.
     */
    async buildGraph(force: boolean = false): Promise<void> {
        const now = Date.now();
        if (!force && (now - this.lastUpdated) < this.updateThreshold) {
            return; // Use cached graph
        }

        console.log('[KnowledgeGraph] Building graph...');
        this.nodes.clear();
        this.edges.clear();
        this.clusters.clear();

        const files = this.app.vault.getMarkdownFiles();

        // Build nodes for all files
        for (const file of files) {
            await this.addFileNode(file);
        }

        // Build edges from links
        for (const file of files) {
            await this.buildEdgesForFile(file);
        }

        // Build tag nodes and edges
        this.buildTagGraph();

        // Identify clusters
        this.identifyClusters();

        this.lastUpdated = now;
        console.log(`[KnowledgeGraph] Built graph: ${this.nodes.size} nodes, ${this.edges.size} edges`);
    }

    /**
     * Adds a file as a node in the graph.
     */
    private async addFileNode(file: TFile): Promise<void> {
        const cache = this.app.metadataCache.getFileCache(file);
        const content = await this.app.vault.cachedRead(file);

        const node: GraphNode = {
            id: file.path,
            path: file.path,
            title: file.basename,
            type: 'note',
            metadata: {
                tags: this.extractTags(cache),
                frontmatter: cache?.frontmatter,
                created: file.stat.ctime,
                modified: file.stat.mtime,
                wordCount: content.split(/\s+/).length
            }
        };

        this.nodes.set(file.path, node);
    }

    /**
     * Builds edges (connections) for a file.
     */
    private async buildEdgesForFile(file: TFile): Promise<void> {
        const cache = this.app.metadataCache.getFileCache(file);
        
        if (!cache?.links) return;

        for (const link of cache.links) {
            const resolved = this.app.metadataCache.getFirstLinkpathDest(link.link, file.path);
            if (!resolved) continue;

            const edgeId = `${file.path}->${resolved.path}`;
            const edge: GraphEdge = {
                source: file.path,
                target: resolved.path,
                type: 'link',
                weight: 1.0,
                metadata: {
                    displayText: link.displayText
                }
            };

            this.edges.set(edgeId, edge);
        }
    }

    /**
     * Builds the tag portion of the graph.
     */
    private buildTagGraph(): void {
        const tagCounts: Map<string, string[]> = new Map();

        // Collect all tags and their files
        for (const node of this.nodes.values()) {
            if (node.type !== 'note' || !node.metadata?.tags) continue;
            
            for (const tag of node.metadata.tags) {
                if (!tagCounts.has(tag)) {
                    tagCounts.set(tag, []);
                }
                tagCounts.get(tag)!.push(node.id);
            }
        }

        // Create tag nodes and edges
        for (const [tag, files] of tagCounts.entries()) {
            const tagNodeId = `tag:${tag}`;
            
            // Add tag node
            this.nodes.set(tagNodeId, {
                id: tagNodeId,
                path: tagNodeId,
                title: `#${tag}`,
                type: 'tag',
                metadata: {
                    wordCount: files.length
                }
            });

            // Add edges from files to tag
            for (const filePath of files) {
                const edgeId = `${filePath}->tag:${tag}`;
                this.edges.set(edgeId, {
                    source: filePath,
                    target: tagNodeId,
                    type: 'tag',
                    weight: 0.5
                });
            }
        }
    }

    // ============================================
    // CLUSTERING & ANALYSIS
    // ============================================

    /**
     * Identifies clusters of related notes.
     */
    private identifyClusters(): void {
        // Simple clustering based on shared tags and links
        const visited = new Set<string>();
        let clusterId = 0;

        for (const node of this.nodes.values()) {
            if (node.type !== 'note' || visited.has(node.id)) continue;

            const clusterNodes = this.expandCluster(node.id, visited);
            if (clusterNodes.length >= 2) {
                const cluster: Cluster = {
                    id: `cluster-${clusterId++}`,
                    name: this.generateClusterName(clusterNodes),
                    nodes: clusterNodes,
                    centroid: this.findCentroid(clusterNodes),
                    cohesion: this.calculateCohesion(clusterNodes)
                };
                this.clusters.set(cluster.id, cluster);
            }
        }
    }

    /**
     * Expands a cluster from a starting node using BFS.
     */
    private expandCluster(startId: string, visited: Set<string>): string[] {
        const cluster: string[] = [];
        const queue = [startId];
        const maxSize = 50;

        while (queue.length > 0 && cluster.length < maxSize) {
            const nodeId = queue.shift()!;
            if (visited.has(nodeId)) continue;
            
            const node = this.nodes.get(nodeId);
            if (!node || node.type !== 'note') continue;

            visited.add(nodeId);
            cluster.push(nodeId);

            // Find connected nodes
            const connected = this.getConnectedNodes(nodeId);
            for (const conn of connected) {
                if (!visited.has(conn) && this.nodes.get(conn)?.type === 'note') {
                    queue.push(conn);
                }
            }
        }

        return cluster;
    }

    /**
     * Generates a name for a cluster based on common tags.
     */
    private generateClusterName(nodeIds: string[]): string {
        const tagCounts: Record<string, number> = {};

        for (const nodeId of nodeIds) {
            const node = this.nodes.get(nodeId);
            if (!node?.metadata?.tags) continue;
            
            for (const tag of node.metadata.tags) {
                tagCounts[tag] = (tagCounts[tag] || 0) + 1;
            }
        }

        const topTag = Object.entries(tagCounts)
            .sort((a, b) => b[1] - a[1])[0];

        return topTag ? `#${topTag[0]}` : 'Mixed';
    }

    /**
     * Finds the centroid (most connected node) of a cluster.
     */
    private findCentroid(nodeIds: string[]): string {
        let maxConnections = 0;
        let centroid = nodeIds[0];

        for (const nodeId of nodeIds) {
            const connections = this.getConnectedNodes(nodeId)
                .filter(c => nodeIds.includes(c)).length;
            
            if (connections > maxConnections) {
                maxConnections = connections;
                centroid = nodeId;
            }
        }

        return centroid;
    }

    /**
     * Calculates the cohesion of a cluster (0-1).
     */
    private calculateCohesion(nodeIds: string[]): number {
        if (nodeIds.length <= 1) return 1;

        let totalConnections = 0;
        const maxPossible = nodeIds.length * (nodeIds.length - 1);

        for (const nodeId of nodeIds) {
            const connections = this.getConnectedNodes(nodeId)
                .filter(c => nodeIds.includes(c));
            totalConnections += connections.length;
        }

        return maxPossible > 0 ? totalConnections / maxPossible : 0;
    }

    // ============================================
    // QUERYING
    // ============================================

    /**
     * Gets all nodes connected to a given node.
     */
    getConnectedNodes(nodeId: string): string[] {
        const connected: Set<string> = new Set();

        for (const edge of this.edges.values()) {
            if (edge.source === nodeId) {
                connected.add(edge.target);
            } else if (edge.target === nodeId) {
                connected.add(edge.source);
            }
        }

        return Array.from(connected);
    }

    /**
     * Gets the shortest path between two nodes.
     */
    findPath(fromId: string, toId: string): string[] | null {
        if (!this.nodes.has(fromId) || !this.nodes.has(toId)) {
            return null;
        }

        const visited = new Set<string>();
        const queue: { node: string; path: string[] }[] = [{ node: fromId, path: [fromId] }];

        while (queue.length > 0) {
            const { node, path } = queue.shift()!;
            
            if (node === toId) {
                return path;
            }

            if (visited.has(node)) continue;
            visited.add(node);

            const connected = this.getConnectedNodes(node);
            for (const neighbor of connected) {
                if (!visited.has(neighbor)) {
                    queue.push({ node: neighbor, path: [...path, neighbor] });
                }
            }
        }

        return null;
    }

    /**
     * Finds related notes based on graph proximity and shared attributes.
     */
    async findRelated(
        noteId: string, 
        options?: { 
            limit?: number; 
            includeTagRelated?: boolean;
            maxDistance?: number 
        }
    ): Promise<{ path: string; score: number; reason: string }[]> {
        await this.buildGraph();
        
        const limit = options?.limit || 10;
        const maxDistance = options?.maxDistance || 3;
        const results: Map<string, { score: number; reasons: string[] }> = new Map();

        const sourceNode = this.nodes.get(noteId);
        if (!sourceNode) return [];

        // Direct links (highest score)
        const outgoing = this.vaultManager.getOutgoingLinks(noteId);
        for (const link of outgoing) {
            const targetPath = this.resolveLinkPath(link.link, noteId);
            if (targetPath) {
                this.addScore(results, targetPath, 1.0, 'direct link');
            }
        }

        // Backlinks
        const backlinks = this.vaultManager.getBacklinks(noteId);
        for (const bl of backlinks) {
            this.addScore(results, bl.path, 0.9, 'backlink');
        }

        // Tag-based relations
        if (options?.includeTagRelated !== false && sourceNode.metadata?.tags) {
            for (const tag of sourceNode.metadata.tags) {
                const tagResults = this.vaultManager.searchByTag(tag, 20);
                for (const tr of tagResults) {
                    if (tr.path !== noteId) {
                        this.addScore(results, tr.path, 0.6, `shared tag #${tag}`);
                    }
                }
            }
        }

        // Graph proximity (BFS up to maxDistance)
        const visited = new Set<string>([noteId]);
        let frontier = [noteId];
        
        for (let distance = 1; distance <= maxDistance; distance++) {
            const nextFrontier: string[] = [];
            const score = 0.5 / distance;

            for (const node of frontier) {
                const neighbors = this.getConnectedNodes(node);
                for (const neighbor of neighbors) {
                    if (!visited.has(neighbor) && this.nodes.get(neighbor)?.type === 'note') {
                        visited.add(neighbor);
                        nextFrontier.push(neighbor);
                        this.addScore(results, neighbor, score, `${distance} hops away`);
                    }
                }
            }

            frontier = nextFrontier;
        }

        // Sort and return
        return Array.from(results.entries())
            .filter(([path]) => path !== noteId)
            .map(([path, data]) => ({
                path,
                score: data.score,
                reason: data.reasons.join(', ')
            }))
            .sort((a, b) => b.score - a.score)
            .slice(0, limit);
    }

    /**
     * Adds or updates a score for a result.
     */
    private addScore(
        results: Map<string, { score: number; reasons: string[] }>,
        path: string,
        score: number,
        reason: string
    ): void {
        const existing = results.get(path);
        if (existing) {
            existing.score += score;
            if (!existing.reasons.includes(reason)) {
                existing.reasons.push(reason);
            }
        } else {
            results.set(path, { score, reasons: [reason] });
        }
    }

    /**
     * Resolves a link to an absolute path.
     */
    private resolveLinkPath(link: string, sourcePath: string): string | null {
        const file = this.app.metadataCache.getFirstLinkpathDest(link, sourcePath);
        return file?.path || null;
    }

    /**
     * Suggests notes that might be good to link to.
     */
    async suggestLinks(noteId: string, limit: number = 5): Promise<string[]> {
        await this.buildGraph();
        
        const node = this.nodes.get(noteId);
        if (!node) return [];

        const currentLinks = new Set(
            this.vaultManager.getOutgoingLinks(noteId).map(l => l.link)
        );
        const currentBacklinks = new Set(
            this.vaultManager.getBacklinks(noteId).map(b => b.path)
        );

        const candidates: { path: string; score: number }[] = [];

        // Find notes with shared tags but no links
        if (node.metadata?.tags) {
            for (const tag of node.metadata.tags) {
                const tagResults = this.vaultManager.searchByTag(tag, 30);
                for (const tr of tagResults) {
                    if (
                        tr.path !== noteId &&
                        !currentLinks.has(tr.path) &&
                        !currentBacklinks.has(tr.path)
                    ) {
                        const existingIdx = candidates.findIndex(c => c.path === tr.path);
                        if (existingIdx >= 0) {
                            candidates[existingIdx].score += 1;
                        } else {
                            candidates.push({ path: tr.path, score: 1 });
                        }
                    }
                }
            }
        }

        // Notes in the same cluster
        for (const cluster of this.clusters.values()) {
            if (cluster.nodes.includes(noteId)) {
                for (const clusterNode of cluster.nodes) {
                    if (
                        clusterNode !== noteId &&
                        !currentLinks.has(clusterNode) &&
                        !currentBacklinks.has(clusterNode)
                    ) {
                        const existingIdx = candidates.findIndex(c => c.path === clusterNode);
                        if (existingIdx >= 0) {
                            candidates[existingIdx].score += 0.5;
                        } else {
                            candidates.push({ path: clusterNode, score: 0.5 });
                        }
                    }
                }
            }
        }

        return candidates
            .sort((a, b) => b.score - a.score)
            .slice(0, limit)
            .map(c => c.path);
    }

    // ============================================
    // INSIGHTS & ANALYTICS
    // ============================================

    /**
     * Gets the most connected notes (hubs).
     */
    getHubNotes(limit: number = 10): { path: string; connections: number }[] {
        const connectionCounts: Map<string, number> = new Map();

        for (const edge of this.edges.values()) {
            if (edge.type === 'link') {
                connectionCounts.set(
                    edge.source, 
                    (connectionCounts.get(edge.source) || 0) + 1
                );
                connectionCounts.set(
                    edge.target, 
                    (connectionCounts.get(edge.target) || 0) + 1
                );
            }
        }

        return Array.from(connectionCounts.entries())
            .filter(([path]) => this.nodes.get(path)?.type === 'note')
            .map(([path, connections]) => ({ path, connections }))
            .sort((a, b) => b.connections - a.connections)
            .slice(0, limit);
    }

    /**
     * Gets graph statistics.
     */
    getGraphStats(): {
        nodeCount: number;
        edgeCount: number;
        clusterCount: number;
        avgConnections: number;
        orphanCount: number;
        hubNotes: string[];
    } {
        let totalConnections = 0;
        let noteCount = 0;
        const orphans: string[] = [];

        for (const node of this.nodes.values()) {
            if (node.type !== 'note') continue;
            noteCount++;
            
            const connections = this.getConnectedNodes(node.id)
                .filter(c => this.nodes.get(c)?.type === 'note').length;
            totalConnections += connections;
            
            if (connections === 0) {
                orphans.push(node.id);
            }
        }

        const hubs = this.getHubNotes(5).map(h => h.path);

        return {
            nodeCount: this.nodes.size,
            edgeCount: this.edges.size,
            clusterCount: this.clusters.size,
            avgConnections: noteCount > 0 ? totalConnections / noteCount / 2 : 0,
            orphanCount: orphans.length,
            hubNotes: hubs
        };
    }

    /**
     * Gets clusters with their details.
     */
    getClusters(): Cluster[] {
        return Array.from(this.clusters.values())
            .sort((a, b) => b.nodes.length - a.nodes.length);
    }

    /**
     * Finds potential duplicate or very similar notes.
     */
    async findSimilarNotes(
        noteId: string, 
        threshold: number = 0.7
    ): Promise<{ path: string; similarity: number }[]> {
        await this.buildGraph();
        
        const sourceNode = this.nodes.get(noteId);
        if (!sourceNode || sourceNode.type !== 'note') return [];

        const sourceTags = new Set(sourceNode.metadata?.tags || []);
        const results: { path: string; similarity: number }[] = [];

        for (const [id, node] of this.nodes.entries()) {
            if (id === noteId || node.type !== 'note') continue;

            const targetTags = new Set(node.metadata?.tags || []);
            
            // Jaccard similarity for tags
            const intersection = new Set([...sourceTags].filter(t => targetTags.has(t)));
            const union = new Set([...sourceTags, ...targetTags]);
            
            if (union.size === 0) continue;
            
            const tagSimilarity = intersection.size / union.size;

            // Title similarity (simple)
            const titleSimilarity = this.stringSimilarity(
                sourceNode.title.toLowerCase(),
                node.title.toLowerCase()
            );

            const combinedSimilarity = (tagSimilarity * 0.6) + (titleSimilarity * 0.4);

            if (combinedSimilarity >= threshold) {
                results.push({ path: id, similarity: combinedSimilarity });
            }
        }

        return results.sort((a, b) => b.similarity - a.similarity);
    }

    /**
     * Simple string similarity (Levenshtein-based).
     */
    private stringSimilarity(a: string, b: string): number {
        if (a === b) return 1;
        if (a.length === 0 || b.length === 0) return 0;

        const maxLen = Math.max(a.length, b.length);
        const distance = this.levenshteinDistance(a, b);
        
        return 1 - (distance / maxLen);
    }

    /**
     * Levenshtein distance calculation.
     */
    private levenshteinDistance(a: string, b: string): number {
        const matrix: number[][] = [];

        for (let i = 0; i <= b.length; i++) {
            matrix[i] = [i];
        }
        for (let j = 0; j <= a.length; j++) {
            matrix[0][j] = j;
        }

        for (let i = 1; i <= b.length; i++) {
            for (let j = 1; j <= a.length; j++) {
                if (b.charAt(i - 1) === a.charAt(j - 1)) {
                    matrix[i][j] = matrix[i - 1][j - 1];
                } else {
                    matrix[i][j] = Math.min(
                        matrix[i - 1][j - 1] + 1,
                        matrix[i][j - 1] + 1,
                        matrix[i - 1][j] + 1
                    );
                }
            }
        }

        return matrix[b.length][a.length];
    }

    /**
     * Extracts tags from cache.
     */
    private extractTags(cache: CachedMetadata | null): string[] {
        if (!cache) return [];
        
        const tags: string[] = [];
        
        if (cache.frontmatter?.tags) {
            const fmTags = Array.isArray(cache.frontmatter.tags) 
                ? cache.frontmatter.tags 
                : [cache.frontmatter.tags];
            tags.push(...fmTags.map(t => String(t)));
        }
        
        if (cache.tags) {
            tags.push(...cache.tags.map(t => t.tag.slice(1)));
        }

        return [...new Set(tags)];
    }

    /**
     * Gets a node by ID.
     */
    getNode(id: string): GraphNode | undefined {
        return this.nodes.get(id);
    }

    /**
     * Gets all note nodes.
     */
    getNoteNodes(): GraphNode[] {
        return Array.from(this.nodes.values()).filter(n => n.type === 'note');
    }
}
