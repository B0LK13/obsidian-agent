# PKM Agent

Personal Knowledge Management Agent - Python backend for Obsidian Agent plugin.

## Overview

This package provides advanced backend features for the Obsidian Agent plugin, including:
- Full vault indexing and search
- Vector embeddings for semantic search  
- RAG (Retrieval-Augmented Generation) pipeline
- Real-time file synchronization via WebSockets
- Advanced analytics and link analysis

## Installation

### Development Installation

```bash
cd pkm-agent
pip install -e ".[dev]"
```

### Production Installation

```bash
pip install pkm-agent
```

## Features

- **Full-Text Search**: Fast SQLite FTS5-based search
- **Semantic Search**: Vector embeddings with ChromaDB
- **Real-time Sync**: WebSocket-based file watching and synchronization
- **Extensible**: Plugin architecture for custom features

## Quick Start

```bash
# Index your vault
pkm-agent index --vault ~/Documents/MyVault

# Start the sync server
pkm-agent serve --port 8000

# Search your notes
pkm-agent search "machine learning"
```

## Configuration

Create a configuration file at `~/.config/pkm-agent/config.yaml`:

```yaml
vault:
  path: ~/Documents/MyVault
  
server:
  host: 127.0.0.1
  port: 8000
  
search:
  provider: chromadb
  embedding_model: all-MiniLM-L6-v2
```

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run comprehensive tests
python test_comprehensive.py

# Run demo
python demo_poc.py
```

## License

MIT License - see LICENSE file for details
