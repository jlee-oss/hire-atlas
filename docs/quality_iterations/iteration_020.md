# Quality Iteration 020

- 상태: `converged`
- 생성 시각: `2026-04-10T10:23:39.407140+00:00`
- optimization score: `100.0`
- release champion: `gemma-4-31b / field_aware_v3`

## 핵심 지표

- boardLowRate: `0.049057`
- boardMissingSummaryRows: `0`
- boardExplicitLowRows: `13`
- signalMetaLeakRows: `0`
- mixedClusterRoleLeakRows: `0`
- roleConflictRows: `0`
- roleLowConfidenceConflictRows: `3`
- roleMissingClassifierRows: `0`
- roleStaleClassifierRows: `0`
- releaseCoreFocusExact: `0.9286`
- releaseCoreKeywordF1: `0.8079`
- releaseIncrementalUsable: `0.9697`
- releaseIncrementalLowRate: `0.0303`
- releaseIncrementalBannedKeywordRate: `0.0`

## Target Checks

- `boardLowRate`: `actual=0.049057` / `target=0.05` / `max` / `pass=True`
- `boardMissingSummaryRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `signalMetaLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `mixedClusterRoleLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleConflictRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleMissingClassifierRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleStaleClassifierRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `releaseCoreFocusExact`: `actual=0.9286` / `target=0.85` / `min` / `pass=True`
- `releaseCoreKeywordF1`: `actual=0.8079` / `target=0.62` / `min` / `pass=True`
- `releaseIncrementalUsable`: `actual=0.9697` / `target=0.93` / `min` / `pass=True`
- `releaseIncrementalLowRate`: `actual=0.0303` / `target=0.08` / `max` / `pass=True`
- `releaseIncrementalBannedKeywordRate`: `actual=0.0` / `target=0.0` / `max` / `pass=True`

## 샘플

- `boardLowRows`: `9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, fa070d5aca80533fd9b38a4cb43c1af154b2e5d2e456f2b552775f24ca3a85f3, dcc6666c4ec968b53098490e72dfd5f1c44f71fe349e22165c0ba6bbbdcf73c4, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f, 1d96f77a4041bf5f7713462f400ada313717733c2e42cb42bdc3a5ec01ea0d09, b069c168e7db9f950e1be45aeec8fdf37bf63dc55e9242bcb4b2dabb776b8c72, ccb72064162209088093c8f39fdd5aae570517312bc1112b9444199b2a4e08ca, 84584e02a8f3fd15f2d9099ccb5bb1b8da5d1bec6df53d1ea35b3a89e1ef2d2b, 80dd8761e1cf512f819ae16fd447624ad5cd753f05f0be1fc736e73dfa96fb81, 2be64e75450abf6761094f0fb6011719890a6a9cd5f09d5c464c83d92880444d`
- `boardMissingSummaryRows`: `없음`
- `boardExplicitLowRows`: `9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, fa070d5aca80533fd9b38a4cb43c1af154b2e5d2e456f2b552775f24ca3a85f3, dcc6666c4ec968b53098490e72dfd5f1c44f71fe349e22165c0ba6bbbdcf73c4, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f, 1d96f77a4041bf5f7713462f400ada313717733c2e42cb42bdc3a5ec01ea0d09, b069c168e7db9f950e1be45aeec8fdf37bf63dc55e9242bcb4b2dabb776b8c72, ccb72064162209088093c8f39fdd5aae570517312bc1112b9444199b2a4e08ca, 84584e02a8f3fd15f2d9099ccb5bb1b8da5d1bec6df53d1ea35b3a89e1ef2d2b, 80dd8761e1cf512f819ae16fd447624ad5cd753f05f0be1fc736e73dfa96fb81, 2be64e75450abf6761094f0fb6011719890a6a9cd5f09d5c464c83d92880444d`
- `signalMetaLeakRows`: `없음`
- `displayMetaLeakRows`: `없음`
- `mixedClusterRoleLeakRows`: `없음`
- `roleConflictRows`: `없음`
- `roleLowConfidenceConflictRows`: `f3765941ec9a7d9959982b760a8d1aa1ae41c4f833def39918dadcf862d63179, 84584e02a8f3fd15f2d9099ccb5bb1b8da5d1bec6df53d1ea35b3a89e1ef2d2b, c096dbe43acbb917fe6739200ff4695818e345f6cdb2d06efa0fbdfd62a3c083`
- `roleMissingClassifierRows`: `없음`
- `roleStaleClassifierRows`: `없음`

## Next Actions

- `medium` `manual_review` `expand_review_goldset`: 검수 골드셋 확장 (평가셋 검수 커버리지가 낮아 모델 품질 판단의 신뢰도가 떨어집니다.)
