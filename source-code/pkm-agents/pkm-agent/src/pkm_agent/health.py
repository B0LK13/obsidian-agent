"""
Health check and monitoring utilities for PKM Agent.

Provides health status endpoints and system diagnostics.
"""

import sys
from datetime import datetime
from typing import Any

import psutil

from pkm_agent.config import Config
from pkm_agent.exceptions import DatabaseConnectionError


class HealthChecker:
    """System health checker for PKM Agent."""

    def __init__(self, config: Config):
        self.config = config
        self.start_time = datetime.now()
        self._last_check: datetime | None = None
        self._last_status: dict[str, Any] = {}

    async def check_health(self, detailed: bool = False) -> dict[str, Any]:
        """
        Perform health check.

        Args:
            detailed: Include detailed diagnostics

        Returns:
            Health status dictionary
        """
        now = datetime.now()
        status = {
            "status": "healthy",
            "timestamp": now.isoformat(),
            "uptime_seconds": (now - self.start_time).total_seconds(),
            "checks": {}
        }

        # Check database
        try:
            db_healthy = await self._check_database()
            status["checks"]["database"] = {
                "healthy": db_healthy,
                "path": str(self.config.db_path)
            }
        except Exception as e:
            status["checks"]["database"] = {
                "healthy": False,
                "error": str(e)
            }
            status["status"] = "unhealthy"

        # Check vector store
        try:
            vs_healthy = await self._check_vector_store()
            status["checks"]["vector_store"] = {
                "healthy": vs_healthy,
                "path": str(self.config.chroma_path)
            }
        except Exception as e:
            status["checks"]["vector_store"] = {
                "healthy": False,
                "error": str(e)
            }
            status["status"] = "degraded" if status["status"] == "healthy" else "unhealthy"

        # Check PKM root
        pkm_exists = self.config.pkm_root.exists()
        status["checks"]["pkm_root"] = {
            "healthy": pkm_exists,
            "path": str(self.config.pkm_root),
            "exists": pkm_exists
        }
        if not pkm_exists and status["status"] == "healthy":
            status["status"] = "degraded"

        # Add detailed diagnostics if requested
        if detailed:
            status["diagnostics"] = await self._get_diagnostics()

        self._last_check = now
        self._last_status = status

        return status

    async def _check_database(self) -> bool:
        """Check database connection."""
        try:
            import aiosqlite
            async with aiosqlite.connect(self.config.db_path) as db:
                await db.execute("SELECT 1")
            return True
        except Exception as e:
            raise DatabaseConnectionError(
                operation="health_check",
                message=f"Database health check failed: {e}"
            )

    async def _check_vector_store(self) -> bool:
        """Check vector store accessibility."""
        return self.config.chroma_path.exists() and self.config.chroma_path.is_dir()

    async def _get_diagnostics(self) -> dict[str, Any]:
        """Get detailed system diagnostics."""
        try:
            process = psutil.Process()

            return {
                "system": {
                    "python_version": sys.version,
                    "platform": sys.platform,
                    "cpu_count": psutil.cpu_count(),
                    "cpu_percent": psutil.cpu_percent(interval=0.1),
                    "memory_total_mb": psutil.virtual_memory().total / (1024 * 1024),
                    "memory_available_mb": psutil.virtual_memory().available / (1024 * 1024),
                    "disk_usage_percent": psutil.disk_usage(str(self.config.data_dir.parent)).percent,
                },
                "process": {
                    "pid": process.pid,
                    "memory_mb": process.memory_info().rss / (1024 * 1024),
                    "cpu_percent": process.cpu_percent(interval=0.1),
                    "num_threads": process.num_threads(),
                    "open_files": len(process.open_files()),
                },
                "config": {
                    "llm_provider": self.config.llm.provider,
                    "llm_model": self.config.llm.model,
                    "rag_embedding_model": self.config.rag.embedding_model,
                    "data_dir": str(self.config.data_dir),
                    "pkm_root": str(self.config.pkm_root),
                }
            }
        except Exception as e:
            return {"error": str(e)}

    def get_cached_status(self) -> dict[str, Any] | None:
        """Get last health check result (cached)."""
        return self._last_status if self._last_check else None


