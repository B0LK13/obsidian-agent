# Contributing to Obsidian Agent

Thank you for your interest in contributing to Obsidian Agent! This document provides guidelines and instructions for contributing.

## 🤝 How to Contribute

### Reporting Bugs

1. **Check existing issues** to avoid duplicates
2. **Use the bug report template** when creating a new issue
3. **Include details:**
   - Obsidian version
   - Plugin version
   - Operating system
   - Steps to reproduce
   - Expected vs actual behavior
   - Error messages/screenshots

### Suggesting Features

1. **Check existing feature requests** first
2. **Describe the use case** clearly
3. **Explain why it would benefit users**
4. **Consider implementation complexity**

### Code Contributions

We welcome pull requests! Here's how to contribute code:

## 🚀 Development Setup

### Prerequisites

- **Node.js** 16+ and npm
- **Git**
- **Obsidian** (for testing)
- **Code editor** (VS Code recommended)

### Setup Steps

1. **Fork the repository**
   ```bash
   # Click "Fork" on GitHub
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/YOUR_USERNAME/obsidian-agent.git
   cd obsidian-agent
   ```

3. **Install dependencies**
   ```bash
   npm install
   ```

4. **Create a development branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

5. **Link to Obsidian vault for testing**
   ```bash
   # Create symlink to your test vault
   # Windows (PowerShell as Admin):
   New-Item -ItemType SymbolicLink -Path "C:\Users\YourName\Documents\Obsidian Vaults\TestVault\.obsidian\plugins\obsidian-agent" -Target "$(pwd)"
   
   # macOS/Linux:
   ln -s "$(pwd)" ~/Documents/Obsidian\ Vaults/TestVault/.obsidian/plugins/obsidian-agent
   ```

## 🔨 Development Workflow

### Build Commands

```bash
# Development build with watch mode
npm run dev

# Production build
npm run build

# Type checking
npm run check

# Linting
npm run lint

# Run tests
npm test
```

### Making Changes

1. **Write your code**
   - Follow existing code style
   - Use TypeScript
   - Add JSDoc comments for public APIs

2. **Test your changes**
   ```bash
   npm run build
   # Reload Obsidian and test manually
   ```

3. **Run linter**
   ```bash
   npm run lint
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add awesome feature"
   # or
   git commit -m "fix: resolve issue #123"
   ```

## 📝 Code Style Guidelines

### TypeScript

- Use **TypeScript strict mode**
- Prefer **const** over let
- Use **async/await** over promises
- Add **type annotations** for function parameters and returns
- Use **interfaces** for object shapes

### Naming Conventions

- **Classes**: PascalCase (`AIService`, `CacheManager`)
- **Functions/Methods**: camelCase (`generateCompletion`, `handleError`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_SETTINGS`, `MAX_RETRIES`)
- **Files**: camelCase or kebab-case (`aiService.ts`, `error-handler.ts`)

### Error Handling

Use our custom error classes from `src/errors.ts`:

```typescript
import { ValidationError, APIError } from './src/errors';

// Validate input
if (!prompt) {
  throw new ValidationError('Prompt is required', 'prompt');
}

// Handle API errors
try {
  const result = await api.call();
} catch (error) {
  throw new APIError('API call failed', 500, 'openai');
}
```

### Input Validation

Use the Validators utility from `src/validators.ts`:

```typescript
import { Validators } from './src/validators';

// Validate required fields
Validators.required(value, 'fieldName');

// Validate strings
Validators.notEmpty(str, 'prompt');

// Validate numbers
Validators.inRange(temp, 0, 2, 'temperature');
```

## 🧪 Testing

### Manual Testing

1. Build the plugin: `npm run build`
2. Reload Obsidian (Ctrl+R or Cmd+R)
3. Test the affected features
4. Check console for errors (Ctrl+Shift+I)

### Writing Tests

Add tests to the `tests/` directory:

```typescript
import { describe, it, expect } from 'vitest';

describe('MyFeature', () => {
  it('should do something', () => {
    // Test implementation
    expect(result).toBe(expected);
  });
});
```

Run tests:
```bash
npm test
```

## 📋 Commit Message Format

We use conventional commits:

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `perf`: Performance improvements
- `test`: Adding/updating tests
- `chore`: Maintenance tasks

### Examples

```bash
feat(cache): add batch operations for cache service

Implemented batch get and set operations to improve performance
when handling multiple cache entries.

Closes #97

fix(windows): resolve defender false positive

Added automated setup script for Windows Defender exclusions
and comprehensive documentation.

Fixes #104

docs(install): add Windows-specific installation guide

Created detailed guide with step-by-step instructions,
troubleshooting, and Ollama setup for Windows users.

Closes #111
```

## 🔍 Code Review Process

### Before Submitting PR

- [ ] Code builds without errors
- [ ] Linter passes (`npm run lint`)
- [ ] Tests pass (`npm test`)
- [ ] Manually tested in Obsidian
- [ ] Updated documentation if needed
- [ ] Commit messages follow conventions

### Creating Pull Request

1. **Push your branch**
   ```bash
   git push origin feature/your-feature-name
   ```

2. **Create PR on GitHub**
   - Use clear title describing the change
   - Reference related issues (#123)
   - Describe what changed and why
   - Add screenshots for UI changes
   - Check "Allow edits from maintainers"

3. **Respond to feedback**
   - Address review comments
   - Push additional commits
   - Be open to suggestions

## 🏗️ Project Structure

```
obsidian-agent/
├── src/
│   ├── errors.ts           # Custom error classes
│   ├── validators.ts       # Input validation
│   └── gpuMemoryManager.ts # GPU utilities
├── scripts/
│   └── setup-defender-exclusions.ps1
├── tests/
│   └── *.test.ts           # Test files
├── main.ts                 # Plugin entry point
├── aiService.ts            # AI API integration
├── cacheService.ts         # Response caching
├── settings.ts             # Settings interface
├── settingsTab.ts          # Settings UI
├── agentModalEnhanced.ts   # Chat UI
├── manifest.json           # Plugin metadata
├── package.json            # Dependencies
└── tsconfig.json           # TypeScript config
```

## 🎯 Areas for Contribution

### High Priority

- **Performance optimization** - Caching, lazy loading
- **Error handling** - Edge cases, better messages
- **Testing** - Unit tests, integration tests
- **Documentation** - Guides, examples, API docs

### Feature Ideas

- **Vector search** - Semantic note search
- **Link suggestions** - Auto-linking related notes
- **Dead link detection** - Find and fix broken links
- **Incremental indexing** - Fast updates for large vaults

### Good First Issues

Look for issues labeled `good first issue`:
- Documentation improvements
- Simple bug fixes
- Code cleanup
- Test additions

## 📚 Resources

### Documentation

- [Obsidian Plugin API](https://github.com/obsidianmd/obsidian-api)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [Plugin Development Guide](https://marcus.se.net/obsidian-plugin-docs/)

### Tools

- [Obsidian Developer Tools](https://github.com/obsidianmd/obsidian-api)
- [Hot Reload Plugin](https://github.com/pjeby/hot-reload) (for development)

## ❓ Getting Help

- **Questions:** [GitHub Discussions](https://github.com/B0LK13/obsidian-agent/discussions)
- **Bugs:** [GitHub Issues](https://github.com/B0LK13/obsidian-agent/issues)
- **Discord:** (Coming soon)

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Acknowledgments

Thank you for contributing to Obsidian Agent! Your efforts help make this plugin better for everyone.

---

**Questions?** Open a [discussion](https://github.com/B0LK13/obsidian-agent/discussions) or comment on an existing issue.
