/**
 * CircuitBreaker - Protects against cascading failures
 * 
 * States:
 * - CLOSED: Normal operation, requests pass through
 * - OPEN: Failures exceeded threshold, requests fail fast
 * - HALF_OPEN: Testing if service recovered
 */

export enum CircuitState {
  CLOSED = 'CLOSED',
  OPEN = 'OPEN',
  HALF_OPEN = 'HALF_OPEN',
}

export interface CircuitBreakerConfig {
  failureThreshold: number; // Failures before opening circuit
  successThreshold: number; // Successes to close circuit from half-open
  timeout: number; // Time in ms before trying half-open
  resetTimeout: number; // Time to reset failure count in closed state
}

export interface CircuitBreakerStats {
  state: CircuitState;
  failureCount: number;
  successCount: number;
  lastFailureTime?: number;
  lastSuccessTime?: number;
  totalRequests: number;
  totalFailures: number;
  totalSuccesses: number;
}

const DEFAULT_CONFIG: CircuitBreakerConfig = {
  failureThreshold: 5,
  successThreshold: 2,
  timeout: 60000, // 1 minute
  resetTimeout: 300000, // 5 minutes
};

export class CircuitBreaker {
  private state: CircuitState = CircuitState.CLOSED;
  private failureCount = 0;
  private successCount = 0;
  private lastFailureTime?: number;
  private lastSuccessTime?: number;
  private totalRequests = 0;
  private totalFailures = 0;
  private totalSuccesses = 0;
  private config: CircuitBreakerConfig;
  private name: string;

