# 성능 개선 다음 단계

- 작성일: `2026-04-09`
- 우선순위: `정확도 > 속도 > 비용`

## 현재 최고 기준선

- 모델: `qwen2.5:7b`
- prompt profile: `field_aware_v3`
- 입력 전처리: `입력 정리 2차`
- 출력 후처리: `focus 재선정 + low 보정`
- 호출 전략: `batch-size 2 + suspicious single retry`

## 최신 확인 수치

- 기준 파일: [goldset_018_full14_v3_7b_batch2_hybrid_retry.json](/Users/junheelee/Desktop/career_dashboard/data/prompt_benchmarks/goldset_018_full14_v3_7b_batch2_hybrid_retry.json)
- `summaryExactRate`: `0.2857`
- `focusExactRate`: `0.7143`
- `avgKeywordF1`: `0.5816`
- `strictPassRate`: `0.2857`
- `lowMatchRate`: `1.0`

## 전체 재생성 결과

- 실행 상태: `완료`
- summary 존재: `197/210`
- focusLabel 존재: `196/210`
- low: `13/210`
- broad focus(raw): `31/210`
- accepted broad(raw): `28/210`
- bad broad(raw): `3/210`
- broad focus(board): `35/210`
- accepted broad(board): `35/210`
- bad broad(board): `0/210`
- 주된 focus(raw):
  - `RAG: 20`
  - `의료 데이터: 16`
  - `시스템 아키텍처: 8`
  - `하이브리드 인프라: 8`
  - `3D 공간 이해: 7`

- 해석:
  - coverage와 low 안정성은 약간 흔들렸지만, 확장 골드셋 정확도는 크게 올라갔다
  - raw broad focus 수치는 `31`이지만, 이 중 `28`은 허용 가능한 상위 taxonomy이고 실제 문제 broad는 `3`이다
  - board broad focus는 `35`로 보이지만 전부 `accepted broad`로 분류되고, 현재 `bad broad(board)`는 `0`이다
  - 지금은 `모델 교체`보다 `raw extractor를 board projection에 덜 의존하게 만드는 작업`이 우선이다

## 확장 골드셋 기준 최신 변화

- 기준 셋: `48건`
- 이전 current raw focus hit: `15/48`
- relabel guardrail 적용 후 focus hit: `23/48`
- focus precision v2 적용 후 focus hit: `39/48`
- 저장된 평가 리포트:
  - [goldset_022_store_expansion48_qwen7b_relabel_guardrail.json](/Users/junheelee/Desktop/career_dashboard/data/prompt_benchmarks/goldset_022_store_expansion48_qwen7b_relabel_guardrail.json)
  - [goldset_024_store_expansion48_qwen7b_focus_precision_v2.json](/Users/junheelee/Desktop/career_dashboard/data/prompt_benchmarks/goldset_024_store_expansion48_qwen7b_focus_precision_v2.json)
- 주요 수치:
  - `summaryExactRate`: `0.8333`
  - `focusExactRate`: `0.8125`
  - `avgKeywordF1`: `0.9087`
  - `strictPassRate`: `0.6667`
  - `qualityExactRate`: `1.0`
  - `lowMatchRate`: `1.0`
- 해석:
  - 이번 라운드는 prompt 변경 없이 `focus 선택 로직`과 `저신뢰 판정`만 고쳐서 얻은 개선이다
  - 확장 골드셋에서 `focusExactRate`는 `0.3125 -> 0.8125`, `strictPassRate`는 `0.2917 -> 0.6667`로 올랐다
  - 회귀는 `0건`이었다
  - 남은 focus miss는 `9건`이다
  - 따라서 이번 focus precision v2는 채택하고, 다음 병목은 `모델 교체`보다 `남은 9개 miss 축약`과 `broad metric 재정의`이다

## 이번 라운드 구조 전환

- 목적:
  - 같은 패턴의 미세 보정을 계속 붙이지 않고, `summary/focus/keywords` 아래에 구조화 신호층을 추가
- 반영:
  - `job_summaries.json` 각 항목에 `structuredSignals` 저장
  - `summary_board.json`이 이제 `structuredSignals`를 `signalFacets`, 연결 신호, 그래프 신호에 우선 사용
- 현재 커버리지:
  - `domainSignals`: `87`
  - `problemSignals`: `93`
  - `systemSignals`: `102`
  - `modelSignals`: `111`
  - `dataSignals`: `83`
  - `workflowSignals`: `122`
