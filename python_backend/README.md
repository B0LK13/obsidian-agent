# Obsidian Agent - Python Backend

Advanced features for the Obsidian Agent plugin, including:
- 📊 **Full Vault Indexing** - Fast SQLite FTS5 search
- 🧠 **Vector Embeddings** - Semantic search with ChromaDB
- 🔍 **RAG Pipeline** - Retrieval-Augmented Generation
- 📈 **Analytics** - Vault statistics and insights
- 🔗 **Link Analysis** - Graph-based relationship discovery

## Requirements

- Python 3.10+
- 2GB+ RAM (for embeddings)
- SQLite 3.35+ (for FTS5)

## Installation

### Using Poetry (Recommended)

```bash
cd python_backend
poetry install
```

### Using pip

```bash
cd python_backend
pip install -e .
```

### With API Server

```bash
poetry install --extras api
# or
pip install -e ".[api]"
```

## Quick Start

### 1. Index Your Vault

```bash
obsidian-agent index --vault ~/Documents/MyVault
```

### 2. Search

```bash
# Semantic search
obsidian-agent search "machine learning concepts"

# Keyword search
obsidian-agent search "TODO" --keyword

# Limit results
obsidian-agent search "python" --limit 5
```

### 3. Get Statistics

```bash
obsidian-agent stats
```

### 4. Start API Server (Optional)

```bash
obsidian-agent serve --port 8000
```

## Configuration

Create `~/.config/obsidian-agent/config.yaml`:

```yaml
vault:
  path: ~/Documents/MyVault
  exclude_folders:
    - .obsidian
    - templates
    - _archive

database:
  path: ~/.local/share/obsidian-agent/vault.db
  backup_enabled: true

vector_store:
  provider: chromadb
  embedding_model: all-MiniLM-L6-v2
  persist_directory: ~/.local/share/obsidian-agent/chroma

search:
  default_limit: 10
  semantic_threshold: 0.7
```

Or use environment variables:

```bash
export OBSIDIAN_VAULT_PATH=~/Documents/MyVault
export OBSIDIAN_DB_PATH=~/.local/share/obsidian-agent/vault.db
```

## CLI Commands

### `index`
Index all notes in the vault.

```bash
obsidian-agent index [OPTIONS]

Options:
  --vault PATH          Path to Obsidian vault [required]
  --incremental         Only index changed files
  --force              Force re-index all files
  --embeddings         Generate embeddings (slower)
```

### `search`
Search the indexed vault.

```bash
obsidian-agent search QUERY [OPTIONS]

Options:
  --limit INTEGER       Number of results (default: 10)
  --semantic/--keyword  Search type (default: semantic)
  --threshold FLOAT     Similarity threshold (0-1)
```

### `stats`
Show vault statistics.

```bash
obsidian-agent stats

Displays:
  - Total notes
  - Total words
  - Average note length
  - Most common tags
  - Link statistics
  - Recent activity
```

### `serve`
Start API server (requires fastapi extra).

```bash
obsidian-agent serve [OPTIONS]

Options:
  --host TEXT    Host to bind to (default: 127.0.0.1)
  --port INTEGER Port to bind to (default: 8000)
  --reload      Enable auto-reload
```

### `export`
Export data in various formats.

```bash
obsidian-agent export [OPTIONS]

Options:
  --format [json|csv|markdown]  Output format
  --output PATH                  Output file
```

## API Endpoints

When running the API server:

### `POST /search`
```json
{
  "query": "machine learning",
  "limit": 10,
  "semantic": true
}
```

### `GET /stats`
Returns vault statistics.

### `POST /index`
Trigger re-indexing.

### `GET /notes/{note_id}`
Get note details.

## Development

### Setup Development Environment

```bash
# Install with dev dependencies
poetry install --with dev

# Activate virtual environment
poetry shell
```

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov

# Specific test
pytest tests/test_indexing.py -v
```

### Code Quality

```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Linting
ruff src/ tests/
```

## Architecture

```
src/obsidian_agent/
├── cli.py              # CLI interface (Typer)
├── config.py           # Configuration (Pydantic)
├── database/           # SQLite database layer
│   ├── models.py       # SQLAlchemy models
│   ├── connection.py   # Connection management
│   └── migrations/     # Alembic migrations
├── indexing/           # Document indexing
│   ├── indexer.py      # Main indexer
│   └── parser.py       # Markdown parser
├── vector_store/       # Vector embeddings
│   ├── chromadb_store.py
│   └── embeddings.py   # Embedding generation
├── search/             # Search functionality
│   ├── semantic.py     # Semantic search
│   └── keyword.py      # Keyword search
└── api/               # FastAPI server
    └── server.py
```

## Performance

- **Indexing Speed**: ~100-500 notes/second (without embeddings)
- **With Embeddings**: ~10-50 notes/second (depends on GPU)
- **Search Speed**: <100ms for most queries
- **Memory Usage**: ~500MB base + ~1MB per 1000 notes

## Troubleshooting

### ImportError: chromadb

```bash
pip install chromadb==0.4.24
```

### SQLite version too old

ChromaDB requires SQLite 3.35+. Update SQLite or use system packages.

### Embedding generation is slow

Use GPU acceleration:
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

### Memory issues

Reduce batch size in config:
```yaml
indexing:
  batch_size: 10  # Default: 100
```

## Integration with TypeScript Plugin

The TypeScript plugin can call the Python backend via:

1. **CLI Commands** - Execute via Node.js `child_process`
2. **API Server** - HTTP requests to localhost
3. **Shared Database** - Direct SQLite access

Example from TypeScript:
```typescript
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

async function searchVault(query: string): Promise<string> {
  const { stdout } = await execAsync(
    `obsidian-agent search "${query}" --limit 5`
  );
  return stdout;
}
```

## License

MIT - See LICENSE file for details
