"""Dependency injection for FastAPI."""

from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from obsidian_agent.config import Settings
from obsidian_agent.vector_store.chromadb_store import ChromaDBStore
from obsidian_agent.search.search_service import SearchService
from obsidian_agent.indexing.indexer import VaultIndexer
from obsidian_agent.indexing.parser import MarkdownParser
from obsidian_agent.features.duplicates import DuplicateDetectionService
from obsidian_agent.features.linking import AutoLinkingService
from obsidian_agent.features.organization import AutoOrganizationService
from obsidian_agent.features.summarization import SummarizationService
from obsidian_agent.features.templates import TemplateService
from obsidian_agent.health import HealthChecker


# Global service instances
SERVICES = {}


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()


async def init_services(settings: Settings) -> None:
    """Initialize all services."""
    global SERVICES
    
    # Initialize vector store
    vector_store = ChromaDBStore(
        persist_directory=str(settings.data_dir / "chromadb"),
        collection_name="obsidian_notes",
    )
    await vector_store.initialize()
    
    # Initialize parser
    parser = MarkdownParser(settings.vault_path)
    
    # Store services
    SERVICES.update({
        "settings": settings,
        "vector_store": vector_store,
        "parser": parser,
        "indexer": VaultIndexer(vector_store, parser),
        "search_service": SearchService(vector_store, parser),
        "duplicate_service": DuplicateDetectionService(vector_store),
        "linking_service": AutoLinkingService(vector_store),
        "organization_service": AutoOrganizationService(vector_store),
        "summarization_service": SummarizationService(vector_store),
        "template_service": TemplateService(vector_store),
        "health_checker": HealthChecker(settings),
    })


async def cleanup_services() -> None:
    """Cleanup services on shutdown."""
    global SERVICES
    SERVICES.clear()


def get_vector_store() -> ChromaDBStore:
    return SERVICES["vector_store"]


def get_indexer() -> VaultIndexer:
    return SERVICES["indexer"]


def get_search_service() -> SearchService:
    return SERVICES["search_service"]


def get_duplicate_service() -> DuplicateDetectionService:
    return SERVICES["duplicate_service"]


def get_linking_service() -> AutoLinkingService:
    return SERVICES["linking_service"]


def get_organization_service() -> AutoOrganizationService:
    return SERVICES["organization_service"]


def get_summarization_service() -> SummarizationService:
    return SERVICES["summarization_service"]


def get_template_service() -> TemplateService:
    return SERVICES["template_service"]


def get_health_checker() -> HealthChecker:
    return SERVICES["health_checker"]


# Type aliases for dependency injection
VectorStoreDep = Annotated[ChromaDBStore, Depends(get_vector_store)]
IndexerDep = Annotated[VaultIndexer, Depends(get_indexer)]
SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]
DuplicateServiceDep = Annotated[DuplicateDetectionService, Depends(get_duplicate_service)]
LinkingServiceDep = Annotated[AutoLinkingService, Depends(get_linking_service)]
OrganizationServiceDep = Annotated[AutoOrganizationService, Depends(get_organization_service)]
SummarizationServiceDep = Annotated[SummarizationService, Depends(get_summarization_service)]
TemplateServiceDep = Annotated[TemplateService, Depends(get_template_service)]
HealthCheckerDep = Annotated[HealthChecker, Depends(get_health_checker)]
