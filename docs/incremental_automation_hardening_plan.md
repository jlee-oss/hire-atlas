# Incremental Automation Hardening Plan

- 작성일: `2026-04-12`
- 상태: `orchestrator 1차 구현 완료`
- 기준 RC: `iteration_037`
- 기준 패키지: `/Users/junheelee/Desktop/career_dashboard/docs/final_confirmation_package_001.md`

## 1. 현재 결론

현재 career dashboard의 service scope 모델 개선은 gate 기준으로 통과했다.

- operationalStatus: `ready_for_user_confirmation`
- modelImprovementStatus: `complete_guard_independent`
- optimizationScore: `100.0`
- guardRecoveredRows: `0`
- guardRecoveredHighQualityRows: `0`
- falseExcludeCount: `0`
- highQualityFalseExcludeCount: `0`
- shadowGuardOffTargetsPassed: `true`

따라서 다음 작업은 모델 성능 자체를 더 밀어붙이는 것이 아니라, 증분 데이터가 들어올 때도 같은 방어선을 자동으로 유지하는 체계를 만드는 것이다.

## 2. 승인된 운영 원칙

사용자는 증분 자동화 hardening 진행을 허락했다.

허락의 핵심 이유는 아래 원칙 때문이다.

> 기본값은 항상 `--no-apply`다.

증분 파이프라인은 모델 후보 결과를 먼저 생성하고, benchmark/shadow/quality/gate를 모두 통과하기 전까지 운영 override에 절대 반영하지 않는다.

## 3. 자동화 경계

### 허용

- 신규/변경 공고 후보 재판정
- 후보 결과 리포트 생성
- benchmark 실행
- shadow guard-off 실행
- quality loop 실행
- model improvement gate 실행
- final confirmation package 갱신
- 적용 전 dry-run 및 impact report 생성

### 금지

- gate 통과 전 `service_scope_overrides.json` 자동 수정
- provisional goldset 자동 적용
- `review`를 hard exclude처럼 취급
- API key를 파일에 저장
- 증분 실패를 운영 성공으로 포장

## 4. 적용 조건

운영 override 반영은 아래 조건을 모두 만족할 때만 가능하다.

- `goldsetStatus=confirmed`
- `provisionalGoldsetItems=0`
- `falseExcludeCount=0`
- `highQualityFalseExcludeCount=0`
- `includeOrReviewRecall=1.0`
- `schemaValidRate=1.0`
- `shadowGuardRecoveredRows=0`
- `shadowGuardRecoveredHighQualityRows=0`
- `shadowExcludedAiAdjacentRows=0`
- `shadowTargetsPassed=true`
- quality loop `status=converged`
- quality loop `optimizationScore=100.0`
- `modelImprovementGateStatus=passed`

## 5. 다음 구현 계획

### Phase A. 단일 orchestrator 작성

새 스크립트:

- `scripts/run_incremental_service_scope_pipeline.py`

기본 동작:

- 항상 dry-run
- 항상 `--no-apply`
- 후보 결과를 별도 파일에 저장
- 운영 override는 수정하지 않음

예상 입력:

- `--job-ids`
- `--changed-since`
- `--model-review-output`
- `--goldset`
- `--apply`는 명시적으로만 허용

구현 상태:

- 완료.
- 기본 실행은 report-only이며 운영 override를 수정하지 않는다.
- 모델 API 호출은 `--job-ids` 또는 `--job-ids-file`이 없으면 거부한다.
- 기존 후보 리포트를 평가하려면 `--skip-model-review`를 명시해야 한다.
- dry-run 결과는 `data/incremental_service_scope_pipeline_latest.json`와 `docs/incremental_service_scope_pipeline_latest.md`에 기록한다.

### Phase B. Gate bundle 생성

orchestrator는 한 번의 실행으로 아래 산출물을 생성한다.

- model review report
- benchmark report
- shadow guard-off report
- quality iteration
- model improvement gate
- final confirmation package
- apply/dry-run summary

### Phase C. Apply guard 추가

