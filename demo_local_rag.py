"""
Demo script for Local RAG (Retrieval-Augmented Generation) with LM Studio.
Demonstrates:
1. Connecting to Local LLM (LM Studio)
2. Creating and Indexing Notes (Chunking)
3. Semantic Search (Vector DB)
4. Context-Aware Chat (RAG)
"""
import asyncio
import os
import shutil
from pathlib import Path
from pkm_agent.app import PKMAgentApp
from pkm_agent.config import Config
from pkm_agent.llm import Message

# --- CONFIGURATION ---
# Point to LM Studio (OpenAI-compatible server)
os.environ["PKMA_LLM__PROVIDER"] = "openai"
os.environ["PKMA_LLM__BASE_URL"] = "http://localhost:1234/v1"
os.environ["PKMA_LLM__API_KEY"] = "lm-studio"
os.environ["PKMA_LLM__MODEL"] = "local-model" # LM Studio usually ignores this or uses loaded model

# Setup paths
DEMO_DIR = Path("demo_rag_env")
VAULT_DIR = DEMO_DIR / "vault"

async def main():
    print("🚀 Starting Local RAG Demo...")
    
    # 1. Setup clean environment
    if DEMO_DIR.exists():
        shutil.rmtree(DEMO_DIR)
    VAULT_DIR.mkdir(parents=True)
    
    config = Config()
    config.pkm_root = VAULT_DIR
    config.data_dir = DEMO_DIR / ".pkm-agent"
    
    app = PKMAgentApp(config)
    
    try:
        print("\n📥 Initializing App & Local Embeddings (sentence-transformers)...")
        await app.initialize()
        
        # 2. Create Content (The Knowledge Base)
        print("\n📝 Creating knowledge base...")
        
        note1 = """# The PKM Agent Protocol
The PKM Agent is an autonomous system designed to organize personal knowledge.
It uses a local vector database to chunk and index markdown files.
Key features include:
- Auto-healing of broken links
- Semantic search using embeddings
- Local LLM integration for privacy
"""
        (VAULT_DIR / "Protocol.md").write_text(note1)
        
        note2 = """# Deployment Architecture
The system runs as a Python backend server exposing a WebSocket API.
Clients like Obsidian connect to this server.
Data is stored in ChromaDB (vectors) and SQLite (metadata).
"""
        (VAULT_DIR / "Architecture.md").write_text(note2)
        
        # 3. Indexing & Chunking
        print("\n⚙️  Indexing and Chunking...")
        stats = await app.index_pkm()
        print(f"   ✅ Indexed {stats['indexed']} files")
        print(f"   ✅ Created {stats['chunks']} vector chunks")
        
        # 4. Semantic Search
        print("\n🔎 Testing Semantic Search...")
        query = "How does the system store data?"
        print(f"   Query: '{query}'")
        results = await app.search(query, limit=1)
        if results:
            print(f"   ✅ Found relevant note: {results[0]['title']}")
            print(f"   📄 Snippet: {results[0]['snippet'][:100]}...")
        else:
            print("   ❌ No results found!")

        # 5. RAG Chat with Local LLM
        print("\n🤖 Chatting with Local LLM (RAG)...")
        question = "What databases does the PKM agent use?"
        print(f"   User: {question}")
        
        print("   Assistant: ", end="", flush=True)
        response_text = ""
        try:
            async for chunk in app.ask_with_context(question):
                print(chunk, end="", flush=True)
                response_text += chunk
            print("\n")
            
            if response_text:
                print("✅ RAG Chat Successful!")
            else:
                print("❌ No response received. Is LM Studio running on port 1234?")
                
        except Exception as e:
            print(f"\n❌ Error calling LLM: {e}")
            print("💡 Tip: Ensure LM Studio Server is started (Start Server button) and a model is loaded.")

    finally:
        await app.close()
        # Cleanup
        # shutil.rmtree(DEMO_DIR) 
        print(f"\n✨ Demo complete. Data stored in: {DEMO_DIR}")

if __name__ == "__main__":
    asyncio.run(main())
