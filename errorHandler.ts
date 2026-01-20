import { Notice } from 'obsidian';
import { Logger } from './logger';

export enum ErrorSeverity {
	LOW = 'low',
	MEDIUM = 'medium',
	HIGH = 'high',
	CRITICAL = 'critical'
}

export enum ErrorCategory {
	NETWORK = 'network',
	API = 'api',
	FILE_SYSTEM = 'file_system',
	VALIDATION = 'validation',
	CONFIGURATION = 'configuration',
	UNKNOWN = 'unknown'
}

export interface ErrorContext {
	category: ErrorCategory;
	severity: ErrorSeverity;
	operation: string;
	details?: Record<string, any>;
	userMessage?: string;
}

export class AppError extends Error {
	category: ErrorCategory;
	severity: ErrorSeverity;
	operation: string;
	details?: Record<string, any>;
	userMessage?: string;
	timestamp: Date;

	constructor(message: string, context: ErrorContext) {
		super(message);
		this.name = 'AppError';
		this.category = context.category;
		this.severity = context.severity;
		this.operation = context.operation;
		this.details = context.details;
		this.userMessage = context.userMessage;
		this.timestamp = new Date();

		// Maintains proper stack trace for where error was thrown (only in V8)
		if (Error.captureStackTrace) {
			Error.captureStackTrace(this, AppError);
		}
	}

	toJSON() {
		return {
			name: this.name,
			message: this.message,
			category: this.category,
			severity: this.severity,
			operation: this.operation,
			details: this.details,
			userMessage: this.userMessage,
			timestamp: this.timestamp,
			stack: this.stack
		};
	}
}

export class ErrorHandler {
	private logger: Logger;
	private errorCount: Map<string, number> = new Map();
	private readonly MAX_ERRORS_PER_OPERATION = 5;
	private readonly ERROR_RESET_INTERVAL = 60000; // 1 minute

	constructor(logger: Logger) {
		this.logger = logger;
		this.setupErrorResetInterval();
	}

	private setupErrorResetInterval(): void {
		setInterval(() => {
			this.errorCount.clear();
		}, this.ERROR_RESET_INTERVAL);
	}

	/**
	 * Handle an error with appropriate logging and user notification
	 */
	handle(error: Error | AppError, context?: Partial<ErrorContext>): void {
		const appError = this.normalizeError(error, context);
		
		// Log the error
		this.logError(appError);

		// Check if we should show notification (avoid spam)
		if (this.shouldNotifyUser(appError)) {
			this.notifyUser(appError);
		}

		// Track error for rate limiting
		this.trackError(appError);
	}

	/**
	 * Normalize any error to AppError
	 */
	private normalizeError(error: Error | AppError, context?: Partial<ErrorContext>): AppError {
		if (error instanceof AppError) {
			return error;
		}

		const category = this.categorizeError(error);
		const severity = this.determineSeverity(error, category);

		return new AppError(error.message, {
			category,
			severity,
			operation: context?.operation || 'unknown',
			details: {
				...context?.details,
				originalError: error.name,
				stack: error.stack
			},
			userMessage: context?.userMessage
		});
	}

	/**
	 * Categorize error based on error properties
	 */
	private categorizeError(error: Error): ErrorCategory {
		const message = error.message.toLowerCase();

		if (message.includes('network') || message.includes('fetch') || message.includes('timeout')) {
			return ErrorCategory.NETWORK;
		}
		if (message.includes('api') || message.includes('unauthorized') || message.includes('forbidden')) {
			return ErrorCategory.API;
		}
		if (message.includes('file') || message.includes('path') || message.includes('read') || message.includes('write')) {
			return ErrorCategory.FILE_SYSTEM;
		}
		if (message.includes('invalid') || message.includes('validation') || message.includes('required')) {
			return ErrorCategory.VALIDATION;
		}
		if (message.includes('config') || message.includes('setting')) {
			return ErrorCategory.CONFIGURATION;
		}

		return ErrorCategory.UNKNOWN;
	}

	/**
	 * Determine error severity
	 */
	private determineSeverity(error: Error, category: ErrorCategory): ErrorSeverity {
		// Network and API errors are usually medium severity
		if (category === ErrorCategory.NETWORK || category === ErrorCategory.API) {
			return ErrorSeverity.MEDIUM;
		}

		// File system errors can be critical
		if (category === ErrorCategory.FILE_SYSTEM) {
			return ErrorSeverity.HIGH;
		}

		// Configuration errors are critical as they block functionality
		if (category === ErrorCategory.CONFIGURATION) {
			return ErrorSeverity.CRITICAL;
		}

		// Validation errors are low severity
		if (category === ErrorCategory.VALIDATION) {
			return ErrorSeverity.LOW;
		}

		return ErrorSeverity.MEDIUM;
	}

