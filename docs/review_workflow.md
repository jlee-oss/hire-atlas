# 리뷰 워크플로

이 문서는 `모델 정확도`를 사람 기준으로 점검하기 위한 첫 리뷰 웨이브 운영 방법을 정리합니다.

## 1. 왜 필요한가

현재는 다음 지표만 있습니다.

- usable rate
- low rate
- empty focusLabel rate
- 금지어 비율

이 지표들은 `망가졌는지`는 잘 보여주지만, `의미가 맞는지`를 직접 증명하지는 못합니다.  
그래서 `low + borderline + control sample`을 섞은 리뷰 웨이브를 따로 만들고, 사람이 직접 통과 여부와 수정값을 남깁니다.

## 2. 리뷰 웨이브 생성

```bash
python3 scripts/build_review_wave.py
```

기본 결과 파일:

- `data/review_wave_001.json`

기본 구성:

- core eval 문제 케이스 `24`
- incremental 문제 케이스 `12`
- core control sample `4`
- incremental control sample `2`

총 `42`건을 기본 웨이브로 사용합니다.

## 3. 무엇을 검수하나

각 항목은 아래를 따로 봅니다.

- `summaryPass`
- `focusLabelPass`
- `keywordsPass`
- `overallPass`

필요하면 아래 수정값을 같이 남깁니다.

- `correctedSummary`
- `correctedFocusLabel`
- `correctedKeywords`
- `correctedQuality`
- `notes`

## 3-1. CSV로 내보내기

Google Sheets나 스프레드시트에서 검수하고 싶다면 아래를 실행합니다.

```bash
python3 scripts/export_review_wave_csv.py
```

기본 결과 파일:

- `data/review_wave_001.csv`

우선순위 브리프를 마크다운으로 보고 싶다면:

```bash
python3 scripts/build_review_brief.py
```

기본 결과 파일:

- `docs/review_wave_001_brief.md`

상위 우선순위 항목에 대한 모델 수정 초안을 만들려면:

```bash
python3 scripts/build_review_suggestions.py
```

결과 파일:

- `data/review_suggestions_001.json`
- `docs/review_suggestions_001.md`

현재 기본 검수 제안 모델은 `qwen2.5:7b`입니다.

제가 먼저 정리한 프리필 초안을 리뷰 웨이브에 붙이려면:

```bash
python3 scripts/apply_review_prefill.py
```

이 단계는 review 값을 덮어쓰지 않고, CSV에서 참고할 `assistantSummary / assistantFocusLabel / assistantKeywords` 컬럼만 채워줍니다.

3b와 7b의 hard set 비교 리포트를 만들려면:

```bash
python3 scripts/build_stronger_model_comparison.py
```

결과 파일:

- `data/model_comparisons/review_wave_models_001.json`
- `docs/stronger_model_comparison.md`

## 3-2. CSV를 다시 가져오기

CSV에서 검수 내용을 입력한 뒤 아래를 실행하면 다시 `review_wave_001.json`에 반영됩니다.

```bash
python3 scripts/import_review_wave_csv.py
```

## 4. 우선순위 기준

리뷰 웨이브는 현재 보드 결과를 기준으로 아래 문제를 먼저 모읍니다.

- `low_quality`
- `summary_missing`
- `focus_missing`
- `summary_title_echo`
- `summary_hiring_echo`
- `focus_too_broad`
- `focus_hiring_echo`
- `focus_company_echo`
- `keyword_noise`

즉, 지금 실제 서비스 화면에서 신뢰를 해치는 유형을 먼저 검수합니다.

## 5. 리뷰 반영

리뷰가 끝난 뒤 아래를 실행하면 `review_wave_001.json`의 review 값이 원본 평가셋으로 반영됩니다.

```bash
python3 scripts/apply_review_wave.py
```

반영 대상:

- `data/eval_set.json`
- `data/incremental_eval_set.json`

## 6. 반영 후 확인

리뷰 반영 뒤에는 아래를 다시 실행합니다.

