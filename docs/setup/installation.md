# Installation Guide

## Prerequisites

- Python 3.11 or higher
- Node.js 18 or higher
- Obsidian (for the plugin)

## PKM Agent (Python Backend)

### Quick Install

```bash
cd apps/pkm-agent
pip install -e .
```

### With Development Dependencies

```bash
pip install -e ".[dev]"
```

### With Ollama Support

```bash
pip install -e ".[ollama]"
```

### Environment Configuration

Create a `.env` file in the project root:

```env
PKMA_PKM_ROOT=/path/to/your/obsidian/vault
PKMA_LLM__PROVIDER=openai
PKMA_LLM__MODEL=gpt-4o-mini
OPENAI_API_KEY=your-api-key
```

## Obsidian Plugin

### Manual Installation

1. Build the plugin:
   ```bash
   cd apps/obsidian-plugin
   npm install
   npm run build
   ```

2. Copy files to your vault:
   ```bash
   cp main.js manifest.json styles.css /path/to/vault/.obsidian/plugins/obsidian-pkm-agent/
   ```

3. Enable the plugin in Obsidian Settings > Community Plugins

### Development Mode

```bash
cd apps/obsidian-plugin
npm run dev
```

This watches for changes and rebuilds automatically.

## Web App (Optional)

```bash
cd apps/web
npm install
npm run dev
```

## Verification

### Test PKM Agent

```bash
pkm-agent stats
```

### Test WebSocket Connection

Start the PKM Agent server:
```bash
pkm-agent tui
```

The WebSocket server starts on `ws://127.0.0.1:27125`.

## Troubleshooting

### Common Issues

1. **ChromaDB errors**: Ensure you have sufficient disk space for vector storage
2. **OpenAI API errors**: Verify your API key is valid
3. **WebSocket connection failed**: Check if the PKM Agent is running
4. **Plugin not loading**: Ensure all files are in the correct Obsidian folder
