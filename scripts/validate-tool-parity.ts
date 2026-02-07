/**
 * Tool Parity Validation Script
 * 
 * Validates that tool manifest and runtime registry are in perfect sync.
 * Hard fail on any mismatch - blocks CI/CD pipeline.
 */

import * as fs from 'fs';
import * as path from 'path';

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
}

/**
 * Load tool manifest from openai_assistants_tools.json
 */
function loadToolManifest(): ToolManifest {
  const manifestPath = path.join(__dirname, '..', 'openai_assistants_tools.json');
  
  if (!fs.existsSync(manifestPath)) {
    throw new Error(`Tool manifest not found: ${manifestPath}`);
  }
  
  const content = fs.readFileSync(manifestPath, 'utf-8');
  return JSON.parse(content) as ToolManifest;
}

/**
 * Load runtime tool registry
 * This simulates the runtime registry - in production, this would import from src/runtime/toolRegistry.ts
 */
function loadRuntimeRegistry(): string[] {
  // For now, we'll scan the tools directory
  const toolsDir = path.join(__dirname, '..', 'src', 'services', 'agent', 'tools');
  
  if (!fs.existsSync(toolsDir)) {
    console.warn(`Tools directory not found: ${toolsDir}`);
    return [];
  }
  
  // Extract tool names from tool files
  // This is a simplified check - production would use the actual registry
  const toolFiles = fs.readdirSync(toolsDir)
    .filter(f => f.endsWith('.ts') && !f.includes('.test.'));
  
  // Map file names to tool names (e.g., SearchVaultTool.ts -> search_vault)
  const toolNames = toolFiles.map(file => {
    const className = file.replace('.ts', '');
    return classNameToSnakeCase(className).replace(/_tool$/, '');
  });
  
  return toolNames.sort();
}

/**
 * Convert PascalCase class name to snake_case
 */
function classNameToSnakeCase(className: string): string {
  return className
    .replace(/([A-Z])/g, '_$1')
    .toLowerCase()
    .replace(/^_/, '');
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
  let manifest: ToolManifest;
  try {
    manifest = loadToolManifest();
  } catch (error) {
    return {
      valid: false,
      mismatches: [`Failed to load manifest: ${error}`],
      manifestTools: [],
      runtimeTools: []
    };
  }
  
  // Extract manifest tool names
  const manifestTools = manifest.tools
    .map(extractManifestToolName)
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
  
  return {
    valid: mismatches.length === 0,
    mismatches,
    manifestTools,
    runtimeTools
  };
}

/**
 * Main execution
 */
function main(): void {
  console.log('🔍 Validating Tool Manifest↔Registry Parity...\n');
  
  const result = validateToolParity();
  
  console.log(`Manifest Tools (${result.manifestTools.length}):`);
  for (const t of result.manifestTools) {
    console.log(`  ✓ ${t}`);
  }
  
  console.log(`\nRuntime Tools (${result.runtimeTools.length}):`);
  for (const t of result.runtimeTools) {
    console.log(`  ✓ ${t}`);
  }
  
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
if (require.main === module) {
  main();
}
