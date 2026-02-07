# 🤖 The Agentic Brain (Auto Mode)

Unlike standard AI chat which just responds to your last message, the **Agentic Brain** can think, plan, and use tools to solve complex requests.

## ⚡ The "Ask Agent (Auto)" Command
This command triggers a **ReAct (Reason + Act) loop**. 

### Example Use Case:
**User Input:** "Find my notes on the marketing project and tell me what the next deadline is."

**Agent's Internal Process:**
1. **Thought:** I need to find notes related to 'marketing project'.
2. **Action:** `search_vault("marketing project")`
3. **Observation:** Found `Projects/Marketing/Q1_Plan.md`.
4. **Thought:** I should read that file to find deadlines.
5. **Action:** `read_note("Projects/Marketing/Q1_Plan.md")`
6. **Observation:** Note content mentions "Final Review: March 15th".
7. **Final Answer:** The next deadline for the marketing project is March 15th.

## 🛠️ Available Tools
- `search_vault`: Semantic search across all markdown files.
- `read_note`: Reads the full text of a specific file.
- `list_files`: Explores folders in your vault.
- `remember_fact`: Saves a fact to your long-term memory.
