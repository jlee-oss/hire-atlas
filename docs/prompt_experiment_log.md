# Prompt Experiment Log

이 문서는 prompt 변경 전후를 같은 평가셋으로 비교하기 위한 실험 로그 템플릿입니다.

## 기록 규칙

- 하나의 prompt 변경마다 한 섹션씩 추가합니다.
- 반드시 같은 `data/eval_set.json`을 기준으로 비교합니다.
- 결과는 인상평이 아니라 지표와 실패 사례 중심으로 적습니다.

## 기본 항목

- 날짜
- 모델
- base URL
- input fields
- output schema
- prompt 변경 요약
- 금지어 발생률
- 문장형 keyword 비율
- 그룹 제목 신뢰도
- low 비율
- 대표 실패 사례
- 채택 여부

---

## Experiment 001

- 날짜: 2026-04-07
- 모델: `qwen2.5:3b`
- base URL: `http://127.0.0.1:11434/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`
- prompt 변경 요약:
  - `baseline_v1` 대비 `field_aware_v2` 추가
  - detail/tasks 우선 읽기
  - 학력/경력/제품/서비스 계열 negative instruction 강화
  - `focusLabel`과 `keywords`를 그룹 seed 전제로 제한

### Metrics

- 평가셋: `data/eval_set.json` 상위 12건 스모크
- 샘플링 온도: `0.1`
- `baseline_v1`
  - 금지어 발생률: `0.00%`
  - 문장형 keyword 비율: `0.00%`
  - low 비율: `33.33%`
  - usable item 비율: `33.33%`
  - empty focusLabel 비율: `66.67%`
- `field_aware_v2`
  - 금지어 발생률: `0.00%`
  - 문장형 keyword 비율: `0.00%`
  - low 비율: `33.33%`
  - usable item 비율: `0.00%`
  - empty focusLabel 비율: `100.00%`

### 실패 사례

- 사례 1: `네이버 / [네이버랩스] Generative AI Research Engineer`
  - `field_aware_v2`에서 `quality=low`, `summary=""`, `focusLabel=""`로 과도하게 비워짐
- 사례 2: `노타 / [NetsPresso] Senior Edge AI Engineer`
  - `baseline_v1`, `field_aware_v2` 모두 low로 떨어졌지만 기존 current 값은 `모델 변환/최적화` 방향 신호를 일부 보유
- 사례 3: `field_aware_v2`
  - focusLabel을 거의 살리지 못해 그룹 seed로 쓰기 어려움

### 판단

- 채택 여부: `미채택`
- 다음 수정 포인트:
  - `focusLabel`을 low가 아닌 경우 비우지 않도록 프롬프트 수정
  - 역할명 반복 summary 금지 강화
  - 너무 엄격해서 비워버리는 경향을 완화

---

## Experiment 002

- 날짜: 2026-04-07
- 모델: `qwen2.5:3b`
- base URL: `http://127.0.0.1:11434/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`
- prompt 변경 요약:
  - `field_aware_v3` 추가
  - `focusLabel`은 low가 아닌 경우 반드시 채우도록 지시
  - focusLabel은 keyword 중 핵심 1개를 재사용 가능하도록 허용
  - 역할명만 반복하는 summary 금지 강화
  - 벤치 온도를 `0.0`으로 고정해 비교 흔들림 축소

### Metrics

- 평가셋: `data/eval_set.json` 상위 12건 스모크
- 샘플링 온도: `0.0`
- `baseline_v1`
  - 금지어 발생률: `0.00%`
  - 문장형 keyword 비율: `0.00%`
  - low 비율: `33.33%`
  - usable item 비율: `0.00%`
  - empty focusLabel 비율: `91.67%`
- `field_aware_v3`
  - 금지어 발생률: `0.00%`
  - 문장형 keyword 비율: `0.00%`
  - low 비율: `25.00%`
  - usable item 비율: `16.67%`
  - empty focusLabel 비율: `83.33%`

### 실패 사례

- 사례 1: `뷰노 / (전문연지원가능) AI Research Engineer / Scientist`
  - `field_aware_v3`에서도 여전히 low 처리. 신호 처리/의료 데이터 계열을 더 잘 살리는 후속 수정 필요
- 사례 2: `네이버 / [네이버랩스] Generative AI Research Engineer`
  - summary와 keywords는 살아났지만 focusLabel은 여전히 비어 있음
