"""Notion connector for importing pages."""

import logging
from typing import Any
from obsidian_agent.connectors.base import Connector, ConnectorConfig, SyncResult

logger = logging.getLogger(__name__)

class NotionConnector(Connector):
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self.base_url = config.base_url or "https://api.notion.com/v1"
        self._headers = {"Authorization": f"Bearer {config.api_key}", "Notion-Version": "2022-06-28"}
    
    async def connect(self) -> bool:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/users/me", headers=self._headers)
                return resp.status_code == 200
        except Exception as e:
            logger.error(f"Notion connection failed: {e}")
            return False
    
    async def sync(self) -> SyncResult:
        items = await self.fetch_items()
        return SyncResult(items_synced=len(items), items_created=len(items), items_updated=0, errors=[])
    
    async def fetch_items(self, limit: int = 100) -> list[dict[str, Any]]:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.post(f"{self.base_url}/search", headers=self._headers, json={"page_size": limit})
                if resp.status_code == 200:
                    return resp.json().get("results", [])
        except Exception as e:
            logger.error(f"Notion fetch failed: {e}")
        return []
    
    async def get_page(self, page_id: str) -> dict[str, Any] | None:
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self.base_url}/pages/{page_id}", headers=self._headers)
                if resp.status_code == 200:
                    return resp.json()
        except Exception as e:
            logger.error(f"Notion get page failed: {e}")
        return None
