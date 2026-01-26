"""Knowledge graph builder for vault visualization."""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class NodeType(str, Enum):
    NOTE = "note"
    TAG = "tag"
    FOLDER = "folder"
    EXTERNAL = "external"


class EdgeType(str, Enum):
    LINK = "link"
    BACKLINK = "backlink"
    TAG = "tag"
    FOLDER = "folder"
    SEMANTIC = "semantic"


@dataclass
class GraphNode:
    """A node in the knowledge graph."""
    id: str
    label: str
    node_type: NodeType
    weight: float = 1.0
    color: str | None = None
    size: float = 10.0
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "label": self.label, "type": self.node_type.value,
            "weight": self.weight, "color": self.color, "size": self.size, **self.metadata,
        }


@dataclass
class GraphEdge:
    """An edge in the knowledge graph."""
    source: str
    target: str
    edge_type: EdgeType
    weight: float = 1.0
    label: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source, "target": self.target, "type": self.edge_type.value,
            "weight": self.weight, "label": self.label, **self.metadata,
        }


@dataclass
class KnowledgeGraph:
    """Complete knowledge graph structure."""
    nodes: list[GraphNode] = field(default_factory=list)
    edges: list[GraphEdge] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {"nodes": [n.to_dict() for n in self.nodes], "edges": [e.to_dict() for e in self.edges]}
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)
    
    def to_cytoscape(self) -> dict[str, Any]:
        """Export in Cytoscape.js format."""
        elements = []
        for node in self.nodes:
            elements.append({"data": {"id": node.id, "label": node.label}, "classes": node.node_type.value})
        for edge in self.edges:
            elements.append({"data": {"source": edge.source, "target": edge.target}, "classes": edge.edge_type.value})
        return {"elements": elements}
    
    def to_d3(self) -> dict[str, Any]:
        """Export in D3.js force-directed format."""
        return {
            "nodes": [{"id": n.id, "label": n.label, "group": n.node_type.value} for n in self.nodes],
            "links": [{"source": e.source, "target": e.target, "value": e.weight} for e in self.edges],
        }
    
    def get_neighbors(self, node_id: str) -> list[str]:
        return list({e.target for e in self.edges if e.source == node_id} | 
                   {e.source for e in self.edges if e.target == node_id})
    
    def get_subgraph(self, center_id: str, depth: int = 1) -> "KnowledgeGraph":
        included = {center_id}
        current = {center_id}
        for _ in range(depth):
            next_layer = set()
            for nid in current:
                next_layer.update(self.get_neighbors(nid))
            included.update(next_layer)
            current = next_layer
        nodes = [n for n in self.nodes if n.id in included]
        edges = [e for e in self.edges if e.source in included and e.target in included]
        return KnowledgeGraph(nodes=nodes, edges=edges)


class GraphBuilder:
    """Builds knowledge graphs from vault notes."""
    
    def __init__(self, parser):
        self.parser = parser
        self._colors = {NodeType.NOTE: "#7c3aed", NodeType.TAG: "#10b981", NodeType.FOLDER: "#f59e0b"}
    
    async def build_graph(self, include_tags: bool = True) -> KnowledgeGraph:
        graph = KnowledgeGraph()
        notes = {}
        for md_file in self.parser.vault_path.rglob("*.md"):
            note = await self.parser.parse_file(md_file)
            if note:
                notes[note.path] = note
                graph.nodes.append(GraphNode(id=note.path, label=note.title, node_type=NodeType.NOTE))
                for link in note.links:
                    graph.edges.append(GraphEdge(source=note.path, target=link, edge_type=EdgeType.LINK))
        if include_tags:
            all_tags = set()
            for note in notes.values():
                all_tags.update(note.tags)
            for tag in all_tags:
                graph.nodes.append(GraphNode(id=f"tag:{tag}", label=f"#{tag}", node_type=NodeType.TAG))
            for path, note in notes.items():
                for tag in note.tags:
                    graph.edges.append(GraphEdge(source=path, target=f"tag:{tag}", edge_type=EdgeType.TAG))
        graph.metadata = {"note_count": len(notes), "edge_count": len(graph.edges)}
        return graph
