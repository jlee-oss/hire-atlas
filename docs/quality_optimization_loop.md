# Quality Optimization Loop

이 문서는 `분류 / 키워드 / 군집` 품질을 반복적으로 점검하고, 다음 수행을 기록하며, 목표 범위에 수렴하면 자동으로 멈추는 운영 루프를 설명합니다.

## 목적

- 현재 서비스 품질을 `숫자`로 계속 추적합니다.
- 각 실행마다 `무엇이 아직 문제인지`, `다음에 무엇을 해야 하는지`를 자동으로 기록합니다.
- 품질이 목표 범위에 들어오면 자동으로 중지하고, 보고서만 남깁니다.
- 품질이 수렴하지 않으면 `어떤 축이 병목인지`를 명시한 채 다음 remediation artifact를 갱신합니다.

## 핵심 원칙

- 기준 문서는 [model_quality_principles.md](/Users/junheelee/Desktop/career_dashboard/docs/model_quality_principles.md) 입니다.
- `배제`나 `가리기`는 본질 해결로 간주하지 않습니다.
- `raw 채용 문장`이 카드 라벨을 직접 만들지 않도록 구조를 계속 감시합니다.
- `모델 기반 구조화 신호`와 `release gate`를 품질 기준으로 삼습니다.
- 하네스는 `실제 오분류`와 `문맥 존재`를 구분합니다.
  - 예: `deeptech_in_data_analyst`, `business_in_engineer_family`는 dominance failure입니다.
  - `deeptech_context_present`, `business_context_present`는 info family입니다.
  - `broad_focus_specificity_gap`은 focus가 너무 넓어 더 구체한 신호를 가리는지 보는 medium family입니다.

## 실행 스크립트

- 메인 루프: [run_quality_optimization_loop.py](/Users/junheelee/Desktop/career_dashboard/scripts/run_quality_optimization_loop.py)
- 설정 파일: [quality_optimization_loop_config.json](/Users/junheelee/Desktop/career_dashboard/data/quality_optimization_loop_config.json)

## 자동으로 갱신하는 산출물

- summary snapshot
- release remediation wave
- role group remediation wave
- model decision report
- role group benchmark snapshot
- review accuracy report

이 산출물은 루프 실행 시 자동으로 새로 만들거나 덮어씁니다.

- 최신 summary snapshot: [summary_snapshot_latest.json](/Users/junheelee/Desktop/career_dashboard/data/summary_snapshot_latest.json)
- 최신 role benchmark: [role_group_benchmark_latest.json](/Users/junheelee/Desktop/career_dashboard/data/role_group_benchmark_latest.json)

## 측정 전 자동 복구

- 모델 설정이 있고 `autoRepairs.refreshMissingSummariesBeforeMeasure`가 켜져 있으면, 루프는 측정 전에 `missing/low summary`를 먼저 backfill 합니다.
- 모델 설정이 있고 `autoRepairs.refreshRoleOverridesBeforeMeasure`가 켜져 있으면, 루프는 측정 전에 `stale role override`를 먼저 다시 분류합니다.
- `autoRepairs.refreshMissingRoleOverridesBeforeMeasure`까지 켜져 있으면, 이어서 `missing role override`도 보강한 뒤 보드를 다시 빌드합니다.
- 즉 같은 실행 안에서 `summary 미생성`과 `stale signature` 때문에 지표가 거짓으로 나빠지는 문제를 먼저 줄인 뒤 측정합니다.

## 기록 위치

- JSON 기록: `/Users/junheelee/Desktop/career_dashboard/data/quality_iterations/iteration_XXX.json`
- Markdown 기록: `/Users/junheelee/Desktop/career_dashboard/docs/quality_iterations/iteration_XXX.md`
- 최신 상태: `/Users/junheelee/Desktop/career_dashboard/data/quality_iterations/latest_state.json`

## 추적 지표

- `boardLowRate`
- `boardMissingSummaryRows`
- `signalMetaLeakRows`
- `mixedClusterRoleLeakRows`
- `roleConflictRows`
- `roleMissingClassifierRows`
- `roleStaleClassifierRows`
- `releaseCoreFocusExact`
- `releaseCoreKeywordF1`
- `releaseIncrementalUsable`
- `releaseIncrementalLowRate`
- `releaseIncrementalBannedKeywordRate`
- `sourceRetentionRate`
- `filteredOutRate`
- `excludedHighQualityRows`
- `excludedAiAdjacentRows`
- `excludedLeakedIntoDisplayRows`
- `deeptechInDataAnalystRows`
- `businessInEngineerFamilyRows`
- `toolFirstFocusRows`
- `serviceScopeStaleRows`
- `broadFocusSpecificityGap`

## 자동 중지 조건

