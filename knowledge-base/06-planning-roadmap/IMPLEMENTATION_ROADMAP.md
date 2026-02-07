# PKM-Agent Complete Implementation Roadmap

**Status**: In Progress  
**Start Date**: 2026-01-17  
**Estimated Completion**: 2026-03-17 (60 development days)

## Executive Summary

This document outlines the complete implementation plan for resolving all 15 identified issues in the PKM-Agent system. The work is organized into 4 phases over 3 months.

---

## Phase 1: Critical Infrastructure (Days 1-15)

### ✅ Completed

#### Issue #2: Custom Exception Hierarchy
- **File Created**: `src/pkm_agent/exceptions.py`
- **Status**: ✅ COMPLETE
- **Contents**:
  - Base exception classes (`PKMAgentError`, `RetriableError`, `Permanent Error`)
  - Domain-specific exceptions (Indexing, Search, LLM, Storage, Config, Network, Sync, Validation, Resource)
  - Context-aware error reporting
  - Structured logging support

### 🔄 In Progress

#### Issue #1: Incremental File System Indexing
**Files to Create**:
1. `src/pkm_agent/data/file_watcher.py` - File system watcher using watchdog
2. `src/pkm_agent/data/incremental_indexer.py` - Delta indexing logic

**Files to Modify**:
1. `src/pkm_agent/data/indexer.py` - Add watch mode and incremental methods
2. `src/pkm_agent/app.py` - Integrate file watcher
3. `src/pkm_agent/config.py` - Add watcher configuration

**Implementation Steps**:
```python
# 1. Install watchdog dependency
# Add to pyproject.toml: watchdog>=4.0.0

# 2. Create FileWatcher class
class FileWatcher:
    def __init__(self, pkm_root, on_change_callback):
        self.observer = Observer()
        self.handler = MarkdownFileHandler(on_change_callback)
    
    def start_watching(self):
        self.observer.schedule(self.handler, self.pkm_root, recursive=True)
        self.observer.start()

# 3. Modify FileIndexer to support incremental updates
class FileIndexer:
    def start_watch_mode(self):
        self.watcher = FileWatcher(self.pkm_root, self.on_file_changed)
        self.watcher.start()
    
    async def on_file_changed(self, filepath):
        # Only reindex changed file
        await self.index_file(filepath)
        # Update embeddings for this file only
        await self.update_file_embeddings(filepath)

# 4. Update PKMAgentApp initialization
class PKMAgentApp:
    async def initialize(self):
        # Start file watcher in background
        self.indexer.start_watch_mode()
        # Initial index (only new/modified files)
        await self.indexer.sync()  # Use sync instead of index_all
```

**Testing Checklist**:
- [ ] File creation detected within 1 second
- [ ] File modification triggers reindex
- [ ] File deletion removes from index
- [ ] Startup time <5s for 10k file vault
- [ ] Background watcher doesn't block operations
- [ ] Memory usage stable over 24 hours

**Estimated Completion**: Day 5

---

#### Issue #4: Bidirectional Real-Time Sync
**Dependency**: Requires Issue #1 to be complete

**Files to Create**:
1. `src/pkm_agent/sync/websocket_server.py` - WebSocket sync server
2. `src/pkm_agent/sync/sync_event.py` - Sync event models
3. `obsidian-pkm-agent/src/SyncClient.ts` - TypeScript WebSocket client

**Implementation Steps**:
```python
# 1. WebSocket Server
class SyncServer:
    def __init__(self, app, host="localhost", port=27125):
        self.app = app
        self.clients = set()
    
    async def start(self):
        async with websockets.serve(self.handle_client, self.host, self.port):
            await asyncio.Future()  # Run forever
    
    async def handle_client(self, websocket, path):
        self.clients.add(websocket)
        async for message in websocket:
            event = json.loads(message)
            await self.process_sync_event(event)
    
    async def broadcast_event(self, event):
        if self.clients:
            message = json.dumps(asdict(event))
            await asyncio.gather(*[c.send(message) for c in self.clients])

# 2. Integrate with FileWatcher
class FileIndexer:
    async def on_file_changed(self, filepath):
        # Index the file
        note = await self.index_file(filepath)
        
        # Broadcast sync event
        event = SyncEvent(
            event_type='file_modified',
            note_id=note.id,
            path=str(filepath),
            timestamp=time.time()
        )
        await self.sync_server.broadcast_event(event)
```

