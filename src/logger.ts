/**
 * Structured Logging System for Obsidian Agent
 * Provides JSON-formatted logs with levels, contexts, and metadata
 */

export enum LogLevel {
	DEBUG = 'DEBUG',
	INFO = 'INFO',
	WARN = 'WARN',
	ERROR = 'ERROR',
	PERFORMANCE = 'PERFORMANCE'
}

export interface LogContext {
	component?: string;
	requestId?: string;
	userId?: string;
	operation?: string;
	[key: string]: any;
}

export interface LogEntry {
	timestamp: string;
	level: LogLevel;
	message: string;
	context?: LogContext;
	error?: {
		name: string;
		message: string;
		stack?: string;
	};
	performance?: {
		duration: number;
		memoryUsage?: number;
	};
}

export class Logger {
	private static instance: Logger;
	private logHistory: LogEntry[] = [];
	private maxHistorySize = 1000;
	private minLevel: LogLevel = LogLevel.INFO;

	private constructor() {}

	static getInstance(): Logger {
		if (!Logger.instance) {
			Logger.instance = new Logger();
		}
		return Logger.instance;
	}

	setLogLevel(level: LogLevel): void {
		this.minLevel = level;
	}

	private shouldLog(level: LogLevel): boolean {
		const levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARN, LogLevel.ERROR, LogLevel.PERFORMANCE];
		return levels.indexOf(level) >= levels.indexOf(this.minLevel);
	}

	private createLogEntry(level: LogLevel, message: string, context?: LogContext, error?: Error, performance?: { duration: number }): LogEntry {
		const entry: LogEntry = {
			timestamp: new Date().toISOString(),
			level,
			message,
			context
		};

		if (error) {
			entry.error = {
				name: error.name,
				message: error.message,
				stack: error.stack
			};
		}

		if (performance) {
			entry.performance = {
				duration: performance.duration,
				memoryUsage: (performance as any).memoryUsage
			};
		}

		return entry;
	}

	private log(entry: LogEntry): void {
		if (!this.shouldLog(entry.level)) {
			return;
		}

		// Store in history
		this.logHistory.push(entry);
		if (this.logHistory.length > this.maxHistorySize) {
			this.logHistory.shift();
		}

		// Console output
		const formattedMessage = `[${entry.timestamp}] [${entry.level}]${entry.context?.component ? ` [${entry.context.component}]` : ''} ${entry.message}`;
		
		switch (entry.level) {
			case LogLevel.ERROR:
				console.error(formattedMessage, entry);
				break;
			case LogLevel.WARN:
				console.warn(formattedMessage, entry);
				break;
			case LogLevel.DEBUG:
				console.debug(formattedMessage, entry);
				break;
			default:
				console.log(formattedMessage, entry);
		}
	}

	debug(message: string, context?: LogContext): void {
		this.log(this.createLogEntry(LogLevel.DEBUG, message, context));
	}

	info(message: string, context?: LogContext): void {
		this.log(this.createLogEntry(LogLevel.INFO, message, context));
	}

	warn(message: string, context?: LogContext): void {
		this.log(this.createLogEntry(LogLevel.WARN, message, context));
	}

	error(message: string, error?: Error, context?: LogContext): void {
		this.log(this.createLogEntry(LogLevel.ERROR, message, context, error));
	}

	performance(message: string, duration: number, context?: LogContext): void {
		this.log(this.createLogEntry(LogLevel.PERFORMANCE, message, context, undefined, { duration }));
	}

	// Utility method for timing operations
	async measureAsync<T>(operation: string, fn: () => Promise<T>, context?: LogContext): Promise<T> {
		const startTime = performance.now();
		try {
			const result = await fn();
			const duration = performance.now() - startTime;
			this.performance(`${operation} completed`, duration, context);
			return result;
		} catch (error) {
			const duration = performance.now() - startTime;
			this.error(`${operation} failed after ${duration.toFixed(2)}ms`, error as Error, context);
			throw error;
		}
	}

	// Get logs for export/debugging
	getLogs(filter?: { level?: LogLevel; component?: string; since?: Date }): LogEntry[] {
		let logs = this.logHistory;

		if (filter) {
			if (filter.level) {
				logs = logs.filter(log => log.level === filter.level);
			}
			if (filter.component) {
				logs = logs.filter(log => log.context?.component === filter.component);
			}
			if (filter.since) {
				const sinceDate = filter.since;
				logs = logs.filter(log => new Date(log.timestamp) >= sinceDate);
			}
		}

		return logs;
	}

	// Export logs as JSON
	exportLogs(): string {
		return JSON.stringify(this.logHistory, null, 2);
	}

	// Clear log history
	clearLogs(): void {
		this.logHistory = [];
	}
}

// Export singleton instance
export const logger = Logger.getInstance();
