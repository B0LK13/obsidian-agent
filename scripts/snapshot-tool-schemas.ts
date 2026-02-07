/**
 * Tool Schema Snapshot Generator
 * 
 * Parses openai_assistants_tools.json and generates canonical
 * schema snapshots for each tool. Used to detect drift.
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
      additionalProperties?: boolean;
    };
  };
}

interface ToolManifest {
  tools: ToolDefinition[];
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
 * Generate snapshot filename from tool name
 */
function getSnapshotFilename(toolName: string): string {
  return `${toolName}.schema.json`;
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
 * Ensure snapshot directory exists
 */
function ensureSnapshotDir(): string {
  const snapshotDir = path.join(__dirname, '..', 'tests', 'snapshots', 'tool-schemas');
  
  if (!fs.existsSync(snapshotDir)) {
    fs.mkdirSync(snapshotDir, { recursive: true });
    console.log(`Created directory: ${snapshotDir}`);
  }
  
  return snapshotDir;
}

/**
 * Generate schema snapshots
 */
function generateSnapshots(): { tool: string; file: string; success: boolean }[] {
  console.log('📸 Generating Tool Schema Snapshots...\n');
  
  const manifest = loadManifest();
  const snapshotDir = ensureSnapshotDir();
  const results: { tool: string; file: string; success: boolean }[] = [];
  
  for (const tool of manifest.tools) {
    const toolName = tool.function.name;
    const schema = extractToolSchema(tool);
    const canonicalSchema = canonicalizeJSON(schema);
    
    const filename = getSnapshotFilename(toolName);
    const filepath = path.join(snapshotDir, filename);
    
    try {
      fs.writeFileSync(
        filepath,
        JSON.stringify(canonicalSchema, null, 2) + '\n',
        'utf-8'
      );
      
      results.push({ tool: toolName, file: filename, success: true });
      console.log(`  ✓ ${toolName} → ${filename}`);
    } catch (error) {
      results.push({ tool: toolName, file: filename, success: false });
      console.log(`  ✗ ${toolName} → ERROR: ${error}`);
    }
  }
  
  return results;
}

/**
 * Main execution
 */
function main(): void {
  try {
    const results = generateSnapshots();
    const successCount = results.filter(r => r.success).length;
    const totalCount = results.length;
    
    console.log(`\n✅ Generated ${successCount}/${totalCount} schema snapshots`);
    
    if (successCount === totalCount) {
      console.log('   All snapshots created successfully');
      process.exit(0);
    } else {
      console.log('   Some snapshots failed to generate');
      process.exit(1);
    }
  } catch (error) {
    console.error(`\n❌ Failed to generate snapshots: ${error}`);
    process.exit(1);
  }
}

// Export for testing
export {
  canonicalizeJSON,
  extractToolSchema,
  getSnapshotFilename,
  loadManifest,
  generateSnapshots
};

// Run if called directly
if (require.main === module) {
  main();
}
