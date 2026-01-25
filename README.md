# Obsidian Agent

AI-enhanced Obsidian Agent for intelligent note-taking, knowledge management, and content generation with advanced features.

## Features

- 🤖 **AI-Powered Assistance**: Integrate powerful AI models (OpenAI, Anthropic, or custom) directly into your Obsidian workflow
- 📝 **Smart Commands**: 20+ built-in commands for common writing tasks
- 🔍 **Context-Aware**: Agent understands your current note context
- ⚙️ **Configurable**: Customize AI behavior, model selection, and parameters
- 🔐 **Secure**: Your API keys are stored locally
- 💬 **Chat Sidebar**: Persistent AI chat interface
- 📋 **Templates**: Custom prompt templates for reusable tasks
- 📊 **Token Tracking**: Monitor API usage and costs
- 🔄 **Conversation History**: Multi-turn conversations with context
- ⚡ **Response Caching**: Faster responses for repeated queries
- 🎯 **Batch Processing**: Process multiple notes at once

## Commands

The plugin provides the following commands (accessible via Command Palette - `Ctrl/Cmd + P`):

### Core Commands
1. **Ask AI Agent**: Open a dialog to ask the AI anything about your current note
2. **Generate Summary**: Automatically summarize selected text or entire note
3. **Expand Ideas**: Take brief notes and expand them into detailed content
4. **Improve Writing**: Enhance clarity, grammar, and style of selected text
5. **Generate Outline**: Create a structured outline from a topic
6. **Answer Question Based on Note**: Ask questions about your note content

### Writing Enhancement
7. **Rephrase Text**: Rephrase selected text while maintaining meaning
8. **Make Text Professional**: Convert text to professional, formal tone
9. **Make Text Casual**: Convert text to casual, friendly tone
10. **Translate Text**: Translate to your default language

### Code Assistance
11. **Generate Code from Description**: Create code from plain English description
12. **Explain Selected Code**: Get detailed explanations of code snippets
13. **Find and Fix Errors in Code**: Automated code review and bug fixing

### Content Generation
14. **Generate Table of Contents**: Auto-generate TOC with markdown links
15. **Generate Tags for Note**: AI-suggested tags based on content
16. **Create Flashcards from Note**: Generate Q&A flashcards for studying
17. **Brainstorm Ideas**: Generate creative ideas for any topic
18. **Generate Meeting Notes Template**: Create structured meeting templates

### Utility Commands
19. **Show Token Usage Statistics**: View API usage and estimated costs
20. **Clear Response Cache**: Clear cached responses
21. **Open AI Chat Sidebar**: Open persistent chat interface

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

### Advanced Settings

- **Conversation History**: Enable multi-turn conversations with context retention
- **Max Conversation Length**: Number of messages to keep in history (default: 10)
- **Response Caching**: Cache responses to speed up repeated queries
- **Cache Expiration**: How long to keep cached responses (in minutes)
- **Token Tracking**: Monitor API usage and estimated costs
- **Show Token Count**: Display token usage after each request
- **Custom Templates**: Create reusable prompt templates
- **Smart Suggestions**: Get context-aware command suggestions
- **Auto-Linking**: Automatically generate wikilinks in responses
- **Default Language**: Language for translation commands
- **Streaming**: Enable real-time response streaming (if supported)

### API Keys

- **OpenAI**: Get your API key from [OpenAI Platform](https://platform.openai.com/api-keys)
- **Anthropic**: Get your API key from [Anthropic Console](https://console.anthropic.com/)
- **Custom API**: Use any OpenAI-compatible API endpoint

## Advanced Features

### Chat Sidebar
- Click the message icon in the ribbon or use "Open AI Chat Sidebar" command
- Persistent chat interface with conversation history
- Context-aware responses based on your vault
- Clear chat button to start fresh conversations

### Custom Templates
The plugin includes 8 built-in templates:
1. **Meeting Notes Formatter** - Structure raw meeting notes
2. **Explain Code** - Detailed code explanations
3. **Blog Post Generator** - Create blog posts from topics
4. **Translate Text** - Multi-language translation
5. **Brainstorm Ideas** - Creative idea generation
6. **Grammar Check** - Grammar and style improvements
7. **Email Composer** - Professional email drafts
8. **Study Notes Generator** - Create study materials

You can create custom templates with variables like `{{topic}}`, `{{text}}`, etc.

### Token Usage Tracking
- Enable token tracking in settings
- Use "Show Token Usage Statistics" command to view:
  - Total requests and tokens used
  - Estimated costs (based on current model pricing)
  - Usage breakdown by time period (24h, 7d, total)
- Monitor costs to stay within budget

### Response Caching
- Enable caching to get instant responses for repeated queries
- Configurable cache size and expiration time
- Automatic cleanup of expired entries
- View cache statistics in settings

### Batch Processing (Coming Soon)
- Process multiple notes with the same operation
- Useful for bulk summarization, translation, or tagging
- Progress tracking and error handling
- Scheduled batch jobs

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

### Completed ✅
- [x] Support for multiple AI providers (OpenAI, Anthropic, Custom)
- [x] Custom prompt templates system
- [x] Conversation history with multi-turn context
- [x] Token usage tracking and cost estimation
- [x] Response caching for faster repeated queries
- [x] AI chat sidebar with persistent conversations
- [x] 20+ built-in commands for various tasks
- [x] Code generation and explanation features
- [x] Multi-language translation support
- [x] Batch processing framework
- [x] Template system with 8 default templates

### Planned 🚀
- [ ] Voice input integration (speech-to-text)
- [ ] Image analysis and description
- [ ] PDF and document parsing
- [ ] Obsidian Canvas integration
- [ ] Scheduled automated tasks
- [ ] Plugin API for extensions
- [ ] Cloud sync for templates and history
- [ ] Advanced prompt engineering tools
- [ ] Fine-tuning support for custom models
- [ ] Collaboration features for team vaults
- [ ] Mobile app optimizations
- [ ] Integration with external knowledge bases

### Under Consideration 💭
- [ ] Local AI model support (Ollama, llama.cpp)
- [ ] Vector database integration for RAG
- [ ] Automated note linking and graph building
- [ ] Real-time collaborative editing with AI
- [ ] Custom workflow automation
- [ ] Plugin marketplace for community templates

---

**Note**: This plugin requires an active API key from your chosen AI provider. API usage may incur costs based on your provider's pricing.
