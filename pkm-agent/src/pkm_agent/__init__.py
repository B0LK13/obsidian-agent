"""PKM Agent - Personal Knowledge Management Agent"""

__version__ = "0.1.0"

from pkm_agent.errors import (
    PermanentError,
    TemporaryError,
    RateLimitError,
    IndexingError,
)
from pkm_agent.sync import (
    SyncEvent,
    SyncEventType,
    SyncServer,
)
from pkm_agent.watcher import (
    FileWatcher,
    MarkdownFileHandler,
)

__all__ = [
    "__version__",
    "PermanentError",
    "TemporaryError",
    "RateLimitError",
    "IndexingError",
    "SyncEvent",
    "SyncEventType",
    "SyncServer",
    "FileWatcher",
    "MarkdownFileHandler",
]
