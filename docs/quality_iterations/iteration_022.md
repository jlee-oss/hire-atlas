# Quality Iteration 022

- 상태: `manual_intervention_required`
- 생성 시각: `2026-04-11T11:41:40.852041+00:00`
- optimization score: `83.7607`
- release champion: `gemma-4-31b / field_aware_v3`

## 핵심 지표

- boardLowRate: `0.017544`
- boardMissingSummaryRows: `0`
- boardExplicitLowRows: `3`
- sourceRetentionRate: `0.802817`
- filteredOutRate: `0.197183`
- excludedHighQualityRows: `27`
- excludedAiAdjacentRows: `21`
- highConfidenceExcludedRows: `41`
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

- `boardLowRate`: `actual=0.017544` / `target=0.05` / `max` / `pass=True`
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
- `sourceRetentionRate`: `actual=0.802817` / `target=0.8` / `min` / `pass=True`
- `filteredOutRate`: `actual=0.197183` / `target=0.2` / `max` / `pass=True`
- `excludedHighQualityRows`: `actual=27.0` / `target=10.0` / `max` / `pass=False`
- `excludedAiAdjacentRows`: `actual=21.0` / `target=0.0` / `max` / `pass=False`
- `excludedLeakedIntoDisplayRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `deeptechInDataAnalystRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `businessInEngineerFamilyRows`: `actual=2.0` / `target=0.0` / `max` / `pass=False`
- `toolFirstFocusRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `serviceScopeStaleRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`

## 샘플

- `boardLowRows`: `9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, 800d7f4b7af63cc4fcbd923b8d76aee2c4c2ebfdb3777297f9a976986c765009, b8b2fff13f42640489832974f5d0d914170617a3a5fd2534056e99aa47c979df`
- `boardMissingSummaryRows`: `없음`
- `boardExplicitLowRows`: `9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, 800d7f4b7af63cc4fcbd923b8d76aee2c4c2ebfdb3777297f9a976986c765009, b8b2fff13f42640489832974f5d0d914170617a3a5fd2534056e99aa47c979df`
- `signalMetaLeakRows`: `없음`
- `displayMetaLeakRows`: `없음`
- `mixedClusterRoleLeakRows`: `없음`
- `roleConflictRows`: `없음`
- `roleLowConfidenceConflictRows`: `없음`
- `roleMissingClassifierRows`: `없음`
- `roleStaleClassifierRows`: `없음`
- `deeptechInDataAnalystRows`: `없음`
- `businessInEngineerFamilyRows`: `하이퍼커넥트 | Senior Machine Learning Engineer (Match Group AI) | 인공지능 엔지니어 | 제품 성장 분석 | business focus dominates engineer/research/science, 당근 | Software Engineer, Machine Learning | 검색 (품질) | 인공지능 엔지니어 | 제품 성장 분석 | business focus dominates engineer/research/science`
- `toolFirstFocusRows`: `없음`
- `excludedHighQualityRows`: `49de8c0f74b6b6934fa130ad30ddaf91f974c4e4fa5bf61910834ace11039f01, b927c1f19c992ed2335dc4419f2aa5d412a08762e2d8a24669c296ccfb7fed20, 14ac45625bdb2881ff30ddd874871663eb1bea0e55b86eef907e11f42f0a6a65, 5d5e2ba2737958d1cb7ba49862740d9ea95a402732d1e80709c3dbb69355c0c8, 3a43422a9911cb573cda32706d79aeb4de650535628e74df14292ab683e69754, b3e29f75eb8ebfd79db6753b9ab936407ea18a4c0b1d2be32c257b758acd034b, 14f5df29aff3b2c02640a37aab45cf30f888b15f0a55ef35f8c9606b854b2fb8, 2233d3266907c2588e0b015d76182f5d801ff66a8199e14b716d7e5a42ea09d8, 755aa2b91bb02e73fbe5f050f505a4a3b2d385feda15dd0e05ac9fc8e515b99a, 8585662928f5ad392209af6fde575ef19ca74ea260c03c33203ef4bb7318ebe3`
- `excludedAiAdjacentRows`: `e8e8ab27dd23da088f9d9f77d16788cb21728e1865cb15209f69f6dc79714c0f, 49de8c0f74b6b6934fa130ad30ddaf91f974c4e4fa5bf61910834ace11039f01, b927c1f19c992ed2335dc4419f2aa5d412a08762e2d8a24669c296ccfb7fed20, 14ac45625bdb2881ff30ddd874871663eb1bea0e55b86eef907e11f42f0a6a65, 5d5e2ba2737958d1cb7ba49862740d9ea95a402732d1e80709c3dbb69355c0c8, 3a43422a9911cb573cda32706d79aeb4de650535628e74df14292ab683e69754, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f, 14f5df29aff3b2c02640a37aab45cf30f888b15f0a55ef35f8c9606b854b2fb8, 2233d3266907c2588e0b015d76182f5d801ff66a8199e14b716d7e5a42ea09d8, 8585662928f5ad392209af6fde575ef19ca74ea260c03c33203ef4bb7318ebe3`
- `highConfidenceExcludedRows`: `e8e8ab27dd23da088f9d9f77d16788cb21728e1865cb15209f69f6dc79714c0f, 49de8c0f74b6b6934fa130ad30ddaf91f974c4e4fa5bf61910834ace11039f01, b927c1f19c992ed2335dc4419f2aa5d412a08762e2d8a24669c296ccfb7fed20, 14ac45625bdb2881ff30ddd874871663eb1bea0e55b86eef907e11f42f0a6a65, 5d5e2ba2737958d1cb7ba49862740d9ea95a402732d1e80709c3dbb69355c0c8, 3a43422a9911cb573cda32706d79aeb4de650535628e74df14292ab683e69754, b3e29f75eb8ebfd79db6753b9ab936407ea18a4c0b1d2be32c257b758acd034b, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f, 14f5df29aff3b2c02640a37aab45cf30f888b15f0a55ef35f8c9606b854b2fb8, 2233d3266907c2588e0b015d76182f5d801ff66a8199e14b716d7e5a42ea09d8`

## Next Actions

- `critical` `manual_review` `audit_ai_adjacent_scope_exclusions`: AI/data 인접 제외 row 검수 (scope gate 가 AI/data 인접 신호를 가진 공고를 제외해 false negative 위험이 큽니다.)
- `high` `manual_model` `remediate_business_focus_dominance`: business focus dominance 보정 (엔지니어/리서처 공고의 focus 가 제품 성장 분석 같은 비즈니스 축으로 과잉 수렴합니다.)
- `medium` `manual_review` `expand_review_goldset`: 검수 골드셋 확장 (평가셋 검수 커버리지가 낮아 모델 품질 판단의 신뢰도가 떨어집니다.)