- 사례 3: `노타 / [Solution AI-Industry] Business Developer`
  - `사업`처럼 너무 넓은 keyword만 남아 도메인/문제 맥락이 충분히 포착되지 않음

### 판단

- 채택 여부: `v2 대비 조건부 채택`
- 다음 수정 포인트:
  - focusLabel 전용 후보 집합을 keyword와 별도로 유도
  - `사업`, `소프트웨어`, `데이터 처리` 같은 넓은 표현을 더 좁히기
  - summary 길이 및 서술형 표현을 후처리로 한 번 더 다듬기

---

## Experiment 003

- 날짜: 2026-04-07
- 모델: `qwen2.5:3b`
- base URL: `http://127.0.0.1:11434/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`
- prompt 변경 요약:
  - `focusLabel` 후처리 fallback 추가
  - keyword가 있으면 대표 라벨을 자동 선택
  - 비교 대상: `baseline_v1`, `field_aware_v3`, `field_aware_v4`
  - 샘플링 온도: `0.0`

### Metrics

- 평가셋: `data/eval_set.json` 상위 12건 스모크
- `baseline_v1`
  - usable item 비율: `33.33%`
  - low 비율: `33.33%`
  - empty focusLabel 비율: `41.67%`
- `field_aware_v3`
  - usable item 비율: `58.33%`
  - low 비율: `25.00%`
  - empty focusLabel 비율: `25.00%`
- `field_aware_v4`
  - usable item 비율: `8.33%`
  - low 비율: `50.00%`
  - empty focusLabel 비율: `50.00%`

### 실패 사례

- 사례 1: `field_aware_v4`
  - summary 명사구 제약이 너무 세서 오히려 빈 summary와 low 판정이 늘어남
- 사례 2: `field_aware_v3`
  - `PyTorch`, `TensorFlow` 같은 프레임워크가 도메인 신호보다 앞서 대표 라벨로 선택되는 경우가 남음
- 사례 3: `baseline_v1`
  - focusLabel은 후처리로 일부 복구되지만 low 공고 비중 자체는 줄지 않음

### 판단

- 채택 여부: `field_aware_v3 채택, field_aware_v4 미채택`
- 다음 수정 포인트:
  - summary에 직접 드러난 도메인 신호를 focusLabel보다 우선 반영
  - 키워드 표기를 canonical form으로 정리

---

## Experiment 004

- 날짜: 2026-04-07
- 모델: `qwen2.5:3b`
- base URL: `http://127.0.0.1:11434/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`
- prompt 변경 요약:
  - term canonicalization 추가: `엘엘엠 -> LLM`, `파이토치 -> PyTorch`, `오엔엔엑스 -> ONNX`
  - summary 힌트 기반 focusLabel 보강 추가
  - 예: summary에 `자율주행`, `ONNX`, `고객 관계 관리`가 직접 있으면 framework보다 우선 선택

### Metrics

- 평가셋: `data/eval_set.json` 상위 12건 스모크
- 샘플링 온도: `0.0`
- `baseline_v1`
  - usable item 비율: `33.33%`
  - low 비율: `33.33%`
  - empty focusLabel 비율: `41.67%`
- `field_aware_v3`
  - usable item 비율: `58.33%`
  - low 비율: `25.00%`
  - empty focusLabel 비율: `25.00%`

### 실패 사례

- 사례 1: `뷰노 / (전문연지원가능) AI Research Engineer / Scientist`
  - 여전히 low. 생체신호/의료 쪽 약한 원문은 별도 prompt 보강이 필요
- 사례 2: `모빌린트 / SDK Field Engineer`
  - `소프트웨어 개발`처럼 아직 넓은 label이 남을 수 있음
- 사례 3: `노타 / [Solution AI-Industry] Business Developer`
  - `사업 개발`은 비어있는 것보단 낫지만 프로젝트/도메인 맥락이 더 필요함

### 판단

- 채택 여부: `현재 기본 프로필로 field_aware_v3 채택`
- 다음 수정 포인트:
  - `생체신호`, `의료기기`, `CRM`, `SDK` 등 희소 도메인 alias 추가
  - focusLabel 전용 허용어 사전을 더 세밀하게 좁히기

---

## Experiment 005

