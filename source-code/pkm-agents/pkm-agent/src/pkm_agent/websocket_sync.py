"""
WebSocket-based Synchronization System for PKM Agent.

Provides bidirectional real-time synchronization between Python backend
and Obsidian plugin via WebSocket protocol.

This module combines:
- Sync event models
- WebSocket server
- Event broadcasting
- Client connection management
"""

import asyncio
import json
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import websockets
from websockets import ServerConnection

from pkm_agent.exceptions import NetworkError, SyncProtocolError

logger = logging.getLogger(__name__)


# ============================================
# SYNC EVENT MODELS
# ============================================

class SyncEventType(Enum):
    """Types of sync events."""
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_RENAMED = "file_renamed"
    NOTE_INDEXED = "note_indexed"
    INDEX_UPDATED = "index_updated"
    EMBEDDING_UPDATED = "embedding_updated"
    SYNC_REQUEST = "sync_request"
    SYNC_RESPONSE = "sync_response"
    SYNC_ERROR = "sync_error"
    HEARTBEAT = "heartbeat"
    HEALTH_CHECK = "health_check"
    CLIENT_CONNECTED = "client_connected"
    CLIENT_DISCONNECTED = "client_disconnected"


@dataclass
class SyncEvent:
    """
    Base sync event for communication between components.

    Attributes:
        event_type: Type of sync event
        source: Component that generated the event ('python' or 'obsidian')
        data: Event-specific data payload
        event_id: Unique identifier for this event
        timestamp: When the event occurred (Unix timestamp)
        metadata: Additional context information
    """
    event_type: SyncEventType
    source: str
    data: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value if isinstance(self.event_type, Enum) else self.event_type,
            "timestamp": self.timestamp,
            "source": self.source,
            "data": self.data,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> 'SyncEvent':
        """Create SyncEvent from dictionary."""
        event_type_str = data.get("event_type")
        try:
            event_type = SyncEventType(event_type_str)
        except ValueError:
            event_type = event_type_str

        return cls(
            event_id=data.get("event_id", str(uuid.uuid4())),
            event_type=event_type,
            timestamp=data.get("timestamp", datetime.now().timestamp()),
            source=data.get("source", "unknown"),
            data=data.get("data", {}),
            metadata=data.get("metadata", {})
        )


# ============================================
# WEBSOCKET SERVER
# ============================================

