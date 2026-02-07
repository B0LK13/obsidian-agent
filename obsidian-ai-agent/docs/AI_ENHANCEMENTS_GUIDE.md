# AI Enhancements Guide

Complete guide to the advanced AI capabilities added to the Obsidian AI Agent.

## Overview

The enhanced AI Agent includes several advanced modules that work together to provide:

- **Smarter Retrieval**: Multi-hop RAG with query rewriting and re-ranking
- **Agent Tools**: Function calling for interacting with your vault
- **Advanced Reasoning**: Chain-of-thought, ReAct, and Tree of Thoughts
- **Better Memory**: Hierarchical memory with knowledge graph integration
- **Context Management**: Intelligent context window optimization
- **Quality Assurance**: Hallucination detection and response evaluation
- **Prompt Engineering**: Optimized prompts for various tasks

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                       │
│         (Unified interface for all capabilities)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    │                  │                  │
┌───▼────┐     ┌──────▼──────┐     ┌─────▼─────┐
│  RAG   │     │   Tools     │     │ Reasoning │
│ Module │     │   Agent     │     │  Engine   │
└───┬────┘     └──────┬──────┘     └─────┬─────┘
    │                 │                   │
┌───▼────┐     ┌──────▼──────┐     ┌─────▼─────┐
│ Memory │     │   Context   │     │   Eval    │
│ System │     │   Manager   │     │  Harness  │
└────────┘     └─────────────┘     └───────────┘
```

## Modules

### 1. Advanced RAG (`advanced_rag.py`)

Multi-hop retrieval with intelligent query processing.

**Features:**
- Query rewriting and expansion
- Hybrid search (dense + BM25)
- HNSW indexing for fast retrieval
- Multi-hop traversal
- Cross-encoder re-ranking

**Usage:**
```python
from ai_stack.advanced_rag import AdvancedRAG

rag = AdvancedRAG()
rag.add_document("doc1", "Your note content here...", {"tag": "ai"})

result = rag.retrieve(
    "What do I know about machine learning?",
    use_multi_hop=True,
    top_k=5
)

for doc in result['documents']:
    print(f"{doc.id}: {doc.content[:100]}...")
```

### 2. Agent Tools (`agent_tools.py`)

Function calling system for vault interaction.

**Available Tools:**
- `search_notes` - Semantic search across vault
- `get_note` - Retrieve specific note content
- `create_note` - Create new notes
- `get_vault_stats` - Get vault statistics
- `summarize_note` - Generate summaries
- `extract_tasks` - Find action items
- `calculate` - Mathematical calculations

**Usage:**
```python
from ai_stack.agent_tools import create_obsidian_tools, ToolUsingAgent

# Create tools with vault interface
tools = create_obsidian_tools(vault_interface)
agent = ToolUsingAgent(llm_client, tools)

# Execute with tool use
result = agent.run("Create a note about my project ideas")
```

### 3. Reasoning Engine (`reasoning_engine.py`)

Multiple reasoning strategies for complex problems.

**Strategies:**
- **Chain-of-Thought**: Step-by-step reasoning
- **ReAct**: Alternate reasoning and acting
- **Tree of Thoughts**: Explore multiple paths
- **Self-Reflective**: Iterative improvement

**Usage:**
```python
from ai_stack.reasoning_engine import ReasoningOrchestrator

reasoner = ReasoningOrchestrator(llm_client)
result = reasoner.solve("How do I deploy this application?")

print(result['strategy'])  # e.g., "planning"
print(result['result'])
```

### 4. Advanced Memory (`advanced_memory.py`)

Hierarchical memory system with knowledge graphs.

**Memory Types:**
- **Working Memory**: Recent, high-access items
- **Episodic Memory**: Time-based experiences
- **Semantic Memory**: Facts and concepts
- **Knowledge Graph**: Entity relationships

**Usage:**
```python
from ai_stack.advanced_memory import AdvancedMemorySystem

memory = AdvancedMemorySystem()

# Store memories
memory.store("Met with Alice about project", "episodic", importance=0.8)
memory.store("Python is a programming language", "semantic", importance=0.9)

# Retrieve
results = memory.retrieve("project meeting")

# Query knowledge graph
related = memory.query_knowledge_graph("relations", entity="Alice")
```

### 5. Context Manager (`context_manager.py`)

Intelligent context window management.

**Features:**
- Sliding window with priority
- Hierarchical summarization
- Token budget management
- Dynamic context injection

**Usage:**
```python
from ai_stack.context_manager import SmartContextBuilder

builder = SmartContextBuilder(llm_client, max_context_tokens=6000)
builder.set_system_prompt("You are a helpful assistant.")
builder.add_user_message("Tell me about...")
builder.add_retrieved_context(documents)

messages = builder.build_context()
```

### 6. Evaluation Harness (`evaluation_harness.py`)

Response quality evaluation and hallucination detection.

**Metrics:**
- Hallucination risk score
- Faithfulness to context
- Answer relevance
- Structure quality

**Usage:**
```python
from ai_stack.evaluation_harness import ResponseEvaluator

