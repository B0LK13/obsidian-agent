# PKM Agent

AI-enhanced Personal Knowledge Management agent with production-grade security, performance optimization, and comprehensive audit capabilities.

## Features

### Core Capabilities
- **TUI Interface**: Rich terminal UI for interacting with your knowledge base
- **Advanced RAG Pipeline**: FAISS HNSW vector search with multi-level caching
- **MCP Server**: Model Context Protocol server for IDE integration
- **Multi-LLM Support**: OpenAI, Ollama, and Anthropic providers
- **Real-time Sync**: WebSocket-based synchronization with Obsidian
- **ReAct Agent**: Autonomous reasoning with tool use for complex workflows

### Security & Governance (Phase 3)
- **Prompt Injection Protection**: 13-pattern detection system blocks malicious inputs
- **Path Traversal Defense**: Allowlist-based file system protection
- **Secrets Redaction**: Automatic sanitization of API keys, tokens, and passwords in logs
- **Input Validation**: Length limits and encoding normalization
- **Audit Trail**: Immutable operation log with SHA256 hash chain verification
- **Rollback Support**: Restore any operation with checksum validation

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

# Run autonomous research
pkma research "machine learning best practices"

# Search with caching
pkma search "deep learning"
```

## Performance

**Benchmark Results** (Windows 11, 16-core, 64GB RAM):

| Vault Size | Notes | Indexing | Search p95 | Cache Hit Rate |
|------------|-------|----------|------------|----------------|
| Small      | 10    | ~5s      | <50ms      | 73%            |
| Medium     | 100   | ~45s     | <100ms     | 75%            |
| Large      | 1000  | ~120s    | <200ms     | 78%            |

**Performance Features:**
- ✅ FAISS HNSW vector index (10-20x faster than flat search)
- ✅ Multi-level caching (memory + disk)
- ✅ Intelligent embedding cache (reduces API calls by 70%+)
- ✅ Adaptive index selection based on vault size

**Run benchmarks:**
```bash
python scripts/benchmark.py
```

## Security

### Security Controls

| Control | Status | Details |
|---------|--------|---------|
| **Prompt Injection Detection** | ✅ Active | 13 regex patterns block malicious inputs |
| **Path Traversal Protection** | ✅ Active | Allowlist enforcement prevents directory escapes |
| **Secrets Redaction** | ✅ Active | Automatic sanitization in logs (6 pattern types) |
| **Input Validation** | ✅ Active | Length limits + encoding normalization |

### Protected Operations

All user inputs are automatically sanitized:
- Search queries → Validated before processing
- Research topics → Checked for injection patterns  
- File paths → Restricted to allowed directories
- Audit logs → Secrets automatically redacted

### Security Architecture

```
User Input → Sanitization → Validation → Processing → Redacted Logging
              ↓                ↓            ↓             ↓
         Block injection   Check length   Enforce      Remove secrets
         patterns          limits         allowlist    before audit
```

**See:** `src/pkm_agent/security.py` for implementation.

## Testing

Comprehensive test suite with 43+ tests covering security, integration, and regression.

```bash
# Run all tests
pytest -v

# Security tests
pytest tests/test_security.py -v

# E2E integration tests
pytest tests/e2e/ -v

# With coverage
pytest --cov=src/pkm_agent --cov-report=html

# Automated validation (12 quality gates)
.\scripts\release_signoff.ps1
```

### Test Coverage

| Suite | Tests | Purpose |
|-------|-------|---------|
| Security | 21 | Injection, traversal, redaction |
| E2E Pipeline | 8 | Integration, caching, errors |
| Rollback Integrity | 7 | Audit chain, checksums |
| Security Regression | 7 | Control enforcement |
| **Total** | **43+** | **>80% coverage** |

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
├── agentzero/          # Agent orchestration
├── api/                # REST API routes
├── data/               # Database and indexing
├── llm/                # LLM providers
├── observability/      # Metrics and monitoring
├── plugins/            # Plugin system
├── rag/                # RAG pipeline with FAISS HNSW
├── tools/              # Utility tools
├── app.py              # Main application
├── app_enhanced.py     # Phase 1-3 optimizations integrated
├── audit_logger.py     # Immutable operation log
├── cache_manager.py    # Multi-level caching
├── cli.py              # CLI interface
├── cli_enhanced.py     # Enhanced CLI with new commands
├── config.py           # Configuration
├── mcp_server.py       # MCP server
├── react_agent.py      # ReAct autonomous agent
├── security.py         # Security controls (Phase 3)
├── studio.py           # Studio interface
└── tui.py              # Terminal UI
```

## Quality Gates

Automated quality gates run on every commit via GitHub Actions.

### CI/CD Pipeline

```yaml
Jobs:
  - test: Linting (ruff) + Type checks (mypy) + Unit tests
  - e2e: End-to-end integration tests
  - security: Security validation tests
  - benchmark: Performance smoke test
```

### Running Gates Locally

```bash
# Automated validation (all gates)
.\scripts\release_signoff.ps1

# Or manually:
ruff check src/ tests/ scripts/
mypy src/
pytest -v
pip-audit
python scripts/benchmark.py
```

### Release Criteria

All gates must pass:
- ✅ Linting clean (0 errors)
- ✅ Type checking clean (0 errors)
- ✅ All tests passing (43+ tests)
- ✅ Security regression passing
- ✅ No critical vulnerabilities
- ✅ Benchmark artifacts generated

## Audit & Rollback

Every mutable operation is logged with rollback capability.

### Audit Trail

```python
# View recent operations
await app.audit_logger.get_recent(limit=10)

# Get statistics
stats = await app.audit_logger.get_stats()

# Verify integrity
is_valid = await app.audit_logger.verify_integrity()
```

### Rollback Operations

```python
# Rollback specific operation
await app.rollback_operation(operation_id)
```

**Features:**
- Immutable append-only log (SQLite WAL mode)
- SHA256 hash chain verification
- Automatic metadata redaction
- Concurrent operation support

## Development

### Setup

```bash
# Clone repository
git clone <repo-url>
cd project_obsidian_agent/apps/pkm-agent

# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate   # Linux/Mac

# Install dependencies
pip install -e ".[dev]"

# Initialize
python -m pkm_agent init
```

### Development Workflow

```bash
# Run linters
ruff check src/
ruff format src/

# Type checking
mypy src/

# Run tests
pytest -v

# Coverage
pytest --cov=src/pkm_agent --cov-report=html
```

## Documentation

- **[PHASE3_QUICKSTART.md](PHASE3_QUICKSTART.md)** - Quick reference guide
- **[SECURITY_INTEGRATION_COMPLETE.md](SECURITY_INTEGRATION_COMPLETE.md)** - Security details
- **[GO_LIVE_CHECKLIST.md](GO_LIVE_CHECKLIST.md)** - Release validation steps
- **[docs/benchmarks.md](docs/benchmarks.md)** - Detailed performance metrics

## License

MIT
