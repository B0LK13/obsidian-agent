# Phase 3B: Production Truthing - Implementation Guide

**Status**: Foundation ready, requires live environment setup  
**Created**: 2026-02-07  
**Estimated Time**: 2-4 hours for full completion

---

## ✅ What's Complete

### 1. Production Benchmark Runner Created
- **File**: `eval/runProductionBenchmark.ts` (16.5KB)
- **Features**:
  - Loads 200-query dataset from datasetV2
  - Initializes AgentService with real dependencies
  - Executes queries through actual ReAct loop
  - Tracks per-query traces (tools used, execution time, evidence)
  - Calculates real metrics from live runs
  - Generates production-v1.json and production-v1.md
  - Quality gate checking against thresholds

### 2. Phase 3B Plan & Todos
- **Plan**: Updated in session plan.md
- **Todos**: 7 tasks created in SQL database
- **Quality Gates**: Defined (Citation≥98%, Completeness≥95%, ECE≤0.15, P@5≥73%)

---

## 🚧 What's Needed to Complete

### Immediate Blockers

#### 1. **Ollama Must Be Running**
```bash
# Start Ollama service
ollama serve

# Pull model (if not already available)
ollama pull llama2
```

#### 2. **Real Vault Required**
The mock vault in `runProductionBenchmark.ts` needs to be replaced with:
- Path to actual Obsidian vault (e.g., `C:\Users\Admin\Documents\B0LK13v2`)
- Real file reading via Obsidian API
- Actual metadata cache

**Quick fix for testing**:
```typescript
// Replace MockVault with real vault loader
const vaultPath = 'C:\\Users\\Admin\\Documents\\B0LK13v2';
// Use Obsidian's vault loading mechanism
```

#### 3. **API Key Configuration**
Ollama doesn't need API keys, but AIService is checking for them.

**Fix in `aiService.ts`**:
```typescript
// Skip API key check for Ollama provider
if (this.settings.aiProvider !== 'ollama' && !this.settings.apiKey) {
  throw new Error('ConfigurationError: API key not configured');
}
```

---

## 📋 Remaining Tasks

### Task 2: Promote hybrid_learned as Default ⏳
**File to edit**: `src/services/agent/tools.ts` (SearchVaultTool)

**Current**: Uses basic search  
**Target**: Use hybrid search with learned weights

**Implementation**:
```typescript
// In SearchVaultTool.execute()
const searchStrategy = 'hybrid_learned';  // Default
const weights = { keyword: 0.24, semantic: 0.50, graph: 0.26 };  // Optimized from ablation

// Fallback trigger
if (results.length === 0 || timeout) {
  fallbackStrategy = 'semantic_only';
  logFallbackReason('low_coverage');
}
```

**Deliverable**: Updated SearchVaultTool with hybrid_learned default

---

### Task 3: Implement Query-Type Router ⏳
**New file**: `src/intelligence/rag/queryRouter.ts`

**Purpose**: Route queries to optimal strategy per type

**Implementation**:
```typescript
export class QueryRouter {
  classify(query: string): QueryType {
    // Simple keyword-based classifier
    if (query.match(/\b(how|implement|code|debug|error)\b/i)) return 'technical';
    if (query.match(/\b(project|status|timeline|deadline)\b/i)) return 'project';
    if (query.match(/\b(learn|explain|understand|concept)\b/i)) return 'research';
    if (query.match(/\b(find|organize|cleanup|fix)\b/i)) return 'maintenance';
    return 'research';  // Default
  }
  
  getStrategyForType(type: QueryType): SearchStrategy {
    const strategyMap = {
      'technical': { keyword: 0.20, semantic: 0.60, graph: 0.20 },  // Semantic-heavy
      'project': { keyword: 0.30, semantic: 0.50, graph: 0.20, freshness: 0.15 },  // Add freshness
      'research': { keyword: 0.20, semantic: 0.45, graph: 0.35 },  // Graph-assisted
      'maintenance': { keyword: 0.40, semantic: 0.40, graph: 0.20 }  // Keyword-boosted
    };
    return strategyMap[type];
  }
}
```

**Deliverable**: QueryRouter class integrated into SearchVaultTool

---

### Task 4: Recalibrate Confidence (Real Data) ⏳
**File to edit**: `src/intelligence/reasoning/confidenceEstimator.ts`

**Current**: Uses heuristics  
**Target**: Use actual prediction vs outcome data

**Implementation**:
```typescript
// After running production benchmark
const predictions = traces.map(t => t.confidence);
const actual = traces.map(t => t.expected_confidence === 'high' ? 0.9 : 0.6);

// Calculate Brier score
const brierScore = predictions.map((pred, i) => 
  Math.pow(pred - actual[i], 2)
).reduce((a, b) => a + b) / predictions.length;

// Calculate ECE (Expected Calibration Error)
const bins = 10;
const ece = calculateECE(predictions, actual, bins);

// Tune thresholds per query type
const techThresholds = calibrateForType('technical', traces);
const projThresholds = calibrateForType('project', traces);
```

**Deliverable**: Calibrated confidence thresholds per query type

---

### Task 5: Add Weekly Drift Detection ⏳
**New file**: `eval/driftMonitor.ts`

**Purpose**: Detect performance degradation over time

