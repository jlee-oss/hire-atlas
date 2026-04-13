# 모델 의사결정 리포트

- 생성 시각: `2026-04-12T05:19:16.040220+00:00`
- 현재 jobs 기준: `172`건

## 현재 상태

- summary 존재: `161/172` (`93.6%`)
- focusLabel 존재: `161/172` (`93.6%`)
- low: `11/172` (`6.4%`)
- 넓은 focusLabel 잔존(raw): `49/172` (`28.5%`)
- 허용 broad focus(raw): `29/172` (`16.9%`)
- 문제 broad focus(raw): `20/172` (`11.6%`)
- 넓은 focusLabel 잔존(board): `28/172` (`16.3%`)
- 허용 broad focus(board): `28/172` (`16.3%`)
- 문제 broad focus(board): `0/172` (`0.0%`)

## 평가 체계

- core eval set: `96`건 / 검수된 항목 `10`건
- incremental holdout: `48`건 / 검수된 항목 `4`건

## 리뷰 정확도

- core overall pass: `0/10` (`0.0%`)
- incremental overall pass: `0/4` (`0.0%`)

## 일반화 확인

- 최신 suite benchmark: `suite_001_smoke.json`
- core + incremental 게이트 통과: `True`
- latest core usable rate: `0.5833`
- latest incremental usable rate: `0.7500`

## 모델 비교 상태

- benchmark에 등장한 모델: `gemma-4-31b, qwen2.5:3b, qwen2.5:7b`
- 더 강한 모델 비교 완료: `True`
- 최신 stronger-model 비교: `review_wave_models_001.json`

- hard set quality 개선: `3`건
- hard set quality 악화: `0`건

## 현재 판단

- 결론: 현재는 파인튜닝 진입 단계가 아닙니다.
- 다음 우선순위: 1) 골드셋 검수 2) review pass rate 계산 3) 그 후에만 튜닝 여부 판단

## 현재 blocker

- 사람이 검토한 core 골드셋이 부족합니다.
- 사람이 검토한 incremental 골드셋이 부족합니다.

## 튜닝 진입 조건

- core + incremental 둘 다 통과
- 더 강한 모델 비교 완료
- 반복 오류 유형이 구조적으로 남음
- 검수된 골드셋이 충분함
- 목표가 자유 생성이 아니라 structured extraction으로 명확함