```bash
python3 scripts/build_model_decision_report.py
```

그러면 현재 리포트에 `검수된 core 항목 수`, `검수된 incremental 항목 수`가 잡히고, 튜닝 진입 판단 근거가 실제 리뷰 기반으로 바뀝니다.

정확도 수치만 따로 보고 싶다면 아래를 실행합니다.

```bash
python3 scripts/score_review_accuracy.py
```

결과 파일:

- `docs/review_accuracy_report.md`

검수 순서를 더 줄이고 싶다면 아래를 실행합니다.

```bash
python3 scripts/build_review_triage.py
```

결과 파일:

- `data/review_triage_001.json`
- `docs/review_triage_001.md`

assistant draft가 모두 붙은 뒤, 실제로 어떤 종류의 확인만 남았는지 핸드오프용으로 압축하려면 아래를 실행합니다.

```bash
python3 scripts/build_review_handoff.py
```

결과 파일:

- `data/review_handoff_001.json`
- `data/review_handoff_001.csv`
- `docs/review_handoff_001.md`

이 단계는 `정확도`를 새로 계산하지는 않지만, 남은 검수량을 `upgrade / full rewrite / focus check / low confirm` 수준으로 분해해 실제 사람 확인 부담을 줄이는 데 목적이 있습니다.

핸드오프 이후 실제로 사람이 확인해야 하는 최소 큐와, 후순위 focus 백로그를 분리하려면 아래를 실행합니다.

```bash
python3 scripts/build_review_confirm_queue.py
```

결과 파일:

- `data/review_confirm_queue_001.json`
- `data/review_confirm_queue_001.csv`
- `docs/review_confirm_queue_001.md`
- `data/review_focus_backlog_001.json`
- `data/review_focus_backlog_001.csv`
- `docs/review_focus_backlog_001.md`

이 단계는 `즉시 확인 대상`과 `후순위 그룹 조정 대상`을 나눠, 실제 사람 검수량을 더 줄이는 데 목적이 있습니다.

즉시 확인 큐를 승인/반려 중심의 초경량 시트로 만들려면 아래를 실행합니다.

```bash
python3 scripts/build_review_decision_sheet.py
```

결과 파일:

- `data/review_decision_sheet_001.csv`
- `docs/review_decision_sheet_001.md`

시트 입력 후 웨이브 review 필드에 반영하려면 아래를 실행합니다.

```bash
python3 scripts/apply_review_decision_sheet.py
```

지원하는 결정값:

- `approve_draft`
- `approve_low`
- `approve_current`
- `needs_edit`
- `skip`

현재 결정 시트를 그대로 적용했을 때 어떤 provisional 결과가 나오는지 미리 보려면 아래를 실행합니다.

```bash
python3 scripts/build_provisional_review_report.py
```

결과 파일:

- `docs/provisional_review_report.md`

이 리포트는 **실제 사람 검수 결과가 아니라**, 현재 decision sheet를 가정 적용한 미리보기입니다.

실제 검수 반영 이후 오류 유형을 다시 요약하려면 아래를 실행합니다.

```bash
python3 scripts/build_review_error_analysis.py
```

결과 파일:

- `data/review_error_analysis_001.json`
- `docs/review_error_analysis_001.md`

현재 검수 결과를 다음 프롬프트 개선용 seed로 묶으려면 아래를 실행합니다.

```bash
python3 scripts/build_review_goldset_seed.py
```

결과 파일:

- `data/review_goldset_seed_001.json`
- `data/review_goldset_seed_001.jsonl`
- `docs/review_goldset_seed_001.md`

## 7. 현재 원칙

- 리뷰 없는 모델 평가는 `proxy metric`으로만 취급합니다.
- 리뷰 웨이브는 문제 케이스만이 아니라 control sample도 함께 봅니다.
- 정답을 모를 때 억지로 채우기보다 `low`로 두는 편이 낫습니다.
- 튜닝 판단은 리뷰 누적 이후에만 합니다.
