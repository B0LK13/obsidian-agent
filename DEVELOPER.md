# Developer Documentation

Technical documentation for developers working on Obsidian Agent.

## Architecture Overview

```
obsidian-agent/
├── main.ts              # Plugin entry point, command registration
├── settings.ts          # Settings interface and defaults
├── settingsTab.ts       # Settings UI implementation
├── aiService.ts         # AI API integration layer
├── agentModal.ts        # Interactive modal component
└── styles.css           # Plugin styling
```

## Core Components

### 1. Main Plugin (`main.ts`)

**Responsibilities:**
- Plugin lifecycle management (load/unload)
- Command registration
- Settings persistence
- Integration between components

**Key Methods:**
- `onload()`: Initialize plugin, register commands, add settings tab
- `onunload()`: Cleanup on plugin disable
- `loadSettings()`: Load saved settings from disk
- `saveSettings()`: Save settings to disk and update AI service

### 2. AI Service (`aiService.ts`)

**Responsibilities:**
- Abstract API communication
- Handle different AI providers (OpenAI, Anthropic, Custom)
- Message formatting and parsing
- Error handling

**Key Methods:**
- `generateCompletion(prompt, context?)`: Main method for AI requests
- `callAPI(messages)`: Low-level API communication

**Supported Providers:**
- OpenAI: `https://api.openai.com/v1/chat/completions`
- Anthropic: `https://api.anthropic.com/v1/messages`
- Custom: User-defined endpoint (OpenAI-compatible format)

### 3. Settings Management

**Settings Interface (`settings.ts`):**
```typescript
interface ObsidianAgentSettings {
  apiKey: string;
  apiProvider: 'openai' | 'anthropic' | 'custom';
  customApiUrl: string;
  model: string;
  temperature: number;
  maxTokens: number;
  systemPrompt: string;
  enableContextAwareness: boolean;
}
```

**Settings UI (`settingsTab.ts`):**
- Dropdown for provider selection
- Text input for API key (password field)
- Conditional custom URL field
- Slider for temperature
- Text area for system prompt
- Toggle for context awareness

### 4. Agent Modal (`agentModal.ts`)

**Purpose:** Interactive dialog for custom AI queries

**Features:**
- Text area for user prompt input
- Context passing from current note
- Loading state during API calls
- Error handling with user notifications
- Result callback to insert AI response

## Command System

All commands use Obsidian's `editorCallback` pattern:

```typescript
this.addCommand({
  id: 'command-id',
  name: 'Command Name',
  editorCallback: async (editor: Editor, view: MarkdownView) => {
    // Command implementation
  }
});
```

### Available Commands

1. **ask-ai-agent**: Opens modal for custom queries
2. **generate-summary**: Summarizes selected/all text
3. **expand-ideas**: Expands brief notes into detail
4. **improve-writing**: Enhances text quality
5. **generate-outline**: Creates structured outline
6. **answer-question**: Context-aware Q&A

## API Integration Details

### Request Format

**OpenAI:**
```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
  ],
  "temperature": 0.7,
  "max_tokens": 2000
}
```

**Anthropic:**
```json
{
  "model": "claude-3-opus-20240229",
  "max_tokens": 2000,
  "temperature": 0.7,
  "system": "...",
  "messages": [
    {"role": "user", "content": "..."}
  ]
}
```

### Response Parsing

- OpenAI: `response.choices[0].message.content`
- Anthropic: `response.content[0].text`
- Error handling validates array existence and length

### Error Handling Strategy

1. **API Key Validation**: Check before any API call
2. **Network Errors**: Caught and displayed to user
3. **Response Validation**: Check for expected structure
4. **User Feedback**: Use Obsidian's Notice API for all errors

## Build System

### ESBuild Configuration

**Input:** `main.ts`  
**Output:** `main.js` (bundled)

**Key Settings:**
- Format: CommonJS (required by Obsidian)
- Target: ES2018
- Bundle: true
- External: Obsidian API, CodeMirror, Electron
- Sourcemap: inline (dev), none (production)

### Build Commands

```bash
# Development (watch mode)
npm run dev

# Production build
npm run build

# Type checking
npx tsc --noEmit
```

