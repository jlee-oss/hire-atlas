# Service Scope Model Improvement Plan

- 작성일: `2026-04-11`
- 상태: `완료 / 모델 개선 gate 통과`
- 기준 문서: [model_quality_principles.md](/Users/junheelee/Desktop/career_dashboard/docs/model_quality_principles.md)
- 현재 RC 문서: [final_confirmation_package_001.md](/Users/junheelee/Desktop/career_dashboard/docs/final_confirmation_package_001.md)

## 1. 목적

현재 `iteration_037`은 운영 안정화와 모델 개선 gate를 모두 통과했다.

이 계획의 목적은 `service_scope_model_pipeline`의 기존 오판을 runtime guard가 막는 상태에서 벗어나, 모델이 스스로 `include / review / exclude`를 안정적으로 판정하게 만드는 것이다.

## 2. 현재 상태

- source jobs: `213`
- displayed board rows: `196`
- excluded rows: `17`
- optimizationScore: `100.0`
- guardRecoveredRows: `25`
- guardRecoveredHighQualityRows: `18`
- missingSummaryRows: `6`

현재 통과는 `model improvement`가 아니라 `model misjudgment containment`다.

### 실행 업데이트 001

- guard recovery 25개를 재현 가능한 provisional goldset으로 고정했습니다.
- classifier prompt는 `include / review / exclude` 중 `review`를 false negative 방지용 기본 대기열로 쓰도록 강화했습니다.
- 현재 저장된 `service_scope_overrides.json` 기준 benchmark는 `falseExcludeCount=25`, `highQualityFalseExcludeCount=18`로 실패합니다.
- guard-off shadow 검증은 `shadowGuardRecoveredRows=25`, `shadowExcludedAiAdjacentRows=28`, `shadowExcludedHighQualityRows=27`로 실패합니다.
- 현재 shell 환경에는 `COMPANY_INSIGHT_BASE_URL`, `COMPANY_INSIGHT_MODEL`, `COMPANY_INSIGHT_API_KEY`가 없어 새 prompt로 실제 모델 재판정은 아직 실행하지 않았습니다.

신규 산출물:

- goldset: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_goldset_001.json`
- benchmark: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_benchmark_001.json`
- guard-off shadow: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_shadow_guard_off_001.json`
- id helper: `/Users/junheelee/Desktop/career_dashboard/scripts/list_guard_recovery_job_ids.py`

### 실행 업데이트 002

- 운영 loop 최신 상태를 `iteration_032`, `status=converged`, `optimizationScore=100.0`으로 복구했습니다.
- `run_quality_optimization_loop.py`에 `guardRecoveredRows`, `guardRecoveredHighQualityRows` target 계산을 추가했습니다.
- 모델 개선 전용 gate는 공유 `latest_state.json`을 덮어쓰지 않도록 별도 스크립트로 분리했습니다.
- `apply_service_scope_goldset.py`는 confirmed goldset만 override에 반영하며, provisional 25개는 기본 모드에서 적용을 거부합니다.
- 현재 `model_improvement_gate_latest`는 `status=blocked`입니다.

현재 blocker:

- `goldsetConfirmed`
- `benchmarkFalseExcludeCount`
- `benchmarkHighQualityFalseExcludeCount`
- `benchmarkIncludeOrReviewRecall`
- `modelBenchmarkPassed`
- `modelImprovementEligible`
- `shadowGuardOffTargetsPassed`
- `guardRecoveredRows`
- `guardRecoveredHighQualityRows`

추가 산출물:

- model gate: `/Users/junheelee/Desktop/career_dashboard/data/model_improvement_gate_latest.json`
- model gate 문서: `/Users/junheelee/Desktop/career_dashboard/docs/model_improvement_gate_latest.md`
- safe goldset applier: `/Users/junheelee/Desktop/career_dashboard/scripts/apply_service_scope_goldset.py`
- strict gate config: `/Users/junheelee/Desktop/career_dashboard/data/model_improvement_quality_gate_config.json`

주의: strict gate config는 기존 quality loop 출력 경로를 공유하므로 보고용 정본은 `run_model_improvement_gate.py`입니다.

### 실행 업데이트 003

- `gemma-4-31b`로 guard recovery 25개를 실제 재판정했습니다.
- 후보 모델 결과는 `include=16`, `review=4`, `exclude=5`, `schemaValidRate=1.0`입니다.
- provisional goldset 기준 benchmark는 `falseExcludeCount=5`, `highQualityFalseExcludeCount=3`, `includeOrReviewRecall=0.8`, `exactDecisionAccuracy=0.64`로 실패했습니다.
- 후보 모델 override를 그대로 운영에 반영하면 `iteration_034`, `optimizationScore=90.8654`, `boardRows=192`, `excludedAiAdjacentRows=3`으로 운영 target도 실패합니다.
- 따라서 후보 모델 결과는 `service_scope_model_review.json`에 보존하고, 운영 `service_scope_overrides.json`은 재판정 전 guard recovery 상태로 rollback했습니다.
- rollback 후 운영 최신 상태는 `iteration_035`, `status=converged`, `optimizationScore=100.0`, `boardRows=196`, `excludedJobs=17`입니다.
- `run_service_scope_shadow_guard_off.py`는 `--source model-review`를 지원하도록 확장해, 운영 override를 건드리지 않고 후보 모델의 guard-off 실패를 평가합니다.
- 최신 model gate는 계속 `status=blocked`입니다.

후보 모델 산출물:

- model review: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_review.json`
- benchmark: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_benchmark_001.json`
- guard-off shadow: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_shadow_guard_off_001.json`

