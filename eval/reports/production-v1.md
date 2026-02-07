# Production Benchmark v1 - LIVE Agent Execution

**Date**: 2026-02-07T16:40:34.253Z  
**Dataset**: 3 queries  
**Completed**: 3 (100.0%)  
**Failed**: 0  
**Strategy**: hybrid_learned  
**Git Commit**: 77297674529e8b733b42e69aa0fe665c41667c92

---

## 🎯 Quality Gates: ❌ FAILED

| Gate | Value | Threshold | Status |
|------|-------|-----------|--------|
| **Citation Correctness** | 0.0% | ≥98% | ❌ |
| **Completeness** | 0.0% | ≥95% | ❌ |
| **ECE** | 0.060 | ≤0.15 | ✅ |
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
- **Confidence Calibration**: 94.0%
- **ECE**: 0.060

---

## ⚡ Execution Stats

- **Avg Tools per Query**: 0.0
- **Avg Execution Time**: 53696ms
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
