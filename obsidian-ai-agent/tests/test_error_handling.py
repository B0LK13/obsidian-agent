"""
Unit tests for Error Handling System (Issue #99)
"""

import unittest
import time
from datetime import datetime

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "local-ai-stack" / "ai_stack"))

from error_handling import (
    ErrorHandler,
    ErrorContext,
    ErrorCategory,
    ErrorSeverity,
    CircuitBreaker,
    CircuitBreakerState,
    CircuitBreakerOpenError,
    RetryStrategy,
    with_retry,
    with_circuit_breaker,
    Validator,
    SafeExecutor,
    GracefulDegradation,
    HealthMonitor,
    HealthStatus
)


class TestErrorHandler(unittest.TestCase):
    """Test error handling functionality."""
    
    def setUp(self):
        self.handler = ErrorHandler()
    
    def test_handle_error(self):
        """Test basic error handling."""
        try:
            raise ValueError("Test error")
        except Exception as e:
            ctx = self.handler.handle(
                error=e,
                category=ErrorCategory.VALIDATION,
                severity=ErrorSeverity.WARNING,
                component="test",
                operation="test_op"
            )
        
        self.assertIn('ValueError', type(ctx.error).__name__)
        self.assertEqual(ctx.category, ErrorCategory.VALIDATION)
        self.assertEqual(ctx.severity, ErrorSeverity.WARNING)
        self.assertEqual(ctx.component, "test")
    
    def test_error_stats(self):
        """Test error statistics."""
        for i in range(5):
            try:
                raise RuntimeError(f"Error {i}")
            except Exception as e:
                self.handler.handle(
                    error=e,
                    category=ErrorCategory.NETWORK if i < 3 else ErrorCategory.DATABASE
                )
        
        stats = self.handler.get_error_stats()
        self.assertEqual(stats['total_errors'], 5)
        self.assertEqual(stats['by_category'].get(ErrorCategory.NETWORK, 0), 3)
        self.assertEqual(stats['by_category'].get(ErrorCategory.DATABASE, 0), 2)
    
    def test_recent_errors(self):
        """Test retrieving recent errors."""
        for i in range(10):
            try:
                raise ValueError(f"Error {i}")
            except Exception as e:
                self.handler.handle(error=e)
        
        recent = self.handler.get_recent_errors(count=5)
        self.assertEqual(len(recent), 5)
    
    def test_custom_handler(self):
        """Test custom error handler registration."""
        handled_errors = []
        
        def custom_handler(ctx: ErrorContext):
            handled_errors.append(str(ctx.error))
        
        self.handler.register_handler(ErrorCategory.VALIDATION, custom_handler)
        
        try:
            raise ValueError("Custom test")
        except Exception as e:
            self.handler.handle(error=e, category=ErrorCategory.VALIDATION)
        
        self.assertEqual(len(handled_errors), 1)


class TestCircuitBreaker(unittest.TestCase):
    """Test circuit breaker pattern."""
    
    def setUp(self):
        self.cb = CircuitBreaker(
            name="test",
            failure_threshold=3,
            recovery_timeout=1.0
        )
    
    def test_initial_state(self):
        """Test initial state is closed."""
        self.assertEqual(self.cb.state, CircuitBreakerState.CLOSED)
        self.assertTrue(self.cb.can_execute())
    
    def test_open_after_failures(self):
        """Test circuit opens after threshold failures."""
        for _ in range(3):
            self.cb.record_failure()
        
        self.assertEqual(self.cb.state, CircuitBreakerState.OPEN)
        self.assertFalse(self.cb.can_execute())
    
    def test_half_open_after_timeout(self):
        """Test circuit enters half-open after timeout."""
        for _ in range(3):
            self.cb.record_failure()
        
        self.assertEqual(self.cb.state, CircuitBreakerState.OPEN)
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        self.assertTrue(self.cb.can_execute())
        self.assertEqual(self.cb.state, CircuitBreakerState.HALF_OPEN)
    
    def test_close_after_success(self):
        """Test circuit closes after successful calls in half-open."""
        for _ in range(3):
            self.cb.record_failure()
        
        time.sleep(1.1)
        self.cb.can_execute()  # Enter half-open
        
        # Record successes
        for _ in range(2):
            self.cb.record_success()
        
        self.assertEqual(self.cb.state, CircuitBreakerState.CLOSED)
    
    def test_decorator(self):
        """Test circuit breaker decorator."""
        cb = CircuitBreaker("decorator_test", failure_threshold=2)
        call_count = 0
        
        @with_circuit_breaker(cb)
        def failing_function():
            nonlocal call_count
            call_count += 1
            raise RuntimeError("Always fails")
        
        # Trigger failures
        for _ in range(3):
            try:
                failing_function()
            except:
                pass
        
        # Should be open now
        with self.assertRaises(CircuitBreakerOpenError):
            failing_function()
    
    def test_get_stats(self):
        """Test statistics retrieval."""
        self.cb.record_failure()
        self.cb.record_failure()
        
        stats = self.cb.get_stats()
        self.assertEqual(stats['name'], "test")
        self.assertEqual(stats['failure_count'], 2)


