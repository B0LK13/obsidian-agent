# Project TODO List

**Last Updated:** 2026-01-17  
**Project:** B0LK13v2 (PKM-Agent System)

---

## Table of Contents
- [PKM-Agent System Improvements](#pkm-agent-system-improvements)
  - [Priority 1 (P1) - Critical Features](#priority-1-p1---critical-features)
  - [Priority 2 (P2) - High Priority](#priority-2-p2---high-priority)
  - [Priority 3 (P3) - Medium Priority](#priority-3-p3---medium-priority)
- [Development Sprint Plan (W1-W8)](#development-sprint-plan-w1-w8)
  - [Week 1: Foundation](#week-1-foundation)
  - [Week 2: Core Workflow](#week-2-core-workflow)
  - [Week 3: Sandbox Integration](#week-3-sandbox-integration)
  - [Week 4: Browser Tools](#week-4-browser-tools)
  - [Week 5: Outputs & Completion](#week-5-outputs--completion)
  - [Week 6: Projects & Knowledge Base](#week-6-projects--knowledge-base)
  - [Week 7: API & Export](#week-7-api--export)
  - [Week 8: Polish & Webhooks](#week-8-polish--webhooks)

---

## PKM-Agent System Improvements

### Priority 1 (P1) - Critical Features

#### 🔥 FEAT: Implement Incremental Indexing Mechanism
**Labels:** `feature`, `priority:high`, `performance`

**Problem Statement:**  
The current indexing approach performs full re-indexing of the entire knowledge base on each update, resulting in poor performance, especially with large knowledge bases containing thousands of notes.

**Proposed Solution:**  
Implement an incremental indexing mechanism that tracks changes to notes (additions, modifications, deletions) and updates the index incrementally based on these changes, rather than performing full re-indexing on each update.

**Acceptance Criteria:**
1. ✅ The incremental indexing mechanism should process updates to 1000 notes within 10 seconds
2. ✅ Maintain index consistency with a correctness rate of at least 99.9% based on manual validation
3. ✅ Reduce average indexing time for subsequent updates by at least 80% compared to full re-indexing
4. ✅ Memory footprint should remain under 100MB during indexing operations

**Status:** 🔴 Not Started  
**Milestone:** Foundation

---

#### 🔥 FEAT: Implement Vector Database Layer for Semantic Search
**Labels:** `feature`, `priority:high`, `enhancement`

**Problem Statement:**  
The current search mechanism relies on traditional keyword-based search, which may not effectively capture the semantic relationships and contextual meaning of the content in the knowledge base.

**Proposed Solution:**  
Implement a vector database layer that converts the content of notes into vector embeddings using a pre-trained language model, and enables semantic search capabilities that can retrieve relevant notes based on the semantic similarity of their content, rather than just keyword matching.

**Acceptance Criteria:**
1. ✅ Generate vector embeddings for 1000 notes within 60 seconds
2. ✅ Provide semantic search results with a relevance score of at least 0.8 (on a scale of 0 to 1) for at least 80% of search queries
3. ✅ Memory footprint should remain under 500MB
4. ✅ Integrate seamlessly with existing search interface and functionality

**Status:** 🔴 Not Started  
**Milestone:** Foundation

---

#### 🔥 FEAT: Implement Automated Link Suggestions
**Labels:** `feature`, `priority:high`, `ml`

**Problem Statement:**  
The current system lacks the ability to automatically suggest relevant links between notes based on semantic similarity or shared concepts.

**Proposed Solution:**  
Implement a machine learning-based link suggestion engine that analyzes the content of notes and suggests relevant connections based on semantic relationships, shared keywords, or conceptual overlap.

**Acceptance Criteria:**
1. ✅ Suggest at least 5 relevant links for any given note
2. ✅ Achieve accuracy rate of at least 80% based on manual validation
3. ✅ Integrate seamlessly with existing note editing interface
4. ✅ Provide real-time link suggestions as user types or edits a note

**Status:** 🔴 Not Started  
**Milestone:** Week 4

---

#### 🔥 FEAT: Implement Dead Link Detection and Repair
**Labels:** `feature`, `priority:high`, `reliability`

**Problem Statement:**  
The current system lacks the ability to automatically detect and report broken internal links within the knowledge base.

**Proposed Solution:**  
Implement a link validation and repair mechanism that scans all internal links in the knowledge base, identifies broken or invalid links, and provides suggestions for repairing or updating these links.

**Acceptance Criteria:**
1. ✅ Detect at least 90% of broken internal links in a test knowledge base containing 1000 notes with 5000 internal links
2. ✅ Provide accurate repair suggestions for at least 80% of detected broken links
3. ✅ Integrate seamlessly with existing note editing and management interface
4. ✅ Run validation in background without blocking user interface

**Status:** 🔴 Not Started  
**Milestone:** Week 3

---

### Priority 2 (P2) - High Priority

#### ⚡ FEAT: Implement Caching and Optimization Layer
**Labels:** `feature`, `priority:high`, `performance`

**Problem Statement:**  
The current system lacks efficient caching mechanisms for frequently accessed notes, search results, and knowledge graphs, resulting in unnecessary disk I/O operations and increased latency for common user interactions.

**Proposed Solution:**  
Implement a caching and optimization layer that provides in-memory caching for frequently accessed notes, search results, and knowledge graphs, and employs various optimization techniques such as lazy loading, prefetching, and batch processing to minimize disk I/O operations.

**Acceptance Criteria:**
1. ✅ Cache at least 1000 frequently accessed notes within 10 seconds
2. ✅ Achieve cache hit rate of at least 80% for subsequent accesses to same notes
3. ✅ Reduce average latency for common user interactions by at least 50%
4. ✅ Implement intelligent cache eviction policy

**Status:** 🔴 Not Started  
**Milestone:** Week 5

---

#### ⚡ FEAT: Implement Knowledge Graph Visualization
**Labels:** `feature`, `priority:high`, `visualization`

**Problem Statement:**  
The current system lacks the ability to visualize the relationships and connections between notes in the knowledge base as an interactive knowledge graph.

**Proposed Solution:**  
Implement a knowledge graph visualization component that represents notes as nodes and their relationships as edges, allowing users to explore the structure and connections of their knowledge base in an intuitive and interactive manner.

**Acceptance Criteria:**
1. ✅ Render a knowledge base containing 1000 notes and 5000 relationships within 5 seconds
2. ✅ Provide smooth interactive performance with panning, zooming, and node selection features
3. ✅ Integrate seamlessly with existing note editing and management interface
4. ✅ Support different visualization layouts (force-directed, hierarchical, radial)

**Status:** 🔴 Not Started  
**Milestone:** Week 6

---

#### ⚡ REFACTOR: Separate Concerns in Indexing Module
**Labels:** `refactor`, `priority:high`, `architecture`

**Problem Statement:**  
The current indexing module mixes file system operations, data parsing, and index construction logic within the same module, resulting in a monolithic and difficult-to-maintain structure.

**Proposed Solution:**  
Refactor the indexing module to separate the concerns of file system operations, data parsing, and index construction into distinct, well-defined modules or classes, each responsible for a specific aspect of the indexing process.

**Acceptance Criteria:**
1. ✅ Refactored module consists of at least 3 distinct, well-defined modules/classes
2. ✅ Clear interfaces and dependencies between modules
3. ✅ Process indexing of 1000 notes within same time frame as current system
4. ✅ Improved code maintainability and testability (measured by test coverage increase)

**Status:** 🔴 Not Started  
**Milestone:** Week 2

---

#### ⚡ REFACTOR: Implement Asynchronous Processing for Long-Running Operations
**Labels:** `refactor`, `priority:high`, `async`

**Problem Statement:**  
The current system performs long-running operations (such as full re-indexing or generating vector embeddings) synchronously, blocking the user interface and preventing users from performing other tasks.

**Proposed Solution:**  
Refactor the system to implement asynchronous processing for long-running operations, using modern asynchronous programming techniques (async/await, Promises, or observables) to perform these operations in the background without blocking the UI.

**Acceptance Criteria:**
1. ✅ Perform long-running operations asynchronously without blocking UI
2. ✅ Provide progress feedback and completion notifications
3. ✅ Maintain same level of functionality and performance
4. ✅ Support cancellation of in-progress operations

**Status:** 🔴 Not Started  
**Milestone:** Week 2

---

#### ⚡ REFACTOR: Implement Defensive Coding and Error Handling Improvements
**Labels:** `refactor`, `priority:high`, `reliability`

**Problem Statement:**  
The current system lacks robust defensive coding practices and comprehensive error handling mechanisms, resulting in potential crashes, data corruption, or unexpected behavior when encountering edge cases.

**Proposed Solution:**  
Refactor the system to implement robust defensive coding practices and comprehensive error handling mechanisms throughout the codebase, including input validation, boundary checking, null pointer checks, and proper error propagation and recovery strategies.

**Acceptance Criteria:**
1. ✅ Implement comprehensive input validation throughout codebase
2. ✅ Add boundary checking and null pointer checks
3. ✅ Gracefully handle edge cases without crashing or corrupting data
4. ✅ Maintain same level of functionality and performance
5. ✅ All error paths tested with unit tests

**Status:** 🔴 Not Started  
**Milestone:** Week 7

---

### Priority 3 (P3) - Medium Priority

#### 📋 ENHANCEMENT: Improve Search Algorithm Efficiency
**Labels:** `enhancement`, `priority:medium`, `performance`

**Problem Statement:**  
The current search algorithm may not be optimized for efficiency, potentially resulting in slow search response times when searching large knowledge bases.

**Proposed Solution:**  
Enhance the search algorithm to improve efficiency by implementing advanced data structures (inverted indexes, trie structures), optimizing query parsing and execution, implementing caching for frequent queries, and exploring advanced search techniques (fuzzy searching, synonym expansion).

**Acceptance Criteria:**
1. ✅ Reduce average search response times by at least 30% for large knowledge bases (1000+ notes)
2. ✅ Maintain or improve search accuracy and relevance
3. ✅ Integrate seamlessly with existing search interface

**Status:** 🔴 Not Started  
**Milestone:** Week 5

---

#### 📋 ENHANCEMENT: Improve Note Ingestion and Indexing Reliability
**Labels:** `enhancement`, `priority:medium`, `reliability`

**Problem Statement:**  
The current note ingestion and indexing mechanism may not be fully reliable, potentially resulting in missed notes, incomplete indexing, or data inconsistencies.

**Proposed Solution:**  
Enhance the note ingestion and indexing mechanism by implementing robust file system monitoring, improving error handling for file parsing, implementing validation and consistency checks, and exploring advanced indexing techniques.

**Acceptance Criteria:**
1. ✅ Reduce rate of missed notes, incomplete indexing, or data inconsistencies by at least 50%
2. ✅ Handle diverse file formats and structures reliably
3. ✅ Integrate seamlessly with existing ingestion and indexing pipeline

**Status:** 🔴 Not Started  
**Milestone:** Week 3

---

## Development Sprint Plan (W1-W8)

### Week 1: Foundation

#### W1/UI: Task List Page (tasks + status)
**Labels:** `week:1`, `service:UI`, `priority:P0`

**Description:**  
Build Task List page: display tasks, status, created_at; link to task detail.

**Acceptance Criteria:**
- ✅ Renders list from API
- ✅ Handles empty/loading/error states

**Dependencies:** Orchestrator GET /tasks  
**Status:** 🔴 Not Started

---

#### W1/UI: Create Task Modal (prompt + optional project placeholder)
**Labels:** `week:1`, `service:UI`, `priority:P0`

**Description:**  
Create Task modal with prompt input and submit.

**Acceptance Criteria:**
- ✅ Calls POST /tasks
- ✅ Navigates to task detail
- ✅ Validates empty prompt

**Dependencies:** Orchestrator POST /tasks  
**Status:** 🔴 Not Started

---

#### W1/UI: Task Detail Skeleton (Timeline/Outputs/Files tabs)
**Labels:** `week:1`, `service:UI`, `priority:P0`

**Description:**  
Task detail page shell with three tabs and empty states.

**Acceptance Criteria:**
- ✅ Route /tasks/:id loads basic task header
- ✅ Tabs switch without breaking

**Dependencies:** GET /tasks/:id  
**Status:** 🔴 Not Started

---

#### W1/Orchestrator: DB Schema for Task + TaskEvent + Artifact + SandboxRef
**Labels:** `week:1`, `service:Orchestrator`, `priority:P0`

**Description:**  
Add migrations/models for Task, TaskEvent (timeline), Artifact, SandboxRef.

**Acceptance Criteria:**
- ✅ Migrations run successfully
- ✅ CRUD works in dev
- ✅ Indexes on task_id & created_at

**Status:** 🔴 Not Started

---

#### W1/Orchestrator: Task Lifecycle State Machine (CREATED→...→COMPLETED)
**Labels:** `week:1`, `service:Orchestrator`, `priority:P0`

**Description:**  
Implement task states and transitions: CREATED, PLANNING, EXECUTING, DELIVERING, COMPLETED + FAILED, CANCELLED.

**Acceptance Criteria:**
- ✅ Transitions validated
- ✅ State change creates TaskEvent entry

**Status:** 🔴 Not Started

---

#### W1/Orchestrator: Task API (POST /tasks, GET /tasks, GET /tasks/:id)
**Labels:** `week:1`, `service:Orchestrator`, `priority:P0`

**Description:**  
Implement endpoints for UI.

**Acceptance Criteria:**
- ✅ POST creates task
- ✅ GET list paginated
- ✅ GET single returns state, timestamps, sandbox ref, artifacts summary

**Status:** 🔴 Not Started

---

#### W1/Orchestrator: Runner Worker Stub (advance states)
**Labels:** `week:1`, `service:Orchestrator`, `priority:P0`

**Description:**  
Add background worker that picks tasks and advances state with stubbed behavior.

**Acceptance Criteria:**
- ✅ Task moves CREATED→PLANNING→EXECUTING→DELIVERING→COMPLETED in dev
- ✅ Emits events

**Status:** 🔴 Not Started

---

#### W1/Sandbox: Define Sandbox Service Interface Contract
**Labels:** `week:1`, `service:Sandbox`, `priority:P0`

**Description:**  
Create code-level interface: createSandbox/destroySandbox + execTool + listFiles.

**Acceptance Criteria:**
- ✅ Orchestrator compiles against interface
- ✅ Default adapter returns structured NotImplemented errors

**Status:** 🔴 Not Started

---

#### W1/Artifacts: Artifact Metadata Schema + Registration Helper
**Labels:** `week:1`, `service:Artifacts`, `priority:P0`

**Description:**  
Implement artifact model and helper function registerArtifact(task_id,...).

**Acceptance Criteria:**
- ✅ Artifacts can be recorded for a task
- ✅ Visible in GET /tasks/:id

**Status:** 🔴 Not Started

---

### Week 2: Core Workflow

#### W2/UI: Timeline View Rendering from TaskEvents
**Labels:** `week:2`, `service:UI`, `priority:P0`

**Description:**  
Render chronological timeline from TaskEvents.

**Acceptance Criteria:**
- ✅ Polling or SSE
- ✅ Step cards show tool_name/status/duration
- ✅ Detail drawer shows JSON

**Dependencies:** GET /tasks/:id/events or embed events  
**Status:** 🔴 Not Started

---

#### W2/UI: Cancel Task Button (wired)
**Labels:** `week:2`, `service:UI`, `priority:P0`

**Description:**  
Add cancel CTA.

**Acceptance Criteria:**
- ✅ Calls POST /tasks/:id/cancel
- ✅ UI reflects CANCELLED
- ✅ Disables further actions

**Dependencies:** Cancel endpoint  
**Status:** 🔴 Not Started

---

#### W2/Orchestrator: Tool Router + TaskEvent Emission
**Labels:** `week:2`, `service:Orchestrator`, `priority:P0`

**Description:**  
Implement tool router: tool call in/out logged as TaskEvent with step_id.

**Acceptance Criteria:**
- ✅ Every tool call produces start+end events
- ✅ Errors captured

**Status:** 🔴 Not Started

---

#### W2/Orchestrator: Cancel Endpoint + Worker Interrupt
**Labels:** `week:2`, `service:Orchestrator`, `priority:P0`

**Description:**  
POST /tasks/:id/cancel transitions state and interrupts execution.

**Acceptance Criteria:**
- ✅ Sandbox teardown called if active
- ✅ No further tool calls happen

**Dependencies:** Worker signal mechanism  
**Status:** 🔴 Not Started

---

#### W2/Orchestrator: Task Timeout Policy (global + per task)
**Labels:** `week:2`, `service:Orchestrator`, `priority:P0`

**Description:**  
Add config timeout; enforce in worker.

**Acceptance Criteria:**
- ✅ Tasks exceeding time stop
- ✅ Set FAILED or CANCELLED(reason=timeout)
- ✅ Partial artifacts preserved

**Status:** 🔴 Not Started

---

#### W2/Sandbox: Simulated Workspace Adapter (local temp dir per task)
**Labels:** `week:2`, `service:Sandbox`, `priority:P0`

**Description:**  
Implement simulated sandbox adapter with filesystem.write/list/zip using local temp dirs.

**Acceptance Criteria:**
- ✅ Enables E2E run without real sandbox

**Status:** 🔴 Not Started

---

#### W2/Artifacts: ZIP Artifact Creation from Simulated Workspace
**Labels:** `week:2`, `service:Artifacts`, `priority:P0`

**Description:**  
Create ZIP from simulated workspace; store as artifact.

**Acceptance Criteria:**
- ✅ Outputs panel can download ZIP
- ✅ Integrity check passes

**Status:** 🔴 Not Started

---

### Week 3: Sandbox Integration

#### W3/UI: Files Tab (list files + metadata)
**Labels:** `week:3`, `service:UI`, `priority:P0`

**Description:**  
Implement Files tab showing name/size/mtime; refresh.

**Acceptance Criteria:**
- ✅ Shows workspace files
- ✅ Handles empty state

**Dependencies:** filesystem.list  
**Status:** 🔴 Not Started

---

#### W3/UI: Download All Files (ZIP) CTA
**Labels:** `week:3`, `service:UI`, `priority:P0`

**Description:**  
Button triggers ZIP generation/download.

**Acceptance Criteria:**
- ✅ Returns ZIP artifact
- ✅ Button disabled while generating

**Dependencies:** filesystem.zip + artifact store  
**Status:** 🔴 Not Started

---

#### W3/Orchestrator: Integrate Real Sandbox Service (replace simulated)
**Labels:** `week:3`, `service:Orchestrator`, `priority:P0`

**Description:**  
Switch adapter to real Sandbox service calls for filesystem tools.

**Acceptance Criteria:**
- ✅ Tasks run using sandbox
- ✅ Events reflect sandbox tool calls

**Status:** 🔴 Not Started

---

#### W3/Orchestrator: Persist SandboxRef on Task
**Labels:** `week:3`, `service:Orchestrator`, `priority:P0`

**Description:**  
Store sandbox_id/status in DB and expose in GET /tasks/:id.

**Acceptance Criteria:**
- ✅ Sandbox ref visible
- ✅ Status updates on create/destroy

**Status:** 🔴 Not Started

---

#### W3/Sandbox: Container Image + Runtime (filesystem tooling)
**Labels:** `week:3`, `service:Sandbox`, `priority:P0`

**Description:**  
Build sandbox container image with zip + runtimes. Implement create/destroy and filesystem endpoints.

**Acceptance Criteria:**
- ✅ Provision <60s
- ✅ Isolated per task
- ✅ Resource limits set

**Status:** 🔴 Not Started

---

#### W3/Artifacts: ZIP Creation from Sandbox Workspace
**Labels:** `week:3`, `service:Artifacts`, `priority:P0`

**Description:**  
Generate ZIP by pulling from sandbox volume or via endpoint.

**Acceptance Criteria:**
- ✅ Stable download link
- ✅ Artifact metadata recorded

**Status:** 🔴 Not Started

---

### Week 4: Browser Tools

#### W4/UI: Timeline Shows Visited URLs + Extracted Preview
**Labels:** `week:4`, `service:UI`, `priority:P0`

**Description:**  
Enhance timeline cards for browser tools.

**Acceptance Criteria:**
- ✅ URL displayed
- ✅ Extracted text preview truncated
- ✅ Errors visible

**Status:** 🔴 Not Started

---

#### W4/UI: Sources/Evidence Section on Task Detail
**Labels:** `week:4`, `service:UI`, `priority:P1`

**Description:**  
Add evidence list derived from browser events.

**Acceptance Criteria:**
- ✅ Shows unique URLs used
- ✅ Link out opens in new tab

**Status:** 🔴 Not Started

---

#### W4/Orchestrator: Add browser.* Tools to Router
**Labels:** `week:4`, `service:Orchestrator`, `priority:P0`

**Description:**  
Implement browser.navigate/extract_text/download tools.

**Acceptance Criteria:**
- ✅ Tool calls logged
- ✅ Retry policy for transient failures

**Status:** 🔴 Not Started

---

#### W4/Orchestrator: Redaction Hooks for Logs (secrets)
**Labels:** `week:4`, `service:Orchestrator`, `priority:P0`

**Description:**  
Implement redaction policy for tool inputs/outputs.

**Acceptance Criteria:**
- ✅ Secrets not stored in TaskEvents
- ✅ Configurable fields

**Status:** 🔴 Not Started

---

#### W4/Sandbox: Playwright Integration in Sandbox Image
**Labels:** `week:4`, `service:Sandbox`, `priority:P0`

**Description:**  
Install/config Playwright. Implement endpoints for navigate/extract_text/download.

**Acceptance Criteria:**
- ✅ Can visit a URL
- ✅ Extract body text
- ✅ Download to workspace path

**Status:** 🔴 Not Started

---

#### W4/Artifacts: Register report.md / report.html as Artifacts
**Labels:** `week:4`, `service:Artifacts`, `priority:P1`

**Description:**  
Define artifact types for report outputs and register them when generated.

**Acceptance Criteria:**
- ✅ Outputs panel shows reports
- ✅ Downloads work

**Status:** 🔴 Not Started

---

### Week 5: Outputs & Completion

#### W5/UI: Outputs Panel with Artifact Cards
**Labels:** `week:5`, `service:UI`, `priority:P0`

**Description:**  
Implement Outputs tab: list artifacts with type/size/download.

**Acceptance Criteria:**
- ✅ Live updates when artifacts appear

**Status:** 🔴 Not Started

---

#### W5/UI: Safe HTML Report Preview Renderer
**Labels:** `week:5`, `service:UI`, `priority:P1`

**Description:**  
Render report.html in UI with sanitization.

**Acceptance Criteria:**
- ✅ No script execution
- ✅ Supports basic formatting

**Status:** 🔴 Not Started

---

#### W5/Orchestrator: Define "Done" Contract + Completion Gating
**Labels:** `week:5`, `service:Orchestrator`, `priority:P0`

**Description:**  
Task completes only when artifact exists or explicit no-artifact.

**Acceptance Criteria:**
- ✅ Prevents premature completion
- ✅ Produces final summary with links

**Status:** 🔴 Not Started

---

#### W5/Orchestrator: Stop Conditions + Loop Safeguards
**Labels:** `week:5`, `service:Orchestrator`, `priority:P0`

**Description:**  
Implement max steps/tool calls; prevent infinite loops.

**Acceptance Criteria:**
- ✅ Terminates with FAILED(reason=max_steps) and logs

**Status:** 🔴 Not Started

---

#### W5/Sandbox: Export Helper (md→html) or Consistent Paths
**Labels:** `week:5`, `service:Sandbox`, `priority:P1`

**Description:**  
Implement markdown-to-html conversion in sandbox OR guarantee stable paths.

**Acceptance Criteria:**
- ✅ Report generated deterministically at /workspace/report.md

**Status:** 🔴 Not Started

---

#### W5/Artifacts: Artifact Storage (object store) + Durable Links
**Labels:** `week:5`, `service:Artifacts`, `priority:P0`

**Description:**  
Integrate object storage and signed/proxied downloads.

**Acceptance Criteria:**
- ✅ Downloads stable
- ✅ Metadata persisted
- ✅ Access control enforced

**Status:** 🔴 Not Started

---

#### W5/Artifacts: Preview Pipeline (report.md→report.html)
**Labels:** `week:5`, `service:Artifacts`, `priority:P1`

**Description:**  
Auto-generate report.html when report.md exists and register both.

**Acceptance Criteria:**
- ✅ Preview available <30s after md creation

**Status:** 🔴 Not Started

---

### Week 6: Projects & Knowledge Base

#### W6/UI: Projects List + Create/Edit (name + master instruction)
**Labels:** `week:6`, `service:UI`, `priority:P1`

**Description:**  
Add Projects UI with CRUD.

**Acceptance Criteria:**
- ✅ Create/edit works
- ✅ List shows projects
- ✅ Link to project detail

**Status:** 🔴 Not Started

---

#### W6/UI: Project KB Upload + List
**Labels:** `week:6`, `service:UI`, `priority:P1`

**Description:**  
Upload KB files and display them.

**Acceptance Criteria:**
- ✅ Upload progress
- ✅ Delete option
- ✅ Size/type constraints visible

**Status:** 🔴 Not Started

---

#### W6/UI: Create Task Inside Project Flow
**Labels:** `week:6`, `service:UI`, `priority:P1`

**Description:**  
From project view, create a new task with project_id.

**Acceptance Criteria:**
- ✅ Task inherits project
- ✅ UI shows project badge

**Status:** 🔴 Not Started

---

#### W6/Orchestrator: Project Model + CRUD API
**Labels:** `week:6`, `service:Orchestrator`, `priority:P1`

**Description:**  
Implement Project schema + endpoints.

**Acceptance Criteria:**
- ✅ Can create/update/read/list projects
- ✅ Stored master_instruction

**Status:** 🔴 Not Started

---

#### W6/Orchestrator: Task Context Resolution (project master instruction snapshot)
**Labels:** `week:6`, `service:Orchestrator`, `priority:P1`

**Description:**  
On task creation/start, resolve and snapshot system context.

**Acceptance Criteria:**
- ✅ Changes to project apply to new tasks only

**Status:** 🔴 Not Started

---

#### W6/Orchestrator: Project KB File Attachment into Sandbox Bootstrap
**Labels:** `week:6`, `service:Orchestrator`, `priority:P1`

**Description:**  
Mount/copy KB files to /workspace/kb.

**Acceptance Criteria:**
- ✅ KB available for tool reads
- ✅ Read-only recommended

**Status:** 🔴 Not Started

---

#### W6/Sandbox: Workspace Bootstrap Step for KB Files
**Labels:** `week:6`, `service:Sandbox`, `priority:P1`

**Description:**  
Implement bootstrap routine in sandbox to place KB files.

**Acceptance Criteria:**
- ✅ KB files present for tasks in project

**Status:** 🔴 Not Started

---

#### W6/Artifacts: Reuse Storage Primitives for KB Uploads
**Labels:** `week:6`, `service:Artifacts`, `priority:P1`

**Description:**  
Use artifact storage/upload to store KB files and reference from project.

**Acceptance Criteria:**
- ✅ KB downloads possible
- ✅ Retention defined

**Status:** 🔴 Not Started

---

### Week 7: API & Export

#### W7/UI: Download Trace JSON Button
**Labels:** `week:7`, `service:UI`, `priority:P0`

**Description:**  
Add button to export trace JSON (events + plan + artifacts).

**Acceptance Criteria:**
- ✅ Downloads successfully
- ✅ Secrets redacted

**Status:** 🔴 Not Started

---

#### W7/UI: Improved Error States + Retry Hints
**Labels:** `week:7`, `service:UI`, `priority:P1`

**Description:**  
Polish UI errors for sandbox/browser failures.

**Acceptance Criteria:**
- ✅ Actionable messaging
- ✅ Show last failing step

**Status:** 🔴 Not Started

---

#### W7/Orchestrator: Trace Export Endpoint
**Labels:** `week:7`, `service:Orchestrator`, `priority:P0`

**Description:**  
Implement /tasks/:id/trace export.

**Acceptance Criteria:**
- ✅ Includes lifecycle, tool calls, sandbox id, artifacts
- ✅ Redacted secrets

**Status:** 🔴 Not Started

---

#### W7/Orchestrator: Idempotency Key for Task Creation
**Labels:** `week:7`, `service:Orchestrator`, `priority:P1`

**Description:**  
Support idempotency header.

**Acceptance Criteria:**
- ✅ Duplicate creates return same task_id within TTL

**Status:** 🔴 Not Started

---

#### W7/Orchestrator: Developer API Key Auth + /v1/tasks Endpoints
**Labels:** `week:7`, `service:Orchestrator`, `priority:P1`

**Description:**  
Implement API key auth and /v1/tasks create + get status/artifacts.

**Acceptance Criteria:**
- ✅ Basic rate limit
- ✅ Clear error codes

**Status:** 🔴 Not Started

---

#### W7/Sandbox: Cleanup Reliability on Cancel/Fail
**Labels:** `week:7`, `service:Sandbox`, `priority:P0`

**Description:**  
Ensure sandbox destroyed on task cancel/fail.

**Acceptance Criteria:**
- ✅ No leaked resources
- ✅ Audit logs show teardown

**Status:** 🔴 Not Started

---

#### W7/Artifacts: Signed URLs / Proxied Downloads with Expiry
**Labels:** `week:7`, `service:Artifacts`, `priority:P0`

**Description:**  
Implement secure downloads.

**Acceptance Criteria:**
- ✅ Unauthorized blocked
- ✅ URLs expire

**Status:** 🔴 Not Started

---

### Week 8: Polish & Webhooks

#### W8/Orchestrator: Webhooks (task.completed, task.failed) [optional]
**Labels:** `week:8`, `service:Orchestrator`, `priority:P2`

**Description:**  
Implement webhook registration and delivery with signatures and retries.

**Acceptance Criteria:**
- ✅ Verify signature
- ✅ DLQ after N failures

**Status:** 🔴 Not Started

---

#### W8/Sandbox: Idle Detection + Stop [optional]
**Labels:** `week:8`, `service:Sandbox`, `priority:P2`

**Description:**  
Implement idle timer and stop sandbox after N minutes.

**Acceptance Criteria:**
- ✅ Resources reclaimed
- ✅ Artifacts remain

**Status:** 🔴 Not Started

---

#### W8/UI: Stability Polish + Bug Bash Checklist
**Labels:** `week:8`, `service:UI`, `priority:P1`

**Description:**  
Week 8 reserved for bug bash; track top issues; polish progress indicators.

**Acceptance Criteria:**
- ✅ Critical bugs closed
- ✅ Demo script passes

**Status:** 🔴 Not Started

---

#### W8/Artifacts: Webhook Delivery Logs [optional]
**Labels:** `week:8`, `service:Artifacts`, `priority:P2`

**Description:**  
Store webhook delivery attempts.

**Acceptance Criteria:**
- ✅ Visible to operators
- ✅ Supports debugging

**Status:** 🔴 Not Started

---

## Progress Summary

### By Priority
- **P0 (Critical):** 0/44 completed (0%)
- **P1 (High):** 0/18 completed (0%)
- **P2 (Medium):** 0/3 completed (0%)
- **P3 (Low):** 0/2 completed (0%)

### By Week
- **Week 1:** 0/9 completed (0%)
- **Week 2:** 0/7 completed (0%)
- **Week 3:** 0/6 completed (0%)
- **Week 4:** 0/6 completed (0%)
- **Week 5:** 0/7 completed (0%)
- **Week 6:** 0/8 completed (0%)
- **Week 7:** 0/7 completed (0%)
- **Week 8:** 0/4 completed (0%)

### By Service
- **UI:** 0/19 completed (0%)
- **Orchestrator:** 0/27 completed (0%)
- **Sandbox:** 0/10 completed (0%)
- **Artifacts:** 0/11 completed (0%)

---

## Notes

### Error Handling Strategy
All components should implement:
1. **File System Errors:** Permission checking, file integrity validation, fallback mechanisms
2. **API/LLM Errors:** Timeout handling, rate limit management, malformed response handling
3. **Data Integrity:** Index-sync validation, metadata verification, transactional updates

### Performance Targets
- Indexing: 1000 notes in <10s
- Search: Response <2s
- Vector embeddings: 1000 notes in <60s
- Cache hit rate: >80%
- UI responsiveness: No blocking operations

### Testing Requirements
- Unit tests for all new features
- Integration tests for API endpoints
- E2E tests for critical user flows
- Performance benchmarks for optimization features

---

**Last Updated:** 2026-01-17  
**Total Items:** 67  
**Completed:** 0  
**In Progress:** 0  
**Not Started:** 67
