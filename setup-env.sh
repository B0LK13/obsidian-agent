#!/bin/bash
# Bash Environment Setup Script for Obsidian Agent
# Run this script to set up all necessary environment variables

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Obsidian Agent - Environment Setup${NC}"
echo -e "${GREEN}=====================================${NC}"
echo ""

# Function to prompt for input with default value
prompt_input() {
    local prompt="$1"
    local default="$2"
    local result
    
    if [ -n "$default" ]; then
        read -p "$prompt [$default]: " result
        echo "${result:-$default}"
    else
        read -p "$prompt: " result
        echo "$result"
    fi
}

# Function to prompt for password (hidden input)
prompt_password() {
    local prompt="$1"
    local result
    
    read -s -p "$prompt: " result
    echo ""
    echo "$result"
}

# Check if .env.example exists
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"
ENV_EXAMPLE_FILE="$SCRIPT_DIR/.env.example"

if [ ! -f "$ENV_EXAMPLE_FILE" ]; then
    echo -e "${RED}❌ Error: .env.example file not found!${NC}"
    echo -e "${RED}Please ensure .env.example exists in the project root.${NC}"
    exit 1
fi

# Determine shell config file
SHELL_CONFIG=""
if [ -n "$BASH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.bashrc"
elif [ -n "$ZSH_VERSION" ]; then
    SHELL_CONFIG="$HOME/.zshrc"
fi

# Ask user for setup mode
echo -e "${CYAN}Setup Mode:${NC}"
echo -e "${NC}1. Interactive setup (recommended)${NC}"
echo -e "${NC}2. Create .env from template${NC}"
echo -e "${NC}3. Add to shell config (~/.bashrc or ~/.zshrc)${NC}"
echo ""

SETUP_MODE=$(prompt_input "Choose setup mode [1-3]" "1")

case $SETUP_MODE in
    1)
        # Interactive setup
        echo -e "\n${CYAN}📝 Interactive Setup${NC}"
        echo -e "${CYAN}=====================${NC}"
        echo ""
        
        # Vault Configuration
        echo -e "${YELLOW}📁 Vault Configuration${NC}"
        VAULT_PATH=$(prompt_input "Obsidian vault path" "$HOME/Documents/ObsidianVault")
        EXCLUDE_FOLDERS=$(prompt_input "Exclude folders (comma-separated)" ".obsidian,templates,_archive")
        
        # Database Configuration
        echo -e "\n${YELLOW}💾 Database Configuration${NC}"
        DB_PATH=$(prompt_input "Database path" "$HOME/.local/share/obsidian-agent/vault.db")
        BACKUP_ENABLED=$(prompt_input "Enable backups? (true/false)" "true")
        
        # Vector Store Configuration
        echo -e "\n${YELLOW}🧠 Vector Store Configuration${NC}"
        CHROMA_PATH=$(prompt_input "ChromaDB directory" "$HOME/.local/share/obsidian-agent/chroma")
        EMBEDDING_MODEL=$(prompt_input "Embedding model" "all-MiniLM-L6-v2")
        
        # AI Configuration
        echo -e "\n${YELLOW}🤖 AI Configuration${NC}"
        AI_PROVIDER=$(prompt_input "AI Provider (openai/anthropic/ollama)" "openai")
        
        API_KEY=""
        if [ "$AI_PROVIDER" = "openai" ]; then
            API_KEY=$(prompt_password "OpenAI API Key (will be hidden)")
            API_KEY_VAR="OPENAI_API_KEY=$API_KEY"
        elif [ "$AI_PROVIDER" = "anthropic" ]; then
            API_KEY=$(prompt_password "Anthropic API Key (will be hidden)")
            API_KEY_VAR="ANTHROPIC_API_KEY=$API_KEY"
        elif [ "$AI_PROVIDER" = "ollama" ]; then
            OLLAMA_URL=$(prompt_input "Ollama URL" "http://localhost:11434")
            API_KEY_VAR="CUSTOM_API_URL=$OLLAMA_URL"
        fi
        
        AI_MODEL=$(prompt_input "AI Model" "gpt-4")
        
        # Create .env file
        echo -e "\n${CYAN}📄 Creating .env file...${NC}"
        
        cat > "$ENV_FILE" << EOF
