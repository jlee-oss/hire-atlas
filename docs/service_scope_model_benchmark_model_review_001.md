# Service Scope Model Benchmark 001

- generatedAt: `2026-04-11T13:53:35.394887+00:00`
- source: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_review.json`
- goldsetStatus: `provisional_requires_human_confirmation`
- modelImprovementEligible: `False`

## Metrics

- evaluated: `25`
- exactDecisionAccuracy: `0.0`
- includeOrReviewRecall: `0.96`
- schemaValidRate: `0.04`
- reviewUsageRate: `0.0`
- falseExcludeCount: `1`
- highQualityFalseExcludeCount: `1`
- missingPredictionCount: `24`

## Criteria

- `falseExcludeCount` actual `1` target `0` passed `False`
- `highQualityFalseExcludeCount` actual `1` target `0` passed `False`
- `includeOrReviewRecall` actual `0.96` target `1.0` passed `False`
- `schemaValidRate` actual `0.04` target `1.0` passed `False`

## False Excludes

| # | company | title | quality | expected | actual | reason |
|---:|---|---|---|---|---|---|
| 1 | 인터엑스 | [대구] C#, .NET 개발자 (C#/.NET, 실시간 데이터) | high | include | exclude | 일반 C#/.NET SW 개발 |
