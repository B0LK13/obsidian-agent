"""AI-powered features module"""

from .duplicates import DuplicateDetectionService
from .linking import AutoLinkingService
from .organization import AutoOrganizationService
from .summarization import SummarizationService
from .templates import TemplateService

__all__ = [
    "DuplicateDetectionService",
    "AutoLinkingService",
    "AutoOrganizationService",
    "SummarizationService",
    "TemplateService",
]
