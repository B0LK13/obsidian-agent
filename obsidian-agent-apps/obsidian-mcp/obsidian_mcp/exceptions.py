"""Custom exceptions for Obsidian MCP Server."""


class ObsidianError(Exception):
    """Base exception for Obsidian MCP errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class APIError(ObsidianError):
    """Exception raised when Obsidian API request fails."""
    
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response or {}


class NoteNotFoundError(ObsidianError):
    """Exception raised when a note is not found."""
    pass


class FolderNotFoundError(ObsidianError):
    """Exception raised when a folder is not found."""
    pass


class InvalidPathError(ObsidianError):
    """Exception raised when a path is invalid."""
    pass


class TemplateError(ObsidianError):
    """Exception raised when template operations fail."""
    pass


class GraphAnalysisError(ObsidianError):
    """Exception raised when graph analysis fails."""
    pass
