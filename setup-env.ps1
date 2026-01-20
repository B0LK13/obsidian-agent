#!/usr/bin/env pwsh
# PowerShell Environment Setup Script for Obsidian Agent
# Run this script to set up all necessary environment variables

Write-Host "🚀 Obsidian Agent - Environment Setup" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green
Write-Host ""

# Function to prompt for input with default value
function Get-UserInput {
    param(
        [string]$Prompt,
        [string]$Default = ""
    )
    
    if ($Default) {
        $userInput = Read-Host "$Prompt [$Default]"
        if ([string]::IsNullOrWhiteSpace($userInput)) {
            return $Default
        }
        return $userInput
    } else {
        return Read-Host $Prompt
    }
}

# Function to set environment variable
function Set-EnvVar {
    param(
        [string]$Name,
        [string]$Value,
        [switch]$UserScope
    )
    
    if ($UserScope) {
        [Environment]::SetEnvironmentVariable($Name, $Value, "User")
        Write-Host "✓ Set $Name (User scope)" -ForegroundColor Green
    } else {
        $env:Name = $Value
        Write-Host "✓ Set $Name (Session scope)" -ForegroundColor Yellow
    }
}

# Check if .env file exists
$envFile = Join-Path $PSScriptRoot ".env"
$envExampleFile = Join-Path $PSScriptRoot ".env.example"

if (-not (Test-Path $envExampleFile)) {
    Write-Host "❌ Error: .env.example file not found!" -ForegroundColor Red
    Write-Host "Please ensure .env.example exists in the project root." -ForegroundColor Red
    exit 1
}

# Ask user for setup mode
Write-Host "Setup Mode:" -ForegroundColor Cyan
Write-Host "1. Interactive setup (recommended)" -ForegroundColor White
Write-Host "2. Create .env from template" -ForegroundColor White
Write-Host "3. Set system environment variables (persistent)" -ForegroundColor White
Write-Host ""

$setupMode = Get-UserInput "Choose setup mode [1-3]" "1"

switch ($setupMode) {
    "1" {
        # Interactive setup
        Write-Host "`n📝 Interactive Setup" -ForegroundColor Cyan
        Write-Host "=====================" -ForegroundColor Cyan
        Write-Host ""
        
        # Vault Configuration
        Write-Host "📁 Vault Configuration" -ForegroundColor Yellow
        $vaultPath = Get-UserInput "Obsidian vault path" "$env:USERPROFILE\Documents\ObsidianVault"
        $excludeFolders = Get-UserInput "Exclude folders (comma-separated)" ".obsidian,templates,_archive"
        
        # Database Configuration
        Write-Host "`n💾 Database Configuration" -ForegroundColor Yellow
        $dbPath = Get-UserInput "Database path" "$env:LOCALAPPDATA\obsidian-agent\vault.db"
        $backupEnabled = Get-UserInput "Enable backups? (true/false)" "true"
        
        # Vector Store Configuration
        Write-Host "`n🧠 Vector Store Configuration" -ForegroundColor Yellow
        $chromaPath = Get-UserInput "ChromaDB directory" "$env:LOCALAPPDATA\obsidian-agent\chroma"
        $embeddingModel = Get-UserInput "Embedding model" "all-MiniLM-L6-v2"
        
        # AI Configuration
        Write-Host "`n🤖 AI Configuration" -ForegroundColor Yellow
        $aiProvider = Get-UserInput "AI Provider (openai/anthropic/ollama)" "openai"
        
        if ($aiProvider -eq "openai") {
            $apiKey = Read-Host "OpenAI API Key (will be hidden)" -AsSecureString
            $apiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                [Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey)
            )
            Set-EnvVar "OPENAI_API_KEY" $apiKeyPlain -UserScope
        } elseif ($aiProvider -eq "anthropic") {
            $apiKey = Read-Host "Anthropic API Key (will be hidden)" -AsSecureString
            $apiKeyPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                [Runtime.InteropServices.Marshal]::SecureStringToBSTR($apiKey)
            )
            Set-EnvVar "ANTHROPIC_API_KEY" $apiKeyPlain -UserScope
        } elseif ($aiProvider -eq "ollama") {
            $ollamaUrl = Get-UserInput "Ollama URL" "http://localhost:11434"
            Set-EnvVar "CUSTOM_API_URL" $ollamaUrl -UserScope
        }
        
        $aiModel = Get-UserInput "AI Model" "gpt-4"
        
        # Create .env file
        Write-Host "`n📄 Creating .env file..." -ForegroundColor Cyan
        
        $envContent = @"
