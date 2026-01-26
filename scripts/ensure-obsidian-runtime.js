const { existsSync, mkdirSync, writeFileSync } = require('node:fs');
const path = require('node:path');

const shimPath = path.join(process.cwd(), 'node_modules', 'obsidian', 'index.js');

if (!existsSync(shimPath)) {
	mkdirSync(path.dirname(shimPath), { recursive: true });
	writeFileSync(shimPath, 'module.exports = {};\n');
}
