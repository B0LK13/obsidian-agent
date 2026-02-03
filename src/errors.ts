/**
 * Custom error classes for the Obsidian Agent plugin
 */

export class AgentError extends Error {
	constructor(message: string, public readonly code?: string) {
		super(message);
		this.name = 'AgentError';
		Object.setPrototypeOf(this, AgentError.prototype);
	}
}

export class ValidationError extends AgentError {
	constructor(message: string, public readonly field?: string) {
		super(message, 'VALIDATION_ERROR');
		this.name = 'ValidationError';
		Object.setPrototypeOf(this, ValidationError.prototype);
	}
}

export class APIError extends AgentError {
	constructor(
		message: string,
		public readonly statusCode?: number,
		public readonly provider?: string
	) {
		super(message, 'API_ERROR');
		this.name = 'APIError';
		Object.setPrototypeOf(this, APIError.prototype);
	}
}

export class ConfigurationError extends AgentError {
	constructor(message: string, public readonly setting?: string) {
		super(message, 'CONFIGURATION_ERROR');
		this.name = 'ConfigurationError';
		Object.setPrototypeOf(this, ConfigurationError.prototype);
	}
}

export class NetworkError extends AgentError {
	constructor(message: string, public readonly originalError?: Error) {
		super(message, 'NETWORK_ERROR');
		this.name = 'NetworkError';
		Object.setPrototypeOf(this, NetworkError.prototype);
	}
}

export class CacheError extends AgentError {
	constructor(message: string) {
		super(message, 'CACHE_ERROR');
		this.name = 'CacheError';
		Object.setPrototypeOf(this, CacheError.prototype);
	}
}

export class ContextError extends AgentError {
	constructor(message: string) {
		super(message, 'CONTEXT_ERROR');
		this.name = 'ContextError';
		Object.setPrototypeOf(this, ContextError.prototype);
	}
}

export class GPUMemoryError extends AgentError {
	constructor(message: string, public readonly requiredMemory?: number, public readonly availableMemory?: number) {
		super(message, 'GPU_MEMORY_ERROR');
		this.name = 'GPUMemoryError';
		Object.setPrototypeOf(this, GPUMemoryError.prototype);
	}
}