- 해석:
  - 이번 단계는 정확도 수치를 더 올리는 실험이 아니라, 다음부터 `raw extractor -> structured signal -> board projection` 구조로 갈 수 있게 저장 포맷을 바꾼 단계다
  - 즉 반복 패치 루프를 끊기 위한 구조 전환 1차다

## signal-first projection 적용 결과

- 방식:
  - `focusLabel`을 raw 결과에서 바로 쓰지 않고 `structuredSignals` 우선순위로 다시 투영
  - 우선순위: `problem > domain > data > system > workflow > model`
- 확장 골드셋 48건 기준 보드 평가:
  - 기준 파일: [goldset_025_store_expansion48_signal_first_projection.json](/Users/junheelee/Desktop/career_dashboard/data/prompt_benchmarks/goldset_025_store_expansion48_signal_first_projection.json)
  - `summaryExactRate`: `0.875`
  - `focusExactRate`: `0.9167`
  - `qualityExactRate`: `1.0`
  - `avgKeywordF1`: `0.8914`
  - `strictPassRate`: `0.8542`
- 해석:
  - 이번 단계는 현재까지의 가장 큰 성능 점프다
  - 이제 `focusLabel`은 raw current보다 `structured signal projection`을 중심으로 보는 것이 맞다
  - 즉 다음 병목은 `focusLabel` 대표값 자체보다 `accepted broad / bad broad` 지표 분리와 projection 유지 관리다

## store-level projection 동기화 시도

- 시도 내용:
  - `structuredSignals -> focusLabel` projection을 board뿐 아니라 `job_summaries` 저장층에도 직접 반영
- 결과:
  - board 기준 성능은 변화 없음
  - 대신 raw broad가 악화됨
  - 최신 진단:
    - `accepted broad(raw): 25/210`
    - `bad broad(raw): 9/210`
    - `accepted broad(board): 35/210`
    - `bad broad(board): 0/210`
- 해석:
  - 이 시도는 `raw extractor 개선`으로 보기에 부작용이 크고, 현재 단계에선 채택하지 않는다
  - 즉 다음은 저장층까지 강제로 맞추는 것이 아니라, `board projection을 canonical output`으로 보고 raw 수치는 진단용으로만 유지하는 방향이 맞다

## 이번 라운드 목표

1. 골드셋을 `14건 -> 40~60건`으로 확장하고 검수 시작
2. raw focus relabel 개선을 실제 재추론 벤치로 검증
3. 구조화 추출 schema를 실제 projection 규칙으로 연결
4. 그 후에만 Qwen/Gemma를 다시 비교

## 현재 준비 완료된 다음 단계 자산

- 구조화 신호 스키마 초안:
  - [structured_signal_schema.md](/Users/junheelee/Desktop/career_dashboard/docs/structured_signal_schema.md)
- structured signal 최소 검증 웨이브 `20건`:
  - [structured_signal_validation_wave_001.md](/Users/junheelee/Desktop/career_dashboard/docs/structured_signal_validation_wave_001.md)
  - [structured_signal_validation_wave_001.csv](/Users/junheelee/Desktop/career_dashboard/data/structured_signal_validation_wave_001.csv)
  - [structured_signal_validation_wave_001.xlsx](/Users/junheelee/Desktop/career_dashboard/data/structured_signal_validation_wave_001.xlsx)
  - provisional review:
    - [structured_signal_validation_review_001.json](/Users/junheelee/Desktop/career_dashboard/data/structured_signal_validation_review_001.json)
    - [structured_signal_validation_provisional_report_001.md](/Users/junheelee/Desktop/career_dashboard/docs/structured_signal_validation_provisional_report_001.md)
    - [structured_signal_validation_comparison_report_001.md](/Users/junheelee/Desktop/career_dashboard/docs/structured_signal_validation_comparison_report_001.md)
    - [structured_signal_validation_score_001.md](/Users/junheelee/Desktop/career_dashboard/docs/structured_signal_validation_score_001.md)
- 골드셋 확장 후보 `110건`:
  - [goldset_expansion_candidates.md](/Users/junheelee/Desktop/career_dashboard/docs/goldset_expansion_candidates.md)
- 골드셋 확장 웨이브 `48건`:
  - [goldset_expansion_wave_001.md](/Users/junheelee/Desktop/career_dashboard/docs/goldset_expansion_wave_001.md)
  - [goldset_expansion_wave_001.csv](/Users/junheelee/Desktop/career_dashboard/data/goldset_expansion_wave_001.csv)
