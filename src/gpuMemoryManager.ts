/**
 * GPU Memory Management utilities for the Obsidian Agent plugin
 * Addresses issue #103: GPU Memory Management - OOM on Large Models
 */

import { GPUMemoryError } from './errors';

export interface GPUMemoryInfo {
	total: number;
	available: number;
	used: number;
	percentUsed: number;
}

export interface ModelMemoryRequirements {
	modelSize: number; // in MB
	contextSize: number;
	recommendedVRAM: number; // in MB
	minimumVRAM: number; // in MB
}

export class GPUMemoryManager {
	private static readonly SAFETY_MARGIN_MB = 1024; // 1GB safety margin
	private static readonly WARNING_THRESHOLD = 0.85; // Warn at 85% usage

	/**
	 * Estimate memory requirements for a model
	 */
	static estimateModelMemory(modelName: string, contextSize: number = 4096): ModelMemoryRequirements {
		// Estimate based on model size from name
		let modelSizeMB = 0;
		
		// Extract parameter count from model name (e.g., "llama-2-13b" -> 13B parameters)
		const paramMatch = modelName.toLowerCase().match(/(\d+)b/);
		if (paramMatch) {
			const params = parseInt(paramMatch[1]);
			
			// Rough estimates based on quantization level (Q4, Q5, Q6, etc.)
			if (modelName.includes('Q4') || modelName.includes('q4')) {
				modelSizeMB = params * 512; // ~4 bits per parameter
			} else if (modelName.includes('Q5') || modelName.includes('q5')) {
				modelSizeMB = params * 640; // ~5 bits per parameter
			} else if (modelName.includes('Q6') || modelName.includes('q6')) {
				modelSizeMB = params * 768; // ~6 bits per parameter
			} else if (modelName.includes('Q8') || modelName.includes('q8')) {
				modelSizeMB = params * 1024; // ~8 bits per parameter
			} else {
				// Default to Q4 estimate
				modelSizeMB = params * 512;
			}
		} else {
			// Default conservative estimate for unknown models
			modelSizeMB = 4096; // 4GB default
		}

		// Add overhead for context size (rough estimate: 1MB per 1000 tokens)
		const contextOverheadMB = (contextSize / 1000) * 1;

		return {
			modelSize: modelSizeMB,
			contextSize,
			recommendedVRAM: modelSizeMB + contextOverheadMB + this.SAFETY_MARGIN_MB,
			minimumVRAM: modelSizeMB + contextOverheadMB + 512
		};
	}

	/**
	 * Calculate optimal number of GPU layers based on available VRAM
	 */
	static calculateOptimalGPULayers(
		availableVRAM: number,
		totalLayers: number,
		memoryPerLayer: number
	): number {
		if (availableVRAM <= 0) {
			return 0; // No GPU, use CPU only
		}

		// Reserve safety margin
		const usableVRAM = availableVRAM - this.SAFETY_MARGIN_MB;
		
		if (usableVRAM <= 0) {
			return 0; // Not enough VRAM
		}

		// Calculate how many layers can fit
		const maxLayers = Math.floor(usableVRAM / memoryPerLayer);
		
		// Don't exceed total layers
		return Math.min(maxLayers, totalLayers);
	}

	/**
	 * Estimate memory per layer for a given model
	 */
	static estimateMemoryPerLayer(modelName: string): number {
		// Extract parameter count
		const paramMatch = modelName.toLowerCase().match(/(\d+)b/);
		if (!paramMatch) {
			return 100; // Default conservative estimate (100MB per layer)
		}

		const params = parseInt(paramMatch[1]);
		
		// Rough estimate: larger models have more parameters per layer
		if (params <= 7) {
			return 64; // ~64MB per layer for 7B models
		} else if (params <= 13) {
			return 128; // ~128MB per layer for 13B models
		} else if (params <= 30) {
			return 256; // ~256MB per layer for 30B models
		} else {
			return 512; // ~512MB per layer for 70B+ models
		}
	}

