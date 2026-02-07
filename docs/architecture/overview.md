# Architecture Overview

## System Components

```
┌─────────────────────────────────────────────────────────────┐
│                      B0LK13v2 System                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────┐     WebSocket      ┌────────────────┐ │
│  │  Obsidian       │◄──────────────────►│  PKM Agent     │ │
│  │  Plugin         │    (Port 27125)    │  (Python)      │ │
│  │  (TypeScript)   │                    │                │ │
│  └─────────────────┘                    └────────────────┘ │
│         │                                      │           │
│         │                                      │           │
│         ▼                                      ▼           │
│  ┌─────────────────┐                    ┌────────────────┐ │
│  │  Obsidian       │                    │  ChromaDB      │ │
│  │  Vault          │                    │  (Vectors)     │ │
│  │  (Markdown)     │                    └────────────────┘ │
│  └─────────────────┘                           │           │
│                                                │           │
│                                                ▼           │
│                                         ┌────────────────┐ │
│                                         │  SQLite        │ │
│                                         │  (Metadata)    │ │
│                                         └────────────────┘ │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## PKM Agent Components

### Core Modules

- **app.py**: Main application orchestrator
- **config.py**: Configuration management with Pydantic
- **cli.py**: Command-line interface with Click
- **tui.py**: Terminal UI with Textual

### Data Layer (`data/`)

- **database.py**: SQLite database for notes, tags, links, conversations
- **indexer.py**: File indexer with watch mode for real-time updates

### RAG Pipeline (`rag/`)

- **chunker.py**: Text chunking for embeddings
- **embeddings.py**: Sentence-transformers embedding engine
- **vectorstore.py**: ChromaDB vector storage
- **retriever.py**: Semantic search and context retrieval

### LLM Providers (`llm/`)

- **base.py**: Abstract LLM provider interface
- **openai_provider.py**: OpenAI API integration
- **ollama_provider.py**: Ollama local LLM support

### Sync System

- **websocket_sync.py**: WebSocket server for real-time sync with Obsidian

## Obsidian Plugin Components

### Core Files

- **main.tsx**: Plugin entry point and React components
- **src/SyncClient.ts**: WebSocket client for backend communication
- **src/VaultManager.ts**: Obsidian vault operations
- **src/OpenAIService.ts**: Direct OpenAI API for plugin-side AI
- **src/ToolHandler.ts**: Tool execution for AI function calls

## Data Flow

### Indexing Flow

1. File watcher detects changes in vault
2. FileIndexer parses markdown and frontmatter
3. Database stores note metadata
4. Chunker splits content into chunks
5. EmbeddingEngine generates vectors
6. VectorStore persists embeddings

### Query Flow

1. User enters query
2. EmbeddingEngine generates query vector
3. VectorStore performs similarity search
4. Retriever formats context
5. LLM generates response with context
6. Response streamed to user

### Sync Flow

1. Obsidian plugin connects via WebSocket
2. File changes trigger sync events
3. PKM Agent processes events
4. Updates propagated to all connected clients

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| PKMA_PKM_ROOT | Path to Obsidian vault | ./pkm |
| PKMA_LLM__PROVIDER | LLM provider | openai |
| PKMA_LLM__MODEL | Model name | gpt-4o-mini |
| OPENAI_API_KEY | OpenAI API key | - |

### Plugin Settings

- OpenAI API Key
- Model selection
- Temperature
- Base URL (for local LLMs)
