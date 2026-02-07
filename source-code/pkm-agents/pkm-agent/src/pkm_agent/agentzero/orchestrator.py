"""
AgentZero-based Orchestrator for Obsidian Agent System.

This module provides a multi-agent orchestration system using AgentZero
framework to coordinate between different specialized agents:
- Vault Manager Agent: Manages Obsidian vault operations
- RAG Agent: Handles retrieval-augmented generation
- Context Agent: Manages context awareness
- Planner Agent: Plans and executes multi-step tasks
"""

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class AgentType(Enum):
    """Types of specialized agents."""

    VAULT_MANAGER = "vault_manager"
    RAG_AGENT = "rag_agent"
    CONTEXT_AGENT = "context_agent"
    PLANNER_AGENT = "planner_agent"
    MEMORY_AGENT = "memory_agent"
    TOOL_EXECUTOR = "tool_executor"


class TaskStatus(Enum):
    """Status of agent tasks."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentMessage:
    """Message between agents."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_agent: str = ""
    to_agent: str = ""
    content: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: float = 0.0

    def __post_init__(self):
        if self.timestamp == 0.0:
            import time

            self.timestamp = time.time()


@dataclass
class AgentTask:
    """Task for an agent to execute."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_type: AgentType = AgentType.VAULT_MANAGER
    description: str = ""
    input_data: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    status: TaskStatus = TaskStatus.PENDING
    result: Any | None = None
    error: str | None = None
    created_at: float = 0.0
    completed_at: float | None = None

    def __post_init__(self):
        if self.created_at == 0.0:
            import time

            self.created_at = time.time()


@dataclass
class AgentCapability:
    """Capability of an agent."""

    name: str
    description: str
    input_schema: dict[str, Any]
    output_schema: dict[str, Any]


class BaseAgent:
    """Base class for all specialized agents."""

    def __init__(self, agent_id: str, agent_type: AgentType):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.capabilities: list[AgentCapability] = []
        self.message_queue: asyncio.Queue = asyncio.Queue()
        self.active_tasks: dict[str, AgentTask] = {}
        self.running = False

    async def initialize(self):
        """Initialize the agent."""
        logger.info(f"Initializing agent {self.agent_id} of type {self.agent_type.value}")
        self.running = True

    async def start(self):
        """Start the agent message processing loop."""
        logger.info(f"Starting agent {self.agent_id}")
        asyncio.create_task(self._process_messages())

    async def stop(self):
        """Stop the agent."""
        logger.info(f"Stopping agent {self.agent_id}")
        self.running = False

    async def _process_messages(self):
        """Process incoming messages."""
        while self.running:
            try:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=1.0)
                await self.handle_message(message)
            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing message in {self.agent_id}: {e}")

    async def send_message(self, message: AgentMessage):
        """Send a message to another agent."""
        await self.message_queue.put(message)

    async def handle_message(self, message: AgentMessage):
        """Handle an incoming message."""
        logger.debug(f"{self.agent_id} received message: {message.content[:100]}")

    async def execute_task(self, task: AgentTask) -> Any:
        """Execute a task."""
        logger.info(f"{self.agent_id} executing task: {task.description}")
        self.active_tasks[task.id] = task
        task.status = TaskStatus.IN_PROGRESS

        try:
            result = await self._execute_task_impl(task)
            task.result = result
            task.status = TaskStatus.COMPLETED
            return result
        except Exception as e:
            task.error = str(e)
            task.status = TaskStatus.FAILED
            logger.error(f"Task {task.id} failed: {e}")
            raise

    async def _execute_task_impl(self, task: AgentTask) -> Any:
        """Implement task execution in subclass."""
        raise NotImplementedError

    def get_capabilities(self) -> list[AgentCapability]:
        """Get agent capabilities."""
        return self.capabilities


class VaultManagerAgent(BaseAgent):
    """Agent for managing Obsidian vault operations."""

    def __init__(self, agent_id: str, vault_api_client):
        super().__init__(agent_id, AgentType.VAULT_MANAGER)
        self.vault_api = vault_api_client

    async def initialize(self):
        await super().initialize()
        self.capabilities = [
            # Core note operations
            AgentCapability(
                name="read_note",
                description="Read a note from the vault",
                input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"content": {"type": "string"}}},
            ),
            AgentCapability(
                name="create_note",
                description="Create a new note with optional frontmatter",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                        "frontmatter": {"type": "object"},
                    },
                },
                output_schema={"type": "object", "properties": {"success": {"type": "boolean"}}},
            ),
            AgentCapability(
                name="update_note",
                description="Update an existing note (overwrite, append, or prepend)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "content": {"type": "string"},
                        "mode": {"type": "string"},
                    },
                },
                output_schema={"type": "object", "properties": {"success": {"type": "boolean"}}},
            ),
            AgentCapability(
                name="delete_note",
                description="Delete a note from the vault",
                input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
                output_schema={"type": "object", "properties": {"success": {"type": "boolean"}}},
            ),
            # Search operations
            AgentCapability(
                name="search_vault",
                description="Search across the vault with optional path filter",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "path_filter": {"type": "string"},
                        "use_regex": {"type": "boolean"},
                    },
                },
                output_schema={"type": "array", "items": {"type": "object"}},
            ),
            AgentCapability(
                name="search_replace",
                description="Search and replace text in a note",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "search": {"type": "string"},
                        "replace": {"type": "string"},
                        "use_regex": {"type": "boolean"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {"success": {"type": "boolean"}, "count": {"type": "integer"}},
                },
            ),
            # Tag operations
            AgentCapability(
                name="manage_tags",
                description="Manage note tags (list, add, remove)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "action": {"type": "string"},
                        "tags": {"type": "array"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {"success": {"type": "boolean"}, "tags": {"type": "array"}},
                },
            ),
            # Frontmatter operations
            AgentCapability(
                name="manage_frontmatter",
                description="Manage note frontmatter (get, set, delete)",
                input_schema={
                    "type": "object",
                    "properties": {
                        "path": {"type": "string"},
                        "action": {"type": "string"},
                        "key": {"type": "string"},
                        "value": {},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "success": {"type": "boolean"},
                        "frontmatter": {"type": "object"},
                    },
                },
            ),
            # Periodic notes
            AgentCapability(
                name="get_daily_note",
                description="Get or create the daily note for a given date",
                input_schema={"type": "object", "properties": {"date": {"type": "string"}}},
                output_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                },
            ),
            AgentCapability(
                name="get_periodic_note",
                description="Get a periodic note (daily, weekly, monthly, quarterly, yearly)",
                input_schema={
                    "type": "object",
                    "properties": {"period": {"type": "string"}, "date": {"type": "string"}},
                },
                output_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                },
            ),
            # Templates
            AgentCapability(
                name="apply_template",
                description="Apply a template to create or update a note",
                input_schema={
                    "type": "object",
                    "properties": {
                        "template_path": {"type": "string"},
                        "target_path": {"type": "string"},
                        "variables": {"type": "object"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {"success": {"type": "boolean"}, "path": {"type": "string"}},
                },
            ),
            # Backlinks and links
            AgentCapability(
                name="get_backlinks",
                description="Get all notes that link to the specified note",
                input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
                output_schema={"type": "array", "items": {"type": "object"}},
            ),
            AgentCapability(
                name="get_links",
                description="Get all outgoing links from a note",
                input_schema={"type": "object", "properties": {"path": {"type": "string"}}},
                output_schema={
                    "type": "object",
                    "properties": {
                        "internal_links": {"type": "array"},
                        "external_links": {"type": "array"},
                    },
                },
            ),
            # Batch operations
            AgentCapability(
                name="batch_operations",
                description="Execute multiple operations in batch",
                input_schema={"type": "object", "properties": {"operations": {"type": "array"}}},
                output_schema={"type": "array", "items": {"type": "object"}},
            ),
            # Attachments
            AgentCapability(
                name="list_attachments",
                description="List attachments in a directory",
                input_schema={
                    "type": "object",
                    "properties": {
                        "directory": {"type": "string"},
                        "extension_filter": {"type": "string"},
                    },
                },
                output_schema={"type": "array", "items": {"type": "object"}},
            ),
            # Active file
            AgentCapability(
                name="get_active_note",
                description="Get the currently active note in Obsidian",
                input_schema={"type": "object"},
                output_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}, "content": {"type": "string"}},
                },
            ),
            AgentCapability(
                name="update_active_note",
                description="Update the currently active note",
                input_schema={
                    "type": "object",
                    "properties": {"content": {"type": "string"}, "mode": {"type": "string"}},
                },
                output_schema={"type": "object", "properties": {"success": {"type": "boolean"}}},
            ),
        ]

    async def _execute_task_impl(self, task: AgentTask) -> Any:
        """Execute vault manager operations."""
        operation = task.input_data.get("operation")

        # Core note operations
        if operation == "read_note":
            return await self.vault_api.read_note(task.input_data["path"])

        elif operation == "create_note":
            return await self.vault_api.create_note(
                task.input_data["path"],
                task.input_data["content"],
                task.input_data.get("frontmatter"),
            )

        elif operation == "update_note":
            return await self.vault_api.update_note(
                task.input_data["path"],
                task.input_data.get("content", ""),
                task.input_data.get("mode", "overwrite"),
            )

        elif operation == "delete_note":
            return await self.vault_api.delete_note(task.input_data["path"])

        # Search operations
        elif operation == "search":
            return await self.vault_api.global_search(
                task.input_data["query"],
                use_regex=task.input_data.get("use_regex", False),
                path_filter=task.input_data.get("path_filter"),
                limit=task.input_data.get("limit", 20),
            )

        elif operation == "search_replace":
            return await self.vault_api.search_and_replace(
                task.input_data["path"],
                task.input_data["search"],
                task.input_data["replace"],
                use_regex=task.input_data.get("use_regex", False),
                case_sensitive=task.input_data.get("case_sensitive", False),
                replace_all=task.input_data.get("replace_all", True),
            )

        # Tag operations
        elif operation == "manage_tags":
            action = task.input_data.get("action", "list")
            if action == "list":
                return {"tags": await self.vault_api.get_tags(task.input_data["path"])}
            elif action == "add":
                return await self.vault_api.add_tags(
                    task.input_data["path"], task.input_data.get("tags", [])
                )
            elif action == "remove":
                return await self.vault_api.remove_tags(
                    task.input_data["path"], task.input_data.get("tags", [])
                )
            else:
                return await self.vault_api.manage_tags(
                    task.input_data["path"], action, task.input_data.get("tags", [])
                )

        # Frontmatter operations
        elif operation == "manage_frontmatter":
            action = task.input_data.get("action", "get")
            if action == "get":
                return {
                    "frontmatter": await self.vault_api.get_frontmatter(task.input_data["path"])
                }
            elif action == "set":
                return await self.vault_api.set_frontmatter_key(
                    task.input_data["path"], task.input_data["key"], task.input_data["value"]
                )
            elif action == "delete":
                return await self.vault_api.delete_frontmatter_key(
                    task.input_data["path"], task.input_data["key"]
                )
            else:
                return await self.vault_api.manage_frontmatter(
                    task.input_data["path"],
                    action,
                    task.input_data.get("key"),
                    task.input_data.get("value"),
                )

        # Periodic notes
        elif operation == "get_daily_note":
            return await self.vault_api.get_periodic_note("daily", task.input_data.get("date"))

        elif operation == "get_periodic_note":
            return await self.vault_api.get_periodic_note(
                task.input_data.get("period", "daily"), task.input_data.get("date")
            )

        # Templates
        elif operation == "apply_template":
            # Read template, substitute variables, create note
            template = await self.vault_api.read_note(task.input_data["template_path"])
            content = template.get("content", "")
            variables = task.input_data.get("variables", {})

            # Simple variable substitution
            for key, value in variables.items():
                content = content.replace(f"{{{{  {key} }}}}", str(value))
                content = content.replace(f"{{{{{key}}}}}", str(value))

            return await self.vault_api.update_note(
                task.input_data["target_path"], content, mode="overwrite"
            )

        # Backlinks and links
        elif operation == "get_backlinks":
            return await self.vault_api.get_backlinks(task.input_data["path"])

        elif operation == "get_links":
            return await self.vault_api.get_note_links(task.input_data["path"])

        # Batch operations
        elif operation == "batch_operations":
            results = []
            for op in task.input_data.get("operations", []):
                try:
                    sub_task = AgentTask(
                        description=f"Batch sub-operation: {op.get('operation')}", input_data=op
                    )
                    result = await self._execute_task_impl(sub_task)
                    results.append({"success": True, "result": result})
                except Exception as e:
                    results.append({"success": False, "error": str(e)})
            return results

        # Attachments
        elif operation == "list_attachments":
            return await self.vault_api.list_notes(
                directory=task.input_data.get("directory", "/"),
                extension_filter=task.input_data.get(
                    "extension_filter", "png,jpg,jpeg,gif,pdf,mp3,mp4"
                ),
            )

        # Active note
        elif operation == "get_active_note":
            return await self.vault_api.get_active_note()

        elif operation == "update_active_note":
            return await self.vault_api.update_active_note(
                task.input_data.get("content", ""), task.input_data.get("mode", "append")
            )

        else:
            raise ValueError(f"Unknown operation: {operation}")


class RAGAgent(BaseAgent):
    """Agent for retrieval-augmented generation."""

    def __init__(self, agent_id: str, rag_engine):
        super().__init__(agent_id, AgentType.RAG_AGENT)
        self.rag_engine = rag_engine

    async def initialize(self):
        await super().initialize()
        self.capabilities = [
            AgentCapability(
                name="search_knowledge",
                description="Search the knowledge base semantically",
                input_schema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}, "limit": {"type": "integer"}},
                },
                output_schema={"type": "array", "items": {"type": "object"}},
            ),
            AgentCapability(
                name="generate_response",
                description="Generate a response with context",
                input_schema={
                    "type": "object",
                    "properties": {"query": {"type": "string"}, "use_context": {"type": "boolean"}},
                },
                output_schema={"type": "object", "properties": {"response": {"type": "string"}}},
            ),
        ]

    async def _execute_task_impl(self, task: AgentTask) -> Any:
        operation = task.input_data.get("operation")

        if operation == "search":
            return await self.rag_engine.search(
                task.input_data["query"], limit=task.input_data.get("limit", 10)
            )
        elif operation == "generate":
            return await self.rag_engine.generate(
                task.input_data["query"], use_context=task.input_data.get("use_context", True)
            )
        else:
            raise ValueError(f"Unknown operation: {operation}")


class ContextAgent(BaseAgent):
    """Agent for managing context awareness."""

    def __init__(self, agent_id: str, vault_api_client):
        super().__init__(agent_id, AgentType.CONTEXT_AGENT)
        self.vault_api = vault_api_client
        self.context_cache: dict[str, Any] = {}

    async def initialize(self):
        await super().initialize()
        self.capabilities = [
            AgentCapability(
                name="get_active_context",
                description="Get context of the active file",
                input_schema={"type": "object"},
                output_schema={"type": "object", "properties": {"context": {"type": "string"}}},
            ),
            AgentCapability(
                name="update_context",
                description="Update the current context",
                input_schema={"type": "object", "properties": {"context": {"type": "object"}}},
                output_schema={"type": "object", "properties": {"success": {"type": "boolean"}}},
            ),
        ]

    async def _execute_task_impl(self, task: AgentTask) -> Any:
        operation = task.input_data.get("operation")

        if operation == "get_active":
            active_file = await self.vault_api.get_active_file()
            if active_file:
                return {
                    "file_path": active_file,
                    "content": await self.vault_api.read_note(active_file),
                }
            return {}
        elif operation == "update":
            self.context_cache.update(task.input_data.get("context", {}))
            return {"success": True}
        else:
            raise ValueError(f"Unknown operation: {operation}")


class PlannerAgent(BaseAgent):
    """Agent for planning and coordinating multi-step tasks."""

    def __init__(self, agent_id: str, llm_client):
        super().__init__(agent_id, AgentType.PLANNER_AGENT)
        self.llm_client = llm_client
        self.task_plans: dict[str, list[AgentTask]] = {}

    async def initialize(self):
        await super().initialize()
        self.capabilities = [
            AgentCapability(
                name="plan_task",
                description="Create a plan for a complex task",
                input_schema={
                    "type": "object",
                    "properties": {"task_description": {"type": "string"}},
                },
                output_schema={"type": "array", "items": {"type": "object"}},
            ),
            AgentCapability(
                name="coordinate_agents",
                description="Coordinate multiple agents to complete tasks",
                input_schema={"type": "object", "properties": {"tasks": {"type": "array"}}},
                output_schema={"type": "object", "properties": {"results": {"type": "array"}}},
            ),
        ]

    async def _execute_task_impl(self, task: AgentTask) -> Any:
        operation = task.input_data.get("operation")

        if operation == "plan":
            return await self._create_plan(task.input_data["task_description"])
        elif operation == "coordinate":
            return await self._coordinate_tasks(task.input_data["tasks"])
        else:
            raise ValueError(f"Unknown operation: {operation}")

    async def _create_plan(self, task_description: str) -> list[dict[str, Any]]:
        """Create a plan using LLM."""
        prompt = f"""