- 날짜: 2026-04-08
- 모델: `qwen2.5:3b`
- base URL: `http://127.0.0.1:11434/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`
- prompt 변경 요약:
  - 리뷰 골드셋 14건을 기준으로 `field_aware_v5`, `field_aware_v6`, `field_aware_v7`를 추가
  - `low` 판정 강화, 게시용 summary 예시 강화, focusLabel 우선순위 명시
  - 지시문을 길게 늘린 버전(`v5`)과 예시 중심 축약 버전(`v6`, `v7`)을 비교

### Metrics

- 평가셋: `data/review_goldset_seed_001.json`
- 샘플링 온도: `0.0`
- `goldset_003_smoke2_v5_vs_v3_3b`
  - `field_aware_v3`: `summary 50.00% / focus 50.00% / avgKeywordF1 50.00% / strict 50.00% / lowMatch 100.00%`
  - `field_aware_v5`: `summary 0.00% / focus 0.00% / avgKeywordF1 12.50% / strict 0.00% / lowMatch 0.00%`
- `goldset_005_smoke4_v6_vs_v3_3b`
  - `field_aware_v3`: `summary 25.00% / focus 25.00% / avgKeywordF1 25.00% / strict 25.00% / lowMatch 100.00%`
  - `field_aware_v6`: `summary 25.00% / focus 25.00% / avgKeywordF1 25.00% / strict 25.00% / lowMatch 100.00%`
- `goldset_006_smoke4_v7_vs_v3_3b`
  - `field_aware_v3`: `summary 25.00% / focus 25.00% / avgKeywordF1 25.00% / strict 25.00% / lowMatch 100.00%`
  - `field_aware_v7`: `summary 25.00% / focus 25.00% / avgKeywordF1 25.00% / strict 25.00% / lowMatch 100.00%`
  - 단, `qualityExactRate`는 `field_aware_v7`가 `-0.50` 악화

### 실패 사례

- 사례 1: `field_aware_v5`
  - `한국뇌연구원 실증지원사업단` low는 맞췄지만, `뷰노`, `쿠팡`, `네이버랩스`까지 low로 과도하게 비워버림
- 사례 2: `field_aware_v6`
  - 3b에서는 `v3`보다 좋아지지 않았고, summary 개선보다 keyword/focus 안정화가 부족
- 사례 3: `field_aware_v7`
  - 예시를 더 넣어도 3b는 `low` 판정을 과도하게 적용하며 `qualityExactRate`를 악화시킴

### 판단

- 채택 여부: `v5/v6/v7 모두 미채택`
- 다음 수정 포인트:
  - 프롬프트 확장보다 입력 압축 품질 개선이 더 중요함
  - 긴 `detailBody`를 업무 문장과 요건 문장으로 더 잘 분리해야 함

---

## Experiment 006

- 날짜: 2026-04-08
- 모델: `qwen2.5:3b`, `qwen2.5:7b`
- base URL: `http://127.0.0.1:11434/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`
- 변경 요약:
  - `clean_detail_for_summary()`를 개선
  - 긴 `detailBody`를 문장 단위로 더 잘 분리
  - `해외여행`, `병역`, `관련 분야`, `채용하고 싶은 사람`, `N년 이상` 같은 요건/안내 문장을 별도로 분리
  - `detailBody`와 `tasks`가 섞인 긴 문단에서 업무 신호만 남기도록 입력 정리 강화

### Metrics

- 평가셋: `data/review_goldset_seed_001.json`
- 샘플링 온도: `0.0`
- `goldset_008_smoke4_v3_3b_after_input_cleanup`
  - `field_aware_v3`: `summary 25.00% / focus 50.00% / quality 75.00% / avgKeywordF1 33.33% / strict 25.00% / lowMatch 100.00%`
  - 입력 정리 전 스모크(`goldset_005`) 대비 `focusExactRate +25pt`, `avgKeywordF1 +8.33pt`
- `goldset_007_smoke4_v3_vs_v6_7b`
  - `field_aware_v6`: `summary 50.00% / focus 50.00% / avgKeywordF1 32.14% / strict 25.00% / lowMatch 100.00%`
  - `field_aware_v3`: `summary 25.00% / focus 50.00% / avgKeywordF1 45.54% / strict 25.00% / lowMatch 100.00%`
- `goldset_009_full14_v3_vs_v6_3b_after_input_cleanup`
  - `field_aware_v6`: `summary 21.43% / focus 21.43% / avgKeywordF1 21.43% / strict 21.43% / lowMatch 75.00%`
  - `field_aware_v3`: `summary 28.57% / focus 42.86% / avgKeywordF1 34.33% / strict 28.57% / lowMatch 100.00%`
