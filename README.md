# Hire Atlas

Google Sheet의 채용 공고를 읽어와, New Tech 채용시장의 흐름을 읽고 지원자와 업계 사이의 이해관계 간극을 좁혀가기 위한 인사이트 보드로 정리하는 프로토타입입니다.

## 제품 방향

- 이 프로젝트는 로컬 실험용으로 끝내지 않고, 차후 공식 서비스로 배포하는 것을 전제로 유지합니다.
- 이 서비스는 교육 업계를 위한 수직형 서비스라기보다, 교육 현장에서 사용하면서 기업 협업 가능성과 채용 신호를 해석하는 운영 도구를 목표로 합니다.
- 핵심 목적은 공고 데이터에서 앞으로 상정해볼 수 있는 기업 협업 프로젝트의 가능성을 미리 타진하고, 지원자와 업계 사이의 기대 차이와 이해관계적 이질감을 분석하는 데 있습니다.
- 운영 데이터 흐름은 `외부 자동화 증분 체계 -> 1차 Google Sheets -> 2차 검증 Sheets -> 본 프로젝트 검수/게시 보드 -> 배포`를 기준으로 합니다.
- 본 프로젝트의 핵심 역할은 1차 시트에 반영된 증분 결과를 2차 시트와 대조하고, 최종 서버 배포 전 추가 품질 검증/gate를 수행하는 것입니다.
- 모델 요약/보정과 회사군 재계산은 2차 검증 안에서 사용하는 하위 검증 수단이며, 1차 결과나 2차 승인 결과를 무단으로 덮어쓰지 않습니다.
- 앞으로 군집은 `직무명_표시`, `상세본문_분석용`뿐 아니라 `핵심기술`, `자격요건`, `주요업무`, `우대사항` 같은 다중 필드 신호까지 합쳐 더 큰 단위로 확장하는 것을 목표로 합니다.
- 페이지 구성 역시 현재 보드에 머무르지 않고, 보고서형 페이지와 AI 활용 페이지를 계속 추가해 축적한 자료의 활용 가치를 높이는 방향으로 확장합니다.
- 그래서 현재 보드 데이터도 단순 리스트가 아니라 `cluster -> signal -> posting` 그래프 형태로 확장 가능한 구조를 기본 전제로 유지합니다.
- 임시 UI 연출보다 중요한 기준은 `모델이 어떤 신호를 추출했고, 그 신호가 어떤 군집과 공고를 연결하는가`가 데이터 레벨에서 일관되게 남는 것입니다.
- 현재 화면도 이 방향에 맞춰 `상세본문_분석용 / 주요업무_분석용 / 자격요건_분석용 / 우대사항_분석용 / 핵심기술_분석용`의 5개 섹션을 한 페이지에 병렬로 보여주는 구조를 기본으로 사용합니다.

## 다음 목표

- 다음 구현 우선순위는 성능 개선입니다.
- 그 다음 핵심 인터랙션은 `각 섹션의 그룹 카드 클릭 -> 화면 오른쪽에서 공고 패널이 슬라이드 인` 되는 구조입니다.
- 이 오른쪽 패널은 새 페이지 이동이 아니라 같은 화면 안에서 열려야 하며, 사용자가 클릭한 그룹에 속한 공고들만 모아서 보여줘야 합니다.
- 즉 기본 보드는 왼쪽에 유지하고, 오른쪽에는 선택된 그룹의 공고 리스트와 세부 탐색 영역이 밀려 들어오는 방식으로 설계합니다.
- 품질·성능 개선의 전체 절차는 [docs/quality_execution_plan.md](/Users/junheelee/Desktop/career_dashboard/docs/quality_execution_plan.md)에 기록합니다.
- 현재 품질 개선의 비가역 원칙과 금지 방향은 [docs/model_quality_principles.md](/Users/junheelee/Desktop/career_dashboard/docs/model_quality_principles.md)에 기록합니다.
- 오버피팅을 막기 위한 일반화 기준은 [docs/generalization_guardrails.md](/Users/junheelee/Desktop/career_dashboard/docs/generalization_guardrails.md)에 기록합니다.
- 모델 튜닝 판단 우선순위는 [docs/model_tuning_decision_priority.md](/Users/junheelee/Desktop/career_dashboard/docs/model_tuning_decision_priority.md)에 기록합니다.
- 현재 상태 판정 리포트는 [docs/model_decision_report.md](/Users/junheelee/Desktop/career_dashboard/docs/model_decision_report.md)에서 확인합니다.
- 사람 검수 웨이브 운영 방법은 [docs/review_workflow.md](/Users/junheelee/Desktop/career_dashboard/docs/review_workflow.md)에 기록합니다.

## 그래프 기준

