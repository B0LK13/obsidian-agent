/**
 * Tool Manifest Generator
 * 
 * Generates openai_assistants_tools.json from canonical tool definitions.
 * This is the single source of truth for tool schemas.
 */

import * as fs from 'fs';
import * as path from 'path';

const TOOLS = [
  {
    type: 'function',
    function: {
      name: 'create_note',
      description: 'Create a new note in the vault. Returns success message or error if note exists.',
      parameters: {
        type: 'object',
        properties: {
          title: {
            type: 'string',
            description: 'The title for the new note (optional).'
          },
          path: {
            type: 'string',
            description: 'The path for the new note (e.g., "Research/My Topic"). Extension .md is added automatically if missing.'
          },
          content: {
            type: 'string',
            description: 'The initial content of the note in Markdown format.'
          }
        },
        required: ['path', 'content'] // NON-BREAKING: Added optional 'title'
      }
    }
  },
  {
    type: 'function',
    function: {
      name: 'update_note',
      description: 'Update or append content to an existing note in the vault.',
      parameters: {
        type: 'object',
        properties: {
          path: {
            type: 'string',
            description: 'The path of the note to update.'
          },
          content: {
            type: 'string',
            description: 'The new content to append or overwrite.'
          },
          mode: {
            type: 'string',
            enum: ['append', 'overwrite'],
            description: 'Whether to append to existing content or overwrite it completely. Defaults to append.',
            default: 'append'
          }
        },
        required: ['path', 'content']
      }
    }
  }
];

import { fileURLToPath } from 'url';

function generateManifest() {
  const manifestPath = path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'openai_assistants_tools.json');
  const content = JSON.stringify({ tools: TOOLS }, null, 2);
  
  fs.writeFileSync(manifestPath, content, 'utf-8');
  console.log(`✅ Generated manifest with ${TOOLS.length} tools at: ${manifestPath}`);
}

// ES module equivalent of require.main === module
if (process.argv[1] === fileURLToPath(import.meta.url)) {
  generateManifest();
}

export { TOOLS };