```typescript
// 3. TypeScript SyncClient
class SyncClient {
    private ws: WebSocket;
    
    connect(): void {
        this.ws = new WebSocket('ws://localhost:27125');
        
        this.ws.onmessage = (event) => {
            const syncEvent = JSON.parse(event.data);
            this.handleSyncEvent(syncEvent);
        };
    }
    
    sendEvent(event: SyncEvent): void {
        if (this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(event));
        }
    }
}

// 4. Integrate into Plugin
class PKMAgentPlugin extends Plugin {
    onload() {
        this.syncClient = new SyncClient();
        this.syncClient.connect();
        
        // Listen to vault events
        this.registerEvent(
            this.app.vault.on('modify', (file) => {
                this.syncClient.sendEvent({
                    event_type: 'file_modified',
                    path: file.path,
                    timestamp: Date.now()
                });
            })
        );
    }
}
```

**Testing Checklist**:
- [ ] WebSocket connection established on plugin load
- [ ] File changes in Obsidian → Python within 2s
- [ ] Python changes → Obsidian notification
- [ ] Auto-reconnect on disconnection
- [ ] No data loss during network issues
- [ ] Handle 100 events/minute without lag

**Estimated Completion**: Day 13

---

## Phase 2: Core Features (Days 16-30)

### Issue #3: Dead Link Detection and Auto-Healing

**Files to Create**:
1. `src/pkm_agent/tools/link_analyzer.py` - Link extraction and validation
2. `src/pkm_agent/tools/link_healer.py` - Auto-fix broken links
3. `src/pkm_agent/cli_commands/check_links.py` - CLI command

**Key Components**:
```python
class LinkExtractor:
    WIKI_LINK = r'\[\[([^\]|]+)(\|[^\]]+)?\]\]'
    MD_LINK = r'\[([^\]]+)\]\(([^\)]+)\)'
    
    def extract_links(self, content, source):
        # Extract all wiki and markdown links
        pass

class LinkValidator:
    def validate_link(self, link):
        if not self._link_exists(link.target):
            suggestions = self._find_similar(link.target)
            return BrokenLink(link, suggestions)
        return None
    
    def _find_similar(self, target):
        # Fuzzy match using fuzzywuzzy
        scores = [(path, fuzz.ratio(target, path)) for path in self.all_paths]
        return sorted(scores, key=lambda x: x[1], reverse=True)[:3]

class LinkHealer:
    async def scan_vault(self):
        broken_links = []
        for note in self.vault.get_all_notes():
            links = self.extractor.extract_links(note.content)
            for link in links:
                if broken := self.validator.validate_link(link):
                    broken_links.append(broken)
        return broken_links
    
    async def auto_fix(self, broken_links, confidence=0.8):
        for broken in broken_links:
            if broken.suggestions[0][1] >= confidence:
                await self.fix_link(broken)
```

**CLI Integration**:
```bash
# Commands to add
pkm-agent check-links                    # Scan for broken links
pkm-agent check-links --auto-fix          # Auto-fix high confidence
pkm-agent check-links --confidence 0.9   # Custom threshold
```

**Testing Checklist**:
- [ ] Detects all wiki and markdown links
- [ ] Identifies broken links accurately
- [ ] Suggestions >80% relevant
- [ ] Auto-fix applies correctly
- [ ] Supports undo operations
- [ ] Handles 1000+ links efficiently

**Estimated Completion**: Day 22

---

### Issue #5: Semantic Chunking Strategy

**Files to Create**:
1. `src/pkm_agent/rag/semantic_chunker.py` - Markdown-aware chunking

**Implementation**:
```python
class SemanticChunker:
    def chunk_note(self, note):
        # Parse markdown structure
        sections = self._parse_sections(note.content)
        
        chunks = []
        for section in sections:
            chunks.extend(self._chunk_section(section))
        
        return chunks
    
    def _parse_sections(self, content):
        # Identify headings, code blocks, lists, paragraphs
        sections = []
        
        # Use regex to find:
        # - Headings (# ## ###)
        # - Code blocks (```)
        # - Lists (- * + or 1.)
        # - Paragraphs (text blocks)
        
        return sections
    
    def _chunk_section(self, section):
        # Smart chunking that respects:
        # - Section boundaries
        # - Semantic units
        # - Size constraints
        
        if len(section) <= self.max_size:
            return [section]
        
        # Split by paragraphs
        paragraphs = section.split('\n\n')
        return self._combine_paragraphs(paragraphs)