- `goldset_010_full14_v3_7b_after_input_cleanup`
  - `field_aware_v3`: `summary 28.57% / focus 50.00% / avgKeywordF1 45.92% / strict 28.57% / lowMatch 100.00%`
  - 같은 입력/프롬프트에서 3b 대비 `focusExactRate +7.14pt`, `avgKeywordF1 +11.59pt`

### 실패 사례

- 사례 1: `뷰노`
  - 입력 정리 후에도 3b는 여전히 `low`로 떨어짐
  - 같은 케이스에서 7b + `v6`는 summary/focus는 맞췄지만 keyword가 충분히 구체적이지 않음
- 사례 2: `쿠팡`
  - 3b는 `사용자 퍼널`, `코호트 분석` 쪽으로 과도하게 좁혀 `그로스 마케팅/CRM/리텐션` 축을 놓침
- 사례 3: `네이버랩스`
  - 3b는 `컴퓨터 비전`까지는 맞추지만 summary와 keyword가 여전히 추상적
  - 7b는 keyword 축이 더 풍부해지지만 summary 자체는 여전히 게시용 문구보다 연구 일반론에 가까운 경우가 남음

### 판단

- 채택 여부: `입력 정리 채택`, `현재 3b 기본 프로필은 field_aware_v3 유지`
- 다음 수정 포인트:
  - 3b 프롬프트 추가 튜닝보다 입력 정리/소스 정제 확대가 우선
  - 7b는 `grouping signal` 기준으로 3b보다 우세하므로, 이후 비교 기준 모델로 쓸 가치가 있음
  - summary 전용 제약은 별도 개선이 필요함

---

## Experiment 007

- 날짜: 2026-04-08
- 모델: `qwen2.5:7b`
- base URL: `http://127.0.0.1:11434/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`
- 변경 요약:
  - `tasks / requirements / preferred / skills` 정제 2차 적용
  - inline canonicalization 강화 (`VLM`, `NLP`, `RAG`, `A/B 테스트`, `EMR`, `심전도`, `BigQuery` 등)
  - 입력 기반 composite focus 후보 합성 추가
  - `batch contamination` 확인 후 `batch 2 + suspicious single retry` 하이브리드 재시도 추가

### Metrics

- 평가셋: `data/review_goldset_seed_001.json`
- 샘플링 온도: `0.0`
- `goldset_014_full14_v3_7b_input_cleanup_v2`
  - `field_aware_v3`: `summary 21.43% / focus 50.00% / avgKeywordF1 48.98% / strict 21.43% / lowMatch 75.00%`
  - 입력 정리만 강하게 적용하면 keyword는 좋아지지만 low 안정성이 흔들림
- `goldset_016_full14_v3_7b_input_cleanup_v2_postprocess_fix`
  - `field_aware_v3`: `summary 21.43% / focus 57.14% / avgKeywordF1 48.98% / strict 21.43% / lowMatch 75.00%`
  - postprocess로 focus는 개선되지만 batch contamination 문제는 남음
- `goldset_017_full14_v3_7b_batch1`
  - `field_aware_v3`: `summary 28.57% / focus 64.29% / avgKeywordF1 53.74% / strict 28.57% / lowMatch 100.00%`
  - 단건 호출이 batch contamination을 제거하며 품질을 크게 끌어올림
- `goldset_018_full14_v3_7b_batch2_hybrid_retry`
  - `field_aware_v3`: `summary 28.57% / focus 71.43% / avgKeywordF1 58.16% / strict 28.57% / lowMatch 100.00%`
  - 현재까지 검증된 최고 조합

### 실패 사례

- 사례 1: `Talent Pool (R&D)`
  - 단건 호출에서는 low가 안정적이지만, 배치 호출에서는 옆 공고 신호를 먹고 medium으로 올라오는 contamination이 확인됨
- 사례 2: `메디컬에이아이`, `뷰노`
  - 입력 정리 후에도 `의료`처럼 넓은 focus로 묶이는 경향이 남아 있어 composite focus 후보가 계속 필요함
- 사례 3: `쿠팡`, `당근`
  - 제품 성장/그로스 계열은 summary보다 focus와 keyword는 좋아졌지만 summary exact는 여전히 높지 않음

