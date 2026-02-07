#!/bin/bash
# Comprehensive Test and POC Runner for Unix/Linux/Mac
# Run this script to test all implementations and see the demo

set -e

echo "========================================"
echo "PKM-Agent Test and Demo Suite"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check Python
echo "[1/5] Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found"
    echo "Please install Python 3.11+"
    exit 1
fi
python3 --version
echo ""

# Install dependencies
echo "[2/5] Installing dependencies..."
cd "$SCRIPT_DIR/pkm-agent"
python3 -m pip install -e ".[dev]"
echo ""

# Run comprehensive tests
echo "[3/5] Running comprehensive test suite..."
cd "$SCRIPT_DIR"
python3 test_comprehensive.py
if [ $? -ne 0 ]; then
    echo "WARNING: Some tests failed"
    echo "Check test_results.json for details"
else
    echo "SUCCESS: All tests passed!"
fi
echo ""
read -p "Press ENTER to continue to demo..."

# Run POC demo
echo "[4/5] Running Proof of Concept demo..."
echo "This is an interactive demo - follow the prompts"
echo ""
python3 demo_poc.py
echo ""

# Build TypeScript plugin
echo "[5/5] Building TypeScript plugin..."
cd "$SCRIPT_DIR/obsidian-pkm-agent"
if [ -d "node_modules" ]; then
    echo "Running npm build..."
    npm run build
    if [ $? -eq 0 ]; then
        echo "SUCCESS: Plugin built successfully"
        echo "Output: main.js"
    else
        echo "ERROR: Build failed"
    fi
else
    echo "WARNING: node_modules not found"
    echo "Run 'npm install' first to build the plugin"
fi
cd "$SCRIPT_DIR"
echo ""

echo "========================================"
echo "Test and Demo Complete"
echo "========================================"
echo ""
echo "Check the following:"
echo "  - test_results.json (test results)"
echo "  - obsidian-pkm-agent/main.js (built plugin)"
echo ""
echo "Next steps:"
echo "  1. Review test results"
echo "  2. Copy plugin to Obsidian vault"
echo "  3. Follow DEPLOYMENT_CHECKLIST.md"
echo ""
