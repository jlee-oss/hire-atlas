# Quality Iteration 017

- 상태: `manual_intervention_required`
- 생성 시각: `2026-04-10T09:52:16.912090+00:00`
- optimization score: `76.4529`
- release champion: `gemma-4-31b / field_aware_v3`

## 핵심 지표

- boardLowRate: `0.286792`
- boardMissingSummaryRows: `65`
- boardExplicitLowRows: `11`
- signalMetaLeakRows: `0`
- mixedClusterRoleLeakRows: `0`
- roleConflictRows: `0`
- roleLowConfidenceConflictRows: `0`
- roleMissingClassifierRows: `0`
- roleStaleClassifierRows: `257`
- releaseCoreFocusExact: `0.9286`
- releaseCoreKeywordF1: `0.8079`
- releaseIncrementalUsable: `0.9697`
- releaseIncrementalLowRate: `0.0303`
- releaseIncrementalBannedKeywordRate: `0.0`

## Target Checks

- `boardLowRate`: `actual=0.286792` / `target=0.05` / `max` / `pass=False`
- `boardMissingSummaryRows`: `actual=65.0` / `target=0.0` / `max` / `pass=False`
- `signalMetaLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `mixedClusterRoleLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleConflictRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleMissingClassifierRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleStaleClassifierRows`: `actual=257.0` / `target=0.0` / `max` / `pass=False`
- `releaseCoreFocusExact`: `actual=0.9286` / `target=0.85` / `min` / `pass=True`
- `releaseCoreKeywordF1`: `actual=0.8079` / `target=0.62` / `min` / `pass=True`
- `releaseIncrementalUsable`: `actual=0.9697` / `target=0.93` / `min` / `pass=True`
- `releaseIncrementalLowRate`: `actual=0.0303` / `target=0.08` / `max` / `pass=True`
- `releaseIncrementalBannedKeywordRate`: `actual=0.0` / `target=0.0` / `max` / `pass=True`

## 샘플

- `boardLowRows`: `b7cd343f31600421ea16fd66c441b20aafe3e71023438405a0df6f45ddd7fac3, 9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, 4edf5d71ede69bba8e2a1977ec561ebc254937a291afd7e3b61dc14db2e13c10, 3df159f3833ac42a707314ca7d1d01c164fcebe7b0bb14fb6b71a6e8167f19fb, fa070d5aca80533fd9b38a4cb43c1af154b2e5d2e456f2b552775f24ca3a85f3, 6b05164bb2c48c397a3ed7be1f0e01ae1359ecfbfa2260c1360341ebfa5a93f7, 53e58a53691a5cc2403347332cbfa09a3717a46b5f770c6a626ae0e6dfd545bc, f950f5536d005afc1b7fb432a7cf5bff0bdc29fb81f1e427b43542de54b89912, 46e1b0537157b0b053db4b6519b3432261c9e0a1c13ca89dd537bb1d59fe7ae1, 9b0654078e9a0ab2e1ea3982b4377465f14af34a047610b7864b9f8f7177be4e`
- `boardMissingSummaryRows`: `b7cd343f31600421ea16fd66c441b20aafe3e71023438405a0df6f45ddd7fac3, 4edf5d71ede69bba8e2a1977ec561ebc254937a291afd7e3b61dc14db2e13c10, 3df159f3833ac42a707314ca7d1d01c164fcebe7b0bb14fb6b71a6e8167f19fb, fa070d5aca80533fd9b38a4cb43c1af154b2e5d2e456f2b552775f24ca3a85f3, 6b05164bb2c48c397a3ed7be1f0e01ae1359ecfbfa2260c1360341ebfa5a93f7, 53e58a53691a5cc2403347332cbfa09a3717a46b5f770c6a626ae0e6dfd545bc, f950f5536d005afc1b7fb432a7cf5bff0bdc29fb81f1e427b43542de54b89912, 46e1b0537157b0b053db4b6519b3432261c9e0a1c13ca89dd537bb1d59fe7ae1, 9b0654078e9a0ab2e1ea3982b4377465f14af34a047610b7864b9f8f7177be4e, 2284e6c9342420836a55e2f5c2af756d82ce6c79b26574286e7d7abdb929c39e`
- `boardExplicitLowRows`: `9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, 9ba7b9b4ab629bde0ece86efb05daa9d647efde59bace3f7fdb7db064ab19978, 708c8e44b6884abbc28080b22ccfd962197e37ee49dbe1dc9128dd12e1ed2c80, d76ec340dfc5c7073f4ee0a6cd574ead5ec30c68f06827f2392331a9180f7adf, aaaef3795309f37ad82e68447adb62c019e14d9e929b0d9aa34c81c4e4734492, b8b2fff13f42640489832974f5d0d914170617a3a5fd2534056e99aa47c979df, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f, 1d96f77a4041bf5f7713462f400ada313717733c2e42cb42bdc3a5ec01ea0d09, db2d1564b340b5b31a0113c4df702f709861e1a8e4b58745b1a11fb031bf8651, 2be64e75450abf6761094f0fb6011719890a6a9cd5f09d5c464c83d92880444d`
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
