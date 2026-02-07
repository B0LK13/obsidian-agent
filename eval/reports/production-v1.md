# Production Benchmark v1 - LIVE Agent Execution

**Date**: 2026-02-07T16:50:32.288Z  
**Dataset**: 2 queries  
**Completed**: 2 (100.0%)  
**Failed**: 0  
**Strategy**: hybrid_learned  
**Git Commit**: 7c5a032f61e4a98d92b3a1415b15c15824d1bc78

---

## 🎯 Quality Gates: ❌ FAILED

| Gate | Value | Threshold | Status |
|------|-------|-----------|--------|
| **Citation Correctness** | 0.0% | ≥98% | ❌ |
| **Completeness** | 50.0% | ≥95% | ❌ |
| **ECE** | 0.090 | ≤0.15 | ✅ |
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
- **Completeness**: 50.0%

### Calibration
- **Confidence Calibration**: 91.0%
- **ECE**: 0.090

---

## ⚡ Execution Stats

- **Avg Tools per Query**: 0.0
- **Avg Execution Time**: 55151ms
- **Fallback Rate**: 0.0%

---

## ❌ Failure Analysis

No failures detected ✅

---

## 🔍 Top Failed Queries

No failures in top 10

---

## 📈 Comparison with Ablation-v1

| Metric | Production v1 | Ablation v1 | Δ |
|--------|---------------|-------------|---|
| Precision@5 | 0.0% | 76.0% | -76.0pp |
| Citation | 0.0% | 99.0% | -99.0pp |
| Complete | 50.0% | 96.0% | -46.0pp |

---

## ✅ Next Steps


### Immediate (Failed Gates)
1. Address top failure modes
2. Review queries with missing citations
3. Improve completeness detection
4. Recalibrate confidence thresholds


---

*Production benchmark v1 - live agent execution*
