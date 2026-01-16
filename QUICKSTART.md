# Quick Start Guide

Get started with Obsidian Agent in 3 simple steps!

## Step 1: Install

### Option A: From Community Plugins (Recommended - Coming Soon)
1. Open Obsidian Settings
2. Go to Community Plugins → Browse
3. Search for "Obsidian Agent"
4. Click Install, then Enable

### Option B: Manual Installation
1. Download the [latest release](https://github.com/B0LK13/obsidian-agent/releases)
2. Extract `main.js`, `manifest.json`, and `styles.css` to:
   ```
   <your-vault>/.obsidian/plugins/obsidian-agent/
   ```
3. Reload Obsidian or restart
4. Enable in Settings → Community Plugins

## Step 2: Configure

1. Open Settings → Obsidian Agent
2. Choose your AI Provider:
   - **OpenAI**: Get API key from [platform.openai.com](https://platform.openai.com/api-keys)
   - **Anthropic**: Get API key from [console.anthropic.com](https://console.anthropic.com/)
   - **Custom API**: Use any OpenAI-compatible endpoint
3. Enter your API Key
4. (Optional) Adjust settings:
   - Model name (e.g., `gpt-4`, `claude-3-opus-20240229`)
   - Temperature (creativity level: 0 = focused, 1 = creative)
   - Max tokens (response length limit)

## Step 3: Use!

### Quick Commands (Press `Ctrl/Cmd + P` to open command palette)

1. **Ask AI Agent** - Chat with AI about your notes
   - Opens a dialog where you can ask anything
   - AI has context from your current note
   - Response inserted at cursor

2. **Generate Summary** - Auto-summarize text
   - Select text (or use entire note)
   - Run command
   - Summary appended to your note

3. **Expand Ideas** - Turn brief notes into detailed content
   - Select your bullet points or brief notes
   - Run command
   - Get expanded, detailed version

4. **Improve Writing** - Enhance clarity and grammar
   - Select text to improve
   - Run command
   - Text replaced with improved version

5. **Generate Outline** - Create structured outlines
   - Select a topic or title
   - Run command
   - Get a detailed outline

6. **Answer Question** - Ask about your note
   - Opens dialog to ask questions
   - AI uses note content as context
   - Answer inserted in note

## Example Workflow

1. **Taking Quick Notes**
   ```
   - Meeting with team
   - Discussed project timeline
   - Need to revise Q2 goals
   ```
   → Use "Expand Ideas" to get detailed notes

2. **Writing an Article**
   - Write rough draft
   - Select paragraphs and use "Improve Writing"
   - Use "Generate Summary" for TL;DR

3. **Research Notes**
   - Paste research content
   - Use "Ask AI Agent" to ask questions
   - Use "Generate Outline" to organize

## Tips

- 💡 **Context Awareness**: Enable in settings to let AI see your note
- 🔑 **API Costs**: Check your provider's pricing (usually $0.01-0.10 per request)
- ⚡ **Keyboard Shortcuts**: Assign custom shortcuts in Settings → Hotkeys
- 📝 **System Prompt**: Customize AI personality in plugin settings
- 🔒 **Privacy**: Your API key stays local, only you and your AI provider see your notes

## Troubleshooting

### "API key not configured" error
- Go to Settings → Obsidian Agent
- Enter your API key
- Save settings

### "Failed to generate completion" error
- Check your API key is valid
- Ensure you have API credits/quota remaining
- Verify internet connection
- Check console for detailed error (Ctrl/Cmd + Shift + I)

### Commands not appearing
- Make sure plugin is enabled in Community Plugins
- Try reloading Obsidian
- Check there are no plugin conflicts

## Need Help?

- 📖 [Full Documentation](README.md)
- 🐛 [Report Issues](https://github.com/B0LK13/obsidian-agent/issues)
- 💬 [Discussions](https://github.com/B0LK13/obsidian-agent/discussions)

Happy note-taking! 🎉