- 위 지표들이 설정 파일의 목표 범위 안에 모두 들어오면 `converged` 상태로 중지합니다.
- 목표에 못 들어왔더라도, 연속 실행에서 점수 변화가 거의 없고 자동으로 더 바꿀 수 있는 항목이 없으면 `manual_intervention_required` 또는 `plateaued`로 중지합니다.
- 백그라운드 연속 실행은 [run_continuous_quality_loop.py](/Users/junheelee/Desktop/career_dashboard/scripts/run_continuous_quality_loop.py)를 사용합니다.
- 이 wrapper는 `run_quality_optimization_loop.py`를 반복 호출하고, `optimizationScore`와 모든 target check가 기준을 만족할 때만 종료합니다.
- 단일 loop가 `manual_intervention_required`로 끝나도 wrapper는 다음 주기에서 다시 측정합니다. 즉 사람이 검수/수정하거나 API key가 주입된 뒤에도 같은 background process가 다음 판단을 이어갈 수 있습니다.
- 현재 추가된 핵심 중지 기준은 `excludedAiAdjacentRows=0`, `excludedHighQualityRows<=10`, `businessInEngineerFamilyRows=0`, `sourceRetentionRate>=0.8`, `filteredOutRate<=0.2`입니다. 이는 단순히 보드 row 수를 줄여 score를 올리는 경로를 막기 위한 최소 방어선입니다.
- `excludedAiAdjacentRows`는 충분한 summary 근거가 있는 AI/data/deeptech 인접 row가 hard exclude로 사라지는지를 봅니다. 단순 저품질/직무 상세 부족 row나 PM·영업·디자인·행정처럼 강한 non-scope 증거가 있는 row는 false negative 위험으로 세지 않습니다.
- 최신 검증 기준 통과 결과는 `iteration_028`, `optimizationScore=100.0`, `stopReason=criteria_met`입니다.

## iteration_028 해석 기록

- `iteration_028`의 `converged`는 모델 자체가 개선되었다는 뜻이 아닙니다.
- 이번 통과는 주로 `service_scope_model_pipeline`의 hard exclude가 AI/data/deeptech 근거 row를 삭제하지 못하게 하는 guard와, 엔지니어 row의 business/tool-first focus를 낮추는 후처리로 달성되었습니다.
- 따라서 현재 상태는 `model improvement`가 아니라 `model misjudgment containment`, 즉 모델 오판이 데이터 손실로 이어지는 경로를 막은 상태입니다.
- 진짜 모델 개선으로 인정하려면 guard가 복구한 row를 평가셋에 넣고, `include/review/exclude`, `mappedRole`, `focusLabel`, `keywords`를 새 모델/프롬프트로 다시 산정한 뒤 guard 없이 동일 target을 통과해야 합니다.
- 이 검증 전까지 `optimizationScore=100.0`은 운영 안정화 점수로만 해석하고, 모델 성능 향상 근거로 쓰지 않습니다.

## 최종 컴펌 패키지

- 최종 컴펌용 운영 안정화 RC는 [final_confirmation_package_001.md](/Users/junheelee/Desktop/career_dashboard/docs/final_confirmation_package_001.md)에 기록합니다.
- guard 복구 25개 검수 대상은 [service_scope_guard_recovery_candidates_001.md](/Users/junheelee/Desktop/career_dashboard/docs/service_scope_guard_recovery_candidates_001.md)에 기록합니다.
- 모델 개선 완료까지의 실행 계획은 [service_scope_model_improvement_plan.md](/Users/junheelee/Desktop/career_dashboard/docs/service_scope_model_improvement_plan.md)에 기록합니다.
- CSV 검수 파일은 `/Users/junheelee/Desktop/career_dashboard/data/service_scope_guard_recovery_candidates_001.csv`입니다.
- 이 패키지의 승인 문구는 `운영 안정화 RC는 승인 가능. 모델 개선 완료는 guard recovery goldset 검증 전까지 보류.`입니다.

## 기본 실행 예시

```bash
python3 /Users/junheelee/Desktop/career_dashboard/scripts/run_quality_optimization_loop.py
```

## 백그라운드 연속 실행 예시

```bash
python3 /Users/junheelee/Desktop/career_dashboard/scripts/run_continuous_quality_loop.py \
  --per-run-iterations 3 \
  --interval-seconds 300 \
  --min-score 100
```

상태 파일은 `/Users/junheelee/Desktop/career_dashboard/data/quality_iterations/continuous_loop_state.json`에 기록되고, 라인 로그는 `/Users/junheelee/Desktop/career_dashboard/logs/continuous_quality_loop.ndjson`에 누적됩니다.

## 선택적 release gate 실행

API 정보가 있을 때만 candidate prompt를 같이 검증할 수 있습니다.

```bash
python3 /Users/junheelee/Desktop/career_dashboard/scripts/run_quality_optimization_loop.py \
  --base-url https://api.vibemakers.kr/v1 \
  --model gemma-4-31b \
  --api-key YOUR_KEY \
  --candidate-profile field_aware_v9 \
  --compare-to field_aware_v3
```

candidate가 gate를 통과하고 `autoApplyChampion`이 켜져 있으면, 루프가 release config 업데이트까지 자동 적용합니다.

## 모델 액션 실행 조건

- summary 재생성, role 재판정, release gate 재실행 같은 모델 액션은 `baseUrl`, `model`, `apiKey`가 모두 있을 때만 자동 실행됩니다.
- API 정보가 없으면 루프는 측정과 기록은 계속 수행하되, `manual_intervention_required` 상태로 멈추고 다음 액션만 제안합니다.
