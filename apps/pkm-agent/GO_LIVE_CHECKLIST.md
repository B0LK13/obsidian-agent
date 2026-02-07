# Phase 3: Go-Live Checklist

**Version:** phase3-security-v1  
**Date:** 2026-02-07  
**Sprint:** Final Validation (2 hours)

---

## Pre-Flight Checks

### Environment
- [ ] Python 3.11+ installed
- [ ] Git configured and authenticated
- [ ] Write access to repository
- [ ] Clean working directory (`git status`)

### Dependencies
- [ ] `requirements.txt` exists (or install manually)
- [ ] `requirements-dev.txt` exists (or install manually)
- [ ] Test fixtures generated (`tests/fixtures/vaults/`)

---

## Automated Validation (Recommended)

### Single-Command Validation

```powershell
cd F:\CascadeProjects\project_obsidian_agent\apps\pkm-agent

# Create fresh environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Run automated validation
.\scripts\release_signoff.ps1
```

**Expected result:** `✅ ALL GATES PASSED`

**If failed:** Fix reported issues and re-run script

---

## Manual Validation (Fallback)

If automated script fails, run gates manually:

### Gate 1: Environment Setup (5 min)

```powershell
cd F:\CascadeProjects\project_obsidian_agent\apps\pkm-agent

# Create venv
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Upgrade pip
python -m pip install --upgrade pip setuptools wheel

# Install dependencies
pip install pytest pytest-asyncio pytest-cov psutil ruff mypy pip-audit
pip install aiosqlite pydantic rich typer sentence-transformers faiss-cpu
```

**Success criteria:** All packages installed without errors

---

### Gate 2: Code Quality (5 min)

```powershell
# Linting
ruff check src/ tests/ scripts/

# Formatting
ruff format --check src/ tests/ scripts/

# Type checking
mypy src/
```

**Success criteria:**
- [ ] ruff: 0 errors
- [ ] mypy: 0 type errors

---

### Gate 3: Security Tests (5 min)

```powershell
pytest tests/test_security.py -v
```

**Success criteria:**
- [ ] 21/21 tests passing
- [ ] No errors or failures

---

### Gate 4: E2E Tests (10 min)

```powershell
# Pipeline tests
pytest tests/e2e/test_pipeline_success.py -v

# Rollback tests
pytest tests/e2e/test_rollback_integrity.py -v

# Security regression
pytest tests/e2e/test_security_regression.py -v
```

**Success criteria:**
- [ ] All E2E tests passing (8+7+7 = 22 tests)
- [ ] No integration failures

---

### Gate 5: Full Test Suite (5 min)

```powershell
pytest -v
```

**Success criteria:**
- [ ] 43+ tests passing
- [ ] Coverage >80% (if measured)

---

### Gate 6: Security Scan (2 min)

```powershell
pip-audit
```

**Success criteria:**
- [ ] 0 critical vulnerabilities
- [ ] Any medium/low vulnerabilities documented

---

### Gate 7: Benchmarks (20 min)

```powershell
# Generate fixtures (if needed)
python tests/fixtures/generate_vaults.py

# Run benchmarks
python scripts/benchmark.py

# Verify outputs
Get-Content docs/benchmarks.md
Get-Content eval/results/benchmark_latest.json
```

**Success criteria:**
- [ ] `docs/benchmarks.md` exists
- [ ] `eval/results/benchmark_latest.json` exists
- [ ] Search p95 <200ms on all vault sizes
- [ ] Cache hit rate >70%

---

## Documentation Updates

### Update README.md

```powershell
# Copy sections from README_UPDATES.md to README.md
# Add:
# - Security section
# - Testing section
# - Performance/Benchmarks section
# - Quality Gates section
# - Audit & Rollback section
```

**Success criteria:**
- [ ] README includes security controls
- [ ] README includes benchmark results
- [ ] README includes test commands
- [ ] README includes CI/CD info

---

## Artifact Verification

### Required Files

Check these files exist and are properly generated:

```powershell
# Source code
Get-Item src/pkm_agent/security.py
Get-Item src/pkm_agent/app_enhanced.py

# Tests
Get-Item tests/test_security.py
Get-Item tests/e2e/test_security_regression.py
Get-Item tests/e2e/test_pipeline_success.py
Get-Item tests/e2e/test_rollback_integrity.py

# Scripts
Get-Item scripts/benchmark.py
Get-Item scripts/release_signoff.ps1

# Documentation
Get-Item PHASE3_SUMMARY.md
Get-Item PHASE3_CHECKPOINT.md
Get-Item FINAL_SIGNOFF_CHECKLIST.md
Get-Item RELEASE_SUMMARY.md
Get-Item README_UPDATES.md
Get-Item GO_LIVE_CHECKLIST.md

# CI/CD
Get-Item .github/workflows/quality-gates.yml

# Benchmark artifacts
Get-Item docs/benchmarks.md
Get-Item eval/results/benchmark_latest.json
```

**Success criteria:**
- [ ] All files exist
- [ ] No placeholder content
- [ ] All markdown renders correctly

---

## Release Preparation

### Stage Changes

```powershell
# Stage all changes
git add src/
git add tests/
git add scripts/
git add docs/
git add .github/workflows/
git add README.md
git add *.md

# Review staged changes
git status
git diff --cached
```

**Success criteria:**
- [ ] All new files staged
- [ ] Modified files staged
- [ ] No unintended changes

---

### Commit & Tag

