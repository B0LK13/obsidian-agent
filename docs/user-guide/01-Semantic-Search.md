# 🧠 Semantic Search & Vector Core

The Obsidian Agent has been upgraded from simple keyword matching to a modern **Semantic Vector Store**. This allows the agent to understand the *meaning* of your notes rather than just looking for exact words.

## 🚀 Getting Started

### 1. Build the Index
Before you can use semantic features, you must index your vault.
- Open the Command Palette (`Ctrl/Cmd + P`)
- Run: `Obsidian Agent: Rebuild Semantic Index`
- Type `yes` to confirm.
- The agent will scan your markdown files and generate embeddings.

### 🔍 How to Search
Once indexed, you can search your vault by concept:
- Run: `Obsidian Agent: Semantic Search`
- Enter a query like: "How do I manage my database backups?"
- Even if your note is titled "Postgres Maintenance," the agent will find it because it understands the relationship.

## 🛠️ Technical Details
- **Provider:** OpenAI (default)
- **Model:** `text-embedding-3-small`
- **Storage:** `.obsidian/plugins/obsidian-agent/vector_store.json`
- **Logic:** Uses Cosine Similarity to find the closest conceptual matches.
