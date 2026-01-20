export enum LogLevel {
	DEBUG = 0,
	INFO = 1,
	WARN = 2,
	ERROR = 3,
	NONE = 4
}

export interface LogEntry {
	timestamp: Date;
	level: LogLevel;
	message: string;
	context?: Record<string, any>;
	operation?: string;
}

export interface LoggerConfig {
	level: LogLevel;
	enableConsole: boolean;
	enableFile: boolean;
	maxLogEntries: number;
	logFilePath?: string;
}

const DEFAULT_LOGGER_CONFIG: LoggerConfig = {
	level: LogLevel.INFO,
	enableConsole: true,
	enableFile: false,
	maxLogEntries: 1000
};

export class Logger {
	private config: LoggerConfig;
	private logEntries: LogEntry[] = [];
	private listeners: Set<(entry: LogEntry) => void> = new Set();

	constructor(config?: Partial<LoggerConfig>) {
		this.config = { ...DEFAULT_LOGGER_CONFIG, ...config };
	}

	/**
	 * Log debug message
	 */
	debug(message: string, context?: Record<string, any>): void {
		this.log(LogLevel.DEBUG, message, context);
	}

	/**
	 * Log info message
	 */
	info(message: string, context?: Record<string, any>): void {
		this.log(LogLevel.INFO, message, context);
	}

	/**
	 * Log warning message
	 */
	warn(message: string, context?: Record<string, any>): void {
		this.log(LogLevel.WARN, message, context);
	}

	/**
	 * Log error message
	 */
	error(message: string, context?: Record<string, any>): void {
		this.log(LogLevel.ERROR, message, context);
	}

	/**
	 * Core logging method
	 */
	private log(level: LogLevel, message: string, context?: Record<string, any>): void {
		if (level < this.config.level) {
			return;
		}

		const entry: LogEntry = {
			timestamp: new Date(),
			level,
			message,
			context,
			operation: context?.operation
		};

		// Store log entry
		this.addLogEntry(entry);

		// Output to console if enabled
		if (this.config.enableConsole) {
			this.logToConsole(entry);
		}

		// Notify listeners
		this.notifyListeners(entry);
	}

	/**
	 * Add log entry to internal storage
	 */
	private addLogEntry(entry: LogEntry): void {
		this.logEntries.push(entry);

		// Trim log entries if exceeds max
		if (this.logEntries.length > this.config.maxLogEntries) {
			this.logEntries = this.logEntries.slice(-this.config.maxLogEntries);
		}
	}

	/**
	 * Log to browser console
	 */
	private logToConsole(entry: LogEntry): void {
		const prefix = `[${this.getLogLevelName(entry.level)}]`;
		const timestamp = entry.timestamp.toISOString();
		const message = `${prefix} ${timestamp} - ${entry.message}`;

		switch (entry.level) {
			case LogLevel.DEBUG:
				console.debug(message, entry.context || '');
				break;
			case LogLevel.INFO:
				console.info(message, entry.context || '');
				break;
			case LogLevel.WARN:
				console.warn(message, entry.context || '');
				break;
			case LogLevel.ERROR:
				console.error(message, entry.context || '');
				break;
		}
	}

	/**
	 * Get log level name
	 */
	private getLogLevelName(level: LogLevel): string {
		switch (level) {
			case LogLevel.DEBUG: return 'DEBUG';
			case LogLevel.INFO: return 'INFO';
			case LogLevel.WARN: return 'WARN';
			case LogLevel.ERROR: return 'ERROR';
			default: return 'UNKNOWN';
		}
	}

	/**
	 * Notify all listeners
	 */
	private notifyListeners(entry: LogEntry): void {
		this.listeners.forEach(listener => {
			try {
				listener(entry);
			} catch (error) {
				console.error('Error in log listener:', error);
			}
		});
	}

	/**
	 * Add a listener for log entries
	 */
	addListener(listener: (entry: LogEntry) => void): void {
		this.listeners.add(listener);
	}

	/**
	 * Remove a listener
	 */
	removeListener(listener: (entry: LogEntry) => void): void {
		this.listeners.delete(listener);
	}

