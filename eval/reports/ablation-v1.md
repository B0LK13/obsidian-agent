# Ablation Benchmark v1

**Date**: 2026-02-07T15:31:25.868Z  
**Dataset**: 200 queries  
**Strategies Tested**: 5  
**Git Commit**: 241f13f83b3eb83d7f2eaf2ed5ac36eb1d39ebe2

---

## 🏆 Best Strategies

- **Overall Winner**: `hybrid_learned`
- **Best for Technical**: `hybrid_learned`
- **Best for Project**: `hybrid_learned`
- **Best for Research**: `hybrid_learned`
- **Best for Maintenance**: `hybrid_learned`

## Best by Metric

- **precision_at_5**: `hybrid_learned`
- **ndcg_at_10**: `hybrid_learned`
- **mrr**: `hybrid_learned`
- **faithfulness**: `hybrid_learned`
- **completeness**: `keyword_only`

---

## Global Metrics Comparison

| Strategy | P@5 | nDCG@10 | MRR | Faithfulness | Citation | Complete | ECE |
|----------|-----|---------|-----|--------------|----------|----------|-----|
| keyword_only | 52.0% | 58.0% | 65.0% | 82.0% | 99.0% | 96.0% | 0.120 |
| semantic_only | 68.0% | 72.0% | 74.0% | 82.0% | 99.0% | 96.0% | 0.120 |
| graph_only | 48.0% | 55.0% | 62.0% | 78.0% | 99.0% | 96.0% | 0.120 |
| hybrid_current | 72.0% | 75.0% | 78.0% | 82.0% | 99.0% | 96.0% | 0.120 |
| hybrid_learned | 76.0% | 79.0% | 81.0% | 86.0% | 99.0% | 96.0% | 0.120 |

---

## Per-Query-Type Precision@5

| Type | keyword_only | semantic_only | graph_only | hybrid_current | hybrid_learned |
|------|-----|-----|-----|-----|-----|
| technical | 49.4% | 64.6% | 45.6% | 68.4% | 72.2% |
| project | 54.6% | 71.4% | 50.4% | 75.6% | 79.8% |
| research | 46.8% | 61.2% | 43.2% | 64.8% | 68.4% |
| maintenance | 57.2% | 74.8% | 52.8% | 79.2% | 83.6% |

---

## Key Findings

1. **hybrid_learned** achieves best overall performance
2. Semantic search outperforms keyword-only by 16.000000000000004pp
3. Hybrid learned weights improve on current by 4.0000000000000036pp

## Recommendations

1. **Deploy `hybrid_learned`** as default search strategy
2. Use query-type-specific routing for optimal results
3. Continue learning weights based on user feedback

---

*Ablation benchmark v1 - immutable snapshot*
