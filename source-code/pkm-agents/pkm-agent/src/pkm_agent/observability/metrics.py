"""Metrics and Telemetry."""

import time
import logging
from typing import Callable

from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

logger = logging.getLogger(__name__)

# --- Metrics Definitions ---

# API Request Metrics
HTTP_REQUESTS_TOTAL = Counter(
    "pkm_http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"]
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "pkm_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0, 5.0, 10.0]
)

# LLM Metrics
LLM_REQUESTS_TOTAL = Counter(
    "pkm_llm_requests_total",
    "Total number of LLM requests",
    ["provider", "model"]
)

LLM_TOKENS_TOTAL = Counter(
    "pkm_llm_tokens_total",
    "Total number of tokens processed",
    ["provider", "model", "type"]  # type: input, output
)

LLM_COST_TOTAL = Counter(
    "pkm_llm_cost_total",
    "Total estimated cost in USD",
    ["provider", "model"]
)

LLM_REQUEST_DURATION_SECONDS = Histogram(
    "pkm_llm_request_duration_seconds",
    "LLM request latency",
    ["provider", "model"]
)

# Database/System Metrics
DB_NOTES_COUNT = Gauge(
    "pkm_db_notes_count",
    "Total number of notes in database"
)

DB_CHUNKS_COUNT = Gauge(
    "pkm_vector_chunks_count",
    "Total number of chunks in vector store"
)

SYSTEM_MEMORY_USAGE = Gauge(
    "pkm_system_memory_usage_bytes",
    "Current memory usage in bytes"
)

SYSTEM_CPU_USAGE = Gauge(
    "pkm_system_cpu_usage_percent",
    "Current CPU usage percent"
)


class MetricsManager:
    """Manages metrics collection and export."""
    
    def get_metrics(self) -> bytes:
        """Get current metrics in Prometheus format."""
        # Update gauges before collection
        self._update_system_metrics()
        return generate_latest()
        
    def _update_system_metrics(self):
        """Update system resource metrics."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        SYSTEM_MEMORY_USAGE.set(process.memory_info().rss)
        SYSTEM_CPU_USAGE.set(process.cpu_percent())

    @property
    def content_type(self) -> str:
        return CONTENT_TYPE_LATEST

# Global instance
metrics_manager = MetricsManager()
