"""Health check system for monitoring component status"""

import asyncio
import logging
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheck:
    """Health check result"""
    name: str
    status: HealthStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    latency_ms: Optional[float] = None


class HealthChecker:
    """Performs health checks on all components"""
    
    async def check_database(self, db_path: Path) -> HealthCheck:
        """Check database health"""
        start = time.time()
        
        try:
            from .database import DatabaseConnection
            
            if not db_path.exists():
                return HealthCheck(
                    name="database",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Database not found: {db_path}",
                )
            
            conn = DatabaseConnection(db_path)
            with conn.get_session() as session:
                session.execute("SELECT 1")
            conn.close()
            
            latency = (time.time() - start) * 1000
            
            return HealthCheck(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database is accessible",
                latency_ms=latency,
            )
        except Exception as e:
            return HealthCheck(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {e}",
                details={"error": str(e)},
            )
    
    async def check_vault_access(self, vault_path: Path) -> HealthCheck:
        """Check vault accessibility"""
        try:
            if not vault_path.exists():
                return HealthCheck(
                    name="vault_access",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Vault not found: {vault_path}",
                )
            
            if not vault_path.is_dir():
                return HealthCheck(
                    name="vault_access",
                    status=HealthStatus.UNHEALTHY,
                    message=f"Vault path is not a directory: {vault_path}",
                )
            
            md_count = len(list(vault_path.rglob("*.md")))
            
            return HealthCheck(
                name="vault_access",
                status=HealthStatus.HEALTHY,
                message=f"Vault is accessible ({md_count} markdown files)",
                details={"markdown_files": md_count},
            )
        except PermissionError:
            return HealthCheck(
                name="vault_access",
                status=HealthStatus.UNHEALTHY,
                message="Permission denied accessing vault",
            )
        except Exception as e:
            return HealthCheck(
                name="vault_access",
                status=HealthStatus.UNHEALTHY,
                message=f"Vault check failed: {e}",
            )
    
    async def check_vector_store(self, persist_dir: Path) -> HealthCheck:
        """Check vector store health"""
        start = time.time()
        
        try:
            if not persist_dir.exists():
                return HealthCheck(
                    name="vector_store",
                    status=HealthStatus.DEGRADED,
                    message="Vector store not initialized",
                )
            
            latency = (time.time() - start) * 1000
            
            return HealthCheck(
                name="vector_store",
                status=HealthStatus.HEALTHY,
                message="Vector store directory exists",
                latency_ms=latency,
            )
        except Exception as e:
            return HealthCheck(
                name="vector_store",
                status=HealthStatus.UNHEALTHY,
                message=f"Vector store check failed: {e}",
            )
    
    async def check_dependencies(self) -> HealthCheck:
        """Check critical dependencies"""
        missing = []
        
        deps = [
            ("chromadb", "chromadb"),
            ("sentence_transformers", "sentence-transformers"),
            ("tiktoken", "tiktoken"),
            ("typer", "typer"),
            ("rich", "rich"),
            ("frontmatter", "python-frontmatter"),
        ]
        
        for module_name, package_name in deps:
            try:
                __import__(module_name)
            except ImportError:
                missing.append(package_name)
        
        if missing:
            return HealthCheck(
                name="dependencies",
                status=HealthStatus.UNHEALTHY,
                message=f"Missing dependencies: {', '.join(missing)}",
                details={"missing": missing},
            )
        
        return HealthCheck(
            name="dependencies",
            status=HealthStatus.HEALTHY,
            message="All dependencies installed",
        )
    
    async def check_all(
        self,
        db_path: Optional[Path] = None,
        vault_path: Optional[Path] = None,
        vector_persist_dir: Optional[Path] = None,
    ) -> Dict[str, HealthCheck]:
        """Run all health checks"""
        checks = [self.check_dependencies()]
        
        if db_path:
            checks.append(self.check_database(db_path))
        if vault_path:
            checks.append(self.check_vault_access(vault_path))
        if vector_persist_dir:
            checks.append(self.check_vector_store(vector_persist_dir))
        
        results = await asyncio.gather(*checks, return_exceptions=True)
        
        return {
            check.name: check
            for check in results
            if isinstance(check, HealthCheck)
        }