### 판단

- 채택 여부: `batch 2 + hybrid retry 채택`
- 현재 최선 조합:
  - `qwen2.5:7b`
  - `field_aware_v3`
  - `입력 정리 2차`
  - `postprocess`
  - `batch-size 2 + suspicious single retry`
- 다음 수정 포인트:
  - 프롬프트 추가 확장보다 `summary schema 재정의`가 우선
  - 전체 210건 재생성은 위 조합으로 진행

---

## Experiment 008

- 날짜: 2026-04-08
- 모델: `gemma-4-31b`
- base URL: `https://api.vibemakers.kr/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`
- 변경 요약:
  - Gemma를 최신 입력 정리 2차 + postprocess + hybrid retry 전략 위에서 재평가
  - 이후 Gemma 전용 focus 지시 프로필 `gemma_focus_v1` 추가 비교

### Metrics

- 평가셋: `data/review_goldset_seed_001.json`
- 샘플링 온도: `0.0`
- `goldset_013_full14_gemma31b_v3`
  - `field_aware_v3`: `summary 28.57% / focus 35.71% / avgKeywordF1 59.16% / strict 28.57% / lowMatch 100.00%`
  - 초기 Gemma 비교. keyword는 좋지만 focusLabel이 넓고 흔들림
- `goldset_019_full14_gemma31b_v3_hybrid_retry`
  - `field_aware_v3`: `summary 28.57% / focus 57.14% / avgKeywordF1 55.47% / strict 28.57% / lowMatch 100.00%`
  - 최신 파이프라인 위에서는 Gemma가 크게 개선됨
- `goldset_020_full14_gemma31b_gemma_focus_v1`
  - `field_aware_v3`: `summary 28.57% / focus 57.14% / avgKeywordF1 55.47% / strict 28.57% / lowMatch 100.00%`
  - `gemma_focus_v1`: `summary 21.43% / focus 57.14% / avgKeywordF1 60.75% / strict 21.43% / lowMatch 75.00%`
  - Gemma 전용 지시는 keyword는 늘었지만 low 안정성을 악화시켜 미채택

### 실패 사례

- 사례 1: `워트인텔리전스`
  - Gemma는 `RAG`보다 `LLM`을 대표 라벨로 잡으려는 경향이 남음
- 사례 2: `노타 [Solution]`
  - `컴퓨터 비전`보다 `클라우드`로 기울며 시스템 축을 과대평가
- 사례 3: `Talent Pool / 전문연구요원`
  - Gemma 전용 지시를 강하게 걸면 오히려 low 케이스에서도 plausible한 내용을 채워 넣는 경향이 생김

### 판단

- 채택 여부:
  - `Gemma + 최신 hybrid retry`: 유효한 재평가 결과
  - `gemma_focus_v1`: 미채택
- 해석:
  - Gemma는 keyword 확장과 서술 풍부화는 강함
  - 하지만 대표 focusLabel을 고를 때 도메인/문제보다 시스템/스택을 과대선택하는 경향이 남음
  - 프롬프트만 더 강하게 주면 low 케이스에서 과생성(overfill)이 발생함

---

## Experiment 009

- 날짜: 2026-04-10
- 모델: `gemma-4-31b`
- base URL: `https://api.vibemakers.kr/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`, `structuredSignals`
- 변경 요약:
  - `raw 문장 -> 라벨` 누수를 줄인 최신 구조 위에서 `field_aware_v9`를 `field_aware_v3`와 release gate로 직접 비교
  - 목적: `Growth / Vision / Medical / Digital Agriculture` 경계 품질을 올리되, 증분 일반화가 깨지지 않는지 확인

### Metrics

- 게이트 리포트: `data/release_gates/release_gate_field_aware_v9_20260410b.json`
- `field_aware_v3`
  - core focus exact: `85.71%`
  - core avg keyword F1: `59.57%`
  - incremental usable: `92.50%`
  - incremental low: `7.50%`
  - incremental banned keyword: `0.00%`
  - incremental empty focus: `7.50%`
- `field_aware_v9`
  - core focus exact: `85.71%`
  - core avg keyword F1: `64.52%`
  - incremental usable: `90.00%`
  - incremental low: `10.00%`
  - incremental banned keyword: `3.01%`
  - incremental empty focus: `10.00%`

### 실패 사례

