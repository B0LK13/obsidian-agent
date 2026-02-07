# 🎯 Testing & Verification Guide

## Quick Start

### Option 1: Automated Testing (Recommended)

**Windows:**
```batch
run_tests.bat
```

**Linux/Mac:**
```bash
chmod +x run_tests.sh
./run_tests.sh
```

This will:
1. Verify Python version
2. Install dependencies
3. Run comprehensive tests
4. Run interactive POC demo
5. Build TypeScript plugin

---

### Option 2: Manual Step-by-Step

#### Step 1: Verify Environment
```bash
python verify_setup.py
```

Expected output:
```
✅ Python 3.11.x
✅ watchdog - File system monitoring
✅ websockets - WebSocket sync server
✅ rapidfuzz - Fuzzy string matching
...
✅ ALL CHECKS PASSED - Ready to test!
```

#### Step 2: Install Dependencies
```bash
cd pkm-agent
pip install -e ".[dev]"
```

#### Step 3: Run Comprehensive Tests
```bash
python test_comprehensive.py
```

This runs 8 test suites:
- ✅ Module imports
- ✅ Exception hierarchy
- ✅ Link analyzer
- ✅ Link validator (fuzzy matching)
- ✅ Link healer (dry run and real)
- ✅ File watcher
- ✅ WebSocket sync server
- ✅ Full app integration

**Expected output:**
```
=================================================================
  TEST SUMMARY
=================================================================
Total Tests: 8
✅ Passed: 8
🎉 ALL TESTS PASSED! 🎉
```

Results are saved to `test_results.json`.

#### Step 4: Run POC Demo (Interactive)
```bash
python demo_poc.py
```

This interactive demo will:
1. Create a temporary vault with sample notes
2. Demonstrate link analysis (find broken links, hubs, orphans)
3. Show fuzzy matching suggestions
4. Auto-heal broken links (dry run then real)
5. Demonstrate real-time file watching
6. Test WebSocket sync server
7. Show full app integration

Follow the on-screen prompts and press ENTER to advance through steps.

#### Step 5: Build TypeScript Plugin
```bash
cd obsidian-pkm-agent
npm install  # if not already done
npm run build
```

Expected output:
```
> obsidian-pkm-agent@1.0.0 build
> esbuild main.tsx --bundle --outfile=main.js ...

  main.js  XXX kb
✨ Done
```

---

## Test Details

### Test 1: Module Imports
Verifies all new modules can be imported:
- `pkm_agent.exceptions`
- `pkm_agent.data.file_watcher`
- `pkm_agent.websocket_sync`
- `pkm_agent.data.link_analyzer`
- `pkm_agent.data.link_healer`

### Test 2: Exception Hierarchy
Tests:
- Exception creation with context
- Retriable vs Permanent classification
- Serialization (`to_dict()`)

### Test 3: Link Analyzer
Tests with temporary vault:
- Extract wikilinks, embeds, markdown links, tags
- Validate link targets
- Build link graph
- Find broken links
- Identify orphans and hubs

### Test 4: Link Validator
Tests fuzzy matching:
- Create broken links with typos
- Generate fix suggestions
- Verify confidence scoring
- Test prefix/suffix/word overlap boosting

### Test 5: Link Healer
Tests auto-healing:
- Dry run mode (no file changes)
- Real mode (fixes applied)
- Preserves file formatting
- Handles multiple link types

### Test 6: File Watcher
Tests real-time monitoring:
- Start watcher
- Create file → event captured
- Modify file → event captured
- Proper cleanup

### Test 7: WebSocket Sync Server
Tests bidirectional sync:
- Server startup
- Client connection
- Ping/pong heartbeat
- Event broadcasting
- Multiple events
- Clean shutdown

### Test 8: Full App Integration
Tests PKMAgentApp with all features:
- Sync server initialization
- File watcher enabled
- All components integrated
- Clean startup and shutdown

---

## POC Demo Flow

### Demo 1: Link Analysis
Creates sample vault with:
- 5 notes with intentional typos
- Cross-references between notes
- Orphan notes
- Hub notes

**Output:**
- Total links count
- Broken links detected
- Orphan notes identified
- Top hub notes shown

### Demo 2: Link Validation
Runs fuzzy matching on broken links.

**Output:**
- Fix suggestions with confidence scores
- Reasoning for each suggestion
- Fixable vs unfixable counts

### Demo 3: Link Healing
First runs dry-run, then applies fixes for real.

