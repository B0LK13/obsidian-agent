# Contributing to Obsidian Agent

Thank you for your interest in contributing to Obsidian Agent! This document provides guidelines for contributing to the project.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Install dependencies: `npm install`
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn
- Obsidian (for testing)

### Local Development

1. Clone the repo into your Obsidian vault's plugins folder:
   ```bash
   cd /path/to/vault/.obsidian/plugins
   git clone https://github.com/B0LK13/obsidian-agent.git
   cd obsidian-agent
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Run the development build (with hot reload):
   ```bash
   npm run dev
   ```

4. In Obsidian:
   - Open Settings → Community Plugins
   - Reload plugins or restart Obsidian
   - Enable "Obsidian Agent"

### Making Changes

1. Create a new branch for your feature or fix:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes following the code style guidelines

3. Test your changes thoroughly

4. Commit your changes with clear, descriptive messages:
   ```bash
   git commit -m "Add feature: description of what you added"
   ```

## Code Style Guidelines

- Use TypeScript for all new code
- Follow the existing code structure and naming conventions
- Use meaningful variable and function names
- Add comments for complex logic
- Keep functions focused and modular
- Use async/await for asynchronous operations

## Testing

Before submitting a PR:

1. Build the plugin without errors:
   ```bash
   npm run build
   ```

2. Test all commands in Obsidian
3. Verify settings changes work correctly
4. Test with different AI providers (if applicable)
5. Check for console errors

## Pull Request Process

1. Update the README.md if you've added new features
2. Update the version number in manifest.json following semantic versioning
3. Describe your changes clearly in the PR description
4. Link any related issues
5. Wait for review and address any feedback

## Feature Requests

Have an idea for a new feature? Please:

1. Check existing issues to avoid duplicates
2. Open a new issue with the "enhancement" label
3. Clearly describe the feature and its benefits
4. Be open to discussion and feedback

## Bug Reports

Found a bug? Please:

1. Check if it's already reported in issues
2. Open a new issue with the "bug" label
3. Include:
   - Steps to reproduce
   - Expected behavior
   - Actual behavior
   - Obsidian version
   - Plugin version
   - Error messages or console logs

## Code of Conduct

- Be respectful and constructive
- Welcome newcomers and help them learn
- Focus on what's best for the community
- Show empathy towards others

## Questions?

If you have questions about contributing, feel free to:
- Open a discussion on GitHub
- Ask in the issues section
- Reach out to the maintainers

Thank you for contributing! 🎉