- 사례 1: `모빌린트 / SDK Field Engineer`
  - `field_aware_v9`가 `기술 문서`를 keyword로 올려 banned keyword를 유발
- 사례 2: `안랩 / AI Agent 프론트엔드 개발`
  - `field_aware_v9`가 `웹 서비스 개발`처럼 너무 넓은 keyword를 생성
- 사례 3: `여기어때 / UX Designer`
  - `field_aware_v9`가 UX 직군을 `제품 성장 분석`으로 과하게 끌어당겨 incremental 일반화를 해침
- 사례 4: `인터엑스 / Agent AI PM`
  - `field_aware_v9`가 `기술 컨설팅` 같은 넓은 표현을 keyword로 남김

### 판단

- 채택 여부: `미채택`
- 해석:
  - `field_aware_v9`는 core hard case에서 keyword 품질을 올린다.
  - 하지만 incremental 데이터에서는 `웹 서비스 개발`, `기술 문서`, `기술 컨설팅` 같은 넓은 일반 표현이 다시 살아나며 generalization이 악화된다.
  - 즉 `core 개선`만 보고 승격하면 안 되고, 다음 라운드는 `core gain 유지 + incremental generic keyword 억제`를 동시에 달성해야 한다.

---

## Experiment 010

- 날짜: 2026-04-10
- 모델: `gemma-4-31b`
- base URL: `https://api.vibemakers.kr/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`
- 변경 요약:
  - 현재 배포 챔피언 `field_aware_v3`를 최신 코드와 최신 증분 데이터 기준으로 다시 release gate에 태움
  - 목적: 오래된 gate 포인터를 걷어내고, 지금 실제 운영 상태의 기준선을 다시 고정

### Metrics

- 게이트 리포트: `data/release_gates/release_gate_field_aware_v3_refresh_20260410.json`
- `field_aware_v3`
  - core focus exact: `78.57%`
  - core avg keyword F1: `59.57%`
  - incremental usable: `96.97%`
  - incremental low: `3.03%`
  - incremental banned keyword: `0.00%`
  - incremental empty focus: `3.03%`

### 판단

- 채택 여부: `기준선 갱신`
- 해석:
  - 이전 포인터보다 현재 배포 상태를 더 정직하게 반영하는 baseline이 확보됐다.
  - 현재 병목은 `incremental 안정성`이 아니라 `core focus exact`와 `core keyword F1`이다.

---

## Experiment 011

- 날짜: 2026-04-10
- 모델: `gemma-4-31b`
- base URL: `https://api.vibemakers.kr/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`, `structuredSignals`
- 변경 요약:
  - `field_aware_v10`을 `field_aware_v3`와 release gate로 직접 비교
  - 목적: `그로스 마케팅`, `제품 성장 분석`, `심전도`, `의료영상`, `디지털 농업` 같은 core specificity를 더 올리되 incremental 안정성을 유지하는지 확인

### Metrics

- 게이트 리포트: `data/release_gates/release_gate_field_aware_v10_20260410.json`
- `field_aware_v3`
  - core focus exact: `85.71%`
  - core avg keyword F1: `59.57%`
  - incremental usable: `96.97%`
  - incremental low: `3.03%`
  - incremental banned keyword: `0.00%`
- `field_aware_v10`
  - core focus exact: `78.57%`
  - core avg keyword F1: `69.96%`
  - incremental usable: `93.94%`
  - incremental low: `6.06%`
  - incremental banned keyword: `1.35%`

### 판단

- 채택 여부: `미채택`
- 해석:
  - `field_aware_v10`은 core keyword specificity는 크게 올린다.
  - 하지만 core focus exact를 떨어뜨리고, incremental에서도 `usable`이 내려가며 `banned keyword`가 다시 생긴다.
  - 즉 다음 후보는 `keyword F1 상승`만 볼 것이 아니라, `focusLabel 선택`의 보수성과 `incremental generic keyword 억제`를 함께 만족해야 한다.

---

## Experiment 012

- 날짜: 2026-04-10
- 모델: `gemma-4-31b`
- base URL: `https://api.vibemakers.kr/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`
- 변경 요약:
  - `override_focus_label_from_context`를 보강해서 `3D 공간 이해 -> 컴퓨터 비전`, `고객 관계 관리 -> 그로스 마케팅`, `데이터 파이프라인 -> 생체신호/심전도/클라우드`, `로봇 제어 -> 로보틱스` 같은 좁은 정규화를 추가
  - 그 뒤 현재 챔피언 `field_aware_v3`를 다시 release gate에 태워 최신 baseline을 재고정

