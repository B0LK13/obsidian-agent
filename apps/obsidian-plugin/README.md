# Obsidian PKM Agent Plugin

AI-powered Obsidian plugin for intelligent note-taking and knowledge management.

## Features

- **AI Chat**: Natural language interaction with your vault
- **Context Awareness**: Understands note relationships and links
- **Knowledge Graph**: Visual representation of note connections
- **Task Planning**: AI-assisted task management
- **Memory Manager**: Persistent context across sessions
- **MCP Integration**: Connects to PKM Agent backend

## Installation

1. Copy `main.js`, `manifest.json`, and `styles.css` to your vault's `.obsidian/plugins/obsidian-pkm-agent/` folder
2. Enable the plugin in Obsidian settings
3. Configure your API keys in plugin settings

## Development

```bash
# Install dependencies
npm install

# Build for development (watch mode)
npm run dev

# Build for production
npm run build
```

## Configuration

In Obsidian Settings > PKM Agent:

- **OpenAI API Key**: Your OpenAI API key
- **Model**: GPT model to use (default: gpt-4o)
- **PKM Agent URL**: Backend server URL (default: ws://127.0.0.1:27125)

## Project Structure

```text
src/
├── ContextAwareness.ts   # Note context analysis
├── KnowledgeGraph.ts     # Graph visualization
├── MCPClient.ts          # MCP protocol client
├── MemoryManager.ts      # Session memory
├── OpenAIService.ts      # OpenAI integration
├── SyncClient.ts         # Backend sync
├── TaskPlanner.ts        # Task management
├── ToolHandler.ts        # Tool execution
└── VaultManager.ts       # Vault operations
```

## License

MIT