**Output:**
- Simulation results
- Actual fixes applied
- Modified files shown
- Before/after content preview

### Demo 4: File Watcher
Creates and modifies files while watcher is active.

**Output:**
- Real-time event notifications
- Event types captured
- File names tracked

### Demo 5: WebSocket Sync
Starts server and connects client.

**Output:**
- Connection established
- Ping/pong exchange
- Event broadcasting
- Multiple clients support demo

### Demo 6: Full Integration
Initializes PKMAgentApp with all features.

**Output:**
- Component status
- Active services listed
- Capabilities summary
- Clean shutdown

---

## Verification Checklist

After running tests and demo, verify:

### Python Backend
- [ ] All 8 tests pass
- [ ] No import errors
- [ ] File watcher captures events
- [ ] WebSocket server accepts connections
- [ ] Link analysis finds broken links
- [ ] Link healing fixes typos
- [ ] App initializes without errors

### TypeScript Plugin
- [ ] `npm run build` succeeds
- [ ] `main.js` file created
- [ ] File size reasonable (~500KB-2MB)
- [ ] No TypeScript compilation errors

### Integration
- [ ] Sync server starts on port 27125
- [ ] File watcher monitors vault
- [ ] Link management CLI works
- [ ] Error handling in place

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'X'"
```bash
cd pkm-agent
pip install -e ".[dev]"
```

### "Address already in use" (WebSocket tests)
Another process is using the port. Tests use port 27126/27127 (not 27125) to avoid conflicts.

If still failing:
```bash
# Windows
netstat -ano | findstr :27126
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:27126 | xargs kill -9
```

### Tests timeout
Increase timeout values in test code or check firewall settings.

### TypeScript build errors
```bash
cd obsidian-pkm-agent
rm -rf node_modules package-lock.json
npm install
npm run build
```

### Python version too old
Need Python 3.11+:
```bash
python --version  # Check current version
# Install Python 3.11+ from python.org
```

---

## Performance Benchmarks

Run these after tests pass:

### Indexing Speed
```bash
cd pkm-agent
python -c "
import asyncio
import time
from pathlib import Path
from pkm_agent.config import Config
from pkm_agent.app import PKMAgentApp

async def bench():
    config = Config()
    app = PKMAgentApp(config)
    
    start = time.time()
    await app.initialize()
    elapsed = time.time() - start
    
    print(f'Initialization: {elapsed:.2f}s')
    await app.close()

asyncio.run(bench())
"
```

Expected: <10s for typical vault

### Link Analysis Speed
```bash
python -c "
import time
from pathlib import Path
from pkm_agent.data.link_analyzer import LinkAnalyzer

vault = Path.home() / 'your-vault'  # Change to your vault
start = time.time()
analyzer = LinkAnalyzer(vault)
result = analyzer.analyze_vault()
elapsed = time.time() - start

print(f'Analyzed {result.total_links} links in {elapsed:.2f}s')
"
```

Expected: <15s for 5k notes

---

## Next Steps After Verification

Once all tests pass:

1. **Review Results**
   - Check `test_results.json`
   - Verify all features work
   - Note any warnings

2. **Deploy to Production**
   - Follow `DEPLOYMENT_CHECKLIST.md`
   - Copy plugin to Obsidian vault
   - Start backend with real vault

3. **Create GitHub Issues**
   - Post issues from `GITHUB_ISSUES.md`
   - Tag with appropriate labels
   - Link to this verification report

4. **Document Findings**
   - Note any edge cases discovered
   - Record performance metrics
   - Update documentation if needed

5. **Plan Phase 2 Completion**
   - Implement Issue #5 (Semantic Chunking)
   - Implement Issue #6 (Rate Limiting)
   - Continue with Phase 3

---

## Files Generated

After running tests and demo:

- `test_results.json` - Detailed test results
- `obsidian-pkm-agent/main.js` - Built plugin
- Temporary vault (cleaned up after demo)

---

## Support

If tests fail:
1. Check error messages in output
2. Review `test_results.json`
3. Ensure all dependencies installed
4. Check Python version (need 3.11+)
5. Verify all files exist (run `verify_setup.py`)

For further assistance:
- See `TROUBLESHOOTING.md` (if exists)
- Review `DEPLOYMENT_CHECKLIST.md`
- Check `PHASE_2_PROGRESS.md` for known issues

---

**Last Updated:** 2026-01-17
**Test Suite Version:** 1.0
**Coverage:** Phase 1 (Issues #1, #2, #4) + Phase 2 (Issue #3)
