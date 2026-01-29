#!/usr/bin/env node
/**
 * Version bump script for Obsidian Agent Plugin
 * Updates version in manifest.json and creates versions.json entry
 */

import { readFileSync, writeFileSync } from "fs";

const targetVersion = process.env.npm_package_version;

if (!targetVersion) {
    console.error("❌ npm_package_version not set");
    process.exit(1);
}

// Read manifest.json
const manifest = JSON.parse(readFileSync("manifest.json", "utf8"));
const { minAppVersion } = manifest;
manifest.version = targetVersion;

// Write manifest.json
writeFileSync("manifest.json", JSON.stringify(manifest, null, "\t"));
console.log(`✅ Updated manifest.json to version ${targetVersion}`);

// Update versions.json
let versions = {};
try {
    versions = JSON.parse(readFileSync("versions.json", "utf8"));
} catch (e) {
    console.log("Creating new versions.json");
}

versions[targetVersion] = minAppVersion;
writeFileSync("versions.json", JSON.stringify(versions, null, "\t"));
console.log(`✅ Updated versions.json`);
