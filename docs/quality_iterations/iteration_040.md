# Quality Iteration 040

- 상태: `manual_intervention_required`
- 생성 시각: `2026-04-12T05:19:16.142495+00:00`
- optimization score: `96.1538`
- release champion: `gemma-4-31b / field_aware_v3`

## 핵심 지표

- boardLowRate: `0.044304`
- boardMissingSummaryRows: `0`
- boardExplicitLowRows: `7`
- sourceRetentionRate: `0.918605`
- filteredOutRate: `0.081395`
- excludedHighQualityRows: `1`
- excludedAiAdjacentRows: `0`
- highConfidenceExcludedRows: `1`
- guardRecoveredRows: `0`
- guardRecoveredHighQualityRows: `0`
- signalMetaLeakRows: `0`
- mixedClusterRoleLeakRows: `0`
- roleConflictRows: `0`
- roleLowConfidenceConflictRows: `0`
- roleMissingClassifierRows: `0`
- roleStaleClassifierRows: `0`
- releaseCoreFocusExact: `0.9286`
- releaseCoreKeywordF1: `0.8079`
- releaseIncrementalUsable: `0.9667`
- releaseIncrementalLowRate: `0.0333`
- releaseIncrementalBannedKeywordRate: `0.0`

## Target Checks

- `boardLowRate`: `actual=0.044304` / `target=0.05` / `max` / `pass=True`
- `boardMissingSummaryRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `signalMetaLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `mixedClusterRoleLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleConflictRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleMissingClassifierRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleStaleClassifierRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `releaseCoreFocusExact`: `actual=0.9286` / `target=0.85` / `min` / `pass=True`
- `releaseCoreKeywordF1`: `actual=0.8079` / `target=0.62` / `min` / `pass=True`
- `releaseIncrementalUsable`: `actual=0.9667` / `target=0.93` / `min` / `pass=True`
- `releaseIncrementalLowRate`: `actual=0.0333` / `target=0.08` / `max` / `pass=True`
- `releaseIncrementalBannedKeywordRate`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `sourceRetentionRate`: `actual=0.918605` / `target=0.8` / `min` / `pass=True`
- `filteredOutRate`: `actual=0.081395` / `target=0.2` / `max` / `pass=True`
- `excludedHighQualityRows`: `actual=1.0` / `target=10.0` / `max` / `pass=True`
- `excludedAiAdjacentRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `excludedLeakedIntoDisplayRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `deeptechInDataAnalystRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `businessInEngineerFamilyRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `toolFirstFocusRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `serviceScopeStaleRows`: `actual=38.0` / `target=0.0` / `max` / `pass=False`

## 샘플

- `boardLowRows`: `295f24c5156e197ea7a2f0370415d710c1f391e2f88fd95a1a95d7c9889d8a32, 5f920781cdc8e1391db5eb6437e77d463748efa13d30c40b25c6532821aa5c81, 800c930f817175a5b21d7cd8ebb472b13718b2be83a019d227977ce3c1dc6979, 52b449ba9e386190ca9134debbb8ed3fe5152b1d4dc8f1b6862e29f1b28339f5, d2d66165e6c3bd206f67aa16e0c14a32799abdbf7652a8cec243834f81681188, bc4ea07a6f45a0ccbc0f6d95c56568c3ea5f6208c3119e7a94173dd15791e0e3, b8b2fff13f42640489832974f5d0d914170617a3a5fd2534056e99aa47c979df`
- `boardMissingSummaryRows`: `없음`
- `boardExplicitLowRows`: `295f24c5156e197ea7a2f0370415d710c1f391e2f88fd95a1a95d7c9889d8a32, 5f920781cdc8e1391db5eb6437e77d463748efa13d30c40b25c6532821aa5c81, 800c930f817175a5b21d7cd8ebb472b13718b2be83a019d227977ce3c1dc6979, 52b449ba9e386190ca9134debbb8ed3fe5152b1d4dc8f1b6862e29f1b28339f5, d2d66165e6c3bd206f67aa16e0c14a32799abdbf7652a8cec243834f81681188, bc4ea07a6f45a0ccbc0f6d95c56568c3ea5f6208c3119e7a94173dd15791e0e3, b8b2fff13f42640489832974f5d0d914170617a3a5fd2534056e99aa47c979df`
- `signalMetaLeakRows`: `없음`
- `displayMetaLeakRows`: `없음`
- `mixedClusterRoleLeakRows`: `없음`
- `roleConflictRows`: `없음`
- `roleLowConfidenceConflictRows`: `없음`
- `roleMissingClassifierRows`: `없음`
- `roleStaleClassifierRows`: `없음`
- `deeptechInDataAnalystRows`: `없음`
- `businessInEngineerFamilyRows`: `없음`
- `toolFirstFocusRows`: `없음`
- `excludedHighQualityRows`: `53e58a53691a5cc2403347332cbfa09a3717a46b5f770c6a626ae0e6dfd545bc`
- `excludedAiAdjacentRows`: `없음`
- `highConfidenceExcludedRows`: `53e58a53691a5cc2403347332cbfa09a3717a46b5f770c6a626ae0e6dfd545bc`
- `guardRecoveredRows`: `없음`

## Next Actions

- `medium` `manual_review` `expand_review_goldset`: 검수 골드셋 확장 (평가셋 검수 커버리지가 낮아 모델 품질 판단의 신뢰도가 떨어집니다.)