class SyncServer:
    """
    WebSocket server for real-time synchronization.

    Manages client connections and broadcasts sync events between
    Python backend and Obsidian plugin instances.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 27125,
        heartbeat_interval: float = 30.0
    ):
        self.host = host
        self.port = port
        self.heartbeat_interval = heartbeat_interval

        self.clients: set[ServerConnection] = set()
        self.event_handlers: dict[SyncEventType, Callable] = {}
        self.running = False
        self._server = None
        self._heartbeat_task = None

        logger.info(f"Sync server initialized for ws://{host}:{port}")

    def register_handler(self, event_type: SyncEventType, handler: Callable):
        """
        Register a handler for specific event type.

        Args:
            event_type: Type of event to handle
            handler: Async function to call when event received
        """
        self.event_handlers[event_type] = handler
        logger.debug(f"Registered handler for {event_type.value}")

    async def start(self):
        """Start the WebSocket server."""
        if self.running:
            logger.warning("Sync server already running")
            return

        logger.info(f"Starting sync server on ws://{self.host}:{self.port}")

        try:
            self._server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port
            )

            self.running = True

            # Start heartbeat task
            self._heartbeat_task = asyncio.create_task(self._send_heartbeats())

            logger.info("Sync server started successfully")

        except Exception as e:
            logger.error(f"Failed to start sync server: {e}")
            raise NetworkError(
                f"Cannot start sync server on {self.host}:{self.port}",
                context={"error": str(e)}
            ) from e

    async def stop(self):
        """Stop the WebSocket server."""
        if not self.running:
            return

        logger.info("Stopping sync server...")

        self.running = False

        # Cancel heartbeat
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        # Close all client connections
        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients],
                return_exceptions=True
            )

        # Close server
        if self._server:
            self._server.close()
            await self._server.wait_closed()

        logger.info("Sync server stopped")

    async def handle_client(
        self,
        websocket: ServerConnection,
        *args
    ):
        """
        Handle individual client connection.

        Args:
            websocket: WebSocket connection
            *args: Additional arguments (path in older websockets, ignored now)
        """
        path = args[0] if args else None
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client connected: {client_id}")

        self.clients.add(websocket)

        # Notify other clients
        await self.broadcast_event(SyncEvent(
            event_type=SyncEventType.CLIENT_CONNECTED,
            source="python",
            data={"client_id": client_id}
        ), exclude={websocket})

        try:
            async for message in websocket:
                await self._process_message(websocket, message, client_id)

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {client_id}")

        except Exception as e:
            logger.error(f"Error handling client {client_id}: {e}", exc_info=True)

        finally:
            self.clients.discard(websocket)

            # Notify other clients
            await self.broadcast_event(SyncEvent(
                event_type=SyncEventType.CLIENT_DISCONNECTED,
                source="python",
                data={"client_id": client_id}
            ))

    async def _process_message(
        self,
        websocket: ServerConnection,
        message: str,
        client_id: str
    ):
        """
        Process incoming message from client.

        Args:
            websocket: Client websocket
            message: Raw message string
            client_id: Client identifier
        """
        try:
            # Parse message
            data = json.loads(message)
            if data.get("type") == "ping":
                await websocket.send(json.dumps({"type": "pong"}))
                return

            event = SyncEvent.from_dict(data)

            if event.event_type == SyncEventType.HEALTH_CHECK:
                await websocket.send(json.dumps(SyncEvent(
                    event_type=SyncEventType.SYNC_RESPONSE,
                    source="python",
                    data={
                        "status": "healthy",
                        "server_time": datetime.now().isoformat(),
                        "stats": self.get_stats()
                    },
                    metadata={"reply_to": event.event_id}
                ).to_dict()))
                return

            event_label = (
                event.event_type.value
                if isinstance(event.event_type, SyncEventType)
                else str(event.event_type)
            )
            logger.debug(f"Received {event_label} from {client_id}")

            # Call registered handler if exists
            handler = self.event_handlers.get(event.event_type)
            if handler:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type.value}: {e}")
                    await self._send_error(websocket, event, str(e))
                    return

            # Send acknowledgment
            response = SyncEvent(
                event_type=SyncEventType.SYNC_RESPONSE,
                source="python",
                data={
                    "status": "ok",
                    "event_id": event.event_id,
                    "processed_at": datetime.now().isoformat()
                }
            )
            await websocket.send(json.dumps(response.to_dict()))

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON from {client_id}: {e}")
            raise SyncProtocolError(f"Invalid JSON: {e}")

        except Exception as e:
            logger.error(f"Error processing message from {client_id}: {e}")
            await self._send_error(websocket, None, str(e))

    async def _send_error(
        self,
        websocket: ServerConnection,
        original_event: SyncEvent | None,
        error_message: str
    ):
        """Send error event to client."""
        error_event = SyncEvent(
            event_type=SyncEventType.SYNC_ERROR,
            source="python",
            data={
                "error_message": error_message,
                "error_type": "processing_error",
                "related_event_id": original_event.event_id if original_event else None
            }
        )

        try:
            await websocket.send(json.dumps(error_event.to_dict()))
        except Exception as e:
            logger.error(f"Failed to send error to client: {e}")

    async def broadcast_event(
        self,
        event: SyncEvent | SyncEventType | str,
        data: dict[str, Any] | None = None,
        exclude: set[ServerConnection] | None = None
    ):
        """
        Broadcast event to all connected clients.

        Args:
            event: Event or event type to broadcast
            data: Optional payload when passing an event type
            exclude: Set of clients to exclude from broadcast
        """
        if not self.clients:
            logger.debug("No clients connected, skipping broadcast")
            return

        if not isinstance(event, SyncEvent):
            event = SyncEvent(
                event_type=event,
                source="python",
                data=data or {}
            )

        exclude = exclude or set()
        target_clients = self.clients - exclude

        if not target_clients:
            return

        message = json.dumps(event.to_dict())
        event_label = (
            event.event_type.value
            if isinstance(event.event_type, SyncEventType)
            else str(event.event_type)
        )
        logger.debug(f"Broadcasting {event_label} to {len(target_clients)} clients")

        # Send to all clients concurrently
        results = await asyncio.gather(
            *[client.send(message) for client in target_clients],
            return_exceptions=True
        )

        # Log any errors
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Failed to send to client: {result}")

    async def _send_heartbeats(self):
        """Periodically send heartbeat to keep connections alive."""
        while self.running:
            try:
                await asyncio.sleep(self.heartbeat_interval)

                if self.clients:
                    heartbeat = SyncEvent(
                        event_type=SyncEventType.HEARTBEAT,
                        source="python",
                        data={"server_time": datetime.now().isoformat()}
                    )

                    await self.broadcast_event(heartbeat)
                    logger.debug(f"Sent heartbeat to {len(self.clients)} clients")

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")

    async def send_to_client(
        self,
        client: ServerConnection,
        event: SyncEvent
    ):
        """
        Send event to specific client.

        Args:
            client: Target client
            event: Event to send
        """
        try:
            message = json.dumps(event.to_dict())
            await client.send(message)
        except Exception as e:
            logger.error(f"Failed to send to client: {e}")
            raise NetworkError(f"Failed to send event: {e}") from e

    def get_stats(self) -> dict[str, Any]:
        """Get server statistics."""
        return {
            "running": self.running,
            "host": self.host,
            "port": self.port,
            "connected_clients": len(self.clients),
            "registered_handlers": len(self.event_handlers),
            "heartbeat_interval": self.heartbeat_interval
        }


# ============================================
# INTEGRATION HELPERS
# ============================================

class SyncServerIntegration:
    """
    Helper class to integrate SyncServer with FileIndexer and PKMAgentApp.
    """

    def __init__(self, sync_server: SyncServer, pkm_app):
        self.sync_server = sync_server
        self.app = pkm_app

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self):
        """Register handlers for incoming events from Obsidian."""
        self.sync_server.register_handler(
            SyncEventType.FILE_MODIFIED,
            self._handle_file_modified
        )
        self.sync_server.register_handler(
            SyncEventType.FILE_CREATED,
            self._handle_file_created
        )
        self.sync_server.register_handler(
            SyncEventType.FILE_DELETED,
            self._handle_file_deleted
        )
        self.sync_server.register_handler(
            SyncEventType.SYNC_REQUEST,
            self._handle_sync_request
        )

    async def _handle_file_modified(self, event: SyncEvent):
        """Handle file modification from Obsidian."""
        filepath = Path(event.data.get("filepath"))

        logger.info(f"Syncing file modification: {filepath}")

        # Reindex the file
        note = await self.app.indexer.index_file(
            self.app.config.pkm_root / filepath
        )

        if note:
            # Update embeddings
            chunks = self.app.chunker.chunk_note(note)
            self.app.vectorstore.delete_note_chunks(note.id)
            self.app.vectorstore.add_chunks(chunks)

            # Broadcast indexed event
            await self.sync_server.broadcast_event(SyncEvent(
                event_type=SyncEventType.NOTE_INDEXED,
                source="python",
                data={
                    "filepath": str(filepath),
                    "note_id": note.id,
                    "title": note.title
                }
            ))

    async def _handle_file_created(self, event: SyncEvent):
        """Handle file creation from Obsidian."""
        await self._handle_file_modified(event)  # Same process

    async def _handle_file_deleted(self, event: SyncEvent):
        """Handle file deletion from Obsidian."""
        filepath = event.data.get("filepath")

        logger.info(f"Syncing file deletion: {filepath}")

        # Remove from database
        note = self.app.db.get_note_by_path(filepath)
        if note:
            self.app.vectorstore.delete_note_chunks(note.id)
            self.app.db.delete_note(note.id)

    async def _handle_sync_request(self, event: SyncEvent):
        """Handle sync request from Obsidian."""
        resource_type = event.data.get("resource_type")

        logger.info(f"Sync request for: {resource_type}")

        if resource_type == "stats":
            stats = await self.app.get_stats()

            await self.sync_server.broadcast_event(SyncEvent(
                event_type=SyncEventType.SYNC_RESPONSE,
                source="python",
                data={
                    "request_id": event.event_id,
                    "status": "ok",
                    "resource_type": resource_type,
                    "stats": stats
                }
            ))


# ============================================
# USAGE EXAMPLE
# ============================================

if __name__ == "__main__":
    async def main():
        # Create server
        server = SyncServer(host="localhost", port=27125)

        # Register custom handler
        async def handle_custom_event(event: SyncEvent):
            print(f"Received event: {event.event_type}")

        server.register_handler(SyncEventType.FILE_MODIFIED, handle_custom_event)

        # Start server
        await server.start()

        # Run forever
        try:
            await asyncio.Future()
        except KeyboardInterrupt:
            await server.stop()

    asyncio.run(main())

