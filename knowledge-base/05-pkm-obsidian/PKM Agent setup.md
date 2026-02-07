## Prerequisites

- **Python 3.11+**
- **pip** package manager
- (Optional) **Ollama** for local LLM support
- (Optional) **OpenAI API key** for cloud LLM

# Quick-setup
## Windows
```
cd B0LK13v2\pkm-agent
.\build.bat
```

## MacOS
```
cd B0LK13v2/pkm-agent
chmod +x build.sh
./build.sh
```

# Manual installation
```
cd pkm-agent

# Basic install with dev dependencies
pip install -e ".[dev]"

# With Ollama support
pip install -e ".[dev,ollama]"
```

## Environment variables
```
# LLM Provider (openai or ollama)
PKMA_LLM__PROVIDER=openai
PKMA_LLM__API_KEY=your-api-key-here

# Or for Ollama (local)
PKMA_LLM__PROVIDER=ollama
```

# Create PKM directory
```
mkdir pkm
# Add your markdown notes here
```

# Search knowledge base
```
pkm-agent search "your query"
```

## Launch TUI
```
pkm-agent tui
```

## Ask question RAG-chat
```
pkm-agent ask "What is in my notes about X?"
```

## Run as MCP server (integration)
```
python -m pkm_agent.mcp_server
```

## Running tests
```
pytest tests/ -v
```

## Key environment variables
```
Variable	        Description	                    Default
PKMA_LLM__PROVIDER	LLM provider (openai or ollama)	openai
PKMA_LLM__API_KEY	API key for OpenAI	            -
PKMA_PKM_ROOT	    Path to your notes directory	./pkm
PKMA_DATA_DIR	    Data directory for DB/vectors	./.pkm-agent
PKMA_LOG_LEVEL	    Logging level	                INFO
PKMA_DEBUG	        Enable debug mode	            False
```

## Full system-setup
```
# From repository root
.\setup-agent-system.bat   # Windows
./setup-agent-system.sh    # Linux/Mac
```