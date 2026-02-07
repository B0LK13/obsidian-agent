"""FastAPI server for PKM Agent."""

import logging
from typing import Any

logger = logging.getLogger(__name__)


def create_app():
    """Create FastAPI application."""
    try:
        from fastapi import FastAPI
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError:
        raise ImportError("fastapi not installed. Install with: pip install fastapi")

    app = FastAPI(
        title="PKM Agent API",
        description="AI-enhanced Personal Knowledge Management API",
        version="0.1.0",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health():
        return {"status": "healthy"}

    @app.get("/api/stats")
    async def get_stats():
        return {"notes": 0, "tags": 0, "links": 0}

    return app
