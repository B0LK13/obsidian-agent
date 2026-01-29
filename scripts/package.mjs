#!/usr/bin/env node
/**
 * Package script for Obsidian Agent Plugin
 * Creates distribution archives ready for release
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import os from 'os';

const REQUIRED_FILES = [
    'main.js',
    'manifest.json',
    'styles.css',
    'styles-enhanced.css'
];

const OPTIONAL_FILES = [
    'README.md',
    'LICENSE',
    'CHANGELOG.md',
    'versions.json'
];

function readManifest() {
    const manifestPath = path.join(process.cwd(), 'manifest.json');
    return JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
}

function checkRequiredFiles() {
    console.log('\n📋 Checking required files...\n');
    
    const missing = [];
    for (const file of REQUIRED_FILES) {
        const filePath = path.join(process.cwd(), file);
        if (!fs.existsSync(filePath)) {
            missing.push(file);
            console.log(`  ❌ Missing: ${file}`);
        } else {
            const stats = fs.statSync(filePath);
            const sizeKB = (stats.size / 1024).toFixed(2);
            console.log(`  ✅ ${file} (${sizeKB} KB)`);
        }
    }
    
    if (missing.length > 0) {
        console.error(`\n❌ Missing required files: ${missing.join(', ')}`);
        console.log('\nRun "npm run build" to generate main.js');
        process.exit(1);
    }
}

function copyToDist(distDir) {
    console.log('\n📦 Copying files to dist...\n');
    
    // Create dist directory
    if (!fs.existsSync(distDir)) {
        fs.mkdirSync(distDir, { recursive: true });
    }
    
    // Copy required files
    for (const file of REQUIRED_FILES) {
        const src = path.join(process.cwd(), file);
        const dest = path.join(distDir, file);
        if (fs.existsSync(src)) {
            fs.copyFileSync(src, dest);
            console.log(`  ✅ Copied: ${file}`);
        }
    }
    
    // Copy optional files if they exist
    for (const file of OPTIONAL_FILES) {
        const src = path.join(process.cwd(), file);
        const dest = path.join(distDir, file);
        if (fs.existsSync(src)) {
            fs.copyFileSync(src, dest);
            console.log(`  ✅ Copied: ${file}`);
        }
    }
}

function createZipArchive(distDir, outputName) {
    console.log('\n🗜️  Creating archive...\n');
    
    const outputPath = path.join(process.cwd(), `${outputName}.zip`);
    
    try {
        // Remove existing archive if present
        if (fs.existsSync(outputPath)) {
            fs.unlinkSync(outputPath);
        }
        
        // Create zip based on OS
        if (os.platform() === 'win32') {
            // Windows - use PowerShell
            const psCommand = `Compress-Archive -Path "${distDir}\*" -DestinationPath "${outputPath}" -Force`;
            execSync(psCommand, { shell: 'powershell.exe', stdio: 'ignore' });
        } else {
            // macOS/Linux - use zip command
            execSync(`cd "${distDir}" && zip -r "${outputPath}" .`, { stdio: 'ignore' });
        }
        
        const stats = fs.statSync(outputPath);
        const sizeKB = (stats.size / 1024).toFixed(2);
        console.log(`  ✅ Created: ${outputName}.zip (${sizeKB} KB)`);
        
        return outputPath;
    } catch (error) {
        console.error('  ❌ Failed to create archive:', error.message);
        process.exit(1);
    }
}

function generateReleaseNotes(manifest) {
    console.log('\n📝 Generating release notes...\n');
    
    const notesPath = path.join(process.cwd(), 'RELEASE_NOTES.md');
    const notes = `# Obsidian Agent v${manifest.version}

## Installation

### Manual Installation
1. Download \`obsidian-agent-${manifest.version}.zip\`
2. Extract to your vault's plugins folder: \`<vault>/.obsidian/plugins/obsidian-agent/\`
3. Reload Obsidian
4. Enable "Obsidian Agent" in Settings → Community Plugins

### From Community Plugins (Coming Soon)
Search for "Obsidian Agent" in Settings → Community Plugins → Browse

## Files Included
${REQUIRED_FILES.map(f => `- \`${f}\``).join('\n')}
${OPTIONAL_FILES.filter(f => fs.existsSync(path.join(process.cwd(), f))).map(f => `- \`${f}\``).join('\n')}

## Requirements
- Obsidian v${manifest.minAppVersion} or higher
- API key from OpenAI, Anthropic, or Ollama (local)

---
Generated on ${new Date().toISOString().split('T')[0]}
`;
    
    fs.writeFileSync(notesPath, notes);
    console.log(`  ✅ Created: RELEASE_NOTES.md`);
}

function main() {
    console.log('\n📦 Obsidian Agent Plugin Packager\n');
    
    const manifest = readManifest();
    const version = manifest.version;
    const pluginId = manifest.id;
    const distDir = path.join(process.cwd(), 'dist');
    const outputName = `${pluginId}-${version}`;
    
    console.log(`Version: ${version}`);
    console.log(`Plugin ID: ${pluginId}`);
    console.log(`Min Obsidian Version: ${manifest.minAppVersion}`);
    
    // Check required files
    checkRequiredFiles();
    
    // Clean and create dist
    if (fs.existsSync(distDir)) {
        fs.rmSync(distDir, { recursive: true });
    }
    
    // Copy files
    copyToDist(distDir);
    
    // Create archive
    const archivePath = createZipArchive(distDir, outputName);
    
    // Generate release notes
    generateReleaseNotes(manifest);
    
    // Summary
    console.log('\n✅ Packaging complete!\n');
    console.log('Output files:');
    console.log(`  📁 ${distDir}/`);
    console.log(`  📦 ${path.basename(archivePath)}`);
    console.log(`  📝 RELEASE_NOTES.md`);
    console.log('\nNext steps:');
    console.log('  1. Test the plugin in Obsidian');
    console.log('  2. Upload the zip file to GitHub Releases');
    console.log('  3. Copy RELEASE_NOTES.md content to release description\n');
}

main();
