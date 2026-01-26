"""Readwise connector for importing highlights."""

import logging
from typing import Any
from obsidian_agent.connectors.base import Connector, ConnectorConfig, SyncResult

logger = logging.getLogger(__name__)

class ReadwiseConnector(Connector):
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://readwise.io/api/v2"
        self._headers = {"Authorization": f"Token {config.api_key}"}
    
    async def connect(self) -> bool:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/auth", headers=self._headers)
                return resp.status_code == 204
        except Exception as e:
            logger.error(f"Readwise connection failed: {e}")
            return False
    
    async def sync(self) -> SyncResult:
        items = await self.fetch_items()
        return SyncResult(items_synced=len(items), items_created=len(items), items_updated=0, errors=[])
    
    async def fetch_items(self, limit: int = 100) -> list[dict[str, Any]]:
        return await self.fetch_highlights(limit)
    
    async def fetch_highlights(self, limit: int = 100) -> list[dict[str, Any]]:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/highlights", headers=self._headers, params={"page_size": limit})
                if resp.status_code == 200:
                    return resp.json().get("results", [])
        except Exception as e:
            logger.error(f"Readwise fetch failed: {e}")
        return []
    
    async def fetch_books(self, limit: int = 100) -> list[dict[str, Any]]:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/books", headers=self._headers, params={"page_size": limit})
                if resp.status_code == 200:
                    return resp.json().get("results", [])
        except Exception as e:
            logger.error(f"Readwise books fetch failed: {e}")
        return []