**Implementation**:
```typescript
export async function detectDrift() {
  const baseline = loadResults('baseline-v1.json');
  const current = loadResults('production-latest.json');
  
  const drifts = {
    precision_drift: current.metrics.precision_at_5 - baseline.metrics.precision_at_5,
    citation_drift: current.metrics.citation_correctness - baseline.metrics.citation_correctness,
    // ... other metrics
  };
  
  // Check for sustained regression (2+ consecutive weeks)
  if (drifts.precision_drift < -0.03 && isPersistent('precision_drift')) {
    createGitHubIssue({
      title: '🚨 Precision@5 Regression Detected',
      body: `Precision has dropped by ${(drifts.precision_drift * 100).toFixed(1)}pp`,
      labels: ['regression', 'priority:high']
    });
  }
}
```

**Deliverable**: Drift detection script + GitHub Actions weekly cron job

---

### Task 6: Run Live 200-Query Production Benchmark ⏳
**Command**:
```bash
# Ensure Ollama is running
ollama serve &

# Run full production benchmark
cd F:\CascadeProjects\project_obsidian_agent
npx tsx eval/runProductionBenchmark.ts

# Check results
cat eval/reports/production-v1.md
```

**Expected Output**:
- `eval/results/production-v1.json` - Full trace data
- `eval/reports/production-v1.md` - Quality gate report
- Exit code 0 if all gates pass, 1 if any fail

**Quality Gates** (must all pass):
- ✅ Citation Correctness ≥ 98%
- ✅ Completeness ≥ 95%
- ✅ ECE ≤ 0.15
- ✅ Precision@5 ≥ 73% (within 3pp of ablation-v1)
- ✅ Fallback Rate < 10%

**Deliverable**: Frozen production-v1 artifacts with gate status

---

### Task 7: Analyze Failures + Create Fix Backlog ⏳
**Process**:
1. Load production-v1.json traces
2. Filter failed queries (error !== null)
3. Group by failure mode
4. Extract top 10 by impact
5. Tag root causes
6. Prioritize fixes

**Implementation**:
```typescript
const failedTraces = traces.filter(t => t.error);

// Group by failure mode
const failureModes = groupBy(failedTraces, t => t.error.split(':')[0]);

// Root cause tagging
const rootCauses = failedTraces.map(t => ({
  query_id: t.query_id,
  error: t.error,
  root_cause: classifyRootCause(t),  // 'missing_evidence', 'timeout', 'parse_error', etc.
  priority: calculatePriority(t)
}));

// Generate fix backlog
const backlog = rootCauses
  .sort((a, b) => b.priority - a.priority)
  .slice(0, 10);
```

**Deliverable**: `eval/reports/fix-backlog.md` with prioritized issues

---

## 🎯 Phase 3B Definition of Done

### All 7 Tasks Complete:
- [x] Wire eval to real agent execution
- [ ] Promote hybrid_learned as default
- [ ] Implement query-type router
- [ ] Recalibrate confidence from live data
- [ ] Add weekly drift detection
- [ ] Run live 200-query production benchmark
- [ ] Analyze failures + create fix backlog

### Quality Gates Passed on Live Run:
- [ ] Citation Correctness ≥ 98%
- [ ] Completeness ≥ 95%
- [ ] ECE ≤ 0.15
- [ ] Precision@5 ≥ 73%
- [ ] Fallback Rate < 10%

### Artifacts Produced:
- [ ] `eval/results/production-v1.json`
- [ ] `eval/reports/production-v1.md`
- [ ] `eval/reports/drift-weekly.md`
- [ ] `eval/reports/fix-backlog.md`
- [ ] Top 10 failed queries with root-cause tags

### Code Changes Committed:
- [ ] Updated SearchVaultTool with hybrid_learned
- [ ] Added QueryRouter class
- [ ] Recalibrated ConfidenceEstimator
- [ ] Created DriftMonitor
- [ ] Updated production benchmark runner

---

## 📅 Timeline Estimate

| Task | Est. Time | Dependencies |
|------|-----------|--------------|
| Fix Ollama/Vault setup | 30min | None |
| Promote hybrid_learned | 1hr | Ollama running |
| Implement query router | 1.5hr | hybrid_learned |
| Run production benchmark | 30min | All above |
| Recalibrate confidence | 1hr | Production run |
| Add drift detection | 1hr | Production run |
| Analyze failures | 30min | Production run |

**Total**: 6 hours (realistic with breaks)

---

## 🚀 Quick Start (Next Session)

```bash
# 1. Start Ollama
ollama serve

# 2. Verify model available
ollama list | grep llama2

# 3. Fix AIService API key check (if not done)
# Edit aiService.ts to skip Ollama key check

# 4. Run small test (3 queries)
npx tsx eval/runProductionBenchmark.ts 3

# 5. If passes, run full 200
npx tsx eval/runProductionBenchmark.ts

# 6. Review results
cat eval/reports/production-v1.md

# 7. If gates fail, analyze
npx tsx eval/analyzeFailures.ts

# 8. Implement fixes, re-run
```

---

## 📝 Notes

1. **Mock vs Real**: Current runner has mock vault - needs real Obsidian vault path
2. **Ollama Requirement**: Must be running on localhost:11434
3. **API Key Skip**: AIService needs Ollama exemption from API key check
4. **Execution Time**: ~200 queries × ~2-5s each = 10-15 minutes total
5. **Quality Gates**: Designed to catch regressions, may need threshold tuning

---

**Phase 3B Status**: 1/7 tasks complete (14%)  
**Next**: Fix Ollama setup, then run first live benchmark