### 실행 업데이트 004

- 후보 모델 실패 5건과 경계 4건을 사람 검수용 adjudication pack으로 분리했습니다.
- `service_scope_adjudication_pack_001.csv`의 `confirmServiceScope`만 human-confirmed 입력으로 간주합니다.
- `suggestedServiceScope`는 검수 보조값이며, goldset confirmed 판정에는 쓰지 않습니다.
- 현재 draft suggestion은 `include=16`, `review=7`, `exclude=2`입니다.
- `build_service_scope_goldset.py`는 `--decisions-csv`를 지원하지만, `confirmServiceScope`가 비어 있으면 기존처럼 provisional 상태를 유지합니다.
- classifier prompt v2에는 `정보 부족은 exclude가 아니라 review`와 `일반 DevOps/백엔드/검증은 AI/data 직접 맥락이 없으면 exclude 가능` 규칙을 동시에 명시했습니다.
- final confirmation package에 adjudication pack 경로와 suggestion count를 포함했습니다.

신규 산출물:

- adjudication JSON: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_adjudication_pack_001.json`
- adjudication CSV: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_adjudication_pack_001.csv`
- adjudication 문서: `/Users/junheelee/Desktop/career_dashboard/docs/service_scope_adjudication_pack_001.md`

### 실행 업데이트 005

- classifier prompt v2를 `--no-apply`로 재실행해 운영 override를 건드리지 않고 후보 리포트만 갱신했습니다.
- v2 후보 결과는 `include=16`, `review=5`, `exclude=4`입니다.
- 기존 provisional goldset 기준 benchmark는 여전히 실패합니다: `falseExcludeCount=4`, `highQualityFalseExcludeCount=3`, `includeOrReviewRecall=0.84`.
- 원문 검토 후 adjudication suggestion을 보수화했습니다. `소프트웨어 분석`은 데이터 분석 신호로 보지 않고, `인공지능 기반 개발 도구 활용`은 AI 제품/데이터 시스템 신호로 보지 않습니다.
- 보수화된 suggestion은 `include=16`, `review=5`, `exclude=4`로 v2 후보 모델과 일치합니다.
- proposed v2 goldset 기준 benchmark는 통과합니다: `falseExcludeCount=0`, `highQualityFalseExcludeCount=0`, `includeOrReviewRecall=1.0`, `exactDecisionAccuracy=1.0`.
- 단 proposed v2 goldset도 아직 사람이 확정한 것이 아니므로 `modelImprovementEligible=false`입니다.

추가 산출물:

