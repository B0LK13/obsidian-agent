# Contributing to Obsidian Agent

Thank you for your interest in contributing to Obsidian Agent! This document provides guidelines and information to help you contribute effectively.

## Table of Contents

- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Code Style](#code-style)
- [Testing](#testing)
- [Submitting Changes](#submitting-changes)
- [Issue Guidelines](#issue-guidelines)
- [Pull Request Process](#pull-request-process)

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/obsidian-agent.git
   cd obsidian-agent
   ```
3. **Install dependencies**:
   ```bash
   npm install
   ```

## Development Setup

### Prerequisites

- Node.js 18+ (LTS recommended)
- npm 9+
- Git
- An Obsidian vault for testing

### Building the Plugin

```bash
# Development build with hot reload
npm run dev

# Production build
npm run build

# Run tests
npm test

# Run linter
npm run lint

# Full verification
node scripts/verify.mjs
```

### Installing for Development

1. Build the plugin:
   ```bash
   npm run build
   ```
2. Copy/symlink to your vault's plugins folder:
   ```bash
   # Linux/macOS
   ln -s $(pwd) /path/to/vault/.obsidian/plugins/obsidian-agent
   
   # Windows (PowerShell as Admin)
   New-Item -ItemType SymbolicLink -Path "C:\path\to\vault\.obsidian\plugins\obsidian-agent" -Target (Get-Location)
   ```
3. Enable the plugin in Obsidian settings

### Testing with Ollama (Recommended)

For development, we recommend using [Ollama](https://ollama.ai/) for free, local AI:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull a model
ollama pull llama2

# Run Ollama server
ollama serve
```

Then configure the plugin to use Ollama with `http://localhost:11434`.

## Code Style

### TypeScript Guidelines

- Use TypeScript strict mode
- Prefer `const` over `let`
- Use explicit types for function parameters and return values
- Use interfaces for object shapes
- Avoid `any` type when possible (use `unknown` if necessary)

### Naming Conventions

| Type | Convention | Example |
|------|------------|---------|
| Files | camelCase | `aiService.ts` |
| Classes | PascalCase | `AIService` |
| Functions/Methods | camelCase | `generateCompletion` |
| Constants | UPPER_SNAKE_CASE | `DEFAULT_SETTINGS` |
| Interfaces | PascalCase | `CompletionResult` |
| Type aliases | PascalCase | `StreamCallback` |

### Code Comments

- Use JSDoc for public APIs
- Add inline comments for complex logic
- Keep comments up-to-date with code changes

```typescript
/**
 * Generate AI completion for the given prompt.
 * @param prompt - The user's prompt
 * @param context - Optional note context
 * @returns Promise resolving to completion result
 */
async generateCompletion(prompt: string, context?: string): Promise<CompletionResult>
```

## Testing

### Running Tests

```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run specific test file
npm test -- tests/aiService.test.ts
```

### Writing Tests

We use [Vitest](https://vitest.dev/) for testing. Tests are located in the `tests/` directory.

```typescript
import { describe, it, expect, vi } from 'vitest';
import { MyService } from '../myService';

describe('MyService', () => {
    it('should do something', () => {
        const service = new MyService();
        expect(service.doSomething()).toBe(expectedResult);
    });
});
```

### Test Guidelines

- Write tests for new features and bug fixes
- Aim for meaningful test coverage of core functionality
- Mock external dependencies (API calls, file system)
- Test edge cases and error conditions

## Submitting Changes

### Before Submitting

1. **Run the linter**: `npm run lint`
2. **Run tests**: `npm test`
3. **Build successfully**: `npm run build`
4. **Update documentation** if needed

### Commit Messages

Follow the [Conventional Commits](https://www.conventionalcommits.org/) format:

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or fixing tests
- `chore`: Maintenance tasks

Examples:
```
feat(ai): add support for Claude 3 API
fix(chat): resolve message ordering issue
docs: update installation instructions
```

## Issue Guidelines

### Reporting Bugs

Include:
- Obsidian version
- Plugin version
- Operating system
- Steps to reproduce
- Expected vs actual behavior
- Console errors (if any)

### Feature Requests

Include:
- Clear description of the feature
- Use case / problem it solves
- Proposed implementation (optional)
- Mockups or examples (if applicable)

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feat/my-feature
   ```

2. **Make your changes** with clear, focused commits

3. **Ensure all checks pass**:
   ```bash
   npm run lint
   npm test
   npm run build
   ```

4. **Push to your fork**:
   ```bash
   git push origin feat/my-feature
   ```

5. **Open a Pull Request** with:
   - Clear title describing the change
   - Description of what and why
   - Link to related issue(s)
   - Screenshots for UI changes

6. **Address review feedback** promptly

### PR Review Criteria

- Code follows project style guidelines
- Tests are included for new functionality
- Documentation is updated if needed
- No breaking changes (or clearly documented)
- Build and tests pass

## Getting Help

- 📖 Check the [README](README.md) and docs
- 🔍 Search existing [issues](https://github.com/B0LK13/obsidian-agent/issues)
- 💬 Open a [discussion](https://github.com/B0LK13/obsidian-agent/discussions)
- 🐛 File a [bug report](https://github.com/B0LK13/obsidian-agent/issues/new)

## License

By contributing to Obsidian Agent, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing! 🎉
