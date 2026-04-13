# Quality Iteration 009

- 상태: `manual_intervention_required`
- 생성 시각: `2026-04-10T08:20:25.954218+00:00`
- optimization score: `82.5027`
- release champion: `gemma-4-31b / field_aware_v3`

## 핵심 지표

- boardLowRate: `0.045283`
- boardMissingSummaryRows: `0`
- boardExplicitLowRows: `12`
- signalMetaLeakRows: `0`
- mixedClusterRoleLeakRows: `0`
- roleConflictRows: `9`
- roleMissingClassifierRows: `0`
- roleStaleClassifierRows: `0`
- releaseCoreFocusExact: `0.4286`
- releaseCoreKeywordF1: `0.5753`
- releaseIncrementalUsable: `0.9487`
- releaseIncrementalLowRate: `0.0513`
- releaseIncrementalBannedKeywordRate: `0.0`

## Target Checks

- `boardLowRate`: `actual=0.045283` / `target=0.05` / `max` / `pass=True`
- `boardMissingSummaryRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `signalMetaLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `mixedClusterRoleLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleConflictRows`: `actual=9.0` / `target=0.0` / `max` / `pass=False`
- `roleMissingClassifierRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleStaleClassifierRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `releaseCoreFocusExact`: `actual=0.4286` / `target=0.85` / `min` / `pass=False`
- `releaseCoreKeywordF1`: `actual=0.5753` / `target=0.62` / `min` / `pass=False`
- `releaseIncrementalUsable`: `actual=0.9487` / `target=0.93` / `min` / `pass=True`
- `releaseIncrementalLowRate`: `actual=0.0513` / `target=0.08` / `max` / `pass=True`
- `releaseIncrementalBannedKeywordRate`: `actual=0.0` / `target=0.0` / `max` / `pass=True`

## 샘플

- `boardLowRows`: `ccb72064162209088093c8f39fdd5aae570517312bc1112b9444199b2a4e08ca, 80dd8761e1cf512f819ae16fd447624ad5cd753f05f0be1fc736e73dfa96fb81, 2be64e75450abf6761094f0fb6011719890a6a9cd5f09d5c464c83d92880444d, 9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, eb9b2ce000b4dc274a0832a14b682e2bc81b7c2584df27ecd2a8286adfb51ebc, 800d7f4b7af63cc4fcbd923b8d76aee2c4c2ebfdb3777297f9a976986c765009, 708c8e44b6884abbc28080b22ccfd962197e37ee49dbe1dc9128dd12e1ed2c80, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f, 1d96f77a4041bf5f7713462f400ada313717733c2e42cb42bdc3a5ec01ea0d09, dcc6666c4ec968b53098490e72dfd5f1c44f71fe349e22165c0ba6bbbdcf73c4`
- `boardMissingSummaryRows`: `없음`
- `boardExplicitLowRows`: `ccb72064162209088093c8f39fdd5aae570517312bc1112b9444199b2a4e08ca, 80dd8761e1cf512f819ae16fd447624ad5cd753f05f0be1fc736e73dfa96fb81, 2be64e75450abf6761094f0fb6011719890a6a9cd5f09d5c464c83d92880444d, 9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, eb9b2ce000b4dc274a0832a14b682e2bc81b7c2584df27ecd2a8286adfb51ebc, 800d7f4b7af63cc4fcbd923b8d76aee2c4c2ebfdb3777297f9a976986c765009, 708c8e44b6884abbc28080b22ccfd962197e37ee49dbe1dc9128dd12e1ed2c80, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f, 1d96f77a4041bf5f7713462f400ada313717733c2e42cb42bdc3a5ec01ea0d09, dcc6666c4ec968b53098490e72dfd5f1c44f71fe349e22165c0ba6bbbdcf73c4`
- `signalMetaLeakRows`: `없음`
- `displayMetaLeakRows`: `없음`
- `mixedClusterRoleLeakRows`: `없음`
- `roleConflictRows`: `84584e02a8f3fd15f2d9099ccb5bb1b8da5d1bec6df53d1ea35b3a89e1ef2d2b, 8276f363942d373702856aaa8469f0132dcd2c0d7dcf665d1327d0d98985e961, f4ec071c9093d3638dc48f49562ed8e829540ec1df81cb8eb62ea4966b1ff599, 2284e6c9342420836a55e2f5c2af756d82ce6c79b26574286e7d7abdb929c39e, dcc6666c4ec968b53098490e72dfd5f1c44f71fe349e22165c0ba6bbbdcf73c4, 8b05a92fbca6b18dd22424854b77f8d34945cd9604facd03f01fc1ead8b0c0c7, 0100638195e8e55f8d12e3c6cdd261cd1f5a0ae1fb6ae3f03ab49ee847565163, 5fae0c92918a46d590304166e58f58c66a72156ec144f64c9f625d048f408990, c096dbe43acbb917fe6739200ff4695818e345f6cdb2d06efa0fbdfd62a3c083`
- `roleMissingClassifierRows`: `없음`
- `roleStaleClassifierRows`: `없음`

## Next Actions

- `high` `manual_benchmark` `run_candidate_release_gate`: candidate prompt release gate 재실행 (release gate 관련 지표 releaseCoreFocusExact, releaseCoreKeywordF1 가 목표 미달입니다.)
- `high` `manual_model` `rerun_role_group_wave`: role remediation wave 재판정 (전용 role 분류기 충돌 또는 비어 있는 출력이 남아 있습니다.)
- `medium` `manual_review` `expand_review_goldset`: 검수 골드셋 확장 (평가셋 검수 커버리지가 낮아 모델 품질 판단의 신뢰도가 떨어집니다.)
