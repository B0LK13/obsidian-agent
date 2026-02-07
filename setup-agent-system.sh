#!/bin/bash
# Setup script for Obsidian Agent System with AgentZero and MCP

set -e

echo "🚀 Setting up Obsidian Agent System..."
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check prerequisites
echo "📋 Checking prerequisites..."

# Check Node.js
if ! command -v node &> /dev/null; then
    echo -e "${YELLOW}⚠️  Node.js not found. Please install Node.js 18+${NC}"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo -e "${YELLOW}⚠️  Python 3 not found. Please install Python 3.11+${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Node.js version: $(node --version)${NC}"
echo -e "${GREEN}✓ Python version: $(python3 --version)${NC}"
echo ""

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p .mcp
mkdir -p pkm-agent/data
mkdir -p pkm-agent/.pkm-agent
echo -e "${GREEN}✓ Directories created${NC}"
echo ""

# Install Obsidian MCP Server
echo "📦 Installing Obsidian MCP Server..."
if ! command -v npx &> /dev/null; then
    echo -e "${YELLOW}⚠️  npx not found. Installing...${NC}"
    npm install -g npx
fi

# Check if obsidian-mcp-server is available
if npx obsidian-mcp-server --version &> /dev/null; then
    echo -e "${GREEN}✓ Obsidian MCP Server already installed${NC}"
else
    echo "Installing obsidian-mcp-server globally..."
    npm install -g obsidian-mcp-server
    echo -e "${GREEN}✓ Obsidian MCP Server installed${NC}"
fi
echo ""

# Install Python dependencies
echo "📦 Installing Python PKM Agent..."
cd pkm-agent

# Check if .venv exists
if [ ! -d ".venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing package dependencies..."
pip install -e ".[dev,ollama]"

echo -e "${GREEN}✓ Python PKM Agent installed${NC}"
deactivate
cd ..
echo ""

# Install Obsidian plugin dependencies
echo "📦 Installing Obsidian plugin dependencies..."
cd obsidian-pkm-agent

if [ ! -d "node_modules" ]; then
    echo "Installing npm packages..."
    npm install
    echo -e "${GREEN}✓ Obsidian plugin dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Obsidian plugin dependencies already installed${NC}"
fi

# Build plugin
echo "Building Obsidian plugin..."
npm run build
echo -e "${GREEN}✓ Obsidian plugin built${NC}"

cd ..
echo ""

# Configure MCP settings
echo "⚙️  Configuring MCP settings..."

if [ ! -f ".mcp/config.json" ]; then
    echo "MCP config not found. Please edit .mcp/config.json with your settings."
    echo "Required settings:"
    echo "  - OBSIDIAN_API_KEY: Your Obsidian Local REST API key"
    echo "  - PKMA_LLM__API_KEY: Your OpenAI API key (or Ollama config)"
else
    echo -e "${GREEN}✓ MCP config exists${NC}"
fi
echo ""

# Create example environment file
echo "📝 Creating example environment file..."
cat > pkm-agent/.env.example << 'EOF'
# LLM Configuration
PKMA_LLM__PROVIDER=openai
PKMA_LLM__MODEL=gpt-4o-mini
PKMA_LLM__API_KEY=your-openai-api-key-here

# For Ollama, use:
# PKMA_LLM__PROVIDER=ollama
# PKMA_LLM__MODEL=llama2
# PKMA_LLM__BASE_URL=http://localhost:11434

# RAG Configuration
PKMA_RAG__EMBEDDING_MODEL=all-MiniLM-L6-v2
PKMA_RAG__CHUNK_SIZE=512
PKMA_RAG__TOP_K=5

# Paths
PKMA_PKM_ROOT=./pkm
PKMA_DATA_DIR=./.pkm-agent
PKMA_DB_PATH=./data/pkm.db
PKMA_CHROMA_PATH=./data/chroma

# MCP Configuration
MCP_LOG_LEVEL=info
OBSIDIAN_BASE_URL=http://127.0.0.1:27123
OBSIDIAN_API_KEY=your-obsidian-api-key-here
OBSIDIAN_VERIFY_SSL=false
OBSIDIAN_ENABLE_CACHE=true
EOF

echo -e "${GREEN}✓ Example environment file created at pkm-agent/.env.example${NC}"
echo ""

# Create startup script
echo "🚀 Creating startup script..."

cat > start-agent-system.sh << 'EOF'
#!/bin/bash
# Startup script for Obsidian Agent System

echo "🚀 Starting Obsidian Agent System..."

# Check if Obsidian Local REST API is running
if ! curl -s http://127.0.0.1:27123 > /dev/null; then
    echo "⚠️  Obsidian Local REST API is not running."
    echo "Please ensure Obsidian is running with the Local REST API plugin enabled."
    exit 1
fi

echo "✓ Obsidian Local REST API is running"

# Start PKM RAG MCP Server
echo "Starting PKM RAG MCP Server..."
cd pkm-agent
source .venv/bin/activate

# Run MCP server in background
python -m pkm_agent.mcp_server &
MCP_PID=$!

echo "PKM RAG MCP Server started (PID: $MCP_PID)"
echo ""
echo "✓ Agent system is ready!"
echo ""
echo "You can now:"
echo "  1. Open Obsidian (if not already open)"
echo "  2. Enable the PKM Agent plugin in Obsidian settings"
echo "  3. Start using the agent from the sidebar"
echo ""
echo "To stop the MCP server, run: kill $MCP_PID"
echo ""
echo "Or press Ctrl+C to stop..."

# Wait for user to stop
wait $MCP_PID
EOF

chmod +x start-agent-system.sh

echo -e "${GREEN}✓ Startup script created: start-agent-system.sh${NC}"
echo ""

# Final instructions
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo ""
echo "1. Configure your API keys:"
echo "   - Edit .mcp/config.json"
echo "   - Copy pkm-agent/.env.example to pkm-agent/.env"
echo "   - Add your API keys to both files"
echo ""
echo "2. Start Obsidian and enable the Local REST API plugin:"
echo "   - Settings → Community Plugins → Obsidian Local REST API"
echo "   - Generate an API key"
echo "   - Note the base URL (default: http://127.0.0.1:27123)"
echo ""
echo "3. Copy the Obsidian plugin to your vault:"
echo "   - Copy obsidian-pkm-agent/dist/* to ~/.obsidian/plugins/obsidian-pkm-agent/"
echo ""
echo "4. Enable the PKM Agent plugin in Obsidian:"
echo "   - Settings → Community Plugins → PKM Agent"
echo ""
echo "5. Start the agent system:"
echo "   - Run: ./start-agent-system.sh"
echo ""
echo "6. Open the PKM Agent sidebar in Obsidian and start chatting!"
echo ""
echo "📚 For detailed documentation, see: AGENTZERO_OBSIDIAN_INTEGRATION.md"
echo ""