```

**Benefits**:
- No split headings/code blocks
- Context preserved within chunks
- Better retrieval quality (+20%)
- Maintains document structure

**Testing Checklist**:
- [ ] Code blocks preserved
- [ ] Headings not split
- [ ] Lists kept together
- [ ] Average chunk size 300-600 chars
- [ ] Retrieval quality improved
- [ ] Migration script works

**Estimated Completion**: Day 27

---

### Issue #6: Rate Limiting and Cost Control

**Files to Create**:
1. `src/pkm_agent/llm/rate_limiter.py` - Token bucket implementation
2. `src/pkm_agent/llm/cost_tracker.py` - Usage and cost tracking

**Implementation**:
```python
class TokenBucket:
    def __init__(self, capacity, refill_rate):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
    
    async def consume(self, tokens):
        # Refill based on elapsed time
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

class RateLimitedLLMProvider:
    def __init__(self, provider, config):
        self.provider = provider
        self.request_bucket = TokenBucket(config.requests_per_minute, ...)
        self.token_bucket = TokenBucket(config.tokens_per_minute, ...)
        self.cost_tracker = CostTracker()
    
    async def generate(self, messages):
        # Check cost limit
        if self.cost_tracker.daily_cost >= self.config.daily_limit:
            raise CostLimitExceededError(...)
        
        # Wait for rate limit tokens
        await self.request_bucket.wait_for_tokens(1)
        await self.token_bucket.wait_for_tokens(estimated_tokens)
        
        # Execute
        response = await self.provider.generate(messages)
        
        # Track usage
        cost = self.cost_tracker.track_usage(model, input_tokens, output_tokens)
        
        return response
```

**Configuration**:
```python
# config.py additions
class RateLimitConfig:
    requests_per_minute: int = 60
    tokens_per_minute: int = 90000
    max_concurrent: int = 10
    daily_cost_limit: float = 10.0
```

**Testing Checklist**:
- [ ] Rate limiting prevents violations
- [ ] Cost tracking accurate
- [ ] Warnings at 80% limit
- [ ] Hard stops at 100%
- [ ] Usage dashboard works
- [ ] Export reports functional

**Estimated Completion**: Day 30

---

## Phase 3: Advanced Features (Days 31-45)

### Issue #7: Multi-Provider LLM Fallback

**Implementation**:
```python
class LLMProviderPool:
    def __init__(self, providers):
        self.providers = providers  # [openai, anthropic, ollama]
        self.health_status = {}
    
    async def generate_with_fallback(self, messages):
        for provider in self.providers:
            try:
                if not self.is_healthy(provider):
                    continue
                
                return await self.execute_with_retry(provider, messages)
            
            except RateLimitError:
                # Try next provider
                continue
            except Exception as e:
                self.mark_unhealthy(provider)
                continue
        
        raise AllProvidersFailedError()
```

---

### Issue #8: Graph Visualization

**Files to Create**:
1. `src/pkm_agent/tools/graph_analyzer.py` - Graph algorithms
2. `obsidian-pkm-agent/src/GraphView.tsx` - React visualization component

**Features**:
- Interactive D3.js graph
- Community detection
- Topic clustering
- Centrality metrics
- Export to JSON/SVG

---

### Issue #9: API Documentation

**Tools**:
- FastAPI for REST API
- Auto-generated OpenAPI/Swagger docs
- Interactive API explorer

```python
from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html

app = FastAPI(
    title="PKM Agent API",
    description="Personal Knowledge Management Agent API",
    version="1.0.0"
)

@app.get("/notes/search")
async def search_notes(query: str, limit: int = 10):
    """
    Search notes using hybrid retrieval.
    
    - **query**: Search query string
    - **limit**: Maximum results to return
    """
    results = await pkm_app.search(query, limit)
    return results
```

---

### Issue #10: Anki Integration

**Features**:
- Convert notes to flashcards
- Extract Q&A pairs
- Sync to AnkiConnect
- Spaced repetition scheduling

```python
class AnkiIntegration:
    async def create_cards_from_note(self, note):
        # Extract Q&A pairs from headings
        qa_pairs = self.extract_qa(note.content)
        
        # Create Anki cards
        for question, answer in qa_pairs:
            await self.anki_client.add_card(
                deck="PKM",
                front=question,
                back=answer,
                tags=note.metadata.tags
            )
```

---

## Phase 4: Production Readiness (Days 46-60)

### Issue #11: Performance Monitoring

**Tools**:
- OpenTelemetry for tracing
- Prometheus metrics
- Grafana dashboards

```python
from opentelemetry import trace
from opentelemetry.exporter.prometheus import PrometheusMetricReader

