# Obsidian Agent - Directory Structure

This document provides a complete overview of the plugin's file organization.

## 📁 Root Directory

```
obsidian-agent/
├── 📄 Core Files
│   ├── manifest.json              # Plugin metadata for Obsidian
│   ├── package.json               # Node.js dependencies and scripts
│   ├── tsconfig.json              # TypeScript configuration
│   ├── .eslintrc.json             # ESLint code quality rules
│   ├── .gitignore                 # Git ignore patterns
│   └── versions.json              # Version compatibility info
│
├── 📖 Documentation
│   ├── README.md                  # Main documentation
│   ├── CHANGELOG.md               # Version history
│   ├── LICENSE                    # MIT License
│   ├── DIRECTORY_STRUCTURE.md     # This file
│   ├── UI_ENHANCEMENTS.md         # UI feature documentation
│   ├── PRODUCTION_OPTIMIZATIONS.md # Build optimization guide
│   ├── TEST_REPORT.md             # Test verification results
│   └── RELEASE_NOTES.md           # Auto-generated release notes
│
├── 💻 Source Code
│   ├── main.ts                    # Plugin entry point
│   ├── settings.ts                # Settings interfaces and defaults
│   ├── settingsTab.ts             # Settings UI components
│   ├── aiService.ts               # AI API integration
│   ├── cacheService.ts            # Response caching
│   ├── contextProvider.ts         # Vault context gathering
│   ├── agentModal.ts              # Original chat modal
│   ├── agentModalEnhanced.ts      # Enhanced 2025 UI modal ⭐
│   ├── uiComponents.ts            # Reusable UI components ⭐
│   ├── promptTemplates.ts         # AI prompt templates
│   ├── tokenCounter.ts            # Token usage tracking
│   ├── inlineCompletionService.ts # Inline text completion
│   └── suggestionService.ts       # Intelligent suggestions
│
├── 🎨 Styles
│   ├── styles.css                 # Base styles (12.92 KB)
│   └── styles-enhanced.css        # 2025 UI styles (20.79 KB) ⭐
│
├── 🧪 Tests
│   ├── tests/
│   │   ├── inlineCompletionService.test.ts
│   │   ├── uiComponents.test.ts   # UI component tests
│   │   └── setupTests.ts          # Test environment setup
│   └── vitest.config.ts           # Vitest configuration
│
├── 🔧 Build & Scripts
│   ├── esbuild.config.mjs         # ESBuild configuration
│   ├── version-bump.mjs           # Version management
│   └── scripts/
│       ├── verify.mjs             # Full verification suite
│       ├── release.mjs            # Release automation
│       ├── package.mjs            # Package creation
│       └── ensure-obsidian-runtime.js # Test runtime stub
│
├── ⚙️ Configuration
│   └── .github/
│       └── workflows/
│           └── ci.yml             # GitHub Actions CI/CD
│
├── 📦 Distribution
│   ├── dist/                      # Distribution files
│   │   ├── main.js
│   │   ├── manifest.json
│   │   ├── styles.css
│   │   ├── styles-enhanced.css
│   │   ├── README.md
│   │   ├── LICENSE
│   │   ├── CHANGELOG.md
│   │   └── versions.json
│   └── obsidian-agent-1.0.0.zip   # Distribution archive
│
└── 🔨 Build Output
    ├── main.js                    # Compiled plugin (94.30 KB)
    ├── build-meta.json            # Build metadata
    └── node_modules/              # Dependencies (not in repo)
```

## 📄 File Details

### Core Plugin Files

| File | Purpose | Size |
|------|---------|------|
| `main.ts` | Plugin entry point, command registration, lifecycle | ~19 KB |
| `settings.ts` | TypeScript interfaces, default values, profile types | ~10 KB |
| `aiService.ts` | API communication, streaming, error handling | ~22 KB |
| `agentModalEnhanced.ts` | Enhanced chat UI with 2025 design patterns | ~22 KB |
| `uiComponents.ts` | Reusable UI components (typing, reactions, voice) | ~18 KB |

