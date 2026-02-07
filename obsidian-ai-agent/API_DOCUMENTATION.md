# Obsidian AI Agent - API Documentation

> **Version**: 1.0.0  
> **Date**: 2026-01-30

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Core API](#core-api)
3. [Incremental Indexing](#incremental-indexing)
4. [Vector Database](#vector-database)
5. [Caching Layer](#caching-layer)
6. [Link Management](#link-management)
7. [Error Handling](#error-handling)
8. [Link Suggestions](#link-suggestions)
9. [Configuration](#configuration)
10. [Performance Benchmarks](#performance-benchmarks)

---

## Quick Start

```python
from obsidian_agent_core import create_agent

# Initialize agent
agent = create_agent(
    vault_path="/path/to/your/vault",
    data_dir="./agent_data"
)

# Index your vault
agent.index_vault()

# Search your notes
results = agent.search_notes("machine learning", top_k=5)

# Get system status
status = agent.get_status()
print(f"Healthy: {status.healthy}")
```

---

## Core API

### `ObsidianAgentCore`

Main integration class that wires all components together.

#### Constructor

```python
from obsidian_agent_core import ObsidianAgentCore, AgentConfig

config = AgentConfig(
    vault_path="/path/to/vault",
    data_dir="./agent_data",
    enable_incremental_indexing=True,
    vector_db_backend="auto",  # auto, chroma, sqlite
    cache_memory_size=1000,
    enable_link_management=True,
    enable_suggestions=True
)

agent = ObsidianAgentCore(config)
agent.initialize()
```

#### Methods

##### `index_vault(force_full=False) -> Optional[ChangeReport]`

Index the vault using incremental or full indexing.

**Parameters:**
- `force_full` (bool): Force full reindex even if incremental is enabled

**Returns:**
- `ChangeReport` with indexing statistics

**Example:**
```python
# Incremental update
report = agent.index_vault()
print(f"Indexed {report.change_count} changes in {report.duration_ms:.1f}ms")

# Force full reindex
report = agent.index_vault(force_full=True)
```

##### `search_notes(query, top_k=5, use_cache=True) -> List[SearchResult]`

Search notes using semantic similarity.

**Parameters:**
- `query` (str): Search query
- `top_k` (int): Number of results to return
- `use_cache` (bool): Use result caching

**Returns:**
- List of `SearchResult` objects

**Example:**
```python
results = agent.search_notes("artificial intelligence", top_k=10)
for result in results:
    print(f"{result.note_id}: {result.score:.3f}")
```

##### `scan_links() -> Optional[LinkReport]`

Scan vault for broken and orphan links.

**Returns:**
- `LinkReport` with link analysis

**Example:**
```python
report = agent.scan_links()
print(f"Broken links: {len(report.broken_links)}")
print(f"Orphan notes: {len(report.orphan_notes)}")

for link in report.broken_links:
    print(f"  {link.source_note} -> {link.target}")
    print(f"    Suggestions: {link.suggestions}")
```

##### `get_link_suggestions(min_confidence=None) -> Optional[SuggestionReport]`

Generate link suggestions for the vault.

**Parameters:**
- `min_confidence` (float): Minimum confidence threshold (0.0-1.0)

**Returns:**
- `SuggestionReport` with suggestions categorized by confidence

**Example:**
```python
report = agent.get_link_suggestions(min_confidence=0.7)

print(f"High confidence: {len(report.high_confidence)}")
for suggestion in report.high_confidence[:5]:
    print(f"  {suggestion.source_note} -> {suggestion.suggested_note}")
    print(f"  Confidence: {suggestion.confidence:.2f}")
    print(f"  Reason: {suggestion.reason}")
```

##### `get_status() -> SystemStatus`

Get comprehensive system status.

**Returns:**
- `SystemStatus` with component health and statistics

**Example:**
```python
status = agent.get_status()
print(f"Healthy: {status.healthy}")
print(f"Components: {status.components}")
print(f"Notes indexed: {status.index_stats.get('total_notes')}")
print(f"Cache hit rate: {status.cache_stats.get('hit_rate', 0):.1%}")
```

##### `shutdown()`

Gracefully shutdown all components.

**Example:**
```python
agent.shutdown()
```

---

## Incremental Indexing

### `IncrementalIndexer`

Provides efficient vault indexing with change detection.

```python
from incremental_indexer import IncrementalIndexer

indexer = IncrementalIndexer(
    vault_path="/path/to/vault",
    state_db_path="index_state.db",
    embedding_callback=None  # Optional callback for embeddings
)

# Detect changes without indexing
report = indexer.detect_changes()
print(f"Changes: {report.change_count}")

# Index only changes
report = indexer.index_changes()

# Full reindex
report = indexer.full_reindex()

# Get stats
stats = indexer.get_index_stats()
print(f"Total notes: {stats['total_notes']}")
print(f"Last index: {stats['last_incremental_index']}")
```

---

## Vector Database

### `VectorDatabase`

Semantic search using vector embeddings.

```python
from vector_database import VectorDatabase, create_embedding_function

# Create embedding function
embed_fn = create_embedding_function("sentence-transformers/all-MiniLM-L6-v2")

# Initialize database
db = VectorDatabase(
    backend="auto",  # auto, chroma, sqlite
    persist_dir="./vector_db",
    embedding_function=embed_fn
)

# Add note
db.add_note(
    note_id="ai/overview.md",
    content="Artificial Intelligence is...",
    metadata={"category": "ai", "tags": ["ml", "dl"]}
)

# Batch add
notes = [
    ("note1.md", "Content 1", {"tag": "a"}),
    ("note2.md", "Content 2", {"tag": "b"}),
]
success_count, fail_count = db.add_notes_batch(notes)

# Search
results = db.search("machine learning", top_k=5)
for result in results:
    print(f"{result.note_id}: {result.score:.3f}")

# Search with filters
results = db.search(
    "neural networks",
    top_k=5,
    filters={"category": "ai"}
)

# Delete note
db.delete_note("note1.md")

# Get stats
stats = db.get_stats()
print(f"Total notes: {stats['total_notes']}")
```

---

## Caching Layer

### `CacheManager`

Two-tier caching with memory (L1) and disk (L2) layers.

```python
from caching_layer import CacheManager, LLMResponseCache, EmbeddingCache

# Initialize cache
cache = CacheManager(
    memory_cache_size=1000,
    memory_cache_mb=50.0,
    disk_cache_path="cache.db",
    default_ttl_seconds=3600
)

# Basic operations
cache.set("namespace", "key", "value", ttl_seconds=1800)
hit, value = cache.get("namespace", "key")

# Specialized caches
llm_cache = LLMResponseCache(cache)
llm_cache.set(prompt, model, response, temperature=0.7)
hit, response = llm_cache.get(prompt, model, temperature=0.7)

emb_cache = EmbeddingCache(cache)
emb_cache.set(text, model, embedding)
hit, embedding = emb_cache.get(text, model)

# Cache decorator
from caching_layer import cached

@cached(cache, namespace="api", ttl_seconds=3600)
def fetch_data(param):
    return expensive_operation(param)

# Stats
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.1%}")
print(f"Total entries: {stats['total_entries']}")
```

---

## Link Management

### `LinkManager`

Dead link detection and repair.

```python
from link_manager import LinkManager

manager = LinkManager(
    vault_path="/path/to/vault",
    db_path="links.db"
)

# Scan vault
report = manager.scan_vault()
print(f"Total links: {report.total_links}")
print(f"Broken: {len(report.broken_links)}")
print(f"Orphans: {len(report.orphan_notes)}")

# View broken links
for link in report.broken_links:
    print(f"{link.source_note}:{link.line_number} -> {link.target}")
    print(f"  Context: {link.context}")
    print(f"  Suggestions: {link.suggestions}")

# Repair a link
if report.broken_links:
    link = report.broken_links[0]
    if link.suggestions:
        success = manager.repair_link(link, link.suggestions[0])
        print(f"Repair {'successful' if success else 'failed'}")

# Export report
manager.export_report(report, "link_report.json")
```

---

## Error Handling

### Error Handler

```python
from error_handling import ErrorHandler, ErrorCategory, ErrorSeverity

handler = ErrorHandler()

try:
    risky_operation()
except Exception as e:
    ctx = handler.handle(
        error=e,
        category=ErrorCategory.NETWORK,
        severity=ErrorSeverity.ERROR,
        component="MyComponent",
        operation="risky_operation",
        context={"user_id": 123}
    )

# Get stats
stats = handler.get_error_stats()
print(f"Total errors: {stats['total_errors']}")
print(f"By category: {stats['by_category']}")
```

### Circuit Breaker

```python
from error_handling import CircuitBreaker, with_circuit_breaker

# Manual usage
cb = CircuitBreaker(
    name="api_service",
    failure_threshold=5,
    recovery_timeout=60.0
)

if cb.can_execute():
    try:
        result = call_external_api()
        cb.record_success()
    except Exception:
        cb.record_failure()
else:
    print("Circuit is OPEN - service unavailable")

# Decorator usage
@with_circuit_breaker(cb)
def fetch_data():
    return requests.get(url)
```

### Retry Decorator

```python
from error_handling import with_retry

@with_retry(
    max_attempts=3,
    initial_delay=1.0,
    max_delay=60.0,
    retryable_exceptions=(ConnectionError, TimeoutError)
)
def unreliable_operation():
    # May fail intermittently
    return api.call()
```

### Validation

```python
from error_handling import Validator

# Various validators
Validator.not_none(value, "field_name")
Validator.not_empty(text, "username")
Validator.in_range(age, 0, 150, "age")
Validator.is_type(data, dict, "config")
Validator.valid_path("/path/to/file", must_exist=True)
Validator.one_of(value, ["a", "b", "c"], "option")
```

---

## Link Suggestions

### `SuggestionEngine`

```python
from link_suggester import SuggestionEngine

engine = SuggestionEngine(
    vault_path="/path/to/vault",
    db_path="suggestions.db"
)

# Analyze vault
report = engine.analyze_vault()

print(f"Total suggestions: {report.total_suggestions}")
print(f"High confidence: {len(report.high_confidence)}")

# View suggestions
for suggestion in report.high_confidence:
    print(f"{suggestion.source_note} -> {suggestion.suggested_note}")
    print(f"  Confidence: {suggestion.confidence:.2f}")
    print(f"  Reason: {suggestion.reason}")
    print(f"  Context: {suggestion.context}")

# Apply suggestion
if report.high_confidence:
    suggestion = report.high_confidence[0]
    success = engine.apply_suggestion(suggestion)

# Get suggestions for specific note
suggestions = engine.get_suggestions_for_note("my_note.md", min_confidence=0.7)

# Stats
stats = engine.get_stats()
print(f"Total: {stats['total_suggestions']}")
print(f"Applied: {stats['applied']}")
```

---

## Configuration

### `AgentConfig`

```python
from obsidian_agent_core import AgentConfig

config = AgentConfig(
    # Required
    vault_path="/path/to/vault",
    
    # Optional
    data_dir="./agent_data",
    
    # Indexing
    enable_incremental_indexing=True,
    index_state_db="index_state.db",
    
    # Vector DB
    vector_db_backend="auto",  # auto, chroma, sqlite
    vector_db_path="vector_db",
    embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    
    # Cache
    cache_memory_size=1000,
    cache_memory_mb=50.0,
    cache_disk_path="cache.db",
    cache_default_ttl=3600,
    
    # Links
    enable_link_management=True,
    links_db_path="links.db",
    
    # Suggestions
    enable_suggestions=True,
    suggestions_db_path="suggestions.db",
    suggestion_min_confidence=0.5,
    
    # Error handling
    enable_circuit_breaker=True,
    circuit_failure_threshold=5,
    retry_max_attempts=3
)

# Save config
config.save("agent_config.json")

# Load config
config = AgentConfig.from_file("agent_config.json")
```

---

## Performance Benchmarks

Typical performance on modern hardware:

| Operation | 100 Notes | 1,000 Notes | 10,000 Notes |
|-----------|-----------|-------------|--------------|
| **Full Index** | 1.1s | 5.9s | ~60s |
| **Incremental** | 19ms | 220ms | ~2s |
| **Single Change** | 47ms | 214ms | ~500ms |
| **Link Scan** | 3.0s | 24s | ~4min |
| **Suggestions** | 0.5s | 1.7s | ~20s |
| **Cache Hit** | 0.01ms | 0.01ms | 0.01ms |
| **Vector Search** | 10ms | 50ms | ~200ms |

*Note: Actual performance depends on hardware, note size, and complexity.*

---

## Error Codes

### Error Categories

| Category | Description |
|----------|-------------|
| `NETWORK` | Network-related errors |
| `FILE_IO` | File system errors |
| `DATABASE` | Database errors |
| `VALIDATION` | Input validation errors |
| `TIMEOUT` | Timeout errors |
| `RESOURCE` | Resource exhaustion |
| `UNKNOWN` | Uncategorized errors |

### Error Severities

| Severity | Description |
|----------|-------------|
| `DEBUG` | Debug information |
| `INFO` | Informational |
| `WARNING` | Warning |
| `ERROR` | Error (recoverable) |
| `CRITICAL` | Critical (may crash) |

---

## Examples

### Complete Workflow

```python
from obsidian_agent_core import create_agent

# Initialize
agent = create_agent("/path/to/vault")

# Initial setup
print("Indexing vault...")
report = agent.index_vault()
print(f"Indexed {report.total_scanned} notes")

# Daily workflow
print("\nScanning links...")
link_report = agent.scan_links()
if link_report.broken_links:
    print(f"Found {len(link_report.broken_links)} broken links")

print("\nGenerating suggestions...")
sug_report = agent.get_link_suggestions()
if sug_report.high_confidence:
    print(f"Found {len(sug_report.high_confidence)} high-confidence suggestions")

# Search
print("\nSearching...")
results = agent.search_notes("project ideas", top_k=5)
for r in results:
    print(f"  {r.note_id}: {r.score:.3f}")

# Status
print("\nStatus:")
print(agent.get_stats_summary())

# Cleanup
agent.shutdown()
```

---

## Support

For issues and feature requests, please visit:
https://github.com/B0LK13/obsidian-agent/issues
