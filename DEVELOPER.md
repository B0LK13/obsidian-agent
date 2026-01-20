# Obsidian Agent - Developer Guide

## Architecture Overview

Obsidian Agent is built with a hybrid architecture:

1. **TypeScript Plugin** - Runs in Obsidian, provides UI and AI integration
2. **Python Backend** (Optional) - Provides advanced features like RAG, vector search, and indexing

## TypeScript Plugin Architecture

### Core Components

#### Error Handling (`errorHandler.ts`)
Comprehensive error handling system with:
- **Error Categorization**: Network, API, File System, Validation, Configuration
- **Severity Levels**: Low, Medium, High, Critical
- **User-Friendly Messages**: Automatic translation of technical errors
- **Rate Limiting**: Prevents notification spam
- **Recovery Mechanisms**: Automatic retry and fallback strategies

```typescript
// Example usage
try {
  await someOperation();
} catch (error) {
  errorHandler.handle(error, {
    operation: 'operationName',
    category: ErrorCategory.API,
    severity: ErrorSeverity.HIGH
  });
}

// With recovery
const result = await errorHandler.withRecovery(
  'primaryOperation',
  () => primaryFunction(),
  () => fallbackFunction()
);
```

#### Logging System (`logger.ts`)
Structured logging with filtering and statistics:
- **Log Levels**: DEBUG, INFO, WARN, ERROR
- **Contextual Logging**: Attach metadata to log entries
- **Operation Tracking**: Measure operation duration
- **Statistics**: Track error rates and log counts
- **Export**: Export logs as JSON or text

```typescript
// Create logger
const logger = new Logger({
  level: LogLevel.INFO,
  enableConsole: true,
  maxLogEntries: 1000
});

// Use operation logger for tracking
const opLogger = logger.createChildLogger('myOperation');
opLogger.info('Starting operation');
// ... do work ...
opLogger.complete(true); // Logs duration automatically

// Get statistics
const stats = logger.getStats();
console.log(`Total errors: ${stats.recentErrors}`);
```

#### AI Service (`aiService.ts`)
Handles all AI API interactions:
- **Multi-Provider Support**: OpenAI, Anthropic, Ollama, Custom
- **Response Caching**: Automatic caching with configurable TTL
- **Retry Logic**: Exponential backoff for transient failures
- **Streaming Support**: Server-sent events for real-time responses
- **Token Tracking**: Monitor usage and costs

```typescript
const aiService = new AIService(settings, logger, errorHandler);

// Generate completion
const result = await aiService.generateCompletion(
  'Summarize this text',
  context,
  false // streaming
);

// With streaming
const result = await aiService.generateCompletion(
  'Write a story',
  context,
  true, // streaming
  (chunk) => {
    console.log('Received:', chunk.content);
  }
);
```

#### Context Provider (`contextProvider.ts`)
Gathers context from vault for AI requests:
- Linked notes
- Backlinks
- Tags
- Folder context
- Configurable depth and token limits

#### Cache Service (`cacheService.ts`)
Response caching to reduce API calls:
- Content-based hashing
- TTL management
- LRU eviction
- Statistics tracking

### Plugin Lifecycle

```typescript
export default class ObsidianAgentPlugin extends Plugin {
  async onload() {
    // 1. Load settings
    await this.loadSettings();
    
    // 2. Initialize logger and error handler
    this.logger = new Logger();
    this.errorHandler = new ErrorHandler(this.logger);
    
    // 3. Initialize services
    this.aiService = new AIService(settings, logger, errorHandler);
    this.contextProvider = new ContextProvider(this.app);
    
    // 4. Register commands
    this.addCommand({ /* ... */ });
    
    // 5. Add settings tab
    this.addSettingTab(new ObsidianAgentSettingTab(this.app, this));
  }

  onunload() {
    // Cleanup
  }
}
```

## Python Backend Architecture

### Overview

The Python backend provides advanced features that are CPU-intensive or require specialized libraries:
- Full-text indexing
- Vector embeddings
- Semantic search
- Document analysis
- Batch processing

### Directory Structure

```
python_backend/
├── pyproject.toml           # Dependencies (Poetry)
├── README.md
├── src/
│   └── obsidian_agent/
│       ├── __init__.py
│       ├── cli.py           # CLI interface (Typer)
│       ├── config.py        # Configuration (Pydantic)
│       ├── database/        # SQLite database
│       │   ├── __init__.py
│       │   ├── models.py
│       │   ├── connection.py
│       │   └── migrations/
│       ├── indexing/        # Document indexing
│       │   ├── __init__.py
│       │   ├── indexer.py
│       │   └── parser.py
│       ├── vector_store/    # Vector embeddings
│       │   ├── __init__.py
│       │   ├── chromadb_store.py
│       │   └── embeddings.py
│       ├── search/          # Search functionality
│       │   ├── __init__.py
│       │   ├── semantic.py
│       │   └── keyword.py
│       └── api/            # Optional API server
│           ├── __init__.py
│           └── server.py
├── tests/
│   ├── __init__.py
│   ├── test_indexing.py
│   ├── test_search.py
│   └── test_vector_store.py
└── scripts/
    ├── setup.sh
    └── migrate.py
```