### Metrics

- 게이트 리포트: `data/release_gates/release_gate_field_aware_v3_refresh_20260410b.json`
- `field_aware_v3`
  - core focus exact: `92.86%`
  - core avg keyword F1: `59.57%`
  - incremental usable: `96.97%`
  - incremental low: `3.03%`
  - incremental banned keyword: `0.00%`
  - incremental empty focus: `3.03%`

### 판단

- 채택 여부: `기준선 갱신`
- 해석:
  - prompt 자체를 바꾸지 않고도, 모델 출력의 표준 라벨 정규화만으로 core focus exact를 크게 끌어올릴 수 있음을 확인했다.
  - 현재 남은 핵심 병목은 `focusLabel 선택`보다 `keyword specificity`다.

---

## Experiment 013

- 날짜: 2026-04-10
- 모델: `gemma-4-31b`
- base URL: `https://api.vibemakers.kr/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`, `structuredSignals`
- 변경 요약:
  - `field_aware_v11`을 추가
  - 목적: `문제/도메인 > 시스템/도구` 우선순위를 더 강하게 주고, `생체신호/그로스/비전/로보틱스` 부모 라벨을 더 일관되게 고르면서 keyword F1도 끌어올리는지 확인

### Metrics

- 게이트 리포트: `data/release_gates/release_gate_field_aware_v11_20260410.json`
- `field_aware_v3`
  - core focus exact: `92.86%`
  - core avg keyword F1: `59.57%`
  - incremental usable: `96.97%`
  - incremental low: `3.03%`
  - incremental banned keyword: `0.00%`
- `field_aware_v11`
  - core focus exact: `85.71%`
  - core avg keyword F1: `69.05%`
  - incremental usable: `93.94%`
  - incremental low: `6.06%`
  - incremental banned keyword: `1.38%`

### 판단

- 채택 여부: `미채택`
- 해석:
  - `field_aware_v11`은 keyword specificity는 크게 오른다.
  - 하지만 core focus exact를 다시 깎고, incremental 안정성도 손상시킨다.
  - 따라서 다음 후보는 `v11`처럼 prompt를 더 세게 밀기보다, 현재 `v3 + 정규화` 위에서 keyword만 더 보강하는 방향이 맞다.


## Experiment 014 — low rescue wave (field_aware_v12)
- Date: 2026-04-10
- Goal: remaining low rows 중 실제 JD를 가진 sparse 공고를 title/skills 중심으로 구제
- Scope: live board low rows 18건 subset
- Result: 안전 반영 5건
- Notes:
  - Rescue accepted: Moloco Senior Machine Learning Engineer, VUNO 생체신호 FE Junior 개발자, 비상교육 GPU 최적화 엔지니어, 세미파이브 SoC Verification Engineer, Upstage AI 교육 멘토풀
  - Rescue rejected: generic landing/company page, recruitment pool, research-admin bundle, title-only rows
  - field_aware_v12는 전면 승격 후보가 아니라 low-salvage 전용 프로파일로 유지

---

## Experiment 015

- 날짜: 2026-04-10
- 모델: `gemma-4-31b`
- base URL: `https://api.vibemakers.kr/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`, `structuredSignals`, `sectionSignalFacets`
- 변경 요약:
  - `field_aware_v13`을 추가
  - `sectionSignalFacets`를 모델이 직접 생성하도록 확장해, `상세본문/업무/요건/우대/기술`이 전체 키워드를 다시 끌어다 쓰지 않고 섹션 로컬 의미를 따로 갖게 하는지 확인
  - 목표: `field_aware_v3`의 incremental 안정성은 유지하면서 core focus/keyword specificity를 더 끌어올리는 것

### Metrics

- 게이트 리포트: `data/release_gates/release_gate_field_aware_v13_full_20260410.json`
- `field_aware_v3`
  - core summary exact: `28.57%`
  - core focus exact: `92.86%`
  - core avg keyword F1: `80.79%`
  - core strict pass: `28.57%`
  - core low match: `100.00%`
  - incremental usable: `96.67%`
  - incremental low: `3.33%`
  - incremental banned keyword: `0.00%`
