"""WebSocket synchronization server for real-time vault updates"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Set, Optional, Union
import websockets
from websockets.server import serve, WebSocketServerProtocol

logger = logging.getLogger(__name__)


class SyncEventType(str, Enum):
    """Event types for synchronization
    
    Fixed for Issue #86: Added INDEX_UPDATED event type
    """
    FILE_CREATED = "file_created"
    FILE_MODIFIED = "file_modified"
    FILE_DELETED = "file_deleted"
    FILE_MOVED = "file_moved"
    INDEX_UPDATED = "index_updated"  # Fix for Issue #86
    SYNC_STARTED = "sync_started"
    SYNC_COMPLETED = "sync_completed"
    ERROR = "error"


@dataclass
class SyncEvent:
    """Represents a synchronization event"""
    event_type: SyncEventType
    data: Dict[str, Any]
    timestamp: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization
        
        Fixed for Issue #86: Includes both 'type' and 'event_type' for compatibility
        """
        result = {
            "type": self.event_type.value,  # Fix for Issue #86: Add 'type' field
            "event_type": self.event_type.value,
            "data": self.data,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }
        return result


class SyncServer:
    """WebSocket server for real-time synchronization
    
    Fixed for Issue #85: Handler signature compatible with websockets>=12
    Fixed for Issue #86: broadcast_event accepts both SyncEvent and (event_type, data)
    """
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self._server: Optional[Any] = None
    
    async def start(self) -> None:
        """Start the WebSocket server"""
        # Fix for Issue #85: Use handler signature compatible with websockets>=12
        # In websockets>=12, handler is called with only 'connection' parameter
        self._server = await serve(
            self.handle_client,  # Handler called with only connection
            self.host,
            self.port,
        )
        logger.info(f"WebSocket server started on {self.host}:{self.port}")
    
    async def stop(self) -> None:
        """Stop the WebSocket server"""
        if self._server:
            self._server.close()
            await self._server.wait_closed()
            logger.info("WebSocket server stopped")
    
    async def handle_client(self, connection: WebSocketServerProtocol) -> None:
        """Handle a client connection
        
        Fixed for Issue #85: Handler signature for websockets>=12
        The path can be obtained from connection.path instead of a separate parameter
        """
        # Register client
        self.clients.add(connection)
        client_path = connection.path  # Get path from connection object
        logger.info(f"Client connected from {client_path}")
        
        try:
            # Send welcome message
            welcome_event = SyncEvent(
                event_type=SyncEventType.SYNC_STARTED,
                data={"message": "Connected to PKM sync server"},
            )
            await connection.send(json.dumps(welcome_event.to_dict()))
            
            # Handle incoming messages
            async for message in connection:
                try:
                    data = json.loads(message)
                    await self._handle_message(connection, data)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON from client: {e}")
                except Exception as e:
                    logger.error(f"Error handling message: {e}")
        
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        finally:
            # Unregister client
            self.clients.discard(connection)
    
    async def _handle_message(
        self,
        connection: WebSocketServerProtocol,
        data: Dict[str, Any],
    ) -> None:
        """Handle incoming message from client"""
        # Echo back for now
        await connection.send(json.dumps({"status": "received", "data": data}))
    
    async def broadcast_event(
        self,
        event: Union[SyncEvent, SyncEventType],
        data: Optional[Dict[str, Any]] = None,
        exclude: Optional[Set[WebSocketServerProtocol]] = None,
    ) -> None:
        """Broadcast an event to all connected clients
        
        Fixed for Issue #86: Accepts either SyncEvent object or (event_type, data) arguments
        
        Args:
            event: Either a SyncEvent object or a SyncEventType
            data: Optional data dict (required when event is SyncEventType)
            exclude: Optional set of clients to exclude from broadcast
        
        Raises:
            TypeError: If event type is invalid or data is missing for SyncEventType
        """
        # Fix for Issue #86: Handle both SyncEvent and (event_type, data) calling patterns
        if isinstance(event, SyncEvent):
            sync_event = event
        elif isinstance(event, SyncEventType):
            # Validate that data is provided when using SyncEventType
            if data is None:
                raise TypeError(
                    "data parameter is required when event is SyncEventType"
                )
            # Create SyncEvent from event_type and data
            sync_event = SyncEvent(event_type=event, data=data)
        else:
            raise TypeError(
                f"event must be SyncEvent or SyncEventType, got {type(event)}"
            )
        
        # Determine which clients to send to
        if exclude is None:
            exclude = set()
        
        targets = self.clients - exclude
        
        if targets:
            message = json.dumps(sync_event.to_dict())
            # Broadcast to all target clients
            await asyncio.gather(
                *[client.send(message) for client in targets],
                return_exceptions=True,
            )
            logger.debug(f"Broadcasted {sync_event.event_type} to {len(targets)} clients")
