"""
AgentZero multi-agent orchestration system for Obsidian PKM.

This package provides:
- Orchestrator for coordinating multiple agents
- MCP client for communicating with Obsidian and RAG servers
- LLM client for AI provider integration
- Storage backends for conversation management
"""

from .llm_client import LLMClient, LLMClientError, OllamaProvider, OpenAIProvider, create_llm_client
from .mcp_client import (
    MCPClientError,
    MCPConnectionError,
    MCPResponseError,
    ObsidianMCPClient,
    PKMRAGMCPClient,
    UnifiedMCPClient,
    create_unified_client,
)
from .orchestrator import (
    AgentCapability,
    AgentMessage,
    AgentTask,
    AgentType,
    AgentZeroOrchestrator,
    BaseAgent,
    ContextAgent,
    MemoryAgent,
    PlannerAgent,
    RAGAgent,
    TaskStatus,
    VaultManagerAgent,
    create_orchestrator,
)
from .storage import BaseStorage, FileStorage, InMemoryStorage, SQLiteStorage, create_storage

__all__ = [
    "AgentZeroOrchestrator",
    "BaseAgent",
    "VaultManagerAgent",
    "RAGAgent",
    "ContextAgent",
    "PlannerAgent",
    "MemoryAgent",
    "AgentType",
    "TaskStatus",
    "AgentMessage",
    "AgentTask",
    "AgentCapability",
    "create_orchestrator",
    "ObsidianMCPClient",
    "PKMRAGMCPClient",
    "UnifiedMCPClient",
    "MCPClientError",
    "MCPConnectionError",
    "MCPResponseError",
    "create_unified_client",
    "LLMClient",
    "OpenAIProvider",
    "OllamaProvider",
    "LLMClientError",
    "create_llm_client",
    "BaseStorage",
    "InMemoryStorage",
    "FileStorage",
    "SQLiteStorage",
    "create_storage",
]
