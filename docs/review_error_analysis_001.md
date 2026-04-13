# 리뷰 오류 분석

- 검수 반영 공고: `14`

## 주요 오류 축

- `keywords_rewrite`: `14`
- `summary_rewrite`: `14`
- `focus_relabel`: `10`
- `keywords_not_groupable`: `10`
- `summary_not_board_ready`: `8`
- `focus_semantic_mismatch`: `6`
- `summary_title_like`: `6`
- `keep_low`: `4`
- `source_not_actionable`: `3`
- `focus_too_broad_or_generic`: `2`
- `source_too_sparse`: `1`

## 해석

- `summary_rewrite`가 전건에 걸쳐 발생했다는 것은 현재 모델의 요약문이 게시용 문구로는 거의 통과하지 못한다는 뜻입니다.
- `keywords_rewrite`도 전건에 가깝게 발생해, 현재 keywords는 그룹 기준어보다 보조 신호 수준에 머물러 있습니다.
- `focus_relabel`은 일부만 유지됐고, 나머지는 더 구체적이거나 더 적절한 도메인 축으로 바뀌었습니다.
- `keep_low`는 원문이 빈약하거나 공고 자체가 운영/안내 문구 중심인 케이스라, 억지 요약보다 low 유지 전략이 맞았음을 보여줍니다.

## 대표 사례

- 뷰노 | (전문연지원가능) AI Research Engineer / Scientist
  issues: summary_rewrite, summary_not_board_ready, keywords_rewrite, keywords_not_groupable
  current: `신호 처리 및 인공지능 연구` / `인공지능 리서처`
  corrected: `생체신호 처리와 신뢰도 평가 알고리즘 개발` / `생체신호`
- 한국뇌연구원 실증지원사업단 | [AI실증지원사업단] [A-21](연구직) 2025년 제4차 사업단 직원(계약직) 채용
  issues: summary_rewrite, summary_title_like, focus_relabel, keywords_rewrite, keep_low, source_not_actionable
  current: `인공지능 연구` / `인공지능실증지원사업단`
  corrected: `(empty)` / `(empty)`
- 네이버 | [네이버랩스] Generative AI Research Engineer
  issues: summary_rewrite, summary_not_board_ready, keywords_rewrite, keywords_not_groupable
  current: `대규모 실외 데이터 기반의 차세대 인공지능 연구` / `컴퓨터 비전`
  corrected: `실외 시공간 데이터 기반 생성형 AI 연구` / `컴퓨터 비전`
- 쿠팡 | Growth Marketing - Coupang Pay
  issues: summary_rewrite, summary_title_like, focus_relabel, focus_semantic_mismatch, keywords_rewrite, keywords_not_groupable
  current: `앱 성장 데이터 분석가` / `앱 마케팅`
  corrected: `앱 성장 채널 운영과 리텐션 최적화` / `그로스 마케팅`
- 메디컬에이아이 | 메디컬그룹 DS(Data Science)팀 연구원
  issues: summary_rewrite, summary_not_board_ready, focus_relabel, focus_semantic_mismatch, keywords_rewrite, keywords_not_groupable
  current: `심전도 기반 인공지능 데이터 분석 연구` / `직무내용`
  corrected: `심전도·임상 데이터 분석과 코호트 구축` / `심전도`
- 엔젤로보틱스 | 개발 | 플래닛 서울/ 플래닛 대전 [신입/경력] 전문연구요원 상시 모집 - AI Researcher (Artificial Intelligence
(인공지능))
  issues: summary_rewrite, summary_not_board_ready, focus_relabel, focus_semantic_mismatch, keywords_rewrite, keywords_not_groupable
  current: `개발 | 플래닛 서울/ 플래닛 대전 [신입/경력] 전문연구요원 상시 모집 - AI Researcher (Artifi` / `휴먼`
  corrected: `로봇 제어 강화학습과 동작 인식 연구` / `로보틱스`
- 노타 | Talent Pool (R&D)
  issues: summary_rewrite, summary_title_like, focus_relabel, keywords_rewrite, keep_low, source_not_actionable
  current: `Talent Pool (R&D)` / `컴퓨터비전`
  corrected: `(empty)` / `(empty)`
- 당근 | Data Analyst
  issues: summary_rewrite, summary_title_like, focus_relabel, focus_semantic_mismatch, keywords_rewrite, keywords_not_groupable
  current: `Data Analyst` / `파이썬`
  corrected: `제품 성장 지표 설계와 실험 분석` / `제품 성장 분석`
- 몰로코 | Senior Applied Scientist (시니어 응용 과학자)
  issues: summary_rewrite, summary_title_like, focus_relabel, focus_too_broad_or_generic, keywords_rewrite, keep_low, source_too_sparse
  current: `Senior Applied Scientist (시니어 응용 과학자)` / `별도`
  corrected: `(empty)` / `(empty)`
- 노타 | 전문연구요원 (R&D)
  issues: summary_rewrite, summary_title_like, focus_relabel, keywords_rewrite, keep_low, source_not_actionable
  current: `전문연구요원 (R&D)` / `모든`
  corrected: `(empty)` / `(empty)`
- 노타 | [Solution] AI Software Engineer Intern (전환형)
  issues: summary_rewrite, summary_not_board_ready, keywords_rewrite, keywords_not_groupable
  current: `컴퓨터비전 모델과 브이엘엠 을 활용한 인공지능 비전 솔루션 설계·개발` / `컴퓨터 비전`
  corrected: `컴퓨터비전·VLM 기반 비전 솔루션 설계와 개발` / `컴퓨터 비전`
- 워트인텔리전스 | Senior AI Engineer (LLM / NLP / MLOps)
  issues: summary_rewrite, summary_not_board_ready, focus_relabel, focus_too_broad_or_generic, focus_semantic_mismatch, keywords_rewrite, keywords_not_groupable
  current: `인공지능 모델 및 시스템 개발` / `MLOps`
  corrected: `LLM 검색 시스템 설계와 성능 개선` / `RAG`
- 다온에이치앤에스 | [개발] Node.js 프로젝트 개발자 채용 (모집중)
  issues: summary_rewrite, summary_not_board_ready, keywords_rewrite, keywords_not_groupable
  current: `인공지능 솔루션 개발 및 실무 운영 경험이 있어야` / `클라우드`
  corrected: `클라우드 환경 서비스 개발과 운영` / `클라우드`
- 크로프트 | Digital Agriculture Consultant
  issues: summary_rewrite, summary_not_board_ready, focus_relabel, focus_semantic_mismatch, keywords_rewrite, keywords_not_groupable
  current: `디지털 농업 플랫폼 구현 및 지원` / `디지털 농업 플랫폼 전문성`
  corrected: `디지털 농업 플랫폼 도입과 현장 컨설팅` / `디지털 농업`

