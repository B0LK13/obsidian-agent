# PKM Agent Product Requirements Document (PRD)

## 1. Goal
Deliver an AI-enhanced Personal Knowledge Management (PKM) agent that indexes markdown notes, supports hybrid search (keyword + semantic), and provides conversational/RAG assistance via CLI and TUI. Include full audit logging of user commands and internal indexing/vector operations.

## 2. Personas
- **Power Note-Taker**: Uses Obsidian/Markdown vault, wants fast search and chat over notes.
- **Researcher/Engineer**: Needs semantic retrieval, citations, and conversation history.
- **CLI/TUI User**: Prefers terminal workflows, needs quick commands and a rich TUI.

## 3. Scope
- **In Scope**: Indexing markdown notes, metadata/frontmatter parsing, SQLite storage, Chroma vector store, hybrid retrieval, OpenAI/Ollama LLMs, CLI + TUI, audit logging, basic stats, conversation history, tests.
- **Out of Scope (current phase)**: Web UI, multi-user auth, cloud sync, advanced summarization, scheduling/cron, mobile.

## 4. Functional Requirements
1) **Configuration**
   - Pydantic settings; env + .env support; defaults for paths/models.

2) **Data & Indexing**
   - Parse markdown with frontmatter; extract title/metadata.
   - Store notes, tags, links in SQLite; maintain counts and word totals.
   - File indexer with ignore patterns; full and incremental sync.
   - Chunking with size/overlap and markdown-awareness.

3) **Embeddings & Vector Store**
   - Sentence-transformers local embeddings (default all-MiniLM-L6-v2).
   - Optional OpenAI embeddings (future toggle).
   - ChromaDB persistent store; add/search/delete per note.

4) **Retrieval**
   - Hybrid search (semantic + keyword) with reciprocal rank fusion and scoring threshold.
   - Filters by note_id, area, tags (string contains for tags).
   - Context builder for RAG with token/char budgeting.

5) **LLM**
   - Providers: OpenAI, Ollama.
   - Streaming responses; tool-call ready interface (Message/ToolCall types).
   - Configurable temperature/max_tokens; model name per provider.

6) **CLI**
   - Commands: `index`, `search`, `ask`, `tui`, `stats`, `conversations`.
   - Options: filters (area/tag), no-index flag, prompt injection for TUI, JSON output for search.

7) **TUI**
   - Panels: Chat (streaming), Search (results list), Stats (db/vector/llm info).
   - Keyboard: quit, focus next/prev; supports initial prompt.

8) **Audit Logging** (new)
   - Persist audit events to SQLite `audit_logs` with category/action/metadata/timestamp.
   - Log user commands (initialize, index start/complete, search, chat user/assistant) and internal operations.

9) **Conversation History**
   - Store messages with role/content/timestamps; list conversations; retrieve history; stats on counts.

10) **Stats**
    - Notes/tags/links/word totals; vector store counts; LLM config info.

## 5. Non-Functional Requirements
- Python 3.11+, asyncio-friendly design.
- Local-first; no external services required beyond chosen LLM.
- Performance: index typical vaults efficiently; embeddings batch per note.
- Observability: logging via standard logging + audit table.
- Test coverage: unit + integration; slow markers for model/vector operations.

## 6. Success Metrics
- Index throughput: completes typical vault (<5k notes) without errors.
- Search latency: sub-second keyword; acceptable semantic given model.
- Chat reliability: successful streaming responses with context.
- Zero unhandled exceptions in CLI/TUI flows during smoke tests.

## 7. Risks & Mitigations
- **Model downloads**: first-run latency/size → document and cache dir.
- **Chroma availability**: optional; handle ImportError gracefully.
- **API keys**: environment-driven; avoid hardcoding.
- **Large vaults**: batching and chunking; configurable limits.

## 8. Milestones
- M1: Core data + indexing + embeddings + vector store.
- M2: Hybrid retrieval + CLI + TUI.
- M3: LLM providers + streaming chat.
- M4: Audit logging + stats + conversations.
- M5: Testing, docs, build scripts.

## 9. Decisions (Past & Pending)
- **Provider choice**: OpenAI + Ollama supported; Anthropic deferred.
- **Embeddings**: Sentence-transformers local default; OpenAI optional later.
- **Vector store**: ChromaDB persistent client with cosine space.
- **Chunking**: Markdown-aware with overlap; min chunk size enforced.
- **Hybrid retrieval**: RRF fusion semantic/keyword; filters by area/tags.
- **Config**: Pydantic settings with env prefix `PKMA_` and nested delimiters.
- **CLI/TUI**: Click-based CLI; Textual TUI with chat/search/stats.
- **Audit logging**: SQLite `audit_logs` for commands/ops (implemented).
- **Testing**: Pytest with async support; slow markers for model/vector ops.

## 10. Open Questions / Future Decisions
- Add reranking (e.g., cross-encoder) for top-k results?
- Add OpenAI embeddings toggle in config and vector pipeline?
- Add note-level delete/update hooks to vector store.
- Add export/import of audit logs.
- Add web UI or API layer.