You are a task planner for an Obsidian agent system. Given a task description, break it down into subtasks.

Task: {task_description}

Available agent types:
- vault_manager: Read, create, update notes, search vault, manage tags
- rag_agent: Search knowledge base, generate responses with context
- context_agent: Get active file context, update context
- memory_agent: Store and retrieve memories

Create a JSON plan with tasks that specify:
- agent_type: Which agent should handle this
- description: What the task should do
- input_data: Required inputs for the task
- dependencies: Which tasks must complete first (by index)

Return only the JSON plan.
"""

        response = await self.llm_client.generate(prompt)

        try:
            plan_data = json.loads(response)
            return plan_data.get("tasks", [])
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse plan: {e}")
            return []

    async def _coordinate_tasks(self, tasks: list[dict[str, Any]]) -> dict[str, Any]:
        """Coordinate task execution."""
        results = {}

        for task_data in tasks:
            deps = task_data.get("dependencies", [])
            if all(dep in results for dep in deps):
                task = AgentTask(**task_data)
                try:
                    result = await self.execute_task(task)
                    results[task.id] = result
                except Exception as e:
                    results[task.id] = {"error": str(e)}

        return results


class MemoryAgent(BaseAgent):
    """Agent for managing conversation memory."""

    def __init__(self, agent_id: str, storage_backend):
        super().__init__(agent_id, AgentType.MEMORY_AGENT)
        self.storage = storage_backend
        self.conversations: dict[str, list[AgentMessage]] = {}

    async def initialize(self):
        await super().initialize()
        self.capabilities = [
            AgentCapability(
                name="store_message",
                description="Store a message in memory",
                input_schema={
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string"},
                        "message": {"type": "object"},
                    },
                },
                output_schema={"type": "object", "properties": {"success": {"type": "boolean"}}},
            ),
            AgentCapability(
                name="retrieve_conversation",
                description="Retrieve conversation history",
                input_schema={
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string"},
                        "limit": {"type": "integer"},
                    },
                },
                output_schema={"type": "array", "items": {"type": "object"}},
            ),
        ]

    async def _execute_task_impl(self, task: AgentTask) -> Any:
        operation = task.input_data.get("operation")
        conversation_id = task.input_data["conversation_id"]

        if operation == "store":
            if conversation_id not in self.conversations:
                self.conversations[conversation_id] = []

            message = AgentMessage(**task.input_data["message"])
            self.conversations[conversation_id].append(message)
            await self.storage.store_message(conversation_id, message)
            return {"success": True}
        elif operation == "retrieve":
            limit = task.input_data.get("limit", 50)
            history = self.conversations.get(conversation_id, [])
            return history[-limit:]
        else:
            raise ValueError(f"Unknown operation: {operation}")


class AgentZeroOrchestrator:
    """Main orchestrator for AgentZero multi-agent system."""

    def __init__(self, config: dict[str, Any]):
        self.config = config
        self.agents: dict[str, BaseAgent] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.running = False

    async def initialize(self):
        """Initialize the orchestrator and all agents."""
        logger.info("Initializing AgentZero Orchestrator")

        # Initialize agents based on config
        if self.config.get("vault_manager", {}).get("enabled", True):
            from .mcp_client import ObsidianMCPClient

            vault_client = ObsidianMCPClient(self.config["vault_manager"])
            self.agents["vault_manager"] = VaultManagerAgent("vault_manager", vault_client)

        if self.config.get("rag_agent", {}).get("enabled", True):
            from pkm_agent.rag import Retriever

            # Initialize RAG engine - will be configured with actual database/vectorstore later
            rag_config = self.config.get("rag_agent", {})
            retriever = Retriever(
                rag_config.get("database"),  # type: ignore[arg-type]
                rag_config.get("vectorstore"),  # type: ignore[arg-type]
            )
            self.agents["rag_agent"] = RAGAgent("rag_agent", retriever)

        if self.config.get("context_agent", {}).get("enabled", True):
            from .mcp_client import ObsidianMCPClient

            vault_client = ObsidianMCPClient(self.config["vault_manager"])
            self.agents["context_agent"] = ContextAgent("context_agent", vault_client)

        if self.config.get("planner_agent", {}).get("enabled", True):
            from .llm_client import LLMClient

            llm_client = LLMClient(self.config["planner_agent"].get("llm", {}))
            self.agents["planner_agent"] = PlannerAgent("planner_agent", llm_client)

        if self.config.get("memory_agent", {}).get("enabled", True):
            from .storage import InMemoryStorage

            storage = InMemoryStorage()
            self.agents["memory_agent"] = MemoryAgent("memory_agent", storage)

        # Initialize all agents
        for agent in self.agents.values():
            await agent.initialize()

        logger.info(f"Initialized {len(self.agents)} agents")

    async def start(self):
        """Start the orchestrator."""
        logger.info("Starting AgentZero Orchestrator")
        self.running = True

        # Start all agents
        for agent in self.agents.values():
            await agent.start()

        # Start task processing
        asyncio.create_task(self._process_tasks())

    async def stop(self):
        """Stop the orchestrator."""
        logger.info("Stopping AgentZero Orchestrator")
        self.running = False

        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()

    async def _process_tasks(self):
        """Process tasks from the queue."""
        while self.running:
            try:
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                await self._execute_task(task)
            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing task: {e}")

    async def submit_task(self, task: AgentTask) -> str:
        """Submit a task for execution."""
        await self.task_queue.put(task)
        return task.id

    async def _execute_task(self, task: AgentTask):
        """Execute a task."""
        agent = self.agents.get(task.agent_type.value)
        if not agent:
            logger.error(f"No agent found for type: {task.agent_type}")
            task.status = TaskStatus.FAILED
            task.error = "Agent not found"
            return

        try:
            await agent.execute_task(task)
        except Exception as e:
            logger.error(f"Task execution failed: {e}")

    async def process_user_request(self, request: str) -> AsyncIterator[str]:
        """Process a user request and stream responses."""
        logger.info(f"Processing user request: {request[:100]}")

        # Use planner to break down the request
        planner = self.agents.get("planner_agent")
        if not planner:
            yield "Error: Planner agent not available"
            return

        plan_task = AgentTask(
            agent_type=AgentType.PLANNER_AGENT,
            description="Create plan for user request",
            input_data={"operation": "plan", "task_description": request},
        )

        plan = await planner.execute_task(plan_task)

        if not plan:
            yield "I couldn't create a plan for your request. Please try again."
            return

        # Execute the plan
        coordinate_task = AgentTask(
            agent_type=AgentType.PLANNER_AGENT,
            description="Coordinate agents to execute plan",
            input_data={"operation": "coordinate", "tasks": plan},
        )

        results = await planner.execute_task(coordinate_task)

        # Stream results
        yield f"Executed {len(results)} tasks:\n"
        for task_id, result in results.items():
            if "error" not in result:
                yield "✓ Task completed\n"
            else:
                yield f"✗ Task failed: {result.get('error', 'Unknown error')}\n"

    def get_agent_capabilities(self) -> dict[str, list[AgentCapability]]:
        """Get capabilities of all agents."""
        return {agent_id: agent.get_capabilities() for agent_id, agent in self.agents.items()}

    async def get_status(self) -> dict[str, Any]:
        """Get status of all agents."""
        return {
            agent_id: {
                "type": agent.agent_type.value,
                "active_tasks": len(agent.active_tasks),
                "running": agent.running,
            }
            for agent_id, agent in self.agents.items()
        }


async def create_orchestrator(config: dict[str, Any]) -> AgentZeroOrchestrator:
    """Create and initialize an orchestrator."""
    orchestrator = AgentZeroOrchestrator(config)
    await orchestrator.initialize()
    await orchestrator.start()
    return orchestrator