# Obsidian Agent Environment Configuration
# Generated on $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

# Vault Configuration
OBSIDIAN_VAULT_PATH=$vaultPath
OBSIDIAN_VAULT__EXCLUDE_FOLDERS=$excludeFolders

# Database Configuration
OBSIDIAN_DATABASE__PATH=$dbPath
OBSIDIAN_DATABASE__BACKUP_ENABLED=$backupEnabled

# Vector Store Configuration
OBSIDIAN_VECTOR_STORE__PERSIST_DIRECTORY=$chromaPath
OBSIDIAN_VECTOR_STORE__EMBEDDING_MODEL=$embeddingModel
OBSIDIAN_VECTOR_STORE__COLLECTION_NAME=obsidian_notes

# AI Configuration
AI_PROVIDER=$aiProvider
AI_MODEL=$aiModel
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
"@
        
        $envContent | Out-File -FilePath $envFile -Encoding UTF8
        Write-Host "✓ Created .env file" -ForegroundColor Green
        
        # Set session environment variables
        Write-Host "`n🔧 Setting session environment variables..." -ForegroundColor Cyan
        Set-EnvVar "OBSIDIAN_VAULT_PATH" $vaultPath
        Set-EnvVar "OBSIDIAN_DATABASE__PATH" $dbPath
        Set-EnvVar "AI_PROVIDER" $aiProvider
        Set-EnvVar "AI_MODEL" $aiModel
        
        Write-Host "`n✅ Setup complete!" -ForegroundColor Green
        Write-Host "Environment variables are set for this session." -ForegroundColor Yellow
        Write-Host "To persist them, add them to your PowerShell profile or use option 3." -ForegroundColor Yellow
    }
    
    "2" {
        # Copy template
        Write-Host "`n📄 Creating .env from template..." -ForegroundColor Cyan
        
        if (Test-Path $envFile) {
            $overwrite = Get-UserInput ".env already exists. Overwrite? (y/n)" "n"
            if ($overwrite -ne "y") {
                Write-Host "❌ Cancelled." -ForegroundColor Red
                exit 0
            }
        }
        
        Copy-Item $envExampleFile $envFile
        Write-Host "✓ Created .env file" -ForegroundColor Green
        Write-Host "`nPlease edit .env and fill in your values." -ForegroundColor Yellow
        Write-Host "File location: $envFile" -ForegroundColor Cyan
    }
    
    "3" {
        # Set system environment variables
        Write-Host "`n⚙️ Setting system environment variables..." -ForegroundColor Cyan
        Write-Host "This will set variables persistently for your user account." -ForegroundColor Yellow
        Write-Host ""
        
        $confirm = Get-UserInput "Continue? (y/n)" "n"
        if ($confirm -ne "y") {
            Write-Host "❌ Cancelled." -ForegroundColor Red
            exit 0
        }
        
        # Core variables
        $vaultPath = Get-UserInput "Obsidian vault path" "$env:USERPROFILE\Documents\ObsidianVault"
        Set-EnvVar "OBSIDIAN_VAULT_PATH" $vaultPath -UserScope
        
        $dbPath = Get-UserInput "Database path" "$env:LOCALAPPDATA\obsidian-agent\vault.db"
        Set-EnvVar "OBSIDIAN_DATABASE__PATH" $dbPath -UserScope
        
        $chromaPath = Get-UserInput "ChromaDB directory" "$env:LOCALAPPDATA\obsidian-agent\chroma"
        Set-EnvVar "OBSIDIAN_VECTOR_STORE__PERSIST_DIRECTORY" $chromaPath -UserScope
        
        Write-Host "`n✅ System environment variables set!" -ForegroundColor Green
        Write-Host "Note: You may need to restart your terminal for changes to take effect." -ForegroundColor Yellow
    }
    
    default {
        Write-Host "❌ Invalid option. Exiting." -ForegroundColor Red
        exit 1
    }
}

Write-Host "`n📋 Next Steps:" -ForegroundColor Cyan
Write-Host "1. Review and edit .env file if needed" -ForegroundColor White
Write-Host "2. For Python backend:" -ForegroundColor White
Write-Host "   cd python_backend" -ForegroundColor Gray
Write-Host "   poetry install" -ForegroundColor Gray
Write-Host "3. For TypeScript plugin:" -ForegroundColor White
Write-Host "   npm install" -ForegroundColor Gray
Write-Host "   npm run build" -ForegroundColor Gray
Write-Host ""
Write-Host "For more information, see DEVELOPER.md" -ForegroundColor Yellow
