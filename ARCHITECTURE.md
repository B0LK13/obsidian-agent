# Architecture Overview

This document describes the high-level architecture of Obsidian Agent, a TypeScript-based plugin for Obsidian that integrates AI capabilities into the note-taking workflow.

## Table of Contents

- [Project Structure](#project-structure)
- [Core Components](#core-components)
- [Data Flow](#data-flow)
- [Configuration System](#configuration-system)
- [UI Architecture](#ui-architecture)
- [API Integration](#api-integration)
- [Caching Strategy](#caching-strategy)
- [Extension Points](#extension-points)

## Project Structure

```
obsidian-agent/
├── main.ts                    # Plugin entry point, command registration
├── aiService.ts               # AI provider abstraction layer
├── cacheService.ts            # Response caching system
├── contextProvider.ts         # Vault context extraction
├── inlineCompletionService.ts # Inline text completions
├── suggestionService.ts       # Intelligent suggestions
├── tokenCounter.ts            # Token usage tracking
├── promptTemplates.ts         # Prompt template management
├── settings.ts                # Settings interfaces & defaults
├── settingsTab.ts             # Settings UI
├── agentModal.ts              # Original chat modal
├── agentModalEnhanced.ts      # Enhanced 2025 chat UI
├── uiComponents.ts            # Reusable UI components
├── styles.css                 # Base styles
├── styles-enhanced.css        # Enhanced UI styles
├── src/
│   └── dashboard/
│       └── dashboardView.ts   # Analytics dashboard
├── tests/                     # Test files
│   ├── setupTests.ts          # Test configuration
│   ├── aiService.test.ts      # AI service tests
│   ├── cacheService.test.ts   # Cache service tests
│   ├── settings.test.ts       # Settings tests
│   ├── uiComponents.test.ts   # UI component tests
│   └── inlineCompletionService.test.ts
├── scripts/                   # Build & utility scripts
├── manifest.json              # Obsidian plugin manifest
├── package.json               # Node.js dependencies
├── esbuild.config.mjs         # Build configuration
└── vitest.config.ts           # Test configuration
```

## Core Components

### 1. Plugin Entry Point (`main.ts`)

The main plugin class extends `Plugin` from Obsidian and handles:
- Plugin lifecycle (onload, onunload)
- Command registration
- Settings loading/saving
- Service initialization

```typescript
class ObsidianAgentPlugin extends Plugin {
    settings: ObsidianAgentSettings;
    aiService: AIService;
    contextProvider: ContextProvider;
    // ...
}
```

### 2. AI Service (`aiService.ts`)

The central service for AI interactions:
- **Multi-provider support**: OpenAI, Anthropic, Ollama, Custom APIs
- **Request handling**: Retry logic, timeout management
- **Streaming support**: Real-time token streaming
- **Caching integration**: Automatic response caching

```
┌─────────────────┐     ┌─────────────────┐
│   User Request  │────▶│    AIService    │
└─────────────────┘     └────────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │  OpenAI  │ │Anthropic │ │  Ollama  │
             └──────────┘ └──────────┘ └──────────┘
```

### 3. Cache Service (`cacheService.ts`)

Reduces API calls through intelligent caching:
- Content-aware cache keys
- LRU eviction policy
- TTL-based expiration
- Hit rate tracking

### 4. Context Provider (`contextProvider.ts`)

Extracts relevant context from the vault:
- Current note content
- Linked notes
- Backlinks
- Tag-based context
- Folder context

### 5. Settings System (`settings.ts`)

Centralized configuration management:
- Default settings definitions
- AI profiles
- Completion configuration
- Suggestion configuration
- Context configuration

## Data Flow

### Chat Request Flow

```
User Input
    │
    ▼
┌─────────────────┐
│  Modal/Command  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     ┌─────────────────┐
│ContextProvider  │────▶│   Build Prompt  │
└─────────────────┘     └────────┬────────┘
                                 │
         ┌───────────────────────┤
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  Cache Check    │     │   AIService     │
└────────┬────────┘     └────────┬────────┘
         │                       │
    Cache Hit?                   │
    ┌────┴────┐                  │
    │         │                  ▼
   Yes        No        ┌─────────────────┐
    │         │         │   API Request   │
    │         └────────▶│  (with retry)   │
    │                   └────────┬────────┘
    │                            │
    │         ┌──────────────────┤
    │         ▼                  ▼
    │  ┌─────────────┐    ┌─────────────┐
    │  │ Store Cache │    │  Response   │
    │  └─────────────┘    └──────┬──────┘
    │                            │
    └───────────────────────────▶│
                                 ▼
                          ┌─────────────┐
                          │   Display   │
                          └─────────────┘
```

### Inline Completion Flow

```
Editor Change
      │
      ▼
┌──────────────────┐
│ Debounce Timer   │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Check Triggers   │
│ (auto/manual/    │
│  phrase)         │
└────────┬─────────┘
         │
    Trigger?
    ┌────┴────┐
   Yes        No (ignore)
    │
    ▼
┌──────────────────┐
│ Extract Context  │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  AIService.      │
│  generateCompletion()
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Show Suggestions │
└──────────────────┘
```

## Configuration System

### Settings Hierarchy

```typescript
ObsidianAgentSettings
├── API Settings
│   ├── apiKey
│   ├── apiProvider
│   ├── model
│   └── temperature
├── profiles: AIProfile[]
├── contextConfig
│   ├── enableLinkedNotes
│   ├── enableBacklinks
│   └── maxNotesPerSource
├── cacheConfig
│   ├── enabled
│   ├── maxEntries
│   └── maxAgeDays
├── completionConfig
│   ├── triggerMode
│   └── phraseTriggers
└── suggestionConfig
    ├── enabled
    └── suggestionTypes
```

### AI Profiles

Profiles allow quick switching between configurations:

```typescript
interface AIProfile {
    id: string;
    name: string;
    apiProvider: 'openai' | 'anthropic' | 'ollama' | 'custom';
    apiKey: string;
    model: string;
    temperature: number;
    maxTokens: number;
    systemPrompt: string;
}
```

## UI Architecture

### Component Hierarchy

```
AgentModalEnhanced
├── Header (title, profile selector)
├── MessageContainer
│   ├── MessageBubble (user)
│   ├── MessageBubble (assistant)
│   │   ├── TypingIndicator
│   │   └── MessageReactions
│   └── ...
├── InputArea
│   ├── TextArea
│   └── SendButton
└── StatusBar
    └── TokenCounter
```

### UI Components (`uiComponents.ts`)

Reusable components with modern design:
- **TypingIndicator**: Animated dots showing AI activity
- **MessageReactions**: Emoji reactions system
- **VoiceRecorder**: Audio capture UI
- **SearchInterface**: Conversation search
- **ScrollToBottom**: Navigation button

### Styling Approach

- CSS Custom Properties for theming
- Glass morphism effects (backdrop-filter)
- Respects Obsidian's theme (light/dark)
- Reduced motion support
- High contrast mode

## API Integration

### Provider Abstraction

Each API provider has specific handling:

```typescript
switch (this.settings.apiProvider) {
    case 'openai':
        // OpenAI Chat Completions API format
        break;
    case 'anthropic':
        // Anthropic Messages API format
        break;
    case 'ollama':
        // Ollama local API format
        break;
    case 'custom':
        // OpenAI-compatible custom endpoint
        break;
}
```

### Error Handling

Robust error handling with:
- Retry logic with exponential backoff
- User-friendly error messages
- Rate limit detection
- Timeout management

## Caching Strategy

### Cache Key Generation

```typescript
// Keys combine: prompt + context + model + temperature
const key = `${promptHash}_${contextHash}_${model}_${temperature}`;
```

### Eviction Policy

- **LRU (Least Recently Used)**: Oldest accessed entries removed first
- **TTL-based**: Entries expire after maxAgeDays
- **Size-based**: Maximum entries limit

### Cache Statistics

Tracks:
- Hit rate
- Miss rate
- Estimated token savings
- Cost savings estimate

## Extension Points

### Adding a New AI Provider

1. Add provider type to settings:
   ```typescript
   apiProvider: 'openai' | 'anthropic' | 'ollama' | 'custom' | 'newprovider';
   ```

2. Implement in `aiService.ts`:
   ```typescript
   case 'newprovider':
       url = 'https://api.newprovider.com/v1/chat';
       headers = { /* provider-specific headers */ };
       body = { /* provider-specific format */ };
       break;
   ```

3. Handle response parsing:
   ```typescript
   if (this.settings.apiProvider === 'newprovider') {
       result.text = response.json.customField;
   }
   ```

### Adding New Commands

In `main.ts`:
```typescript
this.addCommand({
    id: 'my-command',
    name: 'My Command',
    callback: () => {
        // Command implementation
    }
});
```

### Creating New UI Components

Follow existing patterns in `uiComponents.ts`:
```typescript
export function createMyComponent(options: MyOptions): HTMLElement {
    const container = document.createElement('div');
    container.addClass('my-component');
    // Build component...
    return container;
}
```

## Performance Considerations

1. **Debouncing**: Inline completions use debounce to avoid excessive API calls
2. **Caching**: Response caching reduces redundant API requests
3. **Lazy Loading**: Heavy features load on demand
4. **Token Limits**: Context truncation to stay within token limits
5. **Streaming**: Progressive rendering for long responses

## Security

1. **API Keys**: Stored locally in Obsidian vault settings
2. **No Telemetry**: No data sent to third parties (except chosen AI provider)
3. **Local Options**: Full privacy with Ollama
4. **Context Control**: Users control what context is shared

---

For more details, see the source code and inline documentation.
