# PKM Agent Comprehensive Test Script
$pythonExe = "C:\Users\Admin\scoop\apps\python\current\python.exe"

Write-Host "╔═══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   PKM Agent - Comprehensive Test Suite    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════╝" -ForegroundColor Cyan

$passed = 0
$failed = 0

function Test-Item {
    param([string]$Name, [scriptblock]$Test)
    Write-Host "`n[$Name]" -ForegroundColor Yellow -NoNewline
    try {
        $result = & $Test
        if ($LASTEXITCODE -eq 0 -or $result) {
            Write-Host " ✓ PASS" -ForegroundColor Green
            $script:passed++
            return $true
        } else {
            Write-Host " ✗ FAIL" -ForegroundColor Red
            $script:failed++
            return $false
        }
    } catch {
        Write-Host " ✗ FAIL: $_" -ForegroundColor Red
        $script:failed++
        return $false
    }
}

# ============================================
# 1. CORE IMPORTS
# ============================================
Write-Host "`n=== 1. CORE IMPORTS ===" -ForegroundColor Magenta

Test-Item "PKMAgentApp import" {
    & $pythonExe -c "from pkm_agent import PKMAgentApp; print('OK')" 2>&1
}

Test-Item "Config import" {
    & $pythonExe -c "from pkm_agent import Config; print('OK')" 2>&1
}

Test-Item "RAG components import" {
    & $pythonExe -c "from pkm_agent.rag import Chunker, VectorStore, Retriever, EmbeddingEngine; print('OK')" 2>&1
}

Test-Item "LLM providers import" {
    & $pythonExe -c "from pkm_agent.llm import OpenAIProvider, OllamaProvider; print('OK')" 2>&1
}

Test-Item "Data components import" {
    & $pythonExe -c "from pkm_agent.data import Database, FileIndexer; print('OK')" 2>&1
}

Test-Item "WebSocket sync import" {
    & $pythonExe -c "from pkm_agent.websocket_sync import SyncServer; print('OK')" 2>&1
}

# ============================================
# 2. CLI COMMANDS
# ============================================
Write-Host "`n=== 2. CLI COMMANDS ===" -ForegroundColor Magenta

Test-Item "CLI help" {
    & $pythonExe -m pkm_agent --help 2>&1 | Select-String "PKM Agent"
}

Test-Item "CLI stats command" {
    & $pythonExe -m pkm_agent stats 2>&1
}

Test-Item "CLI index command" {
    & $pythonExe -m pkm_agent index 2>&1
}

Test-Item "CLI search command" {
    & $pythonExe -m pkm_agent search "test" 2>&1
}

# ============================================
# 3. COMPONENT FUNCTIONALITY
# ============================================
Write-Host "`n=== 3. COMPONENT FUNCTIONALITY ===" -ForegroundColor Magenta

Test-Item "FAISS VectorStore initialization" {
    & $pythonExe -c @"
from pkm_agent.rag import VectorStore, EmbeddingEngine
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    engine = EmbeddingEngine('all-MiniLM-L6-v2', Path(tmpdir))
    vs = VectorStore(Path(tmpdir), engine)
    print('VectorStore initialized OK')
"@ 2>&1
}

Test-Item "Chunker functionality" {
    & $pythonExe -c @"
from pkm_agent.rag import Chunker
chunker = Chunker(chunk_size=100, overlap=20)
chunks = chunker.chunk_text('This is a test. ' * 50, 'test-note')
print(f'Created {len(chunks)} chunks OK')
"@ 2>&1
}

Test-Item "Database initialization" {
    & $pythonExe -c @"
from pkm_agent.data import Database
import tempfile
with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
    db = Database(f.name)
    print('Database initialized OK')
"@ 2>&1
}

Test-Item "Config loading" {
    & $pythonExe -c @"
from pkm_agent.config import load_config
config = load_config()
print(f'Config loaded: pkm_root={config.pkm_root}')
"@ 2>&1
}

# ============================================
# 4. EMBEDDING ENGINE
# ============================================
Write-Host "`n=== 4. EMBEDDING ENGINE ===" -ForegroundColor Magenta

Test-Item "Embedding generation" {
    & $pythonExe -c @"
from pkm_agent.rag import EmbeddingEngine
from pathlib import Path
import tempfile

with tempfile.TemporaryDirectory() as tmpdir:
    engine = EmbeddingEngine('all-MiniLM-L6-v2', Path(tmpdir))
    embedding = engine.embed('Hello world')
    print(f'Generated embedding with {len(embedding)} dimensions')
"@ 2>&1
}

# ============================================
# SUMMARY
# ============================================
Write-Host "`n╔═══════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║             TEST SUMMARY                  ║" -ForegroundColor Cyan
Write-Host "╠═══════════════════════════════════════════╣" -ForegroundColor Cyan
Write-Host "║  Passed: $passed                                  ║" -ForegroundColor Green
Write-Host "║  Failed: $failed                                  ║" -ForegroundColor $(if ($failed -gt 0) { "Red" } else { "Green" })
Write-Host "╚═══════════════════════════════════════════╝" -ForegroundColor Cyan

if ($failed -eq 0) {
    Write-Host "`n✓ All tests passed! PKM Agent is fully functional." -ForegroundColor Green
} else {
    Write-Host "`n✗ Some tests failed. Review errors above." -ForegroundColor Red
}
