"""Multi-vault management for cross-vault search and operations."""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator

from obsidian_agent.indexing.parser import MarkdownParser
from obsidian_agent.indexing.indexer import VaultIndexer
from obsidian_agent.vector_store.chromadb_store import ChromaDBStore
from obsidian_agent.search.search_service import SearchService

logger = logging.getLogger(__name__)


@dataclass
class VaultConfig:
    """Configuration for a single vault."""
    name: str
    path: Path
    enabled: bool = True
    color: str = "#7c3aed"
    icon: str = "vault"
    tags: list[str] = field(default_factory=list)
    sync_enabled: bool = True
    last_indexed: datetime | None = None
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "path": str(self.path),
            "enabled": self.enabled,
            "color": self.color,
            "icon": self.icon,
            "tags": self.tags,
            "sync_enabled": self.sync_enabled,
            "last_indexed": self.last_indexed.isoformat() if self.last_indexed else None,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VaultConfig":
        data["path"] = Path(data["path"])
        if data.get("last_indexed"):
            data["last_indexed"] = datetime.fromisoformat(data["last_indexed"])
        return cls(**data)


@dataclass
class VaultInfo:
    """Runtime information about a vault."""
    config: VaultConfig
    note_count: int = 0
    total_words: int = 0
    total_links: int = 0
    indexer: VaultIndexer | None = None
    search_service: SearchService | None = None
    is_online: bool = True


@dataclass
class CrossVaultSearchResult:
    """Search result with vault context."""
    vault_name: str
    note_id: str
    title: str
    path: str
    score: float
    snippet: str
    tags: list[str] = field(default_factory=list)


class VaultManager:
    """Manages multiple Obsidian vaults with cross-vault search."""
    
    def __init__(self, config_path: Path, data_dir: Path):
        self.config_path = Path(config_path)
        self.data_dir = Path(data_dir)
        self.vaults: dict[str, VaultInfo] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load vault configurations from file."""
        if self.config_path.exists():
            try:
                data = json.loads(self.config_path.read_text())
                for vault_data in data.get("vaults", []):
                    config = VaultConfig.from_dict(vault_data)
                    self.vaults[config.name] = VaultInfo(config=config)
            except Exception as e:
                logger.error(f"Failed to load vault config: {e}")
    
    def _save_config(self) -> None:
        """Save vault configurations to file."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "vaults": [v.config.to_dict() for v in self.vaults.values()]
        }
        self.config_path.write_text(json.dumps(data, indent=2))
    
    async def add_vault(self, name: str, path: Path, **kwargs) -> VaultInfo:
        """Add a new vault."""
        if name in self.vaults:
            raise ValueError(f"Vault '{name}' already exists")
        
        path = Path(path)
        if not path.exists():
            raise ValueError(f"Vault path does not exist: {path}")
        
        config = VaultConfig(name=name, path=path, **kwargs)
        vault_info = VaultInfo(config=config)
        
        # Initialize vault services
        await self._init_vault_services(vault_info)
        
        self.vaults[name] = vault_info
        self._save_config()
        
        logger.info(f"Added vault: {name} at {path}")
        return vault_info
    
    async def remove_vault(self, name: str) -> None:
        """Remove a vault."""
        if name not in self.vaults:
            raise ValueError(f"Vault '{name}' not found")
        
        del self.vaults[name]
        self._save_config()
        logger.info(f"Removed vault: {name}")
    
    async def _init_vault_services(self, vault_info: VaultInfo) -> None:
        """Initialize indexer and search services for a vault."""
        vault_data_dir = self.data_dir / vault_info.config.name
        vault_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create vector store for this vault
        vector_store = ChromaDBStore(
            persist_directory=str(vault_data_dir / "chromadb"),
            collection_name=f"vault_{vault_info.config.name}",
        )
        await vector_store.initialize()
        
        # Create parser and indexer
        parser = MarkdownParser(vault_info.config.path)
        vault_info.indexer = VaultIndexer(vector_store, parser)
        vault_info.search_service = SearchService(vector_store, parser)
    
    async def index_vault(self, name: str, full_reindex: bool = False) -> dict[str, Any]:
        """Index a specific vault."""
        if name not in self.vaults:
            raise ValueError(f"Vault '{name}' not found")
        
        vault = self.vaults[name]
        if vault.indexer is None:
            await self._init_vault_services(vault)
        
        result = await vault.indexer.index_vault(full_reindex=full_reindex)
        vault.config.last_indexed = datetime.now()
        self._save_config()
        
        return result
    
    async def index_all(self, full_reindex: bool = False) -> dict[str, dict[str, Any]]:
        """Index all enabled vaults."""
        results = {}
        for name, vault in self.vaults.items():
            if vault.config.enabled:
                try:
                    results[name] = await self.index_vault(name, full_reindex)
                except Exception as e:
                    logger.error(f"Failed to index vault {name}: {e}")
                    results[name] = {"error": str(e)}
        return results
    
    async def search(
        self,
        query: str,
        vault_names: list[str] | None = None,
        limit: int = 10,
        threshold: float = 0.3,
    ) -> list[CrossVaultSearchResult]:
        """Search across multiple vaults."""
        results: list[CrossVaultSearchResult] = []
        
        target_vaults = vault_names or list(self.vaults.keys())
        
        for name in target_vaults:
            if name not in self.vaults:
                continue
            
            vault = self.vaults[name]
            if not vault.config.enabled or vault.search_service is None:
                continue
            
            try:
                vault_results = await vault.search_service.search(
                    query=query,
                    limit=limit,
                    threshold=threshold,
                )
                
                for r in vault_results:
                    results.append(CrossVaultSearchResult(
                        vault_name=name,
                        note_id=r.get("id", ""),
                        title=r.get("title", ""),
                        path=r.get("path", ""),
                        score=r.get("score", 0.0),
                        snippet=r.get("snippet", ""),
                        tags=r.get("tags", []),
                    ))
            except Exception as e:
                logger.error(f"Search failed in vault {name}: {e}")
        
        # Sort by score and limit
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    async def find_cross_vault_links(
        self,
        note_id: str,
        source_vault: str,
    ) -> list[CrossVaultSearchResult]:
        """Find related notes across all vaults."""
        if source_vault not in self.vaults:
            raise ValueError(f"Vault '{source_vault}' not found")
        
        source = self.vaults[source_vault]
        if source.search_service is None:
            return []
        
        # Get note content
        note_content = await source.search_service.get_note_content(note_id)
        if not note_content:
            return []
        
        # Search across all other vaults
        results = await self.search(
            query=note_content[:500],  # Use first 500 chars as query
            vault_names=[n for n in self.vaults if n != source_vault],
            limit=10,
        )
        
        return results
    
    def list_vaults(self) -> list[VaultInfo]:
        """List all configured vaults."""
        return list(self.vaults.values())
    
    def get_vault(self, name: str) -> VaultInfo | None:
        """Get a specific vault."""
        return self.vaults.get(name)
    
    async def get_stats(self) -> dict[str, Any]:
        """Get statistics for all vaults."""
        stats = {
            "total_vaults": len(self.vaults),
            "enabled_vaults": sum(1 for v in self.vaults.values() if v.config.enabled),
            "vaults": {},
        }
        
        for name, vault in self.vaults.items():
            stats["vaults"][name] = {
                "enabled": vault.config.enabled,
                "path": str(vault.config.path),
                "note_count": vault.note_count,
                "last_indexed": vault.config.last_indexed.isoformat() if vault.config.last_indexed else None,
            }
        
        return stats
