"""Configuration settings for Obsidian MCP Server."""

from functools import lru_cache
from typing import Optional
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # Obsidian API Configuration
    obsidian_api_token: str
    obsidian_api_url: str = "http://127.0.0.1:27123"
    
    # Vault Configuration
    vault_path: Optional[str] = None
    
    # Server Configuration
    server_name: str = "obsidian-mcp"
    server_host: str = "127.0.0.1"
    server_port: int = 8000
    
    # Logging
    log_level: str = "INFO"
    debug: bool = False
    
    # Feature Flags
    enable_graph_analysis: bool = True
    enable_templates: bool = True
    enable_canvas: bool = True
    
    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v_upper = v.upper()
        if v_upper not in valid_levels:
            raise ValueError(f"Invalid log level: {v}")
        return v_upper


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
