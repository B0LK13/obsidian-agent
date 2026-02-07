import { Vault, TFile } from 'obsidian';
import { AuditLogger, RollbackMetadata } from './auditLogger';
import { VectorStore } from './vectorStore';

export interface TransactionContext {
  operationId: string;
  operation: string;
  checkpoints: Checkpoint[];
  committed: boolean;
}

export interface Checkpoint {
  type: 'vector' | 'file' | 'metadata';
  id: string;
  previousState: any;
  timestamp: number;
}

export interface RollbackPlaybook {
  steps: RollbackStep[];
  validate: () => Promise<boolean>;
}

export interface RollbackStep {
  description: string;
  execute: () => Promise<void>;
  verify: () => Promise<boolean>;
}

/**
 * TransactionManager - Ensures atomic operations with rollback safety
 * 
 * Provides:
 * - Transaction boundaries with commit/rollback
 * - Checkpoint creation for state restoration
 * - Automated rollback playbooks
 * - Integrity verification
 */
export class TransactionManager {
  private activeTransactions: Map<string, TransactionContext> = new Map();
  private vault: Vault;
  private auditLogger: AuditLogger;
  private vectorStore: VectorStore;

  constructor(vault: Vault, auditLogger: AuditLogger, vectorStore: VectorStore) {
    this.vault = vault;
    this.auditLogger = auditLogger;
    this.vectorStore = vectorStore;
  }

  /**
   * Begin a new transaction
   */
  async begin(operationId: string, operation: string): Promise<TransactionContext> {
    if (this.activeTransactions.has(operationId)) {
      throw new Error(`Transaction ${operationId} already active`);
    }

    const ctx: TransactionContext = {
      operationId,
      operation,
      checkpoints: [],
      committed: false,
    };

    this.activeTransactions.set(operationId, ctx);

    await this.auditLogger.startOperation(operationId, operation as any, {
      transactionStarted: true,
    });

    return ctx;
  }

  /**
   * Create a checkpoint before mutation
   */
  async checkpoint(
    operationId: string,
    type: Checkpoint['type'],
    id: string,
    previousState: any
  ): Promise<void> {
    const ctx = this.activeTransactions.get(operationId);
    if (!ctx) {
      throw new Error(`No active transaction: ${operationId}`);
    }

    ctx.checkpoints.push({
      type,
      id,
      previousState,
      timestamp: Date.now(),
    });
  }

  /**
   * Commit transaction - makes changes permanent and logs audit trail
   */
  async commit(operationId: string): Promise<void> {
    const ctx = this.activeTransactions.get(operationId);
    if (!ctx) {
      throw new Error(`No active transaction: ${operationId}`);
    }

    if (ctx.committed) {
      throw new Error(`Transaction ${operationId} already committed`);
    }

    // Build rollback metadata from checkpoints
    const rollbackMetadata: RollbackMetadata = {
      affectedFiles: ctx.checkpoints
        .filter((c) => c.type === 'file')
        .map((c) => c.id),
      affectedIndices: ctx.checkpoints
        .filter((c) => c.type === 'vector')
        .map((c) => c.id),
      previousState: ctx.checkpoints.map((c) => ({
        type: c.type,
        id: c.id,
        state: c.previousState,
      })),
      recoverySteps: this.generateRecoverySteps(ctx.checkpoints),
    };

    // Audit MUST succeed before commit is marked complete
    await this.auditLogger.completeOperation(
      operationId,
      ctx.operation as any,
      {
        checkpointCount: ctx.checkpoints.length,
        transactionCommitted: true,
      },
      rollbackMetadata
    );

    ctx.committed = true;
    this.activeTransactions.delete(operationId);
  }

  /**
   * Rollback transaction - restore all checkpointed state
   */
  async rollback(operationId: string): Promise<void> {
    const ctx = this.activeTransactions.get(operationId);
    if (!ctx) {
      // Check if already committed
      const history = this.auditLogger.getOperationHistory(operationId);
      if (history.length > 0) {
        return this.rollbackCommitted(operationId);
      }
      throw new Error(`No transaction found: ${operationId}`);
    }

    // Rollback checkpoints in reverse order
    for (let i = ctx.checkpoints.length - 1; i >= 0; i--) {
      const checkpoint = ctx.checkpoints[i];
      await this.restoreCheckpoint(checkpoint);
    }

    await this.auditLogger.rollbackOperation(operationId, {
      checkpointsRestored: ctx.checkpoints.length,
    });

    this.activeTransactions.delete(operationId);
  }

