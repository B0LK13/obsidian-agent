"""Security hardening for PKM Agent.

Implements:
- Prompt injection sanitization
- Path traversal protection  
- Secrets redaction
"""

import logging
import re
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


# Prompt injection patterns
INJECTION_PATTERNS = [
    r"ignore\s+(previous|above|all)\s+(instructions|commands|prompts)",
    r"disregard\s+(previous|above|all)",
    r"<\s*script\s*>",
    r"<\s*iframe\s*>",
    r"javascript\s*:",
    r"data\s*:\s*text/html",
    r"system\s*prompt\s*:\s*",
    r"new\s+instructions\s*:",
    r"forget\s+(everything|all|previous)",
]

# Secrets patterns
SECRET_PATTERNS = {
    "openai_key": r"sk-[a-zA-Z0-9]{48}",
    "anthropic_key": r"sk-ant-[a-zA-Z0-9\-]+",
    "generic_api_key": r"['\"]?api[_-]?key['\"]?\s*[:=]\s*['\"]([a-zA-Z0-9\-_]{20,})['\"]",
    "bearer_token": r"Bearer\s+[a-zA-Z0-9\-_.~+/]+",
    "aws_key": r"AKIA[0-9A-Z]{16}",
    "jwt": r"eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+",
}


def sanitize_prompt_input(text: str, max_length: int = 100000) -> str:
    """Sanitize user input for prompt injection attempts.
    
    Args:
        text: Input text to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized text
        
    Raises:
        ValueError: If injection detected
    """
    if not text:
        return text
    
    # Length check
    if len(text) > max_length:
        raise ValueError(f"Input exceeds maximum length of {max_length} characters")
    
    # Check for injection patterns
    text_lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            logger.warning(f"Potential prompt injection detected: {pattern}")
            raise ValueError(f"Input contains suspicious pattern: {pattern}")
    
    # Remove potential HTML/script tags
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<iframe[^>]*>.*?</iframe>", "", text, flags=re.DOTALL | re.IGNORECASE)
    
    return text


def sanitize_retrieved_content(text: str) -> str:
    """Sanitize retrieved content before sending to LLM.
    
    This is lighter than input sanitization since content is from trusted vault.
    Mainly removes potential code injection.
    
    Args:
        text: Retrieved content
        
    Returns:
        Sanitized content
    """
    if not text:
        return text
    
    # Remove script tags
    text = re.sub(r"<script[^>]*>.*?</script>", "[script removed]", text, flags=re.DOTALL | re.IGNORECASE)
    
    # Remove suspicious data URIs
    text = re.sub(r"data:text/html[^\"']*", "[data uri removed]", text, flags=re.IGNORECASE)
    
    return text


def safe_path_join(base: Path, *parts: str) -> Path:
    """Safely join path components with traversal protection.
    
    Args:
        base: Base directory path
        *parts: Path components to join
        
    Returns:
        Resolved absolute path
        
    Raises:
        ValueError: If path attempts to escape base directory
    """
    base = base.resolve()
    
    # Join parts
    target = base
    for part in parts:
        # Remove any path separators and navigate-up attempts
        clean_part = str(part).replace("..", "").replace("/", "").replace("\\", "")
        if not clean_part:
            raise ValueError(f"Invalid path component: {part}")
        target = target / clean_part
    
    # Resolve and verify within base
    target = target.resolve()
    
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(f"Path {target} attempts to escape base directory {base}")
    
    return target


class WritablePathGuard:
    """Enforce allowlist of writable directories."""
    
    def __init__(self, allowed_dirs: list[Path]):
        """Initialize with list of allowed directories.
        
        Args:
            allowed_dirs: List of directories where writes are allowed
        """
        self.allowed_dirs = [d.resolve() for d in allowed_dirs]
    
    def check_write_allowed(self, path: Path) -> bool:
        """Check if writing to path is allowed.
        
        Args:
            path: Path to check
            
        Returns:
            True if write is allowed
            
        Raises:
            PermissionError: If write is not allowed
        """
        path = path.resolve()
        
        for allowed_dir in self.allowed_dirs:
            try:
                path.relative_to(allowed_dir)
                return True
            except ValueError:
                continue
        
        raise PermissionError(
            f"Write to {path} not allowed. Allowed directories: {self.allowed_dirs}"
        )


def redact_secrets(text: str) -> str:
    """Redact secrets from text for safe logging/display.
    
    Args:
        text: Text that may contain secrets
        
    Returns:
        Text with secrets redacted
    """
    if not text:
        return text
    
    redacted = text
    
    for secret_type, pattern in SECRET_PATTERNS.items():
        redacted = re.sub(
            pattern,
            f"[REDACTED-{secret_type.upper()}]",
            redacted,
            flags=re.IGNORECASE
        )
    
    return redacted


def redact_dict(data: dict[str, Any]) -> dict[str, Any]:
    """Recursively redact secrets from dictionary.
    
    Args:
        data: Dictionary that may contain secrets
        
    Returns:
        Dictionary with secrets redacted
    """
    redacted = {}
    
    for key, value in data.items():
        # Check if key suggests sensitive data
        key_lower = key.lower()
        if any(term in key_lower for term in ["key", "token", "secret", "password", "auth"]):
            redacted[key] = "[REDACTED]"
        elif isinstance(value, str):
            redacted[key] = redact_secrets(value)
        elif isinstance(value, dict):
            redacted[key] = redact_dict(value)
        elif isinstance(value, list):
            redacted[key] = [
                redact_dict(item) if isinstance(item, dict) else redact_secrets(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            redacted[key] = value
    
    return redacted


class SecurityMiddleware:
    """Security middleware for PKM Agent operations."""
    
    def __init__(self, vault_path: Path, data_path: Path):
        """Initialize security middleware.
        
        Args:
            vault_path: Path to vault directory
            data_path: Path to data directory
        """
        self.guard = WritablePathGuard([vault_path, data_path])
    
    def sanitize_user_input(self, text: str) -> str:
        """Sanitize user input."""
        return sanitize_prompt_input(text)
    
    def sanitize_retrieval(self, text: str) -> str:
        """Sanitize retrieved content."""
        return sanitize_retrieved_content(text)
    
    def check_write_path(self, path: Path) -> Path:
        """Check if write to path is allowed."""
        self.guard.check_write_allowed(path)
        return path
    
    def safe_join(self, base: Path, *parts: str) -> Path:
        """Safely join paths."""
        return safe_path_join(base, *parts)
    
    def redact_for_logging(self, data: Any) -> Any:
        """Redact secrets from data for logging."""
        if isinstance(data, str):
            return redact_secrets(data)
        elif isinstance(data, dict):
            return redact_dict(data)
        else:
            return data
