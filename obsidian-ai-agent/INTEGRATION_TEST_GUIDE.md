# Integration Test Guide

Complete guide to testing the Obsidian AI Agent with all optimizations.

---

## 🚀 Quick Start Test

### 1. Run Integration Tests

```powershell
cd obsidian-ai-agent/local-ai-stack
python test_integration.py
```

Expected output:
```
======================================================================
OBSIDIAN AI AGENT - INTEGRATION TEST SUITE
======================================================================

[TEST] Memory RAG Initialization
  ✓ PASS

[TEST] Memory RAG Add and Retrieve
  ✓ PASS

[TEST] Hallucination Guard - Fact Checking
  ✓ PASS

...

======================================================================
TEST SUMMARY
======================================================================
Passed: 11
Failed: 0
Total:  11
======================================================================
```

### 2. Start Unified API Server

```powershell
python ai_stack/api_server.py --port 8003
```

Test the API:
```bash
# Health check
curl http://127.0.0.1:8003/api/health

# Test RAG
curl -X POST http://127.0.0.1:8003/api/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Docker?", "query_embedding": [0.1, 0.2, ...]}'

# Test chunking
curl -X POST http://127.0.0.1:8003/api/chunk \
  -H "Content-Type: application/json" \
  -d '{"text": "# Meeting\n\nAlice: Hello\nBob: Hi", "doc_type": "meeting_transcript"}'

# Test validation
curl -X POST http://127.0.0.1:8003/api/validate \
  -H "Content-Type: application/json" \
  -d '{"generated": "Docker is a platform", "source": "Docker is a container platform"}'

# Test evaluation
curl -X POST http://127.0.0.1:8003/api/evaluate \
  -H "Content-Type: application/json" \
  -d '{"prediction": "# Notes\n\n- Point 1", "reference": "Point 1"}'
```

---

## 🔧 Component Tests

### Memory RAG Test

```python
from ai_stack.memory_rag import MemoryAugmentedRAG

rag = MemoryAugmentedRAG()

# Add content
rag.add_to_memory(
    content="Docker is a containerization platform",
    embedding=[0.1] * 384,
    metadata={'significant': True},
    relationships=[('Docker', 'containerization', 'is_a')]
)

# Query
results = rag.process_query("What is Docker?", [0.1] * 384)
print(results['consolidated_context'])
```

### Hallucination Guard Test

```python
from ai_stack.hallucination_guard import HallucinationReductionSystem

guard = HallucinationReductionSystem()

# Test factual content
result = guard.validate(
    generated="Docker is a containerization platform",
    source="Docker is a containerization platform created by Docker Inc"
)
print(f"Score: {result['overall_score']}, Passed: {result['passed']}")

# Test hallucinated content
result = guard.validate(
    generated="Docker was created by Microsoft in 2010",
    source="Docker was created by Docker Inc in 2013"
)
print(f"Score: {result['overall_score']}, Suggestions: {result['suggestions']}")
```

### Semantic Chunking Test

```python
from ai_stack.semantic_chunker import SemanticChunkingStrategy

chunker = SemanticChunkingStrategy()

transcript = """
Alice: Welcome to the meeting.
Bob: I have the projections.
Alice: Please share.
"""

chunks = chunker.chunk_meeting_transcript(transcript)
for chunk in chunks:
    print(f"{chunk.id}: {chunk.text[:50]}...")
```

### Evaluation Test

```python
from ai_stack.evaluation_harness import NoteTakingEvaluator

evaluator = NoteTakingEvaluator()

result = evaluator.evaluate(
    prediction="# Notes\n\n## Action Items\n- [ ] Task 1",
    reference="Task 1 needs to be done"
)

print(f"Overall: {result.overall_score}")
for score in result.dimension_scores:
    print(f"  {score.dimension}: {score.score}")
```

---

## 📊 Performance Benchmarks

Run the benchmark suite:

```powershell
python ai_stack/benchmark.py
```

Expected results on typical hardware:

| Component | Operation | Expected Time |
|-----------|-----------|---------------|
| Memory RAG | Query | < 100ms |
| Hallucination Guard | Validate | < 200ms |
| Semantic Chunking | Chunk | < 50ms |
| Evaluation | Evaluate | < 100ms |

---

## 🔍 Troubleshooting

### Import Errors

```powershell
# Make sure you're in the right directory
cd obsidian-ai-agent/local-ai-stack

# Check Python path
python -c "import sys; print(sys.path)"

# Install missing dependencies
pip install flask flask-cors pyyaml numpy
```

### Component Not Available

If a component shows as "unavailable":

1. Check for import errors:
```python
python -c "from ai_stack.memory_rag import MemoryAugmentedRAG"
```

2. Check dependencies:
```python
python -c "import numpy; print('numpy OK')"
```

### API Connection Failed

1. Check if server is running:
```bash
curl http://127.0.0.1:8003/api/health
```

2. Check firewall settings (should be localhost only)

3. Verify port not in use:
```powershell
Get-NetTCPConnection -LocalPort 8003
```

---

## 🎯 End-to-End Test

Complete workflow test:

```python
import requests

API_URL = "http://127.0.0.1:8003/api"

# 1. Health check
response = requests.get(f"{API_URL}/health")
print(f"Health: {response.json()}")

# 2. Index a document
doc = {
    "file_path": "test/meeting.md",
    "content": """
# Strategy Meeting

Attendees: Alice, Bob

## Decisions
- Approved Q4 budget
- Timeline: 3 months
""",
    "doc_type": "meeting_transcript"
}
response = requests.post(f"{API_URL}/index", json=doc)
print(f"Indexed: {response.json()}")

# 3. Query
data = {
    "query": "What was decided about the budget?",
    "query_embedding": [0.1] * 384
}
response = requests.post(f"{API_URL}/rag/query", json=data)
print(f"Query result: {response.json()}")

# 4. Validate response
data = {
    "generated": "The Q4 budget was approved for 3 months.",
    "source": doc["content"]
}
response = requests.post(f"{API_URL}/validate", json=data)
print(f"Validation: {response.json()}")

# 5. Evaluate
data = {
    "prediction": "# Meeting Notes\n\nBudget approved for Q4.",
    "reference": doc["content"]
}
response = requests.post(f"{API_URL}/evaluate", json=data)
print(f"Evaluation: {response.json()}")
```

---

## ✅ Test Checklist

- [ ] Integration tests pass (11/11)
- [ ] API server starts successfully
- [ ] Health endpoint returns 200
- [ ] Memory RAG endpoints work
- [ ] Hallucination guard detects issues
- [ ] Semantic chunking creates chunks
- [ ] Evaluation returns scores
- [ ] Document indexing works
- [ ] All components show as available

---

## 📈 Next Steps

After successful testing:

1. **Build Obsidian Plugin**
   ```powershell
   cd obsidian-plugin
   npm install
   npm run build
   ```

2. **Install to Obsidian**
   - Copy `main.js` and `manifest.json` to vault plugins folder
   - Enable plugin in Obsidian settings

3. **Configure Endpoints**
   - Set API endpoint to `http://127.0.0.1:8003`
   - Test connection

4. **Start Using**
   - Open AI Chat view
   - Ask questions about your notes
   - See optimized responses with context!

---

*All tests passing? You're ready for production!* 🎉
