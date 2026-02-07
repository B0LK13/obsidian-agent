#!/usr/bin/env python3
"""
Agent Tools and Function Calling System
Provides the AI agent with capabilities to:
- Search and retrieve information
- Create and modify notes
- Execute calculations
- Generate summaries
- Create knowledge graphs
- And more
"""

import json
import logging
from typing import Dict, List, Optional, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('agent_tools')


class ToolCategory(Enum):
    RETRIEVAL = "retrieval"
    CREATION = "creation"
    ANALYSIS = "analysis"
    CALCULATION = "calculation"
    EXTERNAL = "external"


@dataclass
class ToolParameter:
    """Definition of a tool parameter"""
    name: str
    description: str
    type: str  # string, number, boolean, array, object
    required: bool = True
    enum: Optional[List[str]] = None
    default: Any = None


@dataclass
class ToolDefinition:
    """Definition of an available tool"""
    name: str
    description: str
    category: ToolCategory
    parameters: List[ToolParameter]
    function: Callable = field(repr=False)
    examples: List[str] = field(default_factory=list)


@dataclass
class ToolCall:
    """A request to call a tool"""
    tool_name: str
    parameters: Dict[str, Any]
    call_id: str = ""


@dataclass
class ToolResult:
    """Result of a tool execution"""
    success: bool
    data: Any
    error: Optional[str] = None
    execution_time_ms: float = 0.0