- 골드셋 확장 의사결정 시트:
  - [goldset_expansion_decision_sheet_001.md](/Users/junheelee/Desktop/career_dashboard/docs/goldset_expansion_decision_sheet_001.md)
  - [goldset_expansion_decision_sheet_001.csv](/Users/junheelee/Desktop/career_dashboard/data/goldset_expansion_decision_sheet_001.csv)
  - [goldset_expansion_decision_sheet_001.xlsx](/Users/junheelee/Desktop/career_dashboard/data/goldset_expansion_decision_sheet_001.xlsx)
- 골드셋 확장 우선 확인 큐:
  - [goldset_expansion_confirm_queue_001.md](/Users/junheelee/Desktop/career_dashboard/docs/goldset_expansion_confirm_queue_001.md)
  - [goldset_expansion_confirm_queue_001.csv](/Users/junheelee/Desktop/career_dashboard/data/goldset_expansion_confirm_queue_001.csv)
  - [goldset_expansion_confirm_queue_001.xlsx](/Users/junheelee/Desktop/career_dashboard/data/goldset_expansion_confirm_queue_001.xlsx)
- 골드셋 확장 가정 반영 리포트:
  - [goldset_expansion_provisional_report_001.md](/Users/junheelee/Desktop/career_dashboard/docs/goldset_expansion_provisional_report_001.md)
- 골드셋 확장 비교 리포트:
  - [goldset_expansion_comparison_report_001.md](/Users/junheelee/Desktop/career_dashboard/docs/goldset_expansion_comparison_report_001.md)

## 바로 실행할 일

### 1. 재생성 후 품질 점검

- 확인 항목:
  - `summary 존재 수`
  - `focusLabel 존재 수`
  - `low 수`
  - broad focus 잔존 수
  - top focusLabel 분포

### 2. 골드셋 확장

- 추가 샘플링 기준:
  - broad focus 케이스
  - low 유지가 필요한 약한 공고
  - 도메인 특화 공고
  - 비슷한 스택인데 다른 focus가 필요한 공고

### 3. raw focus relabel guardrail 설계

- broad label이 대표값이 되는 조건을 더 엄격히 제한
- `domain/problem` 신호가 있으면 `컴퓨터 비전`, `클라우드`, `LLM`은 대표값에서 한 단계 뒤로 밀기
- `context_text`에서 직접 구체 힌트를 올리고, 이미 구체적인 focus는 덜 흔들리게 보호

### 4. structured signal 검증 시작

- 우선 `48건` 전체가 아니라 `20건` 최소 검증 웨이브부터 사용
- 확인 축:
  - `problemSignals`
  - `domainSignals`
  - `systemSignals`
- 그 결과로 `extractor miss`와 `projection miss`를 분리
- 현재 provisional 기준:
  - `resolved 20/20`
  - `suggested_signals 20`
  - `current_signals 0`
- 현재 score 기준:
  - `strictRate(current): 0.9`
  - `strictRate(suggested): 1.0`
  - `problemSignals exactRate(current -> suggested): 0.9 -> 1.0`
  - `systemSignals exactRate(current -> suggested): 0.95 -> 1.0`
  - `dataSignals / workflowSignals exactRate(suggested): 1.0 / 1.0`

## 이번 라운드에서 하지 않을 것

- prompt를 계속 추가로 꼬기
- Gemma를 기본 모델로 전환
- 파인튜닝 시작
- UI 기능 확장

## 모델 의사결정 게이트

현재는 아래를 모두 통과해야 다음 모델 결정으로 넘어갑니다.

1. 전체 재생성 완료
2. broad focus 분포 개선 확인
3. 골드셋 40건 이상 확보
4. core/incremental/expanded goldset에서 모두 비교

## Gemma 현재 판단

- 최신 비교 파일:
  - [goldset_019_full14_gemma31b_v3_hybrid_retry.json](/Users/junheelee/Desktop/career_dashboard/data/prompt_benchmarks/goldset_019_full14_gemma31b_v3_hybrid_retry.json)
  - [goldset_020_full14_gemma31b_gemma_focus_v1.json](/Users/junheelee/Desktop/career_dashboard/data/prompt_benchmarks/goldset_020_full14_gemma31b_gemma_focus_v1.json)
- 해석:
  - Gemma는 `keyword richness`는 강함
  - 하지만 `focusLabel` 대표성, `low 유지`는 아직 Qwen hybrid가 우세
  - 따라서 지금은 `후보 유지`, `기본 전환 보류`
