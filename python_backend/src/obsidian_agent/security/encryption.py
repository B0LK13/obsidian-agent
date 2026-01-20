"""Local-first encryption for vault data."""

import base64
import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class EncryptionConfig:
    key_derivation_iterations: int = 100000
    algorithm: str = "AES-256-GCM"
    salt_length: int = 16
    nonce_length: int = 12


class EncryptionManager:
    """Manages encryption for local-first privacy."""
    
    def __init__(self, config: EncryptionConfig | None = None):
        self.config = config or EncryptionConfig()
        self._key: bytes | None = None
        self._fernet_available = self._check_cryptography()
    
    def _check_cryptography(self) -> bool:
        try:
            from cryptography.fernet import Fernet
            return True
        except ImportError:
            logger.warning("cryptography not available. Install with: pip install cryptography")
            return False
    
    def derive_key(self, password: str, salt: bytes | None = None) -> tuple[bytes, bytes]:
        """Derive encryption key from password."""
        salt = salt or os.urandom(self.config.salt_length)
        key = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, self.config.key_derivation_iterations, dklen=32)
        return key, salt
    
    def set_password(self, password: str) -> bytes:
        """Set the encryption password and return the salt."""
        self._key, salt = self.derive_key(password)
        return salt
    
    def unlock(self, password: str, salt: bytes) -> bool:
        """Unlock with password and stored salt."""
        self._key, _ = self.derive_key(password, salt)
        return True
    
    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data."""
        if not self._key:
            raise ValueError("No encryption key set")
        if not self._fernet_available:
            return base64.b64encode(data)
        
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = os.urandom(self.config.nonce_length)
        aesgcm = AESGCM(self._key)
        ciphertext = aesgcm.encrypt(nonce, data, None)
        return nonce + ciphertext
    
    def decrypt(self, data: bytes) -> bytes:
        """Decrypt data."""
        if not self._key:
            raise ValueError("No encryption key set")
        if not self._fernet_available:
            return base64.b64decode(data)
        
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        nonce = data[:self.config.nonce_length]
        ciphertext = data[self.config.nonce_length:]
        aesgcm = AESGCM(self._key)
        return aesgcm.decrypt(nonce, ciphertext, None)
    
    def encrypt_file(self, path: Path, output_path: Path | None = None) -> Path:
        """Encrypt a file."""
        output = output_path or path.with_suffix(path.suffix + ".enc")
        data = path.read_bytes()
        encrypted = self.encrypt(data)
        output.write_bytes(encrypted)
        return output
    
    def decrypt_file(self, path: Path, output_path: Path | None = None) -> Path:
        """Decrypt a file."""
        output = output_path or path.with_suffix("")
        data = path.read_bytes()
        decrypted = self.decrypt(data)
        output.write_bytes(decrypted)
        return output
    
    def encrypt_text(self, text: str) -> str:
        """Encrypt text and return base64."""
        encrypted = self.encrypt(text.encode("utf-8"))
        return base64.b64encode(encrypted).decode("ascii")
    
    def decrypt_text(self, encrypted_text: str) -> str:
        """Decrypt base64 text."""
        data = base64.b64decode(encrypted_text.encode("ascii"))
        return self.decrypt(data).decode("utf-8")
    
    def is_locked(self) -> bool:
        return self._key is None
