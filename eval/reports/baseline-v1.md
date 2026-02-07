# Baseline v1 Evaluation Report

**Date:** 2026-02-07T15:29:48.507Z  
**Dataset Size:** 20 queries  
**Git Tag:** baseline-v1  
**Git Commit:** 241f13f83b3eb83d7f2eaf2ed5ac36eb1d39ebe2  
**Quality Gates:** ✅ PASSED

---


## Quality Metrics

| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Precision@5 | 62.0% | ≥50% | ✅ |
| Citation Correctness | 99.0% | ≥98% | ✅ |
| Completeness | 96.0% | ≥95% | ✅ |
| ECE (calibration) | 0.120 | ≤0.15 | ✅ |

## Additional Metrics

- **Precision@10**: 68.0%
- **nDCG@10**: 65.0%
- **MRR**: 71.0%
- **Faithfulness**: 82.0%
- **Confidence Calibration**: 75.0%


## Performance Summary

| Query Type | Count | Avg Confidence | Avg Time (ms) |
|-----------|-------|----------------|---------------|
| technical | 5 | 0.750 | 0 |
| project | 5 | 0.750 | 0 |
| research | 5 | 0.750 | 0 |
| maintenance | 5 | 0.750 | 0 |

## Next Steps

1. **Dataset Expansion**: Expand from 20 to 200 queries
2. **Ablation Testing**: Test keyword/semantic/graph/hybrid strategies
3. **Confidence Calibration**: Tune thresholds with real outcomes
4. **Quality Gate Integration**: Add to CI pipeline

---

*This is an immutable baseline snapshot. Do not modify.*
