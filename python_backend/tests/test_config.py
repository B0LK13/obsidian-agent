"""Tests for configuration"""

import pytest
from pathlib import Path
from obsidian_agent.config import ObsidianAgentConfig, VaultConfig


def test_default_config():
    """Test default configuration"""
    config = ObsidianAgentConfig()
    assert config.database.backup_enabled is True
    assert config.vector_store.provider == "chromadb"
    assert config.search.default_limit == 10


def test_vault_config():
    """Test vault configuration"""
    vault = VaultConfig(path=Path("/test/vault"))
    assert vault.path == Path("/test/vault")
    assert ".obsidian" in vault.exclude_folders


# TODO: Add more tests
