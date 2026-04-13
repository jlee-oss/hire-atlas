# 더 강한 모델 비교

- 생성 시각: `2026-04-07T13:22:08.546205+00:00`
- baseline model: `qwen2.5:3b`
- candidate model: `qwen2.5:7b`
- 비교 웨이브: `/Users/junheelee/Desktop/career_dashboard/data/review_wave_001.json`
- 겹치는 항목 수: `9`
- quality 개선: `3`
- quality 악화: `0`
- low -> non-low 개선: `2`

## 현재 판단

- review hard set 기준으로는 더 강한 모델이 확실히 유리합니다.
- 특히 low에서 medium/high로 올라간 케이스가 실제로 보입니다.
- 다만 원문 자체가 얇은 공고는 더 강한 모델에서도 low로 남습니다.
- 따라서 다음 검수 기준 모델은 더 강한 모델로 두는 것이 맞습니다.

## 개선된 대표 케이스

- `2a805a7ba0ec84b09ef7fb1a16fa7be61dad3cbfbc70b24d187c13e53c621798`
  baseline: `low` / 인공지능 모델 개발 엔엘피 엘엘엠 기반 / TensorFlow
  candidate: `medium` / MLOps 기반 인공지능 모델 개발 / TensorFlow
- `981269a67a0d9f0d961fd4ca48cd9134cdb6028adf125f6a3d42cb3faf0152b4`
  baseline: `medium` / 실내외 환경에서 객체 인식 및 영상 처리 알고리즘을 개발합니다 / 객체 인식
  candidate: `high` / 딥러닝 기반 객체 인식 알고리즘 연구 / 컴퓨터 비전
- `c7566b4fd5f33aae584d6b7fce0d7528831ea047e4aaeae349880e3638767c30`
  baseline: `low` / 심전도 기반 AI 연구원 / 의료 데이터
  candidate: `medium` / 심전도 기반 인공지능 데이터 분석 및 연구 전반을 주도합니다 / 의료 데이터