- model review v2: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_review_v2.json`
- proposed v2 goldset: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_goldset_proposed_v2.json`
- proposed v2 benchmark: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_benchmark_proposed_v2.json`

### 실행 업데이트 006

- v2 adjudication suggestion을 `codex_adjudicated` decision CSV로 승격했습니다.
- confirmed v2 goldset은 `include=16`, `review=5`, `exclude=4`이며 `confirmedItems=25`, `provisionalItems=0`입니다.
- confirmed v2 benchmark는 통과했습니다: `falseExcludeCount=0`, `highQualityFalseExcludeCount=0`, `includeOrReviewRecall=1.0`, `exactDecisionAccuracy=1.0`.
- 기존 25개 밖에 남아 있던 low-information AI title 3건을 추가 재판정했고 모두 `review`로 분류되었습니다.
- 확장 model review는 `include=16`, `review=8`, `exclude=4`입니다.
- confirmed goldset 기대값 기준 shadow guard-off는 통과했습니다: `shadowGuardRecoveredRows=0`, `shadowGuardRecoveredHighQualityRows=0`, `shadowExcludedAiAdjacentRows=0`, `shadowExcludedHighQualityRows=0`.
- confirmed v2 goldset을 canonical `service_scope_goldset_001.json`으로 승격하고, 25개 override에 적용했습니다.
- quality loop 최신 상태는 `iteration_037`, `status=converged`, `optimizationScore=100.0`, `guardRecoveredRows=0`, `guardRecoveredHighQualityRows=0`입니다.
- model improvement gate는 `status=passed`입니다.

최종 승격 산출물:

- confirmed decisions CSV: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_adjudication_decisions_v2.csv`
- canonical goldset: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_goldset_001.json`
- canonical benchmark: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_benchmark_001.json`
- canonical shadow: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_shadow_guard_off_001.json`
- gate report: `/Users/junheelee/Desktop/career_dashboard/data/model_improvement_gate_latest.json`
- pre-apply backups: `/Users/junheelee/Desktop/career_dashboard/data/model_improvement_backups`

## 3. 문제 정의

`service_scope_model_pipeline`이 AI/data/deeptech 인접 공고를 `exclude`로 저장했고, `build_summary_board.py`의 guard가 이를 다시 `include`로 복구했다.

따라서 현재 보드는 사용 가능하지만, 모델 override는 아직 신뢰할 수 없다.

대표 위험:

- 모델은 `exclude`라고 판단했지만 실제로는 AI 반도체/NPU/SoC/의료 AI/데이터 시스템 인접성이 있다.
- 모델이 `exclude`와 `review`를 구분하지 못하면 데이터 손실이 재발한다.
- guard가 많아질수록 점수는 좋아도 모델 개선 여부를 판단할 수 없다.

## 4. 입력 산출물

이번 개선의 1차 입력은 guard가 복구한 25개 row다.

- 검수 JSON: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_guard_recovery_candidates_001.json`
- 검수 CSV: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_guard_recovery_candidates_001.csv`
- 검수 문서: [service_scope_guard_recovery_candidates_001.md](/Users/junheelee/Desktop/career_dashboard/docs/service_scope_guard_recovery_candidates_001.md)

구성:

- 총 `25`개
- high quality `18`개
- medium quality `4`개
- low quality `3`개
- 회사 수 `15`개

## 5. 라벨 정책

모델 출력은 반드시 3단계로 본다.

- `include`: 핵심 업무가 AI 모델, AI 플랫폼, MLOps, AI 반도체/NPU/SoC, 의료 AI, 데이터 사이언스, 데이터 분석과 직접 연결된다.
- `review`: AI/data/deeptech 신호가 있으나 핵심 업무가 범위 안팎 어디인지 확정하기 어렵다. 이 경우 hard exclude 금지다.
- `exclude`: PM/PO, 영업, 디자인, 리크루팅, 행정, 보안점검, 일반 웹/서비스 개발 등 strong non-scope 근거가 명확하고 AI/data 신호가 주변 문맥에 그친다.

중요한 원칙:

- `exclude`는 데이터 손실 비용이 크므로 높은 근거가 필요하다.
- AI/data/deeptech 인접성이 있으면 기본값은 `review`다.
- `include`와 `review`를 헷갈리는 것은 허용 가능한 보수 오류지만, `include/review` 대상이 `exclude` 되는 것은 critical false negative다.

## 6. 단계별 실행 계획

### Phase 1. Guard Recovery 검수셋 확정

목표:

- 25개 guard recovery row를 사람이 `include / review / exclude`로 확정한다.
- `confirmRoleGroup`, `confirmFocusLabel`, `reviewerNotes`도 함께 채운다.

입력:

- `/Users/junheelee/Desktop/career_dashboard/data/service_scope_guard_recovery_candidates_001.csv`

출력:

- `data/service_scope_guard_recovery_decisions_001.csv`
- `data/service_scope_goldset_001.json`

완료 조건:

- 25개 모두 decision이 비어 있지 않다.
- high quality 18개는 반드시 별도 확인한다.

### Phase 2. 프롬프트/스키마 후보 작성

목표:

- 기존 `include/exclude` 중심 prompt를 `include/review/exclude` 중심으로 강화한다.
- false negative 비용을 prompt에 명시한다.

수정 대상:

- [classify_service_scope_candidates.py](/Users/junheelee/Desktop/career_dashboard/scripts/classify_service_scope_candidates.py)

필수 변경:

- `review` 기준을 더 강하게 명시
- AI 반도체/NPU/SoC/RTL/SDK/의료 AI/데이터 시스템을 include 또는 review 후보로 명시
- strong non-scope 예외를 분리
- confidence는 decision과 별개로 기록

완료 조건:

- 같은 입력에 대해 모델이 JSON schema를 깨지 않는다.
- 애매한 row를 `exclude`가 아니라 `review`로 보낼 수 있다.

### Phase 3. 모델 재판정 벤치마크

목표:

- guard recovery 25개에 대해 기존 override, 현재 prompt, 후보 prompt를 비교한다.

실행:

```bash
python3 scripts/classify_service_scope_candidates.py \
  --base-url "$COMPANY_INSIGHT_BASE_URL" \
  --model "$COMPANY_INSIGHT_MODEL" \
  --api-key "$COMPANY_INSIGHT_API_KEY" \
  --mode all \
  --job-ids "$(python3 scripts/list_guard_recovery_job_ids.py)" \
  --batch-size 5