- 공고마다 `signalFacets`를 가집니다. 현재는 `role / keyword / tag / context`로 나누어 저장합니다.
- 군집마다 `signalFacets`를 가집니다. 이는 해당 군집에서 자주 반복된 신호를 facet 단위로 모은 결과입니다.
- 보드 응답에는 `graph`가 포함됩니다.
- `graph.nodes.clusters`: 군집 노드
- `graph.nodes.signals`: 추출된 신호 노드
- `graph.nodes.postings`: 공고 노드
- `graph.edges.clusterToSignal`: 군집과 신호의 연결
- `graph.edges.postingToSignal`: 공고와 신호의 연결

이 구조는 이후 `핵심기술 / 자격요건 / 주요업무 / 상세본문`을 모두 붙여도 같은 방식으로 확장할 수 있게 유지합니다.

## 현재 연결 상태

- Spreadsheet ID: `1bG-aT9L_N3SEPT04ZZZ-2jdRqW_agYhrqsn4fNanA5s`
- GID: `2026513640`
- 기본 시트: `master 탭`
- 2차 검증 Spreadsheet ID: `1z8nDYl0y7IDy4iXe1njrmdHzu0bv_6_zBC6gV7Vjqd0`
- 2차 검증 기본 GID: `0`
- 기본 서비스 계정 JSON 경로: `/Users/junheelee/Downloads/scraper-491619-a85f7518accf.json`
- 기본 서비스 계정 이메일: `sheets-automation@scraper-491619.iam.gserviceaccount.com`

서비스 계정이 시트에 공유되어 있으면 공개 CSV 없이도 Google Sheets API로 직접 읽습니다.

## 실행

1. 시트 동기화

```bash
python3 scripts/run_stage2_validation.py
python3 scripts/run_stage2_deploy_gate.py
python3 scripts/sync_sheet_snapshot.py --use-stage2-deploy
```

2. 앱 서버 실행

```bash
python3 server.py
```

3. 브라우저에서 열기

`http://127.0.0.1:4173`

## 화면에서 할 수 있는 일

- `시트 다시 읽기`: Google Sheets API로 `master 탭` 원문을 읽되, 2차 deploy gate 통과 CSV의 role/focus/keywords/summary를 덮어써 보드를 재생성. 모델 재추론은 기본 실행하지 않음
- `누락 정리`: 아직 요약과 키워드가 없는 공고만 Qwen으로 생성
- `전체 재정리`: 모든 공고 요약과 키워드를 다시 생성하고, 그 결과를 바탕으로 군집을 다시 계산

프롬프트가 바뀐 뒤 기존 결과를 새 기준으로 다시 맞추려면:

```bash
python3 scripts/generate_job_summaries.py \
  --base-url http://127.0.0.1:11434/v1 \
  --model qwen2.5:3b \
  --mode stale \
  --batch-size 4 \
  --temperature 0.0 \
  --prompt-profile field_aware_v3
```

증분 데이터 홀드아웃을 다시 만들려면:

```bash
python3 scripts/build_incremental_holdout.py --holdout-size 48
```

고정 평가셋과 증분 홀드아웃을 함께 비교하려면:

```bash
python3 scripts/run_benchmark_suite.py \
  --base-url http://127.0.0.1:11434/v1 \
  --model qwen2.5:3b \
  --prompt-profile field_aware_v3 \
  --compare-to baseline_v1 \
  --core-limit 12 \
  --incremental-limit 12 \
  --batch-size 4 \
  --temperature 0.0 \
  --experiment-id suite_001_smoke
```

현재 상태 기준으로 튜닝 판단 리포트를 다시 만들려면:

```bash
python3 scripts/build_model_decision_report.py
```

사람 검수용 리뷰 웨이브를 만들려면:

```bash
python3 scripts/build_review_wave.py
```

리뷰 웨이브를 CSV로 내보내려면:

```bash
python3 scripts/export_review_wave_csv.py
```

리뷰 우선순위 브리프를 만들려면:

```bash
python3 scripts/build_review_brief.py
```

상위 우선순위 항목의 수정 초안을 만들려면:

```bash
python3 scripts/build_review_suggestions.py
```

3b와 7b의 hard set 비교 리포트를 만들려면:

```bash
python3 scripts/build_stronger_model_comparison.py
```

CSV 검수 결과를 다시 가져오려면:

```bash
python3 scripts/import_review_wave_csv.py
```

검수 내용을 평가셋에 반영하려면:

```bash
python3 scripts/apply_review_wave.py
```

리뷰 정확도 리포트를 만들려면:

```bash
python3 scripts/score_review_accuracy.py
```

리뷰 웨이브를 `우선 확인 / low 유지 / 표현 차이 확인`으로 나누려면:

```bash
python3 scripts/build_review_triage.py
```

## Google Sheets 설정

환경변수로 덮어쓸 수 있습니다.