class HealthCheckServer:
    """Simple HTTP server for health checks."""

    def __init__(self, config: Config, port: int = 3000):
        self.config = config
        self.port = port
        self.checker = HealthChecker(config)

    async def start(self):
        """Start health check server."""
        from aiohttp import web

        app = web.Application()
        app.router.add_get('/health', self.health_endpoint)
        app.router.add_get('/health/detailed', self.detailed_health_endpoint)
        app.router.add_get('/ready', self.readiness_endpoint)
        app.router.add_get('/live', self.liveness_endpoint)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()

        print(f"Health check server running on http://0.0.0.0:{self.port}")

    async def health_endpoint(self, request):
        """Basic health check endpoint."""
        from aiohttp import web

        status = await self.checker.check_health(detailed=False)
        http_status = 200 if status["status"] == "healthy" else 503

        return web.json_response(status, status=http_status)

    async def detailed_health_endpoint(self, request):
        """Detailed health check endpoint."""
        from aiohttp import web

        status = await self.checker.check_health(detailed=True)
        http_status = 200 if status["status"] == "healthy" else 503

        return web.json_response(status, status=http_status)

    async def readiness_endpoint(self, request):
        """Kubernetes-style readiness probe."""
        from aiohttp import web

        status = await self.checker.check_health(detailed=False)
        ready = status["status"] in ["healthy", "degraded"]

        return web.json_response(
            {"ready": ready, "status": status["status"]},
            status=200 if ready else 503
        )

    async def liveness_endpoint(self, request):
        """Kubernetes-style liveness probe."""
        from aiohttp import web

        # Simple check - if we can respond, we're alive
        return web.json_response(
            {"alive": True, "uptime_seconds": (datetime.now() - self.checker.start_time).total_seconds()},
            status=200
        )


class SelfHealer:
    """Auto-repair system for PKM Agent."""

    def __init__(self, config: Config):
        self.config = config
        self.checker = HealthChecker(config)

    async def diagnose_and_heal(self) -> dict[str, Any]:
        """Run diagnostics and attempt repairs."""
        print("Running system diagnostics...")
        status = await self.checker.check_health(detailed=True)
        report = {
            "initial_status": status["status"],
            "repairs": [],
            "final_status": "unknown"
        }

        if status["status"] == "healthy":
            print("System is healthy.")
            report["final_status"] = "healthy"
            return report

        print(f"System status: {status['status']}. Attempting repairs...")

        # 1. Database Repair
        if not status["checks"]["database"]["healthy"]:
            print("Attempting to repair database...")
            try:
                # Ensure directory exists
                self.config.data_dir.mkdir(parents=True, exist_ok=True)
                # Try to initialize a fresh DB if it doesn't exist or is corrupt
                # Note: In a real scenario, we might want to backup first
                import aiosqlite
                async with aiosqlite.connect(self.config.db_path) as db:
                    # Basic schema init (simplified for self-healing)
                    await db.execute("""
                        CREATE TABLE IF NOT EXISTS notes (
                            path TEXT PRIMARY KEY,
                            content TEXT,
                            modified_at REAL,
                            indexed_at REAL
                        )
                    """)
                    await db.commit()
                report["repairs"].append("database_initialized")
                print("Database initialized/repaired.")
            except Exception as e:
                report["repairs"].append(f"database_repair_failed: {e}")
                print(f"Database repair failed: {e}")

        # 2. Vector Store Repair
        if not status["checks"]["vector_store"]["healthy"]:
            print("Attempting to repair vector store...")
            try:
                if not self.config.chroma_path.exists():
                    self.config.chroma_path.mkdir(parents=True, exist_ok=True)
                    report["repairs"].append("vector_store_directory_created")
                    print("Vector store directory created.")
            except Exception as e:
                report["repairs"].append(f"vector_store_repair_failed: {e}")

        # 3. PKM Root Check
        if not status["checks"]["pkm_root"]["healthy"]:
             print("PKM Root missing. Creating default structure...")
             try:
                 self.config.pkm_root.mkdir(parents=True, exist_ok=True)
                 (self.config.pkm_root / "_meta").mkdir(exist_ok=True)
                 (self.config.pkm_root / "01_projects").mkdir(exist_ok=True)
                 (self.config.pkm_root / "02_areas").mkdir(exist_ok=True)
                 (self.config.pkm_root / "03_resources").mkdir(exist_ok=True)
                 (self.config.pkm_root / "04_archive").mkdir(exist_ok=True)
                 (self.config.pkm_root / "99_zettelkasten").mkdir(exist_ok=True)
                 report["repairs"].append("pkm_root_created")
             except Exception as e:
                 report["repairs"].append(f"pkm_root_repair_failed: {e}")

        # Re-check health
        final_status = await self.checker.check_health(detailed=False)
        report["final_status"] = final_status["status"]
        
        print(f"Repairs complete. Final status: {final_status['status']}")
        return report
