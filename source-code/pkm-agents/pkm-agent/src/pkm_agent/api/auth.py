"""Authentication logic for API."""

import hashlib
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from pkm_agent.api.server import get_pkm_app
from pkm_agent.app import PKMAgentApp

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class APIKeyManager:
    """Manages API keys."""
    
    def __init__(self, app: PKMAgentApp):
        self.app = app
        
    def create_key(self, name: str, expires_days: int = 365) -> str:
        """Create a new API key and store hash in DB."""
        # Generate random key
        key_secret = secrets.token_urlsafe(32)
        key_prefix = key_secret[:8]
        key_hash = self._hash_key(key_secret)
        
        # Calculate expiry
        from datetime import datetime, timedelta
        expires_at = datetime.now() + timedelta(days=expires_days)
        
        # Store in DB
        self.app.db.create_api_key(name, key_hash, key_prefix, expires_at)
        
        return key_secret

    def verify(self, key: str) -> bool:
        """Verify an API key."""
        # Check config-based key first (simple mode)
        config_key = self.app.config.api.api_key
        if config_key and key == config_key:
            return True
            
        # Check DB-based keys
        key_hash = self._hash_key(key)
        return self.app.db.verify_api_key_hash(key_hash)

    def _hash_key(self, key: str) -> str:
        """Hash the API key."""
        return hashlib.sha256(key.encode()).hexdigest()


async def verify_api_key(
    api_key: str | None = Security(api_key_header),
    app: PKMAgentApp = Depends(get_pkm_app)
) -> str:
    """Dependency to verify API key."""
    if not api_key:
        # Check if auth is optional or disabled? 
        # For now, if no key in config and no keys in DB, maybe allow?
        # But safer to deny.
        
        # If config key is not set, and no keys in DB, we might default to allow 
        # for localhost ease of use, but let's be secure by default.
        # Issue 75 implies adding auth, so we should require it.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key required"
        )
        
    manager = APIKeyManager(app)
    if not manager.verify(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
        
    return api_key
