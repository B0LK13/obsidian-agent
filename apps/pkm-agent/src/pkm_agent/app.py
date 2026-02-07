"""Main PKM Agent application."""

import asyncio
import logging
import uuid
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from pkm_agent.config import Config, load_config
from pkm_agent.data import Database, FileIndexer
from pkm_agent.llm import LLMProvider, Message, OllamaProvider, OpenAIProvider
from pkm_agent.rag import Chunker, EmbeddingEngine, Retriever, VectorStore
from pkm_agent.websocket_sync import SyncServer

logger = logging.getLogger(__name__)


class PKMAgentApp:
    """Main application class for PKM Agent."""

    def __init__(self, config: Config | None = None):
        self.config = config or load_config()
        self.config.ensure_dirs()

        # Initialize components
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
        # inject audit logger
        self.vectorstore.audit_logger = self.db.log_action
        self.chunker = Chunker()
        self.retriever = Retriever(
            self.db,
            self.vectorstore,
        )
        self.llm: LLMProvider | None = None
        self.conversation_id: str | None = None

        # Initialize sync server
        self.sync_server = SyncServer(host="127.0.0.1", port=27125)
        self._sync_server_task: asyncio.Task | None = None

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

        return self.llm

    async def initialize(self) -> None:
        """Initialize the application."""
        logger.info("Initializing PKM Agent...")
        self.db.log_action("command", "initialize_start", {})

        # Initialize LLM
        self._init_llm()

        # Index files
        await self.index_pkm()

        # Start file watcher for incremental indexing
        self.indexer.start_watch_mode()
        logger.info("File watcher started for real-time indexing")

        # Start WebSocket sync server
        self._sync_server_task = asyncio.create_task(self.sync_server.start())
        logger.info("WebSocket sync server started on ws://127.0.0.1:27125")

        # Setup sync callbacks
        self._setup_sync_callbacks()

        self.db.log_action("command", "initialize_complete", {})
        logger.info("PKM Agent initialized successfully")

    async def index_pkm(self) -> dict[str, int]:
        """Index all markdown files in PKM directory."""
        logger.info("Indexing PKM directory...")
        self.db.log_action("command", "index_start", {"pkm_root": str(self.config.pkm_root)})

        # Run file indexer
        count = self.indexer.index_all()

        # Update vector embeddings
        notes = self.db.get_all_notes(limit=10000)
        chunks = await self._update_embeddings(notes)

        self.db.log_action(
            "command",
            "index_complete",
            {"indexed_files": count, "chunks_added": chunks},
        )

        return {"indexed": count, "chunks": chunks}

    async def _update_embeddings(self, notes: list[Any]) -> int:
        """Update embeddings for notes."""
        total_chunks = 0

        for note in notes:
            # Chunk the note
            chunks = self.chunker.chunk_note(note)

            if not chunks:
                continue

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
        """Search for relevant notes."""
        self.db.log_action("command", "search", {"query": query, "limit": limit, "filters": filters or {}})
        results = self.retriever.retrieve(query, k=limit, filters=filters)
        self.db.log_action("command", "search_complete", {"results": len(results)})
        return [r.to_dict() for r in results]

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
        self.db.log_action(
            "command",
            "chat_user",
            {"conversation_id": self.conversation_id, "use_context": use_context},
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
        self.db.log_action(
            "command",
            "chat_assistant",
            {"conversation_id": self.conversation_id, "tokens": len(response_content.split())},
        )

    def _build_system_prompt(self, use_context: bool) -> str:
        """Build system prompt for the LLM."""
        prompt = """You are an AI assistant for a Personal Knowledge Management (PKM) system.
Your goal is to help users explore, understand, and connect information in their knowledge base.

When answering:
- Be concise and direct
- Reference specific notes when relevant
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

    async def get_stats(self) -> dict[str, Any]:
        """Get application statistics."""
        db_stats = self.db.get_stats()
        vs_stats = self.vectorstore.get_stats()

        return {
            **db_stats,
            "vector_store": vs_stats,
            "llm": {
                "provider": self.config.llm.provider,
                "model": self.config.llm.model,
            },
            "pkm_root": str(self.config.pkm_root),
        }

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

    async def close(self) -> None:
        """Clean up resources."""
        logger.info("Closing PKM Agent...")

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
