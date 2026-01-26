"""Base connector interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

@dataclass
class ConnectorConfig:
    api_key: str
    base_url: str | None = None
    timeout: int = 30

@dataclass
class SyncResult:
    items_synced: int
    items_created: int
    items_updated: int
    errors: list[str]

class Connector(ABC):
    def __init__(self, config: ConnectorConfig):
        self.config = config
    
    @abstractmethod
    async def connect(self) -> bool:
        pass
    
    @abstractmethod
    async def sync(self) -> SyncResult:
        pass
    
    @abstractmethod
    async def fetch_items(self, limit: int = 100) -> list[dict[str, Any]]:
        pass
