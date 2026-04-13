# Service Scope Adjudication Pack 001

- generatedAt: `2026-04-11T14:56:21.134375+00:00`
- items: `25`
- modelDecisions: `{'exclude': 4, 'include': 16, 'review': 5}`
- suggestedDecisions: `{'exclude': 2, 'include': 16, 'review': 7}`
- reviewPriorities: `{'confirm_positive': 16, 'critical_prompt_failure': 2, 'goldset_conflict_review': 2, 'human_boundary_review': 5}`

이 문서는 confirmed goldset이 아닙니다.
`suggestedServiceScope`는 검수 보조값이며, 최종 확정은 `confirmServiceScope`에 사람이 입력해야 합니다.

## Critical / Conflict Rows

| # | priority | company | title | quality | model | suggested | reason |
|---:|---|---|---|---|---|---|---|
| 1 | critical_prompt_failure | 슈어소프트테크 | [우주항공국방기술실(판교)] SW검증 (경력) | high | exclude | review | AI/data/deeptech 신호가 있어 hard exclude 금지 |
| 2 | critical_prompt_failure | 여기어때 | Server Engineer [숙박플랫폼개발] | high | exclude | review | AI/data/deeptech 신호가 있어 hard exclude 금지 |
| 3 | goldset_conflict_review | 아키드로우 | 클라우드 인프라 엔지니어(DevOps) | high | exclude | exclude | 일반 non-scope 가능성이 커 goldset 과포함 여부 확인 |
| 4 | goldset_conflict_review | 비상교육 | DevOps 엔지니어 | medium | exclude | exclude | 일반 non-scope 가능성이 커 goldset 과포함 여부 확인 |

## All Rows

| # | company | title | quality | model | suggested | confirm |
|---:|---|---|---|---|---|---|
| 1 | 슈어소프트테크 | [우주항공국방기술실(판교)] SW검증 (경력) | high | exclude | review |  |
| 2 | 여기어때 | Server Engineer [숙박플랫폼개발] | high | exclude | review |  |
| 3 | 아키드로우 | 클라우드 인프라 엔지니어(DevOps) | high | exclude | exclude |  |
| 4 | 비상교육 | DevOps 엔지니어 | medium | exclude | exclude |  |
| 5 | 모빌린트 | ARM Architecture Engineer | high | review | review |  |
| 6 | 세미파이브 | Firmware & Embedded Linux Engineer | high | review | review |  |
| 7 | 스트라드비젼 | Software Testing Engineer | high | review | review |  |
| 8 | 세미파이브 | SoC Verification Engineer | low | review | review |  |
| 9 | 케이플러스 | 케이플러스 | low | review | review |  |
| 10 | 딥노이드 | Application Developer (Medical AI) | high | include | include |  |
| 11 | 딥노이드 | Field Application Engineer (SaMD) | high | include | include |  |
| 12 | 리벨리온 | IP Design Verification Engineer | high | include | include |  |
| 13 | 리벨리온 | SoC Design Verification Engineer | high | include | include |  |
| 14 | 모빌린트 | NPU Field Application Engineer (H/W) | high | include | include |  |
| 15 | 모빌린트 | NPU Verification Engineer | high | include | include |  |
| 16 | 모빌린트 | SDK Field Engineer | high | include | include |  |
| 17 | 모빌린트 | SoC Design Engineer | high | include | include |  |
| 18 | 모빌린트 | Windows Driver Engineer | high | include | include |  |
| 19 | 인터엑스 | IT(AX)전략 담당자 대리~본부장급(팀 세팅 중) | high | include | include |  |
| 20 | 인터엑스 | [대구] C#, .NET 개발자 (C#/.NET, 실시간 데이터) | high | include | include |  |
| 21 | 펄어비스 | 펄어비스 | high | include | include |  |
| 22 | 거대한에이아이실험실 주식회사 | 서비스 개발자(Service Developer) | medium | include | include |  |
| 23 | 세미파이브 | SoC Generator Design(Scala/Chisel) Engineer | medium | include | include |  |
| 24 | 안랩 | [경력] Web 개발 | medium | include | include |  |
| 25 | 뷰노 | 생체신호 FE Junior 개발자 | low | include | include |  |
