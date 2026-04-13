# 품질·성능 개선 진행 절차

이 문서는 `Hire Atlas`의 공고 추출 품질, 그룹 신뢰도, 추론 성능, 서비스 응답성을 함께 개선하기 위한 실행 순서를 정리합니다.

현재 이 계획을 실행할 때 반드시 지켜야 하는 품질 원칙은 [model_quality_principles.md](/Users/junheelee/Desktop/career_dashboard/docs/model_quality_principles.md)를 기준으로 삼습니다.

## 1. 목표

- 사용자 화면에서 `납득되는 그룹 제목`이 보이도록 만든다.
- `위한`, `또는`, `석사`, `학력` 같은 약한 표현이 그룹 기준어로 올라오지 않게 한다.
- `상세본문 / 주요업무 / 자격요건 / 우대사항 / 핵심기술`의 5개 섹션이 모두 같은 기준으로 읽히게 만든다.
- 이후 `그룹 카드 클릭 -> 오른쪽 공고 패널 슬라이드 인` 인터랙션을 붙여도 느려지지 않도록 서비스 성능을 정리한다.

## 2. 현재 문제 정의

- Qwen `qwen2.5:3b` 결과 중 low 품질 비율이 높다.
- 저품질 결과가 `keyword`에 그대로 섞여 그룹 제목까지 오염시킨다.
- 프롬프트가 약할 때 field별 의미가 섞여 `문장형 keyword`나 `문법형 단어`가 남는다.
- 클라이언트에서 즉석 그룹화를 할 때 약한 표현이 seed가 되면 신뢰도가 급격히 떨어진다.

## 3. 개선 원칙

- 우선순위는 `파인튜닝`이 아니라 `프롬프팅 + 입력 설계 + 후처리 + 평가 체계`다.
- 모델이 낸 결과를 그대로 쓰지 않고, 서비스 화면에 올라갈 수 있는 값만 정제해서 쓴다.
- `좋은 문장 생성`보다 `구조화 추출 정확도`를 먼저 올린다.
- 품질 실험과 런타임 성능 개선은 분리하되, 같은 milestone 안에서 함께 관리한다.
- 특정 데이터셋에 맞춘 보정이 과해지지 않도록 `generalization guardrails`를 별도로 유지한다.

## 4. 전체 진행 순서

### Phase 0. 기준셋 고정

- 대표 공고 150~300건을 추려 평가셋으로 고정한다.
- 직무, 회사, low/high 품질 공고, 스크랩 품질 편차가 모두 섞이게 뽑는다.
- 이 셋은 prompt 비교와 이후 파인튜닝 판단의 기준이 된다.

### Phase 1. 평가 지표 정의

- 아래 지표를 자동으로 집계한다.
- `금지어 포함 비율`
- `문장형 keyword 비율`
- `중복 그룹 제목 비율`
- `field별 유효 keyword 평균 개수`
- `summaryQuality low 비율`
- `사람 검토 기준 pass rate`
- 추가로 `증분 홀드아웃`에서의 악화 여부를 같이 본다.

### Phase 1-1. 증분 홀드아웃 유지

- 가장 최근에 유입된 공고를 별도 검증셋으로 고정한다.
- 이 셋은 튜닝용이 아니라 일반화 확인용이다.
- 고정 평가셋과 함께 통과해야만 새 prompt/후처리를 채택한다.

### Phase 2. 프롬프트 테스팅

- 먼저 prompt 실험으로 품질 상한을 확인한다.
- 테스트 순서:
  1. 기존 prompt baseline
  2. `title + roleDisplay + detailBody + tasks + requirements + preferred + skills` 전체 입력
  3. strict negative instruction 강화
  4. field별 분리 추출 prompt
  5. 더 강한 모델 benchmark

- 실험 결과는 각 prompt별로 다음을 남긴다.
  - `input schema`
  - `output schema`
  - `금지어 발생률`
  - `대표 실패 사례`
  - `채택 여부`

### Phase 3. 후처리 강화

- 금지어, 조사형 꼬리, 경력/학력형 표현 제거
- 회사명 echo 제거
- 문장형 keyword 제거
- low 품질 결과는 fallback keyword만 제한적으로 허용
- fallback도 그대로 쓰지 않고 `서비스 허용 단어`만 남긴다

### Phase 4. 그룹 로직 개선

