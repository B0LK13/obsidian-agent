import { describe, it, expect } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Helper functions (copied from scripts to avoid import issues)
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

function schemasEqual(a: any, b: any): boolean {
  return JSON.stringify(canonicalizeJSON(a)) === JSON.stringify(canonicalizeJSON(b));
}

function getToolFromFilename(filename: string): string {
  return filename.replace('.schema.json', '');
}

function getSnapshotFiles(snapshotDir: string): string[] {
  if (!fs.existsSync(snapshotDir)) {
    return [];
  }
  
  return fs.readdirSync(snapshotDir)
    .filter(f => f.endsWith('.schema.json'))
    .sort();
}

function loadManifest(): any {
  const manifestPath = path.join(__dirname, '../../', 'openai_assistants_tools.json');
  
  if (!fs.existsSync(manifestPath)) {
    throw new Error(`Tool manifest not found: ${manifestPath}`);
  }
  
  const content = fs.readFileSync(manifestPath, 'utf-8');
  return JSON.parse(content);
}

describe('Tool Schema Contracts', () => {
  const snapshotDir = path.join(__dirname, 'snapshots', 'tools');
  const manifest = loadManifest();
  const snapshotFiles = getSnapshotFiles(snapshotDir);

  it('should have a snapshot for every tool in manifest', () => {
    const manifestToolNames = manifest.tools.map((t: any) => t.function.name);
    const snapshotToolNames = snapshotFiles.map(getToolFromFilename);

    const missing = manifestToolNames.filter(
      (tool: string) => !snapshotToolNames.includes(tool)
    );

    expect(missing).toHaveLength(0);
  });

  it('should detect schema drift', () => {
    const drifted: string[] = [];

    for (const tool of manifest.tools) {
      const toolName = tool.function.name;
      const filename = `${toolName}.schema.json`;
      const filepath = path.join(snapshotDir, filename);

      if (!fs.existsSync(filepath)) {
        continue; // Missing snapshot handled in other test
      }

      const currentSchema = {
        name: tool.function.name,
        description: tool.function.description,
        parameters: {
          type: tool.function.parameters.type,
          properties: tool.function.parameters.properties,
          required: tool.function.parameters.required?.sort() || [],
          additionalProperties: tool.function.parameters.additionalProperties ?? false
        }
      };

      const snapshotContent = fs.readFileSync(filepath, 'utf-8');
      const snapshotSchema = JSON.parse(snapshotContent);

      if (!schemasEqual(currentSchema, snapshotSchema)) {
        drifted.push(toolName);
      }
    }

    expect(drifted).toHaveLength(0);
  });

  it('should validate snapshot structure', () => {
    for (const file of snapshotFiles) {
      const filepath = path.join(snapshotDir, file);
      const content = fs.readFileSync(filepath, 'utf-8');
      
      let schema: any;
      expect(() => {
        schema = JSON.parse(content);
      }).not.toThrow();

      // Validate schema structure
      expect(schema).toHaveProperty('name');
      expect(schema).toHaveProperty('description');
      expect(schema).toHaveProperty('parameters');
      expect(schema.parameters).toHaveProperty('type');
      expect(schema.parameters).toHaveProperty('properties');
    }
  });
});
