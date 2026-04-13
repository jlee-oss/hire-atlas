# Final Confirmation Package 001

- version: `final-confirmation-001-model-improvement-complete`
- generatedAt: `2026-04-12T05:19:16.253519+00:00`
- serverUrl: `http://127.0.0.1:4174/`
- operationalStatus: `ready_for_user_confirmation`
- modelImprovementStatus: `complete_guard_independent`

## 판정

- 운영 안정화 버전으로 컴펌 가능합니다.
- 모델 개선 gate도 통과했습니다.
- guard 의존도 없이 service scope 판정 기준을 통과한 상태입니다.

## 핵심 지표

- sourceJobs: `172`
- boardRows: `158`
- excludedJobs: `14`
- reviewJobs: `11`
- sourceRetentionRate: `0.918605`
- filteredOutRate: `0.081395`
- optimizationScore: `96.1538`
- excludedHighQualityRows: `1`
- excludedAiAdjacentRows: `0`
- businessInEngineerFamilyRows: `0`
- missingSummaryRows: `7`

## Guard 부채

- guardRecoveredRows: `0`
- guardRecoveredHighQualityRows: `0`
- candidatesJson: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_guard_recovery_candidates_001.json`
- candidatesCsv: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_guard_recovery_candidates_001.csv`
- candidatesMd: `/Users/junheelee/Desktop/career_dashboard/docs/service_scope_guard_recovery_candidates_001.md`

## 모델 개선 실행 상태

- goldsetStatus: `confirmed`
- provisionalGoldsetItems: `0`
- benchmarkFalseExcludeCount: `0`
- benchmarkHighQualityFalseExcludeCount: `0`
- shadowGuardRecoveredRows: `0`
- shadowTargetsPassed: `True`
- modelBenchmarkPassed: `True`
- modelImprovementEligible: `True`
- modelImprovementGateStatus: `passed`
- modelImprovementGatePassed: `True`
- modelImprovementGateBlockers: `-`
- adjudicationItems: `25`
- adjudicationSuggestedDecisions: `{'exclude': 4, 'include': 16, 'review': 5}`
- proposedGoldsetDecisions: `{'exclude': 4, 'include': 16, 'review': 5}`
- proposedBenchmarkPassed: `True`
- proposedBenchmarkFalseExcludeCount: `0`
- goldsetJson: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_goldset_001.json`
- benchmarkJson: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_benchmark_001.json`
- shadowJson: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_shadow_guard_off_001.json`
- modelGateJson: `/Users/junheelee/Desktop/career_dashboard/data/model_improvement_gate_latest.json`
- adjudicationCsv: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_adjudication_pack_001.csv`
- proposedBenchmarkJson: `/Users/junheelee/Desktop/career_dashboard/data/service_scope_model_benchmark_proposed_v2.json`

## 남은 점검

- `info` guard dependency cleared: runtime guard 복구 row가 0개입니다.
- `medium` missing summaries: 7개 표시 row가 summary 없이 low 상태입니다.
- `medium` broad focus specificity gap: 1개 row에서 더 구체적인 focus 후보가 남아 있습니다.
- `info` context-only families: deeptech_context_present=0, business_context_present=1

## 컴펌 체크리스트

- [ ] `required` 운영 및 모델 개선 완료 승인 - 158개 표시 공고, 14개 제외 공고, 11개 review 공고 구성을 승인합니다.
- [ ] `required` confirmed v2 goldset 승인 - service scope confirmed v2 goldset 25개 판정을 모델 개선 기준으로 승인합니다.
- [ ] `optional` missing summary 7개 보류 승인 - 현재 모델 개선 gate와 운영 target에는 영향이 없습니다.

## 최종 문구

> 운영 안정화 및 모델 개선 gate 모두 승인 가능.