	/**
	 * Get recommended configuration for a model given available VRAM
	 */
	static getRecommendedConfig(
		modelName: string,
		availableVRAM: number,
		contextSize: number = 4096
	): {
		gpuLayers: number;
		useGPU: boolean;
		warning?: string;
		recommendation?: string;
	} {
		const requirements = this.estimateModelMemory(modelName, contextSize);
		
		// Check if we have enough VRAM
		if (availableVRAM < requirements.minimumVRAM) {
			return {
				gpuLayers: 0,
				useGPU: false,
				warning: `Insufficient VRAM (${availableVRAM}MB available, ${requirements.minimumVRAM}MB minimum required)`,
				recommendation: 'Use CPU-only mode or switch to a smaller model'
			};
		}

		// Calculate optimal layers
		const memoryPerLayer = this.estimateMemoryPerLayer(modelName);
		const totalLayers = this.estimateTotalLayers(modelName);
		const optimalLayers = this.calculateOptimalGPULayers(availableVRAM, totalLayers, memoryPerLayer);

		// Determine if we should use GPU
		const useGPU = optimalLayers > 0;
		
		// Generate warnings/recommendations
		let warning: string | undefined;
		let recommendation: string | undefined;

		if (availableVRAM < requirements.recommendedVRAM) {
			warning = `Limited VRAM (${availableVRAM}MB available, ${requirements.recommendedVRAM}MB recommended)`;
			recommendation = optimalLayers < totalLayers 
				? `Using partial GPU offloading (${optimalLayers}/${totalLayers} layers). Consider reducing context size or using a more quantized model.`
				: 'Consider reducing context size or using a more quantized model for better performance.';
		}

		return {
			gpuLayers: optimalLayers,
			useGPU,
			warning,
			recommendation
		};
	}

	/**
	 * Estimate total number of layers in a model
	 */
	static estimateTotalLayers(modelName: string): number {
		// Extract parameter count
		const paramMatch = modelName.toLowerCase().match(/(\d+)b/);
		if (!paramMatch) {
			return 32; // Default estimate
		}

		const params = parseInt(paramMatch[1]);
		
		// Rough estimates based on common architectures
		if (params <= 1) {
			return 24; // Small models like 1B
		} else if (params <= 7) {
			return 32; // 7B models (LLaMA-7B has 32 layers)
		} else if (params <= 13) {
			return 40; // 13B models (LLaMA-13B has 40 layers)
		} else if (params <= 30) {
			return 60; // 30B models
		} else if (params <= 70) {
			return 80; // 70B models (LLaMA-70B has 80 layers)
		} else {
			return 100; // Larger models
		}
	}

	/**
	 * Validate memory configuration before starting inference
	 */
	static validateMemoryConfig(
		modelName: string,
		gpuLayers: number,
		availableVRAM: number,
		contextSize: number
	): void {
		const requirements = this.estimateModelMemory(modelName, contextSize);
		const memoryPerLayer = this.estimateMemoryPerLayer(modelName);
		const estimatedUsage = gpuLayers * memoryPerLayer;

		// Check if configuration is safe
		if (estimatedUsage > availableVRAM - this.SAFETY_MARGIN_MB) {
			throw new GPUMemoryError(
				`Memory configuration may cause OOM: estimated usage ${estimatedUsage}MB exceeds available VRAM ${availableVRAM}MB (with ${this.SAFETY_MARGIN_MB}MB safety margin)`,
				estimatedUsage,
				availableVRAM
			);
		}

		// Warn if approaching limits
		const percentUsed = estimatedUsage / availableVRAM;
		if (percentUsed > this.WARNING_THRESHOLD) {
			console.warn(`GPU memory usage approaching limit: ${(percentUsed * 100).toFixed(1)}% (${estimatedUsage}MB / ${availableVRAM}MB)`);
		}
	}

	/**
	 * Get fallback configuration for CPU-only mode
	 */
	static getCPUFallbackConfig(): {
		gpuLayers: number;
		useGPU: boolean;
		message: string;
	} {
		return {
			gpuLayers: 0,
			useGPU: false,
			message: 'Falling back to CPU-only mode due to insufficient GPU memory'
		};
	}
}
