# AI Chat & Notes for Obsidian

An AI-enhanced chat and note-taking platform plugin for Obsidian, implementing the Liquid Glass design language with intelligent note management, semantic search, and seamless AI integration.

![Design Philosophy](https://img.shields.io/badge/Design-Liquid%20Glass-purple)
![AI Ready](https://img.shields.io/badge/AI-Integrated-blue)
![Obsidian](https://img.shields.io/badge/Obsidian-Compatible-black)

## ✨ Features

### 🤖 AI Chat Interface
- **Modern Chat UI** with message bubbles following 2025 design patterns
- **Liquid Glass Design** with glass-morphism effects
- **Typing indicators** and read receipts
- **Context-aware conversations** with your notes
- **Multiple AI providers** support (Ollama, OpenAI, Anthropic)

### 📝 Note Management
- **Note Browser** with tree view and drag-and-drop
- **Context integration** - Ask AI about any note
- **Chat-to-Note conversion** - Save conversations as structured notes
- **Smart note linking** and bi-directional references

### 🔍 Semantic Search
- **AI-powered search** using embeddings
- **Natural language queries** - search by meaning, not just keywords
- **Similarity matching** - find related notes automatically
- **Vector-based indexing** for fast retrieval

### 🎨 Design System
- **Liquid Glass UI** - Transparency, depth, and fluid motion
- **Dark mode optimized** for OLED displays
- **Responsive layout** - works on desktop and mobile
- **Accessibility first** - WCAG 2.0 compliant

## 🚀 Installation

### From Obsidian Community Plugins
1. Open Settings → Community Plugins
2. Search for "AI Chat & Notes"
3. Click Install → Enable

### Manual Installation
1. Download the latest release
2. Extract to `.obsidian/plugins/ai-chat-notes/`
3. Enable in Settings → Community Plugins

## ⚙️ Configuration

### AI Provider Setup

#### Ollama (Recommended for Privacy)
1. Install [Ollama](https://ollama.ai) on your machine
2. Pull a model: `ollama pull llama3.2`
3. In plugin settings, select "Ollama" as provider
4. Set URL to `http://localhost:11434`

#### OpenAI
1. Get your API key from [OpenAI](https://platform.openai.com)
2. In plugin settings, select "OpenAI"
3. Enter your API key

#### Anthropic (Claude)
1. Get your API key from [Anthropic](https://console.anthropic.com)
2. In plugin settings, select "Anthropic"
3. Enter your API key

### UI Settings
- **Liquid Glass Effect** - Toggle glass-morphism design
- **Message Bubble Style** - Modern, Classic, or Minimal
- **Font Size** - Adjust chat text size
- **Theme** - System, Light, or Dark mode

### Feature Settings
- **Semantic Search** - Enable AI-powered note search
- **Auto Sync** - Automatically index notes for search
- **Max Context Notes** - Number of notes to include in AI context

## 📖 Usage

### Starting a Chat
1. Click the 💬 "AI Chat" icon in the ribbon
2. Or use Command Palette → "Open AI Chat"
3. Type your message and press Enter

### Asking About a Note
1. Open any note in your vault
2. Use Command Palette → "Ask AI about current note"
3. The note content becomes context for your questions

### Semantic Search
1. Use Command Palette → "Semantic Search"
2. Type natural language query (e.g., "notes about project planning")
3. Results are ranked by semantic similarity

### Converting Chat to Note
1. In the AI Chat view, click "Save to Note" on any message
2. Or use Command Palette → "Convert chat to note"
3. The entire conversation is saved as a markdown note

## 🏗️ Architecture

This plugin implements the MVVM (Model-View-ViewModel) architecture pattern:

```
┌─────────────┐
│  View Layer │  ← UI Components (Chat, Notes, AI Interface)
├─────────────┤
│ ViewModel   │  ← Business Logic (State Management)
├─────────────┤
│   Model     │  ← Data Layer (Database, AI Services)
└─────────────┘
```

### Key Components

#### Services
- **AIService** - Handles AI provider communication
- **SearchService** - Manages semantic search and embeddings
- **ChatService** - Chat session management
- **DatabaseManager** - Local data persistence

#### Views
- **AIChatView** - Main chat interface
- **NoteBrowserView** - File tree and note navigation

## 🔒 Privacy & Security

- **Local-first** - All data stored locally by default
- **No data sharing** - Your notes never leave your device (with Ollama)
- **Optional encryption** - Enable data encryption in settings
- **No training** - Your data is never used to train AI models

## 🎨 Design Philosophy

This plugin implements the **Liquid Glass** design language:

### Visual Principles
- **Transparency & Depth** - Layered translucent surfaces
- **Fluid Motion** - Seamless 300ms transitions
- **Reflective Surfaces** - Premium glass-like aesthetics

### Color Palette
- **Primary**: `#667eea` (Purple gradient)
- **Background Light**: `#FFFFFF` with 70% opacity
- **Background Dark**: `#121212` (OLED optimized)
- **Text**: High contrast for accessibility

### Typography
- **Body Large**: 18px, 1.6 line height for chat
- **Headlines**: Inter font, bold weights
- **Accessibility**: Minimum 4.5:1 contrast ratio

## 🛠️ Development

### Building from Source
```bash
cd obsidian-ai-chat-plugin
npm install
npm run dev
```

### Project Structure
```
obsidian-ai-chat-plugin/
├── main.ts              # Plugin entry point
├── manifest.json        # Plugin manifest
├── src/
│   ├── views/          # UI Views
│   ├── services/       # Business logic
│   ├── db/             # Database management
│   └── components/     # Shared components
└── styles/             # CSS styles
```

### API Integration
The plugin supports multiple AI providers through a unified interface:

```typescript
// Example: Generate response
const response = await aiService.generateResponse(
  "Summarize this note",
  "llama3.2"
);

// Example: Semantic search
const results = await searchService.semanticSearch(
  "project ideas from last week"
);
```

## 📝 Roadmap

### Phase 1: Foundation ✓
- [x] Core plugin architecture
- [x] Basic chat interface
- [x] AI service integration
- [x] Settings UI

### Phase 2: Enhanced Features ✓
- [x] Note browser view
- [x] Semantic search
- [x] Context-aware AI
- [x] Liquid Glass design

### Phase 3: Advanced Features ✓
- [x] Voice messages with transcription
- [x] Handwriting support
- [x] Knowledge graph visualization
- [x] Plugin API for extensions

#### 🎙️ Voice Messages
- Record voice messages directly in the chat
- Automatic transcription using OpenAI Whisper
- One-click voice-to-text conversion

#### ✍️ Handwriting Canvas
- Natural handwriting with pressure-sensitive strokes
- Multiple colors and brush sizes
- Eraser tool and undo functionality
- Export as images or Obsidian notes

#### 🕸️ Knowledge Graph
- Visual graph of all your notes and connections
- Interactive node exploration
- Automatic layout with force-directed algorithm
- Filter by note type, tags, and concepts

#### 🔌 Plugin API
- Extension system for third-party plugins
- Event system for message/note events
- Register custom commands
- Access to AI, search, and chat services

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- Design specification based on "AI-Enhanced Chat & Note-Taking Platform (2025)"
- Inspired by Obsidian, Notion, and modern messaging apps
- Icons from Lucide

## 📞 Support

- [GitHub Issues](https://github.com/yourusername/obsidian-ai-chat-notes/issues)
- [Obsidian Forum](https://forum.obsidian.md)

---

*Built with ❤️ for the Obsidian community*