# Obsidian Agent Environment Configuration
# Generated on $(date "+%Y-%m-%d %H:%M:%S")

# Vault Configuration
OBSIDIAN_VAULT_PATH=$VAULT_PATH
OBSIDIAN_VAULT__EXCLUDE_FOLDERS=$EXCLUDE_FOLDERS

# Database Configuration
OBSIDIAN_DATABASE__PATH=$DB_PATH
OBSIDIAN_DATABASE__BACKUP_ENABLED=$BACKUP_ENABLED

# Vector Store Configuration
OBSIDIAN_VECTOR_STORE__PERSIST_DIRECTORY=$CHROMA_PATH
OBSIDIAN_VECTOR_STORE__EMBEDDING_MODEL=$EMBEDDING_MODEL
OBSIDIAN_VECTOR_STORE__COLLECTION_NAME=obsidian_notes

# AI Configuration
AI_PROVIDER=$AI_PROVIDER
$API_KEY_VAR
AI_MODEL=$AI_MODEL
AI_TEMPERATURE=0.7
AI_MAX_TOKENS=2000

# Search Configuration
OBSIDIAN_SEARCH__DEFAULT_LIMIT=10
OBSIDIAN_SEARCH__SEMANTIC_THRESHOLD=0.7

# Logging
LOG_LEVEL=INFO
LOG_ENABLE_CONSOLE=true
LOG_MAX_ENTRIES=1000

# Cache
CACHE_ENABLED=true
CACHE_MAX_ENTRIES=100
CACHE_MAX_AGE_DAYS=30

