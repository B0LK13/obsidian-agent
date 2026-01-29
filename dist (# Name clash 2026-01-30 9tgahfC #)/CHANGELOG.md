# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Production-ready build configuration with minification
- Comprehensive CI/CD pipeline with GitHub Actions
- Automated release and packaging scripts
- ESLint configuration for code quality
- Bundle size analysis and optimization

### Changed
- Enhanced esbuild configuration for production builds
- Updated TypeScript configuration with strict checks
- Improved .gitignore for cleaner repository

### Fixed
- Build optimization for smaller bundle size

## [1.0.0] - 2024-01-01

### Added
- Initial release of Obsidian Agent plugin
- AI-powered assistance with multiple providers (OpenAI, Anthropic, Ollama, Custom)
- Smart commands: Ask AI, Generate Summary, Expand Ideas, Improve Writing, Generate Outline
- AI Profile system for switching between different AI configurations
- Context-aware responses using note content
- Response caching for improved performance
- Token usage tracking and cost estimation
- Inline completions with configurable triggers
- Intelligent suggestions for links, tags, and improvements
- Vault-wide context gathering (linked notes, backlinks, tags, folders)
- Accessibility settings (high contrast, reduced motion)
- Conversation persistence and management
- Custom prompt templates

### Security
- Local-first storage for all settings and cache
- Secure API key storage in Obsidian vault
- No telemetry or external data collection

---

## Template for New Releases

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Now removed features

### Fixed
- Bug fixes

### Security
- Security improvements
