# 골드셋 확장 웨이브 002

- 생성 시각: `2026-04-10T13:02:11.565684+00:00`
- 총 항목: `9`
- 목적: `field_aware_v13` 실험 후에도 남아 있는 `focusLabel broadening / tool-first / domain drift` 유형을 다음 goldset 확장 대상으로 고정

## 분포

- `focus_correction_v13_residual`: `9`

## 직무 분포

- `인공지능 엔지니어`: `9`

## current -> target

- `노타` | `[NetsPresso] Senior Edge AI Engineer` | `ONNX` -> `모델 최적화`
- `노타` | `[NetsPresso] AI Platform Engineer` | `컴퓨터 비전` -> `MLOps`
- `업스테이지` | `AI Solution Architect - Cloud` | `시스템 아키텍처` -> `클라우드`
- `서울로보틱스` | `Senior Software Engineer- System` | `데이터 파이프라인` -> `미들웨어`
- `스트라드비젼` | `Sr. Embedded AI Engineer` | `PyTorch` -> `임베디드 배포`
- `리벨리온` | `Design Validation Engineer` | `로보틱스` -> `NPU 검증`
- `마키나락스` | `Forward Deployed Engineer - MLOps` | `클라우드` -> `MLOps`
- `쿠팡` | `Staff, Data Engineer (Ads Ops Data Support)` | `마케팅` -> `광고 데이터 파이프라인`
- `마키나락스` | `Forward Deployed Engineer - LLM` | `컴퓨터 비전` -> `LLM`

## 메모

- 이번 wave는 `배제`가 아니라 `현재 high-quality로 보이는 공고에서도 focusLabel이 잘못 좁혀지거나 넓어지는` 패턴을 바로잡기 위한 후보군이다.
- 공통 원인:
  - `ONNX`, `PyTorch`처럼 스택/포맷이 실제 문제 중심 focus를 덮음
  - `컴퓨터 비전`, `마케팅`, `시스템 아키텍처` 같은 broad label이 applied role을 평탄화함
  - `LLM/VLM`, `platform/domain` 혼합 공고에서 주변 신호가 주축을 빼앗음
- 다음 실험은 이 wave를 core goldset에 편입해 `tool-first suppression`, `domain-over-system`, `applied-role anchoring`을 함께 평가해야 한다.
