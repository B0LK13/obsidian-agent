"""Graph data generation for visualization."""

import logging
from dataclasses import dataclass
from typing import Any

from pkm_agent.data.link_analyzer import LinkAnalyzer

logger = logging.getLogger(__name__)


@dataclass
class GraphData:
    """Graph data structure."""
    nodes: list[dict[str, Any]]
    edges: list[dict[str, Any]]


class GraphGenerator:
    """Generates graph data from vault analysis."""

    def __init__(self, analyzer: LinkAnalyzer):
        self.analyzer = analyzer

    def generate_graph(self) -> GraphData:
        """Generate graph data for visualization."""
        analysis = self.analyzer.analyze_vault()
        
        nodes = []
        edges = []
        
        # Track node existence to ensure edge targets exist
        # analysis.link_graph keys are source paths
        # analysis.link_graph values are sets of target names (titles or paths)
        
        # We need to resolve targets to full paths/IDs to match nodes
        # LinkAnalyzer._note_cache maps titles to paths
        
        # 1. Create nodes for all notes
        # We can use the analyzer's note cache to get all valid notes
        for title, path in self.analyzer._note_cache.items():
            # Use path as ID to be unique
            node_id = str(path)
            
            # Simple weight calculation based on incoming links
            # We'd need to compute this from the graph
            weight = 1 # Default
            
            nodes.append({
                "data": {
                    "id": node_id,
                    "label": title,
                    "path": str(path),
                    "weight": weight
                }
            })

        # 2. Create edges
        for source_path, targets in analysis.link_graph.items():
            for target in targets:
                # Target might be a title or a path
                # Try to resolve to a node ID (path)
                target_path = None
                
                # Check direct path match (if target was a path)
                # LinkAnalyzer puts the raw target string in the set
                
                # Try to look up in note cache
                if target in self.analyzer._note_cache:
                    target_path = str(self.analyzer._note_cache[target])
                elif f"{target}.md" in self.analyzer._note_cache:
                    target_path = str(self.analyzer._note_cache[f"{target}.md"])
                
                # If we found a valid target path, create edge
                if target_path:
                    edges.append({
                        "data": {
                            "source": source_path,
                            "target": target_path
                        }
                    })

        # Calculate weights (degree centrality)
        # This is n^2 ish but usually fine for <10k notes
        incoming = {}
        for edge in edges:
            tgt = edge["data"]["target"]
            incoming[tgt] = incoming.get(tgt, 0) + 1
            
        for node in nodes:
            nid = node["data"]["id"]
            node["data"]["weight"] = incoming.get(nid, 0) + 1 # Base size 1

        return GraphData(nodes=nodes, edges=edges)
