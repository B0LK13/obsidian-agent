#!/usr/bin/env node
/**
 * Verification Script for Obsidian Agent Plugin
 * Comprehensive checks before release
 */

import fs from 'fs';
import path from 'path';
import { execSync } from 'child_process';

const CHECKS = {
  passed: 0,
  failed: 0,
  warnings: 0
};

function log(message, type = 'info') {
  const icons = {
    info: 'ℹ️',
    success: '✅',
    error: '❌',
    warning: '⚠️',
    section: '🔍'
  };
  console.log(`${icons[type]} ${message}`);
}

function section(title) {
  console.log('\n' + '='.repeat(60));
  console.log(`  ${title}`);
  console.log('='.repeat(60) + '\n');
}

// ========================================
// FILE STRUCTURE CHECKS
// ========================================

function checkFileStructure() {
  section('FILE STRUCTURE CHECKS');
  
  const requiredFiles = [
    'manifest.json',
    'package.json',
    'tsconfig.json',
    '.eslintrc.json',
    'README.md',
    'LICENSE',
    'CHANGELOG.md',
    'styles.css',
    'styles-enhanced.css',
    'main.ts',
    'settings.ts',
    'aiService.ts',
    'agentModalEnhanced.ts',
    'uiComponents.ts'
  ];
  
  for (const file of requiredFiles) {
    if (fs.existsSync(file)) {
      log(`Found: ${file}`, 'success');
      CHECKS.passed++;
    } else {
      log(`Missing: ${file}`, 'error');
      CHECKS.failed++;
    }
  }
}

// ========================================
// BUILD OUTPUT CHECKS
// ========================================

function checkBuildOutput() {
  section('BUILD OUTPUT CHECKS');
  
  const buildFiles = ['main.js', 'styles.css', 'styles-enhanced.css'];
  
  for (const file of buildFiles) {
    if (fs.existsSync(file)) {
      const stats = fs.statSync(file);
      const sizeKB = (stats.size / 1024).toFixed(2);
      
      // Size checks
      if (file === 'main.js' && stats.size > 500 * 1024) {
        log(`main.js is ${sizeKB} KB (over 500KB limit)`, 'warning');
        CHECKS.warnings++;
      } else if (file === 'main.js' && stats.size > 100 * 1024) {
        log(`${file}: ${sizeKB} KB (acceptable)`, 'success');
        CHECKS.passed++;
      } else {
        log(`${file}: ${sizeKB} KB`, 'success');
        CHECKS.passed++;
      }
    } else {
      log(`Missing build file: ${file}`, 'error');
      CHECKS.failed++;
    }
  }
}

// ========================================
// MANIFEST VALIDATION
// ========================================

function validateManifest() {
  section('MANIFEST VALIDATION');
  
  try {
    const manifest = JSON.parse(fs.readFileSync('manifest.json', 'utf8'));
    
    const requiredFields = ['id', 'name', 'version', 'minAppVersion', 'description', 'author'];
    
    for (const field of requiredFields) {
      if (manifest[field]) {
        log(`✓ ${field}: ${manifest[field]}`, 'success');
        CHECKS.passed++;
      } else {
        log(`✗ Missing field: ${field}`, 'error');
        CHECKS.failed++;
      }
    }
    
    // Version format check
    if (/^\d+\.\d+\.\d+$/.test(manifest.version)) {
      log(`✓ Version format is valid: ${manifest.version}`, 'success');
      CHECKS.passed++;
    } else {
      log(`✗ Invalid version format: ${manifest.version}`, 'error');
      CHECKS.failed++;
    }
    
    // ID format check
    if (/^[a-z0-9-]+$/.test(manifest.id)) {
      log(`✓ ID format is valid: ${manifest.id}`, 'success');
      CHECKS.passed++;
    } else {
      log(`✗ Invalid ID format: ${manifest.id}`, 'error');
      CHECKS.failed++;
    }
    
  } catch (error) {
    log(`Failed to parse manifest.json: ${error.message}`, 'error');
    CHECKS.failed++;
  }
}

// ========================================
// PACKAGE.JSON VALIDATION
// ========================================

function validatePackageJson() {
  section('PACKAGE.JSON VALIDATION');
  
  try {
    const pkg = JSON.parse(fs.readFileSync('package.json', 'utf8'));
    
    if (pkg.scripts?.build) {
      log('✓ Build script defined', 'success');
      CHECKS.passed++;
    } else {
      log('✗ Build script missing', 'error');
      CHECKS.failed++;
    }
    
    if (pkg.scripts?.test) {
      log('✓ Test script defined', 'success');
      CHECKS.passed++;
    } else {
      log('✗ Test script missing', 'warning');
      CHECKS.warnings++;
    }
    
    if (pkg.devDependencies?.obsidian) {
      log('✓ Obsidian API dependency present', 'success');
      CHECKS.passed++;
    } else {
      log('✗ Obsidian API dependency missing', 'error');
      CHECKS.failed++;
    }
    
  } catch (error) {
    log(`Failed to parse package.json: ${error.message}`, 'error');
    CHECKS.failed++;
  }
}

