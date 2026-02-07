"""Plugin manager for loading and executing plugins."""

import importlib
import logging
import pkgutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pkm_agent.plugins.base import Plugin

if TYPE_CHECKING:
    from pkm_agent.app import PKMAgentApp

logger = logging.getLogger(__name__)


class PluginManager:
    """Manages plugin lifecycle."""

    def __init__(self, app: "PKMAgentApp"):
        self.app = app
        self.plugins: dict[str, Plugin] = {}
        
    def discover_plugins(self) -> None:
        """Discover and load plugins from the plugins directory."""
        # 1. Built-in examples/default plugins
        self._load_from_package("pkm_agent.plugins.examples")
        
        # 2. User plugins directory (if configured)
        # user_plugin_dir = self.app.config.data_dir / "plugins"
        # if user_plugin_dir.exists():
        #     self._load_from_directory(user_plugin_dir)

    def _load_from_package(self, package_name: str) -> None:
        """Load plugins from a python package."""
        try:
            package = importlib.import_module(package_name)
            for _, name, _ in pkgutil.iter_modules(package.__path__):
                full_name = f"{package_name}.{name}"
                self._load_plugin_module(full_name)
        except ImportError:
            logger.debug(f"No plugins found in {package_name}")

    def _load_plugin_module(self, module_name: str) -> None:
        """Import a module and instantiate Plugin subclasses."""
        try:
            module = importlib.import_module(module_name)
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (
                    isinstance(attr, type) 
                    and issubclass(attr, Plugin) 
                    and attr is not Plugin
                ):
                    try:
                        plugin = attr()
                        self.register_plugin(plugin)
                    except Exception as e:
                        logger.error(f"Failed to instantiate plugin {attr_name}: {e}")
        except Exception as e:
            logger.error(f"Failed to load plugin module {module_name}: {e}")

    def register_plugin(self, plugin: Plugin) -> None:
        """Register a plugin instance."""
        if plugin.name in self.plugins:
            logger.warning(f"Plugin {plugin.name} already registered. Overwriting.")
        
        self.plugins[plugin.name] = plugin
        logger.info(f"Loaded plugin: {plugin.name} v{plugin.version}")
        
        # Initialize
        try:
            plugin.on_startup(self.app)
        except Exception as e:
            logger.error(f"Error starting plugin {plugin.name}: {e}")

    def hook(self, hook_name: str, *args, **kwargs) -> Any:
        """Execute a hook on all plugins."""
        results = []
        for name, plugin in self.plugins.items():
            if hasattr(plugin, hook_name):
                try:
                    method = getattr(plugin, hook_name)
                    res = method(*args, **kwargs)
                    if res is not None:
                        results.append(res)
                except Exception as e:
                    logger.error(f"Error in plugin {name} hook {hook_name}: {e}")
        return results
