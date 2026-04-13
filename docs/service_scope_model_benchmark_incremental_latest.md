# Service Scope Model Benchmark 001

- generatedAt: `2026-04-12T05:13:58.930461+00:00`
- source: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_review_incremental_latest.json`
- goldsetStatus: `confirmed`
- modelImprovementEligible: `False`

## Metrics

- evaluated: `25`
- exactDecisionAccuracy: `0.4`
- includeOrReviewRecall: `0.9524`
- schemaValidRate: `0.52`
- reviewUsageRate: `0.2308`
- falseExcludeCount: `1`
- highQualityFalseExcludeCount: `1`
- missingPredictionCount: `12`

## Criteria

- `falseExcludeCount` actual `1` target `0` passed `False`
- `highQualityFalseExcludeCount` actual `1` target `0` passed `False`
- `includeOrReviewRecall` actual `0.9524` target `1.0` passed `False`
- `schemaValidRate` actual `0.52` target `1.0` passed `False`

## False Excludes

| # | company | title | quality | expected | actual | reason |
|---:|---|---|---|---|---|---|
| 1 | 스트라드비젼 | Software Testing Engineer | high | review | exclude | 일반 SW 테스트 및 QA 업무 |
