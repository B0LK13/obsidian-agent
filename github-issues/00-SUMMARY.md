# Issues Summary

**Total Issues:** 65

## By Milestone


### Foundation (2 issues)

1. **FEAT: Implement Incremental Indexing Mechanism** - Labels: feature,priority:high,performance
2. **FEAT: Implement Vector Database Layer for Semantic Search** - Labels: feature,priority:high,enhancement

### Week 1 (9 issues)

1. **W1/UI: Task List Page (tasks + status)** - Labels: week:1,service:UI,priority:P0
2. **W1/UI: Create Task Modal (prompt + optional project placeholder)** - Labels: week:1,service:UI,priority:P0
3. **W1/UI: Task Detail Skeleton (Timeline/Outputs/Files tabs)** - Labels: week:1,service:UI,priority:P0
4. **W1/Orchestrator: DB Schema for Task + TaskEvent + Artifact + SandboxRef** - Labels: week:1,service:Orchestrator,priority:P0
5. **W1/Orchestrator: Task Lifecycle State Machine (CREATED→...→COMPLETED)** - Labels: week:1,service:Orchestrator,priority:P0
6. **W1/Orchestrator: Task API (POST /tasks, GET /tasks, GET /tasks/:id)** - Labels: week:1,service:Orchestrator,priority:P0
7. **W1/Orchestrator: Runner Worker Stub (advance states)** - Labels: week:1,service:Orchestrator,priority:P0
8. **W1/Sandbox: Define Sandbox Service Interface Contract** - Labels: week:1,service:Sandbox,priority:P0
9. **W1/Artifacts: Artifact Metadata Schema + Registration Helper** - Labels: week:1,service:Artifacts,priority:P0

### Week 2 (9 issues)

1. **REFACTOR: Separate Concerns in Indexing Module** - Labels: refactor,priority:high,architecture
2. **REFACTOR: Implement Asynchronous Processing for Long-Running Operations** - Labels: refactor,priority:high,async
3. **W2/UI: Timeline View Rendering from TaskEvents** - Labels: week:2,service:UI,priority:P0
4. **W2/UI: Cancel Task Button (wired)** - Labels: week:2,service:UI,priority:P0
5. **W2/Orchestrator: Tool Router + TaskEvent Emission** - Labels: week:2,service:Orchestrator,priority:P0
6. **W2/Orchestrator: Cancel Endpoint + Worker Interrupt** - Labels: week:2,service:Orchestrator,priority:P0
7. **W2/Orchestrator: Task Timeout Policy (global + per task)** - Labels: week:2,service:Orchestrator,priority:P0
8. **W2/Sandbox: Simulated Workspace Adapter (local temp dir per task)** - Labels: week:2,service:Sandbox,priority:P0
9. **W2/Artifacts: ZIP Artifact Creation from Simulated Workspace** - Labels: week:2,service:Artifacts,priority:P0

### Week 3 (8 issues)

1. **FEAT: Implement Dead Link Detection and Repair** - Labels: feature,priority:high,reliability
2. **ENHANCEMENT: Improve Note Ingestion and Indexing Reliability** - Labels: enhancement,priority:medium,reliability
3. **W3/UI: Files Tab (list files + metadata)** - Labels: week:3,service:UI,priority:P0
4. **W3/UI: Download All Files (ZIP) CTA** - Labels: week:3,service:UI,priority:P0
5. **W3/Orchestrator: Integrate Real Sandbox Service (replace simulated)** - Labels: week:3,service:Orchestrator,priority:P0
6. **W3/Orchestrator: Persist SandboxRef on Task** - Labels: week:3,service:Orchestrator,priority:P0
7. **W3/Sandbox: Container Image + Runtime (filesystem tooling)** - Labels: week:3,service:Sandbox,priority:P0
8. **W3/Artifacts: ZIP Creation from Sandbox Workspace** - Labels: week:3,service:Artifacts,priority:P0

### Week 4 (7 issues)

1. **FEAT: Implement Automated Link Suggestions** - Labels: feature,priority:high,ml
2. **W4/UI: Timeline Shows Visited URLs + Extracted Preview** - Labels: week:4,service:UI,priority:P0
3. **W4/UI: Sources/Evidence Section on Task Detail** - Labels: week:4,service:UI,priority:P1
4. **W4/Orchestrator: Add browser.* Tools to Router** - Labels: week:4,service:Orchestrator,priority:P0
5. **W4/Orchestrator: Redaction Hooks for Logs (secrets)** - Labels: week:4,service:Orchestrator,priority:P0
6. **W4/Sandbox: Playwright Integration in Sandbox Image** - Labels: week:4,service:Sandbox,priority:P0
7. **W4/Artifacts: Register report.md / report.html as Artifacts** - Labels: week:4,service:Artifacts,priority:P1

### Week 5 (9 issues)

