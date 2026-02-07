# Obsidian Agent - Gap Analysis & Modernization Plan
**Date:** February 7, 2026
**Status:** Analysis Complete

## 1. Executive Summary
The current `obsidian-agent` (v1.0.0) is a robust "Command & Chat" plugin. It offers excellent UI polish and a wide range of single-step text utilities. However, its "intelligence" is powered by legacy TF-IDF (Term Frequency-Inverse Document Frequency) algorithms. While fast for small inputs, this approach lacks deep semantic understanding and scales poorly (O(N²) complexity for clustering).

To compete with the "best note-taking agents" (which act as a second brain), the system needs to migrate from **Keyword Matching** to **Semantic Embeddings**, and from **Single-Step Commands** to **Multi-Step Agentic Loops**.

## 2. Gap Analysis

### 🚨 Critical Gaps (Must Fix)

| Feature Area | Current Implementation | The "Best Agent" Standard | Gap Severity |
| :--- | :--- | :--- | :--- |
| **Semantic Search (RAG)** | **TF-IDF / Keywords.** <br>Calculates similarity based on shared words. "Car" does not match "Automobile". | **Vector Embeddings.** <br>Uses LLM embeddings (OpenAI/Local) to match concepts. "Car" matches "Automobile" perfectly. | **EXTREME** |
| **Scalability** | **O(N²) Clustering.** <br>Compares every note to every other note in memory. Will freeze Obsidian on vaults > 2k notes. | **Vector Database (IVF/HNSW).** <br>Scalable approximate nearest neighbor search. Handles 100k+ notes easily. | **EXTREME** |
| **Reasoning Engine** | **Single-Shot Request/Response.** <br>User asks -> AI answers. No internal "thought process" or error correction. | **Agentic Loop (ReAct).** <br>Agent plans: "First I'll search for X, then read note Y, then write summary Z". | **HIGH** |
| **Context Window** | **Naive Context Stuffing.** <br>Stuffs raw text into prompt until limit is hit. Inefficient and expensive. | **Smart Retrieval & Reranking.** <br>Retrieves only relevant snippets, reranks them, and summarizes before context stuffing. | **HIGH** |

### ⚠️ Functional Gaps (Important)

| Feature Area | Current Implementation | The "Best Agent" Standard | Gap Severity |
| :--- | :--- | :--- | :--- |
| **Multi-Modal** | **Text Only.** <br>Ignores images and audio files. | **Vision & Audio.** <br>Transcribes voice notes, analyzes whiteboard photos, indexes diagrams. | **MEDIUM** |
| **Memory** | **Settings Only.** <br>Profiles store API keys/Prompts. No learning. | **Long-term Memory.** <br>Remembers user preferences ("Don't use emojis") and facts ("I live in Tokyo") across sessions. | **MEDIUM** |
| **External Tools** | **None (Vault Only).** | **Connected.** <br>Can search the web for missing info, check calendar, draft emails. | **MEDIUM** |

## 3. Implementation Roadmap

We will transform the agent in 3 phases.

### Phase 1: The Semantic Core (Foundation)
*Goal: Replace TF-IDF with a local Vector Store and Embedding Engine.*
1.  **Select Embedding Strategy:** Support both Local (Transformers.js / Xenova) and API-based (OpenAI text-embedding-3-small) embeddings.
2.  **Implement Vector Store:** Use a lightweight, local vector index (e.g., specific to Obsidian environment, perhaps just a binary file + HNSW or a lightweight JS library).
3.  **Refactor `ContextEngine`:** Replace `scoreNoteRelevance` and `buildSemanticClusters` with vector-based operations.
4.  **Result:** Massive jump in "related note" quality and scalability.

### Phase 2: The Agentic Brain
*Goal: Enable multi-step reasoning.*
1.  **Implement `AgentLoop`:** A standardized ReAct (Reason+Act) loop.
2.  **Tool Definitions:** Expose Obsidian APIs as tools (`readNote`, `createNote`, `appendNote`, `searchNotes`).
3.  **Refactor `AIService`:** Support "function calling" (native or emulated).
4.  **Result:** "Research this topic" command will actually browse your vault, read 10 notes, and write a synthesized report automatically.

### Phase 3: Senses & Memory
*Goal: Multi-modal and personalization.*
1.  **Audio Transcriber:** Add local Whisper support (or API).
2.  **Vision Support:** Send image attachments to GPT-4o/Claude-3-5.
3.  **Memory Store:** specific vector collection for "User Facts".

## 4. Immediate Next Step
**Start Phase 1:** Create `src/services/vectorStore.ts` and `src/services/embeddingService.ts` to begin the migration from TF-IDF.
