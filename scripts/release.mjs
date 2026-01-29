#!/usr/bin/env node
/**
 * Release script for Obsidian Agent Plugin
 * Automates the release process including version bumping and git tagging
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';
import readline from 'readline';

const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout
});

function question(query) {
    return new Promise(resolve => rl.question(query, resolve));
}

function getVersionType(currentVersion) {
    const parts = currentVersion.split('.');
    const major = parseInt(parts[0]);
    const minor = parseInt(parts[1]);
    const patch = parseInt(parts[2]);
    
    return {
        major: `${major + 1}.0.0`,
        minor: `${major}.${minor + 1}.0`,
        patch: `${major}.${minor}.${patch + 1}`
    };
}

async function main() {
    console.log('\n🚀 Obsidian Agent Plugin Release\n');
    
    // Read current manifest
    const manifestPath = path.join(process.cwd(), 'manifest.json');
    const manifest = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    const currentVersion = manifest.version;
    
    console.log(`Current version: ${currentVersion}`);
    
    const versions = getVersionType(currentVersion);
    console.log('\nVersion options:');
    console.log(`  1. Patch (${versions.patch}) - Bug fixes`);
    console.log(`  2. Minor (${versions.minor}) - New features`);
    console.log(`  3. Major (${versions.major}) - Breaking changes`);
    console.log(`  4. Custom version`);
    
    const choice = await question('\nSelect version bump (1-4): ');
    
    let newVersion;
    switch (choice.trim()) {
        case '1':
            newVersion = versions.patch;
            break;
        case '2':
            newVersion = versions.minor;
            break;
        case '3':
            newVersion = versions.major;
            break;
        case '4':
            newVersion = await question('Enter custom version (x.x.x): ');
            break;
        default:
            console.log('❌ Invalid choice');
            process.exit(1);
    }
    
    if (!/^\d+\.\d+\.\d+$/.test(newVersion)) {
        console.log('❌ Invalid version format. Use x.x.x');
        process.exit(1);
    }
    
    // Update manifest.json
    manifest.version = newVersion;
    fs.writeFileSync(manifestPath, JSON.stringify(manifest, null, '\t'));
    console.log(`✅ Updated manifest.json to ${newVersion}`);
    
    // Update versions.json
    const versionsPath = path.join(process.cwd(), 'versions.json');
    const versionsData = JSON.parse(fs.readFileSync(versionsPath, 'utf8'));
    versionsData[newVersion] = manifest.minAppVersion;
    fs.writeFileSync(versionsPath, JSON.stringify(versionsData, null, '\t'));
    console.log(`✅ Updated versions.json`);
    
    // Update package.json
    const packagePath = path.join(process.cwd(), 'package.json');
    const packageData = JSON.parse(fs.readFileSync(packagePath, 'utf8'));
    packageData.version = newVersion;
    fs.writeFileSync(packagePath, JSON.stringify(packageData, null, 2));
    console.log(`✅ Updated package.json`);
    
    // Update CHANGELOG.md if it exists
    const changelogPath = path.join(process.cwd(), 'CHANGELOG.md');
    if (fs.existsSync(changelogPath)) {
        const date = new Date().toISOString().split('T')[0];
        const changelog = fs.readFileSync(changelogPath, 'utf8');
        const newEntry = `## [${newVersion}] - ${date}\n\n### Added\n- \n\n### Changed\n- \n\n### Fixed\n- \n\n`;
        fs.writeFileSync(changelogPath, newEntry + changelog);
        console.log(`✅ Updated CHANGELOG.md`);
    }
    
    // Git operations
    const commitMessage = await question('\nEnter commit message (or press Enter for default): ');
    const finalMessage = commitMessage.trim() || `Release version ${newVersion}`;
    
    try {
        execSync('git add manifest.json versions.json package.json', { stdio: 'inherit' });
        if (fs.existsSync(changelogPath)) {
            execSync('git add CHANGELOG.md', { stdio: 'inherit' });
        }
        execSync(`git commit -m "${finalMessage}"`, { stdio: 'inherit' });
        execSync(`git tag ${newVersion}`, { stdio: 'inherit' });
        
        console.log('\n✅ Release prepared!');
        console.log(`\nNext steps:`);
        console.log(`  1. Review the changes: git show HEAD`);
        console.log(`  2. Push to remote: git push origin main --tags`);
        console.log(`  3. Create a release on GitHub with the tag ${newVersion}`);
        console.log(`  4. Run: npm run package to create distribution files\n`);
        
    } catch (error) {
        console.error('❌ Git operation failed:', error.message);
        process.exit(1);
    }
    
    rl.close();
}

main().catch(err => {
    console.error('❌ Release failed:', err);
    process.exit(1);
});
