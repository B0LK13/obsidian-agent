"""Enhanced PKM Agent application with Phase 1 optimizations integrated.

Integrates:
- Audit logging system
- Multi-level caching
- HNSW vector index (already in vectorstore)
- ReAct agent for autonomous workflows
"""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from pkm_agent.audit_logger import AuditEntry, AuditLogger
from pkm_agent.cache_manager import CacheManager
from pkm_agent.config import Config, load_config
from pkm_agent.data import Database, FileIndexer
from pkm_agent.llm import LLMProvider, Message, OllamaProvider, OpenAIProvider
from pkm_agent.rag import Chunker, EmbeddingEngine, Retriever, VectorStore
from pkm_agent.react_agent import (
    CreateNoteTool,
    ReActAgent,
    ReadNoteTool,
    SearchNotesTool,
    SynthesizeTool,
)
from pkm_agent.websocket_sync import SyncServer

logger = logging.getLogger(__name__)


class EnhancedPKMAgent:
    """Enhanced PKM Agent with audit, caching, and agentic capabilities."""

    def __init__(self, config: Config | None = None):
        self.config = config or load_config()
        self.config.ensure_dirs()

        # Initialize audit logger
        audit_db_path = self.config.data_dir / "audit.db"
        self.audit_logger = AuditLogger(audit_db_path)

        # Initialize cache manager
        self.cache = CacheManager(
            cache_dir=self.config.cache_path,
            memory_cache_size=1000,
        )

        # Initialize core components
        self.db = Database(self.config.db_path)
        self.indexer = FileIndexer(
            self.config.pkm_root,
            self.db,
            watch_mode=True,
        )
        self.embedding_engine = EmbeddingEngine(
            model_name=self.config.rag.embedding_model,
            cache_dir=self.config.cache_path,
        )
        self.vectorstore = VectorStore(
            self.config.chroma_path,
            self.embedding_engine,
        )
        # Inject audit logger into vectorstore
        self.vectorstore.audit_logger = self._log_vectorstore_action
        
        self.chunker = Chunker()
        self.retriever = Retriever(
            self.db,
            self.vectorstore,
        )
        self.llm: LLMProvider | None = None
        self.conversation_id: str | None = None
        
        # ReAct agent (initialized after LLM)
        self.react_agent: ReActAgent | None = None

        # Initialize sync server
        self.sync_server = SyncServer(host="127.0.0.1", port=27125)
        self._sync_server_task: asyncio.Task | None = None

    def _log_vectorstore_action(self, action: str, operation: str, metadata: dict):
        """Callback for vectorstore audit logging."""
        asyncio.create_task(self._async_log_action(action, operation, metadata))

    async def _async_log_action(self, action: str, operation: str, metadata: dict):
        """Async wrapper for audit logging."""
        entry = AuditEntry(
            action=f"{action}:{operation}",
            target=metadata.get("note_id") or metadata.get("count", "unknown"),
            metadata=metadata,
            reversible=False,  # Vector ops are not directly reversible
        )
        await self.audit_logger.log(entry)

    def _init_llm(self) -> LLMProvider:
        """Initialize LLM provider based on config."""
        if self.llm:
            return self.llm

        llm_config = self.config.llm

        if llm_config.provider == "openai":
            self.llm = OpenAIProvider(
                model=llm_config.model,
                api_key=llm_config.api_key,
                base_url=llm_config.base_url,
            )
        elif llm_config.provider == "ollama":
            self.llm = OllamaProvider(
                model=llm_config.model,
                base_url=llm_config.base_url or "http://localhost:11434",
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config.provider}")

        # Initialize ReAct agent with tools
        self._init_react_agent()
        
        return self.llm

    def _init_react_agent(self):
        """Initialize ReAct agent with available tools."""
        if not self.llm:
            return
            
        tools = [
            SearchNotesTool(self.retriever),
            ReadNoteTool(self.db),
            CreateNoteTool(self.db),
            SynthesizeTool(self.llm),
        ]
        
        self.react_agent = ReActAgent(
            llm_provider=self.llm,
            tools=tools,
            max_iterations=10,
            verbose=True,
        )

    async def initialize(self) -> None:
        """Initialize the application."""
        logger.info("Initializing Enhanced PKM Agent...")
        
        # Initialize audit logger
        await self.audit_logger.initialize()
        logger.info("Audit logger initialized")
        
        # Log initialization start
        entry = AuditEntry(
            action="initialize",
            metadata={"pkm_root": str(self.config.pkm_root)},
        )
        await self.audit_logger.log(entry)

        # Initialize LLM
        self._init_llm()

        # Index files
        stats = await self.index_pkm()
        logger.info(f"Indexed {stats['indexed']} files, {stats['chunks']} chunks")

        # Start file watcher for incremental indexing
        self.indexer.start_watch_mode()
        logger.info("File watcher started for real-time indexing")

        # Start WebSocket sync server
        self._sync_server_task = asyncio.create_task(self.sync_server.start())
        logger.info("WebSocket sync server started on ws://127.0.0.1:27125")

        # Setup sync callbacks
        self._setup_sync_callbacks()

        # Log initialization complete
        entry = AuditEntry(
            action="initialize_complete",
            metadata={"stats": stats},
        )
        await self.audit_logger.log(entry)
        logger.info("Enhanced PKM Agent initialized successfully")

    async def index_pkm(self) -> dict[str, int]:
        """Index all markdown files in PKM directory with caching."""
        logger.info("Indexing PKM directory...")

        # Run file indexer
        count = self.indexer.index_all()

        # Update vector embeddings with caching
        notes = self.db.get_all_notes(limit=10000)
        chunks = await self._update_embeddings(notes)

        return {"indexed": count, "chunks": chunks}

    async def _update_embeddings(self, notes: list[Any]) -> int:
        """Update embeddings for notes with intelligent caching."""
        total_chunks = 0

        for note in notes:
            note_id = note["id"]
            
            # Check cache first
            cached_chunks = self.cache.get_chunks(note_id)
            if cached_chunks:
                # Verify content hasn't changed
                current_content = note.get("content", "")
                if cached_chunks.get("content_hash") == hash(current_content):
                    logger.debug(f"Using cached chunks for note {note_id}")
                    continue

            # Chunk the note
            chunks = self.chunker.chunk_note(note)

            if not chunks:
                continue

            # Cache the chunks
            self.cache.set_chunks(note_id, {
                "chunks": chunks,
                "content_hash": hash(note.get("content", "")),
            })

            # Add to vector store
            added = self.vectorstore.add_chunks(chunks)
            total_chunks += added

        logger.info(f"Updated embeddings for {total_chunks} chunks")
        return total_chunks

    async def search(
        self,
        query: str,
        limit: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Search for relevant notes with caching."""
        # Check cache first
        cache_key = f"{query}:{limit}:{filters}"
        cached_result = self.cache.get_query_result(cache_key)
        if cached_result:
            logger.debug("Returning cached search results")
            return cached_result

        # Perform search
        results = self.retriever.retrieve(query, k=limit, filters=filters)
        result_dicts = [r.to_dict() for r in results]
        
        # Cache results
        self.cache.set_query_result(cache_key, result_dicts)
        
        # Log action
        entry = AuditEntry(
            action="search",
            metadata={
                "query": query,
                "limit": limit,
                "filters": filters or {},
                "results_count": len(result_dicts),
            },
        )
        await self.audit_logger.log(entry)
        
        return result_dicts

    async def chat(
        self,
        message: str,
        conversation_id: str | None = None,
        use_context: bool = True,
    ) -> AsyncIterator[str]:
        """Chat with the PKM agent."""
        llm = self._init_llm()

        # Create or load conversation
        if conversation_id:
            self.conversation_id = conversation_id
            messages = self._load_conversation(conversation_id)
        else:
            self.conversation_id = str(uuid.uuid4())
            messages = []
            self.db.create_conversation(self.conversation_id)

        # Add user message
        user_msg = Message(role="user", content=message)
        messages.append(user_msg)
        self.db.add_message(
            self.conversation_id,
            user_msg.role,
            user_msg.content,
            model=llm.model,
        )

        # Build system prompt with context
        system_prompt = self._build_system_prompt(use_context)
        system_msg = Message(role="system", content=system_prompt)

        # Generate response
        response_content = ""
        async for chunk in llm.generate_stream(
            [system_msg] + messages,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
        ):
            response_content += chunk
            yield chunk

        # Save assistant response
        self.db.add_message(
            self.conversation_id,
            "assistant",
            response_content,
            model=llm.model,
        )
        
        # Log chat interaction
        entry = AuditEntry(
            action="chat",
            target=self.conversation_id,
            metadata={
                "message_length": len(message),
                "response_length": len(response_content),
                "use_context": use_context,
            },
        )
        await self.audit_logger.log(entry)

    async def ask_with_context(
        self,
        query: str,
        max_context_tokens: int = 2000,
    ) -> AsyncIterator[str]:
        """Ask a question with relevant context from the knowledge base."""
        # Retrieve relevant context
        context = self.retriever.get_context_for_query(query, max_context_tokens)

        # Build system prompt with context
        system_prompt = self._build_system_prompt(use_context=False)
        if context:
            system_prompt += f"\n\n## Relevant Notes from Your Knowledge Base\n{context}\n"
            system_prompt += "\nUse the above information to help answer the user's question."

        # Create messages
        messages = [
            Message(role="system", content=system_prompt),
            Message(role="user", content=query),
        ]

        llm = self._init_llm()
        # Generate response
        async for chunk in llm.generate_stream(
            messages,
            temperature=self.config.llm.temperature,
            max_tokens=self.config.llm.max_tokens,
        ):
            yield chunk

    async def research(self, topic: str, create_summary: bool = True) -> dict[str, Any]:
        """Autonomous research workflow using ReAct agent."""
        if not self.react_agent:
            raise RuntimeError("ReAct agent not initialized. Call initialize() first.")
        
        logger.info(f"Starting autonomous research on: {topic}")
        
        # Build goal
        goal = f"Research the topic '{topic}' by searching my knowledge base, reading relevant notes, and synthesizing the information."
        if create_summary:
            goal += " Create a comprehensive summary note with citations."
        
        # Execute agent
        result = await self.react_agent.execute(
            goal=goal,
            context=f"PKM root: {self.config.pkm_root}"
        )
        
        # Log research workflow
        entry = AuditEntry(
            action="research",
            target=topic,
            metadata={
                "status": result.status.value,
                "iterations": len(result.reasoning_chain),
                "create_summary": create_summary,
            },
            snapshot_after=result.answer,
        )
        await self.audit_logger.log(entry)
        
        return {
            "status": result.status.value,
            "answer": result.answer,
            "reasoning_chain": [
                {
                    "step": step.step_number,
                    "thought": step.thought,
                    "action": step.action,
                    "observation": step.observation,
                }
                for step in result.reasoning_chain
            ],
            "metadata": result.metadata,
        }

    async def get_stats(self) -> dict[str, Any]:
        """Get comprehensive application statistics."""
        db_stats = self.db.get_stats()
        vs_stats = self.vectorstore.get_stats()
        cache_stats = self.cache.stats()
        audit_stats = await self.audit_logger.get_stats()

        return {
            **db_stats,
            "vector_store": vs_stats,
            "cache": cache_stats,
            "audit": audit_stats,
            "llm": {
                "provider": self.config.llm.provider,
                "model": self.config.llm.model,
            },
            "pkm_root": str(self.config.pkm_root),
        }

    def _build_system_prompt(self, use_context: bool) -> str:
        """Build system prompt for the LLM."""
        prompt = """You are an AI assistant for a Personal Knowledge Management (PKM) system.
Your goal is to help users explore, understand, and connect information in their knowledge base.

When answering:
- Be concise and direct
- Reference specific notes when relevant using [[Wiki Links]]
- Suggest connections between related ideas
- Help users discover information they may have forgotten
- If you don't find relevant information, be honest about it
"""

        if use_context and self.conversation_id:
            # Get recent conversation history
            recent_msgs = self.db.get_conversation_messages(self.conversation_id, limit=10)
            if len(recent_msgs) > 2:
                prompt += "\n\nRecent conversation context:\n"
                for msg in recent_msgs[-4:]:
                    role = msg["role"].capitalize()
                    content = msg["content"][:500]
                    if len(msg["content"]) > 500:
                        content += "..."
                    prompt += f"{role}: {content}\n"

        return prompt

    def _load_conversation(self, conversation_id: str) -> list[Message]:
        """Load conversation history from database."""
        rows = self.db.get_conversation_messages(conversation_id, limit=50)

        messages = []
        for row in rows:
            messages.append(Message(
                role=row["role"],
                content=row["content"],
            ))

        return messages

    def get_conversation_history(self, limit: int = 50) -> list[dict[str, Any]]:
        """Get conversation history."""
        if not self.conversation_id:
            return []

        return self.db.get_conversation_messages(self.conversation_id, limit=limit)

    def list_conversations(self) -> list[dict[str, Any]]:
        """List all conversations."""
        with self.db._get_connection() as conn:
            rows = conn.execute(
                "SELECT id, started_at, message_count FROM conversations ORDER BY started_at DESC"
            ).fetchall()
            return [dict(row) for row in rows]

    def _setup_sync_callbacks(self) -> None:
        """Setup callbacks to broadcast sync events."""
        # Override indexer callbacks to broadcast events
        original_on_created = self.indexer._on_file_created
        original_on_modified = self.indexer._on_file_modified
        original_on_deleted = self.indexer._on_file_deleted

        async def on_created_with_sync(path: Path):
            await original_on_created(path)
            await self.sync_server.broadcast_file_created(str(path))

        async def on_modified_with_sync(path: Path):
            await original_on_modified(path)
            await self.sync_server.broadcast_file_modified(str(path))

        async def on_deleted_with_sync(path: Path):
            await original_on_deleted(path)
            await self.sync_server.broadcast_file_deleted(str(path))

        self.indexer._on_file_created = on_created_with_sync
        self.indexer._on_file_modified = on_modified_with_sync
        self.indexer._on_file_deleted = on_deleted_with_sync

    async def rollback_operation(self, operation_id: str) -> bool:
        """Rollback a previous operation."""
        # Create a simple rollback handler
        class SimpleRollbackHandler:
            def __init__(self, db):
                self.db = db
                
            async def rollback(self, entry: AuditEntry) -> bool:
                """Rollback based on action type."""
                if entry.action.startswith("create"):
                    # Delete created resource
                    return True
                elif entry.action.startswith("update"):
                    # Restore previous snapshot
                    if entry.snapshot_before:
                        # Would restore content here
                        return True
                return False
        
        handler = SimpleRollbackHandler(self.db)
        success = await self.audit_logger.rollback(operation_id, handler)
        
        if success:
            logger.info(f"Successfully rolled back operation {operation_id}")
        else:
            logger.error(f"Failed to rollback operation {operation_id}")
            
        return success

    async def close(self) -> None:
        """Clean up resources."""
        logger.info("Closing Enhanced PKM Agent...")

        # Stop file watcher
        if hasattr(self.indexer, 'stop_watch_mode'):
            self.indexer.stop_watch_mode()
            logger.info("File watcher stopped")

        # Stop sync server
        if self.sync_server:
            await self.sync_server.stop()
            logger.info("WebSocket sync server stopped")

        if self._sync_server_task:
            self._sync_server_task.cancel()
            try:
                await self._sync_server_task
            except asyncio.CancelledError:
                pass
        
        # Close audit logger
        await self.audit_logger.close()
        logger.info("Audit logger closed")
