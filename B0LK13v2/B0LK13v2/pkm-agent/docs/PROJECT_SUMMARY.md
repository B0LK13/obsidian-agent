# Project Summary

## Overview
- **PKM Agent**: Indexes markdown/frontmatter into SQLite; chunking + embeddings; Chroma vector store; hybrid retrieval; streaming LLM chat (OpenAI/Ollama); CLI + TUI; conversation history; stats; audit logging.
- **Audit Logging**: `audit_logs` table and `log_action` helper; logs commands, indexer runs/sync, vectorstore add/search/delete, chat messages. CLI command `pkm-agent audit [--category --action --limit --json]` to inspect.
- **UI Artifacts**: TUI (chat/search/stats panels). Web UI mock at `docs/web-preview.html` showing search, chat, stats, audit, config panels.
- **Documentation**: PRD at `docs/PRD.md`; coding-agent master prompt at `docs/coding_agent_prompt.md`; README and build guides; `.env.example`; build scripts for Win/Unix.
- **Tests**: Suite covers data models, DB, indexer, RAG, integration (async, marked slow). Run with `pytest -v`. Lint/type: `ruff check`, `mypy src/`.
- **Dependencies**: Install via `pip install -e ".[dev]"` (click, chromadb, openai, sentence-transformers, etc.); LSP missing-import warnings clear after install.

## Key Files
- `src/pkm_agent/app.py`, `cli.py`, `tui.py`
- `src/pkm_agent/data/*` (models, database, indexer, audit)
- `src/pkm_agent/llm/*` (base, openai, ollama)
- `src/pkm_agent/rag/*` (chunker, embeddings, vectorstore, retriever)
- `docs/PRD.md`, `docs/coding_agent_prompt.md`, `docs/web-preview.html`, `docs/PROJECT_SUMMARY.md`

## Usage
- Index: `pkm-agent index`
- Search: `pkm-agent search "query" [--area --tag --json]`
- Chat: `pkm-agent ask "question"` (context on by default)
- TUI: `pkm-agent tui`
- Stats: `pkm-agent stats`
- Audit: `pkm-agent audit [--category --action --limit --json]`

## Testing
- Run after installing deps: `pytest -v`
- Lint/type: `ruff check`, `mypy src/`