  constructor(name: string, config: Partial<CircuitBreakerConfig> = {}) {
    this.name = name;
    this.config = { ...DEFAULT_CONFIG, ...config };
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    this.totalRequests++;

    if (this.state === CircuitState.OPEN) {
      if (this.shouldAttemptReset()) {
        this.state = CircuitState.HALF_OPEN;
        this.successCount = 0;
      } else {
        throw new Error(
          `Circuit breaker [${this.name}] is OPEN. Service unavailable.`
        );
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (error) {
      this.onFailure();
      throw error;
    }
  }

  private onSuccess(): void {
    this.lastSuccessTime = Date.now();
    this.totalSuccesses++;

    if (this.state === CircuitState.HALF_OPEN) {
      this.successCount++;
      if (this.successCount >= this.config.successThreshold) {
        this.reset();
      }
    } else if (this.state === CircuitState.CLOSED) {
      // Reset failure count after successful request
      this.failureCount = 0;
    }
  }

  private onFailure(): void {
    this.lastFailureTime = Date.now();
    this.totalFailures++;
    this.failureCount++;

    if (
      this.state === CircuitState.HALF_OPEN ||
      this.failureCount >= this.config.failureThreshold
    ) {
      this.trip();
    }
  }

  private shouldAttemptReset(): boolean {
    if (!this.lastFailureTime) return false;
    return Date.now() - this.lastFailureTime >= this.config.timeout;
  }

  private trip(): void {
    this.state = CircuitState.OPEN;
    console.warn(
      `Circuit breaker [${this.name}] tripped. State: OPEN. Failures: ${this.failureCount}`
    );
  }

  private reset(): void {
    this.state = CircuitState.CLOSED;
    this.failureCount = 0;
    this.successCount = 0;
    console.info(`Circuit breaker [${this.name}] reset. State: CLOSED.`);
  }

  getStats(): CircuitBreakerStats {
    return {
      state: this.state,
      failureCount: this.failureCount,
      successCount: this.successCount,
      lastFailureTime: this.lastFailureTime,
      lastSuccessTime: this.lastSuccessTime,
      totalRequests: this.totalRequests,
      totalFailures: this.totalFailures,
      totalSuccesses: this.totalSuccesses,
    };
  }

  forceOpen(): void {
    this.state = CircuitState.OPEN;
  }

  forceClosed(): void {
    this.reset();
  }
}

/**
 * RetryPolicy - Configurable retry with exponential backoff
 */
export interface RetryConfig {
  maxAttempts: number;
  initialDelayMs: number;
  maxDelayMs: number;
  backoffMultiplier: number;
  retryableErrors?: string[]; // Error message patterns to retry
}

const DEFAULT_RETRY_CONFIG: RetryConfig = {
  maxAttempts: 3,
  initialDelayMs: 1000,
  maxDelayMs: 30000,
  backoffMultiplier: 2,
};

export class RetryPolicy {
  private config: RetryConfig;

  constructor(config: Partial<RetryConfig> = {}) {
    this.config = { ...DEFAULT_RETRY_CONFIG, ...config };
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    let lastError: Error | null = null;

    for (let attempt = 0; attempt < this.config.maxAttempts; attempt++) {
      try {
        return await fn();
      } catch (error) {
        lastError = error instanceof Error ? error : new Error(String(error));

        if (attempt < this.config.maxAttempts - 1) {
          if (this.isRetryable(lastError)) {
            const delay = this.calculateDelay(attempt);
            console.log(
              `Retry attempt ${attempt + 1}/${this.config.maxAttempts} after ${delay}ms. Error: ${lastError.message}`
            );
            await this.sleep(delay);
          } else {
            throw lastError; // Not retryable, fail fast
          }
        }
      }
    }

    throw lastError || new Error('Max retry attempts exceeded');
  }

  private isRetryable(error: Error): boolean {
    if (!this.config.retryableErrors) return true;

    return this.config.retryableErrors.some((pattern) =>
      error.message.includes(pattern)
    );
  }

  private calculateDelay(attempt: number): number {
    const delay =
      this.config.initialDelayMs * Math.pow(this.config.backoffMultiplier, attempt);
    return Math.min(delay, this.config.maxDelayMs);
  }

  private sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

/**
 * ResilientClient - Combines CircuitBreaker + RetryPolicy
 */
export class ResilientClient {
  private circuitBreaker: CircuitBreaker;
  private retryPolicy: RetryPolicy;

  constructor(
    name: string,
    circuitConfig?: Partial<CircuitBreakerConfig>,
    retryConfig?: Partial<RetryConfig>
  ) {
    this.circuitBreaker = new CircuitBreaker(name, circuitConfig);
    this.retryPolicy = new RetryPolicy(retryConfig);
  }

  async execute<T>(fn: () => Promise<T>): Promise<T> {
    return this.circuitBreaker.execute(async () => {
      return this.retryPolicy.execute(fn);
    });
  }

  getCircuitStats(): CircuitBreakerStats {
    return this.circuitBreaker.getStats();
  }

  forceCircuitOpen(): void {
    this.circuitBreaker.forceOpen();
  }

  forceCircuitClosed(): void {
    this.circuitBreaker.forceClosed();
  }
}

/**
 * FailureTracker - Tracks failure patterns across operations
 */
export interface FailureRecord {
  timestamp: number;
  operation: string;
  error: string;
  severity: 'low' | 'medium' | 'high';
}

export class FailureTracker {
  private failures: FailureRecord[] = [];
  private maxRecords = 1000;

  record(operation: string, error: Error | string, severity: FailureRecord['severity'] = 'medium'): void {
    this.failures.push({
      timestamp: Date.now(),
      operation,
      error: error instanceof Error ? error.message : error,
      severity,
    });

    // Trim old records
    if (this.failures.length > this.maxRecords) {
      this.failures = this.failures.slice(-this.maxRecords);
    }
  }

  getRecentFailures(windowMs: number = 3600000): FailureRecord[] {
    const cutoff = Date.now() - windowMs;
    return this.failures.filter((f) => f.timestamp > cutoff);
  }

  getFailureRate(windowMs: number = 3600000): number {
    const recent = this.getRecentFailures(windowMs);
    if (recent.length === 0) return 0;
    return recent.length / (windowMs / 1000); // failures per second
  }

  getTopFailures(limit: number = 10): Array<{ operation: string; count: number }> {
    const counts = new Map<string, number>();

    for (const failure of this.failures) {
      counts.set(failure.operation, (counts.get(failure.operation) || 0) + 1);
    }

    return Array.from(counts.entries())
      .map(([operation, count]) => ({ operation, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, limit);
  }

  clear(): void {
    this.failures = [];
  }
}
