"""Base plugin system with hooks and lifecycle management."""

import importlib.util
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Callable

logger = logging.getLogger(__name__)


class PluginHook(str, Enum):
    ON_STARTUP = "on_startup"
    ON_SHUTDOWN = "on_shutdown"
    ON_INDEX = "on_index"
    ON_SEARCH = "on_search"


@dataclass
class PluginMetadata:
    name: str
    version: str
    description: str = ""
    author: str = ""
    hooks: list[PluginHook] = field(default_factory=list)


class Plugin(ABC):
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        pass
    
    async def on_startup(self, context: dict[str, Any]) -> None:
        pass
    
    async def on_shutdown(self, context: dict[str, Any]) -> None:
        pass


class PluginManager:
    def __init__(self, plugin_dir: Path | None = None):
        self.plugin_dir = plugin_dir
        self._plugins: dict[str, Plugin] = {}
        self._hooks: dict[PluginHook, list[Callable]] = {h: [] for h in PluginHook}
    
    def register(self, plugin: Plugin) -> bool:
        meta = plugin.metadata
        if meta.name in self._plugins:
            return False
        self._plugins[meta.name] = plugin
        for hook in meta.hooks:
            handler = getattr(plugin, hook.value, None)
            if handler:
                self._hooks[hook].append(handler)
        return True
    
    def unregister(self, name: str) -> bool:
        if name not in self._plugins:
            return False
        self._plugins.pop(name)
        return True
    
    async def startup(self) -> None:
        for plugin in self._plugins.values():
            await plugin.on_startup({})
    
    async def shutdown(self) -> None:
        for plugin in self._plugins.values():
            await plugin.on_shutdown({})
    
    def list_plugins(self) -> list[PluginMetadata]:
        return [p.metadata for p in self._plugins.values()]
