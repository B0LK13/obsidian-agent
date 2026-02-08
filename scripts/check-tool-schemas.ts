/**
 * Tool Schema Drift Checker
 * 
 * Validates that current schemas match committed snapshots.
 * Fails CI on any drift (breaking changes).
 * Emits structured events for observability.
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { createAgentEvent, emitAgentEvent } from '../src/observability/emit-agent-event.ts';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

interface ToolDefinition {
  type: string;
  function: {
    name: string;
    description: string;
    parameters: {
      type: string;
      properties: Record<string, any>;
      required?: string[];
      additionalProperties?: boolean;
    };
  };
}

interface ToolManifest {
  tools: ToolDefinition[];
}

interface DriftCheckResult {
  valid: boolean;
  matching: string[];
  drifted: { tool: string; file: string; reason: string; diff?: string }[];
  missing: string[];
  orphaned: string[];
}

/**
 * Canonicalize JSON for stable comparison
 * Sorts keys alphabetically for deterministic output
 */
function canonicalizeJSON(obj: any): any {
  if (obj === null || typeof obj !== 'object') {
    return obj;
  }
  
  if (Array.isArray(obj)) {
    return obj.map(canonicalizeJSON);
  }
  
  const sorted: Record<string, any> = {};
  Object.keys(obj).sort().forEach(key => {
    sorted[key] = canonicalizeJSON(obj[key]);
  });
  
  return sorted;
}

/**
 * Extract schema from tool definition
 */
function extractToolSchema(tool: ToolDefinition): any {
  return {
    name: tool.function.name,
    description: tool.function.description,
    parameters: {
      type: tool.function.parameters.type,
      properties: tool.function.parameters.properties,
      required: tool.function.parameters.required?.sort() || [],
      additionalProperties: tool.function.parameters.additionalProperties ?? false
    }
  };
}

/**
 * Load tool manifest
 */
function loadManifest(): ToolManifest {
  const manifestPath = path.join(__dirname, '..', 'openai_assistants_tools.json');
  
  if (!fs.existsSync(manifestPath)) {
    throw new Error(`Tool manifest not found: ${manifestPath}`);
  }
  
  const content = fs.readFileSync(manifestPath, 'utf-8');
  return JSON.parse(content) as ToolManifest;
}

/**
 * Get all snapshot files in directory
 */
function getSnapshotFiles(snapshotDir: string): string[] {
  if (!fs.existsSync(snapshotDir)) {
    return [];
  }
  
  return fs.readdirSync(snapshotDir)
    .filter(f => f.endsWith('.schema.json'))
    .sort();
}

/**
 * Extract tool name from snapshot filename
 */
function getToolFromFilename(filename: string): string {
  return filename.replace('.schema.json', '');
}

/**
 * Load snapshot from file
 */
function loadSnapshot(filepath: string): any {
  const content = fs.readFileSync(filepath, 'utf-8');
  return JSON.parse(content);
}

/**
 * Compare two schemas for equality
 */
function schemasEqual(a: any, b: any): boolean {
  return JSON.stringify(canonicalizeJSON(a)) === JSON.stringify(canonicalizeJSON(b));
}

/**
 * Detect drift type
 */
function detectDriftType(current: any, snapshot: any): string {
  const currentCanon = canonicalizeJSON(current);
  const snapshotCanon = canonicalizeJSON(snapshot);
  
  const currentProps = currentCanon.parameters?.properties || {};
  const snapshotProps = snapshotCanon.parameters?.properties || {};
  
  const currentReq = currentCanon.parameters?.required || [];
  const snapshotReq = snapshotCanon.parameters?.required || [];

  // Check for breaking changes: Removed properties
  const removedProps = Object.keys(snapshotProps).filter(p => !currentProps[p]);
  if (removedProps.length > 0) {
    return `BREAKING: Properties removed: ${removedProps.join(', ')}`;
  }

  // Check for breaking changes: Optional became Required
  const newRequired = currentReq.filter((r: string) => !snapshotReq.includes(r));
  if (newRequired.length > 0) {
    return `BREAKING: Optional properties became required: ${newRequired.join(', ')}`;
  }

  // Check for breaking changes: Type changed
  for (const prop of Object.keys(snapshotProps)) {
    if (currentProps[prop] && currentProps[prop].type !== snapshotProps[prop].type) {
      return `BREAKING: Type changed for ${prop}: ${snapshotProps[prop].type} -> ${currentProps[prop].type}`;
    }
  }

  // Check for non-breaking changes: Added properties
  const addedProps = Object.keys(currentProps).filter(p => !snapshotProps[p]);
  if (addedProps.length > 0) {
    return `NON-BREAKING: Added properties: ${addedProps.join(', ')}`;
  }
  
  return 'Schema structure changed';
}

/**
 * Check for schema drift
 */