`--apply`가 들어와도 아래 조건을 통과하지 못하면 즉시 실패한다.

- confirmed goldset
- benchmark pass
- shadow pass
- quality pass
- model gate pass

실패 시에는 override를 수정하지 않는다.

구현 상태:

- 완료.
- `--apply`는 명시적일 때만 동작한다.
- gate 실패, quality 실패, apply dry-run 실패, non-canonical goldset apply는 fail-closed 한다.
- 적용 전 `data/model_improvement_backups`에 `service_scope_overrides.json` 백업을 남긴다.
- 적용 후 gate/quality 실패 시 backup에서 rollback한다.

### Phase D. Review queue SLA 추가

`review`는 데이터 손실이 아니라 검수 대기열이다.

다만 review가 무한히 쌓이지 않도록 별도 SLA를 둔다.

- `reviewJobs` count
- high-quality review rows
- 오래된 review rows
- review reason 분포

### Phase E. Human confirmation 정책 분리

decision source는 계속 분리한다.

- `human_confirmed`: 사람이 직접 승인
- `codex_adjudicated`: Codex가 원문/모델 근거로 확정
- `adjudication_suggestion_provisional`: 검수 보조값
- `guard_recovery_provisional`: guard 복구 provisional

대외적으로 강한 승인 문구를 쓰려면 `human_confirmed`로 별도 승격한다.

## 6. 완료 기준

증분 자동화 hardening은 아래를 만족하면 완료로 본다.

- orchestrator 한 명령으로 증분 후보 평가가 가능하다.
- 기본 실행은 운영 파일을 수정하지 않는다.
- `--apply`는 모든 gate 통과 후에만 가능하다.
- 실패 시 어떤 blocker 때문에 막혔는지 final package에 남는다.
- API key가 workspace 파일에 남지 않는다.
- review queue와 hard exclude가 metric에서 분리된다.

## 7. 다음 실행 명령 목표

최종 목표 명령 형태:

```bash
python3 scripts/run_incremental_service_scope_pipeline.py \
  --job-ids "$(python3 scripts/list_changed_service_scope_job_ids.py)" \
  --model-review-output data/service_scope_model_review_incremental_latest.json
```

승격 시에는 별도 명시가 필요하다.

```bash
python3 scripts/run_incremental_service_scope_pipeline.py \
  --job-ids "$(python3 scripts/list_changed_service_scope_job_ids.py)" \
  --model-review-output data/service_scope_model_review_incremental_latest.json \
  --apply
```

`--apply`는 gate가 하나라도 실패하면 override를 수정하지 않는다.

현재 검증된 dry-run 명령:

```bash
python3 scripts/run_incremental_service_scope_pipeline.py \
  --skip-model-review \
  --model-review-output data/service_scope_model_review.json
```

검증 결과:

- status: `passed`
- mode: `dry-run`
- gatePassed: `true`
- applied: `false`
- qualityStatus: `converged`
- optimizationScore: `100.0`

산출물:

- `/Users/junheelee/Desktop/career_dashboard/data/incremental_service_scope_pipeline_latest.json`
- `/Users/junheelee/Desktop/career_dashboard/docs/incremental_service_scope_pipeline_latest.md`
- `/Users/junheelee/Desktop/career_dashboard/data/model_improvement_gate_incremental_latest.json`
- `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_benchmark_incremental_latest.json`
- `/Users/junheelee/Desktop/career_dashboard/data/service_scope_shadow_guard_off_incremental_latest.json`

Fail-closed 검증:

```bash
python3 scripts/run_incremental_service_scope_pipeline.py \
  --skip-model-review \
  --model-review-output data/service_scope_model_review.json \
  --goldset data/service_scope_goldset_confirmed_v2.json \
  --apply
```

결과:

- status: `blocked`
- mode: `apply`
- gatePassed: `true`
- applied: `false`
- reason: `noncanonical_goldset`

즉 gate가 통과하더라도 canonical goldset이 아니면 기본적으로 운영 override를 수정하지 않는다.
