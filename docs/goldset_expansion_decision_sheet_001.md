# 골드셋 확장 의사결정 시트 001

- 대상 공고: `48`
- 이 시트는 `raw extractor 결과(current)`와 `board projection 결과(draft)`를 함께 비교합니다.
- 가능한 결정값: `approve_draft`, `approve_low`, `approve_current`, `needs_edit`, `skip`
- `needs_edit`일 때만 `manualSummary / manualFocusLabel / manualKeywords / manualQuality`를 채우면 됩니다.

## 추천 결정 분포

- `approve_current`: `2`
- `approve_draft`: `31`
- `approve_low`: `10`
- `needs_edit`: `5`

## 이유 분포

- `broad_focus`: `20`
- `domain_specific`: `12`
- `focus_keyword_conflict`: `6`
- `low_or_empty`: `10`

## broad_focus

- `당근` | `Data Analytics Engineer | 테크코어 (데이터 가치화)` | raw `클라우드` -> board `데이터 마트` | 권장 `approve_draft`
- `여기어때` | `Data Analyst [Business Insight]` | raw `그로스 마케팅` -> board `대시보드` | 권장 `approve_draft`
- `여기어때` | `Performance Marketer` | raw `마케팅` -> board `트래킹` | 권장 `approve_draft`
- `채널코퍼레이션` | `Business Analyst` | raw `그로스 마케팅` -> board `대시보드` | 권장 `approve_draft`
- `쿠팡` | `Growth Marketing - Coupang Pay` | raw `제품 성장 분석` -> board `고객 관계 관리` | 권장 `approve_draft`
- `메디컬에이아이` | `메디컬그룹 DS(Data Science)팀 연구원` | raw `심전도` -> board `의료 데이터` | 권장 `approve_draft`
- `신세계` | `[신세계아이앤씨] 데이터분석(데이터사이언스) 인재모집(채용 시 마감)` | raw `클라우드` -> board `의료 데이터` | 권장 `approve_draft`
- `엑셈` | `Data Scientist 채용 (5년 이상)` | raw `RAG` -> board `RAG` | 권장 `approve_draft`
- `네이버` | `[네이버랩스] Generative AI Research Engineer` | raw `컴퓨터 비전` -> board `3D 공간 이해` | 권장 `approve_draft`
- `딥노이드` | `임상연구전문가 (Clinical Research Scientist)` | raw `의료` -> board `의료 데이터` | 권장 `approve_draft`
- `뷰노` | `(전문연지원가능) AI Research Engineer / Scientist` | raw `생체신호` -> board `생체신호` | 권장 `approve_draft`
- `크래프톤` | `[AI Research Div.] Postdoctoral Researcher - LLMs (계약직)` | raw `컴퓨터 비전` -> board `컴퓨터 비전` | 권장 `needs_edit`
- `크래프톤` | `[AI Research Div.] Research Scientist Intern - 독자 AI 파운데이션 모델 (2년 이상 / 인턴)` | raw `컴퓨터 비전` -> board `컴퓨터 비전` | 권장 `needs_edit`
- `퓨리오사` | `Algorithm - AI Research Engineer` | raw `컴퓨터 비전` -> board `컴퓨터 비전` | 권장 `needs_edit`
- `노타` | `[Solution] AI Software Engineer Intern (전환형)` | raw `클라우드` -> board `컴퓨터 비전` | 권장 `approve_draft`
- `센드버드` | `AI Agent Engineer, Intern` | raw `RAG` -> board `RAG` | 권장 `approve_draft`
- `센드버드` | `Applied AI Engineer` | raw `LLM` -> board `RAG` | 권장 `approve_draft`
- `씨어스테크놀로지` | `[경력] Data Engineer` | raw `생체신호` -> board `의료 데이터` | 권장 `approve_draft`
- `업스테이지` | `AI Model Production - Document AI` | raw `컴퓨터 비전` -> board `인프라` | 권장 `approve_draft`
- `카카오모빌리티` | `AI 엔지니어` | raw `클라우드` -> board `MLOps` | 권장 `approve_draft`

## domain_specific

