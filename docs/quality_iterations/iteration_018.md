# Quality Iteration 018

- 상태: `manual_intervention_required`
- 생성 시각: `2026-04-10T09:54:46.260517+00:00`
- optimization score: `76.9717`
- release champion: `gemma-4-31b / field_aware_v3`

## 핵심 지표

- boardLowRate: `0.211321`
- boardMissingSummaryRows: `44`
- boardExplicitLowRows: `12`
- signalMetaLeakRows: `0`
- mixedClusterRoleLeakRows: `0`
- roleConflictRows: `0`
- roleLowConfidenceConflictRows: `0`
- roleMissingClassifierRows: `0`
- roleStaleClassifierRows: `256`
- releaseCoreFocusExact: `0.9286`
- releaseCoreKeywordF1: `0.8079`
- releaseIncrementalUsable: `0.9697`
- releaseIncrementalLowRate: `0.0303`
- releaseIncrementalBannedKeywordRate: `0.0`

## Target Checks

- `boardLowRate`: `actual=0.211321` / `target=0.05` / `max` / `pass=False`
- `boardMissingSummaryRows`: `actual=44.0` / `target=0.0` / `max` / `pass=False`
- `signalMetaLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `mixedClusterRoleLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleConflictRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleMissingClassifierRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleStaleClassifierRows`: `actual=256.0` / `target=0.0` / `max` / `pass=False`
- `releaseCoreFocusExact`: `actual=0.9286` / `target=0.85` / `min` / `pass=True`
- `releaseCoreKeywordF1`: `actual=0.8079` / `target=0.62` / `min` / `pass=True`
- `releaseIncrementalUsable`: `actual=0.9697` / `target=0.93` / `min` / `pass=True`
- `releaseIncrementalLowRate`: `actual=0.0303` / `target=0.08` / `max` / `pass=True`
- `releaseIncrementalBannedKeywordRate`: `actual=0.0` / `target=0.0` / `max` / `pass=True`

## 샘플

- `boardLowRows`: `db2d1564b340b5b31a0113c4df702f709861e1a8e4b58745b1a11fb031bf8651, b069c168e7db9f950e1be45aeec8fdf37bf63dc55e9242bcb4b2dabb776b8c72, ccb72064162209088093c8f39fdd5aae570517312bc1112b9444199b2a4e08ca, 84584e02a8f3fd15f2d9099ccb5bb1b8da5d1bec6df53d1ea35b3a89e1ef2d2b, 80dd8761e1cf512f819ae16fd447624ad5cd753f05f0be1fc736e73dfa96fb81, 3a1af736e9641b8bf16d7565680bcfa5d13c3e65fa63e1cefbf425314fc351e5, 2be64e75450abf6761094f0fb6011719890a6a9cd5f09d5c464c83d92880444d, b7cd343f31600421ea16fd66c441b20aafe3e71023438405a0df6f45ddd7fac3, 9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, fa070d5aca80533fd9b38a4cb43c1af154b2e5d2e456f2b552775f24ca3a85f3`
- `boardMissingSummaryRows`: `b069c168e7db9f950e1be45aeec8fdf37bf63dc55e9242bcb4b2dabb776b8c72, ccb72064162209088093c8f39fdd5aae570517312bc1112b9444199b2a4e08ca, 84584e02a8f3fd15f2d9099ccb5bb1b8da5d1bec6df53d1ea35b3a89e1ef2d2b, 80dd8761e1cf512f819ae16fd447624ad5cd753f05f0be1fc736e73dfa96fb81, 3a1af736e9641b8bf16d7565680bcfa5d13c3e65fa63e1cefbf425314fc351e5, b7cd343f31600421ea16fd66c441b20aafe3e71023438405a0df6f45ddd7fac3, 6b05164bb2c48c397a3ed7be1f0e01ae1359ecfbfa2260c1360341ebfa5a93f7, 53e58a53691a5cc2403347332cbfa09a3717a46b5f770c6a626ae0e6dfd545bc, f950f5536d005afc1b7fb432a7cf5bff0bdc29fb81f1e427b43542de54b89912, 46e1b0537157b0b053db4b6519b3432261c9e0a1c13ca89dd537bb1d59fe7ae1`
- `boardExplicitLowRows`: `db2d1564b340b5b31a0113c4df702f709861e1a8e4b58745b1a11fb031bf8651, 2be64e75450abf6761094f0fb6011719890a6a9cd5f09d5c464c83d92880444d, 9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, fa070d5aca80533fd9b38a4cb43c1af154b2e5d2e456f2b552775f24ca3a85f3, eb9b2ce000b4dc274a0832a14b682e2bc81b7c2584df27ecd2a8286adfb51ebc, 708c8e44b6884abbc28080b22ccfd962197e37ee49dbe1dc9128dd12e1ed2c80, d76ec340dfc5c7073f4ee0a6cd574ead5ec30c68f06827f2392331a9180f7adf, aaaef3795309f37ad82e68447adb62c019e14d9e929b0d9aa34c81c4e4734492, b8b2fff13f42640489832974f5d0d914170617a3a5fd2534056e99aa47c979df, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f`
- `signalMetaLeakRows`: `없음`
- `displayMetaLeakRows`: `없음`
- `mixedClusterRoleLeakRows`: `없음`
- `roleConflictRows`: `없음`
- `roleLowConfidenceConflictRows`: `없음`
- `roleMissingClassifierRows`: `없음`
- `roleStaleClassifierRows`: `e7fa2af5786a826cf23ba90abe2893e43423bbbe50812e892c8d563acd36b9ba, 937cb03faad4a5d12cd5d56a799050f570a5c2466923121fc3e6d91fc1565bac, 6cc457dbc0ba62de75b2c9f89a7b2fc250ae3e2cacdf8cd653778b90deee5999, f2c4092751c810f49d2c315a4beb115280c7b061bb5d7bea29f7b9fdd782f218, a4014f0e58cacdb8cc8d66cf2f08ce5dab40b3ede8848161bf19ececf6e591b7, 8166db52cdbe91cb2c8441bc3c0044f500b562e1e4b322b62eb73b076fd301f8, 6f259c260fd07e5d14192f6a169fc4ba13d5685c9a1c26a08cf2bafbf0b5d3d1, 95e0bd563d26ffd7d9146e5fd040fd79c7a95d17a44b10de74e8ba093b26fcc3, 4b881d193164e8d403d5283090ae8196a0811997794f8a6149d855f5fb2d4aa9, ba9d41db62556f54c71f042b58eea60079ba9d7d2eebe21630301048e1a8f473`

## Next Actions

- `critical` `manual_model` `backfill_missing_summaries`: missing summary backfill (현재 low 보드 행의 큰 비중이 모델 품질이 아니라 summary 미생성 상태입니다.)
- `critical` `manual_model` `rerun_stale_role_signatures`: stale role signature 재판정 (요약 재생성 뒤 role override signature 가 stale 해져 보드가 최신 분류를 읽지 못합니다.)
- `medium` `manual_review` `expand_review_goldset`: 검수 골드셋 확장 (평가셋 검수 커버리지가 낮아 모델 품질 판단의 신뢰도가 떨어집니다.)