tracer = trace.get_tracer(__name__)

@tracer.start_as_current_span("search_notes")
async def search_notes(query):
    with tracer.start_span("vector_search"):
        results = await vectorstore.search(query)
    
    with tracer.start_span("rerank"):
        results = reranker.rerank(results)
    
    return results
```

---

### Issue #12: Integration Tests

**Framework**: pytest with fixtures

```python
@pytest.mark.integration
async def test_end_to_end_search(test_vault):
    # Create test notes
    await test_vault.create_note("Test", "Content about AI")
    
    # Index
    await pkm_app.index_pkm()
    
    # Search
    results = await pkm_app.search("AI")
    
    # Verify
    assert len(results) == 1
    assert results[0].title == "Test"
```

---

### Issue #13: Conversation Branching

**UI Features**:
- Tree view of conversation history
- Branch from any message
- Compare branches
- Merge insights

---

### Issue #14: Security Hardening

**Measures**:
```python
def sanitize_path(user_path):
    # Prevent path traversal
    clean_path = Path(user_path).resolve()
    if not clean_path.is_relative_to(PKM_ROOT):
        raise SecurityError("Path outside PKM root")
    return clean_path

def validate_input(data, schema):
    # Use Pydantic for validation
    try:
        return schema(**data)
    except ValidationError as e:
        raise InvalidInputError(e.errors())
```

---

### Issue #15: Plugin Marketplace

**Features**:
- Plugin registry
- Versioning and dependencies
- Sandboxed execution
- Rating and reviews

---

## Success Metrics

### Performance Targets
- [ ] Indexing: <5s for 10k notes (90% improvement)
- [ ] Search latency: <200ms average
- [ ] Sync delay: <2s file change to update
- [ ] Memory usage: <500MB for 50k notes

### Quality Targets
- [ ] Test coverage: >85%
- [ ] Zero critical security vulnerabilities
- [ ] API uptime: >99.9%
- [ ] User satisfaction: >4.5/5

### Adoption Targets
- [ ] 1000+ active installations
- [ ] 50+ community plugins
- [ ] 10+ integration partners

---

## Risk Management

### Technical Risks
1. **Vector store scalability** - Mitigation: Add Qdrant/Weaviate support
2. **LLM API costs** - Mitigation: Aggressive caching, rate limiting
3. **Sync conflicts** - Mitigation: CRDTs for merge-free sync

### Timeline Risks
1. **Dependency delays** - Mitigation: Parallel work streams
2. **Scope creep** - Mitigation: Strict MVP definition per issue
3. **Integration complexity** - Mitigation: Comprehensive testing

---

## Deployment Strategy

### Rollout Phases
1. **Alpha** (Day 30): Core team testing
2. **Beta** (Day 45): Public beta program (100 users)
3. **GA** (Day 60): General availability

### Rollback Plan
- Feature flags for new functionality
- Database migrations reversible
- Previous version always available

---

## Maintenance Plan

### Ongoing Tasks
- Weekly dependency updates
- Monthly security audits
- Quarterly performance reviews
- Continuous integration improvements

---

## Documentation Deliverables

- [ ] User Guide (Markdown, 50+ pages)
- [ ] API Reference (OpenAPI spec)
- [ ] Developer Guide (Contributing, architecture)
- [ ] Video Tutorials (5+ videos)
- [ ] FAQ and Troubleshooting

---

## Resources Required

### Team
- 1 Senior Backend Engineer (Python)
- 1 Senior Frontend Engineer (TypeScript/React)
- 1 DevOps Engineer (CI/CD, monitoring)
- 1 QA Engineer (Testing)
- 1 Technical Writer (Documentation)

### Infrastructure
- Development environment
- Staging environment
- CI/CD pipeline (GitHub Actions)
- Monitoring stack (Prometheus/Grafana)
- Documentation hosting

---

## Conclusion

This comprehensive roadmap provides a structured path to resolving all 15 identified issues over 60 development days. The phased approach ensures critical infrastructure is built first, followed by core features, advanced capabilities, and production hardening.

**Next Steps**:
1. Review and approve roadmap
2. Allocate resources
3. Set up project tracking (GitHub Projects)
4. Begin Phase 1 implementation
5. Weekly progress reviews

---

**Last Updated**: 2026-01-17  
**Document Owner**: AI Development Team  
**Status**: Approved for Implementation
