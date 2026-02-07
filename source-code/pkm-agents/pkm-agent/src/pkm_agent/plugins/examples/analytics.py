"""Example plugin: Analytics."""

from pkm_agent.plugins.base import Plugin
import logging

logger = logging.getLogger(__name__)

class AnalyticsPlugin(Plugin):
    """Simple analytics plugin."""
    
    @property
    def name(self) -> str:
        return "analytics"
        
    def on_startup(self, app) -> None:
        logger.info("Analytics plugin started")
        
    def on_note_created(self, note) -> None:
        logger.info(f"Analytics: Note created - {note.title}")
        
    def on_chat_message(self, message: str) -> str | None:
        # Don't modify, just log
        logger.info(f"Analytics: Chat message received (len={len(message)})")
        return None
