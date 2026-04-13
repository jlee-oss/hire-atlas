# 리뷰 의사결정 시트

- 대상 공고: `14`
- 기본 권장값은 `recommendedDecision`에 들어 있습니다.
- 가능한 결정값: `approve_draft`, `approve_low`, `approve_current`, `needs_edit`, `skip`
- `needs_edit`를 쓰는 경우 `manualSummary / manualFocusLabel / manualKeywords / manualQuality`를 같이 채우면 됩니다.

## 빠른 해석

- `approve_draft`: assistant draft를 그대로 검수값으로 승인
- `approve_low`: low 유지가 맞다고 승인
- `approve_current`: 현재 모델 출력이 충분히 맞다고 승인
- `needs_edit`: 사람이 직접 수정해서 확정
- `skip`: 지금은 반영하지 않음

- 메디컬에이아이 | 메디컬그룹 DS(Data Science)팀 연구원 -> 권장 `approve_draft`
- 뷰노 | (전문연지원가능) AI Research Engineer / Scientist -> 권장 `approve_draft`
- 엔젤로보틱스 | 개발 | 플래닛 서울/ 플래닛 대전 [신입/경력] 전문연구요원 상시 모집 - AI Researcher (Artificial Intelligence (인공지능)) -> 권장 `approve_draft`
- 워트인텔리전스 | Senior AI Engineer (LLM / NLP / MLOps) -> 권장 `approve_draft`
- 당근 | Data Analyst -> 권장 `approve_draft`
- 쿠팡 | Growth Marketing - Coupang Pay -> 권장 `approve_draft`
- 크로프트 | Digital Agriculture Consultant -> 권장 `approve_draft`
- 네이버 | [네이버랩스] Generative AI Research Engineer -> 권장 `approve_draft`
- 노타 | [Solution] AI Software Engineer Intern (전환형) -> 권장 `approve_draft`
- 다온에이치앤에스 | [개발] Node.js 프로젝트 개발자 채용 (모집중) -> 권장 `approve_draft`
- 노타 | Talent Pool (R&D) -> 권장 `approve_low`
- 노타 | 전문연구요원 (R&D) -> 권장 `approve_low`
- 몰로코 | Senior Applied Scientist (시니어 응용 과학자) -> 권장 `approve_low`
- 한국뇌연구원 실증지원사업단 | [AI실증지원사업단] [A-21](연구직) 2025년 제4차 사업단 직원(계약직) 채용 -> 권장 `approve_low`

