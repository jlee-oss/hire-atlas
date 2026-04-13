# Full Dataset Validation Harness

- generatedAt: `2026-04-12T05:19:14.735510+00:00`
- sourceJobs: `172`
- displayJobs: `158`
- excludedJobs: `14`
- reviewJobs: `11`
- summaryCoverage: `151`
- missingSummaries: `7`
- staleRoleOverrides: `0`
- staleServiceScopeOverrides: `38`

## Anomaly Families

### excluded_leaked_into_display

- severity: `high`
- count: `0`

### deeptech_in_data_analyst

- severity: `high`
- count: `0`

### deeptech_context_present

- severity: `info`
- count: `0`

### business_in_engineer_family

- severity: `high`
- count: `0`

### business_context_present

- severity: `info`
- count: `1`
- `당근` | `[2026 당근 ML] Software Engineer, Machine Learning (석사)` | `인공지능 엔지니어` | `추천 시스템` | business/ops context present under engineer/research/science

### tool_first_focus

- severity: `high`
- count: `0`

### service_scope_review_in_display

- severity: `high`
- count: `0`

### broad_focus_specificity_gap

- severity: `medium`
- count: `1`
- `딥노이드` | `Application Developer (Medical AI)` | `인공지능 엔지니어` | `클라우드` | focus is broad but more specific signal exists: 의료
