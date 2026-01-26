"""Configuration management using Pydantic"""

from pathlib import Path
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class VaultConfig(BaseSettings):
    """Vault configuration"""

    path: Path = Field(..., description="Path to Obsidian vault")
    exclude_folders: List[str] = Field(
        default=[".obsidian", "templates", "_archive"],
        description="Folders to exclude from indexing",
    )
    exclude_patterns: List[str] = Field(
        default=["*.tmp", "*.bak"], description="File patterns to exclude"
    )


class DatabaseConfig(BaseSettings):
    """Database configuration"""

    path: Path = Field(
        default=Path.home() / ".local/share/obsidian-agent/vault.db",
        description="Path to SQLite database",
    )
    backup_enabled: bool = Field(default=True, description="Enable automatic backups")
    backup_interval_hours: int = Field(default=24, description="Backup interval in hours")
    connection_pool_size: int = Field(default=5, description="Connection pool size")


class VectorStoreConfig(BaseSettings):
    """Vector store configuration"""

    provider: str = Field(default="chromadb", description="Vector store provider")
    embedding_model: str = Field(
        default="all-MiniLM-L6-v2", description="Sentence transformer model"
    )
    collection_name: str = Field(default="obsidian_notes", description="Collection name")
    persist_directory: Path = Field(
        default=Path.home() / ".local/share/obsidian-agent/chroma",
        description="ChromaDB persist directory",
    )
    batch_size: int = Field(default=100, description="Batch size for embeddings")


class SearchConfig(BaseSettings):
    """Search configuration"""

    default_limit: int = Field(default=10, description="Default number of results")
    semantic_threshold: float = Field(
        default=0.7, description="Semantic similarity threshold (0-1)"
    )
    enable_reranking: bool = Field(default=True, description="Enable result reranking")


class IndexingConfig(BaseSettings):
    """Indexing configuration"""

    batch_size: int = Field(default=100, description="Files to process per batch")
    max_file_size_mb: int = Field(default=10, description="Max file size to index (MB)")
    update_interval_seconds: int = Field(
        default=300, description="Interval for incremental updates"
    )


class ObsidianAgentConfig(BaseSettings):
    """Main configuration"""

    model_config = SettingsConfigDict(
        env_prefix="OBSIDIAN_",
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
    )

    vault: VaultConfig = Field(default_factory=VaultConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    vector_store: VectorStoreConfig = Field(default_factory=VectorStoreConfig)
    search: SearchConfig = Field(default_factory=SearchConfig)
    indexing: IndexingConfig = Field(default_factory=IndexingConfig)

    @classmethod
    def from_file(cls, config_path: Path) -> "ObsidianAgentConfig":
        """Load configuration from file"""
        import yaml

        with open(config_path) as f:
            config_data = yaml.safe_load(f)
        return cls(**config_data)

    def save_to_file(self, config_path: Path) -> None:
        """Save configuration to file"""
        import yaml

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(self.model_dump(), f, default_flow_style=False)
