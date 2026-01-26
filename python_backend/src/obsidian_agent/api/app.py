"""FastAPI application factory for obsidian-agent."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from obsidian_agent.config import Settings
from obsidian_agent.api.routes import router
from obsidian_agent.api.dependencies import get_settings, init_services, cleanup_services


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Manage application lifespan - initialize and cleanup services."""
    settings = get_settings()
    await init_services(settings)
    yield
    await cleanup_services()


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = get_settings()

    app = FastAPI(
        title="Obsidian Agent API",
        description="""REST API for Obsidian Agent - Semantic search, indexing, and AI-powered features for your Obsidian vault.

## Features
- Semantic search across your vault
- Vector-based similarity search
- Duplicate detection
- Auto-linking suggestions
- Content summarization
- Template generation
""",
        version="0.1.0",
        lifespan=lifespan,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # CORS middleware for Obsidian plugin and web dashboard
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(router, prefix="/api/v1")

    return app


# Default app instance for uvicorn
app = create_app()