class TestRetryStrategy(unittest.TestCase):
    """Test retry mechanisms."""
    
    def test_successful_retry(self):
        """Test successful retry after failures."""
        call_count = 0
        
        def eventually_succeeds():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise RuntimeError("Not ready")
            return "success"
        
        strategy = RetryStrategy(
            max_attempts=5,
            initial_delay=0.01,
            jitter=False
        )
        
        result = strategy.execute(eventually_succeeds)
        
        self.assertEqual(result, "success")
        self.assertEqual(call_count, 3)
    
    def test_max_attempts_exceeded(self):
        """Test failure when max attempts exceeded."""
        def always_fails():
            raise RuntimeError("Always fails")
        
        strategy = RetryStrategy(
            max_attempts=3,
            initial_delay=0.01,
            jitter=False
        )
        
        with self.assertRaises(RuntimeError):
            strategy.execute(always_fails)
    
    def test_retryable_exceptions(self):
        """Test only retrying specified exceptions."""
        call_count = 0
        
        def raises_different_errors():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("Retryable")
            raise TypeError("Not retryable")
        
        strategy = RetryStrategy(
            max_attempts=3,
            initial_delay=0.01,
            retryable_exceptions=(ValueError,),
            jitter=False
        )
        
        with self.assertRaises(TypeError):
            strategy.execute(raises_different_errors)
        
        self.assertEqual(call_count, 2)  # First attempt + one retry
    
    def test_decorator(self):
        """Test retry decorator."""
        
        class RetryTest:
            def __init__(self):
                self.call_count = 0
            
            @with_retry(max_attempts=3, initial_delay=0.01, jitter=False)
            def decorated_function(self):
                self.call_count += 1
                if self.call_count < 2:
                    raise RuntimeError("Fail once")
                return "success"
        
        test = RetryTest()
        result = test.decorated_function()
        self.assertEqual(result, "success")
        self.assertEqual(test.call_count, 2)


class TestValidator(unittest.TestCase):
    """Test validation utilities."""
    
    def test_not_none(self):
        """Test not_none validation."""
        self.assertEqual(Validator.not_none("value"), "value")
        
        with self.assertRaises(ValueError):
            Validator.not_none(None)
    
    def test_not_empty(self):
        """Test not_empty validation."""
        self.assertEqual(Validator.not_empty("hello"), "hello")
        
        with self.assertRaises(ValueError):
            Validator.not_empty("")
        
        with self.assertRaises(ValueError):
            Validator.not_empty("   ")
    
    def test_in_range(self):
        """Test in_range validation."""
        self.assertEqual(Validator.in_range(5, 0, 10), 5)
        
        with self.assertRaises(ValueError):
            Validator.in_range(-1, 0, 10)
        
        with self.assertRaises(ValueError):
            Validator.in_range(11, 0, 10)
    
    def test_is_type(self):
        """Test is_type validation."""
        self.assertEqual(Validator.is_type("hello", str), "hello")
        self.assertEqual(Validator.is_type(42, int), 42)
        
        with self.assertRaises(TypeError):
            Validator.is_type("hello", int)
    
    def test_one_of(self):
        """Test one_of validation."""
        self.assertEqual(Validator.one_of("a", ["a", "b", "c"]), "a")
        
        with self.assertRaises(ValueError):
            Validator.one_of("d", ["a", "b", "c"])