```powershell
# Commit
git commit -m "Phase 3: Production hardening validated

Security controls:
✓ Prompt injection detection (13 patterns)
✓ Path traversal protection (allowlist)
✓ Secrets redaction (6 patterns)
✓ Input validation (length + encoding)

Quality gates:
✓ 43 tests passing (security, E2E, regression)
✓ Linting clean (ruff)
✓ Type checking clean (mypy)
✓ Dependency scan clean (pip-audit)

Performance:
✓ Search p95 <100ms (small vault)
✓ Search p95 <200ms (large vault)
✓ Cache hit rate >70%
✓ Benchmarks generated and documented

Deliverables:
- Security module (200 LOC)
- Integrated into app (5 checkpoints)
- 43 comprehensive tests
- Benchmark harness
- CI/CD pipeline
- Release automation script
- 62KB documentation

See PHASE3_CHECKPOINT.md for complete details."

# Tag release
git tag -a phase3-security-v1 -m "Phase 3: Production Hardening Complete

Security layers:
- Prompt injection detection
- Path traversal protection
- Secrets redaction
- Input validation

Quality assurance:
- 43 tests passing
- Automated validation script
- CI/CD quality gates
- Benchmark baseline established

Performance validated:
- p95 latency <200ms
- Cache hit rate >70%
- Full audit trail

Ready for production deployment."

# Verify tag
git tag -l phase3-security-v1
git show phase3-security-v1
```

**Success criteria:**
- [ ] Commit message is descriptive
- [ ] Tag includes version info
- [ ] Tag message includes key metrics

---

### Push to Remote

```powershell
# Push commits
git push origin main

# Push tags
git push origin --tags

# Verify on GitHub
# Check: Actions tab for CI run
# Check: Tags page for new tag
```

**Success criteria:**
- [ ] Commits pushed successfully
- [ ] Tags visible on GitHub
- [ ] CI pipeline triggered (if configured)

---

## Post-Release Validation

### Verify GitHub

- [ ] Tag `phase3-security-v1` visible in GitHub
- [ ] Release notes display correctly
- [ ] CI pipeline running (if configured)
- [ ] All workflows passing

### Create GitHub Release (Optional)

```markdown
## Phase 3: Production Hardening

**Release:** phase3-security-v1  
**Date:** 2026-02-07

### Security Enhancements

- ✅ Prompt injection detection (13 patterns)
- ✅ Path traversal protection (allowlist-based)
- ✅ Secrets redaction (automatic in logs)
- ✅ Input validation (length + encoding)

### Quality Improvements

- ✅ 43 comprehensive tests (security + E2E + regression)
- ✅ Automated release validation script
- ✅ CI/CD quality gates
- ✅ Benchmark baseline established

### Performance Metrics

- Search p95: <100ms (small), <200ms (large)
- Cache hit rate: >70% after warm-up
- Indexing: <120s for 1000 notes

### Documentation

- 62KB of technical documentation
- Security architecture guide
- Benchmark methodology
- Complete validation checklist

**Upgrade Notes:** This release includes breaking changes to the security model. All user inputs are now sanitized. Update integrations accordingly.

**See:** PHASE3_CHECKPOINT.md for full details.
```

---

## Rollback Plan

If issues discovered after release:

### Option 1: Revert Tag (Pre-Push)

```powershell
# Remove local tag
git tag -d phase3-security-v1

# Fix issues
# ... make corrections ...

# Re-tag
git tag -a phase3-security-v1 -m "..."
```

### Option 2: Revert Tag (Post-Push)

```powershell
# Remove remote tag
git push origin :refs/tags/phase3-security-v1

# Remove local tag
git tag -d phase3-security-v1

# Fix issues, then re-tag and push
```

### Option 3: Revert Commit

```powershell
# Revert last commit
git revert HEAD

# Or hard reset (if not pushed)
git reset --hard HEAD~1
```

---

## Success Criteria Summary

### Code Quality ✅
- [ ] Linting: 0 errors
- [ ] Type checking: 0 errors
- [ ] Test coverage: >80%

### Functional ✅
- [ ] 43+ tests passing
- [ ] Security controls active
- [ ] Benchmarks generated

### Performance ✅
- [ ] Search p95 <200ms
- [ ] Cache hit rate >70%
- [ ] Indexing <120s (1k notes)

### Documentation ✅
- [ ] README updated
- [ ] Benchmarks documented
- [ ] Security architecture documented

### Release ✅
- [ ] Committed to main
- [ ] Tagged phase3-security-v1
- [ ] Pushed to remote
- [ ] CI passing

---

## Next Steps

After successful release:

1. **Monitor first production run**
   - Check security control logs
   - Verify performance matches benchmarks
   - Watch for any errors

2. **Production-v1 evaluation**
   - 200-query real-vault test
   - Measure quality + security together
   - Establish baseline for future

3. **Address findings**
   - Tune security patterns if needed
   - Optimize hot paths if found
   - Document edge cases

---

## Support

If issues encountered:

1. Check `FINAL_SIGNOFF_CHECKLIST.md` for detailed troubleshooting
2. Review `PHASE3_CHECKPOINT.md` for architecture context
3. Run `.\scripts\release_signoff.ps1` for automated diagnostics

---

**Status:** Ready for Go-Live  
**ETA:** 2 hours (with working Python env)  
**Confidence:** High (93% complete, 7% validation)

---

*Last updated: 2026-02-07*  
*Phase: 3 (Production Hardening)*  
*Version: phase3-security-v1*
