"""Graph API endpoints."""

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends

from pkm_agent.api.server import get_pkm_app
from pkm_agent.app import PKMAgentApp
from pkm_agent.data.graph import GraphGenerator
from pkm_agent.data.link_analyzer import LinkAnalyzer

router = APIRouter()

@router.get("/")
async def get_graph(
    app: PKMAgentApp = Depends(get_pkm_app)
):
    """Get knowledge graph data."""
    analyzer = LinkAnalyzer(app.config.pkm_root)
    generator = GraphGenerator(analyzer)
    graph_data = generator.generate_graph()
    
    return {
        "elements": {
            "nodes": graph_data.nodes,
            "edges": graph_data.edges
        }
    }
