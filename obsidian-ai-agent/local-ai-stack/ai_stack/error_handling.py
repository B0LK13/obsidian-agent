"""
Defensive Coding and Error Handling System
Issue #99: Implement Defensive Coding and Error Handling Improvements

Provides comprehensive error handling, retry mechanisms, circuit breakers,
validation, and graceful degradation for production stability.
"""

import functools
import logging
import random
import time
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Type, Tuple, Union
import threading

logger = logging.getLogger(__name__)


class ErrorSeverity(Enum):
    """Severity levels for errors."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors for grouping and analysis."""
    NETWORK = "network"
    FILE_IO = "file_io"
    DATABASE = "database"
    VALIDATION = "validation"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Context information for an error."""
    error: Exception
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime
    component: str
    operation: str
    context_data: Dict[str, Any] = field(default_factory=dict)
    stack_trace: str = ""
    retry_count: int = 0
    recovered: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'error_type': type(self.error).__name__,
            'error_message': str(self.error),
            'category': self.category.value,
            'severity': self.severity.value,
            'timestamp': self.timestamp.isoformat(),
            'component': self.component,
            'operation': self.operation,
            'context': self.context_data,
            'stack_trace': self.stack_trace,
            'retry_count': self.retry_count,
            'recovered': self.recovered
        }


class ErrorHandler:
    """
    Centralized error handler with logging, metrics, and recovery tracking.
    """
    
    def __init__(self):
        self._error_history: List[ErrorContext] = []
        self._error_counts: Dict[ErrorCategory, int] = {}
        self._lock = threading.RLock()
        self._handlers: Dict[ErrorCategory, List[Callable]] = {}
    
    def handle(
        self,
        error: Exception,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        component: str = "unknown",
        operation: str = "unknown",
        context: Optional[Dict] = None,
        reraise: bool = False
    ) -> ErrorContext:
        """
        Handle an error with full context tracking.
        
        Args:
            error: The exception to handle
            category: Error category
            severity: Error severity
            component: Component where error occurred
            operation: Operation being performed
            context: Additional context data
            reraise: Whether to reraise the exception
        
        Returns:
            ErrorContext with full error information
        """
        context_data = context or {}
        
        error_ctx = ErrorContext(
            error=error,
            category=category,
            severity=severity,
            timestamp=datetime.utcnow(),
            component=component,
            operation=operation,
            context_data=context_data,
            stack_trace=traceback.format_exc()
        )
        
        with self._lock:
            self._error_history.append(error_ctx)
            self._error_counts[category] = self._error_counts.get(category, 0) + 1
            
            # Call registered handlers
            for handler in self._handlers.get(category, []):
                try:
                    handler(error_ctx)
                except Exception as e:
                    logger.error(f"Error handler failed: {e}")
        
        # Log based on severity
        log_func = {
            ErrorSeverity.DEBUG: logger.debug,
            ErrorSeverity.INFO: logger.info,
            ErrorSeverity.WARNING: logger.warning,
            ErrorSeverity.ERROR: logger.error,
            ErrorSeverity.CRITICAL: logger.critical
        }.get(severity, logger.error)
        
        log_func(
            f"[{component}.{operation}] {category.value}: {error}",
            extra={
                'error_category': category.value,
                'error_severity': severity.value,
                'error_context': context_data
            }
        )
        
        if reraise:
            raise error
        
        return error_ctx
    
    def register_handler(
        self, 
        category: ErrorCategory, 
        handler: Callable[[ErrorContext], None]
    ) -> None:
        """Register a custom error handler for a category."""
        with self._lock:
            if category not in self._handlers:
                self._handlers[category] = []
            self._handlers[category].append(handler)
    
    def get_error_stats(self) -> Dict:
        """Get error statistics."""
        with self._lock:
            total = len(self._error_history)
            recent = [
                e for e in self._error_history 
                if e.timestamp > datetime.utcnow() - timedelta(hours=24)
            ]
            
            return {
                'total_errors': total,
                'errors_24h': len(recent),
                'by_category': dict(self._error_counts),
                'by_severity': self._count_by_severity()
            }
    
    def _count_by_severity(self) -> Dict[str, int]:
        """Count errors by severity."""
        counts = {}
        for ctx in self._error_history:
            key = ctx.severity.value
            counts[key] = counts.get(key, 0) + 1
        return counts
    
    def get_recent_errors(
        self, 
        count: int = 10,
        category: Optional[ErrorCategory] = None
    ) -> List[ErrorContext]:
        """Get recent errors, optionally filtered by category."""
        with self._lock:
            errors = self._error_history
            if category:
                errors = [e for e in errors if e.category == category]
            return sorted(errors, key=lambda e: e.timestamp, reverse=True)[:count]


# Global error handler instance
_global_error_handler = ErrorHandler()


def get_error_handler() -> ErrorHandler:
    """Get the global error handler instance."""
    return _global_error_handler


class CircuitBreakerState(Enum):
    """States for circuit breaker pattern."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject calls
    HALF_OPEN = "half_open"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit breaker pattern implementation for fault tolerance.
    
    Prevents cascading failures by stopping calls to failing services.
    """
    
    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 60.0,
        half_open_max_calls: int = 3,
        success_threshold: int = 2
    ):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.half_open_max_calls = half_open_max_calls
        self.success_threshold = success_threshold
        
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: Optional[datetime] = None
        self._half_open_calls = 0
        self._lock = threading.RLock()
    
    def can_execute(self) -> bool:
        """Check if a call should be allowed through."""
        with self._lock:
            if self._state == CircuitBreakerState.CLOSED:
                return True
            
            if self._state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self._state = CircuitBreakerState.HALF_OPEN
                    self._half_open_calls = 0
                    logger.info(f"Circuit {self.name} entering HALF_OPEN state")
                    return True
                return False
            
            if self._state == CircuitBreakerState.HALF_OPEN:
                if self._half_open_calls < self.half_open_max_calls:
                    self._half_open_calls += 1
                    return True
                return False
            
            return True
    
    def record_success(self) -> None:
        """Record a successful call."""
        with self._lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._reset()
                    logger.info(f"Circuit {self.name} CLOSED (recovered)")
            else:
                self._failure_count = max(0, self._failure_count - 1)
    
    def record_failure(self) -> None:
        """Record a failed call."""
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = datetime.utcnow()
            
            if self._state == CircuitBreakerState.HALF_OPEN:
                self._state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit {self.name} OPEN (recovery failed)")
            elif self._failure_count >= self.failure_threshold:
                self._state = CircuitBreakerState.OPEN
                logger.warning(f"Circuit {self.name} OPEN ({self._failure_count} failures)")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try recovery."""
        if self._last_failure_time is None:
            return True
        elapsed = (datetime.utcnow() - self._last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout
    
    def _reset(self) -> None:
        """Reset circuit breaker to closed state."""
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        self._last_failure_time = None
    
    @property
    def state(self) -> CircuitBreakerState:
        return self._state
    
    def get_stats(self) -> Dict:
        """Get circuit breaker statistics."""
        return {
            'name': self.name,
            'state': self._state.value,
            'failure_count': self._failure_count,
            'success_count': self._success_count,
            'last_failure': self._last_failure_time.isoformat() if self._last_failure_time else None
        }


class RetryStrategy:
    """
    Configurable retry strategy with exponential backoff.
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 1.0,
        max_delay: float = 60.0,
        exponential_base: float = 2.0,
        jitter: bool = True,
        retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None
    ):
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.exponential_base = exponential_base
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or (Exception,)
    
    def execute(
        self,
        func: Callable,
        *args,
        error_handler: Optional[ErrorHandler] = None,
        component: str = "unknown",
        operation: str = "unknown",
        **kwargs
    ) -> Any:
        """
        Execute a function with retry logic.
        
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_exception = None
        
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = func(*args, **kwargs)
                
                if attempt > 1 and error_handler:
                    logger.info(f"Operation succeeded on attempt {attempt}")
                
                return result
                
            except self.retryable_exceptions as e:
                last_exception = e
                
                if attempt == self.max_attempts:
                    break
                
                # Calculate delay
                delay = min(
                    self.initial_delay * (self.exponential_base ** (attempt - 1)),
                    self.max_delay
                )
                
                if self.jitter:
                    delay = delay * (0.5 + random.random())
                
                if error_handler:
                    error_handler.handle(
                        error=e,
                        category=ErrorCategory.UNKNOWN,
                        severity=ErrorSeverity.WARNING,
                        component=component,
                        operation=operation,
                        context={'attempt': attempt, 'max_attempts': self.max_attempts}
                    )
                
                logger.warning(
                    f"Attempt {attempt}/{self.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                
                time.sleep(delay)
        
        # All retries exhausted
        if error_handler:
            error_handler.handle(
                error=last_exception,
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.ERROR,
                component=component,
                operation=operation,
                context={'attempt': self.max_attempts, 'max_attempts': self.max_attempts}
            )
        
        raise last_exception


# Decorator for retry logic
def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 60.0,
    retryable_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    error_handler: Optional[ErrorHandler] = None,
    jitter: bool = True
):
    """
    Decorator for adding retry logic to functions.
    
    Example:
        @with_retry(max_attempts=3)
        def fetch_data():
            # May raise exceptions
            return api.get_data()
    """
    def decorator(func: Callable) -> Callable:
        strategy = RetryStrategy(
            max_attempts=max_attempts,
            initial_delay=initial_delay,
            max_delay=max_delay,
            retryable_exceptions=retryable_exceptions,
            jitter=jitter
        )
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return strategy.execute(
                func, *args,
                error_handler=error_handler or get_error_handler(),
                component=func.__module__,
                operation=func.__name__,
                **kwargs
            )
        
        return wrapper
    return decorator


# Decorator for circuit breaker
def with_circuit_breaker(circuit_breaker: CircuitBreaker):
    """
    Decorator for circuit breaker protection.
    
    Example:
        cb = CircuitBreaker("api_service")
        
        @with_circuit_breaker(cb)
        def call_api():
            return requests.get(url)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not circuit_breaker.can_execute():
                raise CircuitBreakerOpenError(
                    f"Circuit breaker '{circuit_breaker.name}' is OPEN"
                )
            
            try:
                result = func(*args, **kwargs)
                circuit_breaker.record_success()
                return result
            except Exception as e:
                circuit_breaker.record_failure()
                raise
        
        return wrapper
    return decorator


class CircuitBreakerOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


class Validator:
    """
    Input validation utilities.
    """
    
    @staticmethod
    def not_none(value: Any, name: str = "value") -> Any:
        """Validate that value is not None."""
        if value is None:
            raise ValueError(f"{name} cannot be None")
        return value
    
    @staticmethod
    def not_empty(value: str, name: str = "value") -> str:
        """Validate that string is not empty."""
        if not value or not value.strip():
            raise ValueError(f"{name} cannot be empty")
        return value
    
    @staticmethod
    def in_range(
        value: Union[int, float],
        min_val: Union[int, float],
        max_val: Union[int, float],
        name: str = "value"
    ) -> Union[int, float]:
        """Validate that value is within range."""
        if not min_val <= value <= max_val:
            raise ValueError(
                f"{name} must be between {min_val} and {max_val}, got {value}"
            )
        return value
    
    @staticmethod
    def is_type(value: Any, expected_type: Type, name: str = "value") -> Any:
        """Validate that value is of expected type."""
        if not isinstance(value, expected_type):
            raise TypeError(
                f"{name} must be {expected_type.__name__}, got {type(value).__name__}"
            )
        return value
    
    @staticmethod
    def valid_path(path: str, must_exist: bool = False, name: str = "path") -> Path:
        """Validate file path."""
        try:
            p = Path(path)
            if must_exist and not p.exists():
                raise ValueError(f"{name} does not exist: {path}")
            return p
        except Exception as e:
            raise ValueError(f"Invalid {name}: {e}")
    
    @staticmethod
    def one_of(value: Any, options: List[Any], name: str = "value") -> Any:
        """Validate that value is one of allowed options."""
        if value not in options:
            raise ValueError(f"{name} must be one of {options}, got {value}")
        return value


class SafeExecutor:
    """
    Safe execution context with automatic error handling and graceful degradation.
    """
    
    def __init__(
        self,
        error_handler: Optional[ErrorHandler] = None,
        fallback_value: Any = None,
        log_errors: bool = True,
        reraise: bool = False
    ):
        self.error_handler = error_handler or get_error_handler()
        self.fallback_value = fallback_value
        self.log_errors = log_errors
        self.reraise = reraise
    
    def execute(
        self,
        func: Callable,
        *args,
        error_category: ErrorCategory = ErrorCategory.UNKNOWN,
        error_severity: ErrorSeverity = ErrorSeverity.ERROR,
        component: str = "unknown",
        operation: str = "unknown",
        context: Optional[Dict] = None,
        **kwargs
    ) -> Any:
        """
        Execute a function safely with error handling.
        
        Returns:
            Function result or fallback value on error
        """
        try:
            return func(*args, **kwargs)
        except Exception as e:
            if self.log_errors:
                self.error_handler.handle(
                    error=e,
                    category=error_category,
                    severity=error_severity,
                    component=component,
                    operation=operation,
                    context=context,
                    reraise=self.reraise
                )
            
            return self.fallback_value
    
    def __call__(self, func: Callable) -> Callable:
        """Use as a decorator."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return self.execute(
                func, *args,
                component=func.__module__,
                operation=func.__name__,
                **kwargs
            )
        return wrapper