  /**
   * Rollback a committed operation using audit trail
   */
  private async rollbackCommitted(operationId: string): Promise<void> {
    const history = this.auditLogger.getOperationHistory(operationId);
    if (history.length === 0) {
      throw new Error(`No operation found: ${operationId}`);
    }

    const lastEntry = history[history.length - 1];
    if (!lastEntry.rollbackMetadata?.previousState) {
      throw new Error(`No rollback metadata for operation ${operationId}`);
    }

    // Restore previous state
    const checkpoints = lastEntry.rollbackMetadata.previousState as Array<{
      type: string;
      id: string;
      state: any;
    }>;

    for (let i = checkpoints.length - 1; i >= 0; i--) {
      const cp = checkpoints[i];
      await this.restoreCheckpoint({
        type: cp.type as Checkpoint['type'],
        id: cp.id,
        previousState: cp.state,
        timestamp: Date.now(),
      });
    }

    await this.auditLogger.rollbackOperation(operationId, {
      committedRollback: true,
      checkpointsRestored: checkpoints.length,
    });
  }

  /**
   * Restore a single checkpoint
   */
  private async restoreCheckpoint(checkpoint: Checkpoint): Promise<void> {
    switch (checkpoint.type) {
      case 'vector':
        if (checkpoint.previousState === null) {
          // Was a new entry, remove it
          await this.vectorStore.remove(checkpoint.id);
        } else {
          // Restore previous vector
          await this.vectorStore.add(checkpoint.previousState);
        }
        await this.vectorStore.save();
        break;

      case 'file':
        if (checkpoint.previousState === null) {
          // File was created, delete it
          const file = this.vault.getAbstractFileByPath(checkpoint.id);
          if (file instanceof TFile) {
            await this.vault.delete(file);
          }
        } else if (typeof checkpoint.previousState === 'string') {
          // File was modified, restore content
          const file = this.vault.getAbstractFileByPath(checkpoint.id);
          if (file instanceof TFile) {
            await this.vault.modify(file, checkpoint.previousState);
          }
        }
        break;

      case 'metadata':
        // Metadata rollback - implementation depends on metadata storage
        console.log(`Metadata rollback not yet implemented for ${checkpoint.id}`);
        break;
    }
  }

  /**
   * Generate human-readable recovery steps
   */
  private generateRecoverySteps(checkpoints: Checkpoint[]): string[] {
    return checkpoints.map((cp, i) => {
      switch (cp.type) {
        case 'vector':
          return cp.previousState === null
            ? `Remove vector index for ${cp.id}`
            : `Restore vector for ${cp.id}`;
        case 'file':
          return cp.previousState === null
            ? `Delete file ${cp.id}`
            : `Restore content of ${cp.id}`;
        case 'metadata':
          return `Restore metadata for ${cp.id}`;
        default:
          return `Restore checkpoint ${i + 1}`;
      }
    });
  }

  /**
   * Create a rollback playbook for manual execution
   */
  createPlaybook(operationId: string): RollbackPlaybook {
    const history = this.auditLogger.getOperationHistory(operationId);
    if (history.length === 0) {
      throw new Error(`No operation found: ${operationId}`);
    }

    const lastEntry = history[history.length - 1];
    const rollbackMeta = lastEntry.rollbackMetadata;

    if (!rollbackMeta?.recoverySteps) {
      throw new Error(`No recovery steps available for ${operationId}`);
    }

    const steps: RollbackStep[] = rollbackMeta.recoverySteps.map((desc) => ({
      description: desc,
      execute: async () => {
        await this.rollbackCommitted(operationId);
      },
      verify: async () => {
        // Simple verification: check audit trail
        const newHistory = this.auditLogger.getOperationHistory(operationId);
        return newHistory.some((e) => e.operation === 'rollback');
      },
    }));

    return {
      steps,
      validate: async () => {
        // Verify rollback metadata integrity
        const integrity = await this.auditLogger.verifyIntegrity();
        return integrity.valid;
      },
    };
  }

  /**
   * Get active transaction count
   */
  getActiveTransactionCount(): number {
    return this.activeTransactions.size;
  }

  /**
   * List active transactions
   */
  listActiveTransactions(): TransactionContext[] {
    return Array.from(this.activeTransactions.values());
  }

  /**
   * Force cleanup of stale transactions (for error recovery)
   */
  async cleanup(): Promise<number> {
    let cleaned = 0;

    for (const [opId, ctx] of this.activeTransactions) {
      if (!ctx.committed) {
        await this.rollback(opId);
        cleaned++;
      }
    }

    return cleaned;
  }
}

/**
 * Decorator for transaction-safe operations
 */
export function transactional(
  _txManager: TransactionManager,
  _operation: string
) {
  return function (
    _target: any,
    _propertyKey: string,
    descriptor: PropertyDescriptor
  ) {
    const originalMethod = descriptor.value;

    descriptor.value = async function (...args: any[]) {
      const operationId = _txManager['auditLogger'].createOperationId();
      await _txManager.begin(operationId, _operation);

      try {
        const result = await originalMethod.apply(this, [operationId, ...args]);
        await _txManager.commit(operationId);
        return result;
      } catch (error) {
        await _txManager.rollback(operationId);
        throw error;
      }
    };

    return descriptor;
  };
}
