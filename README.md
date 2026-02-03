# Obsidian Agent

AI-enhanced Obsidian Agent for intelligent note-taking, knowledge management, and content generation. Now featuring a **2025 Chat UI Design** with liquid glass aesthetics, real-time interactions, and enhanced accessibility.

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Obsidian](https://img.shields.io/badge/Obsidian-0.15.0+-purple.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Features

### Core AI Capabilities
- 🤖 **AI-Powered Assistance**: Integrate powerful AI models (OpenAI, Anthropic, Ollama, or custom) directly into your Obsidian workflow
- 📝 **Smart Commands**: Multiple built-in commands for common writing tasks
- 🔍 **Context-Aware**: Agent understands your current note context and linked notes
- ⚙️ **Configurable**: Customize AI behavior, model selection, and parameters
- 🔐 **Secure**: Your API keys are stored locally, no cloud dependencies

### 🎨 2025 Chat UI Design (New!)
- **Liquid Glass Interface**: Translucent backgrounds with backdrop blur effects
- **Typing Indicator**: Real-time AI activity feedback with animated dots
- **Message Reactions**: Quick emoji feedback (👍 ❤️ 😄 🎉 🤔 👀 🔥 ✅)
- **Enhanced Message Bubbles**: Gradient effects with smooth animations
- **Voice Messages**: Waveform visualization for audio content
- **Smart Search**: Progressive conversation search with highlighted matches
- **Scroll to Bottom**: Auto-appearing navigation with unread badge
- **Micro-Interactions**: Subtle hover effects and transitions throughout

### Additional Features
- 🔄 **AI Profiles**: Switch between different AI configurations instantly
- 💬 **Conversation Persistence**: Save and resume chat sessions
- 📊 **Token Tracking**: Monitor usage and estimated costs
- 🎯 **Inline Completions**: Smart text suggestions as you type
- 🔗 **Vault Context**: Include linked notes and backlinks in context
- ♿ **Accessibility**: High contrast mode and reduced motion support

## 🚀 Commands

Access via Command Palette (`Ctrl/Cmd + P`):

| Command | Description |
|---------|-------------|
| **Ask AI Agent** | Open enhanced chat dialog with AI |
| **Ask AI Agent (with Linked Notes)** | Include vault context in conversation |
| **Generate Summary** | Summarize selected text or entire note |
| **Expand Ideas** | Expand brief notes into detailed content |
| **Improve Writing** | Enhance clarity, grammar, and style |
| **Generate Outline** | Create structured outline from topic |
| **Answer Question Based on Note** | Ask questions about note content |
| **Switch AI Profile** | Quickly change between AI configurations |
| **Scan Vault for Dead Links** | Find and report broken links in your vault |
| **Scan Current File for Dead Links** | Check active file for broken links |

## 📦 Installation

### From Obsidian Community Plugins (Coming Soon)

1. Open Settings → Community Plugins
2. Search for "Obsidian Agent"
3. Click Install
4. Enable the plugin

### Manual Installation

1. Download `obsidian-agent-1.0.0.zip` from the [latest release](https://github.com/B0LK13/obsidian-agent/releases)
2. Extract to your vault's plugins folder: `<vault>/.obsidian/plugins/obsidian-agent/`
3. Reload Obsidian
4. Enable "Obsidian Agent" in Settings → Community Plugins

### Development Installation

```bash
cd <vault>/.obsidian/plugins/
git clone https://github.com/B0LK13/obsidian-agent.git
cd obsidian-agent
npm install
npm run build
```

## ⚙️ Configuration

### Quick Setup

1. Open Settings → Obsidian Agent
2. Choose your AI provider (OpenAI, Anthropic, Ollama, or Custom)
3. Enter your API key
4. Select your preferred model

### AI Profiles

Create multiple AI profiles for different use cases:
- **Research**: Deep analysis with GPT-4
- **Quick Notes**: Fast responses with GPT-3.5
- **Local Privacy**: Offline with Ollama
- **Custom API**: Your own AI endpoint

### Settings Options

| Setting | Description |
|---------|-------------|
| **Model** | AI model to use (e.g., `gpt-4`, `claude-3-opus`, `llama2`) |
| **Temperature** | Controls randomness (0-1, higher = more creative) |
| **Max Tokens** | Maximum length of AI responses |
| **System Prompt** | Define the AI's behavior and personality |
| **Context Awareness** | Include note context in AI requests |
| **Conversation Persistence** | Save chat history across sessions |
| **Token Tracking** | Monitor usage and estimated costs |

### Inline Completions & Suggestions

Configure under **Settings → Obsidian Agent → Inline Completions**:

- Trigger mode (Manual, Auto, or Both)
- Auto-trigger delay
- Manual shortcut (default: `Ctrl+Space`)
- Phrase triggers (`...`, `//`)
- Excluded folders
- Max completions and tokens

## 🎯 Usage Examples

### Quick Summary
```
1. Open a note with content to summarize
2. Press Ctrl/Cmd + P → "Generate Summary"
3. AI appends summary to your note
```

### Expand Ideas
```
1. Select brief notes
2. Ctrl/Cmd + P → "Expand Ideas"
3. Selected text expands with detail
```

### Interactive Chat with Vault Context
```
1. Ctrl/Cmd + P → "Ask AI Agent (with Linked Notes)"
2. Type your question
3. AI responds using context from linked notes
```

### Switch AI Profiles
```
1. Ctrl/Cmd + P → "Switch AI Profile"
2. Select from your configured profiles
3. Continue with different AI settings
```

## 🛠️ Development

### Build Commands

```bash
# Install dependencies
npm install

# Development build with hot reload
npm run dev

# Production build
npm run build

# Run tests
npm test

# Run linter
npm run lint

# Create distribution package
npm run package

# Full verification
node scripts/verify.mjs
```

### Project Structure

```
obsidian-agent/
├── src/
│   └── dashboard/              # Dashboard components
├── tests/
│   ├── inlineCompletionService.test.ts
│   └── uiComponents.test.ts    # UI component tests
├── scripts/
│   ├── verify.mjs              # Verification script
│   ├── release.mjs             # Release automation
│   └── package.mjs             # Package creation
├── main.ts                     # Plugin entry point
├── agentModal.ts               # Original chat modal
├── agentModalEnhanced.ts       # 2025 UI enhanced modal ⭐
├── uiComponents.ts             # Reusable UI components ⭐
├── aiService.ts                # AI API integration
├── settings.ts                 # Settings interface
├── settingsTab.ts              # Settings UI
├── styles.css                  # Base styles
├── styles-enhanced.css         # 2025 UI styles ⭐
├── manifest.json               # Plugin metadata
└── README.md                   # This file
```

### Technologies Used

- **TypeScript**: Type-safe development
- **ESBuild**: Fast bundling and minification
- **Vitest**: Unit testing framework
- **ESLint**: Code quality and linting
- **Web Animations API**: Smooth animations
- **CSS Custom Properties**: Dynamic theming

## 🔒 Privacy & Security

- ✅ All API keys stored locally in your Obsidian vault
- ✅ No data sent to third parties except your chosen AI provider
- ✅ Note content only sent when you explicitly use a command
- ✅ Full control over what context is shared
- ✅ Optional local AI with Ollama (no internet required)
- ✅ Response caching to reduce API calls

## ♿ Accessibility

The plugin includes comprehensive accessibility features:

- **High Contrast Mode**: Enhanced visibility
- **Reduced Motion**: Respects `prefers-reduced-motion`
- **Screen Reader Support**: ARIA labels and live regions
- **Keyboard Navigation**: Full keyboard control
- **Focus Indicators**: Clear visual focus states
- **Scalable Typography**: Adjustable font sizes

## 🐛 Troubleshooting

### Common Issues

**Issue**: Plugin won't load  
**Solution**: Ensure all files are extracted to `<vault>/.obsidian/plugins/obsidian-agent/`

**Issue**: API errors  
**Solution**: Check your API key in settings and verify internet connection

**Issue**: Ollama not connecting  
**Solution**: Ensure Ollama is running with `ollama serve` on port 11434

**Issue**: Windows Defender false positive (Windows only)  
**Solution**: See detailed instructions in [INSTALLATION.md](INSTALLATION.md#windows-defender-false-positive-windows-only) or run `scripts/setup-defender-exclusions.ps1` as Administrator

**Issue**: Out of Memory errors with large models (GPU)  
**Solution**: Reduce context size, use more quantized models (Q4 instead of Q6), or enable automatic GPU memory management in settings

### Getting Help

- 📖 [Full Documentation](https://github.com/B0LK13/obsidian-agent/wiki)
- 🐛 [Report Issues](https://github.com/B0LK13/obsidian-agent/issues)
- 💬 [Discussions](https://github.com/B0LK13/obsidian-agent/discussions)

## 📝 Changelog

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### v1.0.0 (2026-01-29)

#### Added
- 2025 Chat UI Design with Liquid Glass aesthetics
- Typing indicator for AI responses
- Message reactions (emoji support)
- Voice message UI components
- Enhanced search interface
- Scroll to bottom button with unread badge
- AI Profiles system for quick switching
- Conversation persistence
- Comprehensive test suite
- Automated verification scripts

#### Changed
- Enhanced esbuild configuration
- Updated TypeScript strict mode
- Improved build pipeline
- Optimized bundle size (94.30 KB)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🙏 Acknowledgments

- UI design patterns inspired by modern chat applications (2025)
- Obsidian Plugin API documentation
- Community contributions and feedback

---

**Made with ❤️ for the Obsidian community**

**Version**: 1.0.0 | **Status**: Production Ready ✅
