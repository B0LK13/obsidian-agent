"""Middleware for metrics collection."""

import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from pkm_agent.observability.metrics import HTTP_REQUESTS_TOTAL, HTTP_REQUEST_DURATION_SECONDS

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request metrics."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Get endpoint template if available (to avoid cardinality explosion)
        endpoint = request.url.path
        
        try:
            response = await call_next(request)
            status_code = str(response.status_code)
        except Exception:
            status_code = "500"
            raise
        finally:
            duration = time.time() - start_time
            
            # Record metrics
            HTTP_REQUESTS_TOTAL.labels(
                method=request.method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=request.method,
                endpoint=endpoint
            ).observe(duration)
            
        return response