class TestSafeExecutor(unittest.TestCase):
    """Test safe execution context."""
    
    def test_successful_execution(self):
        """Test normal function execution."""
        safe = SafeExecutor()
        
        def normal_func():
            return "success"
        
        result = safe.execute(normal_func)
        self.assertEqual(result, "success")
    
    def test_fallback_on_error(self):
        """Test fallback value on error."""
        safe = SafeExecutor(fallback_value="default")
        
        def failing_func():
            raise RuntimeError("Failed")
        
        result = safe.execute(failing_func)
        self.assertEqual(result, "default")
    
    def test_decorator_usage(self):
        """Test as decorator."""
        safe = SafeExecutor(fallback_value="default")
        
        @safe
        def decorated_fail():
            raise RuntimeError("Fail")
        
        result = decorated_fail()
        self.assertEqual(result, "default")


class TestGracefulDegradation(unittest.TestCase):
    """Test graceful degradation strategies."""
    
    def test_with_fallback(self):
        """Test fallback function."""
        def primary():
            raise RuntimeError("Primary failed")
        
        def fallback():
            return "fallback result"
        
        result = GracefulDegradation.with_fallback(primary, fallback)
        self.assertEqual(result, "fallback result")
    
    def test_with_default_on_error(self):
        """Test default value on error."""
        def failing():
            raise RuntimeError("Fail")
        
        result = GracefulDegradation.with_default_on_error(failing, "default")
        self.assertEqual(result, "default")
    
    def test_with_cache_stale_on_error(self):
        """Test stale cache pattern."""
        cache = {}
        call_count = 0
        
        def fetch_data():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "fresh data"
            raise RuntimeError("Service down")
        
        # First call succeeds and caches
        result = GracefulDegradation.with_cache_stale_on_error(
            fetch_data, cache, "key"
        )
        self.assertEqual(result, "fresh data")
        
        # Second call fails but returns cached value
        result = GracefulDegradation.with_cache_stale_on_error(
            fetch_data, cache, "key"
        )
        self.assertEqual(result, "fresh data")


class TestHealthMonitor(unittest.TestCase):
    """Test health monitoring."""
    
    def test_register_and_check(self):
        """Test health check registration and execution."""
        monitor = HealthMonitor()
        
        def check_db():
            return HealthStatus(
                component="database",
                healthy=True,
                message="Connected",
                last_check=datetime.utcnow()
            )
        
        monitor.register_check("database", check_db)
        
        statuses = monitor.check_all()
        self.assertEqual(len(statuses), 1)
        self.assertTrue(statuses["database"].healthy)
    
    def test_is_healthy(self):
        """Test overall health check."""
        monitor = HealthMonitor()
        
        monitor.register_check(
            "service1",
            lambda: HealthStatus("service1", True, "OK", datetime.utcnow())
        )
        monitor.register_check(
            "service2",
            lambda: HealthStatus("service2", True, "OK", datetime.utcnow())
        )
        
        self.assertTrue(monitor.is_healthy())
    
    def test_is_not_healthy(self):
        """Test unhealthy detection."""
        monitor = HealthMonitor()
        
        monitor.register_check(
            "service1",
            lambda: HealthStatus("service1", True, "OK", datetime.utcnow())
        )
        monitor.register_check(
            "service2",
            lambda: HealthStatus("service2", False, "Down", datetime.utcnow())
        )
        
        self.assertFalse(monitor.is_healthy())
    
    def test_check_failure_handling(self):
        """Test handling of failing health checks."""
        monitor = HealthMonitor()
        
        def failing_check():
            raise RuntimeError("Check failed")
        
        monitor.register_check("failing", failing_check)
        
        statuses = monitor.check_all()
        self.assertFalse(statuses["failing"].healthy)
        self.assertIn("failed", statuses["failing"].message)


class TestIntegration(unittest.TestCase):
    """Integration tests."""
    
    def test_complete_error_handling_flow(self):
        """Test complete error handling flow."""
        handler = ErrorHandler()
        cb = CircuitBreaker("api", failure_threshold=2)
        
        class ApiTest:
            def __init__(self):
                self.call_count = 0
            
            @with_circuit_breaker(cb)
            @with_retry(max_attempts=2, initial_delay=0.01, jitter=False)
            def api_call(self, should_fail: bool = False):
                self.call_count += 1
                if should_fail:
                    raise ConnectionError("API down")
                return "data"
        
        api = ApiTest()
        
        # Successful call
        result = api.api_call(False)
        self.assertEqual(result, "data")
        
        # Failed calls
        for _ in range(3):
            try:
                api.api_call(True)
            except:
                pass
        
        # Circuit should be open
        self.assertEqual(cb.state, CircuitBreakerState.OPEN)


if __name__ == "__main__":
    unittest.main(verbosity=2)
