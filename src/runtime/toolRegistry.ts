/**
 * Tool Registry
 * 
 * Central registry for all available tools in the runtime.
 * Provides APIs for tool registration, lookup, and listing.
 */

export interface Tool {
  name: string;
  description: string;
  parameters: ToolParameterSchema;
  execute: (args: any) => Promise<ToolResult>;
}

export interface ToolParameterSchema {
  type: string;
  properties: Record<string, any>;
  required?: string[];
}

export interface ToolResult {
  success: boolean;
  data?: any;
  error?: string;
  fallback?: string;
}

/**
 * Tool Registry Class
 */
class ToolRegistry {
  private tools: Map<string, Tool> = new Map();

  /**
   * Register a tool
   */
  register(tool: Tool): void {
    if (this.tools.has(tool.name)) {
      throw new Error(`Tool already registered: ${tool.name}`);
    }
    this.tools.set(tool.name, tool);
  }

  /**
   * Get a tool by name
   */
  get(name: string): Tool | undefined {
    return this.tools.get(name);
  }

  /**
   * Check if tool exists
   */
  has(name: string): boolean {
    return this.tools.has(name);
  }

  /**
   * List all registered tools (sorted)
   */
  listRegisteredTools(): string[] {
    return Array.from(this.tools.keys()).sort();
  }

  /**
   * Get count of registered tools
   */
  count(): number {
    return this.tools.size;
  }

  /**
   * Clear all tools (mainly for testing)
   */
  clear(): void {
    this.tools.clear();
  }

  /**
   * Get all tools (for parity checking)
   */
  getAllTools(): Tool[] {
    return Array.from(this.tools.values());
  }
}

// Singleton instance
const toolRegistry = new ToolRegistry();

export { toolRegistry, ToolRegistry };
