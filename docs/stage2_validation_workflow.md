# Stage2 Validation Workflow

- 작성일: `2026-04-12`
- 1차 시트: `career_scraper_V2 / master 탭`
- 2차 시트: `career_scraper_V2_post / 시트1`
- 2차 Spreadsheet ID: `1z8nDYl0y7IDy4iXe1njrmdHzu0bv_6_zBC6gV7Vjqd0`
- 상태: `1차-2차 대조 스크립트 구현 / 2차 시트 후보 187건 적재 완료`

## 운영 역할

본 프로젝트는 외부 자동화 증분 체계가 만든 1차 검수 완료 시트를 그대로 배포하지 않는다.

역할은 아래처럼 분리한다.

- 1차 시트: 외부 자동화 증분 체계의 검수 완료 결과
- 2차 시트: 본 프로젝트가 수행하는 최종 서버 배포 전 추가 품질 검증 결과
- 로컬 리포트: 1차와 2차의 diff, stale 여부, 품질 이슈, 배포 전 blocker 기록
- 최종 배포: 2차 검증과 gate를 통과한 후보만 반영

## 기본 원칙

- 1차 시트 결과는 원천 입력으로 보존한다.
- 2차 검증은 1차 결과를 덮어쓰지 않고 별도 결과로 남긴다.
- `공고키 + 변경해시`가 같을 때만 2차 검증 결과를 최신으로 인정한다.
- 1차 변경해시가 바뀌면 기존 2차 검증은 `stage2_stale`로 본다.
- 모델 재처리와 하네스 검증은 2차 검증의 하위 검증 수단이며, 운영 반영은 별도 승인/gate 이후에만 가능하다.
- CSS/UI 변경과 데이터 검증은 분리한다.

## 구현된 명령

```bash
python3 scripts/run_stage2_validation.py
```

기본 동작:

- 1차 시트와 2차 시트를 읽는다.
- `공고키 + 변경해시`로 대조한다.
- 신규/변경/stale/품질 이슈를 분류한다.
- 운영 JSON과 1차 시트는 수정하지 않는다.
- 결과를 아래 파일로 쓴다.

산출물:

- `/Users/junheelee/Desktop/career_dashboard/data/stage2_validation_latest.json`
- `/Users/junheelee/Desktop/career_dashboard/data/stage2_validation_candidates_latest.csv`
- `/Users/junheelee/Desktop/career_dashboard/docs/stage2_validation_latest.md`

배포 gate:

```bash
python3 scripts/run_stage2_deploy_gate.py
```

기본 동작:

- 2차 검증 결과를 읽는다.
- 승인되지 않은 행, 품질 이슈, stale, missing, needs_review가 있으면 `blocked`로 종료한다.
- 후보 행의 `공고키/변경해시` 누락, 중복 `공고키`, 배포 필수 필드 누락, 허용 밖 직군이 있으면 `blocked`로 종료한다.
- 통과한 행만 `/Users/junheelee/Desktop/career_dashboard/data/stage2_deploy_candidates_latest.csv`에 쓴다.
- 운영 JSON과 1차/2차 시트는 수정하지 않는다.

검수 triage 리포트:

```bash
python3 scripts/build_stage2_quality_triage.py
```

기본 동작:

- 2차 검증 후보 CSV를 읽어 `2차 동기화`, `직군/초점 재분류`, `키워드/초점 추출 실패`, `비차단 참고 신호`로 묶는다.
- 사람이 먼저 봐야 할 검수 액션과 대표 예시를 기록한다.
- 운영 JSON과 1차/2차 시트는 수정하지 않는다.

산출물:

- `/Users/junheelee/Desktop/career_dashboard/data/stage2_quality_triage_latest.json`
- `/Users/junheelee/Desktop/career_dashboard/docs/stage2_quality_triage_latest.md`

2차 보정 후보 생성:

```bash
python3 scripts/build_stage2_repair_candidates.py
```

기본 동작:

- 2차 검증에서 `needs_review`로 잡힌 행만 읽는다.
- 현재 1차 시트를 다시 읽어 원본 맥락을 붙인다.
- role/focus/keywords/summary 보정 후보를 별도 로컬 산출물로 만든다.
- 운영 JSON과 1차/2차 시트는 수정하지 않는다.

산출물:

- `/Users/junheelee/Desktop/career_dashboard/data/stage2_repair_candidates_latest.json`
- `/Users/junheelee/Desktop/career_dashboard/data/stage2_repair_candidates_latest.csv`
- `/Users/junheelee/Desktop/career_dashboard/docs/stage2_repair_candidates_latest.md`

2차 시트 적재:

```bash
python3 scripts/run_stage2_validation.py --write-stage2
```

안전장치:

- 2차 시트가 이미 행을 가지고 있으면 기본적으로 덮어쓰지 않는다.
- 덮어쓰려면 `--allow-overwrite-stage2`를 명시해야 한다.
- 2차 시트 적재는 쓰기 권한 확인 후에만 수행한다.

## 현재 최신 실행 결과

