"""
MCP Server for PKM Agent.

This module provides a Model Context Protocol (MCP) server that exposes
the PKM agent's capabilities (search, RAG, etc.) to MCP clients.
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


class PKMMCPServer:
    """MCP server for PKM agent."""

    def __init__(self, app):
        self.app = app
        self.tools = self._register_tools()
        self.resources = self._register_resources()
        self.prompts = self._register_prompts()
        self.streams: dict[str, asyncio.Queue] = {}

    def _register_tools(self) -> dict[str, Any]:
        """Register available MCP tools."""
        return {
            "pkm_search": {
                "name": "pkm_search",
                "description": "Search the PKM knowledge base for relevant notes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of results (default: 10)",
                            "default": 10,
                        },
                        "filters": {
                            "type": "object",
                            "description": "Optional filters (tags, path, etc.)",
                            "default": {},
                        },
                    },
                    "required": ["query"],
                },
            },
            "pkm_ask": {
                "name": "pkm_ask",
                "description": "Ask a question with RAG-enhanced context from the knowledge base",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string", "description": "User's question"},
                        "conversation_id": {
                            "type": "string",
                            "description": "Optional conversation ID for context",
                        },
                        "use_context": {
                            "type": "boolean",
                            "description": "Whether to use RAG context (default: true)",
                            "default": True,
                        },
                    },
                    "required": ["message"],
                },
            },
            "pkm_get_stats": {
                "name": "pkm_get_stats",
                "description": "Get statistics about the PKM knowledge base",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "pkm_list_conversations": {
                "name": "pkm_list_conversations",
                "description": "List all conversations",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "pkm_index_notes": {
                "name": "pkm_index_notes",
                "description": "Index or re-index the PKM notes directory",
                "inputSchema": {"type": "object", "properties": {}},
            },
            "pkm_get_conversation_history": {
                "name": "pkm_get_conversation_history",
                "description": "Get conversation history for a specific conversation",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "conversation_id": {"type": "string", "description": "Conversation ID"},
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of messages (default: 50)",
                            "default": 50,
                        },
                    },
                    "required": ["conversation_id"],
                },
            },
            # ===================================================================
            # Obsidian Vault Operations - Extended PKM Tools
            # ===================================================================
            "pkm_create_note": {
                "name": "pkm_create_note",
                "description": "Create a new note in the Obsidian vault with optional frontmatter",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {
                            "type": "string",
                            "description": "Path for the new note (e.g., 'folder/note.md')",
                        },
                        "content": {
                            "type": "string",
                            "description": "Markdown content for the note",
                        },
                        "frontmatter": {
                            "type": "object",
                            "description": "Optional YAML frontmatter as key-value pairs",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
            "pkm_update_note": {
                "name": "pkm_update_note",
                "description": "Update an existing note (overwrite, append, or prepend)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                        "content": {"type": "string", "description": "Content to add/update"},
                        "mode": {
                            "type": "string",
                            "enum": ["overwrite", "append", "prepend"],
                            "description": "Update mode (default: append)",
                            "default": "append",
                        },
                    },
                    "required": ["path", "content"],
                },
            },
            "pkm_delete_note": {
                "name": "pkm_delete_note",
                "description": "Delete a note from the Obsidian vault",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note to delete"}
                    },
                    "required": ["path"],
                },
            },
            "pkm_search_replace": {
                "name": "pkm_search_replace",
                "description": "Search and replace text within a note",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                        "search": {"type": "string", "description": "Text to search for"},
                        "replace": {"type": "string", "description": "Replacement text"},
                        "use_regex": {
                            "type": "boolean",
                            "description": "Use regex matching (default: false)",
                            "default": False,
                        },
                        "case_sensitive": {
                            "type": "boolean",
                            "description": "Case sensitive search (default: false)",
                            "default": False,
                        },
                        "replace_all": {
                            "type": "boolean",
                            "description": "Replace all occurrences (default: true)",
                            "default": True,
                        },
                    },
                    "required": ["path", "search", "replace"],
                },
            },
            "pkm_manage_frontmatter": {
                "name": "pkm_manage_frontmatter",
                "description": "Manage note frontmatter (get, set, or delete keys)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                        "action": {
                            "type": "string",
                            "enum": ["get", "set", "delete"],
                            "description": "Action to perform",
                            "default": "get",
                        },
                        "key": {
                            "type": "string",
                            "description": "Frontmatter key (required for set/delete)",
                        },
                        "value": {"description": "Value to set (required for set action)"},
                    },
                    "required": ["path"],
                },
            },
            "pkm_manage_tags": {
                "name": "pkm_manage_tags",
                "description": "Manage note tags (list, add, or remove)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Path to the note"},
                        "action": {
                            "type": "string",
                            "enum": ["list", "add", "remove"],
                            "description": "Action to perform",
                            "default": "list",
                        },
                        "tags": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Tags to add or remove",
                        },
                    },
                    "required": ["path"],
                },
            },
            "pkm_get_daily_note": {
                "name": "pkm_get_daily_note",
                "description": "Get the daily note for a specific date (or today)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "date": {
                            "type": "string",
                            "description": "Date in YYYY-MM-DD format (default: today)",
                        }
                    },
                },
            },
            "pkm_apply_template": {
                "name": "pkm_apply_template",
                "description": "Apply a template to create or update a note",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "template_path": {
                            "type": "string",
                            "description": "Path to the template note",
                        },
                        "target_path": {
                            "type": "string",
                            "description": "Path for the target note",
                        },
                        "variables": {
                            "type": "object",
                            "description": "Variables to substitute in the template",
                        },
                    },
                    "required": ["template_path", "target_path"],
                },
            },
            "pkm_get_backlinks": {
                "name": "pkm_get_backlinks",
                "description": "Get all notes that link to the specified note",
                "inputSchema": {
                    "type": "object",
                    "properties": {"path": {"type": "string", "description": "Path to the note"}},
                    "required": ["path"],
                },
            },
            "pkm_batch_operations": {
                "name": "pkm_batch_operations",
                "description": "Execute multiple vault operations in batch",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "operations": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "operation": {"type": "string"},
                                    "path": {"type": "string"},
                                },
                            },
                            "description": "Array of operations to execute",
                        }
                    },
                    "required": ["operations"],
                },
            },
            "pkm_list_attachments": {
                "name": "pkm_list_attachments",
                "description": "List attachments in a directory",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "directory": {
                            "type": "string",
                            "description": "Directory to list (default: /)",
                            "default": "/",
                        },
                        "extension_filter": {
                            "type": "string",
                            "description": "Filter by extension (e.g., 'png,jpg,pdf')",
                        },
                    },
                },
            },
        }

    def _register_resources(self) -> dict[str, Any]:
        """Register available MCP resources."""
        return {
            "pkm://stats": {
                "uri": "pkm://stats",
                "name": "PKM Statistics",
                "description": "Current statistics about the PKM knowledge base",
                "mimeType": "application/json",
            },
            "pkm://config": {
                "uri": "pkm://config",
                "name": "PKM Configuration",
                "description": "Current PKM agent configuration",
                "mimeType": "application/json",
            },
        }

    def _register_prompts(self) -> dict[str, Any]:
        """Register available MCP prompts."""
        return {
            "summarize_notes": {
                "name": "summarize_notes",
                "description": "Generate a summary of the most relevant notes",
                "arguments": [
                    {"name": "topic", "description": "Topic to summarize", "required": True},
                    {
                        "name": "detail_level",
                        "description": "Level of detail (brief, medium, detailed)",
                        "required": False,
                    },
                ],
            },
            "daily_review": {
                "name": "daily_review",
                "description": "Generate a daily review of recent notes",
                "arguments": [
                    {
                        "name": "days_back",
                        "description": "Number of days to review",
                        "required": False,
                    }
                ],
            },
        }

    async def _handle_health(self, request_id: Any) -> dict[str, Any]:
        """Handle health check request."""
        try:
            stats = await self.app.get_stats() if hasattr(self.app, "get_stats") else {}
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "tools_count": len(self.tools),
                "resources_count": len(self.resources),
                "prompts_count": len(self.prompts),
                "stats": stats,
            }
        except Exception as e:
            return {"status": "unhealthy", "timestamp": datetime.now().isoformat(), "error": str(e)}

    async def handle_request(self, request: dict[str, Any]) -> dict[str, Any]:
        """Handle an MCP request."""
        method = request.get("method")
        request_id = request.get("id")

        # Add health check support
        if method == "health":
            return await self._handle_health(request_id)

        logger.debug(f"MCP request: {method} (id: {request_id})")

        try:
            if method == "initialize":
                return await self._handle_initialize(request, request_id)
            elif method == "tools/list":
                return await self._handle_list_tools(request, request_id)
            elif method == "tools/call":
                return await self._handle_tool_call(request, request_id)
            elif method == "resources/list":
                return await self._handle_list_resources(request, request_id)
            elif method == "resources/read":
                return await self._handle_read_resource(request, request_id)
            elif method == "prompts/list":
                return await self._handle_list_prompts(request, request_id)
            elif method == "prompts/get":
                return await self._handle_get_prompt(request, request_id)
            else:
                return self._error_response(request_id, -32601, "Method not found")

        except Exception as e:
            logger.error(f"Error handling MCP request: {e}")
            return self._error_response(request_id, -32603, str(e))

    async def _handle_initialize(self, request: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Handle initialization request."""
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "pkm-rag-mcp-server", "version": "1.0.0"},
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            },
        }

    async def _handle_list_tools(self, request: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Handle tools/list request."""
        tools = [
            {
                "name": tool_name,
                "description": tool["description"],
                "inputSchema": tool["inputSchema"],
            }
            for tool_name, tool in self.tools.items()
        ]

        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": tools}}

    async def _handle_tool_call(self, request: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Handle tools/call request."""
        params = request.get("params", {})
        tool_name = params.get("name")
        arguments = params.get("arguments", {})

        if tool_name not in self.tools:
            return self._error_response(request_id, -32602, f"Unknown tool: {tool_name}")

        try:
            result = await self._execute_tool(tool_name, arguments)
            return {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {"content": [{"type": "text", "text": json.dumps(result, indent=2)}]},
            }
        except Exception as e:
            logger.error(f"Tool execution error: {e}")
            return self._error_response(request_id, -32603, str(e))

    async def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a tool."""
        if tool_name == "pkm_search":
            results = await self.app.search(
                query=arguments.get("query"),
                limit=arguments.get("limit", 10),
                filters=arguments.get("filters", {}),
            )
            return {"results": results}

        elif tool_name == "pkm_ask":
            stream_id = str(datetime.now().timestamp())
            queue = asyncio.Queue()
            self.streams[stream_id] = queue

            # Start streaming task
            asyncio.create_task(self._stream_response(stream_id, arguments))

            return {"stream_id": stream_id, "message": "Streaming response initiated"}

        elif tool_name == "pkm_get_stats":
            stats = await self.app.get_stats()
            return stats

        elif tool_name == "pkm_list_conversations":
            conversations = self.app.list_conversations()
            return {"conversations": conversations}

        elif tool_name == "pkm_index_notes":
            result = await self.app.index_pkm()
            return result

        elif tool_name == "pkm_get_conversation_history":
            history = self.app.get_conversation_history(limit=arguments.get("limit", 50))
            return {"history": history}

        # ===================================================================
        # Obsidian Vault Operations - Extended PKM Tools
        # ===================================================================
        elif tool_name == "pkm_create_note":
            vault_client = self._get_vault_client()
            path = arguments.get("path")
            if not path:
                raise ValueError("path is required for pkm_create_note")
            result = await vault_client.create_note(
                path=str(path),
                content=str(arguments.get("content", "")),
                frontmatter=arguments.get("frontmatter"),
            )
            return {"success": True, "result": result}

        elif tool_name == "pkm_update_note":
            vault_client = self._get_vault_client()
            path = arguments.get("path")
            if not path:
                raise ValueError("path is required for pkm_update_note")
            path_str = str(path)
            content = str(arguments.get("content", ""))
            mode = arguments.get("mode", "append")
            if mode == "append":
                result = await vault_client.append_to_note(path_str, content)
            elif mode == "prepend":
                result = await vault_client.prepend_to_note(path_str, content)
            else:  # overwrite
                result = await vault_client.update_note(path_str, content, mode="overwrite")
            return {"success": True, "result": result}

        elif tool_name == "pkm_delete_note":
            vault_client = self._get_vault_client()
            path = arguments.get("path")
            if not path:
                raise ValueError("path is required for pkm_delete_note")
            result = await vault_client.delete_note(str(path))
            return {"success": True, "result": result}

        elif tool_name == "pkm_search_replace":
            vault_client = self._get_vault_client()
            path = arguments.get("path")
            search = arguments.get("search")
            replace_text = arguments.get("replace")
            if not path or not search:
                raise ValueError("path and search are required for pkm_search_replace")
            result = await vault_client.search_and_replace(
                path=str(path),
                search=str(search),
                replace=str(replace_text) if replace_text else "",
                use_regex=arguments.get("use_regex", False),
                case_sensitive=arguments.get("case_sensitive", False),
                replace_all=arguments.get("replace_all", True),
            )
            return {"success": True, "result": result}

        elif tool_name == "pkm_manage_frontmatter":
            vault_client = self._get_vault_client()
            action = arguments.get("action", "get")
            path = arguments.get("path")
            if not path:
                raise ValueError("path is required for pkm_manage_frontmatter")
            path_str = str(path)

            if action == "get":
                frontmatter = await vault_client.get_frontmatter(path_str)
                return {"frontmatter": frontmatter}
            elif action == "set":
                key = arguments.get("key")
                if not key:
                    raise ValueError("key is required for set action")
                result = await vault_client.set_frontmatter_key(
                    path_str, str(key), arguments.get("value")
                )
                return {"success": True, "result": result}
            elif action == "delete":
                key = arguments.get("key")
                if not key:
                    raise ValueError("key is required for delete action")
                result = await vault_client.delete_frontmatter_key(path_str, str(key))
                return {"success": True, "result": result}
            else:
                raise ValueError(f"Unknown frontmatter action: {action}")

        elif tool_name == "pkm_manage_tags":
            vault_client = self._get_vault_client()
            action = arguments.get("action", "list")
            path = arguments.get("path")
            if not path:
                raise ValueError("path is required for pkm_manage_tags")
            path_str = str(path)

            if action == "list":
                tags = await vault_client.get_tags(path_str)
                return {"tags": tags}
            elif action == "add":
                result = await vault_client.add_tags(path_str, arguments.get("tags", []))
                return {"success": True, "result": result}
            elif action == "remove":
                result = await vault_client.remove_tags(path_str, arguments.get("tags", []))
                return {"success": True, "result": result}
            else:
                raise ValueError(f"Unknown tags action: {action}")

        elif tool_name == "pkm_get_daily_note":
            vault_client = self._get_vault_client()
            result = await vault_client.get_periodic_note("daily", arguments.get("date"))
            return result

        elif tool_name == "pkm_apply_template":
            vault_client = self._get_vault_client()
            template_path = arguments.get("template_path")
            target_path = arguments.get("target_path")
            if not template_path or not target_path:
                raise ValueError("template_path and target_path are required")
            # Read template
            template = await vault_client.read_note(str(template_path))
            content = template.get("content", "")

            # Substitute variables
            variables = arguments.get("variables", {})
            for key, value in variables.items():
                content = content.replace(f"{{{{  {key} }}}}", str(value))
                content = content.replace(f"{{{{{key}}}}}", str(value))

            # Create target note
            result = await vault_client.update_note(str(target_path), content, mode="overwrite")
            return {"success": True, "path": str(target_path), "result": result}

        elif tool_name == "pkm_get_backlinks":
            vault_client = self._get_vault_client()
            path = arguments.get("path")
            if not path:
                raise ValueError("path is required for pkm_get_backlinks")
            backlinks = await vault_client.get_backlinks(str(path))
            return {"backlinks": backlinks}

        elif tool_name == "pkm_batch_operations":
            vault_client = self._get_vault_client()
            operations = arguments.get("operations", [])
            results = []

            for op in operations:
                try:
                    op_type = op.get("operation")
                    if op_type == "add_tags":
                        res = await vault_client.add_tags(op.get("path"), op.get("tags", []))
                    elif op_type == "remove_tags":
                        res = await vault_client.remove_tags(op.get("path"), op.get("tags", []))
                    elif op_type == "set_frontmatter":
                        res = await vault_client.set_frontmatter_key(
                            op.get("path"), op.get("key"), op.get("value")
                        )
                    elif op_type == "append":
                        res = await vault_client.append_to_note(
                            op.get("path"), op.get("content", "")
                        )
                    elif op_type == "delete":
                        res = await vault_client.delete_note(op.get("path"))
                    else:
                        res = {"error": f"Unknown batch operation: {op_type}"}
                    results.append({"success": True, "result": res})
                except Exception as e:
                    results.append({"success": False, "error": str(e)})

            return {"results": results}

        elif tool_name == "pkm_list_attachments":
            vault_client = self._get_vault_client()
            result = await vault_client.list_notes(
                directory=arguments.get("directory", "/"),
                extension_filter=arguments.get(
                    "extension_filter", "png,jpg,jpeg,gif,pdf,mp3,mp4,webp"
                ),
            )
            return result

        else:
            raise ValueError(f"Unknown tool: {tool_name}")

    def _get_vault_client(self):
        """Get or create the Obsidian vault client."""
        if not hasattr(self, "_vault_client"):
            from pkm_agent.agentzero.mcp_client import ObsidianMCPClient

            # Get config from app
            vault_config = getattr(self.app, "vault_config", {})
            if not vault_config:
                vault_config = {"base_url": "http://127.0.0.1:27123", "api_key": ""}
            self._vault_client = ObsidianMCPClient(vault_config)
        return self._vault_client

    async def _stream_response(self, stream_id: str, arguments: dict[str, Any]):
        """Stream a response to the queue."""
        try:
            async for chunk in self.app.chat(
                message=arguments.get("message"),
                conversation_id=arguments.get("conversation_id"),
                use_context=arguments.get("use_context", True),
            ):
                await self.streams[stream_id].put(chunk)
        except Exception as e:
            logger.error(f"Streaming error: {e}")
        finally:
            await self.streams[stream_id].put(None)
            del self.streams[stream_id]

    async def _handle_list_resources(
        self, request: dict[str, Any], request_id: Any
    ) -> dict[str, Any]:
        """Handle resources/list request."""
        resources = [
            {
                "uri": resource["uri"],
                "name": resource["name"],
                "description": resource["description"],
                "mimeType": resource["mimeType"],
            }
            for resource in self.resources.values()
        ]

        return {"jsonrpc": "2.0", "id": request_id, "result": {"resources": resources}}

    async def _handle_read_resource(
        self, request: dict[str, Any], request_id: Any
    ) -> dict[str, Any]:
        """Handle resources/read request."""
        params = request.get("params", {})
        uri = params.get("uri")

        if uri == "pkm://stats":
            stats = await self.app.get_stats()
            content = json.dumps(stats, indent=2)
        elif uri == "pkm://config":
            content = json.dumps(self.app.config.__dict__, indent=2)
        else:
            return self._error_response(request_id, -32602, f"Unknown resource: {uri}")

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"contents": [{"uri": uri, "mimeType": "application/json", "text": content}]},
        }

    async def _handle_list_prompts(
        self, request: dict[str, Any], request_id: Any
    ) -> dict[str, Any]:
        """Handle prompts/list request."""
        prompts = [
            {
                "name": prompt["name"],
                "description": prompt["description"],
                "arguments": prompt.get("arguments", []),
            }
            for prompt in self.prompts.values()
        ]

        return {"jsonrpc": "2.0", "id": request_id, "result": {"prompts": prompts}}

    async def _handle_get_prompt(self, request: dict[str, Any], request_id: Any) -> dict[str, Any]:
        """Handle prompts/get request."""
        params = request.get("params", {})
        prompt_name = params.get("name")
        arguments = params.get("arguments", {})

        if prompt_name not in self.prompts:
            return self._error_response(request_id, -32602, f"Unknown prompt: {prompt_name}")

        if prompt_name == "summarize_notes":
            topic = arguments.get("topic", "")
            detail_level = arguments.get("detail_level", "medium")

            results = await self.app.search(topic, limit=5)

            messages = [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Summarize the following notes about '{topic}' with {detail_level} detail:\n\n"
                        + "\n".join(
                            [
                                f"- {r.get('title', r.get('path', 'Unknown'))}: {r.get('content', '')[:200]}"
                                for r in results
                            ]
                        ),
                    },
                }
            ]
        elif prompt_name == "daily_review":
            days_back = arguments.get("days_back", 1)

            messages = [
                {
                    "role": "user",
                    "content": {
                        "type": "text",
                        "text": f"Generate a daily review of notes from the last {days_back} days.",
                    },
                }
            ]
        else:
            messages = []

        return {"jsonrpc": "2.0", "id": request_id, "result": {"messages": messages}}

    def _error_response(self, request_id: Any, code: int, message: str) -> dict[str, Any]:
        """Create an error response."""
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


async def run_stdio_server(app):
    """Run the MCP server using stdio transport."""
    server = PKMMCPServer(app)
    logger.info("PKM MCP Server starting on stdio transport")

    try:
        while True:
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)

            if not line:
                break

            line = line.strip()
            if not line:
                continue

            try:
                request = json.loads(line)
                response = await server.handle_request(request)
                print(json.dumps(response))
                sys.stdout.flush()
            except json.JSONDecodeError:
                logger.error("Failed to parse request as JSON")
                continue
            except Exception as e:
                logger.error(f"Error processing request: {e}")
                continue

    except KeyboardInterrupt:
        logger.info("PKM MCP Server stopped")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


async def main():
    """Main entry point for the MCP server."""
    import os
    import sys

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

    from pkm_agent.app import PKMAgentApp
    from pkm_agent.config import load_config

    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    config = load_config()
    config.ensure_dirs()

    app = PKMAgentApp(config)
    await app.initialize()

    await run_stdio_server(app)


if __name__ == "__main__":
    asyncio.run(main())
