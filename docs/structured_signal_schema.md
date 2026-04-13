# 구조화 신호 추출 스키마 초안

- 작성일: `2026-04-08`
- 목적: `summary/focusLabel/keywords`를 직접 생성하는 대신, 증분 데이터에도 일반화되는 중립 신호를 먼저 추출하기 위한 기준

## 원칙

1. 게시용 문장을 먼저 만들지 않는다.
2. 신호는 `짧고 정규화 가능`해야 한다.
3. 근거가 약하면 비워두거나 `low`로 둔다.
4. 그룹핑에 바로 쓰지 않고, 먼저 구조화 저장 후 projection 한다.

## 입력 필드

- `직무명_표시`
- `상세본문_분석용`
- `주요업무_분석용`
- `자격요건_분석용`
- `우대사항_분석용`
- `핵심기술_분석용`

## 1차 추출 스키마

```json
{
  "quality": "high | medium | low",
  "domainSignals": ["..."],
  "problemSignals": ["..."],
  "systemSignals": ["..."],
  "modelSignals": ["..."],
  "dataSignals": ["..."],
  "workflowSignals": ["..."],
  "roleSignals": ["..."],
  "confidenceNotes": ["..."]
}
```

## 현재 반영 상태

- 저장 위치: `data/job_summaries.json > items.*.structuredSignals`
- 현재 방식: `모델 재추론 없이`, 기존 `summary/focusLabel/keywords`와 원본 필드를 다시 읽어 구조화 신호를 만든다
- 현재 보드 사용처:
  - `signalFacets`
  - 공고 간 연결 신호
  - 클러스터 그래프 신호
  - 회사/공고 신호 텍스트 누적

## 신호 정의

### domain_signals

- 산업/적용 맥락
- 예: `의료`, `금융`, `광고`, `자율주행`, `교육`, `로보틱스`

### problem_signals

- 풀려는 문제 또는 핵심 과업
- 예: `심전도 분석`, `객체 인식`, `RAG`, `추천`, `이상탐지`, `음성 인식`

### system_signals

- 구현/서빙/아키텍처 계층
- 예: `모델 서빙`, `분산 추론`, `온디바이스`, `클라우드 인프라`, `백엔드`

### model_signals

- 모델/프레임워크/학습 계층
- 예: `LLM`, `멀티모달`, `컴퓨터 비전`, `PyTorch`, `TensorFlow`, `ONNX`

### data_signals

- 데이터 자산/파이프라인/분석 계층
- 예: `데이터 파이프라인`, `SQL`, `ETL`, `실험 데이터`, `로그 분석`

### workflow_signals

- 일하는 방식/실무 흐름
- 예: `A/B 테스트`, `실험 설계`, `MLOps`, `배포`, `모니터링`, `평가`

### role_signals

- 직무 범주 신호
- 예: `인공지능 엔지니어`, `인공지능 리서처`, `데이터 분석가`, `데이터 사이언티스트`

## 2차 projection

1차 추출 결과를 바탕으로 아래를 만듭니다.

```json
{
  "focus_label": "대표 중심 신호 1개",
  "group_keywords": ["그룹 기준 2~4개"],
  "summary": "게시용 식별 문구 1줄"
}
```

## projection 원칙

1. `focus_label`은 `domain/problem` 우선
2. 더 나은 domain/problem이 있으면 `PyTorch`, `SQL`, `파이프라인` 같은 broad label은 대표값이 되지 않는다
3. `summary`는 문장보다 식별 문구에 가깝게 유지한다
4. `quality=low`면 무리하게 채우지 않는다

## 금지 패턴

대표값 및 그룹 seed에서 제외한다.

- 조사/연결어: `위한`, `또는`, `및`, `등`
- 일반 학력/자격: `학력`, `석사`, `박사`, `경력`
- 과도하게 일반적인 단어: `제품`, `서비스`, `기술`, `분석`, `개발`
- 전형/안내 문구: `지원 방법`, `전형 절차`, `우대 사항`, `복리후생`

## 운영 목표

- 대부분의 신규 공고는 1차 추출만으로 안정 처리
- 이상 케이스만 검수 큐로 이동
- 보드 품질은 2차 projection 규칙으로 일관되게 유지