### Configuration System

Uses Pydantic for type-safe configuration:

```python
# config.py
from pydantic import BaseSettings, Field
from pathlib import Path

class VaultConfig(BaseSettings):
    path: Path
    exclude_folders: list[str] = ['.obsidian', 'templates']

class DatabaseConfig(BaseSettings):
    path: Path = Path('./obsidian_agent.db')
    backup_enabled: bool = True
    backup_interval_hours: int = 24

class VectorStoreConfig(BaseSettings):
    provider: str = 'chromadb'
    embedding_model: str = 'all-MiniLM-L6-v2'
    collection_name: str = 'obsidian_notes'

class ObsidianAgentConfig(BaseSettings):
    vault: VaultConfig
    database: DatabaseConfig
    vector_store: VectorStoreConfig
    
    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'
```

### Database Schema

SQLite with FTS5 for full-text search:

```sql
-- Notes table
CREATE TABLE IF NOT EXISTS notes (
    id TEXT PRIMARY KEY,
    path TEXT NOT NULL UNIQUE,
    title TEXT,
    content TEXT,
    created_at REAL,
    modified_at REAL,
    indexed_at REAL,
    checksum TEXT,
    metadata JSON
);

CREATE INDEX idx_notes_path ON notes(path);
CREATE INDEX idx_notes_modified ON notes(modified_at);

-- Full-text search
CREATE VIRTUAL TABLE notes_fts USING fts5(
    title, content,
    content='notes',
    content_rowid='rowid'
);

-- Links table
CREATE TABLE IF NOT EXISTS links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_note_id TEXT NOT NULL,
    target_note_id TEXT NOT NULL,
    link_type TEXT, -- 'internal', 'external', 'embed'
    FOREIGN KEY (source_note_id) REFERENCES notes(id),
    FOREIGN KEY (target_note_id) REFERENCES notes(id)
);

-- Tags table
CREATE TABLE IF NOT EXISTS tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    note_id TEXT NOT NULL,
    tag TEXT NOT NULL,
    FOREIGN KEY (note_id) REFERENCES notes(id)
);
```

### CLI Interface

```python
# cli.py
import typer
from pathlib import Path
from .config import ObsidianAgentConfig
from .indexing import Indexer
from .search import SemanticSearch

app = typer.Typer()

@app.command()
def index(vault_path: Path = typer.Option(..., help="Path to Obsidian vault")):
    """Index all notes in the vault."""
    config = ObsidianAgentConfig(vault={"path": vault_path})
    indexer = Indexer(config)
    indexer.index_vault()
    typer.echo("✅ Indexing complete")

@app.command()
def search(
    query: str,
    limit: int = typer.Option(10, help="Number of results"),
    semantic: bool = typer.Option(True, help="Use semantic search")
):
    """Search the indexed vault."""
    config = ObsidianAgentConfig()
    searcher = SemanticSearch(config)
    results = searcher.search(query, limit=limit)
    
    for i, result in enumerate(results, 1):
        typer.echo(f"{i}. {result.title} (score: {result.score:.2f})")

@app.command()
def stats():
    """Show vault statistics."""
    # Implementation
    pass

if __name__ == "__main__":
    app()
```

## Development Workflow

### TypeScript Development

```bash
# Install dependencies
npm install

# Development build with watch
npm run dev

# Production build
npm run build

# Type checking
npm run build  # Runs tsc -noEmit first
```

### Python Development

```bash
# Create virtual environment
cd python_backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install with Poetry
poetry install

# Or with pip
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Format code
black src/
isort src/
```

### Testing

#### TypeScript
Currently manual testing in Obsidian. Future: Add Jest or Vitest.

#### Python
```bash
# Run all tests
pytest

# With coverage
pytest --cov=obsidian_agent --cov-report=html

# Specific test
pytest tests/test_indexing.py -v
```

## Building for Release

### TypeScript Plugin

```bash
npm run build
# Creates: main.js, manifest.json, styles.css
```

### Python Backend

```bash
# Build distributable
poetry build
# Creates: dist/obsidian_agent-*.whl

# Or with setuptools
python -m build
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Ensure all tests pass
5. Update documentation
6. Submit pull request

## Debugging

### TypeScript
Use Obsidian Developer Console (Ctrl+Shift+I):
```typescript
console.log('Debug info:', value);
```

Logs are also captured by the Logger system:
```typescript
logger.debug('Debug message', { context: 'value' });
```

### Python
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug('Debug message')
```

## Performance Considerations

- **Caching**: Use CacheService to reduce API calls
- **Debouncing**: Delay rapid requests in inline completion
- **Lazy Loading**: Load data only when needed
- **Batch Operations**: Process multiple items together
- **Connection Pooling**: Reuse database connections

## Security

- API keys stored in Obsidian's data.json (encrypted by Obsidian)
- No data sent to third parties except chosen AI provider
- Python backend runs locally, no external connections
- Validate all user inputs

## Troubleshooting

See the main README.md for common issues and solutions.
