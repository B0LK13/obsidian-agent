#!/bin/bash

################################################################################
#   FOLLOW-UP ACTIONS EXECUTION SCRIPT
#   Execute all immediate actions from FOLLOW_UP_ACTIONS.md
################################################################################

echo ""
echo "================================================================================"
echo "   PKM-Agent Follow-Up Actions - Immediate Execution"
echo "================================================================================"
echo ""
echo "This script will execute all Day 1 immediate actions:"
echo "  1. Environment verification"
echo "  2. Dependency installation"
echo "  3. Comprehensive testing"
echo "  4. POC demonstration"
echo "  5. TypeScript plugin build"
echo ""
echo "Estimated total time: 60 minutes"
echo ""
read -p "Press Enter to continue..."

# Set project paths
PROJECT_ROOT="C:/Users/Admin/Documents/B0LK13v2/B0LK13v2"
PKM_AGENT="$PROJECT_ROOT/pkm-agent"
OBSIDIAN_PLUGIN="$PROJECT_ROOT/obsidian-pkm-agent"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo ""
echo "================================================================================"
echo "   STEP 1: ENVIRONMENT VERIFICATION (5 minutes)"
echo "================================================================================"
echo ""
echo "Running verify_setup.py..."
echo ""

cd "$PROJECT_ROOT" || exit 1
if [ -f "verify_setup.py" ]; then
    python verify_setup.py
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}[ERROR] Environment verification failed!${NC}"
        echo "Please review the output above and fix any issues."
        read -p "Press Enter to continue..."
        exit 1
    fi
    echo ""
    echo -e "${GREEN}[SUCCESS] Environment verification complete!${NC}"
else
    echo -e "${YELLOW}[WARNING] verify_setup.py not found!${NC}"
    echo "Skipping environment verification..."
fi

echo ""
read -p "Press Enter to continue..."

echo ""
echo "================================================================================"
echo "   STEP 2: INSTALL PYTHON DEPENDENCIES (10 minutes)"
echo "================================================================================"
echo ""
echo "Installing Python dependencies for pkm-agent..."
echo ""

cd "$PKM_AGENT" || exit 1
if [ -f "pyproject.toml" ]; then
    echo "Installing in editable mode with dev dependencies..."
    pip install -e ".[dev]"
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}[ERROR] Failed to install Python dependencies!${NC}"
        echo ""
        echo "Trying without dev dependencies..."
        pip install -e .
        if [ $? -ne 0 ]; then
            echo ""
            echo -e "${RED}[ERROR] Installation failed completely!${NC}"
            echo "Please check your Python installation and try manually:"
            echo "  cd $PKM_AGENT"
            echo "  pip install -e \".[dev]\""
            read -p "Press Enter to continue..."
            exit 1
        fi
    fi
    echo ""
    echo -e "${GREEN}[SUCCESS] Python dependencies installed!${NC}"
else
    echo -e "${RED}[ERROR] pyproject.toml not found!${NC}"
    echo "Expected at: $PKM_AGENT/pyproject.toml"
    read -p "Press Enter to continue..."
    exit 1
fi

echo ""
read -p "Press Enter to continue..."

echo ""
echo "================================================================================"
echo "   STEP 3: RUN COMPREHENSIVE TESTS (15 minutes)"
echo "================================================================================"
echo ""
echo "Running test_comprehensive.py..."
echo "This will generate test_results.json with detailed results."
echo ""

cd "$PROJECT_ROOT" || exit 1
if [ -f "test_comprehensive.py" ]; then
    python test_comprehensive.py
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${YELLOW}[WARNING] Some tests failed!${NC}"
        echo "Review the output above for details."
        echo ""
        read -p "Continue anyway? (Press Ctrl+C to abort, Enter to continue)"
    else
        echo ""
        echo -e "${GREEN}[SUCCESS] All tests passed!${NC}"
    fi
    
    # Check if results file was created
    if [ -f "test_results.json" ]; then
        echo ""
        echo "Test results saved to: test_results.json"
        echo ""
        echo "Opening results file..."
        cat test_results.json
    fi
