/**
 * Tool Parity Validation Script
 * 
 * Validates that tool manifest and runtime registry are in perfect sync.
 * Hard fail on any mismatch - blocks CI/CD pipeline.
 * Emits structured events for observability.
 */

import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { createAgentEvent, emitAgentEvent } from '../src/observability/emit-agent-event.ts';

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
  const manifestPath = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'openai_assistants_tools.json');
  
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
  const agentDir = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'src', 'services', 'agent');
  
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
  let status: 'pass' | 'fail' = 'pass';
  let errorMessage = '';
  let exitCode = 0;
  let result: ParityValidationResult | null = null;

  try {
    result = validateToolParity();

    console.log(`Manifest Tools (${result.manifestTools.length}):`);
    for (const t of result.manifestTools) {
      console.log(`  ✓ ${t}`);
    }

    console.log(`\nRuntime Tools (${result.runtimeTools.length}):`);
    for (const t of result.runtimeTools) {
      console.log(`  ✓ ${t}`);
    }

    status = result.valid ? 'pass' : 'fail';
    if (!result.valid) {
      exitCode = 1;
    }
  } catch (error) {
    status = 'fail';
    exitCode = 1;
    errorMessage = String(error);
    console.error(`\n❌ Tool parity check failed: ${errorMessage}`);
  } finally {
    const durationMs = Date.now() - startTime;
    emitAgentEvent(
      createAgentEvent({
        event_type: 'tool_parity_check',
        status,
        duration_ms: durationMs,
        payload: {
          tools_manifest: result?.manifestTools.length ?? 0,
          tools_runtime: result?.runtimeTools.length ?? 0,
          mismatch_count: result?.mismatches.length ?? 0,
          mismatches: result?.mismatches ?? (errorMessage ? [errorMessage] : [])
        }
      }),
      { strict: false }
    );
  }

  if (result && result.valid) {
    console.log('\n✅ Tool parity check PASSED');
    console.log('   Manifest and runtime registry are in sync');
  } else if (result) {
    console.log('\n❌ Tool parity check FAILED');
    console.log('\nMismatches found:');
    for (const m of result.mismatches) {
      console.log(`  • ${m}`);
    }
  }

  if (exitCode !== 0) {
    process.exit(exitCode);
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
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  main();
}
