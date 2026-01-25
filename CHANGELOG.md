# Changelog

All notable changes to the Obsidian Agent plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-01-25

### Added - Major Feature Release
- **Chat Sidebar**: Persistent AI chat interface with conversation history
- **Custom Templates**: Template system with 8 built-in templates for common tasks
- **Token Tracking**: Comprehensive usage tracking with cost estimation
- **Response Caching**: Intelligent caching system for faster repeated queries
- **Conversation History**: Multi-turn conversations with context retention
- **Batch Processing**: Framework for processing multiple notes (in development)

#### New Commands (14 additional commands)
- Translate Text to default language
- Generate Code from Description
- Explain Selected Code
- Find and Fix Errors in Code
- Generate Table of Contents
- Generate Tags for Note
- Create Flashcards from Note
- Brainstorm Ideas
- Generate Meeting Notes Template
- Rephrase Selected Text
- Make Text More Professional
- Make Text More Casual
- Show Token Usage Statistics
- Clear Response Cache
- Open AI Chat Sidebar

#### Advanced Settings
- Conversation history length configuration
- Cache size and expiration settings
- Token tracking enable/disable
- Custom template management
- Smart suggestions toggle
- Auto-linking feature
- Default language selection
- Streaming support (foundation)

### Enhanced
- AI Service now supports conversation context
- Improved error handling with detailed messages
- Better response validation for all providers
- Enhanced token estimation algorithm
- Optimized caching strategy

### Technical
- New modules: `conversationHistory.ts`, `templateManager.ts`, `tokenTracker.ts`, `responseCache.ts`, `batchProcessor.ts`, `chatView.ts`
- Expanded settings interface with 12 new configuration options
- Enhanced CSS with chat view and stats styling
- Ribbon icon for quick chat access
- View registration for sidebar integration

## [1.0.0] - 2026-01-16

### Added
- Initial release of Obsidian Agent
- AI integration with OpenAI, Anthropic, and custom API support
- Six core commands:
  - Ask AI Agent: Interactive dialog for custom AI queries
  - Generate Summary: Automatic text summarization
  - Expand Ideas: Transform brief notes into detailed content
  - Improve Writing: Enhance clarity, grammar, and style
  - Generate Outline: Create structured outlines from topics
  - Answer Question: Context-aware question answering
- Comprehensive settings panel:
  - API provider selection (OpenAI, Anthropic, Custom)
  - Model configuration
  - Temperature and max tokens control
  - Custom system prompts
  - Context awareness toggle
- Plugin styling with Obsidian theme compatibility
- Full TypeScript implementation
- Build system with esbuild
- Comprehensive documentation

### Security
- Local API key storage
- No third-party data sharing beyond chosen AI provider
- User-controlled context sharing

[2.0.0]: https://github.com/B0LK13/obsidian-agent/releases/tag/v2.0.0
[1.0.0]: https://github.com/B0LK13/obsidian-agent/releases/tag/v1.0.0