else
    echo -e "${YELLOW}[WARNING] test_comprehensive.py not found!${NC}"
    echo "Skipping comprehensive tests..."
fi

echo ""
read -p "Press Enter to continue..."

echo ""
echo "================================================================================"
echo "   STEP 4: RUN INTERACTIVE POC DEMO (15 minutes)"
echo "================================================================================"
echo ""
echo "Running demo_poc.py..."
echo "This is an interactive demonstration - follow the prompts."
echo ""
read -p "Press Enter to start the demo, or Ctrl+C to skip..."

cd "$PROJECT_ROOT" || exit 1
if [ -f "demo_poc.py" ]; then
    python demo_poc.py
    echo ""
    echo -e "${GREEN}[SUCCESS] Demo complete!${NC}"
else
    echo -e "${YELLOW}[WARNING] demo_poc.py not found!${NC}"
    echo "Skipping POC demo..."
fi

echo ""
read -p "Press Enter to continue..."

echo ""
echo "================================================================================"
echo "   STEP 5: BUILD TYPESCRIPT PLUGIN (15 minutes)"
echo "================================================================================"
echo ""
echo "Building Obsidian plugin..."
echo ""

cd "$OBSIDIAN_PLUGIN" || exit 1
if [ -f "package.json" ]; then
    echo "Installing npm dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}[ERROR] npm install failed!${NC}"
        echo "Please check your Node.js installation."
        read -p "Press Enter to continue..."
        exit 1
    fi
    
    echo ""
    echo "Building plugin..."
    npm run build
    if [ $? -ne 0 ]; then
        echo ""
        echo -e "${RED}[ERROR] Build failed!${NC}"
        echo "Please check the output above for errors."
        read -p "Press Enter to continue..."
        exit 1
    fi
    
    echo ""
    echo -e "${GREEN}[SUCCESS] Plugin built successfully!${NC}"
    echo ""
    echo "Build output should be in: $OBSIDIAN_PLUGIN/build"
    
else
    echo -e "${RED}[ERROR] package.json not found!${NC}"
    echo "Expected at: $OBSIDIAN_PLUGIN/package.json"
    read -p "Press Enter to continue..."
    exit 1
fi

echo ""
read -p "Press Enter to continue..."

echo ""
echo "================================================================================"
echo "   STEP 6: VERIFY INSTALLATIONS"
echo "================================================================================"
echo ""
echo "Checking installed components..."
echo ""

echo "Python version:"
python --version

echo ""
echo "Node.js version:"
node --version

echo ""
echo "npm version:"
npm --version

echo ""
echo "Installed Python packages (pkm-agent):"
cd "$PKM_AGENT" || exit 1
pip list | grep -E "pkm-agent|websockets|rapidfuzz|watchdog"

echo ""
echo "TypeScript build artifacts:"
cd "$OBSIDIAN_PLUGIN" || exit 1
if [ -d "build" ]; then
    echo -e "${GREEN}[SUCCESS] Build directory exists${NC}"
    ls -la build/
else
    echo -e "${YELLOW}[WARNING] Build directory not found!${NC}"
fi

echo ""
read -p "Press Enter to continue..."

echo ""
echo "================================================================================"
echo "   EXECUTION COMPLETE!"
echo "================================================================================"
echo ""
echo "Summary of actions completed:"
echo "  [*] Environment verification"
echo "  [*] Python dependencies installed"
echo "  [*] Comprehensive tests run"
echo "  [*] POC demo executed"
echo "  [*] TypeScript plugin built"
echo ""
echo "Next steps (from FOLLOW_UP_ACTIONS.md):"
echo "  1. Review DEPLOYMENT_CHECKLIST.md"
echo "  2. Create production vault backup"
echo "  3. Configure production settings"
echo "  4. Deploy backend to production"
echo "  5. Deploy plugin to Obsidian"
echo ""
echo "For detailed next steps, see:"
echo "  $PROJECT_ROOT/FOLLOW_UP_ACTIONS.md"
echo "  $PROJECT_ROOT/SPRINT_PLANNING.md"
echo ""
echo "================================================================================"
