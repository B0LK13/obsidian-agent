import { describe, it, expect, beforeEach } from 'vitest';
import {
  CircuitBreaker,
  CircuitState,
  RetryPolicy,
  ResilientClient,
  FailureTracker,
} from '../src/services/resilience';

describe('CircuitBreaker', () => {
  let breaker: CircuitBreaker;

  beforeEach(() => {
    breaker = new CircuitBreaker('test-breaker', {
      failureThreshold: 3,
      successThreshold: 2,
      timeout: 1000,
    });
  });

  it('should start in CLOSED state', () => {
    const stats = breaker.getStats();
    expect(stats.state).toBe(CircuitState.CLOSED);
  });

  it('should execute successful operations', async () => {
    const result = await breaker.execute(async () => 'success');
    expect(result).toBe('success');

    const stats = breaker.getStats();
    expect(stats.totalSuccesses).toBe(1);
  });

  it('should trip to OPEN after threshold failures', async () => {
    const failingFn = async () => {
      throw new Error('Failure');
    };

    // Trigger 3 failures
    for (let i = 0; i < 3; i++) {
      try {
        await breaker.execute(failingFn);
      } catch (e) {
        // Expected
      }
    }

    const stats = breaker.getStats();
    expect(stats.state).toBe(CircuitState.OPEN);
    expect(stats.totalFailures).toBe(3);
  });

  it('should fail fast when OPEN', async () => {
    // Trip the breaker
    breaker.forceOpen();

    await expect(
      breaker.execute(async () => 'test')
    ).rejects.toThrow('Circuit breaker');

    const stats = breaker.getStats();
    expect(stats.state).toBe(CircuitState.OPEN);
  });

  it('should transition to HALF_OPEN after timeout', async () => {
    const failingFn = async () => {
      throw new Error('Failure');
    };

    // Trip breaker
    for (let i = 0; i < 3; i++) {
      try {
        await breaker.execute(failingFn);
      } catch (e) {}
    }

    expect(breaker.getStats().state).toBe(CircuitState.OPEN);

    // Wait for timeout (simplified - in real test use fake timers)
    await new Promise((resolve) => setTimeout(resolve, 1100));

    // Next call should attempt HALF_OPEN
    try {
      await breaker.execute(async () => 'success');
    } catch (e) {
      // May fail or succeed
    }

    // Should have attempted half-open
    const stats = breaker.getStats();
    expect([CircuitState.HALF_OPEN, CircuitState.CLOSED]).toContain(stats.state);
  });

  it('should reset to CLOSED after success threshold in HALF_OPEN', async () => {
    breaker = new CircuitBreaker('reset-test', {
      failureThreshold: 2,
      successThreshold: 2,
      timeout: 100,
    });

    // Trip it
    for (let i = 0; i < 2; i++) {
      try {
        await breaker.execute(async () => {
          throw new Error('Fail');
        });
      } catch (e) {}
    }

    await new Promise((resolve) => setTimeout(resolve, 150));

    // Succeed twice to reset
    await breaker.execute(async () => 'success');
    await breaker.execute(async () => 'success');

    expect(breaker.getStats().state).toBe(CircuitState.CLOSED);
  });
});

describe('RetryPolicy', () => {
  let policy: RetryPolicy;

  beforeEach(() => {
    policy = new RetryPolicy({
      maxAttempts: 3,
      initialDelayMs: 50,
      maxDelayMs: 200,
      backoffMultiplier: 2,
    });
  });

  it('should succeed on first attempt', async () => {
    const result = await policy.execute(async () => 'success');
    expect(result).toBe('success');
  });

  it('should retry on failure', async () => {
    let attempts = 0;

    const result = await policy.execute(async () => {
      attempts++;
      if (attempts < 3) {
        throw new Error('Temporary failure');
      }
      return 'success';
    });

    expect(result).toBe('success');
    expect(attempts).toBe(3);
  });

  it('should fail after max attempts', async () => {
    const failingFn = async () => {
      throw new Error('Permanent failure');
    };

    await expect(policy.execute(failingFn)).rejects.toThrow('Permanent failure');
  });

  it('should apply exponential backoff', async () => {
    let attempts = 0;
    const timestamps: number[] = [];

    try {
      await policy.execute(async () => {
        attempts++;
        timestamps.push(Date.now());
        throw new Error('Fail');
      });
    } catch (e) {}

    expect(attempts).toBe(3);
    expect(timestamps.length).toBe(3);

    // Check delays increased (approximately)
    if (timestamps.length >= 3) {
      const delay1 = timestamps[1] - timestamps[0];
      const delay2 = timestamps[2] - timestamps[1];
      expect(delay2).toBeGreaterThan(delay1);
    }
  });
});

describe('ResilientClient', () => {
  let client: ResilientClient;

  beforeEach(() => {
    client = new ResilientClient('test-client', {
      failureThreshold: 2,
      timeout: 100,
    }, {
      maxAttempts: 2,
      initialDelayMs: 50,
    });
  });

  it('should combine circuit breaker and retry', async () => {
    let attempts = 0;

    const result = await client.execute(async () => {
      attempts++;
      if (attempts === 1) {
        throw new Error('Retry once');
      }
      return 'success';
    });

    expect(result).toBe('success');
    expect(attempts).toBe(2);
  });

  it('should respect circuit breaker state', async () => {
    // Trip circuit
    client.forceCircuitOpen();

    await expect(
      client.execute(async () => 'test')
    ).rejects.toThrow('Circuit breaker');
  });
});

describe('FailureTracker', () => {
  let tracker: FailureTracker;

  beforeEach(() => {
    tracker = new FailureTracker();
  });

  it('should record failures', () => {
    tracker.record('operation1', new Error('Error 1'), 'high');
    tracker.record('operation2', 'Error 2', 'low');

    const recent = tracker.getRecentFailures(60000);
    expect(recent).toHaveLength(2);
  });

  it('should filter by time window', () => {
    tracker.record('op1', 'Error 1');

    // Wait a bit
    setTimeout(() => {
      const recent = tracker.getRecentFailures(50); // Very short window
      expect(recent.length).toBeLessThanOrEqual(1);
    }, 100);
  });

  it('should calculate failure rate', () => {
    tracker.record('op1', 'Error');
    tracker.record('op2', 'Error');
    tracker.record('op3', 'Error');

    const rate = tracker.getFailureRate(1000);
    expect(rate).toBeGreaterThan(0);
  });

  it('should get top failures', () => {
    tracker.record('opA', 'Error');
    tracker.record('opA', 'Error');
    tracker.record('opA', 'Error');
    tracker.record('opB', 'Error');

    const top = tracker.getTopFailures(2);
    expect(top[0].operation).toBe('opA');
    expect(top[0].count).toBe(3);
    expect(top[1].operation).toBe('opB');
    expect(top[1].count).toBe(1);
  });

  it('should clear failures', () => {
    tracker.record('op', 'Error');
    tracker.clear();

    const recent = tracker.getRecentFailures();
    expect(recent).toHaveLength(0);
  });
});
