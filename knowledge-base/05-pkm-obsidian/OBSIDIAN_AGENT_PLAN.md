# Obsidian Native Agent: Development Plan

## 1. Executive Summary
This project aims to build a native Obsidian plugin that acts as an intelligent agent capable of managing the user's vault through natural language interaction. Unlike external scripts, this agent lives *inside* Obsidian, leveraging the Vault API for seamless, real-time access to notes, metadata, and UI hooks.

## 2. Technical Architecture

### 2.1 Technology Stack
*   **Language:** TypeScript (Strict typing for robustness)
*   **Runtime:** Node.js (Development/Build) / Electron (Obsidian Runtime)
*   **Framework:** React (for Chat UI components)
*   **Build Tool:** `esbuild` (Fast bundling)
*   **AI Integration:** OpenAI API (initial provider) with modular interface for generic LLM support (Ollama/Local support).

### 2.2 Core Modules
1.  **Agent Core:** The brain handling NLP, intent recognition, and conversation state.
2.  **Vault Interface:** A robust wrapper around `app.vault` and `app.fileManager` for safe file operations.
3.  **Metadata Manager:** Interfaces with `app.metadataCache` for high-speed linking and tagging.
4.  **UI Layer:** A dedicated Sidebar View (React) for chat interaction and non-blocking notifications.

## 3. Core Functionality & API Integration

### 3.1 Note CRUD
*   **Create:** `vault.create(path, content)` with safe path sanitization.
*   **Read:** `vault.read(tfile)` for content retrieval.
*   **Update:** `vault.process(tfile, callback)` for atomic updates (prevents race conditions).
*   **Delete:** `vault.trash(tfile, true)` (Use system trash for safety).

### 3.2 Tagging & Linking
*   **Linking:** Use `app.fileManager.generateMarkdownLink(file, sourcePath)` to ensure robust internal linking.
*   **Tagging:** Manipulate Frontmatter using `app.fileManager.processFrontMatter`.

### 3.3 Search & Filtering
*   **Search:** Leverage `app.metadataCache` for instant tag/alias lookups.
*   **Full Text:** Optional integration with `prepareSimpleSearch` for content scanning without heavy indexing overhead.

### 3.4 Template Integration
*   **Engine:** Support internal variable replacement (e.g., `{{date}}`, `{{title}}`) or integration with the core Templates plugin logic.

## 4. Request Handling (The "Brain")

### 4.1 NLP & Intent Recognition
The agent will use a **Tool Use** (Function Calling) architecture.
*   **Input:** User says "Create a meeting note for Project X with the team."
*   **Processing:** LLM analyzes intent and maps to a tool: `create_note(title="Meeting - Project X", template="meeting")`.
*   **Execution:** Plugin executes the tool against the Obsidian API.

### 4.2 Action Mapping
| User Intent | Internal Action | Obsidian API Hook |
| :--- | :--- | :--- |
| "New note about X" | `createNote` | `vault.create` |
| "Link X to Y" | `linkNotes` | `fileManager.processFrontMatter` / Editor transaction |
| "Summarize X" | `readNote` -> `llm.summarize` | `vault.read` |
| "Delete X" | `deleteNote` | `vault.trash` |

## 5. Development Phases

### Phase 1: MVP (Foundation & CRUD)
*   **Goal:** A working plugin that can create/read notes via chat.
*   **Tasks:**
    *   Scaffold plugin with `obsidian-plugin-sample`.
    *   Implement `VaultManager` service.
    *   Build basic React Chat UI in the sidebar.
    *   Integrate OpenAI API for basic "Chat" (no tools yet).
    *   **Deliverable:** Chat window that can answer questions and run a hardcoded "create note" command.

### Phase 2: Advanced (The "Agent")
*   **Goal:** Autonomous management using tools.
*   **Tasks:**
    *   Implement "Function Calling" logic in the LLM layer.
    *   Build tools for: `Search`, `Update`, `Tag`, `Link`.
    *   Implement `TemplateService`.
    *   **Deliverable:** User can say "Refactor this note to include a summary and tag it #important", and the agent performs the edits.

### Phase 3: Polish & Integration
*   **Goal:** Seamlessness and Reliability.
*   **Tasks:**
    *   **Error Handling:** Graceful failures (e.g., "Note already exists", "API rate limit").
    *   **UI Polish:** Loading states, markdown rendering in chat, code block syntax highlighting.
    *   **Context Awareness:** Allow agent to "see" the currently active file automatically.
    *   **Deliverable:** Production-ready plugin.

## 6. Measurable Outcomes
1.  **Request Accuracy:** Test suite of 50 common natural language commands (creation, linking, editing) with >95% success rate.
2.  **Performance:** "Time to First Action" < 1s (local processing) or < 3s (API roundtrip).
3.  **Integration:** Zero external dependencies required (node_modules bundled).

## 7. Next Steps
1.  Initialize the repository structure.
2.  Install development dependencies (`npm`, `typescript`, `esbuild`).
3.  Begin Phase 1 Implementation.
