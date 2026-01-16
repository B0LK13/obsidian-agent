# Changelog

All notable changes to the Obsidian Agent plugin will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

[1.0.0]: https://github.com/B0LK13/obsidian-agent/releases/tag/v1.0.0
