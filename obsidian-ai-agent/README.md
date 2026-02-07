# Obsidian AI Agent - Platform Independent, Local-Only

A complete local AI agent system for Obsidian that runs entirely offline with no network egress.

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ Obsidian Desktop                                            │
│  ├─ Obsidian AI Agent Plugin (TypeScript)                   │
│  ├─ Dataview Integration                                    │
│  ├─ Canvas Integration                                      │
│  └─ Local REST API                                          │
└───────────────┬─────────────────────────────────────────────┘
                │ localhost only (127.0.0.1)
                ▼
┌─────────────────────────────────────────────────────────────┐
│ Local AI Stack (Python)                                     │
│  ├─ LLM Server (llama.cpp)         :8000/v1/chat/completions│
│  ├─ Embeddings Server              :8001/embed              │
│  ├─ Vector DB (Chroma/Lance)       :8002                    │
│  └─ Egress Blocker (code-level)                             │
└─────────────────────────────────────────────────────────────┘
```

## 📦 Components

### 1. Local AI Stack (`local-ai-stack/`)

Platform-independent Python services that run on localhost only.

**Services:**
- **LLM Server** (port 8000): OpenAI-compatible chat completions
- **Embeddings Server** (port 8001): Text embeddings for RAG
- **Vector DB** (port 8002): Semantic search database

**Security:**
- All services bind to `127.0.0.1` only
- Code-level egress blocking
- No external network access

### 2. Obsidian Plugin (`obsidian-plugin/`)

TypeScript plugin integrating with Obsidian's API.

**Features:**
- AI Chat view
- RAG (Retrieval Augmented Generation)
- Canvas generation
- Dataview integration
- Semantic search
- Auto-indexing

## 🚀 Quick Start

### Prerequisites

- Python 3.10+
- Obsidian Desktop
- (Optional) NVIDIA GPU for acceleration

### Step 1: Install Local AI Stack

```bash
cd local-ai-stack
pip install -r requirements.txt
```

### Step 2: Download Models

Download GGUF models to `local-ai-stack/models/`:

**Recommended LLM:**
- [Llama-2-7B-Chat-Q4_K_M.gguf](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF) (~4GB)
- [Mistral-7B-Instruct-Q4_K_M.gguf](https://huggingface.co/TheBloke/Mistral-7B-Instruct-v0.2-GGUF) (~4GB)

**Embeddings:**
- Auto-downloaded on first run (sentence-transformers)

### Step 3: Start Local AI Stack

**Windows:**
```powershell
.\start-local-ai-stack.ps1
```

**macOS/Linux:**
```bash
./start-local-ai-stack.sh
```

**Options:**
- `-CpuOnly`: Force CPU mode
- `-LlmPort 8000`: Custom LLM port
- `-SkipHealthCheck`: Skip health checks

### Step 4: Install Obsidian Plugin

1. Build the plugin:
```bash
cd obsidian-plugin
npm install
npm run build
```

2. Copy to Obsidian vault:
```bash
mkdir -p "<vault>/.obsidian/plugins/obsidian-ai-agent"
cp main.js manifest.json "<vault>/.obsidian/plugins/obsidian-ai-agent/"
```

3. Enable plugin in Obsidian:
   - Settings → Community Plugins
   - Enable "Obsidian AI Agent"

### Step 5: Configure

1. Open Obsidian AI Agent settings
2. Verify endpoints (should be localhost):
   - LLM: `http://127.0.0.1:8000`
   - Embeddings: `http://127.0.0.1:8001`
   - Vector DB: `http://127.0.0.1:8002`

3. Click "Index Vault" to build RAG index

## 🎯 Usage

### AI Chat

1. Click the 🤖 ribbon icon or press `Ctrl+Shift+A`
2. Type your question
3. AI responds using your knowledge base context

### Semantic Search

Use the command palette: `Ctrl+P` → "Semantic search with AI"

### Generate Canvas

1. Open a note
2. Run command: "Generate Canvas from selected notes"
3. AI creates a visual map of related notes

### Dataview Integration