- 그룹 seed는 `짧은 명사구`만 허용한다.
- `기술`, `도메인`, `업무 유형`, `서빙/인프라`, `검증/실험`처럼 묶음 근거가 되는 표현만 seed 후보가 된다.
- field별 그룹은 아래처럼 다르게 본다.
  - `상세본문`: 역할+업무 신호 중심
  - `주요업무`: 실제 하는 일 중심
  - `자격요건`: 자격보다 역량/스택 중심
  - `우대사항`: 차별화 신호 중심
  - `핵심기술`: 기술 스택 중심

### Phase 5. 서비스 성능 개선

- quality와 별도로 응답 성능도 정리한다.
- 실행 순서:
  1. `job hash` 기준 재추론 캐시
  2. 변경된 공고만 부분 재생성
  3. field 섹션 precompute
  4. 우측 슬라이드 패널용 posting map precompute
  5. 그룹 클릭 시 full recompute 금지
  6. async batch inference queue 준비

- 목표:
  - 전체 보드 로드 시 즉시 렌더 가능한 데이터 사용
  - 그룹 클릭 시 오른쪽 패널은 서버 재계산 없이 열릴 수 있어야 함

### Phase 6. 더 강한 모델 비교

- prompt가 안정된 뒤 더 강한 모델과 현재 모델을 비교한다.
- 비교 항목:
  - 금지어 감소율
  - 그룹 제목 신뢰도
  - low 비율 감소
  - field별 일관성
  - 비용/속도

- 이 단계에서 `서비스 모델`과 `정답 생성용 모델`을 나눌지 판단한다.

### Phase 7. 파인튜닝 판단

- 아래 조건이 충족되면 그때 파인튜닝으로 넘어간다.
- prompt와 후처리를 충분히 다듬었는데도 같은 오류가 반복된다.
- 더 강한 모델을 써도 `구조화 추출 안정성`이 기대만큼 안 오른다.
- 평가셋 기준으로 field별 편차가 크다.

- 파인튜닝 대상은 자유 생성 모델이 아니라 `구조화 추출기`로 잡는다.

## 5. 바로 실행할 일

1. 평가셋 샘플 추출
2. prompt 실험 로그 포맷 만들기
3. 금지어/허용어 기준표 만들기
4. field별 prompt 분리 초안 작성
5. 전체 재추론 전 stronger-model benchmark 1회 실행

## 6. 산출물

- `docs/quality_execution_plan.md`
- `docs/prompt_experiment_log.md`
- `docs/labeling_rules.md`
- `docs/generalization_guardrails.md`
- `docs/review_workflow.md`
- `data/eval_set.json`
- `data/incremental_eval_set.json`
- `data/review_wave_001.json`
- `data/prompt_benchmarks/*.json`

## 7. 현재 의사결정

- 현재 우선순위는 `프롬프팅 최적화`다.
- 파인튜닝은 이후 단계에서 검토한다.
- 품질 안정화가 선행되어야 오른쪽 슬라이드 패널 인터랙션도 신뢰를 가지고 확장할 수 있다.

## 8. 2026-04-10 추가 고정 방향

- `광주지사`, `경력무관`, `이상이신`, `채용절차법` 같은 표현을 하나씩 막는 방식은 응급처치로만 본다.
- 본질 해결은 `raw 채용문장`이 카드/군집 라벨을 직접 만들지 못하게 경로를 끊는 것이다.
- `focusLabel`, `highlightKeywords`, `structuredSignals` 같은 모델 기반 구조화 신호가 군집과 그래프의 중심 입력이어야 한다.
- `requirements`, `preferred`, `detailBody` 원문은 증거 문장으로는 쓸 수 있어도, 카드 라벨 생성기의 주 입력이 되어서는 안 된다.
- 이후 품질 개선은 `배제`가 아니라 `분류 정확도`, `키워드 정확도`, `군집 purity`를 실제로 올리는 방향으로만 진행한다.

## 9. 2026-04-11 하네스 운영 원칙

- anomaly family는 `dominance failure`와 `context present`를 구분해서 본다.
- 예:
  - `deeptech_in_data_analyst`, `business_in_engineer_family`는 실제 오분류 family다.
  - `deeptech_context_present`, `business_context_present`는 문맥이 남아 있는지 보는 info family다.
- 즉 비즈니스/딥테크 단어가 row 어딘가에 있다는 이유만으로 실패로 세지 않는다.
- 다음 remediation wave는 `focus dominance failure`와 `broad focus specificity gap`을 우선 대상으로 삼는다.
- 대표 예:
  - `클라우드`처럼 너무 넓은 focus가 `광고 데이터` 같은 더 구체한 문제 신호를 가릴 수 있다.
  - 이런 경우는 제거가 아니라 `focus specificity` 개선 대상으로 본다.
