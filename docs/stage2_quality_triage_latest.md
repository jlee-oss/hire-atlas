# Stage2 Quality Triage Latest

- generatedAt: `2026-04-12T10:14:38.624751+00:00`
- totalRows: `187`
- pendingRows: `0`
- needsReviewRows: `0`
- staleRows: `0`

## Blocking Issue Counts


## Triage Groups

### 2차 동기화 문제

- groupKey: `stage2_sync`
- rows: `0`
- action: 1차 변경해시와 2차 후보가 맞지 않으므로 2차 후보를 최신 1차 기준으로 재적재해야 합니다.
- examples: none

### 직군/초점 재분류

- groupKey: `role_mismatch`
- rows: `0`
- action: 공고를 제거하지 말고 제목, 주요업무, 자격요건을 기준으로 직군과 직무초점을 다시 산정해야 합니다.
- examples: none

### 키워드/초점 추출 실패

- groupKey: `signal_extraction`
- rows: `0`
- action: Gemma 기반 field-aware 재추론 또는 수동 2차 보정으로 핵심기술, 직무초점, 구분요약을 채워야 합니다.
- examples: none

### 비차단 참고 신호

- groupKey: `non_blocking_context`
- rows: `48`
- action: 배포 차단 신호가 아니라 검수 참고 정보로만 유지합니다.
- issueCounts: `{'business_context_in_ai_role': 10, 'focus_diff': 34, 'summary_diff': 36, 'role_diff': 10, 'keywords_diff': 24, 'summary_too_short': 3}`

- `노타` | `[NetsPresso] AI Platform Engineer` | `low` | `stage2_approved | business_context_in_ai_role | focus_diff | summary_diff`
- `노타` | `[Solution AIE] AI Engineer` | `low` | `stage2_approved | business_context_in_ai_role`
- `당근` | `Data Analytics Engineer (인턴) | 로컬 비즈니스` | `low` | `stage2_approved | role_diff | focus_diff | summary_diff`
- `당근` | `Data Analytics Engineer | 테크코어 (데이터 가치화)` | `low` | `stage2_approved | role_diff | focus_diff | summary_diff`
- `데브시스터즈` | `[기술본부] Software Engineer, Data Platform` | `low` | `stage2_approved | role_diff | focus_diff | summary_diff`
- `데브시스터즈` | `[기술본부] Data Engineer (BI/DW)` | `low` | `stage2_approved | role_diff | focus_diff | summary_diff`
- `딥노이드` | `Field Application Engineer (SaMD)` | `low` | `stage2_approved | focus_diff | keywords_diff | summary_diff`
- `라온시큐어` | `(주)엠케이디 채용시 마감 엠케이디 Python AI 개발자 채용 (경력 또는 석/박사) E-7 비자지원 정규직 인턴 연구·R&D, IT개발·데이터 부산 남구 기초 회화 가능 E-7` | `low` | `stage2_approved | summary_too_short`
- `리벨리온` | `IP Design Verification Engineer` | `low` | `stage2_approved | focus_diff | keywords_diff | summary_diff`
- `링크업솔루션 주식회사` | `AI Engineer` | `low` | `stage2_approved | focus_diff | keywords_diff | summary_diff`
- `마키나락스` | `Forward Deployed Engineer - LLM` | `low` | `stage2_approved | business_context_in_ai_role`
- `메디컬에이아이` | `메디컬그룹 DS(Data Science)팀 연구원` | `low` | `stage2_approved | role_diff | focus_diff | keywords_diff | summary_diff`

## Outputs

- json: `/Users/junheelee/Desktop/career_dashboard/data/stage2_quality_triage_latest.json`
- md: `/Users/junheelee/Desktop/career_dashboard/docs/stage2_quality_triage_latest.md`
