# Service Scope Shadow Guard-Off 001

- generatedAt: `2026-04-11T14:56:22.050728+00:00`
- predictionSource: `model-review`
- targetsPassed: `False`

## Metrics

- sourceJobs: `213`
- shadowBoardRows: `187`
- shadowExcludedRows: `26`
- shadowSourceRetentionRate: `0.877934`
- shadowFilteredOutRate: `0.122066`
- shadowGuardRecoveredRows: `4`
- shadowGuardRecoveredHighQualityRows: `3`
- shadowExcludedAiAdjacentRows: `12`
- shadowExcludedHighQualityRows: `15`

## Target Status

- `shadowGuardRecoveredRows` actual `4` target `0` passed `False`
- `shadowGuardRecoveredHighQualityRows` actual `3` target `0` passed `False`
- `shadowExcludedAiAdjacentRows` actual `12` target `0` passed `False`
- `shadowExcludedHighQualityRows` actual `15` target `10` passed `False`
- `shadowSourceRetentionRate` actual `0.877934` target `0.8` passed `True`
- `shadowFilteredOutRate` actual `0.122066` target `0.2` passed `True`

## Rows Lost Without Guard

| # | company | title | quality | focus | model reason |
|---:|---|---|---|---|---|
| 1 | 비상교육 | DevOps 엔지니어 | medium | 클라우드 | 일반 인프라 운영 업무 |
| 2 | 슈어소프트테크 | [우주항공국방기술실(판교)] SW검증 (경력) | high | 소프트웨어 검증 | 일반 SW 신뢰성 검증 업무임 |
| 3 | 아키드로우 | 클라우드 인프라 엔지니어(DevOps) | high | 클라우드 | 일반 클라우드 인프라 운영 |
| 4 | 여기어때 | Server Engineer [숙박플랫폼개발] | high | 클라우드 | 일반 백엔드 서버 개발 업무 |
