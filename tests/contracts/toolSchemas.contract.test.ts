/**
 * Tool Schema Contract Tests
 * 
 * Validates that:
 * - Every manifest tool has a committed schema snapshot
 * - No orphan snapshots exist
 * - Schemas are valid and consistent
 */

import { describe, it, expect, beforeAll } from 'vitest';
import * as fs from 'fs';
import * as path from 'path';
import { loadManifest, getSnapshotFilename } from '../../../scripts/snapshot-tool-schemas';
import { getSnapshotFiles, getToolFromFilename, schemasEqual } from '../../../scripts/check-tool-schemas';

describe('Tool Schema Contracts', () => {
  const snapshotDir = path.join(__dirname, '..', '..', 'snapshots', 'tool-schemas');
  let manifest: any;
  let snapshotFiles: string[];

  beforeAll(() => {
    manifest = loadManifest();
    snapshotFiles = fs.existsSync(snapshotDir) ? getSnapshotFiles(snapshotDir) : [];
  });

  it('should have a snapshot for every tool in manifest', () => {
    const manifestToolNames = manifest.tools.map((t: any) => t.function.name);
    const snapshotToolNames = snapshotFiles.map(getToolFromFilename);

    const missing = manifestToolNames.filter(
      (tool: string) => !snapshotToolNames.includes(tool)
    );

    if (missing.length > 0) {
      console.log('Missing snapshots for:', missing);
    }

    expect(missing).toHaveLength(0);
  });

  it('should not have orphan snapshots (snapshot without manifest tool)', () => {
    const manifestToolNames = manifest.tools.map((t: any) => t.function.name);
    const snapshotToolNames = snapshotFiles.map(getToolFromFilename);

    const orphaned = snapshotToolNames.filter(
      (tool: string) => !manifestToolNames.includes(tool)
    );

    if (orphaned.length > 0) {
      console.log('Orphaned snapshots:', orphaned);
    }

    expect(orphaned).toHaveLength(0);
  });

  it('should have valid JSON schema snapshots', () => {
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

  it('should have consistent schema properties', () => {
    for (const file of snapshotFiles) {
      const filepath = path.join(snapshotDir, file);
      const content = fs.readFileSync(filepath, 'utf-8');
      const snapshot = JSON.parse(content);

      // Type must be "function" for all tools
      expect(snapshot.parameters.type).toBe('object');

      // Properties must be an object
      expect(typeof snapshot.parameters.properties).toBe('object');

      // Required must be an array if present
      if (snapshot.parameters.required !== undefined) {
        expect(Array.isArray(snapshot.parameters.required)).toBe(true);
      }
    }
  });

  it('should have matching tool names in filenames and content', () => {
    for (const file of snapshotFiles) {
      const filepath = path.join(snapshotDir, file);
      const content = fs.readFileSync(filepath, 'utf-8');
      const snapshot = JSON.parse(content);

      const filenameTool = getToolFromFilename(file);
      const contentTool = snapshot.name;

      expect(contentTool).toBe(filenameTool);
    }
  });

  it('should detect schema drift if present', () => {
    // This test will fail if schemas have drifted
    // Run contracts:check to validate
    const drifted: string[] = [];

    for (const tool of manifest.tools) {
      const toolName = tool.function.name;
      const filename = getSnapshotFilename(toolName);
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
          required: tool.function.parameters.required || [],
          additionalProperties: tool.function.parameters.additionalProperties ?? false
        }
      };

      const snapshotContent = fs.readFileSync(filepath, 'utf-8');
      const snapshotSchema = JSON.parse(snapshotContent);

      if (!schemasEqual(currentSchema, snapshotSchema)) {
        drifted.push(toolName);
      }
    }

    if (drifted.length > 0) {
      console.log('Drifted schemas:', drifted);
      console.log('Run: npm run contracts:refresh');
    }

    expect(drifted).toHaveLength(0);
  });
});