Query your knowledge base:
```dataview
TABLE aiSummary
FROM #project
WHERE aiRelevance > 0.8
```

## 🔒 Security

### Local-Only Enforcement

The system enforces localhost-only operation at multiple levels:

1. **Code-Level**: Endpoints validated to be 127.0.0.1/localhost
2. **Network**: Services bind to 127.0.0.1 only
3. **Firewall**: Optional OS-level egress blocking

```typescript
// Example: Validation in ai-client.ts
if (url.hostname !== '127.0.0.1' && url.hostname !== 'localhost') {
    throw new Error('External connections blocked');
}
```

### No Data Exfiltration

- No telemetry
- No cloud APIs
- No external requests
- All processing local

## 🛠️ Development

### Project Structure

```
obsidian-ai-agent/
├── local-ai-stack/
│   ├── ai_stack/
│   │   ├── llm_server.py
│   │   ├── embed_server.py
│   │   └── vector_server.py
│   ├── start-local-ai-stack.ps1
│   ├── start-local-ai-stack.sh
│   └── requirements.txt
├── obsidian-plugin/
│   ├── src/
│   │   ├── main.ts
│   │   ├── ai-client.ts
│   │   ├── rag-service.ts
│   │   ├── canvas-integration.ts
│   │   └── dataview-integration.ts
│   ├── esbuild.config.mjs
│   ├── manifest.json
│   └── package.json
└── README.md
```

### Adding Features

**New AI Service:**
1. Add server to `ai_stack/`
2. Update launcher scripts
3. Add client method to `ai-client.ts`

**New Plugin Command:**
1. Add command in `main.ts`
2. Implement in appropriate service
3. Update settings if needed

## 📊 Performance

### Hardware Requirements

**Minimum (CPU-only):**
- 8GB RAM
- 10GB disk space
- Any modern CPU

**Recommended (GPU):**
- 16GB RAM
- NVIDIA GPU with 8GB+ VRAM
- SSD storage

### Benchmarks

| Model | Hardware | Tokens/sec |
|-------|----------|------------|
| Llama-2-7B-Q4 | CPU (8 cores) | ~15 |
| Llama-2-7B-Q4 | RTX 3060 | ~50 |
| Llama-2-13B-Q4 | RTX 3090 | ~40 |

## 🔧 Troubleshooting

### Services Won't Start

Check Python dependencies:
```bash
pip install -r requirements.txt
```

### Out of Memory

Use smaller model:
- Try Q4_K_M quantization
- Reduce context length in settings
- Use CPU-only mode: `-CpuOnly`

### Plugin Can't Connect

1. Verify services are running:
   ```bash
   curl http://127.0.0.1:8000/health
   ```

2. Check Windows Firewall/antivirus

3. Verify plugin settings match service ports

### Slow Performance

- Enable GPU if available
- Use smaller models (7B vs 13B)
- Reduce max context length
- Close other applications

## 🤝 Integration with Existing Knowledge Base

This system integrates with your existing knowledge base at:
```
C:\Users\Admin\Documents\B0LK13v2\knowledge_db\
```

The RAG service will index all markdown files and use the existing graph structure for context-aware responses.

## 📚 API Reference

### Local Endpoints

**LLM Server** (`http://127.0.0.1:8000`)
- `GET /health` - Health check
- `GET /v1/models` - List models
- `POST /v1/chat/completions` - Chat completion

**Embeddings** (`http://127.0.0.1:8001`)
- `GET /health` - Health check
- `POST /embed` - Generate embeddings

**Vector DB** (`http://127.0.0.1:8002`)
- `GET /health` - Health check
- `POST /add` - Add documents
- `POST /query` - Semantic search
- `GET /count` - Document count

## 📄 License

MIT License - See LICENSE file

## 🙏 Acknowledgments

- [llama.cpp](https://github.com/ggerganov/llama.cpp)
- [sentence-transformers](https://www.sbert.net/)
- [Obsidian](https://obsidian.md/)
- [Dataview](https://github.com/blacksmithgu/obsidian-dataview)

---

**Made with 🔒 for offline-first knowledge work**
