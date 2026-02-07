"""Rate limiting implementation."""

import time
from collections import defaultdict
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

# Simple in-memory rate storage
# In production, use Redis
_rate_storage: dict[str, list[float]] = defaultdict(list)

# Default limit: 60 requests per minute
DEFAULT_LIMIT = 60
WINDOW_SECONDS = 60

async def check_rate_limit(request: Request):
    """Check rate limit for the client."""
    client_ip = request.client.host if request.client else "unknown"
    
    now = time.time()
    timestamps = _rate_storage[client_ip]
    
    # Clean up old timestamps
    _rate_storage[client_ip] = [t for t in timestamps if now - t < WINDOW_SECONDS]
    
    if len(_rate_storage[client_ip]) >= DEFAULT_LIMIT:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
        
    _rate_storage[client_ip].append(now)
