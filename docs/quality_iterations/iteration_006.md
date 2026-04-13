# Quality Iteration 006

- 상태: `manual_intervention_required`
- 생성 시각: `2026-04-10T08:04:47.910975+00:00`
- optimization score: `80.0027`
- release champion: `gemma-4-31b / field_aware_v3`

## 핵심 지표

- boardLowRate: `0.045283`
- boardMissingSummaryRows: `0`
- boardExplicitLowRows: `12`
- signalMetaLeakRows: `0`
- mixedClusterRoleLeakRows: `0`
- roleConflictRows: `0`
- roleMissingClassifierRows: `49`
- roleStaleClassifierRows: `191`
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
- `roleConflictRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleMissingClassifierRows`: `actual=49.0` / `target=0.0` / `max` / `pass=False`
- `roleStaleClassifierRows`: `actual=191.0` / `target=0.0` / `max` / `pass=False`
- `releaseCoreFocusExact`: `actual=0.4286` / `target=0.85` / `min` / `pass=False`
- `releaseCoreKeywordF1`: `actual=0.5753` / `target=0.62` / `min` / `pass=False`
- `releaseIncrementalUsable`: `actual=0.9487` / `target=0.93` / `min` / `pass=True`
- `releaseIncrementalLowRate`: `actual=0.0513` / `target=0.08` / `max` / `pass=True`
- `releaseIncrementalBannedKeywordRate`: `actual=0.0` / `target=0.0` / `max` / `pass=True`

## 샘플

- `boardLowRows`: `9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, eb9b2ce000b4dc274a0832a14b682e2bc81b7c2584df27ecd2a8286adfb51ebc, 800d7f4b7af63cc4fcbd923b8d76aee2c4c2ebfdb3777297f9a976986c765009, 708c8e44b6884abbc28080b22ccfd962197e37ee49dbe1dc9128dd12e1ed2c80, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f, 1d96f77a4041bf5f7713462f400ada313717733c2e42cb42bdc3a5ec01ea0d09, ccb72064162209088093c8f39fdd5aae570517312bc1112b9444199b2a4e08ca, 80dd8761e1cf512f819ae16fd447624ad5cd753f05f0be1fc736e73dfa96fb81, 2be64e75450abf6761094f0fb6011719890a6a9cd5f09d5c464c83d92880444d, dcc6666c4ec968b53098490e72dfd5f1c44f71fe349e22165c0ba6bbbdcf73c4`
- `boardMissingSummaryRows`: `없음`
- `boardExplicitLowRows`: `9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5, eb9b2ce000b4dc274a0832a14b682e2bc81b7c2584df27ecd2a8286adfb51ebc, 800d7f4b7af63cc4fcbd923b8d76aee2c4c2ebfdb3777297f9a976986c765009, 708c8e44b6884abbc28080b22ccfd962197e37ee49dbe1dc9128dd12e1ed2c80, 612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f, 1d96f77a4041bf5f7713462f400ada313717733c2e42cb42bdc3a5ec01ea0d09, ccb72064162209088093c8f39fdd5aae570517312bc1112b9444199b2a4e08ca, 80dd8761e1cf512f819ae16fd447624ad5cd753f05f0be1fc736e73dfa96fb81, 2be64e75450abf6761094f0fb6011719890a6a9cd5f09d5c464c83d92880444d, dcc6666c4ec968b53098490e72dfd5f1c44f71fe349e22165c0ba6bbbdcf73c4`
- `signalMetaLeakRows`: `없음`
- `displayMetaLeakRows`: `없음`
- `mixedClusterRoleLeakRows`: `없음`
- `roleConflictRows`: `없음`
- `roleMissingClassifierRows`: `7d82997de2d751cca66deac40290fc6bf563db6050d0b9cc5e12c3e271092ddf, ba9d41db62556f54c71f042b58eea60079ba9d7d2eebe21630301048e1a8f473, 053211466c12ccae4e349e2eb0d7895a998b4349a588301d2d6abc4cfcf3930b, c72caa6f3cb7f3bf8b1139d162fb206ceeba37b9bdaaeb893afc77fa8029e052, b0182fab3007a45c522ddb8d061ce115d875ebdc425f25e18d97127c03a78a5e, 46533418b07ea3bcbf28e53b5992f60761da78725a1b93d93508ca3dc583631b, b8b2fff13f42640489832974f5d0d914170617a3a5fd2534056e99aa47c979df, 84584e02a8f3fd15f2d9099ccb5bb1b8da5d1bec6df53d1ea35b3a89e1ef2d2b, ccb72064162209088093c8f39fdd5aae570517312bc1112b9444199b2a4e08ca, 80dd8761e1cf512f819ae16fd447624ad5cd753f05f0be1fc736e73dfa96fb81`
- `roleStaleClassifierRows`: `d5527fef542a659d966f8a3b672f7831681564b25a9701ae58e5c3f645876575, 15e489b1ea72df2c08f08e6c273779bc96432bcfda7950a3f1c03df2dc5223d3, 937cb03faad4a5d12cd5d56a799050f570a5c2466923121fc3e6d91fc1565bac, e7fa2af5786a826cf23ba90abe2893e43423bbbe50812e892c8d563acd36b9ba, e749af38a2956b86e02f54b3785e06e3539369bdfbe72d321f33d7526da68c9a, 7a6ff0683f5b05ed36f85f4d571a2031229ae870cfbdcccec143a67352ad0e7d, c2d2b6199e099e11606bb0f5a72b35401054885cec0f0edd1de2c24fe7ac2bc0, 7b1509e2da2f3974e53bc722eb07d60af2753c80457cd851bae733efec9d153a, 95f3e5eabacbfa10024881abe08f9144bed0c1fb707d4005c49c21127afc4fe1, cca8f744faac52e4b712b665ce07bc8ae7dc68c42c513597fc42435841e8dd46`

## Next Actions

- `critical` `manual_model` `rerun_stale_role_signatures`: stale role signature 재판정 (요약 재생성 뒤 role override signature 가 stale 해져 보드가 최신 분류를 읽지 못합니다.)
- `high` `manual_benchmark` `run_candidate_release_gate`: candidate prompt release gate 재실행 (release gate 관련 지표 releaseCoreFocusExact, releaseCoreKeywordF1 가 목표 미달입니다.)
- `high` `manual_model` `rerun_role_group_wave`: role remediation wave 재판정 (전용 role 분류기 충돌 또는 비어 있는 출력이 남아 있습니다.)
- `medium` `manual_review` `expand_review_goldset`: 검수 골드셋 확장 (평가셋 검수 커버리지가 낮아 모델 품질 판단의 신뢰도가 떨어집니다.)
