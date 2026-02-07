"""Tests for authentication."""

import pytest
from datetime import datetime, timedelta
from pkm_agent.api.auth import APIKeyManager, verify_api_key
from fastapi import HTTPException

def test_key_creation(test_app):
    """Test creating an API key."""
    manager = APIKeyManager(test_app)
    key = manager.create_key("test-key", expires_days=30)
    
    assert len(key) > 20
    assert manager.verify(key)

def test_key_revocation(test_app):
    """Test revoking a key."""
    manager = APIKeyManager(test_app)
    key = manager.create_key("to-revoke")
    
    # Get ID from DB
    keys = test_app.db.list_api_keys()
    target_key = next(k for k in keys if k["name"] == "to-revoke")
    
    # Revoke
    test_app.db.revoke_api_key(target_key["id"])
    
    # Verify fails
    assert not manager.verify(key)

def test_key_expiration(test_app):
    """Test expired keys."""
    manager = APIKeyManager(test_app)
    # Create manually with past expiration
    import secrets
    import hashlib
    
    key_secret = secrets.token_urlsafe(32)
    key_hash = hashlib.sha256(key_secret.encode()).hexdigest()
    prefix = key_secret[:8]
    expires_at = datetime.now() - timedelta(days=1)
    
    test_app.db.create_api_key("expired", key_hash, prefix, expires_at)
    
    assert not manager.verify(key_secret)
