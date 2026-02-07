# Production Benchmark v1 - LIVE Agent Execution

**Date**: 2026-02-07T16:11:27.357Z  
**Dataset**: 3 queries  
**Completed**: 0 (0.0%)  
**Failed**: 3  
**Strategy**: hybrid_learned  
**Git Commit**: eb1575ebb360f8a50b9e9b65d757e1d45e6ddd59

---

## 🎯 Quality Gates: ❌ FAILED

| Gate | Value | Threshold | Status |
|------|-------|-----------|--------|
| **Citation Correctness** | 0.0% | ≥98% | ❌ |
| **Completeness** | 0.0% | ≥95% | ❌ |
| **ECE** | 0.000 | ≤0.15 | ✅ |
| **Precision@5** | 0.0% | ≥73% (3pp tolerance) | ❌ |
| **Fallback Rate** | 0.0% | <10% | ✅ |

---

## 📊 Performance Metrics

### Retrieval Quality
- **Precision@5**: 0.0%
- **Precision@10**: 0.0%
- **nDCG@10**: 0.0%
- **MRR**: 0.0%

### Answer Quality
- **Faithfulness**: 0.0%
- **Citation Correctness**: 0.0%
- **Completeness**: 0.0%

### Calibration
- **Confidence Calibration**: 100.0%
- **ECE**: 0.000

---

## ⚡ Execution Stats

- **Avg Tools per Query**: 0.0
- **Avg Execution Time**: 0ms
- **Fallback Rate**: 0.0%

---

## ❌ Failure Analysis

| Failure Mode | Count |
|--------------|-------|
| ConfigurationError | 3 |

---

## 🔍 Top Failed Queries

1. **t001** (technical, medium)
   - Query: "How do I implement authentication in my React app?"
   - Error: ConfigurationError: API key not configured. Please set it in settings.

2. **t002** (technical, medium)
   - Query: "What are best practices for API error handling?"
   - Error: ConfigurationError: API key not configured. Please set it in settings.

3. **t003** (technical, hard)
   - Query: "Debug TypeError in validation function"
   - Error: ConfigurationError: API key not configured. Please set it in settings.

---

## 📈 Comparison with Ablation-v1

| Metric | Production v1 | Ablation v1 | Δ |
|--------|---------------|-------------|---|
| Precision@5 | 0.0% | 76.0% | -76.0pp |
| Citation | 0.0% | 99.0% | -99.0pp |
| Complete | 0.0% | 96.0% | -96.0pp |

---

## ✅ Next Steps


### Immediate (Failed Gates)
1. Address top failure modes
2. Review queries with missing citations
3. Improve completeness detection
4. Recalibrate confidence thresholds


---

*Production benchmark v1 - live agent execution*
