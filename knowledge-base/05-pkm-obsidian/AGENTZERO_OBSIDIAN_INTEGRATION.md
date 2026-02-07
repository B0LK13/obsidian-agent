# Obsidian Agent System - AgentZero + MCP Integration

## Overview

This document describes the integration of AgentZero multi-agent orchestration with the Obsidian MCP (Model Context Protocol) server and PKM RAG capabilities. The system provides a powerful, coordinated AI agent architecture for managing your Obsidian vault.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Interface                             │
│  (Obsidian Plugin React UI + Python TUI + CLI)            │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      ▼
┌─────────────────────────────────────────────────────────────────┐
│              AgentZero Orchestrator                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ Vault       │  │ RAG         │  │ Context     │ │
│  │ Manager     │  │ Agent       │  │ Agent       │ │
│  │ Agent       │  │             │  │             │ │
│  └─────────────┘  └─────────────┘  └─────────────┘ │
│  ┌─────────────┐  ┌─────────────┐                    │
│  │ Planner     │  │ Memory      │                    │
│  │ Agent       │  │ Agent       │                    │
│  └─────────────┘  └─────────────┘                    │
└───────────┬─────────────────────┬──────────────────────────┘
            │                     │
            ▼                     ▼
┌──────────────────┐    ┌──────────────────┐
│  Obsidian       │    │  PKM RAG        │
│  MCP Server     │    │  MCP Server     │
└────────┬────────┘    └────────┬────────┘
         │                     │
         ▼                     ▼
┌──────────────────┐    ┌──────────────────┐
│  Obsidian       │    │  PKM Database   │
│  Vault          │    │  + Vector Store │
└──────────────────┘    └──────────────────┘
```

## Components

### 1. AgentZero Orchestrator

**Location**: `pkm-agent/src/pkm_agent/agentzero/`

The AgentZero orchestrator coordinates multiple specialized agents:

#### Vault Manager Agent
- **Capabilities**: Read, create, update notes, search vault, manage tags
- **Tools**:
  - `read_note` - Read note content and metadata
  - `create_note` - Create new notes
  - `update_note` - Update existing notes (append, prepend, overwrite)
  - `search_vault` - Search across vault
  - `manage_tags` - Add/remove/list tags

#### RAG Agent
- **Capabilities**: Search knowledge base semantically, generate responses with context
- **Tools**:
  - `search_knowledge` - Semantic search with embeddings
  - `generate_response` - Generate RAG-enhanced responses

#### Context Agent
- **Capabilities**: Get active file context, update context
- **Tools**:
  - `get_active_context` - Get currently active file
  - `update_context` - Update working context

#### Planner Agent
- **Capabilities**: Create execution plans, coordinate multi-agent tasks
- **Tools**:
  - `plan_task` - Break down complex tasks
  - `coordinate_agents` - Execute coordinated agent workflows

#### Memory Agent
- **Capabilities**: Store and retrieve conversation history
- **Tools**:
  - `store_message` - Store messages in memory
  - `retrieve_conversation` - Retrieve conversation history

### 2. MCP Servers

#### Obsidian MCP Server
**Installation**:
```bash
npm install -g obsidian-mcp-server
```

**Configuration**: See `.mcp/config.json`

**Available Tools**:
- `obsidian_read_note` - Read note content
- `obsidian_update_note` - Update note
- `obsidian_search_replace` - Search and replace
- `obsidian_global_search` - Global vault search
- `obsidian_list_notes` - List notes
- `obsidian_manage_frontmatter` - Manage YAML frontmatter
- `obsidian_manage_tags` - Manage tags
- `obsidian_delete_note` - Delete note

#### PKM RAG MCP Server
**Location**: `pkm-agent/src/pkm_agent/mcp_server.py`

**Running**:
```bash
cd pkm-agent
python -m pkm_agent.mcp_server
```

**Available Tools**:
- `pkm_search` - Search knowledge base
- `pkm_ask` - Ask questions with RAG
- `pkm_get_stats` - Get statistics
- `pkm_list_conversations` - List conversations
- `pkm_index_notes` - Index notes
- `pkm_get_conversation_history` - Get conversation history

### 3. MCP Clients

#### Python MCP Client
**Location**: `pkm-agent/src/pkm_agent/agentzero/mcp_client.py`

Provides clients for both Obsidian and PKM RAG MCP servers.

**Usage**:
```python
from pkm_agent.agentzero import create_unified_client

config = {
    "obsidian": {
        "base_url": "http://127.0.0.1:27123",
        "api_key": "your-api-key"
    },
    "pkm_rag": {
        "base_url": "http://127.0.0.1:27124"
    }
}

client = await create_unified_client(config)

# Use Obsidian client
await client.obsidian_client.read_note("note.md")

# Use PKM RAG client
results = await client.pkm_rag_client.search("python programming")
```

#### TypeScript MCP Client
**Location**: `obsidian-pkm-agent/src/MCPClient.ts`

Provides type-safe MCP client integration for the Obsidian plugin.

**Usage**:
```typescript
import { UnifiedMCPClient } from './MCPClient';

