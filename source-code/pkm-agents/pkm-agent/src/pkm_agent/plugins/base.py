"""Base classes for PKM Agent plugins."""

from abc import ABC, abstractmethod
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from pkm_agent.app import PKMAgentApp

class Plugin(ABC):
    """Abstract base class for all plugins."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name of the plugin."""
        pass
        
    @property
    def version(self) -> str:
        """Plugin version."""
        return "0.1.0"
        
    def on_startup(self, app: "PKMAgentApp") -> None:
        """Called when the application starts."""
        pass
        
    def on_shutdown(self, app: "PKMAgentApp") -> None:
        """Called when the application stops."""
        pass
        
    def on_note_created(self, note: Any) -> None:
        """Called when a new note is indexed."""
        pass
        
    def on_note_modified(self, note: Any) -> None:
        """Called when a note is modified."""
        pass
        
    def on_chat_message(self, message: str) -> str | None:
        """Called on chat message. Return modified message or None."""
        return None
