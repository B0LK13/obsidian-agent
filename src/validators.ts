/**
 * Input validation utilities for the Obsidian Agent plugin
 */

import { ValidationError } from './errors';

export class Validators {
	/**
	 * Validate that a value is not null or undefined
	 */
	static required<T>(value: T | null | undefined, fieldName: string): T {
		if (value === null || value === undefined) {
			throw new ValidationError(`${fieldName} is required`, fieldName);
		}
		return value;
	}

	/**
	 * Validate that a string is not empty
	 */
	static notEmpty(value: string | null | undefined, fieldName: string): string {
		const required = this.required(value, fieldName);
		if (typeof required !== 'string' || required.trim().length === 0) {
			throw new ValidationError(`${fieldName} cannot be empty`, fieldName);
		}
		return required;
	}

	/**
	 * Validate that a number is within a range
	 */
	static inRange(value: number, min: number, max: number, fieldName: string): number {
		if (typeof value !== 'number' || isNaN(value)) {
			throw new ValidationError(`${fieldName} must be a valid number`, fieldName);
		}
		if (value < min || value > max) {
			throw new ValidationError(
				`${fieldName} must be between ${min} and ${max}`,
				fieldName
			);
		}
		return value;
	}

	/**
	 * Validate that a value is a positive number
	 */
	static positive(value: number, fieldName: string): number {
		if (typeof value !== 'number' || isNaN(value) || value <= 0) {
			throw new ValidationError(`${fieldName} must be a positive number`, fieldName);
		}
		return value;
	}

	/**
	 * Validate that a value is a non-negative number
	 */
	static nonNegative(value: number, fieldName: string): number {
		if (typeof value !== 'number' || isNaN(value) || value < 0) {
			throw new ValidationError(`${fieldName} must be a non-negative number`, fieldName);
		}
		return value;
	}

	/**
	 * Validate that an array is not empty
	 */
	static notEmptyArray<T>(value: T[] | null | undefined, fieldName: string): T[] {
		const required = this.required(value, fieldName);
		if (!Array.isArray(required) || required.length === 0) {
			throw new ValidationError(`${fieldName} must be a non-empty array`, fieldName);
		}
		return required;
	}

	/**
	 * Validate that a value is one of the allowed options
	 */
	static oneOf<T>(value: T, options: T[], fieldName: string): T {
		if (!options.includes(value)) {
			throw new ValidationError(
				`${fieldName} must be one of: ${options.join(', ')}`,
				fieldName
			);
		}
		return value;
	}

	/**
	 * Validate API key format
	 */
	static apiKey(value: string | null | undefined, fieldName: string = 'API key'): string {
		const key = this.notEmpty(value, fieldName);
		if (key.length < 10) {
			throw new ValidationError(`${fieldName} is too short (minimum 10 characters)`, fieldName);
		}
		return key;
	}

	/**
	 * Validate URL format
	 */
	static url(value: string | null | undefined, fieldName: string): string {
		const url = this.notEmpty(value, fieldName);
		try {
			new URL(url);
		} catch {
			throw new ValidationError(`${fieldName} is not a valid URL`, fieldName);
		}
		return url;
	}

	/**
	 * Validate temperature value for AI models (0-2 range)
	 */
	static temperature(value: number): number {
		return this.inRange(value, 0, 2, 'temperature');
	}

	/**
	 * Validate max tokens value
	 */
	static maxTokens(value: number): number {
		return this.inRange(value, 1, 100000, 'maxTokens');
	}

	/**
	 * Safe array access with bounds checking
	 */
	static safeArrayAccess<T>(array: T[], index: number, defaultValue?: T): T | undefined {
		if (!Array.isArray(array)) {
			return defaultValue;
		}
		if (index < 0 || index >= array.length) {
			return defaultValue;
		}
		return array[index];
	}

	/**
	 * Safe object property access
	 */
	static safeGet<T, K extends keyof T>(obj: T | null | undefined, key: K, defaultValue?: T[K]): T[K] | undefined {
		if (!obj || typeof obj !== 'object') {
			return defaultValue;
		}
		const value = obj[key];
		return value !== undefined ? value : defaultValue;
	}

	/**
	 * Validate and sanitize string length
	 */
	static maxLength(value: string, maxLen: number, fieldName: string): string {
		const str = this.required(value, fieldName);
		if (typeof str !== 'string') {
			throw new ValidationError(`${fieldName} must be a string`, fieldName);
		}
		if (str.length > maxLen) {
			return str.substring(0, maxLen);
		}
		return str;
	}

	/**
	 * Type guard for checking if value is a string
	 */
	static isString(value: unknown): value is string {
		return typeof value === 'string';
	}

	/**
	 * Type guard for checking if value is a number
	 */
	static isNumber(value: unknown): value is number {
		return typeof value === 'number' && !isNaN(value);
	}

	/**
	 * Type guard for checking if value is an object
	 */
	static isObject(value: unknown): value is Record<string, unknown> {
		return typeof value === 'object' && value !== null && !Array.isArray(value);
	}

	/**
	 * Type guard for checking if value is an array
	 */
	static isArray(value: unknown): value is unknown[] {
		return Array.isArray(value);
	}
}
