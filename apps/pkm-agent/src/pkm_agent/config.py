"""Configuration management for PKM Agent."""

from __future__ import annotations

from pathlib import Path
from typing import Literal
import os

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LLMConfig(BaseSettings):
    """LLM provider configuration."""
    model_config = SettingsConfigDict(populate_by_name=True)

    provider: Literal["openai", "ollama", "anthropic"] = "openai"
    model: str = "gpt-4o-mini"
    api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    base_url: str | None = None
    temperature: float = 0.7
    max_tokens: int = 2048
    streaming: bool = True


class RAGConfig(BaseSettings):
    """RAG engine configuration."""
    model_config = SettingsConfigDict(populate_by_name=True)

    embedding_model: str = "all-MiniLM-L6-v2"
    chunk_size: int = 512
    chunk_overlap: int = 64
    top_k: int = 5
    similarity_threshold: float = 0.7


class TUIConfig(BaseSettings):
    """TUI configuration."""

    theme: str = "tokyo-night"
    show_timestamps: bool = True
    show_sources: bool = True
    vim_mode: bool = False
    max_history: int = 100


DEFAULT_PKM_ROOT = Path(os.environ.get("PKM_ROOT", Path(__file__).resolve().parents[3] / "pkm"))


class Config(BaseSettings):
    """Main application configuration."""

    model_config = SettingsConfigDict(
        env_prefix="PKMA_",
        env_file=".env",
        env_nested_delimiter="__",
        extra="ignore"
    )

    # Paths
    pkm_root: Path = Field(default_factory=lambda: DEFAULT_PKM_ROOT)
    data_dir: Path = Field(default_factory=lambda: Path.cwd() / ".pkm-agent")

    # Sub-configs
    llm: LLMConfig = Field(default_factory=LLMConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    tui: TUIConfig = Field(default_factory=TUIConfig)

    # General
    log_level: str = "INFO"
    log_format: str = "text"
    log_file: Path | None = None
    debug: bool = False

    @property
    def db_path(self) -> Path:
        """Path to SQLite database."""
        return self.data_dir / "pkm_agent.db"

    @property
    def chroma_path(self) -> Path:
        """Path to ChromaDB storage."""
        return self.data_dir / "chroma"

    @property
    def cache_path(self) -> Path:
        """Path to cache directory."""
        return self.data_dir / "cache"

    def ensure_dirs(self) -> None:
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        self.cache_path.mkdir(parents=True, exist_ok=True)


def load_config(config_path: Path | None = None) -> Config:
    """Load configuration from file and environment."""
    if config_path and config_path.exists():
        import toml
        data = toml.load(config_path)
        
        # Handle nested configs
        config_kwargs = {}
        
        # General settings
        if "general" in data:
            general = data["general"]
            if "pkm_root" in general:
                config_kwargs["pkm_root"] = Path(general["pkm_root"]).expanduser()
            if "data_dir" in general:
                config_kwargs["data_dir"] = Path(general["data_dir"]).expanduser()
        
        # LLM config
        if "llm" in data:
            config_kwargs["llm"] = LLMConfig(**data["llm"])
        
        # RAG config
        if "rag" in data:
            config_kwargs["rag"] = RAGConfig(**data["rag"])
        
        # TUI config
        if "tui" in data:
            config_kwargs["tui"] = TUIConfig(**data["tui"])
        
        return Config(**config_kwargs)
    return Config()
