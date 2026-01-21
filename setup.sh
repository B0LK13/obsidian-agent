#!/bin/bash
# Setup script for Obsidian Agent Python backend
# Creates virtual environment and installs dependencies

set -e

echo "Setting up Obsidian Agent Python backend..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Virtual environment path
VENV_DIR="$SCRIPT_DIR/venv"

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: python3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Display Python version
PYTHON_VERSION=$(python3 --version)
echo "Using $PYTHON_VERSION"

# Create virtual environment if it doesn't exist
if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment already exists at $VENV_DIR"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    else
        echo "Using existing virtual environment."
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment at $VENV_DIR..."
    python3 -m venv "$VENV_DIR"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install the package in editable mode with dependencies
echo "Installing obsidian-agent package and dependencies..."
pip install -e "$SCRIPT_DIR"

echo ""
echo "✓ Setup complete!"
echo ""
echo "To use the CLI:"
echo "  1. Run: source venv/bin/activate"
echo "  2. Then use: obsidian-agent --help"
echo ""
echo "Or use the wrapper script:"
echo "  ./bin/obsidian-agent --help"
echo ""
echo "Make the wrapper executable with:"
echo "  chmod +x bin/obsidian-agent"
