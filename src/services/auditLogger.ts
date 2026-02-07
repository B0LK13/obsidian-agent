import { Vault } from 'obsidian';
import { randomUUID } from 'crypto';

export interface AuditEntry {
  operationId: string;
  timestamp: number;
  operation: 'ingest' | 'index' | 'query' | 'rollback' | 'delete';
  status: 'started' | 'completed' | 'failed' | 'rolled_back';
  details: Record<string, any>;
  rollbackMetadata?: RollbackMetadata;
  error?: string;
  checksum?: string;
}

export interface RollbackMetadata {
  previousState?: any;
  affectedFiles?: string[];
  affectedIndices?: string[];
  recoverySteps?: string[];
}

export interface AuditQuery {
  operationId?: string;
  operation?: string;
  status?: string;
  since?: number;
  until?: number;
  limit?: number;
}

export class AuditLogger {
  private entries: Map<string, AuditEntry[]> = new Map();
  private vault: Vault;
  private auditFile: string = '.obsidian/plugins/obsidian-agent/audit.json';
  private checksumHistory: Map<string, string> = new Map();

  constructor(vault: Vault) {
    this.vault = vault;
  }

  async initialize(): Promise<void> {
    await this.load();
  }

  createOperationId(): string {
    return randomUUID();
  }

  async logOperation(
    operationId: string,
    operation: AuditEntry['operation'],
    status: AuditEntry['status'],
    details: Record<string, any>,
    rollbackMetadata?: RollbackMetadata
  ): Promise<void> {
    const entry: AuditEntry = {
      operationId,
      timestamp: Date.now(),
      operation,
      status,
      details,
      rollbackMetadata,
    };

    // Add tamper detection checksum
    entry.checksum = await this.generateChecksum(entry);

    if (!this.entries.has(operationId)) {
      this.entries.set(operationId, []);
    }
    this.entries.get(operationId)!.push(entry);

    // Store checksum for verification
    this.checksumHistory.set(`${operationId}-${entry.timestamp}`, entry.checksum);

    await this.save();
  }

  async startOperation(
    operationId: string,
    operation: AuditEntry['operation'],
    details: Record<string, any>
  ): Promise<void> {
    await this.logOperation(operationId, operation, 'started', details);
  }

  async completeOperation(
    operationId: string,
    operation: AuditEntry['operation'],
    details: Record<string, any>,
    rollbackMetadata?: RollbackMetadata
  ): Promise<void> {
    await this.logOperation(operationId, operation, 'completed', details, rollbackMetadata);
  }

  async failOperation(
    operationId: string,
    operation: AuditEntry['operation'],
    details: Record<string, any>,
    error: string
  ): Promise<void> {
    const entry: AuditEntry = {
      operationId,
      timestamp: Date.now(),
      operation,
      status: 'failed',
      details,
      error,
    };
    entry.checksum = await this.generateChecksum(entry);

    if (!this.entries.has(operationId)) {
      this.entries.set(operationId, []);
    }
    this.entries.get(operationId)!.push(entry);
    this.checksumHistory.set(`${operationId}-${entry.timestamp}`, entry.checksum);

    await this.save();
  }

  async rollbackOperation(
    operationId: string,
    details: Record<string, any>
  ): Promise<void> {
    await this.logOperation(operationId, 'rollback', 'completed', details);
  }

  query(filters: AuditQuery = {}): AuditEntry[] {
    const results: AuditEntry[] = [];

    for (const [opId, entries] of this.entries) {
      for (const entry of entries) {
        let match = true;

        if (filters.operationId && opId !== filters.operationId) {
          match = false;
        }
        if (filters.operation && entry.operation !== filters.operation) {
          match = false;
        }
        if (filters.status && entry.status !== filters.status) {
          match = false;
        }
        if (filters.since && entry.timestamp < filters.since) {
          match = false;
        }
        if (filters.until && entry.timestamp > filters.until) {
          match = false;
        }

        if (match) {
          results.push(entry);
        }
      }
    }

    results.sort((a, b) => b.timestamp - a.timestamp);

    if (filters.limit) {
      return results.slice(0, filters.limit);
    }

    return results;
  }

  getOperationHistory(operationId: string): AuditEntry[] {
    return this.entries.get(operationId) || [];
  }

  async verifyIntegrity(): Promise<{ valid: boolean; tamperedEntries: string[] }> {
    const tamperedEntries: string[] = [];

    for (const [opId, entries] of this.entries) {
      for (const entry of entries) {
        const key = `${opId}-${entry.timestamp}`;
        const storedChecksum = this.checksumHistory.get(key);
        const currentChecksum = await this.generateChecksum(entry);

        if (storedChecksum && storedChecksum !== currentChecksum) {
          tamperedEntries.push(key);
        }
      }
    }

    return {
      valid: tamperedEntries.length === 0,
      tamperedEntries,
    };
  }

  private async generateChecksum(entry: AuditEntry): Promise<string> {
    const { checksum, ...data } = entry;
    const content = JSON.stringify(data);
    
    // Simple hash - in production use crypto.subtle.digest
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return hash.toString(16);
  }

  private async save(): Promise<void> {
    try {
      const data = {
        entries: Array.from(this.entries.entries()),
        checksums: Array.from(this.checksumHistory.entries()),
      };

      const adapter = this.vault.adapter;
      const dir = this.auditFile.substring(0, this.auditFile.lastIndexOf('/'));
      
      if (!(await adapter.exists(dir))) {
        await adapter.mkdir(dir);
      }

      await adapter.write(this.auditFile, JSON.stringify(data, null, 2));
    } catch (error) {
      console.error('Failed to save audit log:', error);
    }
  }

  private async load(): Promise<void> {
    try {
      const adapter = this.vault.adapter;
      
      if (await adapter.exists(this.auditFile)) {
        const content = await adapter.read(this.auditFile);
        const data = JSON.parse(content);

        this.entries = new Map(data.entries || []);
        this.checksumHistory = new Map(data.checksums || []);
      }
    } catch (error) {
      console.error('Failed to load audit log:', error);
      this.entries = new Map();
      this.checksumHistory = new Map();
    }
  }

  async clear(): Promise<void> {
    this.entries.clear();
    this.checksumHistory.clear();
    await this.save();
  }

  getStats(): {
    totalOperations: number;
    completedOperations: number;
    failedOperations: number;
    rolledBackOperations: number;
  } {
    let completed = 0;
    let failed = 0;
    let rolledBack = 0;

    for (const entries of this.entries.values()) {
      for (const entry of entries) {
        if (entry.status === 'completed') completed++;
        if (entry.status === 'failed') failed++;
        if (entry.status === 'rolled_back') rolledBack++;
      }
    }

    return {
      totalOperations: this.entries.size,
      completedOperations: completed,
      failedOperations: failed,
      rolledBackOperations: rolledBack,
    };
  }
}
