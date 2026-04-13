# Service Scope Model Benchmark 001

- generatedAt: `2026-04-11T14:56:21.096557+00:00`
- source: `data/service_scope_model_review_v2.json`
- goldsetStatus: `provisional_requires_human_confirmation`
- modelImprovementEligible: `False`

## Metrics

- evaluated: `25`
- exactDecisionAccuracy: `0.64`
- includeOrReviewRecall: `0.84`
- schemaValidRate: `1.0`
- reviewUsageRate: `0.2`
- falseExcludeCount: `4`
- highQualityFalseExcludeCount: `3`
- missingPredictionCount: `0`

## Criteria

- `falseExcludeCount` actual `4` target `0` passed `False`
- `highQualityFalseExcludeCount` actual `3` target `0` passed `False`
- `includeOrReviewRecall` actual `0.84` target `1.0` passed `False`
- `schemaValidRate` actual `1.0` target `1.0` passed `True`

## False Excludes

| # | company | title | quality | expected | actual | reason |
|---:|---|---|---|---|---|---|
| 1 | 슈어소프트테크 | [우주항공국방기술실(판교)] SW검증 (경력) | high | include | exclude | 일반 SW 검증 직무 |
| 2 | 아키드로우 | 클라우드 인프라 엔지니어(DevOps) | high | include | exclude | 일반 클라우드 인프라 운영 |
| 3 | 여기어때 | Server Engineer [숙박플랫폼개발] | high | include | exclude | 일반 백엔드 서버 개발 |
| 4 | 비상교육 | DevOps 엔지니어 | medium | include | exclude | 일반 인프라 및 보안 운영 |