const client = new UnifiedMCPClient({
  obsidian: {
    baseUrl: 'http://127.0.0.1:27123',
    apiKey: 'your-api-key'
  },
  pkmRAG: {
    baseUrl: 'http://127.0.0.1:27124'
  }
});

await client.initialize();

const obsidianClient = client.getObsidianClient();
const pkmClient = client.getPKMRAGClient();

const note = await obsidianClient.readNote('note.md');
const results = await pkmClient.search('python programming');
```

## Installation

### Prerequisites

1. **Obsidian** - Install from [obsidian.md](https://obsidian.md)
2. **Obsidian Local REST API Plugin** - Enable in Obsidian settings
3. **Node.js 18+** - For MCP servers
4. **Python 3.11+** - For PKM agent

### Step 1: Configure Obsidian Local REST API

1. Open Obsidian Settings → Community Plugins
2. Browse for "Obsidian Local REST API" and install
3. Enable the plugin
4. Generate an API key in plugin settings
5. Note the base URL (default: `http://127.0.0.1:27123`)

### Step 2: Install Obsidian MCP Server

```bash
npm install -g obsidian-mcp-server
```

Or from source:
```bash
git clone https://github.com/cyanheads/obsidian-mcp-server.git
cd obsidian-mcp-server
npm install
npm build
```

### Step 3: Configure MCP Settings

Create `.mcp/config.json`:
```json
{
  "mcpServers": {
    "obsidian-mcp-server": {
      "command": "npx",
      "args": ["obsidian-mcp-server"],
      "env": {
        "OBSIDIAN_API_KEY": "YOUR_API_KEY",
        "OBSIDIAN_BASE_URL": "http://127.0.0.1:27123",
        "OBSIDIAN_VERIFY_SSL": "false",
        "OBSIDIAN_ENABLE_CACHE": "true"
      },
      "disabled": false,
      "autoApprove": ["obsidian_read_note", "obsidian_list_notes"]
    },
    "pkm-rag-server": {
      "command": "python",
      "args": ["-m", "pkm_agent.mcp_server"],
      "env": {
        "PKMA_LLM__PROVIDER": "openai",
        "PKMA_LLM__MODEL": "gpt-4o-mini",
        "PKMA_LLM__API_KEY": "your-openai-api-key",
        "PKMA_PKM_ROOT": "./pkm",
        "PKMA_DATA_DIR": "./.pkm-agent"
      },
      "disabled": false,
      "autoApprove": ["pkm_search", "pkm_ask", "pkm_get_stats"]
    }
  }
}
```

### Step 4: Install Python PKM Agent

```bash
cd pkm-agent
pip install -e ".[dev]"
```

For Ollama support:
```bash
pip install -e ".[dev,ollama]"
```

### Step 5: Build Obsidian Plugin

```bash
cd obsidian-pkm-agent
npm install
npm run build
```

Copy the built files to your Obsidian vault's plugins directory:
```bash
cp -r dist/* ~/.obsidian/plugins/obsidian-pkm-agent/
```

## Usage

### Starting the System

1. **Start Obsidian** (Local REST API plugin should be running)
2. **Start PKM RAG MCP Server**:
   ```bash
   cd pkm-agent
   python -m pkm_agent.mcp_server
   ```
3. **Enable Obsidian Plugin** in Obsidian settings

### Using the Obsidian Plugin

1. Open the PKM Agent sidebar (click the bot icon in ribbon)
2. Type your request in the chat
3. The agent will:
   - Parse your request
   - Use the planner to break it down into tasks
   - Coordinate agents to execute tasks
   - Return results with tool execution details

**Example requests**:
- "Create a daily note with today's date"
- "Search for notes about Python programming"
- "Summarize the note about 'Project X'"
- "Find all notes tagged #important and tag them #urgent"
- "Create a zettelkasten note connecting these ideas..."

### Using the Python CLI

```bash
# Search knowledge base
pkm-agent search "machine learning"

# Ask a question
pkm-agent ask "What did I learn about Python?"

# Launch TUI
pkm-agent tui

# Get statistics
pkm-agent stats
```

### Using AgentZero Directly

```python
import asyncio
from pkm_agent.agentzero import create_orchestrator

async def main():
    config = {
        "vault_manager": {
            "enabled": True,
            "base_url": "http://127.0.0.1:27123",
            "api_key": "your-api-key"
        },
        "rag_agent": {
            "enabled": True
        },
        "context_agent": {
            "enabled": True
        },
        "planner_agent": {
            "enabled": True,
            "llm": {
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "your-openai-api-key"
            }
        },
        "memory_agent": {
            "enabled": True,
            "storage_type": "sqlite",
            "db_path": "./data/agent_memory.db"
        }
    }

    orchestrator = await create_orchestrator(config)

    # Process user request
    async for response in orchestrator.process_user_request(
        "Create a note about Python programming"
    ):
        print(response)

    await orchestrator.stop()

asyncio.run(main())
```

