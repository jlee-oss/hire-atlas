# Model Improvement Gate Latest

- generatedAt: `2026-04-12T05:19:16.199492+00:00`
- status: `blocked`
- passed: `False`

## Criteria

- `operationalLoopConverged` actual `manual_intervention_required` target `converged` passed `False`
- `goldsetConfirmed` actual `confirmed` target `confirmed` passed `True`
- `benchmarkFalseExcludeCount` actual `1` target `0` passed `False`
- `benchmarkHighQualityFalseExcludeCount` actual `1` target `0` passed `False`
- `benchmarkSchemaValidRate` actual `0.52` target `1.0` passed `False`
- `benchmarkIncludeOrReviewRecall` actual `0.9524` target `1.0` passed `False`
- `modelBenchmarkPassed` actual `False` target `True` passed `False`
- `modelImprovementEligible` actual `False` target `True` passed `False`
- `shadowGuardOffTargetsPassed` actual `False` target `True` passed `False`
- `guardRecoveredRows` actual `0` target `0` passed `True`
- `guardRecoveredHighQualityRows` actual `0` target `0` passed `True`

## Inputs

- latestState: `/Users/junheelee/Desktop/career_dashboard/data/quality_iterations/latest_state.json`
- goldset: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_goldset_001.json`
- benchmark: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_benchmark_incremental_latest.json`
- shadowGuardOff: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_shadow_guard_off_incremental_latest.json`

## Blockers

- operationalLoopConverged
- benchmarkFalseExcludeCount
- benchmarkHighQualityFalseExcludeCount
- benchmarkSchemaValidRate
- benchmarkIncludeOrReviewRecall
- modelBenchmarkPassed
- modelImprovementEligible
- shadowGuardOffTargetsPassed
