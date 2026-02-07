# 💾 Long-Term Memory

The agent now has a "Memory" that persists across sessions. This allows it to learn about you, your preferences, and your work.

## 🧠 How it Works
When you ask a question using `Ask Agent (Auto)`, the system performs two searches:
1. **Memory Search:** Finds relevant facts about YOU.
2. **Vault Search:** Finds relevant notes in your vault.

## 📝 How to Save Memories
You can explicitly tell the agent to remember something:
- **Command:** `Ask Agent (Auto)`
- **Input:** "Remember that I prefer to write in a professional but concise tone."
- **Input:** "Remember that my main focus this week is finishing the Obsidian Plugin."

## 🧹 Managing Memory
Your memories are stored in a dedicated file:
- **Path:** `.obsidian/plugins/obsidian-agent/memory_store.json`
- To clear memories, you can use the internal clear method or manually delete this file.
