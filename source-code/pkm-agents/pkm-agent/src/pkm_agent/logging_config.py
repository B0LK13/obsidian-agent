"""
Structured logging configuration for PKM Agent.

Provides consistent logging across the application with context, performance tracking,
and integration with error handling.
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from pkm_agent.config import Config


class StructuredFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add custom fields from extra
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class ColoredFormatter(logging.Formatter):
    """Colored formatter for console output."""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        """Format with colors."""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.RESET}"

        # Add emoji for visual clarity
        emoji_map = {
            'DEBUG': '🔍',
            'INFO': 'ℹ️ ',
            'WARNING': '⚠️ ',
            'ERROR': '❌',
            'CRITICAL': '🔥',
        }
        record.msg = f"{emoji_map.get(levelname, '')} {record.msg}"

        return super().format(record)


def setup_logging(config: Config) -> logging.Logger:
    """
    Setup structured logging for the application.

    Args:
        config: Application configuration

    Returns:
        Root logger instance
    """
    # Create root logger
    logger = logging.getLogger("pkm_agent")
    logger.setLevel(getattr(logging, config.log_level.upper()))
    logger.handlers.clear()  # Remove any existing handlers

    # Console handler with colored output
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO if not config.debug else logging.DEBUG)

    if getattr(config, 'log_format', 'text') == 'json':
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_formatter = ColoredFormatter(
            fmt='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)

    logger.addHandler(console_handler)

    # File handler if log file is specified
    log_file = getattr(config, 'log_file', None)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG if config.debug else logging.INFO)
        file_handler.setFormatter(StructuredFormatter())
        logger.addHandler(file_handler)

    # Add rotating file handler for production
    if not config.debug:
        from logging.handlers import RotatingFileHandler

        log_dir = config.data_dir / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        rotating_handler = RotatingFileHandler(
            log_dir / "pkm-agent.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        rotating_handler.setLevel(logging.INFO)
        rotating_handler.setFormatter(StructuredFormatter())
        logger.addHandler(rotating_handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name."""
    return logging.getLogger(f"pkm_agent.{name}")


class LogContext:
    """Context manager for adding extra fields to log records."""

    def __init__(self, logger: logging.Logger, **extra_fields):
        self.logger = logger
        self.extra_fields = extra_fields
        self.old_factory = logging.getLogRecordFactory()

    def __enter__(self):
        def record_factory(*args, **kwargs):
            record = self.old_factory(*args, **kwargs)
            if not hasattr(record, "extra_fields"):
                record.extra_fields = {}
            record.extra_fields.update(self.extra_fields)
            return record

        logging.setLogRecordFactory(record_factory)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logging.setLogRecordFactory(self.old_factory)


def log_performance(logger: logging.Logger, operation: str):
    """
    Decorator to log performance of operations.

    Usage:
        @log_performance(logger, "indexing")
        async def index_notes():
            ...
    """
    import functools
    import time

    def decorator(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                logger.info(
                    f"✓ {operation} completed in {duration:.2f}s",
                    extra={"extra_fields": {
                        "operation": operation,
                        "duration_seconds": duration,
                        "success": True
                    }}
                )
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"✗ {operation} failed after {duration:.2f}s: {e}",
                    extra={"extra_fields": {
                        "operation": operation,
                        "duration_seconds": duration,
                        "success": False,
                        "error": str(e)
                    }}
                )
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.info(
                    f"✓ {operation} completed in {duration:.2f}s",
                    extra={"extra_fields": {
                        "operation": operation,
                        "duration_seconds": duration,
                        "success": True
                    }}
                )
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"✗ {operation} failed after {duration:.2f}s: {e}",
                    extra={"extra_fields": {
                        "operation": operation,
                        "duration_seconds": duration,
                        "success": False,
                        "error": str(e)
                    }}
                )
                raise

        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# Convenience functions
def debug(msg: str, **kwargs):
    """Log debug message."""
    logger = get_logger("main")
    logger.debug(msg, extra={"extra_fields": kwargs} if kwargs else {})


def info(msg: str, **kwargs):
    """Log info message."""
    logger = get_logger("main")
    logger.info(msg, extra={"extra_fields": kwargs} if kwargs else {})


def warning(msg: str, **kwargs):
    """Log warning message."""
    logger = get_logger("main")
    logger.warning(msg, extra={"extra_fields": kwargs} if kwargs else {})


def error(msg: str, **kwargs):
    """Log error message."""
    logger = get_logger("main")
    logger.error(msg, extra={"extra_fields": kwargs} if kwargs else {})


def critical(msg: str, **kwargs):
    """Log critical message."""
    logger = get_logger("main")
    logger.critical(msg, extra={"extra_fields": kwargs} if kwargs else {})
