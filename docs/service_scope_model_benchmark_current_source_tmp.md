# Service Scope Model Benchmark 001

- generatedAt: `2026-04-12T05:20:30.657805+00:00`
- source: `data/service_scope_model_review_incremental_latest.json`
- goldsetStatus: `confirmed_current_source_subset_for_test`
- modelImprovementEligible: `False`

## Metrics

- evaluated: `13`
- exactDecisionAccuracy: `0.7692`
- includeOrReviewRecall: `0.9167`
- schemaValidRate: `1.0`
- reviewUsageRate: `0.2308`
- falseExcludeCount: `1`
- highQualityFalseExcludeCount: `1`
- missingPredictionCount: `0`

## Criteria

- `falseExcludeCount` actual `1` target `0` passed `False`
- `highQualityFalseExcludeCount` actual `1` target `0` passed `False`
- `includeOrReviewRecall` actual `0.9167` target `1.0` passed `False`
- `schemaValidRate` actual `1.0` target `1.0` passed `True`

## False Excludes

| # | company | title | quality | expected | actual | reason |
|---:|---|---|---|---|---|---|
| 1 | 스트라드비젼 | Software Testing Engineer | high | review | exclude | 일반 SW 테스트 및 QA 업무 |