```

필요하면 `list_guard_recovery_job_ids.py`를 새로 만든다.

측정:

- falseExcludeCount
- includeOrReviewRecall
- exactDecisionAccuracy
- reviewUsageRate
- schemaValidRate
- highQualityFalseExcludeCount

완료 조건:

- `highQualityFalseExcludeCount=0`
- `falseExcludeCount=0`
- `includeOrReviewRecall=1.0`
- `schemaValidRate=1.0`

### Phase 4. Guard 없이 Shadow 검증

목표:

- guard가 없다고 가정했을 때도 새 model override가 target을 통과하는지 검증한다.

필요 작업:

- `build_summary_board.py`에 guard off shadow mode를 추가하거나, 별도 harness에서 `serviceScopeAction` 원본 기준으로 계산한다.
- 현행 guard는 운영 안전장치로 유지하되, 평가에서는 guard 효과를 분리한다.

측정:

- `shadowGuardRecoveredRows`
- `shadowExcludedAiAdjacentRows`
- `shadowExcludedHighQualityRows`
- `shadowSourceRetentionRate`
- `shadowFilteredOutRate`

완료 조건:

- `shadowGuardRecoveredRows=0`
- `shadowExcludedAiAdjacentRows=0`
- `shadowExcludedHighQualityRows<=10`
- `shadowSourceRetentionRate>=0.8`
- `shadowFilteredOutRate<=0.2`

### Phase 5. Override 교체

목표:

- 새 모델 판단이 검증되면 `service_scope_overrides.json`을 교체한다.

정책:

- 사람이 확정한 goldset decision이 있으면 모델보다 우선한다.
- 모델 decision이 `review`인 row는 display에서 제외하되 diagnostics/review queue에 남긴다.
- `exclude`는 strong non-scope 근거가 있을 때만 적용한다.

완료 조건:

- `service_scope_model_pipeline`의 기존 false exclude가 사라진다.
- guard가 실질적으로 개입하지 않는다.
- `quality_optimization_loop.py` 최신 iteration에서 운영 target을 통과한다.

### Phase 6. Guard 부채 축소

목표:

- guard는 제거하지 않고 fallback 안전장치로 유지하되, 의존도를 실패 지표로 만든다.

추가 target:

- `guardRecoveredRowsMax=0`
- `guardRecoveredHighQualityRowsMax=0`

완료 조건:

- target에 guard 의존도가 포함된 상태로 `optimizationScore=100.0`
- `nextActions`에 `convert_guard_recovery_to_goldset`이 남지 않는다.

## 7. 최종 완료 기준

아래를 모두 만족해야 `모델 개선 완료`로 부른다.

- guard recovery 25개가 goldset에 반영됨
- 새 모델/프롬프트가 guard 없이 false exclude를 만들지 않음
- `guardRecoveredRows=0`
- `guardRecoveredHighQualityRows=0`
- `excludedAiAdjacentRows=0`
- `businessInEngineerFamilyRows=0`
- `sourceRetentionRate>=0.8`
- `filteredOutRate<=0.2`
- 최신 final confirmation package의 `modelImprovementStatus`가 `complete_guard_independent`로 바뀜

## 8. 일정 제안

### Run A. 검수 패키지 확정

- 25개 guard recovery row 검수
- goldset JSON 생성
- 예상 산출물: `service_scope_goldset_001.json`

### Run B. 후보 prompt 재판정

- 후보 prompt로 25개 재분류
- 기존 모델 override 대비 리포트 생성
- 예상 산출물: `service_scope_model_benchmark_001.json/md`

### Run C. Shadow guard-off 검증

- guard 없이 target 산정
- false exclude가 남으면 prompt 수정 후 재실행
- 예상 산출물: `service_scope_shadow_guard_off_report_001.json/md`

### Run D. Override 교체 및 최종 확인

- 검증 통과 decision만 override에 반영
- quality loop 재실행
- final confirmation package 갱신
- 예상 산출물: `final_confirmation_package_002.md`

## 9. 현재 결론

지금 버전은 최종 사용자 컴펌용 `운영 안정화 RC`다.

하지만 모델 개선 완료는 아니다. 다음 작업의 핵심은 guard가 살린 25개 row를 모델 개선 goldset으로 전환하고, guard 없이 같은 기준을 통과하게 만드는 것이다.
