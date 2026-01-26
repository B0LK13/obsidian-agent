"""REST API module for obsidian-agent."""

from obsidian_agent.api.app import create_app
from obsidian_agent.api.routes import router

__all__ = ["create_app", "router"]
