# Quality Iteration 001

- 상태: `manual_intervention_required`
- 생성 시각: `2026-04-10T05:53:09.917497+00:00`
- optimization score: `75.9518`
- release champion: `gemma-4-31b / field_aware_v3`

## 핵심 지표

- boardLowRate: `0.256604`
- signalMetaLeakRows: `0`
- mixedClusterRoleLeakRows: `0`
- roleConflictRows: `0`
- roleMissingClassifierRows: `263`
- releaseCoreFocusExact: `0.4286`
- releaseCoreKeywordF1: `0.5753`
- releaseIncrementalUsable: `0.9487`
- releaseIncrementalLowRate: `0.0513`
- releaseIncrementalBannedKeywordRate: `0.0`

## Target Checks

- `boardLowRate`: `actual=0.256604` / `target=0.05` / `max` / `pass=False`
- `signalMetaLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `mixedClusterRoleLeakRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleConflictRows`: `actual=0.0` / `target=0.0` / `max` / `pass=True`
- `roleMissingClassifierRows`: `actual=263.0` / `target=0.0` / `max` / `pass=False`
- `releaseCoreFocusExact`: `actual=0.4286` / `target=0.85` / `min` / `pass=False`
- `releaseCoreKeywordF1`: `actual=0.5753` / `target=0.62` / `min` / `pass=False`
- `releaseIncrementalUsable`: `actual=0.9487` / `target=0.93` / `min` / `pass=True`
- `releaseIncrementalLowRate`: `actual=0.0513` / `target=0.08` / `max` / `pass=True`
- `releaseIncrementalBannedKeywordRate`: `actual=0.0` / `target=0.0` / `max` / `pass=True`

## 샘플

- `boardLowRows`: `b069c168e7db9f950e1be45aeec8fdf37bf63dc55e9242bcb4b2dabb776b8c72, ccb72064162209088093c8f39fdd5aae570517312bc1112b9444199b2a4e08ca, 84584e02a8f3fd15f2d9099ccb5bb1b8da5d1bec6df53d1ea35b3a89e1ef2d2b, 80dd8761e1cf512f819ae16fd447624ad5cd753f05f0be1fc736e73dfa96fb81, e7bdb35202c0b6e7e009e1296ff9748e02e294a2cc1a4a5d9834f06ecf3b8646, d82ee9868386aa10a7bb90c5074d0dac10b8bc46d813dc005e8f9a20609ffc34, 8276f363942d373702856aaa8469f0132dcd2c0d7dcf665d1327d0d98985e961, 340d2d95861f4158083a6312ff2611a4810e0535ea6f488eafbb1390b93f573e, 2be64e75450abf6761094f0fb6011719890a6a9cd5f09d5c464c83d92880444d, 9c932a0a27b486bb9d4f67f5c6912010dc03b233b28101e1dbad95e661bc6da5`
- `signalMetaLeakRows`: `없음`
- `displayMetaLeakRows`: `없음`
- `mixedClusterRoleLeakRows`: `없음`
- `roleConflictRows`: `없음`
- `roleMissingClassifierRows`: `d4ebcf1914b69150717dc042ba1ffa7ce5955f4561bda4278525ec98451648b2, 70c40025f4e22a077dd1b921d0c297acc6b8ef4932e039799bf6eaeaed4b6f83, d5527fef542a659d966f8a3b672f7831681564b25a9701ae58e5c3f645876575, 15e489b1ea72df2c08f08e6c273779bc96432bcfda7950a3f1c03df2dc5223d3, 937cb03faad4a5d12cd5d56a799050f570a5c2466923121fc3e6d91fc1565bac, e7fa2af5786a826cf23ba90abe2893e43423bbbe50812e892c8d563acd36b9ba, 1ca357b80df38943238b62a05c7565408b612ce1d13af84710e2ba1c3abf59cc, e749af38a2956b86e02f54b3785e06e3539369bdfbe72d321f33d7526da68c9a, 7a6ff0683f5b05ed36f85f4d571a2031229ae870cfbdcccec143a67352ad0e7d, c2d2b6199e099e11606bb0f5a72b35401054885cec0f0edd1de2c24fe7ac2bc0`

## Next Actions

- `high` `manual_benchmark` `run_candidate_release_gate`: candidate prompt release gate 재실행 (release gate 관련 지표 releaseCoreFocusExact, releaseCoreKeywordF1 가 목표 미달입니다.)
- `high` `manual_model` `rerun_role_group_wave`: role remediation wave 재판정 (전용 role 분류기 충돌 또는 비어 있는 출력이 남아 있습니다.)
- `medium` `manual_review` `expand_review_goldset`: 검수 골드셋 확장 (평가셋 검수 커버리지가 낮아 모델 품질 판단의 신뢰도가 떨어집니다.)
