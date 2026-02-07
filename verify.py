import sys
sys.path.insert(0, 'apps/pkm-agent/src')

try:
    from pkm_agent import PKMAgentApp, Config
    from pkm_agent.rag import Chunker, EmbeddingEngine, Retriever, VectorStore
    from pkm_agent.llm import LLMProvider, OpenAIProvider, OllamaProvider
    from pkm_agent.data import Database, FileIndexer
    from pkm_agent.websocket_sync import SyncServer
    print("✓ All Python imports successful!")
except ImportError as e:
    print(f"✗ Import error: {e}")