- stage1Rows: `187`
- stage2Rows: `187`
- candidateRows: `187`
- stateCounts.stage2_approved: `187`
- stateCounts.stage2_pending: `0`
- stateCounts.quality_issue: `0`
- stateCounts.stage2_stale: `0`
- latest stage2 write: `187건 전체 승인 후보 반영 완료`
- deploy gate: `passed`
- deployableRows: `187`
- blockingIssueCount: `0`

남은 비차단 참고 이슈 카운트:

- `business_context_in_ai_role`: `10` (info, 배포 차단 아님)
- `focus_diff`: `34` (info, 1차/2차 차이 기록)
- `summary_diff`: `36` (info, 1차/2차 차이 기록)
- `role_diff`: `10` (info, 1차/2차 차이 기록)
- `keywords_diff`: `24` (info, 1차/2차 차이 기록)
- `data_engineering_ai_context`: `4` (info, 배포 차단 아님)
- `data_engineering_ai_title_context`: `1` (info, 배포 차단 아님)
- `summary_too_short`: `3` (low, 단독 배포 차단 아님)

2026-04-12 조정:

- `business_signal_in_ai_role`처럼 상세본문 전체에서 `지표/대시보드/BI`가 보인다는 이유만으로 AI 직군을 차단하지 않는다.
- 차단은 제목/초점/요약에서 해당 신호가 지배적인 경우로 제한한다.
- `Data Analytics Engineer`, `Data Engineer`, `Data Platform`, `BI/DW`처럼 제목 자체가 데이터 엔지니어링/분석가형이면 `data_engineering_as_ai_role`로 차단한다.
- 단, `Robotics Simulation & Data Engineer`처럼 제목 안에 AI/딥테크 앵커가 함께 있으면 `data_engineering_ai_title_review` medium으로 낮춰 사람이 재검증한다.
- AI Platform, AI Agent, LLM, ML Researcher, Model Serving처럼 AI 앵커가 명확한 공고는 비즈니스/지표 문맥이 본문에 있어도 `business_context_in_ai_role` info로만 기록한다.
- `stage2_stale`은 1차와 2차의 `변경해시`가 달라졌다는 뜻이다. 이 상태에서는 2차가 이미 187행을 갖고 있어도 최신 1차 증분을 다시 반영하기 전까지 배포할 수 없다.
- 2026-04-12 18시대 확인된 `stage2_stale=3`은 실제 해시 불일치가 아니라 1차 시트 헤더가 `job_key/change_hash/job_role`로 바뀐 것을 검증기가 읽지 못해 생긴 오판이었다. 헤더 호환층 보강 후 stale은 `0`으로 해소됐다.
- 2026-04-12 19시대 추가 확인: `dominance_text`에 기존 `role` 문자열을 넣으면 이미 `인공지능 엔지니어`로 붙은 행이 스스로 AI 신호를 만족하는 자기합리화가 생긴다. 검증기에서 role 문자열을 AI 지배 신호에서 제거했다.
- `Data Analytics Engineer`, `Analytics Engineer`, `BI/DW`, `Data Analyst` 제목은 AI 세부 문맥이 있더라도 별도 blocking 규칙인 `analytics_engineering_as_ai_role`로 먼저 잡는다.
- `apply_stage2_repairs_to_sheet.py`는 더 이상 repair 대상이 아닌 행을 1차 값으로 되돌리지 않는다. 현재 2차 값을 carry-forward한 뒤 신규 repair만 덮어쓴다.
- `검수완료`, `검수필요`는 키워드/초점 noise로 간주한다. apply 단계에서도 빈 초점을 임시 문자열로 채우지 않는다.
- `sync_sheet_snapshot.py --use-stage2-deploy`는 1차 원문 전체를 유지하면서 2차 gate 통과 CSV의 role/focus/keywords/summary만 덮어쓴다.
- `summary_board.json`은 stage2 deploy payload일 때 예전 service-scope exclude/review와 role-group classifier가 2차 승인값을 다시 숨기거나 덮어쓰지 않도록 2차 role/focus/keywords를 우선한다.
- 최신 triage 기준: `stage2_sync=0`, `role_mismatch=0`, `signal_extraction=0`, `non_blocking_context=48`.
- 최신 repair 기준: 마지막 루프에서 noise focus 6건을 수리했고 `clearsBlockingIssues=6`, `unresolvedAfterRepair=0`.
- 운영 JSON 반영 기준: `/Users/junheelee/Desktop/career_dashboard/data/jobs.json`은 187건, `/Users/junheelee/Desktop/career_dashboard/data/summary_board.json`도 전체 187건을 표시한다.
- 화면 보드 최신 수치: `전체=187`, `인공지능 엔지니어=142`, `인공지능 리서처=23`, `데이터 사이언티스트=8`, `데이터 분석가=14`, `serviceScopeFilteredOutJobs=0`, `displaySummaryCoverage=187`.

## 다음 기준

이제 아래 순서로 운영한다.

1. 외부 자동화가 1차 시트 증분 결과 생성
2. `run_stage2_validation.py` 실행
3. 2차 시트에서 신규/stale/high priority 행 검수
4. `run_stage2_deploy_gate.py`로 승인/품질/stale gate 실행
5. 하네스와 모델 품질 gate 실행
6. 통과 결과만 최종 서버 배포 후보로 승격