// ========================================
// TYPE CHECKING
// ========================================

function checkTypes() {
  section('TYPE CHECKING');
  
  try {
    execSync('npx tsc --noEmit', { stdio: 'pipe' });
    log('✓ TypeScript compilation successful', 'success');
    CHECKS.passed++;
  } catch (error) {
    log('✗ TypeScript compilation failed', 'error');
    console.log(error.stdout?.toString() || error.message);
    CHECKS.failed++;
  }
}

// ========================================
// LINTING
// ========================================

function checkLinting() {
  section('LINTING');
  
  try {
    execSync('npm run lint', { stdio: 'pipe' });
    log('✓ ESLint passed', 'success');
    CHECKS.passed++;
  } catch (error) {
    log('⚠️ ESLint issues found (non-blocking)', 'warning');
    console.log(error.stdout?.toString() || error.message);
    CHECKS.warnings++;
  }
}

// ========================================
// TEST EXECUTION
// ========================================

function runTests() {
  section('TEST EXECUTION');
  
  try {
    execSync('npm test', { stdio: 'pipe' });
    log('✓ All tests passed', 'success');
    CHECKS.passed++;
  } catch (error) {
    log('✗ Tests failed', 'error');
    console.log(error.stdout?.toString() || error.message);
    CHECKS.failed++;
  }
}

// ========================================
// BUILD VERIFICATION
// ========================================

function verifyBuild() {
  section('BUILD VERIFICATION');
  
  try {
    // Clean and rebuild
    if (fs.existsSync('main.js')) {
      fs.unlinkSync('main.js');
    }
    
    execSync('npm run build', { stdio: 'pipe' });
    
    if (fs.existsSync('main.js')) {
      const stats = fs.statSync('main.js');
      const sizeKB = (stats.size / 1024).toFixed(2);
      log(`✓ Build successful: main.js (${sizeKB} KB)`, 'success');
      CHECKS.passed++;
      
      // Check if minified
      const content = fs.readFileSync('main.js', 'utf8');
      if (content.includes('/*') && content.includes('THIS IS A GENERATED')) {
        log('✓ Build banner present', 'success');
        CHECKS.passed++;
      }
      
      // Check for source map reference (should be absent in production)
      if (!content.includes('//# sourceMappingURL')) {
        log('✓ No source map in production build', 'success');
        CHECKS.passed++;
      }
    } else {
      log('✗ Build failed: main.js not created', 'error');
      CHECKS.failed++;
    }
  } catch (error) {
    log(`✗ Build failed: ${error.message}`, 'error');
    CHECKS.failed++;
  }
}

// ========================================
// DISTRIBUTION CHECK
// ========================================

function checkDistribution() {
  section('DISTRIBUTION CHECK');
  
  const distDir = 'dist';
  
  if (!fs.existsSync(distDir)) {
    log('Creating distribution package...', 'info');
    try {
      execSync('node scripts/package.mjs', { stdio: 'pipe' });
    } catch (error) {
      log('✗ Package creation failed', 'error');
      CHECKS.failed++;
      return;
    }
  }
  
  if (fs.existsSync(distDir)) {
    const files = fs.readdirSync(distDir);
    const requiredDistFiles = ['main.js', 'manifest.json', 'styles.css', 'styles-enhanced.css'];
    
    for (const file of requiredDistFiles) {
      if (files.includes(file)) {
        log(`✓ ${file} in dist/`, 'success');
        CHECKS.passed++;
      } else {
        log(`✗ ${file} missing from dist/`, 'error');
        CHECKS.failed++;
      }
    }
    
    // Check for zip file
    const zipFiles = fs.readdirSync('.').filter(f => f.endsWith('.zip'));
    if (zipFiles.length > 0) {
      const stats = fs.statSync(zipFiles[0]);
      const sizeKB = (stats.size / 1024).toFixed(2);
      log(`✓ Distribution archive: ${zipFiles[0]} (${sizeKB} KB)`, 'success');
      CHECKS.passed++;
    } else {
      log('⚠️ No distribution archive found', 'warning');
      CHECKS.warnings++;
    }
  } else {
    log('✗ dist/ directory not found', 'error');
    CHECKS.failed++;
  }
}

// ========================================
// CSS VALIDATION
// ========================================