### Version Management

`version-bump.mjs` script:
- Updates `manifest.json` version
- Updates `versions.json` with minAppVersion mapping
- Runs during `npm version` command

## Testing Strategy

### Manual Testing Checklist

- [ ] Install plugin in test vault
- [ ] Configure API key for each provider
- [ ] Test all 6 commands with different inputs
- [ ] Verify settings changes persist
- [ ] Test error scenarios (invalid key, network failure)
- [ ] Check console for errors
- [ ] Verify UI responsiveness
- [ ] Test on different Obsidian versions

### Edge Cases to Test

1. Empty/whitespace-only selections
2. Very large notes (token limits)
3. Special characters in prompts
4. Network timeout scenarios
5. Invalid API responses
6. Missing API credentials

## Code Style

### TypeScript Guidelines

- Use explicit types for function parameters
- Prefer `async/await` over promises
- Use `const` for immutable values
- Destructure objects when appropriate
- Handle errors explicitly (no silent failures)

### Naming Conventions

- Classes: PascalCase (`ObsidianAgentPlugin`)
- Methods: camelCase (`generateCompletion`)
- Constants: UPPER_SNAKE_CASE (`DEFAULT_SETTINGS`)
- Files: camelCase (`aiService.ts`)

### Comment Style

```typescript
// Single-line explanations for complex logic

/**
 * Multi-line documentation for public APIs
 * @param prompt - User's input prompt
 * @param context - Optional note context
 * @returns AI-generated response
 */
```

## Debugging

### Enable Debug Mode

1. Open Developer Tools: `Ctrl/Cmd + Shift + I`
2. Check Console tab for logs
3. Look for "Obsidian Agent" prefix in logs

### Common Issues

**Issue:** "API key not configured"  
**Fix:** Check settings saved correctly, verify `loadSettings()` called

**Issue:** Build fails  
**Fix:** Run `npm install`, check TypeScript errors with `npx tsc --noEmit`

**Issue:** Commands not appearing  
**Fix:** Check `manifest.json` syntax, reload Obsidian

## Performance Considerations

1. **API Calls**: Cached nowhere, each command = 1 API request
2. **Context Size**: Entire note content sent when context enabled
3. **Bundle Size**: ~15KB minified (acceptable for Obsidian plugin)
4. **Memory**: Minimal, no large data structures held in memory

## Security Best Practices

1. **API Keys**: Never logged or transmitted except to AI provider
2. **Input Sanitization**: Not required (AI handles arbitrary text)
3. **Output Validation**: Check response structure before accessing
4. **Dependencies**: Minimal external deps reduces attack surface

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Quick Contribution Workflow

1. Fork repository
2. Create feature branch
3. Make changes with tests
4. Run `npm run build` to verify
5. Submit PR with clear description

## Release Process

1. Update version in `package.json`
2. Update `CHANGELOG.md`
3. Run `npm run version`
4. Commit changes
5. Create git tag: `git tag -a v1.0.0 -m "Release v1.0.0"`
6. Push tag: `git push origin v1.0.0`
7. GitHub Actions builds and creates draft release
8. Edit release notes and publish

## Troubleshooting Development Issues

### TypeScript Errors

```bash
# Full type check
npx tsc --noEmit

# Watch mode
npx tsc --noEmit --watch
```

### ESLint Issues

```bash
# Check linting
npx eslint .

# Auto-fix
npx eslint . --fix
```

### Plugin Not Loading

1. Check `.obsidian/plugins/obsidian-agent/` exists
2. Verify `manifest.json` syntax valid
3. Check Obsidian version >= minAppVersion
4. Look for errors in Developer Console

## Resources

- [Obsidian Plugin API](https://docs.obsidian.md/Plugins/Getting+started/Build+a+plugin)
- [Obsidian Plugin Developer Docs](https://docs.obsidian.md/Home)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [Anthropic API Reference](https://docs.anthropic.com/claude/reference)

## Support

- GitHub Issues: Bug reports and feature requests
- Discussions: Questions and community support
- Pull Requests: Code contributions welcome
