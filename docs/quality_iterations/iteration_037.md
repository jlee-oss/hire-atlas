# Quality Iteration 037

- 상태: `converged`
- 생성 시각: `2026-04-11T15:06:58.725991+00:00`
- optimization score: `100.0`
- release champion: `gemma-4-31b / field_aware_v3`

## 핵심 지표

- boardLowRate: `0.02139`
- boardMissingSummaryRows: `0`
- boardExplicitLowRows: `4`
- sourceRetentionRate: `0.877934`
- filteredOutRate: `0.122066`
- excludedHighQualityRows: `9`
- excludedAiAdjacentRows: `0`
- highConfidenceExcludedRows: `16`
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

- `boardLowRate`: `actual=0.02139` / `target=0.05` / `max` / `pass=True`
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
- `sourceRetentionRate`: `actual=0.877934` / `target=0.8` / `min` / `pass=True`
- `filteredOutRate`: `actual=0.122066` / `target=0.2` / `max` / `pass=True`
- `excludedHighQualityRows`: `actual=9.0` / `target=10.0` / `max` / `pass=True`
- `excludedAiAdjacentRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `excludedLeakedIntoDisplayRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `deeptechInDataAnalystRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `businessInEngineerFamilyRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `toolFirstFocusRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `serviceScopeStaleRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`

## 샘플

- `boardLowRows`: `9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, 800d7f4b7af63cc4fcbd923b8d76aee2c4c2ebfdb3777297f9a976986c765009, aaaef3795309f37ad82e68447adb62c019e14d9e929b0d9aa34c81c4e4734492, b8b2fff13f42640489832974f5d0d914170617a3a5fd2534056e99aa47c979df`
- `boardMissingSummaryRows`: `없음`
- `boardExplicitLowRows`: `9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, 800d7f4b7af63cc4fcbd923b8d76aee2c4c2ebfdb3777297f9a976986c765009, aaaef3795309f37ad82e68447adb62c019e14d9e929b0d9aa34c81c4e4734492, b8b2fff13f42640489832974f5d0d914170617a3a5fd2534056e99aa47c979df`
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
- `excludedHighQualityRows`: `49de8c0f74b6b6934fa130ad30ddaf91f974c4e4fa5bf61910834ace11039f01, b927c1f19c992ed2335dc4419f2aa5d412a08762e2d8a24669c296ccfb7fed20, 09a310ea09d21ee506d33a665992060afff42e933ad1c874cf1e7b078ecac6f3, c096dbe43acbb917fe6739200ff4695818e345f6cdb2d06efa0fbdfd62a3c083, 57dc52ab25c838a98061efd981f4a4ccc62a821b9e3e6b2c94b64d9efff0c6b0, fbf2a46fb385daffaf7e34a05fb2d389c8d59667286179cbf271746a519ba8fb, 038a7d2110999be04050ae638ee3fef822139e55940da2ee7f9695d6c2823816, 4e0e9d02d52daf4cd024d90ee8078e2faf12b1f08c0c933fb3d20f35781ca2be, 53e58a53691a5cc2403347332cbfa09a3717a46b5f770c6a626ae0e6dfd545bc`
- `excludedAiAdjacentRows`: `없음`
- `highConfidenceExcludedRows`: `49de8c0f74b6b6934fa130ad30ddaf91f974c4e4fa5bf61910834ace11039f01, b927c1f19c992ed2335dc4419f2aa5d412a08762e2d8a24669c296ccfb7fed20, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f, 1d96f77a4041bf5f7713462f400ada313717733c2e42cb42bdc3a5ec01ea0d09, 09a310ea09d21ee506d33a665992060afff42e933ad1c874cf1e7b078ecac6f3, eb9b2ce000b4dc274a0832a14b682e2bc81b7c2584df27ecd2a8286adfb51ebc, c096dbe43acbb917fe6739200ff4695818e345f6cdb2d06efa0fbdfd62a3c083, fa070d5aca80533fd9b38a4cb43c1af154b2e5d2e456f2b552775f24ca3a85f3, 57dc52ab25c838a98061efd981f4a4ccc62a821b9e3e6b2c94b64d9efff0c6b0, fbf2a46fb385daffaf7e34a05fb2d389c8d59667286179cbf271746a519ba8fb`
- `guardRecoveredRows`: `없음`

## Next Actions

- `medium` `manual_review` `expand_review_goldset`: 검수 골드셋 확장 (평가셋 검수 커버리지가 낮아 모델 품질 판단의 신뢰도가 떨어집니다.)
