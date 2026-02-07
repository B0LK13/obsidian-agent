"""
WebSocket-based Synchronization System for PKM Agent.

Provides bidirectional real-time synchronization between Python backend
and Obsidian plugin via WebSocket protocol.
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

logger = logging.getLogger(__name__)


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
    """Base sync event for communication between components."""
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


class SyncServer:
    """WebSocket server for real-time synchronization."""

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
        """Register a handler for specific event type."""
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
            self._heartbeat_task = asyncio.create_task(self._send_heartbeats())
            logger.info("Sync server started successfully")

        except Exception as e:
            logger.error(f"Failed to start sync server: {e}")
            raise

    async def stop(self):
        """Stop the WebSocket server."""
        if not self.running:
            return

        logger.info("Stopping sync server...")
        self.running = False

        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass

        if self.clients:
            await asyncio.gather(
                *[client.close() for client in self.clients],
                return_exceptions=True
            )

        if self._server:
            self._server.close()
            await self._server.wait_closed()

        logger.info("Sync server stopped")

    async def handle_client(self, websocket: ServerConnection, *args):
        """Handle individual client connection."""
        client_id = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"Client connected: {client_id}")

        self.clients.add(websocket)

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
            await self.broadcast_event(SyncEvent(
                event_type=SyncEventType.CLIENT_DISCONNECTED,
                source="python",
                data={"client_id": client_id}
            ))

    async def _process_message(self, websocket: ServerConnection, message: str, client_id: str):
        """Process incoming message from client."""
        try:
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

            handler = self.event_handlers.get(event.event_type)
            if handler:
                try:
                    await handler(event)
                except Exception as e:
                    logger.error(f"Handler error for {event.event_type.value}: {e}")
                    await self._send_error(websocket, event, str(e))
                    return

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

        except Exception as e:
            logger.error(f"Error processing message from {client_id}: {e}")
            await self._send_error(websocket, None, str(e))

    async def _send_error(self, websocket: ServerConnection, original_event, error_message: str):
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

    async def broadcast_event(self, event, data=None, exclude=None):
        """Broadcast event to all connected clients."""
        if not self.clients:
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

        results = await asyncio.gather(
            *[client.send(message) for client in target_clients],
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Failed to send to client: {result}")

    async def broadcast_file_created(self, filepath: str):
        """Broadcast file created event."""
        await self.broadcast_event(SyncEvent(
            event_type=SyncEventType.FILE_CREATED,
            source="python",
            data={"filepath": filepath}
        ))

    async def broadcast_file_modified(self, filepath: str):
        """Broadcast file modified event."""
        await self.broadcast_event(SyncEvent(
            event_type=SyncEventType.FILE_MODIFIED,
            source="python",
            data={"filepath": filepath}
        ))

    async def broadcast_file_deleted(self, filepath: str):
        """Broadcast file deleted event."""
        await self.broadcast_event(SyncEvent(
            event_type=SyncEventType.FILE_DELETED,
            source="python",
            data={"filepath": filepath}
        ))

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

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error sending heartbeat: {e}")

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