evaluator = ResponseEvaluator(llm_client)
result = evaluator.evaluate(
    question="What is ML?",
    answer="Machine learning is...",
    retrieved_contexts=["ML is a subset of AI..."]
)

print(f"Overall score: {result.overall_score}")
print(f"Issues: {result.issues}")
```

### 7. Prompt Engineering (`prompt_engineering.py`)

Optimized prompts and templates.

**Available Templates:**
- `qa_cot` - Question answering with reasoning
- `summarize` - Text summarization
- `code_generate` - Code generation
- `extract_entities` - Entity extraction
- `classify` - Text classification
- `analyze_note` - Note analysis
- `react` - ReAct prompting

**Usage:**
```python
from ai_stack.prompt_engineering import PromptLibrary

library = PromptLibrary()
template = library.get("summarize")

prompt = template.render(text="Your long text here...", max_words=100)
```

## Master Orchestrator

The `agent_orchestrator.py` brings everything together:

```python
from ai_stack.agent_orchestrator import (
    create_enhanced_agent, 
    AgentConfig,
    AgentSession
)

# Configure
config = AgentConfig(
    use_advanced_rag=True,
    use_multi_hop=True,
    reasoning_strategy="auto",
    enable_evaluation=True,
    enable_tools=True
)

# Create agent
agent = create_enhanced_agent(
    llm_client=your_llm,
    config=config,
    vault_interface=your_vault
)

# Start session
session = AgentSession(agent)

# Chat
result = session.send_message("What do I know about AI?")
print(result['response'])

# Check evaluation
if result.get('evaluation'):
    print(f"Quality score: {result['evaluation']['overall_score']}")

# Provide feedback
session.provide_feedback(
    message_index=len(session.history) - 1,
    rating=5,
    comment="Very helpful!"
)
```

## Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `use_advanced_rag` | Enable multi-hop retrieval | True |
| `use_multi_hop` | Follow relationships in RAG | True |
| `retrieval_top_k` | Number of documents to retrieve | 5 |
| `reasoning_strategy` | Reasoning approach | "auto" |
| `use_advanced_memory` | Enable hierarchical memory | True |
| `enable_evaluation` | Enable response evaluation | True |
| `enable_tools` | Enable function calling | True |
| `max_context_tokens` | Context window size | 6000 |

## Performance Tips

### For Large Vaults (>10,000 notes)
```python
config = AgentConfig(
    use_advanced_rag=True,  # HNSW indexing
    retrieval_top_k=10,     # More results
    max_context_tokens=8000 # Larger context
)
```

### For Complex Queries
```python
config = AgentConfig(
    reasoning_strategy="tree_of_thoughts",
    use_multi_hop=True
)
```

### For Speed
```python
config = AgentConfig(
    reasoning_strategy="direct",  # Skip reasoning
    retrieval_top_k=3,            # Fewer docs
    enable_evaluation=False       # Skip eval
)
```

## Testing

Run the test suite to verify all components:

```bash
cd local-ai-stack
python tests/run_tests.py
```

## Troubleshooting

### High Memory Usage
- Reduce `max_context_tokens`
- Lower `retrieval_top_k`
- Disable `use_advanced_memory` if not needed

### Slow Responses
- Use `reasoning_strategy="direct"`
- Reduce `max_reasoning_steps`
- Disable `use_multi_hop`

### Poor Quality
- Increase `retrieval_top_k`
- Enable `enable_evaluation` for feedback
- Use `reasoning_strategy="chain_of_thought"`

## Examples

### Example 1: Research Assistant
```python
agent = create_enhanced_agent(llm, AgentConfig(
    use_advanced_rag=True,
    use_multi_hop=True,
    reasoning_strategy="tree_of_thoughts"
))

result = agent.chat("Compare the approaches in my ML notes")
# Agent will:
# 1. Retrieve relevant notes
# 2. Explore multiple comparison angles
# 3. Provide structured comparison
```

### Example 2: Task Manager
```python
agent = create_enhanced_agent(llm, AgentConfig(
    enable_tools=True,
    use_advanced_memory=True
))

result = agent.chat("What tasks do I have due this week?")
# Agent will:
# 1. Use extract_tasks tool
# 2. Store in episodic memory
# 3. Return organized task list
```

### Example 3: Knowledge Explorer
```python
agent = create_enhanced_agent(llm, AgentConfig(
    use_advanced_rag=True,
    enable_evaluation=True
))

result = agent.chat("Explain the connections between my projects")
# Agent will:
# 1. Multi-hop retrieval
# 2. Build knowledge graph
# 3. Detect any hallucinations
# 4. Provide confidence score
```

## Future Enhancements

Planned additions:
- Multi-modal support (images, audio)
- Fine-tuning capabilities
- Distributed processing
- Real-time collaboration
- Advanced visualization

---

**Last Updated**: 2026-01-30  
**Version**: 1.5.0-Enhanced