class GracefulDegradation:
    """
    Provides graceful degradation strategies for service failures.
    """
    
    @staticmethod
    def with_fallback(primary: Callable, fallback: Callable, *args, **kwargs):
        """Try primary function, fall back to secondary on failure."""
        try:
            return primary(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Primary failed: {e}, using fallback")
            return fallback(*args, **kwargs)
    
    @staticmethod
    def with_cache_stale_on_error(
        func: Callable,
        cache: Dict,
        cache_key: str,
        *args,
        **kwargs
    ):
        """Return cached value on error (stale cache pattern)."""
        try:
            result = func(*args, **kwargs)
            cache[cache_key] = (result, datetime.utcnow())
            return result
        except Exception as e:
            if cache_key in cache:
                result, cached_at = cache[cache_key]
                logger.warning(f"Using stale cache from {cached_at}: {e}")
                return result
            raise
    
    @staticmethod
    def with_default_on_error(func: Callable, default: Any, *args, **kwargs):
        """Return default value on error."""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.warning(f"Using default value: {e}")
            return default


# Health check system
@dataclass
class HealthStatus:
    """Health status for a component."""
    component: str
    healthy: bool
    message: str
    last_check: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)


class HealthMonitor:
    """Monitor health of system components."""
    
    def __init__(self):
        self._checks: Dict[str, Callable[[], HealthStatus]] = {}
        self._statuses: Dict[str, HealthStatus] = {}
        self._lock = threading.RLock()
    
    def register_check(
        self, 
        name: str, 
        check_func: Callable[[], HealthStatus]
    ) -> None:
        """Register a health check."""
        with self._lock:
            self._checks[name] = check_func
    
    def check_all(self) -> Dict[str, HealthStatus]:
        """Run all health checks."""
        with self._lock:
            for name, check_func in self._checks.items():
                try:
                    self._statuses[name] = check_func()
                except Exception as e:
                    self._statuses[name] = HealthStatus(
                        component=name,
                        healthy=False,
                        message=f"Health check failed: {e}",
                        last_check=datetime.utcnow()
                    )
            return dict(self._statuses)
    
    def is_healthy(self) -> bool:
        """Check if all components are healthy."""
        statuses = self.check_all()
        return all(s.healthy for s in statuses.values())


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)
    
    print("Testing Error Handling System...")
    
    # Test error handler
    handler = ErrorHandler()
    
    try:
        raise ValueError("Test error")
    except Exception as e:
        ctx = handler.handle(
            error=e,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.WARNING,
            component="test",
            operation="test_op"
        )
        print(f"Error recorded: {ctx.to_dict()['error_type']}")
    
    # Test circuit breaker
    cb = CircuitBreaker("test_service", failure_threshold=2)
    
    @with_circuit_breaker(cb)
    def flaky_function(should_fail: bool = False):
        if should_fail:
            raise RuntimeError("Service down")
        return "Success"
    
    print("\nTesting circuit breaker...")
    print(flaky_function(False))  # Should work
    
    # Trigger failures
    for _ in range(3):
        try:
            flaky_function(True)
        except:
            pass
    
    print(f"Circuit state: {cb.state.value}")
    
    # Test retry
    print("\nTesting retry...")
    
    class RetryTest:
        def __init__(self):
            self.call_count = 0
        
        @with_retry(max_attempts=3, initial_delay=0.1)
        def eventually_succeeds(self):
            self.call_count += 1
            if self.call_count < 3:
                raise RuntimeError("Not ready")
            return f"Success after {self.call_count} attempts"
    
    retry_test = RetryTest()
    result = retry_test.eventually_succeeds()
    print(result)
    
    # Test validation
    print("\nTesting validation...")
    try:
        Validator.not_empty("", "username")
    except ValueError as e:
        print(f"Validation caught: {e}")
    
    # Test safe executor
    print("\nTesting safe executor...")
    safe = SafeExecutor(fallback_value="default")
    
    def risky_operation():
        raise RuntimeError("Risky!")
    
    result = safe.execute(risky_operation)
    print(f"Safe execution returned: {result}")
    
    print("\nError Handling System test completed successfully!")
