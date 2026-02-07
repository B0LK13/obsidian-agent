import { VaultManager } from './VaultManager';
import { ChatCompletionTool } from 'openai/resources/chat/completions';

/**
 * Comprehensive Tool Definitions for the Autonomous Agent
 * These tools enable full vault management capabilities.
 */
export const AGENT_TOOLS: ChatCompletionTool[] = [
    // ============================================
    // NOTE CRUD OPERATIONS
    // ============================================
    {
        type: "function",
        function: {
            name: "create_note",
            description: "Create a new note in the Obsidian vault. Supports templates, frontmatter, and organized folder placement.",
            parameters: {
                type: "object",
                properties: {
                    title: { 
                        type: "string", 
                        description: "The title of the note (becomes filename)" 
                    },
                    content: { 
                        type: "string", 
                        description: "The markdown content of the note" 
                    },
                    path: { 
                        type: "string", 
                        description: "Folder path (e.g., 'pkm/01_projects/active'). Folders created automatically if needed." 
                    },
                    template: {
                        type: "string",
                        description: "Template name to use (e.g., 'daily-note', 'zettel', 'project', 'meeting-notes')"
                    },
                    tags: {
                        type: "array",
                        items: { type: "string" },
                        description: "Tags to add to frontmatter"
                    },
                    frontmatter: {
                        type: "object",
                        description: "Additional frontmatter properties as key-value pairs"
                    }
                },
                required: ["title", "content"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "read_note",
            description: "Read the content and metadata of a specific note. Returns content, frontmatter, and file path.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "The name or full path of the note to read" 
                    }
                },
                required: ["name"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "update_note",
            description: "Update an existing note. Supports append, prepend, replace, or insert after a specific heading.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "The name or path of the note to update" 
                    },
                    content: { 
                        type: "string", 
                        description: "The content to add/replace" 
                    },
                    mode: {
                        type: "string",
                        enum: ["append", "prepend", "replace", "insert-after-heading"],
                        description: "How to apply the update. Default: append"
                    },
                    heading: {
                        type: "string",
                        description: "For insert-after-heading mode, the heading to insert after"
                    },
                    preserve_frontmatter: {
                        type: "boolean",
                        description: "For replace mode, whether to preserve existing frontmatter"
                    }
                },
                required: ["name", "content"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "delete_note",
            description: "Delete a note (moves to system trash by default for safety).",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "The name or path of the note to delete" 
                    },
                    permanent: {
                        type: "boolean",
                        description: "If true, permanently delete instead of moving to trash. Default: false"
                    }
                },
                required: ["name"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "rename_note",
            description: "Rename a note. Updates all links to the note automatically.",
            parameters: {
                type: "object",
                properties: {
                    old_name: { 
                        type: "string", 
                        description: "Current name or path of the note" 
                    },
                    new_name: {
                        type: "string",
                        description: "New name for the note (without .md extension)"
                    }
                },
                required: ["old_name", "new_name"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "move_note",
            description: "Move a note to a different folder.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "Name or path of the note to move" 
                    },
                    target_folder: {
                        type: "string",
                        description: "Destination folder path (created if doesn't exist)"
                    }
                },
                required: ["name", "target_folder"]
            }
        }
    },

    // ============================================
    // SEARCH & DISCOVERY
    // ============================================
    {
        type: "function",
        function: {
            name: "search_vault",
            description: "Full-text search across all notes in the vault. Returns matching files with context.",
            parameters: {
                type: "object",
                properties: {
                    query: { 
                        type: "string", 
                        description: "Search query (searches content)" 
                    },
                    folder: {
                        type: "string",
                        description: "Limit search to specific folder path"
                    },
                    limit: {
                        type: "number",
                        description: "Maximum results to return. Default: 20"
                    },
                    include_content: {
                        type: "boolean",
                        description: "Include matching content excerpts. Default: true"
                    }
                },
                required: ["query"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "search_by_tag",
            description: "Find all notes with a specific tag.",
            parameters: {
                type: "object",
                properties: {
                    tag: { 
                        type: "string", 
                        description: "Tag to search for (with or without #)" 
                    },
                    limit: {
                        type: "number",
                        description: "Maximum results. Default: 50"
                    }
                },
                required: ["tag"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "search_by_property",
            description: "Find notes by frontmatter property.",
            parameters: {
                type: "object",
                properties: {
                    property: { 
                        type: "string", 
                        description: "Frontmatter property name (e.g., 'type', 'status', 'project')" 
                    },
                    value: {
                        type: "string",
                        description: "Optional value to match (partial match supported)"
                    }
                },
                required: ["property"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "get_recent_files",
            description: "Get recently modified files in the vault.",
            parameters: {
                type: "object",
                properties: {
                    limit: {
                        type: "number",
                        description: "Number of files to return. Default: 10"
                    }
                }
            }
        }
    },
    {
        type: "function",
        function: {
            name: "list_folder",
            description: "List all files and subfolders in a specific folder.",
            parameters: {
                type: "object",
                properties: {
                    path: { 
                        type: "string", 
                        description: "Folder path to list" 
                    },
                    recursive: {
                        type: "boolean",
                        description: "Include nested folders and files. Default: false"
                    }
                },
                required: ["path"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "get_vault_structure",
            description: "Get the folder structure of the vault as a tree. Useful for understanding organization.",
            parameters: {
                type: "object",
                properties: {
                    max_depth: {
                        type: "number",
                        description: "Maximum depth to traverse. Default: 3"
                    }
                }
            }
        }
    },

    // ============================================
    // METADATA & TAGGING
    // ============================================
    {
        type: "function",
        function: {
            name: "get_frontmatter",
            description: "Get the frontmatter/metadata of a note.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "Note name or path" 
                    }
                },
                required: ["name"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "update_frontmatter",
            description: "Update frontmatter properties of a note.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "Note name or path" 
                    },
                    properties: {
                        type: "object",
                        description: "Key-value pairs to set/update in frontmatter"
                    }
                },
                required: ["name", "properties"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "add_tags",
            description: "Add tags to a note's frontmatter.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "Note name or path" 
                    },
                    tags: {
                        type: "array",
                        items: { type: "string" },
                        description: "Tags to add (with or without #)"
                    }
                },
                required: ["name", "tags"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "remove_tags",
            description: "Remove tags from a note's frontmatter.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "Note name or path" 
                    },
                    tags: {
                        type: "array",
                        items: { type: "string" },
                        description: "Tags to remove"
                    }
                },
                required: ["name", "tags"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "get_all_tags",
            description: "Get all unique tags used in the vault with their counts.",
            parameters: {
                type: "object",
                properties: {}
            }
        }
    },

    // ============================================
    // LINKS & RELATIONSHIPS
    // ============================================
    {
        type: "function",
        function: {
            name: "get_outgoing_links",
            description: "Get all links FROM a specific note to other notes.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "Note name or path" 
                    }
                },
                required: ["name"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "get_backlinks",
            description: "Get all notes that link TO a specific note (incoming links).",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "Note name or path" 
                    }
                },
                required: ["name"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "create_link",
            description: "Create a wiki-link from one note to another.",
            parameters: {
                type: "object",
                properties: {
                    from_note: { 
                        type: "string", 
                        description: "Source note (where the link will be added)" 
                    },
                    to_note: {
                        type: "string",
                        description: "Target note (being linked to)"
                    },
                    display_text: {
                        type: "string",
                        description: "Optional display text for the link"
                    }
                },
                required: ["from_note", "to_note"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "find_orphan_notes",
            description: "Find notes with no incoming or outgoing links (isolated notes).",
            parameters: {
                type: "object",
                properties: {}
            }
        }
    },

    // ============================================
    // TEMPLATES & DAILY NOTES
    // ============================================
    {
        type: "function",
        function: {
            name: "list_templates",
            description: "List all available templates.",
            parameters: {
                type: "object",
                properties: {}
            }
        }
    },
    {
        type: "function",
        function: {
            name: "create_from_template",
            description: "Create a new note from a template with variable substitution.",
            parameters: {
                type: "object",
                properties: {
                    template: { 
                        type: "string", 
                        description: "Template name (e.g., 'daily-note', 'zettel', 'project')" 
                    },
                    title: {
                        type: "string",
                        description: "Title for the new note"
                    },
                    path: {
                        type: "string",
                        description: "Folder path for the new note"
                    },
                    variables: {
                        type: "object",
                        description: "Custom variables to substitute in the template"
                    }
                },
                required: ["template", "title"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "get_daily_note",
            description: "Get or create today's daily note (or for a specific date).",
            parameters: {
                type: "object",
                properties: {
                    date: {
                        type: "string",
                        description: "ISO date string (YYYY-MM-DD). Default: today"
                    }
                }
            }
        }
    },

    // ============================================
    // STATISTICS & ANALYTICS
    // ============================================
    {
        type: "function",
        function: {
            name: "get_vault_stats",
            description: "Get comprehensive statistics about the vault (note count, tags, links, folder distribution).",
            parameters: {
                type: "object",
                properties: {}
            }
        }
    },

    // ============================================
    // CONTEXT & ACTIVE FILE
    // ============================================
    {
        type: "function",
        function: {
            name: "get_active_file",
            description: "Get information about the currently open/active file in the editor.",
            parameters: {
                type: "object",
                properties: {}
            }
        }
    },
    {
        type: "function",
        function: {
            name: "open_file",
            description: "Open a specific file in the Obsidian editor.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "Note name or path to open" 
                    }
                },
                required: ["name"]
            }
        }
    },

    // ============================================
    // ADVANCED OPERATIONS
    // ============================================
    {
        type: "function",
        function: {
            name: "batch_operation",
            description: "Perform a batch operation on multiple notes. Useful for bulk tagging, moving, or updating.",
            parameters: {
                type: "object",
                properties: {
                    operation: {
                        type: "string",
                        enum: ["add_tags", "remove_tags", "move", "update_frontmatter"],
                        description: "The operation to perform"
                    },
                    notes: {
                        type: "array",
                        items: { type: "string" },
                        description: "List of note names or paths"
                    },
                    params: {
                        type: "object",
                        description: "Parameters for the operation (e.g., tags to add, target folder, frontmatter properties)"
                    }
                },
                required: ["operation", "notes", "params"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "create_zettel",
            description: "Create a new Zettelkasten-style atomic note with automatic UID and proper placement.",
            parameters: {
                type: "object",
                properties: {
                    title: { 
                        type: "string", 
                        description: "Brief descriptive title (will be slugified)" 
                    },
                    content: {
                        type: "string",
                        description: "The atomic insight/idea content"
                    },
                    tags: {
                        type: "array",
                        items: { type: "string" },
                        description: "Relevant tags"
                    },
                    links: {
                        type: "array",
                        items: { type: "string" },
                        description: "Related notes to link to"
                    },
                    source: {
                        type: "string",
                        description: "Source of the insight (book, article, etc.)"
                    }
                },
                required: ["title", "content"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "create_moc",
            description: "Create a Map of Content (MOC) that organizes notes around a topic.",
            parameters: {
                type: "object",
                properties: {
                    topic: { 
                        type: "string", 
                        description: "The topic for this MOC" 
                    },
                    notes: {
                        type: "array",
                        items: { type: "string" },
                        description: "Notes to include in the MOC"
                    },
                    description: {
                        type: "string",
                        description: "Description of the topic/theme"
                    }
                },
                required: ["topic"]
            }
        }
    },
    {
        type: "function", 
        function: {
            name: "summarize_note",
            description: "Read a note and prepare context for summarization. Returns the note content for LLM processing.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "Note name or path to summarize" 
                    }
                },
                required: ["name"]
            }
        }
    },
    {
        type: "function",
        function: {
            name: "analyze_connections",
            description: "Analyze a note's connections and suggest related notes based on tags, links, and content similarity.",
            parameters: {
                type: "object",
                properties: {
                    name: { 
                        type: "string", 
                        description: "Note to analyze" 
                    }
                },
                required: ["name"]
            }
        }
    }
];

/**
 * ToolHandler - Executes agent tool calls against the VaultManager
 */
export class ToolHandler {
    private vaultManager: VaultManager;

    constructor(vaultManager: VaultManager) {
        this.vaultManager = vaultManager;
    }

    /**
     * Execute a tool call and return the result as a string.
     */
    async executeTool(toolCall: any): Promise<string> {
        const functionName = toolCall.function.name;
        let args: any = {};
        
        try {
            args = JSON.parse(toolCall.function.arguments);
        } catch (e) {
            return `Error: Invalid JSON arguments for ${functionName}`;
        }

        console.log(`[Agent Tool] Executing: ${functionName}`, args);

        try {
            switch (functionName) {
                // NOTE CRUD
                case 'create_note':
                    return await this.handleCreateNote(args);
                case 'read_note':
                    return await this.handleReadNote(args);
                case 'update_note':
                    return await this.handleUpdateNote(args);
                case 'delete_note':
                    return await this.handleDeleteNote(args);
                case 'rename_note':
                    return await this.handleRenameNote(args);
                case 'move_note':
                    return await this.handleMoveNote(args);

                // SEARCH & DISCOVERY
                case 'search_vault':
                    return await this.handleSearchVault(args);
                case 'search_by_tag':
                    return this.handleSearchByTag(args);
                case 'search_by_property':
                    return this.handleSearchByProperty(args);
                case 'get_recent_files':
                    return this.handleGetRecentFiles(args);
                case 'list_folder':
                    return this.handleListFolder(args);
                case 'get_vault_structure':
                    return this.handleGetVaultStructure(args);

                // METADATA & TAGGING
                case 'get_frontmatter':
                    return this.handleGetFrontmatter(args);
                case 'update_frontmatter':
                    return await this.handleUpdateFrontmatter(args);
                case 'add_tags':
                    return await this.handleAddTags(args);
                case 'remove_tags':
                    return await this.handleRemoveTags(args);
                case 'get_all_tags':
                    return this.handleGetAllTags();

                // LINKS & RELATIONSHIPS
                case 'get_outgoing_links':
                    return this.handleGetOutgoingLinks(args);
                case 'get_backlinks':
                    return this.handleGetBacklinks(args);
                case 'create_link':
                    return await this.handleCreateLink(args);
                case 'find_orphan_notes':
                    return this.handleFindOrphanNotes();

                // TEMPLATES & DAILY NOTES
                case 'list_templates':
                    return this.handleListTemplates();
                case 'create_from_template':
                    return await this.handleCreateFromTemplate(args);
                case 'get_daily_note':
                    return await this.handleGetDailyNote(args);

                // STATISTICS
                case 'get_vault_stats':
                    return this.handleGetVaultStats();

                // CONTEXT
                case 'get_active_file':
                    return this.handleGetActiveFile();
                case 'open_file':
                    return await this.handleOpenFile(args);

                // ADVANCED
                case 'batch_operation':
                    return await this.handleBatchOperation(args);
                case 'create_zettel':
                    return await this.handleCreateZettel(args);
                case 'create_moc':
                    return await this.handleCreateMOC(args);
                case 'summarize_note':
                    return await this.handleSummarizeNote(args);
                case 'analyze_connections':
                    return await this.handleAnalyzeConnections(args);

                default:
                    return `Error: Unknown tool "${functionName}"`;
            }
        } catch (error) {
            console.error(`[Agent Tool] Error in ${functionName}:`, error);
            return `Error executing ${functionName}: ${error.message}`;
        }
    }

    // ============================================
    // HANDLER IMPLEMENTATIONS
    // ============================================

    private async handleCreateNote(args: any): Promise<string> {
        const frontmatter: Record<string, any> = args.frontmatter || {};
        if (args.tags) {
            frontmatter.tags = args.tags;
        }
        
        const result = await this.vaultManager.createNote(
            args.title,
            args.content,
            args.path || '',
            Object.keys(frontmatter).length > 0 ? frontmatter : undefined,
            args.template
        );
        
        if (result.success) {
            return `Successfully created note: ${result.path}`;
        }
        return `Error: ${result.error}`;
    }

    private async handleReadNote(args: any): Promise<string> {
        const result = await this.vaultManager.readNote(args.name);
        if (result.success) {
            let response = `**File:** ${result.path}\n\n`;
            if (result.frontmatter) {
                response += `**Frontmatter:**\n\`\`\`yaml\n${JSON.stringify(result.frontmatter, null, 2)}\n\`\`\`\n\n`;
            }
            response += `**Content:**\n${result.content}`;
            return response;
        }
        return `Error: ${result.error}`;
    }

    private async handleUpdateNote(args: any): Promise<string> {
        const result = await this.vaultManager.updateNote(
            args.name,
            args.content,
            args.mode || 'append',
            {
                heading: args.heading,
                preserveFrontmatter: args.preserve_frontmatter
            }
        );
        
        if (result.success) {
            return `Successfully updated note: ${result.path}`;
        }
        return `Error: ${result.error}`;
    }

    private async handleDeleteNote(args: any): Promise<string> {
        const result = await this.vaultManager.deleteNote(args.name, args.permanent || false);
        if (result.success) {
            return `Successfully deleted note: ${args.name}`;
        }
        return `Error: ${result.error}`;
    }

    private async handleRenameNote(args: any): Promise<string> {
        const result = await this.vaultManager.renameNote(args.old_name, args.new_name);
        if (result.success) {
            return `Successfully renamed to: ${result.newPath}`;
        }
        return `Error: ${result.error}`;
    }

    private async handleMoveNote(args: any): Promise<string> {
        const result = await this.vaultManager.moveNote(args.name, args.target_folder);
        if (result.success) {
            return `Successfully moved to: ${result.newPath}`;
        }
        return `Error: ${result.error}`;
    }

    private async handleSearchVault(args: any): Promise<string> {
        const results = await this.vaultManager.searchContent(args.query, {
            folder: args.folder,
            limit: args.limit || 20,
            includeContent: args.include_content !== false
        });

        if (results.length === 0) {
            return `No results found for "${args.query}"`;
        }

        let response = `Found ${results.length} results for "${args.query}":\n\n`;
        for (const r of results) {
            response += `- **${r.path}** (score: ${r.score.toFixed(2)})\n`;
            if (r.matches.length > 0) {
                for (const m of r.matches) {
                    response += `  > ${m.substring(0, 100)}...\n`;
                }
            }
        }
        return response;
    }

    private handleSearchByTag(args: any): string {
        const results = this.vaultManager.searchByTag(args.tag, args.limit || 50);
        if (results.length === 0) {
            return `No notes found with tag "${args.tag}"`;
        }

        let response = `Found ${results.length} notes with tag "${args.tag}":\n\n`;
        for (const r of results) {
            response += `- ${r.path} (tags: ${r.tags.join(', ')})\n`;
        }
        return response;
    }

    private handleSearchByProperty(args: any): string {
        const results = this.vaultManager.searchByProperty(args.property, args.value);
        if (results.length === 0) {
            return `No notes found with property "${args.property}"${args.value ? ` = "${args.value}"` : ''}`;
        }

        let response = `Found ${results.length} notes with property "${args.property}":\n\n`;
        for (const r of results) {
            response += `- ${r.path}: ${JSON.stringify(r.value)}\n`;
        }
        return response;
    }

    private handleGetRecentFiles(args: any): string {
        const files = this.vaultManager.getRecentFiles(args.limit || 10);
        if (files.length === 0) {
            return 'No recent files found';
        }

        let response = `Recent files:\n\n`;
        for (const f of files) {
            const date = new Date(f.modified).toLocaleString();
            response += `- ${f.path} (${date})\n`;
        }
        return response;
    }

    private handleListFolder(args: any): string {
        const items = this.vaultManager.listFolder(args.path, args.recursive || false);
        if (items.length === 0) {
            return `Folder "${args.path}" is empty or doesn't exist`;
        }

        let response = `Contents of "${args.path}":\n\n`;
        for (const item of items) {
            const icon = item.isFolder ? '📁' : '📄';
            response += `${icon} ${item.path}\n`;
        }
        return response;
    }

    private handleGetVaultStructure(args: any): string {
        const structure = this.vaultManager.getVaultStructure(args.max_depth || 3);
        return `Vault Structure:\n\`\`\`json\n${JSON.stringify(structure, null, 2)}\n\`\`\``;
    }

    private handleGetFrontmatter(args: any): string {
        const fm = this.vaultManager.getFrontmatter(args.name);
        if (!fm) {
            return `No frontmatter found for "${args.name}" (or note doesn't exist)`;
        }
        return `Frontmatter for "${args.name}":\n\`\`\`yaml\n${JSON.stringify(fm, null, 2)}\n\`\`\``;
    }

    private async handleUpdateFrontmatter(args: any): Promise<string> {
        const result = await this.vaultManager.updateFrontmatter(args.name, args.properties);
        if (result.success) {
            return `Successfully updated frontmatter for "${args.name}"`;
        }
        return `Error: ${result.error}`;
    }

    private async handleAddTags(args: any): Promise<string> {
        const result = await this.vaultManager.addTags(args.name, args.tags);
        if (result.success) {
            return `Successfully added tags [${args.tags.join(', ')}] to "${args.name}"`;
        }
        return `Error: ${result.error}`;
    }

    private async handleRemoveTags(args: any): Promise<string> {
        const result = await this.vaultManager.removeTags(args.name, args.tags);
        if (result.success) {
            return `Successfully removed tags [${args.tags.join(', ')}] from "${args.name}"`;
        }
        return `Error: ${result.error}`;
    }

    private handleGetAllTags(): string {
        const tags = this.vaultManager.getAllVaultTags();
        if (tags.length === 0) {
            return 'No tags found in the vault';
        }

        let response = `All tags in vault (${tags.length} unique):\n\n`;
        for (const t of tags.slice(0, 50)) {
            response += `- #${t.tag} (${t.count} notes)\n`;
        }
        if (tags.length > 50) {
            response += `\n... and ${tags.length - 50} more`;
        }
        return response;
    }

    private handleGetOutgoingLinks(args: any): string {
        const links = this.vaultManager.getOutgoingLinks(args.name);
        if (links.length === 0) {
            return `No outgoing links from "${args.name}"`;
        }

        let response = `Outgoing links from "${args.name}":\n\n`;
        for (const l of links) {
            response += `- [[${l.link}]]${l.displayText ? ` (${l.displayText})` : ''}\n`;
        }
        return response;
    }

    private handleGetBacklinks(args: any): string {
        const backlinks = this.vaultManager.getBacklinks(args.name);
        if (backlinks.length === 0) {
            return `No backlinks to "${args.name}"`;
        }

        let response = `Backlinks to "${args.name}" (${backlinks.length}):\n\n`;
        for (const b of backlinks) {
            response += `- ${b.path}\n`;
        }
        return response;
    }

    private async handleCreateLink(args: any): Promise<string> {
        const result = await this.vaultManager.createLink(
            args.from_note, 
            args.to_note, 
            args.display_text
        );
        if (result.success) {
            return `Successfully created link from "${args.from_note}" to "${args.to_note}"`;
        }
        return `Error: ${result.error}`;
    }

    private handleFindOrphanNotes(): string {
        const orphans = this.vaultManager.getOrphanNotes();
        if (orphans.length === 0) {
            return 'No orphan notes found (all notes have connections)';
        }

        let response = `Found ${orphans.length} orphan notes:\n\n`;
        for (const o of orphans.slice(0, 30)) {
            response += `- ${o}\n`;
        }
        if (orphans.length > 30) {
            response += `\n... and ${orphans.length - 30} more`;
        }
        return response;
    }

    private handleListTemplates(): string {
        const templates = this.vaultManager.listTemplates();
        if (templates.length === 0) {
            return 'No templates found';
        }
        return `Available templates:\n${templates.map(t => `- ${t}`).join('\n')}`;
    }

    private async handleCreateFromTemplate(args: any): Promise<string> {
        const result = await this.vaultManager.createFromTemplate(
            args.template,
            args.title,
            args.path || '',
            args.variables
        );
        if (result.success) {
            return `Successfully created note from template "${args.template}": ${result.path}`;
        }
        return `Error: ${result.error}`;
    }

    private async handleGetDailyNote(args: any): Promise<string> {
        const date = args.date ? new Date(args.date) : undefined;
        const result = await this.vaultManager.getDailyNote(date);
        
        if (result.success) {
            const status = result.created ? 'Created' : 'Found';
            return `${status} daily note: ${result.path}`;
        }
        return `Error: ${result.error}`;
    }

    private handleGetVaultStats(): string {
        const stats = this.vaultManager.getVaultStats();
        return `**Vault Statistics:**
- Total Notes: ${stats.totalNotes}
- Total Folders: ${stats.totalFolders}
- Unique Tags: ${stats.totalTags}
- Total Links: ${stats.totalLinks}
- Avg Note Size: ${stats.avgNoteLength} bytes

**Notes per Top Folders:**
${Object.entries(stats.notesPerFolder)
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([folder, count]) => `- ${folder}: ${count}`)
    .join('\n')}`;
    }

    private handleGetActiveFile(): string {
        const file = this.vaultManager.getActiveFile();
        if (!file) {
            return 'No file is currently active/open';
        }
        return `Active file: ${file.path}`;
    }

    private async handleOpenFile(args: any): Promise<string> {
        const result = await this.vaultManager.openFile(args.name);
        if (result.success) {
            return `Opened file: ${args.name}`;
        }
        return `Error: ${result.error}`;
    }

    private async handleBatchOperation(args: any): Promise<string> {
        const results: string[] = [];
        const { operation, notes, params } = args;

        for (const note of notes) {
            let result: { success: boolean; error?: string };
            
            switch (operation) {
                case 'add_tags':
                    result = await this.vaultManager.addTags(note, params.tags);
                    break;
                case 'remove_tags':
                    result = await this.vaultManager.removeTags(note, params.tags);
                    break;
                case 'move':
                    result = await this.vaultManager.moveNote(note, params.target_folder);
                    break;
                case 'update_frontmatter':
                    result = await this.vaultManager.updateFrontmatter(note, params.properties);
                    break;
                default:
                    result = { success: false, error: `Unknown operation: ${operation}` };
            }

            results.push(`${note}: ${result.success ? 'OK' : result.error}`);
        }

        return `Batch operation "${operation}" completed:\n${results.map(r => `- ${r}`).join('\n')}`;
    }

    private async handleCreateZettel(args: any): Promise<string> {
        const now = new Date();
        const uid = now.toISOString().replace(/[-:T]/g, '').split('.')[0];
        const slug = args.title.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/-+/g, '-').replace(/^-|-$/g, '');
        const fileName = `${uid}-${slug}`;
        
        let content = args.content;
        
        // Add related links
        if (args.links && args.links.length > 0) {
            content += '\n\n## Related\n';
            for (const link of args.links) {
                content += `- [[${link}]]\n`;
            }
        }

        const frontmatter: Record<string, any> = {
            type: 'zettel',
            created: now.toISOString(),
            tags: args.tags || []
        };
        
        if (args.source) {
            frontmatter.source = args.source;
        }

        const result = await this.vaultManager.createNote(
            fileName,
            content,
            'pkm/99_zettelkasten/notes',
            frontmatter
        );

        if (result.success) {
            return `Created Zettel: ${result.path}`;
        }
        return `Error: ${result.error}`;
    }

    private async handleCreateMOC(args: any): Promise<string> {
        const slug = args.topic.toLowerCase().replace(/[^a-z0-9]+/g, '-');
        const fileName = `${slug}-moc`;
        
        let content = args.description ? `${args.description}\n\n` : '';
        content += '## Notes\n\n';
        
        if (args.notes && args.notes.length > 0) {
            for (const note of args.notes) {
                content += `- [[${note}]]\n`;
            }
        } else {
            content += '*Add related notes here*\n';
        }

        const frontmatter = {
            type: 'moc',
            topic: args.topic,
            created: new Date().toISOString()
        };

        const result = await this.vaultManager.createNote(
            fileName,
            content,
            'pkm/99_zettelkasten/_maps',
            frontmatter
        );

        if (result.success) {
            return `Created MOC: ${result.path}`;
        }
        return `Error: ${result.error}`;
    }

    private async handleSummarizeNote(args: any): Promise<string> {
        const result = await this.vaultManager.readNote(args.name);
        if (!result.success) {
            return `Error: ${result.error}`;
        }
        
        return `**Note to summarize:** ${result.path}\n\n**Content:**\n${result.content}\n\n*Please provide a concise summary of this note.*`;
    }

    private async handleAnalyzeConnections(args: any): Promise<string> {
        const file = this.vaultManager.findFile(args.name);
        if (!file) {
            return `Error: Note "${args.name}" not found`;
        }

        const outgoing = this.vaultManager.getOutgoingLinks(args.name);
        const backlinks = this.vaultManager.getBacklinks(args.name);
        const frontmatter = this.vaultManager.getFrontmatter(args.name);
        
        let response = `**Connection Analysis for "${args.name}":**\n\n`;
        response += `**Outgoing Links (${outgoing.length}):**\n`;
        response += outgoing.length > 0 
            ? outgoing.map(l => `- [[${l.link}]]`).join('\n')
            : '*No outgoing links*';
        
        response += `\n\n**Backlinks (${backlinks.length}):**\n`;
        response += backlinks.length > 0
            ? backlinks.map(b => `- ${b.path}`).join('\n')
            : '*No backlinks*';

        if (frontmatter?.tags) {
            const tags = Array.isArray(frontmatter.tags) ? frontmatter.tags : [frontmatter.tags];
            response += `\n\n**Tags:** ${tags.map(t => `#${t}`).join(', ')}`;
            
            // Find notes with same tags
            const relatedByTag: string[] = [];
            for (const tag of tags) {
                const tagResults = this.vaultManager.searchByTag(tag, 10);
                for (const r of tagResults) {
                    if (r.path !== file.path && !relatedByTag.includes(r.path)) {
                        relatedByTag.push(r.path);
                    }
                }
            }
            
            if (relatedByTag.length > 0) {
                response += `\n\n**Related by Tags (${relatedByTag.length}):**\n`;
                response += relatedByTag.slice(0, 10).map(p => `- ${p}`).join('\n');
            }
        }

        return response;
    }
}