	/**
	 * Get recent log entries
	 */
	getRecentLogs(count: number = 100): LogEntry[] {
		return this.logEntries.slice(-count);
	}

	/**
	 * Get logs filtered by level
	 */
	getLogsByLevel(level: LogLevel, count: number = 100): LogEntry[] {
		return this.logEntries
			.filter(entry => entry.level === level)
			.slice(-count);
	}

	/**
	 * Get logs filtered by operation
	 */
	getLogsByOperation(operation: string, count: number = 100): LogEntry[] {
		return this.logEntries
			.filter(entry => entry.operation === operation)
			.slice(-count);
	}

	/**
	 * Clear all logs
	 */
	clearLogs(): void {
		this.logEntries = [];
	}

	/**
	 * Update logger configuration
	 */
	updateConfig(config: Partial<LoggerConfig>): void {
		this.config = { ...this.config, ...config };
	}

	/**
	 * Get current configuration
	 */
	getConfig(): LoggerConfig {
		return { ...this.config };
	}

	/**
	 * Export logs as JSON
	 */
	exportLogsAsJSON(): string {
		return JSON.stringify(this.logEntries, null, 2);
	}

	/**
	 * Export logs as plain text
	 */
	exportLogsAsText(): string {
		return this.logEntries.map(entry => {
			const timestamp = entry.timestamp.toISOString();
			const level = this.getLogLevelName(entry.level);
			const context = entry.context ? ` | ${JSON.stringify(entry.context)}` : '';
			return `[${level}] ${timestamp} - ${entry.message}${context}`;
		}).join('\n');
	}

	/**
	 * Get log statistics
	 */
	getStats(): {
		total: number;
		byLevel: Record<string, number>;
		recentErrors: number;
	} {
		const now = Date.now();
		const oneHourAgo = now - 3600000;

		const stats: {
			total: number;
			byLevel: Record<string, number>;
			recentErrors: number;
		} = {
			total: this.logEntries.length,
			byLevel: {
				'DEBUG': 0,
				'INFO': 0,
				'WARN': 0,
				'ERROR': 0
			},
			recentErrors: 0
		};

		this.logEntries.forEach(entry => {
			const levelName = this.getLogLevelName(entry.level);
			stats.byLevel[levelName] = (stats.byLevel[levelName] || 0) + 1;

			if (entry.level === LogLevel.ERROR && entry.timestamp.getTime() > oneHourAgo) {
				stats.recentErrors++;
			}
		});

		return stats;
	}

	/**
	 * Create a child logger with operation context
	 */
	createChildLogger(operation: string): OperationLogger {
		return new OperationLogger(this, operation);
	}
}

/**
 * Operation-specific logger that automatically includes operation context
 */
export class OperationLogger {
	private parent: Logger;
	private operation: string;
	private startTime: number;

	constructor(parent: Logger, operation: string) {
		this.parent = parent;
		this.operation = operation;
		this.startTime = Date.now();
		this.parent.debug(`Operation started: ${operation}`);
	}

	debug(message: string, context?: Record<string, any>): void {
		this.parent.debug(message, { ...context, operation: this.operation });
	}

	info(message: string, context?: Record<string, any>): void {
		this.parent.info(message, { ...context, operation: this.operation });
	}

	warn(message: string, context?: Record<string, any>): void {
		this.parent.warn(message, { ...context, operation: this.operation });
	}

	error(message: string, context?: Record<string, any>): void {
		this.parent.error(message, { ...context, operation: this.operation });
	}

	/**
	 * Complete the operation and log duration
	 */
	complete(success: boolean = true): void {
		const duration = Date.now() - this.startTime;
		const message = `Operation ${success ? 'completed' : 'failed'}: ${this.operation}`;
		
		if (success) {
			this.parent.info(message, { 
				operation: this.operation, 
				duration,
				durationMs: `${duration}ms`
			});
		} else {
			this.parent.error(message, { 
				operation: this.operation, 
				duration,
				durationMs: `${duration}ms`
			});
		}
	}
}