# Performance
ENABLE_EMBEDDINGS=true
USE_GPU=false
EOF
        
        echo -e "${GREEN}✓ Created .env file${NC}"
        
        # Export for current session
        echo -e "\n${CYAN}🔧 Setting environment variables for current session...${NC}"
        export OBSIDIAN_VAULT_PATH="$VAULT_PATH"
        export OBSIDIAN_DATABASE__PATH="$DB_PATH"
        export AI_PROVIDER="$AI_PROVIDER"
        export AI_MODEL="$AI_MODEL"
        
        if [ "$AI_PROVIDER" = "openai" ]; then
            export OPENAI_API_KEY="$API_KEY"
        elif [ "$AI_PROVIDER" = "anthropic" ]; then
            export ANTHROPIC_API_KEY="$API_KEY"
        fi
        
        echo -e "${GREEN}✓ Environment variables set for current session${NC}"
        
        # Offer to add to shell config
        if [ -n "$SHELL_CONFIG" ]; then
            echo ""
            ADD_TO_SHELL=$(prompt_input "Add to $SHELL_CONFIG for persistence? (y/n)" "n")
            if [ "$ADD_TO_SHELL" = "y" ]; then
                echo "" >> "$SHELL_CONFIG"
                echo "# Obsidian Agent environment variables" >> "$SHELL_CONFIG"
                echo "export OBSIDIAN_VAULT_PATH=\"$VAULT_PATH\"" >> "$SHELL_CONFIG"
                echo "export OBSIDIAN_DATABASE__PATH=\"$DB_PATH\"" >> "$SHELL_CONFIG"
                echo "export AI_PROVIDER=\"$AI_PROVIDER\"" >> "$SHELL_CONFIG"
                echo "export AI_MODEL=\"$AI_MODEL\"" >> "$SHELL_CONFIG"
                
                if [ "$AI_PROVIDER" = "openai" ]; then
                    echo "export OPENAI_API_KEY=\"$API_KEY\"" >> "$SHELL_CONFIG"
                elif [ "$AI_PROVIDER" = "anthropic" ]; then
                    echo "export ANTHROPIC_API_KEY=\"$API_KEY\"" >> "$SHELL_CONFIG"
                fi
                
                echo -e "${GREEN}✓ Added to $SHELL_CONFIG${NC}"
                echo -e "${YELLOW}Note: Run 'source $SHELL_CONFIG' or restart your terminal${NC}"
            fi
        fi
        
        echo -e "\n${GREEN}✅ Setup complete!${NC}"
        ;;
    
    2)
        # Copy template
        echo -e "\n${CYAN}📄 Creating .env from template...${NC}"
        
        if [ -f "$ENV_FILE" ]; then
            OVERWRITE=$(prompt_input ".env already exists. Overwrite? (y/n)" "n")
            if [ "$OVERWRITE" != "y" ]; then
                echo -e "${RED}❌ Cancelled.${NC}"
                exit 0
            fi
        fi
        
        cp "$ENV_EXAMPLE_FILE" "$ENV_FILE"
        echo -e "${GREEN}✓ Created .env file${NC}"
        echo -e "\n${YELLOW}Please edit .env and fill in your values.${NC}"
        echo -e "${CYAN}File location: $ENV_FILE${NC}"
        ;;
    
    3)
        # Add to shell config
        if [ -z "$SHELL_CONFIG" ]; then
            echo -e "${RED}❌ Could not determine shell config file${NC}"
            exit 1
        fi
        
        echo -e "\n${CYAN}⚙️ Adding to $SHELL_CONFIG...${NC}"
        echo -e "${YELLOW}This will add variables persistently for your shell.${NC}"
        echo ""
        
        CONFIRM=$(prompt_input "Continue? (y/n)" "n")
        if [ "$CONFIRM" != "y" ]; then
            echo -e "${RED}❌ Cancelled.${NC}"
            exit 0
        fi
        
        # Core variables
        VAULT_PATH=$(prompt_input "Obsidian vault path" "$HOME/Documents/ObsidianVault")
        DB_PATH=$(prompt_input "Database path" "$HOME/.local/share/obsidian-agent/vault.db")
        CHROMA_PATH=$(prompt_input "ChromaDB directory" "$HOME/.local/share/obsidian-agent/chroma")
        
        echo "" >> "$SHELL_CONFIG"
        echo "# Obsidian Agent environment variables" >> "$SHELL_CONFIG"
        echo "export OBSIDIAN_VAULT_PATH=\"$VAULT_PATH\"" >> "$SHELL_CONFIG"
        echo "export OBSIDIAN_DATABASE__PATH=\"$DB_PATH\"" >> "$SHELL_CONFIG"
        echo "export OBSIDIAN_VECTOR_STORE__PERSIST_DIRECTORY=\"$CHROMA_PATH\"" >> "$SHELL_CONFIG"
        
        echo -e "${GREEN}✓ Added to $SHELL_CONFIG${NC}"
        echo -e "\n${GREEN}✅ Setup complete!${NC}"
        echo -e "${YELLOW}Note: Run 'source $SHELL_CONFIG' or restart your terminal${NC}"
        ;;
    
    *)
        echo -e "${RED}❌ Invalid option. Exiting.${NC}"
        exit 1
        ;;
esac

echo -e "\n${CYAN}📋 Next Steps:${NC}"
echo -e "${NC}1. Review and edit .env file if needed${NC}"
echo -e "${NC}2. For Python backend:${NC}"
echo -e "   ${CYAN}cd python_backend${NC}"
echo -e "   ${CYAN}poetry install${NC}"
echo -e "${NC}3. For TypeScript plugin:${NC}"
echo -e "   ${CYAN}npm install${NC}"
echo -e "   ${CYAN}npm run build${NC}"
echo ""
echo -e "${YELLOW}For more information, see DEVELOPER.md${NC}"