class ToolRegistry:
    """Registry of all available tools"""
    
    def __init__(self):
        self.tools: Dict[str, ToolDefinition] = {}
        self.categories: Dict[ToolCategory, List[str]] = {
            cat: [] for cat in ToolCategory
        }
    
    def register(self, tool: ToolDefinition):
        """Register a new tool"""
        self.tools[tool.name] = tool
        self.categories[tool.category].append(tool.name)
        logger.info(f"Registered tool: {tool.name}")
    
    def get(self, name: str) -> Optional[ToolDefinition]:
        """Get a tool by name"""
        return self.tools.get(name)
    
    def list_tools(self, category: Optional[ToolCategory] = None) -> List[ToolDefinition]:
        """List all tools or tools in a category"""
        if category:
            return [self.tools[name] for name in self.categories[category]]
        return list(self.tools.values())
    
    def get_openai_schema(self) -> List[Dict]:
        """Get tools in OpenAI function calling format"""
        schemas = []
        for tool in self.tools.values():
            schema = {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
            
            for param in tool.parameters:
                prop = {
                    "type": param.type,
                    "description": param.description
                }
                if param.enum:
                    prop["enum"] = param.enum
                if param.default is not None:
                    prop["default"] = param.default
                
                schema["function"]["parameters"]["properties"][param.name] = prop
                
                if param.required:
                    schema["function"]["parameters"]["required"].append(param.name)
            
            schemas.append(schema)
        
        return schemas


class ToolExecutor:
    """Executes tool calls and manages results"""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
        self.execution_history: List[Dict] = []
    
    def execute(self, tool_call: ToolCall) -> ToolResult:
        """Execute a tool call"""
        import time
        start_time = time.time()
        
        tool = self.registry.get(tool_call.tool_name)
        if not tool:
            return ToolResult(
                success=False,
                data=None,
                error=f"Tool '{tool_call.tool_name}' not found"
            )
        
        # Validate parameters
        validation_error = self._validate_params(tool, tool_call.parameters)
        if validation_error:
            return ToolResult(
                success=False,
                data=None,
                error=validation_error
            )
        
        try:
            # Execute tool
            result_data = tool.function(**tool_call.parameters)
            
            execution_time = (time.time() - start_time) * 1000
            
            result = ToolResult(
                success=True,
                data=result_data,
                execution_time_ms=execution_time
            )
            
            # Record in history
            self.execution_history.append({
                'timestamp': datetime.now().isoformat(),
                'tool': tool_call.tool_name,
                'parameters': tool_call.parameters,
                'success': True,
                'execution_time_ms': execution_time
            })
            
            return result
            
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            
            error_msg = str(e)
            logger.error(f"Tool execution failed: {tool_call.tool_name} - {error_msg}")
            
            self.execution_history.append({
                'timestamp': datetime.now().isoformat(),
                'tool': tool_call.tool_name,
                'parameters': tool_call.parameters,
                'success': False,
                'error': error_msg
            })
            
            return ToolResult(
                success=False,
                data=None,
                error=error_msg,
                execution_time_ms=execution_time
            )
    
    def _validate_params(self, tool: ToolDefinition, 
                         params: Dict[str, Any]) -> Optional[str]:
        """Validate tool parameters"""
        # Check required parameters
        for param in tool.parameters:
            if param.required and param.name not in params:
                return f"Missing required parameter: {param.name}"
        
        # Check for extra parameters
        valid_names = {p.name for p in tool.parameters}
        for key in params:
            if key not in valid_names:
                return f"Unknown parameter: {key}"
        
        return None
    
    def parse_tool_calls(self, llm_response: str) -> List[ToolCall]:
        """
        Parse tool calls from LLM response
        Supports multiple formats:
        - JSON: {"tool": "name", "parameters": {...}}
        - XML: <tool name="name"><param>...</param></tool>
        - Natural: "I'll use the search_notes tool to find..."
        """
        tool_calls = []
        
        # Try JSON format
        try:
            data = json.loads(llm_response)
            if isinstance(data, dict) and 'tool' in data:
                tool_calls.append(ToolCall(
                    tool_name=data['tool'],
                    parameters=data.get('parameters', {}),
                    call_id=data.get('call_id', '')
                ))
            elif isinstance(data, list):
                for item in data:
                    if 'tool' in item:
                        tool_calls.append(ToolCall(
                            tool_name=item['tool'],
                            parameters=item.get('parameters', {}),
                            call_id=item.get('call_id', '')
                        ))
        except json.JSONDecodeError:
            pass
        
        # Try to extract from natural language
        if not tool_calls:
            tool_calls = self._extract_from_text(llm_response)
        
        return tool_calls
    
    def _extract_from_text(self, text: str) -> List[ToolCall]:
        """Extract tool calls from natural language text"""
        tool_calls = []
        
        # Pattern: "use [tool_name] with [param] = [value]"
        pattern = r'(?:use|call|invoke)\s+(?:the\s+)?(\w+)\s+(?:tool\s+)?(?:with\s+)?(.+?)(?:\.|$|and)'
        matches = re.finditer(pattern, text, re.IGNORECASE)
        
        for match in matches:
            tool_name = match.group(1)
            param_str = match.group(2)
            
            # Parse parameters
            params = {}
            param_pattern = r'(\w+)\s*=\s*["\']?([^"\';,]+)["\']?'
            for pm in re.finditer(param_pattern, param_str):
                params[pm.group(1)] = pm.group(2).strip()
            
            tool_calls.append(ToolCall(
                tool_name=tool_name,
                parameters=params
            ))
        
        return tool_calls


# ============== Tool Implementations ==============

def create_obsidian_tools(vault_interface) -> ToolRegistry:
    """Create tool registry with Obsidian-specific tools"""
    registry = ToolRegistry()
    
    # === RETRIEVAL TOOLS ===
    
    registry.register(ToolDefinition(
        name="search_notes",
        description="Search for notes in the vault using semantic search",
        category=ToolCategory.RETRIEVAL,
        parameters=[
            ToolParameter("query", "The search query", "string", required=True),
            ToolParameter("limit", "Maximum number of results", "number", required=False, default=5),
            ToolParameter("include_content", "Whether to include note content", "boolean", required=False, default=True)
        ],
        function=vault_interface.search_notes if vault_interface else lambda **kwargs: [],
        examples=[
            "search_notes(query="machine learning")",
            "search_notes(query="project ideas", limit=10)"
        ]
    ))
    
    registry.register(ToolDefinition(
        name="get_note",
        description="Get the content of a specific note by path",
        category=ToolCategory.RETRIEVAL,
        parameters=[
            ToolParameter("path", "Path to the note", "string", required=True)
        ],
        function=vault_interface.get_note if vault_interface else lambda **kwargs: None
    ))
    
    registry.register(ToolDefinition(
        name="get_vault_stats",
        description="Get statistics about the vault (total notes, folders, words, tags)",
        category=ToolCategory.RETRIEVAL,
        parameters=[],
        function=vault_interface.get_vault_stats if vault_interface else lambda: {}
    ))
    
    registry.register(ToolDefinition(
        name="get_related_notes",
        description="Find notes related to a given note",
        category=ToolCategory.RETRIEVAL,
        parameters=[
            ToolParameter("note_path", "Path to the reference note", "string", required=True),
            ToolParameter("limit", "Maximum number of results", "number", required=False, default=5)
        ],
        function=vault_interface.get_related_notes if vault_interface else lambda **kwargs: []
    ))
    
    # === CREATION TOOLS ===
    
    registry.register(ToolDefinition(
        name="create_note",
        description="Create a new note with given content",
        category=ToolCategory.CREATION,
        parameters=[
            ToolParameter("title", "Title of the note", "string", required=True),
            ToolParameter("content", "Content of the note", "string", required=True),
            ToolParameter("folder", "Folder to create the note in", "string", required=False, default=""),
            ToolParameter("tags", "Tags to add to the note", "array", required=False, default=[])
        ],
        function=vault_interface.create_note if vault_interface else lambda **kwargs: None
    ))
    
    registry.register(ToolDefinition(
        name="append_to_note",
        description="Append content to an existing note",
        category=ToolCategory.CREATION,
        parameters=[
            ToolParameter("path", "Path to the note", "string", required=True),
            ToolParameter("content", "Content to append", "string", required=True),
            ToolParameter("heading", "Optional heading to add before content", "string", required=False, default="")
        ],
        function=vault_interface.append_to_note if vault_interface else lambda **kwargs: None
    ))
    
    registry.register(ToolDefinition(
        name="create_daily_note",
        description="Create or open today's daily note",
        category=ToolCategory.CREATION,
        parameters=[
            ToolParameter("content", "Optional initial content", "string", required=False, default="")
        ],
        function=vault_interface.create_daily_note if vault_interface else lambda **kwargs: None
    ))
    
    # === ANALYSIS TOOLS ===
    
    registry.register(ToolDefinition(
        name="summarize_note",
        description="Generate a summary of a note",
        category=ToolCategory.ANALYSIS,
        parameters=[
            ToolParameter("path", "Path to the note", "string", required=True),
            ToolParameter("max_length", "Maximum summary length", "number", required=False, default=200)
        ],
        function=vault_interface.summarize_note if vault_interface else lambda **kwargs: ""
    ))
    
    registry.register(ToolDefinition(
        name="extract_tasks",
        description="Extract tasks/todos from notes",
        category=ToolCategory.ANALYSIS,
        parameters=[
            ToolParameter("path", "Path to the note (optional, searches all if not provided)", "string", required=False, default=""),
            ToolParameter("include_completed", "Whether to include completed tasks", "boolean", required=False, default=False)
        ],
        function=vault_interface.extract_tasks if vault_interface else lambda **kwargs: []
    ))
    
    registry.register(ToolDefinition(
        name="find_connections",
        description="Find connections between notes using graph analysis",
        category=ToolCategory.ANALYSIS,
        parameters=[
            ToolParameter("note_paths", "List of note paths to analyze", "array", required=True),
            ToolParameter("depth", "How many hops to follow", "number", required=False, default=2)
        ],
        function=vault_interface.find_connections if vault_interface else lambda **kwargs: {}
    ))
    
    # === CALCULATION TOOLS ===
    
    registry.register(ToolDefinition(
        name="calculate",
        description="Perform mathematical calculations",
        category=ToolCategory.CALCULATION,
        parameters=[
            ToolParameter("expression", "Mathematical expression to evaluate", "string", required=True)
        ],
        function=lambda expression: eval(expression, {"__builtins__": {}}, {"math": __import__('math')}),
        examples=["calculate(expression="2 + 2 * 5")", "calculate(expression="math.sqrt(16)")"]
    ))
    
    registry.register(ToolDefinition(
        name="count_words",
        description="Count words in text or notes",
        category=ToolCategory.CALCULATION,
        parameters=[
            ToolParameter("path", "Path to note (optional)", "string", required=False, default=""),
            ToolParameter("text", "Text to count (optional)", "string", required=False, default="")
        ],
        function=vault_interface.count_words if vault_interface else lambda **kwargs: 0
    ))
    
    # === EXTERNAL TOOLS ===
    
    registry.register(ToolDefinition(
        name="web_search",
        description="Search the web for information (requires internet)",
        category=ToolCategory.EXTERNAL,
        parameters=[
            ToolParameter("query", "Search query", "string", required=True),
            ToolParameter("num_results", "Number of results", "number", required=False, default=3)
        ],
        function=lambda query, num_results=3: {"status": "not_implemented", "message": "Web search requires configuration"}
    ))
    
    return registry


# ============== Smart Agent with Tool Use ==============

class ToolUsingAgent:
    """
    Agent that can use tools to accomplish tasks
    Combines LLM reasoning with tool execution
    """
    
    def __init__(self, llm_client, tool_registry: ToolRegistry):
        self.llm = llm_client
        self.tools = tool_registry
        self.executor = ToolExecutor(tool_registry)
        self.max_iterations = 5
    
    def run(self, user_query: str, context: str = "") -> Dict:
        """
        Run the agent on a user query
        Returns final response and execution trace
        """
        iteration = 0
        conversation = [
            {"role": "system", "content": self._get_system_prompt()},
            {"role": "user", "content": user_query}
        ]
        
        tool_results = []
        
        while iteration < self.max_iterations:
            # Get LLM response
            response = self.llm.chat(conversation, tools=self.tools.get_openai_schema())
            
            # Check for tool calls
            tool_calls = self.executor.parse_tool_calls(response)
            
            if not tool_calls:
                # No more tools needed, return final answer
                return {
                    'response': response,
                    'tool_calls': tool_results,
                    'iterations': iteration + 1
                }
            
            # Execute tool calls
            for tc in tool_calls:
                result = self.executor.execute(tc)
                tool_results.append({
                    'tool': tc.tool_name,
                    'parameters': tc.parameters,
                    'result': result
                })
                
                # Add to conversation
                conversation.append({
                    "role": "assistant",
                    "content": f"I'll use the {tc.tool_name} tool."
                })
                conversation.append({
                    "role": "system",
                    "content": f"Tool result: {json.dumps(result.data if result.success else result.error)}"
                })
            
            iteration += 1
        
        # Max iterations reached
        return {
            'response': "I've reached the maximum number of tool calls. Here's what I found:",
            'tool_calls': tool_results,
            'iterations': iteration,
            'incomplete': True
        }
    
    def _get_system_prompt(self) -> str:
        """Generate system prompt with available tools"""
        tools_desc = []
        for tool in self.tools.list_tools():
            params = ", ".join([f"{p.name}: {p.type}" for p in tool.parameters])
            tools_desc.append(f"- {tool.name}({params}): {tool.description}")
        
        return f"""You are a helpful AI assistant with access to tools. 
Use tools when needed to answer user queries accurately.

Available tools:
{chr(10).join(tools_desc)}

When you need to use a tool, respond with:
{{"tool": "tool_name", "parameters": {{"param1": "value1"}}}}

After receiving tool results, provide a helpful response to the user."""


# Example usage
if __name__ == '__main__':
    # Create mock vault interface for testing
    class MockVault:
        def search_notes(self, query, limit=5, include_content=True):
            return [{"title": "Test Note", "path": "test.md", "content": "This is a test"}]
        
        def get_vault_stats(self):
            return {"total_notes": 42, "total_words": 15000}
    
    vault = MockVault()
    registry = create_obsidian_tools(vault)
    
    print("Available Tools:")
    for tool in registry.list_tools():
        print(f"  - {tool.name}: {tool.description}")
    
    print("\nOpenAI Schema:")
    print(json.dumps(registry.get_openai_schema(), indent=2))
