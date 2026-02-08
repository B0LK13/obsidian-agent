/**
 * Tool Parity Validation Script - Simplified Version
 * 
 * Validates that tool manifest and runtime registry are in perfect sync.
 * Hard fail on any mismatch - blocks CI/CD pipeline.
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
    };
  };
}

interface ToolManifest {
  tools: ToolDefinition[];
}

interface ParityValidationResult {
  valid: boolean;
  mismatches: string[];
  manifestTools: string[];
  runtimeTools: string[];
  matching: string[];
  drifted: string[];
  missing: string[];
  orphaned: string[];
}

/**
 * Load tool manifest from openai_assistants_tools.json
 */
function loadToolManifest(): ToolManifest {
  const manifestPath = path.join(__dirname, '..', 'openai_assistants_tools.json');
  
  if (!fs.existsSync(manifestPath)) {
    // Return empty if not exists yet, so we can generate it
    return { tools: [] };
  }
  
  const content = fs.readFileSync(manifestPath, 'utf-8');
  return JSON.parse(content) as ToolManifest;
}

/**
 * Load runtime tool registry
 * This simulates the runtime registry by scanning the agent services directory
 */
function loadRuntimeRegistry(): string[] {
  // Point to actual tool location
  const agentDir = path.join(__dirname, '..', 'src', 'services', 'agent');
  
  if (!fs.existsSync(agentDir)) {
    console.warn(`Agent directory not found: ${agentDir}`);
    return [];
  }
  
  // Extract tool names from files ending in 'Tool.ts'
  const toolFiles = fs.readdirSync(agentDir)
    .filter(f => f.endsWith('Tool.ts') && !f.includes('.test.'));
  
  const toolNames = toolFiles.map(file => {
    // e.g., createNoteTool.ts -> create_note
    return file
      .replace('Tool.ts', '')
      .replace(/([A-Z])/g, '_$1')
      .toLowerCase()
      .replace(/^_/, '');
  });
  
  return toolNames.sort();
}

/**
 * Extract tool name from manifest function name
 */
function extractManifestToolName(tool: ToolDefinition): string {
  return tool.function.name;
}

/**
 * Check for snake_case naming
 */
function isSnakeCase(name: string): boolean {
  return /^[a-z][a-z0-9_]*$/.test(name) && !/[A-Z]/.test(name);
}

/**
 * Find duplicate tool names
 */
function findDuplicates(names: string[]): string[] {
  const seen = new Set<string>();
  const duplicates: string[] = [];
  
  for (const name of names) {
    if (seen.has(name)) {
      duplicates.push(name);
    }
    seen.add(name);
  }
  
  return duplicates;
}

/**
 * Emit structured event for observability
 */
function emitToolParityEvent(
  result: 'pass' | 'fail',
  manifestTools: number,
  runtimeTools: number,
  mismatches: string[],
  durationMs: number
): void {
  emitAgentEvent(
    createAgentEvent({
      event_type: 'tool_parity_check',
      status: result,
      duration_ms: durationMs,
      payload: {
        tools_manifest: manifestTools,
        tools_runtime: runtimeTools,
        mismatch_count: mismatches.length,
        mismatches
      }
    }),
    { strict: false }
  );
}

/**
 * Validate tool parity between manifest and runtime
 */
function validateToolParity(): ParityValidationResult {
  const mismatches: string[] = [];
  
  // Load manifest
  const manifest = loadToolManifest();
  
  // Extract manifest tool names
  const manifestTools = manifest.tools
    .map((t: ToolDefinition) => extractManifestToolName(t))
    .sort();
  
  // Load runtime registry
  const runtimeTools = loadRuntimeRegistry();
  
  // Check for duplicates in manifest
  const manifestDuplicates = findDuplicates(manifestTools);
  if (manifestDuplicates.length > 0) {
    mismatches.push(`Duplicate tool names in manifest: ${manifestDuplicates.join(', ')}`);
  }
  
  // Check for duplicates in runtime
  const runtimeDuplicates = findDuplicates(runtimeTools);
  if (runtimeDuplicates.length > 0) {
    mismatches.push(`Duplicate tool names in runtime: ${runtimeDuplicates.join(', ')}`);
  }
  
  // Check snake_case naming
  const nonSnakeCaseManifest = manifestTools.filter(t => !isSnakeCase(t));
  if (nonSnakeCaseManifest.length > 0) {
    mismatches.push(`Non-snake_case names in manifest: ${nonSnakeCaseManifest.join(', ')}`);
  }
  
  const nonSnakeCaseRuntime = runtimeTools.filter(t => !isSnakeCase(t));
  if (nonSnakeCaseRuntime.length > 0) {
    mismatches.push(`Non-snake_case names in runtime: ${nonSnakeCaseRuntime.join(', ')}`);
  }
  
  // Bidirectional check: manifest → runtime
  const manifestOnly = manifestTools.filter(t => !runtimeTools.includes(t));
  if (manifestOnly.length > 0) {
    mismatches.push(`Tools in manifest but not in runtime: ${manifestOnly.join(', ')}`);
  }
  
  // Bidirectional check: runtime → manifest
  const runtimeOnly = runtimeTools.filter(t => !manifestTools.includes(t));
  if (runtimeOnly.length > 0) {
    mismatches.push(`Tools in runtime but not in manifest: ${runtimeOnly.join(', ')}`);
  }
  
  // Calculate matching, drifted, missing, orphaned
  const matching: string[] = manifestTools.filter(t => runtimeTools.includes(t));
  const drifted: string[] = []; // No schema drift in parity check
  const missing: string[] = manifestOnly;
  const orphaned: string[] = runtimeOnly;
  
  return {
    valid: mismatches.length === 0,
    mismatches,
    manifestTools,
    runtimeTools,
    matching,
    drifted,
    missing,
    orphaned
  };
}

/**
 * Main execution
 */
function main(): void {
  console.log('🔍 Validating Tool Manifest↔Registry Parity...\n');
  
  const startTime = Date.now();
  const result = validateToolParity();
  const durationMs = Date.now() - startTime;
  
  console.log(`Manifest Tools (${result.manifestTools.length}):`);
  for (const t of result.manifestTools) {
    console.log(`  ✓ ${t}`);
  }
  
  console.log(`\nRuntime Tools (${result.runtimeTools.length}):`);
  for (const t of result.runtimeTools) {
    console.log(`  ✓ ${t}`);
  }
  
  // Emit structured event
  emitToolParityEvent(
    result.valid ? 'pass' : 'fail',
    result.manifestTools.length,
    result.runtimeTools.length,
    result.mismatches,
    durationMs
  );
  
  if (result.valid) {
    console.log('\n✅ Tool parity check PASSED');
    console.log('   Manifest and runtime registry are in sync');
    process.exit(0);
  } else {
    console.log('\n❌ Tool parity check FAILED');
    console.log('\nMismatches found:');
    for (const m of result.mismatches) {
      console.log(`  • ${m}`);
    }
    process.exit(1);
  }
}

// Export for testing
export {
  validateToolParity,
  loadToolManifest,
  loadRuntimeRegistry,
  isSnakeCase,
  findDuplicates
};

// Run if called directly
if (process.argv[1] === __filename) {
  main();
}