```bash
export GOOGLE_SHEETS_SPREADSHEET_ID="1bG-aT9L_N3SEPT04ZZZ-2jdRqW_agYhrqsn4fNanA5s"
export GOOGLE_SHEETS_GID="2026513640"
export GOOGLE_SHEETS_SHEET_TITLE="master 탭"
export GOOGLE_SERVICE_ACCOUNT_JSON="/path/to/service-account.json"
```

추가로 `GOOGLE_SHEETS_GID`도 지원합니다. `GOOGLE_SHEETS_SHEET_TITLE`이 있으면 제목 기준으로 우선 선택합니다.

## 모델 설정

- 기본 Base URL: `http://127.0.0.1:11434/v1`
- 현재 기준 Model: `qwen2.5:7b`
- 현재 기본 Prompt Profile: `field_aware_v3`
- 리뷰/검수용 제안 기본 모델: `qwen2.5:7b`
- 현재 운영 기준 전략: `batch-size 2 + suspicious single retry`

구조는 OpenAI 호환 endpoint 기준이라서, 나중에 배포된 모델 URL로 바꿔도 같은 흐름을 유지할 수 있습니다.

- 성능 개선 다음 단계 문서: [docs/performance_next_steps.md](/Users/junheelee/Desktop/career_dashboard/docs/performance_next_steps.md)
- 구조화 신호 추출 스키마 초안: [docs/structured_signal_schema.md](/Users/junheelee/Desktop/career_dashboard/docs/structured_signal_schema.md)
- 골드셋 확장 웨이브: [docs/goldset_expansion_wave_001.md](/Users/junheelee/Desktop/career_dashboard/docs/goldset_expansion_wave_001.md)

## 프롬프트 벤치

평가셋 기준으로 prompt profile을 비교할 수 있습니다.

```bash
python3 scripts/run_prompt_benchmark.py \
  --base-url http://127.0.0.1:11434/v1 \
  --model qwen2.5:3b \
  --prompt-profile field_aware_v3 \
  --compare-to baseline_v1 \
  --limit 12 \
  --batch-size 4 \
  --temperature 0.0 \
  --experiment-id experiment_002_smoke
```

- 결과 JSON은 `data/prompt_benchmarks/*.json`에 저장합니다.
- 실험 판단 로그는 [docs/prompt_experiment_log.md](/Users/junheelee/Desktop/career_dashboard/docs/prompt_experiment_log.md)에 누적합니다.

## 주요 파일

- `index.html`: 5개 분석 컬럼 군집 보드 UI
- `styles.css`: 운영툴 스타일 레이아웃
- `app.js`: 필터, 시트 동기화, 요약 실행, 5개 필드 군집 섹션 렌더링
- `server.py`: 정적 파일 + 시트 동기화 + 요약 생성 API
- `scripts/google_sheets_runtime.py`: 서비스 계정 JWT 생성 + Google Sheets API 호출
- `scripts/sync_sheet_snapshot.py`: 시트 데이터를 `jobs.json`으로 동기화
- `scripts/run_stage2_validation.py`: 1차 증분 시트와 2차 검증 시트를 대조하고 배포 전 품질 후보를 생성
- `scripts/run_stage2_deploy_gate.py`: 2차 승인/품질/stale 조건을 통과한 행만 배포 후보로 생성
- `scripts/build_summary_board.py`: 게시 보드용 데이터 생성
- `scripts/generate_job_summaries.py`: Qwen 배치 생성 CLI
- `scripts/run_prompt_benchmark.py`: 평가셋 기준 prompt profile 비교 벤치
- `scripts/run_benchmark_suite.py`: core eval + incremental holdout 동시 벤치
- `scripts/build_review_wave.py`: 문제 케이스와 control sample을 섞은 사람 검수 웨이브 생성
- `scripts/export_review_wave_csv.py`: 리뷰 웨이브를 스프레드시트용 CSV로 내보내기
- `scripts/build_review_brief.py`: 우선순위 리뷰 케이스 브리프 생성
- `scripts/build_review_suggestions.py`: 상위 리뷰 케이스에 대한 모델 수정 초안 생성
- `scripts/build_stronger_model_comparison.py`: hard set 기준 stronger-model 비교 리포트 생성
- `scripts/import_review_wave_csv.py`: CSV 검수 결과를 리뷰 웨이브 JSON으로 다시 가져오기
- `scripts/apply_review_wave.py`: 리뷰 웨이브 결과를 eval_set / incremental_eval_set에 반영
- `scripts/score_review_accuracy.py`: 사람 검수 결과를 바탕으로 실제 pass rate 계산
- `scripts/build_review_triage.py`: 리뷰 웨이브를 검수 우선순위별로 분류
- `scripts/build_model_decision_report.py`: 현재 상태 기준 모델 판단 리포트 생성
- `scripts/ai_runtime.py`: OpenAI 호환 모델 호출 공용 로직과 회사군 분류 생성
