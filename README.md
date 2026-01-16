# Obsidian Agent

AI-enhanced Obsidian Agent for intelligent note-taking, knowledge management, and content generation.

## Features

- 🤖 **AI-Powered Assistance**: Integrate powerful AI models (OpenAI, Anthropic, or custom) directly into your Obsidian workflow
- 📝 **Smart Commands**: Multiple built-in commands for common writing tasks
- 🔍 **Context-Aware**: Agent understands your current note context
- ⚙️ **Configurable**: Customize AI behavior, model selection, and parameters
- 🔐 **Secure**: Your API keys are stored locally

## Commands

The plugin provides the following commands (accessible via Command Palette - `Ctrl/Cmd + P`):

1. **Ask AI Agent**: Open a dialog to ask the AI anything about your current note
2. **Generate Summary**: Automatically summarize selected text or entire note
3. **Expand Ideas**: Take brief notes and expand them into detailed content
4. **Improve Writing**: Enhance clarity, grammar, and style of selected text
5. **Generate Outline**: Create a structured outline from a topic
6. **Answer Question Based on Note**: Ask questions about your note content

## Installation

### From Obsidian Community Plugins (Coming Soon)

1. Open Settings → Community Plugins
2. Search for "Obsidian Agent"
3. Click Install
4. Enable the plugin

### Manual Installation

1. Download the latest release from GitHub
2. Extract the files to your vault's plugins folder: `<vault>/.obsidian/plugins/obsidian-agent/`
3. Reload Obsidian
4. Enable "Obsidian Agent" in Settings → Community Plugins

### Development Installation

1. Clone this repository into your vault's plugins folder:
   ```bash
   cd <vault>/.obsidian/plugins/
   git clone https://github.com/B0LK13/obsidian-agent.git
   ```

2. Install dependencies:
   ```bash
   cd obsidian-agent
   npm install
   ```

3. Build the plugin:
   ```bash
   npm run build
   ```

4. Reload Obsidian and enable the plugin

## Configuration

1. Open Settings → Obsidian Agent
2. Choose your AI provider (OpenAI, Anthropic, or Custom API)
3. Enter your API key
4. Configure model and parameters:
   - **Model**: The AI model to use (e.g., `gpt-4`, `claude-3-opus-20240229`)
   - **Temperature**: Controls randomness (0-1, higher = more creative)
   - **Max Tokens**: Maximum length of AI responses
   - **System Prompt**: Define the AI's behavior and personality
   - **Context Awareness**: Enable/disable sharing note context with AI

### API Keys

- **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Anthropic**: Get your API key from [Anthropic Console](https://console.anthropic.com/)
- **Custom API**: Use any OpenAI-compatible API endpoint

## Usage Examples

### Quick Summary
1. Open a note with content you want to summarize
2. Press `Ctrl/Cmd + P` to open Command Palette
3. Type "Generate Summary"
4. The AI will append a summary to your note

### Expand Brief Notes
1. Select text you want to expand
2. Use "Expand Ideas" command
3. The selected text will be replaced with an expanded version

### Interactive Questions
1. Use "Ask AI Agent" command
2. Enter your question in the dialog
3. The AI response will be inserted at your cursor

## Development

### Build from Source

```bash
# Install dependencies
npm install

# Development build with hot reload
npm run dev

# Production build
npm run build
```

### Project Structure

- `main.ts`: Main plugin entry point and command definitions
- `settings.ts`: Settings interface and defaults
- `settingsTab.ts`: Settings UI
- `aiService.ts`: AI API integration layer
- `agentModal.ts`: Interactive modal for AI conversations
- `manifest.json`: Plugin metadata
- `esbuild.config.mjs`: Build configuration

## Privacy & Security

- All API keys are stored locally in your Obsidian vault
- No data is sent to third parties except your chosen AI provider
- Note content is only sent to the AI when you explicitly use a command
- You have full control over what context is shared with the AI

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see [LICENSE](LICENSE) file for details

## Support

If you encounter any issues or have questions:
- Open an issue on [GitHub](https://github.com/B0LK13/obsidian-agent/issues)
- Check existing issues for solutions

## Roadmap

- [ ] Support for more AI providers
- [ ] Custom command creation
- [ ] Batch processing of multiple notes
- [ ] Integration with Obsidian templates
- [ ] Voice input support
- [ ] Multi-language support

---

**Note**: This plugin requires an active API key from your chosen AI provider. API usage may incur costs based on your provider's pricing.
