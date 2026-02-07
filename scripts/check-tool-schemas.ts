/**
 * Tool Schema Drift Checker
 * 
 * Validates that current schemas match committed snapshots.
 * Fails CI on any drift (breaking changes).
 */

import * as fs from 'fs';
import * as path from 'path';
import { canonicalizeJSON, extractToolSchema, loadManifest } from './snapshot-tool-schemas';

interface DriftCheckResult {
  valid: boolean;
  matching: string[];
  drifted: { tool: string; file: string; reason: string }[];
  missing: string[];
  orphaned: string[];
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
  
  // Check for breaking changes
  if (JSON.stringify(currentCanon.required || []) !== JSON.stringify(snapshotCanon.required || [])) {
    return 'required fields changed';
  }
  
  if (JSON.stringify(Object.keys(currentCanon.properties || {}).sort()) !== 
      JSON.stringify(Object.keys(snapshotCanon.properties || {}).sort())) {
    return 'properties changed';
  }
  
  if (currentCanon.type !== snapshotCanon.type) {
    return 'type changed';
  }
  
  return 'schema structure changed';
}

/**
 * Check for schema drift
 */
function checkDrift(): DriftCheckResult {
  console.log('🔍 Checking Tool Schema Drift...\n');
  
  const manifest = loadManifest();
  const snapshotDir = path.join(__dirname, '..', 'tests', 'snapshots', 'tool-schemas');
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
  try {
    const result = checkDrift();
    generateReport(result);
    
    if (result.valid) {
      console.log('\n✅ Schema contract check PASSED');
      console.log('   All schemas match committed snapshots');
      process.exit(0);
    } else {
      console.log('\n❌ Schema contract check FAILED');
      console.log('\nTo update snapshots:');
      console.log('  npm run contracts:refresh');
      console.log('\nReview changes before committing.');
      process.exit(1);
    }
  } catch (error) {
    console.error(`\n❌ Failed to check schema drift: ${error}`);
    process.exit(1);
  }
}

// Export for testing
export {
  checkDrift,
  detectDriftType,
  schemasEqual,
  getSnapshotFiles
};

// Run if called directly
if (require.main === module) {
  main();
}
