"""
Storage backend for AgentZero orchestrator.

This module provides storage solutions for conversations and memories.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


class BaseStorage:
    """Base storage backend."""

    async def store_message(self, conversation_id: str, message: Any) -> bool:
        """Store a message."""
        raise NotImplementedError

    async def retrieve_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> list[Any]:
        """Retrieve messages."""
        raise NotImplementedError

    async def create_conversation(self, conversation_id: str, metadata: dict[str, Any] | None = None) -> bool:
        """Create a new conversation."""
        raise NotImplementedError

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        """Get conversation metadata."""
        raise NotImplementedError

    async def list_conversations(self) -> list[dict[str, Any]]:
        """List all conversations."""
        raise NotImplementedError


class InMemoryStorage(BaseStorage):
    """In-memory storage backend."""

    def __init__(self):
        self.conversations: dict[str, dict[str, Any]] = {}
        self.messages: dict[str, list[Any]] = {}

    async def store_message(self, conversation_id: str, message: Any) -> bool:
        """Store a message in memory."""
        if conversation_id not in self.messages:
            self.messages[conversation_id] = []

        # Convert message to dict if needed
        if hasattr(message, 'to_dict'):
            msg_dict = message.to_dict()
        elif isinstance(message, dict):
            msg_dict = message
        else:
            msg_dict = {"content": str(message)}

        self.messages[conversation_id].append(msg_dict)
        return True

    async def retrieve_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> list[Any]:
        """Retrieve messages from memory."""
        if conversation_id not in self.messages:
            return []

        return self.messages[conversation_id][-limit:]

    async def create_conversation(
        self,
        conversation_id: str,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """Create a new conversation in memory."""
        if conversation_id in self.conversations:
            logger.warning(f"Conversation {conversation_id} already exists")
            return False

        self.conversations[conversation_id] = {
            "id": conversation_id,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {},
            "message_count": 0
        }

        if conversation_id not in self.messages:
            self.messages[conversation_id] = []

        return True

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        """Get conversation metadata from memory."""
        return self.conversations.get(conversation_id)

    async def list_conversations(self) -> list[dict[str, Any]]:
        """List all conversations from memory."""
        return list(self.conversations.values())

    async def clear(self):
        """Clear all stored data."""
        self.conversations.clear()
        self.messages.clear()


class FileStorage(BaseStorage):
    """File-based storage backend."""

    def __init__(self, storage_dir: str):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.conversations_dir = self.storage_dir / "conversations"
        self.conversations_dir.mkdir(exist_ok=True)
        self.messages_dir = self.storage_dir / "messages"
        self.messages_dir.mkdir(exist_ok=True)

    async def store_message(self, conversation_id: str, message: Any) -> bool:
        """Store a message in a file."""
        message_file = self.messages_dir / f"{conversation_id}.jsonl"

        # Convert message to dict
        if hasattr(message, 'to_dict'):
            msg_dict = message.to_dict()
        elif isinstance(message, dict):
            msg_dict = message
        else:
            msg_dict = {"content": str(message)}

        # Append to file
        try:
            with open(message_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(msg_dict) + '\n')
            return True
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            return False

    async def retrieve_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> list[Any]:
        """Retrieve messages from file."""
        message_file = self.messages_dir / f"{conversation_id}.jsonl"

        if not message_file.exists():
            return []

        messages = []
        try:
            with open(message_file, encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        messages.append(json.loads(line))

            return messages[-limit:] if limit else messages
        except Exception as e:
            logger.error(f"Failed to retrieve messages: {e}")
            return []

    async def create_conversation(
        self,
        conversation_id: str,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """Create a new conversation file."""
        conversation_file = self.conversations_dir / f"{conversation_id}.json"

        if conversation_file.exists():
            logger.warning(f"Conversation {conversation_id} already exists")
            return False

        data = {
            "id": conversation_id,
            "created_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        try:
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return False

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        """Get conversation metadata from file."""
        conversation_file = self.conversations_dir / f"{conversation_id}.json"

        if not conversation_file.exists():
            return None

        try:
            with open(conversation_file, encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None

    async def list_conversations(self) -> list[dict[str, Any]]:
        """List all conversations from files."""
        conversations = []

        try:
            for file_path in self.conversations_dir.glob("*.json"):
                with open(file_path, encoding='utf-8') as f:
                    conversations.append(json.load(f))
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")

        return conversations


class SQLiteStorage(BaseStorage):
    """SQLite-based storage backend."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._initialized = False

    async def _initialize(self):
        """Initialize the database."""
        if self._initialized:
            return

        try:
            import aiosqlite
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS conversations (
                        id TEXT PRIMARY KEY,
                        created_at TEXT NOT NULL,
                        metadata TEXT,
                        message_count INTEGER DEFAULT 0
                    )
                ''')
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        conversation_id TEXT NOT NULL,
                        role TEXT NOT NULL,
                        content TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (conversation_id) REFERENCES conversations(id)
                    )
                ''')
                await db.commit()

            self._initialized = True
            logger.info("SQLite storage initialized")
        except ImportError:
            logger.warning("aiosqlite not available, falling back to in-memory storage")
        except Exception as e:
            logger.error(f"Failed to initialize SQLite storage: {e}")

    async def store_message(self, conversation_id: str, message: Any) -> bool:
        """Store a message in SQLite."""
        await self._initialize()

        if not self._initialized:
            return False

        try:
            import aiosqlite

            # Extract message data
            if isinstance(message, dict):
                role = message.get("role", "user")
                content = message.get("content", str(message))
            elif hasattr(message, 'role'):
                role = message.role
                content = message.content
            else:
                role = "user"
                content = str(message)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    '''
                    INSERT INTO messages (conversation_id, role, content, created_at)
                    VALUES (?, ?, ?, ?)
                    ''',
                    (conversation_id, role, content, datetime.now().isoformat())
                )

                await db.execute(
                    '''
                    UPDATE conversations
                    SET message_count = message_count + 1
                    WHERE id = ?
                    ''',
                    (conversation_id,)
                )

                await db.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to store message: {e}")
            return False

    async def retrieve_messages(
        self,
        conversation_id: str,
        limit: int = 50
    ) -> list[Any]:
        """Retrieve messages from SQLite."""
        await self._initialize()

        if not self._initialized:
            return []

        try:
            import aiosqlite

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    '''
                    SELECT role, content, created_at
                    FROM messages
                    WHERE conversation_id = ?
                    ORDER BY id DESC
                    LIMIT ?
                    ''',
                    (conversation_id, limit)
                )
                rows = await cursor.fetchall()

                return [
                    {"role": row[0], "content": row[1], "created_at": row[2]}
                    for row in reversed(rows)
                ]
        except Exception as e:
            logger.error(f"Failed to retrieve messages: {e}")
            return []

    async def create_conversation(
        self,
        conversation_id: str,
        metadata: dict[str, Any] | None = None
    ) -> bool:
        """Create a new conversation in SQLite."""
        await self._initialize()

        if not self._initialized:
            return False

        try:
            import aiosqlite

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    '''
                    INSERT INTO conversations (id, created_at, metadata)
                    VALUES (?, ?, ?)
                    ''',
                    (conversation_id, datetime.now().isoformat(), json.dumps(metadata or {}))
                )
                await db.commit()

            return True
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            return False

    async def get_conversation(self, conversation_id: str) -> dict[str, Any] | None:
        """Get conversation metadata from SQLite."""
        await self._initialize()

        if not self._initialized:
            return None

        try:
            import aiosqlite

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    '''
                    SELECT id, created_at, metadata, message_count
                    FROM conversations
                    WHERE id = ?
                    ''',
                    (conversation_id,)
                )
                row = await cursor.fetchone()

                if row:
                    return {
                        "id": row[0],
                        "created_at": row[1],
                        "metadata": json.loads(row[2]) if row[2] else {},
                        "message_count": row[3]
                    }
                return None
        except Exception as e:
            logger.error(f"Failed to get conversation: {e}")
            return None

    async def list_conversations(self) -> list[dict[str, Any]]:
        """List all conversations from SQLite."""
        await self._initialize()

        if not self._initialized:
            return []

        try:
            import aiosqlite

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    '''
                    SELECT id, created_at, metadata, message_count
                    FROM conversations
                    ORDER BY created_at DESC
                    '''
                )
                rows = await cursor.fetchall()

                return [
                    {
                        "id": row[0],
                        "created_at": row[1],
                        "metadata": json.loads(row[2]) if row[2] else {},
                        "message_count": row[3]
                    }
                    for row in rows
                ]
        except Exception as e:
            logger.error(f"Failed to list conversations: {e}")
            return []


async def create_storage(
    storage_type: str = "memory",
    **kwargs
) -> BaseStorage:
    """Create a storage backend."""
    if storage_type == "memory":
        return InMemoryStorage()
    elif storage_type == "file":
        storage_dir = kwargs.get("storage_dir", "./data/agent_storage")
        return FileStorage(storage_dir)
    elif storage_type == "sqlite":
        db_path = kwargs.get("db_path", "./data/agent_storage.db")
        return SQLiteStorage(db_path)
    else:
        raise ValueError(f"Unsupported storage type: {storage_type}")
