"""FastAPI server for PKM Agent."""

import logging
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from pkm_agent.app import PKMAgentApp
from pkm_agent.config import Config, load_config
from pkm_agent.data.models import Note

logger = logging.getLogger(__name__)

# Global app instance for dependency injection
_pkm_app: PKMAgentApp | None = None


def get_pkm_app() -> PKMAgentApp:
    """Get the global PKM app instance."""
    if _pkm_app is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="PKM Agent not initialized"
        )
    return _pkm_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events."""
    global _pkm_app
    
    config = load_config()
    _pkm_app = PKMAgentApp(config)
    await _pkm_app.initialize()
    
    yield
    
    await _pkm_app.close()
    _pkm_app = None


from pkm_agent.api.auth import verify_api_key
from pkm_agent.api.ratelimit import check_rate_limit
from pkm_agent.observability.middleware import MetricsMiddleware
from pkm_agent.observability.metrics import metrics_manager
from pkm_agent.security.headers import SecurityHeadersMiddleware

def create_api_server(config: Config | None = None) -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="PKM Agent API",
        description="API for Personal Knowledge Management Agent",
        version="0.1.0",
        lifespan=lifespan,
        dependencies=[Depends(check_rate_limit), Depends(verify_api_key)]
    )
    
    # Middleware (order matters - last added runs first for request)
    # 1. Security Headers (should wrap everything)
    app.add_middleware(SecurityHeadersMiddleware)
    
    # 2. Metrics (measure everything inside)
    app.add_middleware(MetricsMiddleware)
    
    # 3. CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Import and include routers here to avoid circular imports
    from pkm_agent.api.routes import notes, search, chat, graph
    
    app.include_router(notes.router, prefix="/api/v1/notes", tags=["notes"])
    app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
    app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
    app.include_router(graph.router, prefix="/api/v1/graph", tags=["graph"])
    
    # Mount static files for visualization
    from fastapi.staticfiles import StaticFiles
    from pathlib import Path
    
    static_dir = Path(__file__).parent.parent / "static"
    if static_dir.exists():
        app.mount("/view", StaticFiles(directory=static_dir, html=True), name="static")
    
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": "0.1.0"}

    @app.get("/metrics")
    async def metrics():
        from fastapi.responses import Response
        return Response(
            content=metrics_manager.get_metrics(),
            media_type=metrics_manager.content_type
        )
        
    return app