## Features

### Multi-Agent Coordination
- **Vault Management**: Read, create, update notes via MCP
- **RAG Integration**: Semantic search with vector embeddings
- **Context Awareness**: Knows about active file
- **Task Planning**: Breaks down complex requests
- **Memory Management**: Stores conversation history

### Tool Execution
- Streaming responses
- Visual tool execution details
- Error handling and recovery
- Tool dependency management

### MCP Protocol Compliance
- Standardized tool interface
- Resource management
- Prompt templates
- Streaming support

## Configuration

### Obsidian Plugin Settings

Accessible via Settings → PKM Agent:

- **OpenAI API Key**: Required for AI features
- **Model**: GPT-4o, GPT-4o Mini, GPT-4 Turbo, GPT-3.5 Turbo
- **Temperature**: Controls randomness (0-1)
- **Context Awareness**: Enable active file context
- **Proactive Assistance**: Experimental feature

### Environment Variables

```bash
# LLM Configuration
PKMA_LLM__PROVIDER=openai
PKMA_LLM__MODEL=gpt-4o-mini
PKMA_LLM__API_KEY=sk-...
PKMA_LLM__BASE_URL=https://api.openai.com/v1

# RAG Configuration
PKMA_RAG__EMBEDDING_MODEL=all-MiniLM-L6-v2
PKMA_RAG__CHUNK_SIZE=512
PKMA_RAG__TOP_K=5

# Storage Configuration
PKMA_PKM_ROOT=./pkm
PKMA_DATA_DIR=./.pkm-agent
PKMA_DB_PATH=./data/pkm.db
PKMA_CHROMA_PATH=./data/chroma

# MCP Configuration
MCP_LOG_LEVEL=info
OBSIDIAN_BASE_URL=http://127.0.0.1:27123
OBSIDIAN_API_KEY=your-api-key
OBSIDIAN_VERIFY_SSL=false
OBSIDIAN_ENABLE_CACHE=true
```

## Troubleshooting

### Common Issues

**1. Obsidian MCP Server connection fails**
- Verify Obsidian is running
- Check Local REST API plugin is enabled
- Confirm API key is correct
- Check base URL matches plugin settings

**2. PKM RAG MCP Server won't start**
- Verify Python dependencies are installed
- Check environment variables are set
- Ensure PKM directory exists
- Check port 27124 is not in use

**3. Agent doesn't respond**
- Check OpenAI API key is configured
- Verify internet connection for API calls
- Check logs for errors
- Try restarting the plugin

**4. Vector store errors**
- Re-index the PKM directory: `pkm-agent index`
- Check embedding model is downloaded
- Verify ChromaDB is installed

### Debug Logging

Enable debug logging:
```bash
# Python
export PKMA_LOG_LEVEL=debug

# MCP Server
export MCP_LOG_LEVEL=debug

# Obsidian Plugin
# Check console in Obsidian Developer Tools (Ctrl+Shift+I)
```

## Development

### Running Tests

```bash
# Python tests
cd pkm-agent
pytest tests/

# With coverage
pytest tests/ --cov=src/pkm_agent
```

### Building

```bash
# Obsidian plugin
cd obsidian-pkm-agent
npm run build

# Python package
cd pkm-agent
pip install -e .
```

### Project Structure

```
.
├── .mcp/
│   └── config.json              # MCP server configuration
├── obsidian-pkm-agent/         # TypeScript Obsidian plugin
│   ├── src/
│   │   ├── MCPClient.ts        # MCP client implementation
│   │   ├── VaultManager.ts    # Vault operations
│   │   ├── OpenAIService.ts   # OpenAI integration
│   │   ├── ToolHandler.ts     # Tool execution
│   │   └── main.tsx         # React UI + Plugin
│   └── package.json
├── pkm-agent/                 # Python PKM agent
│   ├── src/pkm_agent/
│   │   ├── agentzero/        # AgentZero orchestration
│   │   │   ├── orchestrator.py
│   │   │   ├── mcp_client.py
│   │   │   ├── llm_client.py
│   │   │   └── storage.py
│   │   ├── mcp_server.py      # PKM MCP server
│   │   ├── app.py            # Main application
│   │   ├── data/             # Database & indexing
│   │   ├── llm/              # LLM providers
│   │   └── rag/              # RAG engine
│   └── pyproject.toml
├── pkm/                       # Obsidian vault / PKM directory
└── OBSIDIAN_AGENT_PLAN.md    # Development plan
```

## License

MIT License - See LICENSE files in respective directories.

## Contributing

Contributions welcome! Please read CONTRIBUTING.md for guidelines.

## Support

- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions
- **Documentation**: Full docs at [URL]

---

**Built with AgentZero, Model Context Protocol, and ❤️**