function checkDrift(): DriftCheckResult {
  console.log('🔍 Checking Tool Schema Drift...\n');
  
  const manifest = loadManifest();
  const snapshotDir = path.join(__dirname, '..', 'tests', 'contracts', 'snapshots', 'tools');
  const committedSnapshots = getSnapshotFiles(snapshotDir);
  
  const manifestToolNames = manifest.tools.map(t => t.function.name).sort();
  const snapshotToolNames = committedSnapshots.map(getToolFromFilename).sort();
  
  const result: DriftCheckResult = {
    valid: true,
    matching: [],
    drifted: [],
    missing: [],
    orphaned: []
  };
  
  // Check for missing snapshots (tools in manifest but no snapshot)
  for (const toolName of manifestToolNames) {
    if (!snapshotToolNames.includes(toolName)) {
      result.missing.push(toolName);
      result.valid = false;
    }
  }
  
  // Check for orphaned snapshots (snapshot exists but tool not in manifest)
  for (const snapshotFile of committedSnapshots) {
    const toolName = getToolFromFilename(snapshotFile);
    if (!manifestToolNames.includes(toolName)) {
      result.orphaned.push(toolName);
      result.valid = false;
    }
  }
  
  // Check for drift (compare current schema with snapshot)
  for (const tool of manifest.tools) {
    const toolName = tool.function.name;
    const filename = `${toolName}.schema.json`;
    const filepath = path.join(snapshotDir, filename);
    
    if (!fs.existsSync(filepath)) {
      continue; // Already recorded as missing
    }
    
    const currentSchema = extractToolSchema(tool);
    const snapshotSchema = loadSnapshot(filepath);
    
    if (schemasEqual(currentSchema, snapshotSchema)) {
      result.matching.push(toolName);
    } else {
      const driftReason = detectDriftType(currentSchema, snapshotSchema);
      result.drifted.push({
        tool: toolName,
        file: filename,
        reason: driftReason
      });
      result.valid = false;
    }
  }
  
  return result;
}

/**
 * Generate drift report
 */
function generateReport(result: DriftCheckResult): void {
  console.log(`\n📊 Schema Drift Report\n`);
  
  console.log(`Matching (${result.matching.length}):`);
  for (const tool of result.matching) {
    console.log(`  ✓ ${tool}`);
  }
  
  if (result.drifted.length > 0) {
    console.log(`\nDrifted (${result.drifted.length}):`);
    for (const { tool, file, reason } of result.drifted) {
      console.log(`  ✗ ${tool} (${file}): ${reason}`);
    }
  }
  
  if (result.missing.length > 0) {
    console.log(`\nMissing Snapshots (${result.missing.length}):`);
    for (const tool of result.missing) {
      console.log(`  ⚠ ${tool} (no snapshot file)`);
    }
  }
  
  if (result.orphaned.length > 0) {
    console.log(`\nOrphaned Snapshots (${result.orphaned.length}):`);
    for (const tool of result.orphaned) {
      console.log(`  🗑 ${tool} (tool not in manifest)`);
    }
  }
}

/**
 * Main execution
 */
function main(): void {
  const startTime = Date.now();
  let status: 'pass' | 'fail' = 'pass';
  let exitCode = 0;
  let errorMessage = '';
  let result: DriftCheckResult | null = null;

  try {
    result = checkDrift();
    generateReport(result);

    status = result.valid ? 'pass' : 'fail';
    if (!result.valid) {
      exitCode = 1;
    }
  } catch (error) {
    status = 'fail';
    exitCode = 1;
    errorMessage = String(error);
    console.error(`\n❌ Failed to check schema drift: ${errorMessage}`);
  } finally {
    const durationMs = Date.now() - startTime;
    const breakingChanges = result ? result.drifted.filter(d => d.reason.includes('BREAKING')).length : 0;
    const nonBreakingChanges = result ? result.drifted.filter(d => !d.reason.includes('BREAKING')).length : 0;

    emitAgentEvent(
      createAgentEvent({
        event_type: 'schema_contract_check',
        status,
        duration_ms: durationMs,
        payload: {
          tools_checked: result ? result.matching.length + result.drifted.length : 0,
          matching: result?.matching.length ?? 0,
          drifted: result?.drifted.length ?? 0,
          missing: result?.missing.length ?? 0,
          orphaned: result?.orphaned.length ?? 0,
          breaking_changes: breakingChanges,
          non_breaking_changes: nonBreakingChanges,
          failure_reason: errorMessage || undefined
        }
      }),
      { strict: false }
    );
  }

  if (result && result.valid) {
    console.log('\n✅ Schema contract check PASSED');
    console.log('   All schemas match committed snapshots');
  } else if (result) {
    console.log('\n❌ Schema contract check FAILED');
    console.log('\nTo update snapshots:');
    console.log('  npm run contracts:refresh');
    console.log('\nReview changes before committing.');
  }

  if (exitCode !== 0) {
    process.exit(exitCode);
  }
}

// Run if called directly
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main();
}

// Export for testing
export {
  checkDrift,
  detectDriftType,
  schemasEqual,
  getSnapshotFiles
};
