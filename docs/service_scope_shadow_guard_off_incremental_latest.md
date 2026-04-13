# Service Scope Shadow Guard-Off 001

- generatedAt: `2026-04-12T05:13:59.983038+00:00`
- predictionSource: `model-review`
- goldsetStatus: `confirmed`
- targetsPassed: `False`

## Metrics

- sourceJobs: `172`
- shadowBoardRows: `154`
- shadowExcludedRows: `18`
- shadowReviewRows: `14`
- shadowHardExcludedRows: `4`
- shadowSourceRetentionRate: `0.895349`
- shadowFilteredOutRate: `0.104651`
- shadowGuardRecoveredRows: `2`
- shadowGuardRecoveredHighQualityRows: `1`
- shadowExcludedAiAdjacentRows: `2`
- shadowExcludedHighQualityRows: `1`

## Target Status

- `shadowGuardRecoveredRows` actual `2` target `0` passed `False`
- `shadowGuardRecoveredHighQualityRows` actual `1` target `0` passed `False`
- `shadowExcludedAiAdjacentRows` actual `2` target `0` passed `False`
- `shadowExcludedHighQualityRows` actual `1` target `10` passed `True`
- `shadowSourceRetentionRate` actual `0.895349` target `0.8` passed `True`
- `shadowFilteredOutRate` actual `0.104651` target `0.2` passed `True`

## Rows Lost Without Guard

| # | company | title | quality | focus | model reason |
|---:|---|---|---|---|---|
| 1 | 스트라드비젼 | Software Testing Engineer | high | 컴퓨터 비전 | codex_adjudicated; priority=human_boundary_review; model=review; suggestedReason |
| 2 | 티오리한국 | Security Software Engineer - αprism | low | - | - |