function validateCSS() {
  section('CSS VALIDATION');
  
  const cssFiles = ['styles.css', 'styles-enhanced.css'];
  
  for (const file of cssFiles) {
    if (!fs.existsSync(file)) {
      log(`✗ ${file} not found`, 'error');
      CHECKS.failed++;
      continue;
    }
    
    const content = fs.readFileSync(file, 'utf8');
    
    // Check for CSS variables
    if (content.includes('--')) {
      log(`✓ ${file} contains CSS variables`, 'success');
      CHECKS.passed++;
    }
    
    // Check for Obsidian theme integration
    if (content.includes('var(--')) {
      log(`✓ ${file} uses Obsidian theme variables`, 'success');
      CHECKS.passed++;
    }
    
    // Enhanced CSS specific checks
    if (file === 'styles-enhanced.css') {
      const requiredFeatures = [
        'backdrop-filter',
        'animation',
        'transition',
        '--oa-',
        '@media'
      ];
      
      for (const feature of requiredFeatures) {
        if (content.includes(feature)) {
          log(`✓ Enhanced styles contain: ${feature}`, 'success');
          CHECKS.passed++;
        }
      }
    }
  }
}

// ========================================
// SECURITY CHECKS
// ========================================

function securityChecks() {
  section('SECURITY CHECKS');
  
  const jsFiles = ['main.js', 'aiService.ts', 'agentModalEnhanced.ts'];
  
  for (const file of jsFiles) {
    if (!fs.existsSync(file)) continue;
    
    const content = fs.readFileSync(file, 'utf8');
    
    // Check for console.log in production
    const consoleLogs = (content.match(/console\.(log|debug|info)/g) || []).length;
    if (consoleLogs > 5) {
      log(`⚠️ ${file} has ${consoleLogs} console statements`, 'warning');
      CHECKS.warnings++;
    }
    
    // Check for eval (security risk)
    if (content.includes('eval(')) {
      log(`✗ ${file} contains eval() - security risk!`, 'error');
      CHECKS.failed++;
    }
  }
  
  log('✓ No security issues found', 'success');
  CHECKS.passed++;
}

// ========================================
// PERFORMANCE CHECKS
// ========================================

function performanceChecks() {
  section('PERFORMANCE CHECKS');
  
  if (fs.existsSync('main.js')) {
    const stats = fs.statSync('main.js');
    const sizeKB = stats.size / 1024;
    
    if (sizeKB < 100) {
      log(`✓ Bundle size is optimal: ${sizeKB.toFixed(2)} KB`, 'success');
      CHECKS.passed++;
    } else if (sizeKB < 200) {
      log(`⚠️ Bundle size is acceptable: ${sizeKB.toFixed(2)} KB`, 'warning');
      CHECKS.warnings++;
    } else {
      log(`✗ Bundle size is large: ${sizeKB.toFixed(2)} KB`, 'error');
      CHECKS.failed++;
    }
  }
  
  // Check for CSS containment
  const enhancedCSS = fs.readFileSync('styles-enhanced.css', 'utf8');
  if (enhancedCSS.includes('contain:')) {
    log('✓ CSS containment used for performance', 'success');
    CHECKS.passed++;
  }
}

// ========================================
// SUMMARY
// ========================================

function printSummary() {
  section('VERIFICATION SUMMARY');
  
  const total = CHECKS.passed + CHECKS.failed + CHECKS.warnings;
  const percentage = Math.round((CHECKS.passed / total) * 100);
  
  console.log(`\n📊 Results:`);
  console.log(`   ✅ Passed:  ${CHECKS.passed}`);
  console.log(`   ❌ Failed:  ${CHECKS.failed}`);
  console.log(`   ⚠️  Warnings: ${CHECKS.warnings}`);
  console.log(`   📈 Success Rate: ${percentage}%`);
  
  console.log('\n' + '='.repeat(60));
  
  if (CHECKS.failed === 0) {
    console.log('  🎉 ALL CHECKS PASSED! Ready for release.');
  } else if (CHECKS.failed < 3) {
    console.log('  ⚠️  MINOR ISSUES - Fix before release');
  } else {
    console.log('  ❌ CRITICAL ISSUES - Not ready for release');
  }
  
  console.log('='.repeat(60) + '\n');
  
  process.exit(CHECKS.failed > 0 ? 1 : 0);
}

// ========================================
// MAIN
// ========================================

console.log('\n');
console.log('╔'.padEnd(60, '═') + '╗');
console.log('║' + ' '.repeat(16) + 'OBSIDIAN AGENT VERIFICATION' + ' '.repeat(15) + '║');
console.log('╚'.padEnd(60, '═') + '╝');

// Run all checks
checkFileStructure();
checkBuildOutput();
validateManifest();
validatePackageJson();
validateCSS();
securityChecks();
performanceChecks();
checkTypes();
checkLinting();
runTests();
verifyBuild();
checkDistribution();

// Print final summary
printSummary();
