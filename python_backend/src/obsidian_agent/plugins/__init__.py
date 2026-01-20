"""Extensible plugin system for obsidian-agent."""

from obsidian_agent.plugins.base import Plugin, PluginManager, PluginMetadata, PluginHook

__all__ = ["Plugin", "PluginManager", "PluginMetadata", "PluginHook"]
