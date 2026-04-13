# Quality Iteration 016

- 상태: `manual_intervention_required`
- 생성 시각: `2026-04-10T09:45:43.585197+00:00`
- optimization score: `75.4167`
- release champion: `gemma-4-31b / field_aware_v3`

## 핵심 지표

- boardLowRate: `1.0`
- boardMissingSummaryRows: `265`
- boardExplicitLowRows: `0`
- signalMetaLeakRows: `0`
- mixedClusterRoleLeakRows: `0`
- roleConflictRows: `0`
- roleLowConfidenceConflictRows: `0`
- roleMissingClassifierRows: `0`
- roleStaleClassifierRows: `265`
- releaseCoreFocusExact: `0.9286`
- releaseCoreKeywordF1: `0.8079`
- releaseIncrementalUsable: `0.9697`
- releaseIncrementalLowRate: `0.0303`
- releaseIncrementalBannedKeywordRate: `0.0`

## Target Checks

- `boardLowRate`: `actual=1.0` / `target=0.05` / `max` / `pass=False`
- `boardMissingSummaryRows`: `actual=265.0` / `target=0.0` / `max` / `pass=False`
- `signalMetaLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `mixedClusterRoleLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleConflictRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleMissingClassifierRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleStaleClassifierRows`: `actual=265.0` / `target=0.0` / `max` / `pass=False`
- `releaseCoreFocusExact`: `actual=0.9286` / `target=0.85` / `min` / `pass=True`
- `releaseCoreKeywordF1`: `actual=0.8079` / `target=0.62` / `min` / `pass=True`
- `releaseIncrementalUsable`: `actual=0.9697` / `target=0.93` / `min` / `pass=True`
- `releaseIncrementalLowRate`: `actual=0.0303` / `target=0.08` / `max` / `pass=True`
- `releaseIncrementalBannedKeywordRate`: `actual=0.0` / `target=0.0` / `max` / `pass=True`

## 샘플

- `boardLowRows`: `3bbd4030db95fc7517d3a364e840a168aab2329a250a93257f825e53fbb4581d, f35dcba448565a83607904f5ee253bae8e5ede3f1581f364a5da1bff9adfab86, 4986f3c9f3d430b6679afccbc9b1df91c86b8df0e0af26a2b26e02cb12c469a4, b76f5113e1aeac811a6cd5451b2063a77cdefb46b2884b817951a7c2abf6cf0b, b7cd343f31600421ea16fd66c441b20aafe3e71023438405a0df6f45ddd7fac3, bc37e2981eb8f66a4e50ce5ec37b8e3716c0b60770554f448d4213271dc92ad2, 9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, 6cc457dbc0ba62de75b2c9f89a7b2fc250ae3e2cacdf8cd653778b90deee5999, 8863b1b8daebdf7556e861b3c69656f100382adeeff2dd571a2b89b850cdd427, 4f1ad494f86464493921a068ec6dda48f02b8479274f05407c90030867708bc6`
- `boardMissingSummaryRows`: `3bbd4030db95fc7517d3a364e840a168aab2329a250a93257f825e53fbb4581d, f35dcba448565a83607904f5ee253bae8e5ede3f1581f364a5da1bff9adfab86, 4986f3c9f3d430b6679afccbc9b1df91c86b8df0e0af26a2b26e02cb12c469a4, b76f5113e1aeac811a6cd5451b2063a77cdefb46b2884b817951a7c2abf6cf0b, b7cd343f31600421ea16fd66c441b20aafe3e71023438405a0df6f45ddd7fac3, bc37e2981eb8f66a4e50ce5ec37b8e3716c0b60770554f448d4213271dc92ad2, 9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, 6cc457dbc0ba62de75b2c9f89a7b2fc250ae3e2cacdf8cd653778b90deee5999, 8863b1b8daebdf7556e861b3c69656f100382adeeff2dd571a2b89b850cdd427, 4f1ad494f86464493921a068ec6dda48f02b8479274f05407c90030867708bc6`
- `boardExplicitLowRows`: `없음`
- `signalMetaLeakRows`: `없음`
- `displayMetaLeakRows`: `없음`
- `mixedClusterRoleLeakRows`: `없음`
- `roleConflictRows`: `없음`
- `roleLowConfidenceConflictRows`: `없음`
- `roleMissingClassifierRows`: `없음`
- `roleStaleClassifierRows`: `3bbd4030db95fc7517d3a364e840a168aab2329a250a93257f825e53fbb4581d, f35dcba448565a83607904f5ee253bae8e5ede3f1581f364a5da1bff9adfab86, 4986f3c9f3d430b6679afccbc9b1df91c86b8df0e0af26a2b26e02cb12c469a4, b76f5113e1aeac811a6cd5451b2063a77cdefb46b2884b817951a7c2abf6cf0b, b7cd343f31600421ea16fd66c441b20aafe3e71023438405a0df6f45ddd7fac3, bc37e2981eb8f66a4e50ce5ec37b8e3716c0b60770554f448d4213271dc92ad2, 9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, 6cc457dbc0ba62de75b2c9f89a7b2fc250ae3e2cacdf8cd653778b90deee5999, 8863b1b8daebdf7556e861b3c69656f100382adeeff2dd571a2b89b850cdd427, 4f1ad494f86464493921a068ec6dda48f02b8479274f05407c90030867708bc6`

## Next Actions

- `critical` `manual_model` `backfill_missing_summaries`: missing summary backfill (현재 low 보드 행의 큰 비중이 모델 품질이 아니라 summary 미생성 상태입니다.)
- `critical` `manual_model` `rerun_stale_role_signatures`: stale role signature 재판정 (요약 재생성 뒤 role override signature 가 stale 해져 보드가 최신 분류를 읽지 못합니다.)
- `medium` `manual_review` `expand_review_goldset`: 검수 골드셋 확장 (평가셋 검수 커버리지가 낮아 모델 품질 판단의 신뢰도가 떨어집니다.)