### Style Files

| File | Purpose | Size |
|------|---------|------|
| `styles.css` | Base Obsidian-compatible styles | 12.92 KB |
| `styles-enhanced.css` | Liquid glass, animations, 2025 UI | 20.79 KB |

### Configuration Files

| File | Purpose |
|------|---------|
| `manifest.json` | Plugin ID, version, requirements for Obsidian |
| `package.json` | NPM scripts, dependencies, metadata |
| `tsconfig.json` | TypeScript compiler options |
| `.eslintrc.json` | Code quality rules |

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | User documentation, installation, usage |
| `CHANGELOG.md` | Version history and changes |
| `UI_ENHANCEMENTS.md` | Detailed UI feature documentation |
| `PRODUCTION_OPTIMIZATIONS.md` | Build optimization details |
| `TEST_REPORT.md` | Test results and verification |

## 🎯 Key Directories

### `/src` (Development)
Contains TypeScript source files that get compiled to JavaScript.

### `/tests` (Testing)
Contains unit tests using Vitest framework.

### `/scripts` (Automation)
Contains Node.js scripts for build, release, and verification automation.

### `/dist` (Distribution)
Contains files ready for distribution. This is what users install.

### `/.github/workflows` (CI/CD)
Contains GitHub Actions configuration for automated testing and releases.

## 📦 Distribution Package

The final distribution package (`obsidian-agent-1.0.0.zip`) contains:

```
obsidian-agent-1.0.0.zip
├── main.js              # Compiled and minified plugin code
├── manifest.json        # Plugin metadata
├── styles.css           # Base styles
├── styles-enhanced.css  # Enhanced 2025 UI styles
├── README.md            # Documentation
├── LICENSE              # MIT License
├── CHANGELOG.md         # Version history
└── versions.json        # Version compatibility
```

## 🔧 Installation Paths

### Development Installation
```
<Vault>/.obsidian/plugins/obsidian-agent/
├── (all source files)
├── node_modules/
└── main.js (after build)
```

### Production Installation
```
<Vault>/.obsidian/plugins/obsidian-agent/
├── main.js
├── manifest.json
├── styles.css
├── styles-enhanced.css
├── README.md
├── LICENSE
├── CHANGELOG.md
└── versions.json
```

## 📝 File Size Summary

| Category | Total Size |
|----------|------------|
| Source Code | ~110 KB |
| Styles | ~34 KB |
| Documentation | ~35 KB |
| Tests | ~8 KB |
| **Distribution** | **~73 KB** |
| **Compiled** | **~94 KB** |

## 🔄 Build Process

```
Source Files (.ts)
       ↓
  TypeScript Compiler
       ↓
ESBuild (bundle + minify)
       ↓
   main.js
       ↓
Package Script
       ↓
obsidian-agent-1.0.0.zip
```

## 🎯 Entry Points

| Context | Entry Point |
|---------|-------------|
| Obsidian Plugin | `main.ts` → `main.js` |
| Settings UI | `settingsTab.ts` |
| Chat Modal | `agentModalEnhanced.ts` |
| AI Service | `aiService.ts` |
| Tests | `tests/*.test.ts` |

## 🚫 Files Not in Repository

These files are generated or installed and should not be committed:

- `node_modules/` - NPM dependencies
- `main.js` - Compiled output
- `build-meta.json` - Build metadata
- `dist/` - Distribution folder
- `*.zip` - Distribution archives
- `RELEASE_NOTES.md` - Auto-generated
- `.cache/` - Cache files

## 📋 Checklist for Contributors

When adding new features:

- [ ] Add source file to root or `/src`
- [ ] Add tests to `/tests`
- [ ] Update `README.md` with new features
- [ ] Update `CHANGELOG.md` with changes
- [ ] Ensure `manifest.json` version is updated
- [ ] Run `npm run build` successfully
- [ ] Run `npm test` with all tests passing
- [ ] Run `node scripts/verify.mjs` with 100% success

---

**Last Updated**: 2026-01-29  
**Version**: 1.0.0
