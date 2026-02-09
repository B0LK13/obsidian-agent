/**
 * Centralized Configuration Management System
 * Provides validation, migration, and type-safe configuration
 */

import { ObsidianAgentSettings, DEFAULT_SETTINGS } from '../../settings';
import { logger } from '../logger';

export interface ConfigValidationResult {
valid: boolean;
errors: string[];
warnings: string[];
}

export class ConfigManager {
private static instance: ConfigManager;
private config: ObsidianAgentSettings;

private constructor(initialConfig: ObsidianAgentSettings) {
this.config = initialConfig;
}

static getInstance(config?: ObsidianAgentSettings): ConfigManager {
if (!ConfigManager.instance && config) {
ConfigManager.instance = new ConfigManager(config);
} else if (!ConfigManager.instance) {
ConfigManager.instance = new ConfigManager(DEFAULT_SETTINGS);
}
return ConfigManager.instance;
}

validate(): ConfigValidationResult {
const errors: string[] = [];
const warnings: string[] = [];

if (!['openai', 'anthropic', 'ollama', 'custom'].includes(this.config.apiProvider)) {
errors.push(`Invalid API provider: ${this.config.apiProvider}`);
}

if (this.config.apiProvider !== 'ollama' && !this.config.apiKey) {
warnings.push('API key is not set');
}

if (!this.config.model || this.config.model.trim() === '') {
errors.push('Model name is required');
}

if (this.config.temperature < 0 || this.config.temperature > 2) {
errors.push('Temperature must be between 0 and 2');
}

if (this.config.maxTokens < 1 || this.config.maxTokens > 128000) {
errors.push('Max tokens must be between 1 and 128000');
}

return {
valid: errors.length === 0,
errors,
warnings
};
}

get<K extends keyof ObsidianAgentSettings>(key: K): ObsidianAgentSettings[K] {
return this.config[key];
}

set<K extends keyof ObsidianAgentSettings>(key: K, value: ObsidianAgentSettings[K]): boolean {
const oldValue = this.config[key];
this.config[key] = value;

const validation = this.validate();
if (!validation.valid) {
this.config[key] = oldValue;
logger.error('Configuration update failed validation', undefined, {
component: 'ConfigManager',
key: key.toString()
});
return false;
}

logger.info('Configuration updated', { component: 'ConfigManager', key: key.toString() });
return true;
}

update(updates: Partial<ObsidianAgentSettings>): boolean {
const backup = { ...this.config };
Object.assign(this.config, updates);

const validation = this.validate();
if (!validation.valid) {
this.config = backup;
logger.error('Bulk configuration update failed', undefined, { component: 'ConfigManager' });
return false;
}

logger.info('Bulk configuration updated', { component: 'ConfigManager' });
return true;
}

getAll(): ObsidianAgentSettings {
return { ...this.config };
}

reset(): void {
this.config = { ...DEFAULT_SETTINGS };
logger.info('Configuration reset to defaults', { component: 'ConfigManager' });
}

export(): string {
return JSON.stringify(this.config, null, 2);
}
}

export function getConfigManager(config?: ObsidianAgentSettings): ConfigManager {
return ConfigManager.getInstance(config);
}
