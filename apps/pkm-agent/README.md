# PKM Agent

AI-enhanced Personal Knowledge Management agent with TUI, RAG, and MCP server capabilities.

## Features

- **TUI Interface**: Rich terminal UI for interacting with your knowledge base
- **RAG Pipeline**: Semantic search with ChromaDB vector store
- **MCP Server**: Model Context Protocol server for IDE integration
- **Multi-LLM Support**: OpenAI, Ollama, and Anthropic providers
- **Real-time Sync**: WebSocket-based synchronization with Obsidian
- **Plugin System**: Extensible architecture for custom functionality

## Installation

```bash
# Install with pip
pip install -e .

# Or with optional Ollama support
pip install -e ".[ollama]"

# Development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Start the TUI
pkm-agent tui

# Or use the short alias
pkma tui

# Start the MCP server
pkma mcp-server

# Start the API server
pkma api
```

## Configuration

Create a `.env` file or set environment variables:

```env
PKM_ROOT=/path/to/your/vault
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key
```

## Project Structure

```text
src/pkm_agent/
├── agentzero/       # Agent orchestration
├── api/             # REST API routes
├── data/            # Database and indexing
├── llm/             # LLM providers
├── observability/   # Metrics and monitoring
├── plugins/         # Plugin system
├── rag/             # RAG pipeline
├── security/        # Security middleware
├── tools/           # Utility tools
├── app.py           # Main application
├── cli.py           # CLI interface
├── config.py        # Configuration
├── mcp_server.py    # MCP server
├── studio.py        # Studio interface
└── tui.py           # Terminal UI
```

## License

MIT
