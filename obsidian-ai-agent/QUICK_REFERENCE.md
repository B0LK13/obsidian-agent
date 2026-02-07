# Quick Reference Card

## 🚀 One-Command Start

```powershell
cd obsidian-ai-agent/local-ai-stack
python ai_stack/api_server.py
```

## 🔧 Common Tasks

### Test Everything
```powershell
python test_integration.py
```

### Start with Benchmark
```powershell
.\start-optimized.ps1 -Benchmark
```

### Download Model
```powershell
python ai_stack/model_manager_cli.py download llama-2-7b-chat --quant Q4_K_M
```

### Check Status
```bash
curl http://127.0.0.1:8003/api/health
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | System status |
| `/api/rag/query` | POST | Query memory RAG |
| `/api/rag/add` | POST | Add to memory |
| `/api/rag/stats` | GET | Memory stats |
| `/api/validate` | POST | Check hallucinations |
| `/api/chunk` | POST | Chunk document |
| `/api/evaluate` | POST | Evaluate text |
| `/api/index` | POST | Index document |
| `/api/admin/stats` | GET | All stats |
| `/api/admin/clear-cache` | POST | Clear cache |

## 🐍 Python Examples

### Query Memory RAG
```python
from ai_stack.memory_rag import MemoryAugmentedRAG

rag = MemoryAugmentedRAG()
rag.add_to_memory("Docker is...", embedding, relationships=[...])
results = rag.process_query("What is Docker?", query_embedding)
print(results['consolidated_context'])
```

### Check Hallucination
```python
from ai_stack.hallucination_guard import HallucinationReductionSystem

guard = HallucinationReductionSystem()
result = guard.validate(generated, source)
print(f"Score: {result['overall_score']}")
```

### Chunk Document
```python
from ai_stack.semantic_chunker import SemanticChunkingStrategy

chunker = SemanticChunkingStrategy()
chunks = chunker.chunk_meeting_transcript(transcript)
```

### Evaluate
```python
from ai_stack.evaluation_harness import NoteTakingEvaluator

evaluator = NoteTakingEvaluator()
result = evaluator.evaluate(prediction, reference)
```

## 📝 Plugin Usage

### Available Commands
- `Open AI Chat` - Open chat panel
- `Index Vault for RAG` - Build index
- `Ask AI about current note` - Context query
- `Generate Canvas from notes` - Visual map
- `Semantic search with AI` - Find related

### Settings
```yaml
llmEndpoint: http://127.0.0.1:8000
embedEndpoint: http://127.0.0.1:8001
vectorEndpoint: http://127.0.0.1:8003  # Unified API
```

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| Import error | `pip install -r requirements.txt` |
| Port in use | Change port: `--port 8004` |
| No GPU | Use `--cpu-only` flag |
| Tests fail | Check Python version (3.10+) |

## 📊 Performance Tips

- **Speed**: Use Q4_K_M quantization
- **Quality**: Use Q5_K_M or Q6_K
- **Memory**: Enable `use_mmap: true`
- **GPU**: Set `gpu_layers: -1` (auto)

## 🔗 File Locations

```
Backend:  obsidian-ai-agent/local-ai-stack/ai_stack/
Plugin:   obsidian-ai-agent/obsidian-plugin/src/
Tests:    obsidian-ai-agent/local-ai-stack/test_integration.py
Config:   obsidian-ai-agent/local-ai-stack/ai_stack/config.yaml
```

---

*Keep this card handy!* 📌