1. **FEAT: Implement Caching and Optimization Layer** - Labels: feature,priority:high,performance
2. **ENHANCEMENT: Improve Search Algorithm Efficiency** - Labels: enhancement,priority:medium,performance
3. **W5/UI: Outputs Panel with Artifact Cards** - Labels: week:5,service:UI,priority:P0
4. **W5/UI: Safe HTML Report Preview Renderer** - Labels: week:5,service:UI,priority:P1
5. **W5/Orchestrator: Define Done Contract + Completion Gating** - Labels: week:5,service:Orchestrator,priority:P0
6. **W5/Orchestrator: Stop Conditions + Loop Safeguards** - Labels: week:5,service:Orchestrator,priority:P0
7. **W5/Sandbox: Export Helper (md→html) or Consistent Paths** - Labels: week:5,service:Sandbox,priority:P1
8. **W5/Artifacts: Artifact Storage (object store) + Durable Links** - Labels: week:5,service:Artifacts,priority:P0
9. **W5/Artifacts: Preview Pipeline (report.md→report.html)** - Labels: week:5,service:Artifacts,priority:P1

### Week 6 (9 issues)

1. **FEAT: Implement Knowledge Graph Visualization** - Labels: feature,priority:high,visualization
2. **W6/UI: Projects List + Create/Edit (name + master instruction)** - Labels: week:6,service:UI,priority:P1
3. **W6/UI: Project KB Upload + List** - Labels: week:6,service:UI,priority:P1
4. **W6/UI: Create Task Inside Project Flow** - Labels: week:6,service:UI,priority:P1
5. **W6/Orchestrator: Project Model + CRUD API** - Labels: week:6,service:Orchestrator,priority:P1
6. **W6/Orchestrator: Task Context Resolution (project master instruction snapshot)** - Labels: week:6,service:Orchestrator,priority:P1
7. **W6/Orchestrator: Project KB File Attachment into Sandbox Bootstrap** - Labels: week:6,service:Orchestrator,priority:P1
8. **W6/Sandbox: Workspace Bootstrap Step for KB Files** - Labels: week:6,service:Sandbox,priority:P1
9. **W6/Artifacts: Reuse Storage Primitives for KB Uploads** - Labels: week:6,service:Artifacts,priority:P1

### Week 7 (8 issues)

1. **REFACTOR: Implement Defensive Coding and Error Handling Improvements** - Labels: refactor,priority:high,reliability
2. **W7/UI: Download Trace JSON Button** - Labels: week:7,service:UI,priority:P0
3. **W7/UI: Improved Error States + Retry Hints** - Labels: week:7,service:UI,priority:P1
4. **W7/Orchestrator: Trace Export Endpoint** - Labels: week:7,service:Orchestrator,priority:P0
5. **W7/Orchestrator: Idempotency Key for Task Creation** - Labels: week:7,service:Orchestrator,priority:P1
6. **W7/Orchestrator: Developer API Key Auth + /v1/tasks Endpoints** - Labels: week:7,service:Orchestrator,priority:P1
7. **W7/Sandbox: Cleanup Reliability on Cancel/Fail** - Labels: week:7,service:Sandbox,priority:P0
8. **W7/Artifacts: Signed URLs / Proxied Downloads with Expiry** - Labels: week:7,service:Artifacts,priority:P0

### Week 8 (4 issues)

1. **W8/Orchestrator: Webhooks (task.completed, task.failed) [optional]** - Labels: week:8,service:Orchestrator,priority:P2
2. **W8/Sandbox: Idle Detection + Stop [optional]** - Labels: week:8,service:Sandbox,priority:P2
3. **W8/UI: Stability Polish + Bug Bash Checklist** - Labels: week:8,service:UI,priority:P1
4. **W8/Artifacts: Webhook Delivery Logs [optional]** - Labels: week:8,service:Artifacts,priority:P2


---

## Quick Start

### Option 1: Manual Creation
1. Navigate through the milestone folders
2. Open each .md file
3. Follow the instructions in each file to create the issue on GitHub

### Option 2: GitHub CLI (Recommended)
```bash
# Install GitHub CLI from https://cli.github.com/
gh auth login
# Then run the PowerShell setup script
```

### Option 3: GitHub API (This Script)
```bash
# Set your GitHub token
export GITHUB_TOKEN=your_token_here
export GITHUB_REPO=username/repo

# Run with API mode
python create-github-issues.py --api
```

---

## Labels to Create First

Create these labels in your GitHub repository before creating issues:

**Priority Labels:**
- `priority:high` (red: #d73a4a)
- `priority:medium` (yellow: #fbca04)
- `priority:low` (green: #0e8a16)
- `priority:P0` (dark red: #b60205)
- `priority:P1` (red: #d93f0b)
- `priority:P2` (yellow: #fbca04)

**Week Labels:**
- `week:1` through `week:8` (blue: #1d76db)

**Service Labels:**
- `service:UI` (light blue: #c5def5)
- `service:Orchestrator` (light blue: #c5def5)
- `service:Sandbox` (light blue: #c5def5)
- `service:Artifacts` (light blue: #c5def5)

**Type Labels:**
- `feature` (green: #0e8a16)
- `enhancement` (light blue: #a2eeef)
- `refactor` (purple: #d4c5f9)

**Category Labels:**
- `performance`, `reliability`, `ml`, `visualization`, `architecture`, `async`

---

## Milestones to Create

1. **Foundation** - Core PKM-Agent improvements and foundation
2. **Week 1** - Foundation - Task infrastructure
3. **Week 2** - Core Workflow - Events and cancellation
4. **Week 3** - Sandbox Integration
5. **Week 4** - Browser Tools
6. **Week 5** - Outputs & Completion
7. **Week 6** - Projects & Knowledge Base
8. **Week 7** - API & Export
9. **Week 8** - Polish & Webhooks