- `여기어때` | `CRM Team Leader` | raw `제품 성장 분석` -> board `고객 관계 관리` | 권장 `approve_draft`
- `크로프트` | `Digital Agriculture Consultant` | raw `디지털 농업` -> board `데이터 분석` | 권장 `approve_draft`
- `엔젤로보틱스` | `개발 | 플래닛 서울/ 플래닛 대전 [신입/경력] 전문연구요원 상시 모집 - Data Scientist (Data (데이터))` | raw `로보틱스` -> board `클라우드` | 권장 `approve_draft`
- `딥노이드` | `AI Researcher (Multimodal)` | raw `컴퓨터 비전` -> board `의료 데이터` | 권장 `approve_draft`
- `메디컬에이아이` | `상시채용 R&D Center AI Group` | raw `생체신호` -> board `생체신호` | 권장 `approve_current`
- `엔젤로보틱스` | `개발 | 플래닛 서울/ 플래닛 대전 [신입/경력] 전문연구요원 상시 모집 - AI Researcher (Artificial Intelligence (인공지능))` | raw `로보틱스` -> board `검색` | 권장 `approve_draft`
- `서울로보틱스` | `Software Engineer - General Software Engineering` | raw `컴퓨터 비전` -> board `자율주행` | 권장 `approve_draft`
- `스캐터랩` | `Site Reliability Engineer (DevOps)` | raw `클라우드` -> board `인프라` | 권장 `approve_draft`
- `아키드로우` | `Robotics Simulation & Data Engineer (Isaac Sim / ROS)` | raw `로보틱스` -> board `3D 공간 이해` | 권장 `approve_draft`
- `이지케어텍` | `[경력] 연구소 MLOps Engineer 채용` | raw `클라우드` -> board `의료 데이터` | 권장 `approve_draft`
- `카카오모빌리티` | `자율주행 AI 엔지니어 (R&D)` | raw `자율주행` -> board `자율주행` | 권장 `approve_current`
- `쿠팡` | `Sr.Staff, Back-end Engineer (Fintech Product Engineering)` | raw `클라우드` -> board `RAG` | 권장 `approve_draft`

## focus_keyword_conflict

- `쿠팡` | `[쿠팡이츠서비스] 배달파트너 CX 운영 담당자` | raw `운영 관리` -> board `임베디드 최적화` | 권장 `approve_draft`
- `리벨리온` | `NPU Library Software Engineer` | raw `컴퓨터 비전` -> board `음성인식` | 권장 `approve_draft`
- `신세계` | `[신세계아이앤씨] AI서비스개발 직무 인재모집(채용 시 마감)` | raw `RAG` -> board `RAG` | 권장 `needs_edit`
- `업스테이지` | `Platform Software Engineer` | raw `인프라` -> board `인프라` | 권장 `needs_edit`
- `인이지` | `[INEEJI] 소프트웨어 엔지니어 경력자 채용` | raw `아키텍처` -> board `클라우드` | 권장 `approve_draft`
- `인터엑스` | `Head of Physical AI` | raw `로보틱스` -> board `인프라` | 권장 `approve_draft`

## low_or_empty

- `몰로코` | `Senior Applied Scientist (시니어 응용 과학자)` | raw `-` -> board `-` | 권장 `approve_low`
- `노타` | `Talent Pool (R&D)` | raw `-` -> board `-` | 권장 `approve_low`
- `노타` | `전문연구요원 (R&D)` | raw `-` -> board `-` | 권장 `approve_low`
- `쓰리디랩스` | `채용공고` | raw `-` -> board `-` | 권장 `approve_low`
- `한국뇌연구원 실증지원사업단` | `[AI실증지원사업단] [A-21](연구직) 2025년 제4차 사업단 직원(계약직) 채용` | raw `-` -> board `-` | 권장 `approve_low`
- `다온에이치앤에스` | `[개발] Node.js 프로젝트 개발자 채용 (모집중)` | raw `-` -> board `-` | 권장 `approve_low`
- `데이터메이커` | `AI개발자_프론트엔드` | raw `-` -> board `-` | 권장 `approve_low`
- `링크업솔루션 주식회사` | `AI Engineer` | raw `-` -> board `-` | 권장 `approve_low`
- `코그로보` | `Recruitment` | raw `문제 해결` -> board `문제 해결` | 권장 `approve_low`
- `트위그팜` | `Twigfarm Official Website` | raw `-` -> board `-` | 권장 `approve_low`