	/**
	 * Log error with appropriate level
	 */
	private logError(error: AppError): void {
		const logMessage = `[${error.category}] ${error.operation}: ${error.message}`;
		const logContext = {
			severity: error.severity,
			details: error.details,
			timestamp: error.timestamp,
			stack: error.stack
		};

		switch (error.severity) {
			case ErrorSeverity.CRITICAL:
				this.logger.error(logMessage, logContext);
				break;
			case ErrorSeverity.HIGH:
				this.logger.error(logMessage, logContext);
				break;
			case ErrorSeverity.MEDIUM:
				this.logger.warn(logMessage, logContext);
				break;
			case ErrorSeverity.LOW:
				this.logger.info(logMessage, logContext);
				break;
		}
	}

	/**
	 * Check if we should notify user (avoid notification spam)
	 */
	private shouldNotifyUser(error: AppError): boolean {
		const errorKey = `${error.category}:${error.operation}`;
		const count = this.errorCount.get(errorKey) || 0;
		
		// Only show first few errors per operation to avoid spam
		return count < this.MAX_ERRORS_PER_OPERATION && 
		       error.severity !== ErrorSeverity.LOW;
	}

	/**
	 * Notify user with friendly message
	 */
	private notifyUser(error: AppError): void {
		const message = error.userMessage || this.getFriendlyMessage(error);
		
		// Show notice with duration based on severity
		const duration = this.getNoticeDuration(error.severity);
		new Notice(message, duration);
	}

	/**
	 * Get friendly error message for user
	 */
	private getFriendlyMessage(error: AppError): string {
		const baseMessage = this.getBaseMessage(error.category);
		
		if (error.severity === ErrorSeverity.CRITICAL) {
			return `⛔ ${baseMessage} Please check your settings.`;
		} else if (error.severity === ErrorSeverity.HIGH) {
			return `❌ ${baseMessage} Please try again.`;
		} else {
			return `⚠️ ${baseMessage}`;
		}
	}

	/**
	 * Get base message for error category
	 */
	private getBaseMessage(category: ErrorCategory): string {
		switch (category) {
			case ErrorCategory.NETWORK:
				return 'Network error occurred.';
			case ErrorCategory.API:
				return 'API request failed.';
			case ErrorCategory.FILE_SYSTEM:
				return 'File operation failed.';
			case ErrorCategory.VALIDATION:
				return 'Invalid input provided.';
			case ErrorCategory.CONFIGURATION:
				return 'Configuration error detected.';
			default:
				return 'An error occurred.';
		}
	}

	/**
	 * Get notice duration based on severity
	 */
	private getNoticeDuration(severity: ErrorSeverity): number {
		switch (severity) {
			case ErrorSeverity.CRITICAL:
				return 10000; // 10 seconds
			case ErrorSeverity.HIGH:
				return 7000;  // 7 seconds
			case ErrorSeverity.MEDIUM:
				return 5000;  // 5 seconds
			case ErrorSeverity.LOW:
				return 3000;  // 3 seconds
			default:
				return 5000;
		}
	}

	/**
	 * Track error count for rate limiting
	 */
	private trackError(error: AppError): void {
		const errorKey = `${error.category}:${error.operation}`;
		const count = this.errorCount.get(errorKey) || 0;
		this.errorCount.set(errorKey, count + 1);
	}

	/**
	 * Create a wrapped async function with error handling
	 */
	wrapAsync<T>(
		operation: string, 
		fn: () => Promise<T>, 
		context?: Partial<ErrorContext>
	): Promise<T> {
		return fn().catch((error) => {
			this.handle(error, { operation, ...context });
			throw error;
		});
	}

	/**
	 * Create a recovery handler for operations
	 */
	async withRecovery<T>(
		operation: string,
		primaryFn: () => Promise<T>,
		fallbackFn?: () => Promise<T>,
		context?: Partial<ErrorContext>
	): Promise<T | null> {
		try {
			return await primaryFn();
		} catch (error) {
			this.handle(error, { operation, ...context });
			
			if (fallbackFn) {
				try {
					this.logger.info(`Attempting fallback for operation: ${operation}`);
					return await fallbackFn();
				} catch (fallbackError) {
					this.handle(fallbackError, { 
						operation: `${operation} (fallback)`, 
						...context 
					});
				}
			}
			
			return null;
		}
	}

	/**
	 * Validate API key configuration
	 */
	validateApiKey(apiKey: string | undefined, provider: string): void {
		if (!apiKey || apiKey.trim() === '') {
			throw new AppError(`API key for ${provider} is not configured`, {
				category: ErrorCategory.CONFIGURATION,
				severity: ErrorSeverity.CRITICAL,
				operation: 'validateApiKey',
				userMessage: `Please configure your ${provider} API key in settings`
			});
		}
	}

	/**
	 * Validate URL configuration
	 */
	validateUrl(url: string | undefined, name: string): void {
		if (!url || url.trim() === '') {
			throw new AppError(`${name} URL is not configured`, {
				category: ErrorCategory.CONFIGURATION,
				severity: ErrorSeverity.CRITICAL,
				operation: 'validateUrl',
				userMessage: `Please configure ${name} URL in settings`
			});
		}

		try {
			new URL(url);
		} catch {
			throw new AppError(`Invalid ${name} URL: ${url}`, {
				category: ErrorCategory.VALIDATION,
				severity: ErrorSeverity.HIGH,
				operation: 'validateUrl',
				userMessage: `Please provide a valid ${name} URL in settings`
			});
		}
	}
}