- `field_aware_v13`
  - core summary exact: `14.29%`
  - core focus exact: `78.57%`
  - core avg keyword F1: `71.07%`
  - core strict pass: `14.29%`
  - core low match: `50.00%`
  - incremental usable: `96.67%`
  - incremental low: `3.33%`
  - incremental banned keyword: `2.01%`

### 판단

- 채택 여부: `미채택`
- 해석:
  - `field_aware_v13`은 `sectionSignalFacets`를 도입해 섹션 로컬 동작 자체는 개선했다.
  - 하지만 formal gate 기준으로는 `field_aware_v3` 대비 core focus exact와 keyword F1이 모두 하락했고, low-match도 크게 악화됐다.
  - incremental usable은 유지했지만 banned keyword가 다시 생겨 승격 조건을 충족하지 못했다.
  - 따라서 구조 개선은 유지하되, live summary champion은 계속 `field_aware_v3`로 두고 summary store도 다시 `v3` 기준으로 롤백했다.

---

## Experiment 016

- 날짜: 2026-04-11
- 모델: `gemma-4-31b`
- base URL: `https://api.vibemakers.kr/v1`
- input fields: `roleDisplay`, `title`, `detailBody`, `tasks`, `requirements`, `preferred`, `skills`
- output schema: `summary`, `keywords`, `focusLabel`, `quality`, `structuredSignals`, `sectionSignalFacets`
- 변경 요약:
  - `field_aware_v14`를 추가
  - 목적: `tool-first focus`, `deeptech in data analyst`, `business in engineer family` 같은 하네스 기반 anomaly family를 직접 줄일 수 있는지 확인
  - 동시에 service-scope / role-group 분류를 전량 다시 돌려 stale/contract 문제를 제거한 상태에서, `fresh field_aware_v3`와 `field_aware_v14`를 같은 harness family 기준으로 비교
  - 결과적으로 `v14`를 새 champion으로 올리지 않고, `fresh field_aware_v3`로 anomaly wave 대상 row만 다시 생성해 live board를 갱신

### Metrics

- family benchmark 리포트: `data/harness_family_benchmarks/harness_family_benchmark_v14_20260411.json`
- `field_aware_v3`
  - `deeptech_in_data_analyst`: `1`
  - `business_in_engineer_family`: `2`
  - `tool_first_focus`: `0`
- `field_aware_v14`
  - `deeptech_in_data_analyst`: `1`
  - `business_in_engineer_family`: `2`
  - `tool_first_focus`: `0`

### 판단

- 채택 여부: `v14 미채택`, `fresh v3 remediation 채택`
- 해석:
  - `v14`는 새 champion으로 올릴 만큼 뚜렷한 우위를 만들지 못했다.
  - 대신 stale signature, service-scope contract, role override 경로를 먼저 바로잡고 `fresh v3`로 문제 row를 다시 생성하자 주요 anomaly family가 정리됐다.
  - 추가로 `structuredSignals -> focusLabel` projection이 실제 후처리 경로에 연결되지 않던 누수를 고쳐, `광고 데이터`, `RAG`, `3D 공간 이해`, `NPU 적용`처럼 더 구체한 focus가 live board에 반영되게 했다.
  - 즉 이 라운드의 본질 개선은 `새 prompt 승격`보다 `하네스 기반 재검증 + stale/contract 해소 + fresh regeneration + structured focus projection 활성화`였다.

### Remediation 결과

- live harness 기준
  - `excluded_leaked_into_display`: `0`
  - `deeptech_in_data_analyst`: `0`
  - `tool_first_focus`: `0`
  - `broad_focus_specificity_gap`: `0`
- 여전히 남은 high family
  - `business_in_engineer_family`: `2`
- 남은 info family
  - `deeptech_context_present`: `1`
  - `business_context_present`: `2`
- 대표 복구 예시
  - `Staff, Data Engineer (Ads Ops Data Support)` -> `focusLabel=광고 데이터`
  - `[강남오피스] AI Agent Engineer` -> `focusLabel=RAG`
  - `VSLAM Engineer - Team Lead` -> `focusLabel=3D 공간 이해`
  - `NPU Library Software Engineer` -> `focusLabel=NPU 적용`
- 현재 하네스는 `dominance failure`와 `context present`를 구분한다.
- 다음 개선 축은 남은 `business_in_engineer_family 2건`의 focus를 `제품 성장 분석`에서 더 기술/문제 축으로 좁히는 것이다.
