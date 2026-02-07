/**
 * Tool handler for executing vault operations from AI commands.
 */

import { App } from 'obsidian';
import { VaultManager } from './VaultManager';

export interface ToolDefinition {
    type: 'function';
    function: {
        name: string;
        description: string;
        parameters: {
            type: 'object';
            properties: Record<string, any>;
            required?: string[];
        };
    };
}

export class ToolHandler {
    private vaultManager: VaultManager;
    private app: App;

    constructor(app: App) {
        this.app = app;
        this.vaultManager = new VaultManager(app);
    }

    getTools(): ToolDefinition[] {
        return [
            {
                type: 'function',
                function: {
                    name: 'create_note',
                    description: 'Create a new note in the vault',
                    parameters: {
                        type: 'object',
                        properties: {
                            path: { type: 'string', description: 'Path for the new note (e.g., "folder/note.md")' },
                            content: { type: 'string', description: 'Content of the note' },
                        },
                        required: ['path', 'content'],
                    },
                },
            },
            {
                type: 'function',
                function: {
                    name: 'read_note',
                    description: 'Read the content of an existing note',
                    parameters: {
                        type: 'object',
                        properties: {
                            path: { type: 'string', description: 'Path to the note' },
                        },
                        required: ['path'],
                    },
                },
            },
            {
                type: 'function',
                function: {
                    name: 'update_note',
                    description: 'Update the content of an existing note',
                    parameters: {
                        type: 'object',
                        properties: {
                            path: { type: 'string', description: 'Path to the note' },
                            content: { type: 'string', description: 'New content for the note' },
                        },
                        required: ['path', 'content'],
                    },
                },
            },
            {
                type: 'function',
                function: {
                    name: 'delete_note',
                    description: 'Delete a note from the vault',
                    parameters: {
                        type: 'object',
                        properties: {
                            path: { type: 'string', description: 'Path to the note to delete' },
                        },
                        required: ['path'],
                    },
                },
            },
            {
                type: 'function',
                function: {
                    name: 'search_notes',
                    description: 'Search for notes containing specific text',
                    parameters: {
                        type: 'object',
                        properties: {
                            query: { type: 'string', description: 'Search query' },
                        },
                        required: ['query'],
                    },
                },
            },
            {
                type: 'function',
                function: {
                    name: 'get_daily_note',
                    description: 'Get or create today\'s daily note',
                    parameters: {
                        type: 'object',
                        properties: {},
                    },
                },
            },
            {
                type: 'function',
                function: {
                    name: 'get_vault_stats',
                    description: 'Get statistics about the vault',
                    parameters: {
                        type: 'object',
                        properties: {},
                    },
                },
            },
        ];
    }

    async executeTool(name: string, args: Record<string, any>): Promise<string> {
        try {
            switch (name) {
                case 'create_note': {
                    const result = await this.vaultManager.createNote(args.path, args.content);
                    return JSON.stringify(result);
                }
                case 'read_note': {
                    const result = await this.vaultManager.readNote(args.path);
                    return JSON.stringify(result);
                }
                case 'update_note': {
                    const result = await this.vaultManager.updateNote(args.path, args.content);
                    return JSON.stringify(result);
                }
                case 'delete_note': {
                    const result = await this.vaultManager.deleteNote(args.path);
                    return JSON.stringify(result);
                }
                case 'search_notes': {
                    const result = await this.vaultManager.searchNotes(args.query);
                    return JSON.stringify(result);
                }
                case 'get_daily_note': {
                    const result = await this.vaultManager.getDailyNote();
                    return JSON.stringify(result);
                }
                case 'get_vault_stats': {
                    const result = await this.vaultManager.getVaultStats();
                    return JSON.stringify(result);
                }
                default:
                    return JSON.stringify({ success: false, message: `Unknown tool: ${name}` });
            }
        } catch (error) {
            return JSON.stringify({ success: false, message: `Tool error: ${error}` });
        }
    }
}
