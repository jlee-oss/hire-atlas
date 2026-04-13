#!/usr/bin/env python3

import hashlib
import json
import os
import pathlib
import re
import urllib.request
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
ENRICHMENTS_PATH = ROOT / "data" / "ai_enrichment_results.json"
SUMMARIES_PATH = ROOT / "data" / "job_summaries.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
TONE_LEGEND_PATH = ROOT / "data" / "tone_legend.json"
COMPANY_CLUSTERS_PATH = ROOT / "data" / "company_clusters.json"
RELEASE_CONFIG_PATH = ROOT / "data" / "model_release_config.json"

SUMMARY_NOISE_PATTERNS = [
    r"^운영시간$",
    r"^지원 전,?\s*확인해주세요!?$",
    r"^읽어보면 도움 되는 관련 자료$",
    r"^채용 관련 문의사항.*$",
    r"^제출하신 .*",
    r"^필요 시 .*",
    r"^입사 후 .*",
    r"^서류.*합격.*$",
    r"^경험이 없거나.*$",
    r"^경험 직접 작성하기$",
    r"^경험이 있고.*$",
    r"^로 보내주세요\.?$",
    r"^\(.*로그인.*\)$",
    r"^\(.*문의 가능.*\)$",
    r"^&\s.*$",
    r"^\(.*\)$",
]
DETAIL_NOISE_PATTERNS = [
    r"^관련 분야 .*학위.*$",
    r"^관련 분야 .*경험.*$",
    r"^아래 분야 .*경험.*$",
    r"^학력은 .*",
    r"^신입 또는.*$",
    r"^[0-9]+년 이상 .*",
    r"^유관 업무 경력.*$",
    r"^채용하고 싶은 사람.*$",
    r"^스스로 성장.*$",
    r"^각자의 전문성을 .*",
    r"^해외여행에 .*",
    r"^남성은 .*",
    r"^취업보호대상자는 .*",
    r"^.*우대합니다\.?$",
    r"^.*있으면 좋습니다\.?$",
    r"^.*필요합니다\.?$",
    r"^.*요구됩니다\.?$",
    r"^.*경험이 있어야 합니다\.?$",
    r"^.*역량을 갖춰야 합니다\.?$",
    r"^.*능력이 요구됩니다\.?$",
]
FIELD_LINE_NOISE_PATTERNS = [
    r"^직무내용$",
    r"^공고명[:：].*$",
    r"^\(공고문\).*$",
    r"^\(양식\).*$",
    r"^별도 우대사항 미기재$",
    r"^참고해 주세요$",
    r"^지원 전,?\s*확인해주세요!?$",
    r"^채용 관련 문의사항.*$",
    r"^제출하신 내용에 허위 사실.*$",
    r"^필요 시 레퍼런스 체크.*$",
    r"^서류 검토.*최종 선발$",
    r"^노타 채용 과정.*$",
    r"^노타와 신규 입사자가.*$",
    r"^노타는 핵심 가치.*$",
    r"^워트만의 이야기.*$",
    r"^인공지능: 기술 리서치의 새로운 기준.*$",
    r"^모든 포지션에서 .*근무가 가능합니다.*$",
    r"^을 통해 입사한 지원자.*$",
    r"^로 보내주세요\.?$",
    r"^혜택 및 복지$",
    r"^⏩ 채용 전형$",
    r"^서류 전형.*$",
    r"^정규직 채용의 경우.*$",
    r"^전형 시 우대하고 있어요$",
    r"^근무 환경$",
    r"^초역세권 위치.*$",
    r"^.*출근 시간 조정.*$",
    r"^업무 몰입 지원.*$",
    r"^워트 멤버들의 성장.*$",
    r"^사용 언어는 .*진행되어요$",
]
GENERIC_FRAGMENT_PATTERNS = [
    r"^(개발|연구|수행|담당|운영|관리|구현|분석|지원|개선)합니다\.?$",
    r"^(개발|연구|수행|담당|운영|관리|구현|분석|지원|개선)$",
    r"^(통합|검증|최적화|운영|관리|구축)$",
    r"^요 연구 영역은 다음과 같습니다\.?$",
    r"^해당 직무$",
    r"^신입 또는$",
    r"^및$",
    r"^등을 사용합니다\.?$",
    r"^찾습니다\.?$",
]
GENERIC_KEYWORD_PATTERNS = [
    r"^ai$",
    r"^인공지능$",
    r"^엔지니어$",
    r"^리서처$",
    r"^개발$",
    r"^연구$",
    r"^분석$",
    r"^데이터$",
    r"^모델$",
    r"^기반$",
    r"^위한$",
    r"^또는$",
    r"^관련$",
    r"^경력$",
    r"^신입$",
    r"^학력$",
    r"^학위$",
    r"^(학사|석사|박사)$",
    r"^전공$",
    r"^요건$",
    r"^자격$",
    r"^우대$",
    r"^필수$",
    r"^제품$",
    r"^서비스$",
    r"^인공지능\s*(엔지니어|리서처)$",
    r"^ai\s*(engineer|researcher)$",
    r"^경험자$",
    r"^가능자$",
    r"^이상이신$",
    r"^채용절차법$",
    r"^우대합니다$",
    r"^있습니다\.?$",
]

WEAK_KEYWORD_SUFFIXES = (
    "위한",
    "또는",
    "기반",
    "관련",
    "중심",
    "가능",
    "경험",
    "학력",
    "학위",
)

WEAK_FOCUS_LABEL_PATTERNS = [
    r"^(ai|인공지능)\s*(엔지니어|리서처|연구원|연구자)$",
    r"^(데이터|소프트웨어)\s*(엔지니어|리서처|사이언티스트|분석가)$",
    r"^(엔지니어|리서처|연구원|연구자|분석가|사이언티스트)$",
]

WEAK_FOCUS_LABEL_TERMS = {
    "사업",
    "소프트웨어",
    "데이터 처리",
    "처리",
    "분석",
    "개발",
    "연구",
    "엔지니어링",
}

FOCUS_SIGNAL_HINTS = (
    "llm",
    "rag",
    "onnx",
    "npu",
    "gpu",
    "cuda",
    "triton",
    "pytorch",
    "tensorflow",
    "kubernetes",
    "docker",
    "spark",
    "sql",
    "python",
    "파이토치",
    "텐서플로",
    "컴퓨터비전",
    "컴퓨터 비전",
    "자율주행",
    "로봇",
    "의료",
    "헬스케어",
    "생체신호",
    "파이프라인",
    "서빙",
    "아키텍처",
    "고객 관계 관리",
    "마케팅",
    "crm",
    "검증",
    "테스트벤치",
    "멀티모달",
    "검색",
    "추천",
    "데이터셋",
    "실험",
    "최적화",
    "온디바이스",
    "심전도",
    "EMR",
    "그로스 마케팅",
    "제품 성장 분석",
    "로보틱스",
    "클라우드",
    "디지털 농업",
)
SIGNAL_KEEP_HINTS = (
    "llm",
    "rag",
    "onnx",
    "vlm",
    "nlp",
    "mlops",
    "aws",
    "linux",
    "cloud",
    "클라우드",
    "파이프라인",
    "서빙",
    "컴퓨터 비전",
    "자율주행",
    "로봇",
    "로보틱스",
    "강화 학습",
    "시뮬레이션",
    "동작 인식",
    "의료",
    "헬스케어",
    "생체신호",
    "심전도",
    "EMR",
    "환자 모니터링",
    "고객 관계 관리",
    "crm",
    "리텐션",
    "퍼널",
    "코호트",
    "그로스",
    "마케팅",
    "A/B 테스트",
    "제품 성장",
    "디지털 농업",
    "농업",
    "GIS",
    "위성",
    "센서",
    "현장 데이터",
    "BigQuery",
    "SQL",
    "Python",
    "PyTorch",
    "TensorFlow",
    "실증",
    "검색",
    "추천",
    "멀티모달",
)

CANONICAL_TERM_MAP = {
    "엘엘엠": "LLM",
    "llm": "LLM",
    "브이엘엠": "VLM",
    "vlm": "VLM",
    "엔엘피": "NLP",
    "nlp": "NLP",
    "검색증강생성": "RAG",
    "검색 증강 생성": "RAG",
    "엠엘옵스": "MLOps",
    "mlops": "MLOps",
    "오엔엔엑스": "ONNX",
    "onnx": "ONNX",
    "파이토치": "PyTorch",
    "pytorch": "PyTorch",
    "텐서플로": "TensorFlow",
    "tensorflow": "TensorFlow",
    "에스큐엘": "SQL",
    "sql": "SQL",
    "에이비 테스트": "A/B 테스트",
    "a/b 테스트": "A/B 테스트",
    "빅쿼리": "BigQuery",
    "bigquery": "BigQuery",
    "앰플리튜드": "Amplitude",
    "amplitude": "Amplitude",
    "에이더블유에스": "AWS",
    "aws": "AWS",
    "리눅스": "Linux",
    "linux": "Linux",
    "이엠알": "EMR",
    "emr": "EMR",
    "전자의무기록": "EMR",
    "이씨지": "심전도",
    "ecg": "심전도",
    "지아이에스": "GIS",
    "gis": "GIS",
    "에이에이알알알": "AARRR",
    "깃허브": "GitHub",
    "컴퓨터비전": "컴퓨터 비전",
    "고객 관계관리": "고객 관계 관리",
    "자율 주행": "자율주행",
    "온 디바이스": "온디바이스",
    "에스디케이": "SDK",
    "브이엘엠 솔루션": "VLM",
    "3 비전": "3D 비전",
    "강화 학습": "강화학습",
}
INLINE_TERM_REPLACEMENTS = [
    (re.compile(r"엘엘엠", re.IGNORECASE), "LLM"),
    (re.compile(r"\bllm\b", re.IGNORECASE), "LLM"),
    (re.compile(r"브이엘엠", re.IGNORECASE), "VLM"),
    (re.compile(r"\bvlm\b", re.IGNORECASE), "VLM"),
    (re.compile(r"엔엘피", re.IGNORECASE), "NLP"),
    (re.compile(r"\bnlp\b", re.IGNORECASE), "NLP"),
    (re.compile(r"검색\s*증강\s*생성", re.IGNORECASE), "RAG"),
    (re.compile(r"검색증강생성", re.IGNORECASE), "RAG"),
    (re.compile(r"\brag\b", re.IGNORECASE), "RAG"),
    (re.compile(r"엠엘옵스", re.IGNORECASE), "MLOps"),
    (re.compile(r"\bmlops\b", re.IGNORECASE), "MLOps"),
    (re.compile(r"오엔엔엑스", re.IGNORECASE), "ONNX"),
    (re.compile(r"\bonnx\b", re.IGNORECASE), "ONNX"),
    (re.compile(r"파이토치", re.IGNORECASE), "PyTorch"),
    (re.compile(r"\bpytorch\b", re.IGNORECASE), "PyTorch"),
    (re.compile(r"텐서플로", re.IGNORECASE), "TensorFlow"),
    (re.compile(r"\btensorflow\b", re.IGNORECASE), "TensorFlow"),
    (re.compile(r"에스큐엘", re.IGNORECASE), "SQL"),
    (re.compile(r"\bsql\b", re.IGNORECASE), "SQL"),
    (re.compile(r"에이비\s*테스트", re.IGNORECASE), "A/B 테스트"),
    (re.compile(r"a/b\s*테스트", re.IGNORECASE), "A/B 테스트"),
    (re.compile(r"빅쿼리", re.IGNORECASE), "BigQuery"),
    (re.compile(r"\bbigquery\b", re.IGNORECASE), "BigQuery"),
    (re.compile(r"앰플리튜드", re.IGNORECASE), "Amplitude"),
    (re.compile(r"\bamplitude\b", re.IGNORECASE), "Amplitude"),
    (re.compile(r"에이더블유에스", re.IGNORECASE), "AWS"),
    (re.compile(r"\baws\b", re.IGNORECASE), "AWS"),
    (re.compile(r"리눅스", re.IGNORECASE), "Linux"),
    (re.compile(r"\blinux\b", re.IGNORECASE), "Linux"),
    (re.compile(r"이엠알", re.IGNORECASE), "EMR"),
    (re.compile(r"\bemr\b", re.IGNORECASE), "EMR"),
    (re.compile(r"전자의무기록", re.IGNORECASE), "EMR"),
    (re.compile(r"이씨지", re.IGNORECASE), "심전도"),
    (re.compile(r"\becg\b", re.IGNORECASE), "심전도"),
    (re.compile(r"지아이에스", re.IGNORECASE), "GIS"),
    (re.compile(r"\bgis\b", re.IGNORECASE), "GIS"),
    (re.compile(r"에이에이알알알", re.IGNORECASE), "AARRR"),
    (re.compile(r"컴퓨터비전", re.IGNORECASE), "컴퓨터 비전"),
    (re.compile(r"3\s*비전", re.IGNORECASE), "3D 비전"),
    (re.compile(r"고객 관계관리", re.IGNORECASE), "고객 관계 관리"),
    (re.compile(r"자율\s*주행", re.IGNORECASE), "자율주행"),
    (re.compile(r"온\s*디바이스", re.IGNORECASE), "온디바이스"),
    (re.compile(r"에스디케이", re.IGNORECASE), "SDK"),
    (re.compile(r"깃허브", re.IGNORECASE), "GitHub"),
]

SUMMARY_HINT_LABELS = [
    ("onnx", "ONNX"),
    ("오엔엔엑스", "ONNX"),
    ("llm", "LLM"),
    ("vlm", "VLM"),
    ("nlp", "NLP"),
    ("rag", "RAG"),
    ("검색증강생성", "RAG"),
    ("하이브리드 검색", "RAG"),
    ("컴퓨터 비전", "컴퓨터 비전"),
    ("컴퓨터비전", "컴퓨터 비전"),
    ("객체 인식", "객체 인식"),
    ("vslam", "3D 공간 이해"),
    ("자율주행", "자율주행"),
    ("자율 주행", "자율주행"),
    ("고객 관계 관리", "고객 관계 관리"),
    ("crm", "고객 관계 관리"),
    ("데이터 마트", "데이터 마트"),
    ("마트 테이블", "데이터 마트"),
    ("마트 데이터", "데이터 마트"),
    ("대시보드", "대시보드"),
    ("태블로", "대시보드"),
    ("슈퍼셋", "대시보드"),
    ("씨아이씨디", "CI/CD"),
    ("릴리스 자동화", "CI/CD"),
    ("모델 서빙", "모델 서빙"),
    ("gpu 스케줄링", "모델 서빙"),
    ("mlops", "MLOps"),
    ("엠엘옵스", "MLOps"),
    ("양자화", "양자화"),
    ("사후학습", "사후학습"),
    ("의료 데이터", "의료 데이터"),
    ("의료영상", "의료 데이터"),
    ("임상", "의료 데이터"),
    ("npu", "NPU 적용"),
    ("파이프라인", "파이프라인"),
    ("테스트 자동화", "테스트 자동화"),
    ("시스템 아키텍처", "시스템 아키텍처"),
    ("아키텍처", "시스템 아키텍처"),
    ("마케팅", "마케팅"),
    ("의료", "의료"),
    ("생체신호", "생체신호"),
    ("심전도", "심전도"),
    ("헬스케어", "헬스케어"),
    ("실증", "실증"),
    ("사업 개발", "사업 개발"),
    ("fp&a", "재무 계획 분석"),
    ("financial planning", "재무 계획 분석"),
    ("손익", "재무 계획 분석"),
    ("재무 모델", "재무 계획 분석"),
    ("비용 편익", "재무 계획 분석"),
    ("process innovation", "프로세스 혁신"),
    ("전사 프로세스", "프로세스 혁신"),
    ("표준 운영 절차", "프로세스 혁신"),
    ("업무 자동화", "프로세스 혁신"),
    ("플랫폼 운영", "플랫폼 운영"),
    ("작품 운영", "플랫폼 운영"),
    ("웹툰 플랫폼", "웹툰 플랫폼"),
    ("광고 데이터", "광고 데이터"),
    ("캠페인 성과", "광고 성과 분석"),
    ("모델 변환", "모델 최적화"),
    ("연산자 호환성", "모델 최적화"),
    ("온디바이스", "온디바이스 최적화"),
    ("검색", "검색"),
    ("추천", "추천"),
]
FOCUS_COMPOSITE_RULES = [
    {
        "label": "LLM 해석",
        "all": ["LLM"],
        "any": ["작동 원리", "모델 해석", "표현 학습", "스케일링 법칙", "일반화 성능", "추론 능력", "모델 아키텍처"],
    },
    {
        "label": "모델 해석",
        "any": ["모델 해석", "표현 학습", "스케일링 법칙", "작동 원리"],
    },
    {
        "label": "RAG",
        "any": ["RAG", "검색", "벡터 데이터베이스", "검색증강생성", "하이브리드 검색"],
    },
    {
        "label": "데이터 마트",
        "any": ["데이터 마트", "마트 데이터", "마트 테이블", "mart"],
    },
    {
        "label": "대시보드",
        "any": ["대시보드", "Tableau", "Superset", "BI", "태블로", "슈퍼셋"],
    },
    {
        "label": "심전도",
        "any": ["심전도", "ECG"],
    },
    {
        "label": "생체신호",
        "any": ["생체신호", "신호 처리", "환자 모니터링"],
    },
    {
        "label": "재무 계획 분석",
        "any": ["FP&A", "Financial Planning", "손익", "재무 모델", "비용-편익", "ROI", "실적 예측", "재무 예측"],
    },
    {
        "label": "프로세스 혁신",
        "any": ["Process Innovation", "전사 프로세스", "표준 운영 절차", "SOP", "운영 표준화", "업무 자동화", "KPI", "OKR"],
    },
    {
        "label": "플랫폼 운영",
        "all": ["플랫폼"],
        "any": ["운영", "프로모션", "작품 운영", "서비스 운영"],
    },
    {
        "label": "웹툰 플랫폼",
        "all": ["플랫폼"],
        "any": ["웹툰", "웹소설", "작품 운영", "프로모션"],
    },
    {
        "label": "그로스 마케팅",
        "any": ["퍼포먼스 마케팅", "리텐션", "앱 스토어 최적화", "리워드", "유저 획득", "캠페인 최적화"],
    },
    {
        "label": "그로스 마케팅",
        "all": ["CRM"],
        "any": ["리텐션", "퍼널", "코호트", "캠페인", "획득", "활성", "앱"],
    },
    {
        "label": "제품 성장 분석",
        "all": ["A/B 테스트"],
        "any": ["제품", "사용자", "퍼널", "코호트", "성장"],
    },
    {
        "label": "광고 데이터",
        "all": ["광고"],
        "any": ["데이터 파이프라인", "데이터 거버넌스", "SQL", "쿼리", "Ads Ops"],
    },
    {
        "label": "광고 성과 분석",
        "all": ["광고"],
        "any": ["캠페인 성과", "캠페인 최적화", "모바일 앱 추적", "통계 분석", "데이터 시각화", "Growth Analytics"],
    },
    {
        "label": "로보틱스",
        "any": ["로봇", "로보틱스", "강화 학습", "동작 인식", "로봇 제어", "Isaac Sim", "ROS"],
    },
    {
        "label": "로보틱스",
        "all": ["시뮬레이션"],
        "any": ["로봇", "로보틱스", "강화 학습", "동작 인식", "제어", "Isaac Sim", "ROS", "자율"],
    },
    {
        "label": "하이브리드 인프라",
        "all": ["쿠버네티스"],
        "any": ["온프레미스", "하이브리드", "다중 리전", "GPU", "모델 서빙"],
    },
    {
        "label": "MLOps",
        "any": ["MLOps", "머신러닝 메타데이터", "실험 추적", "모델 서빙", "학습 파이프라인"],
    },
    {
        "label": "모델 서빙",
        "any": ["모델 서빙", "서빙", "배포 시스템", "GPU 스케줄링"],
    },
    {
        "label": "클라우드",
        "all": ["클라우드"],
        "any": ["AWS", "Linux", "배포", "운영", "모니터링", "서비스"],
    },
    {
        "label": "디지털 농업",
        "all": ["농업"],
        "any": ["디지털 농업", "센서", "위성", "GIS", "농장", "현장 데이터"],
    },
    {
        "label": "컴퓨터 비전",
        "any": ["컴퓨터 비전", "VLM", "영상", "객체 인식"],
    },
    {
        "label": "객체 인식",
        "any": ["객체 인식", "검출", "인식/분석"],
    },
    {
        "label": "3D 공간 이해",
        "all": ["3D"],
        "any": ["실외", "공간", "VSLAM", "예측"],
    },
    {
        "label": "NPU 적용",
        "all": ["NPU"],
        "any": ["적용", "접목", "런타임", "컴파일", "하드웨어"],
    },
    {
        "label": "모델 최적화",
        "any": ["모델 변환", "연산자 호환성", "메모리 최적화", "양자화", "컴파일"],
    },
    {
        "label": "온디바이스 최적화",
        "any": ["온디바이스", "on-device", "edge", "디바이스 기반 컴파일"],
    },
    {
        "label": "의료 데이터",
        "any": ["의료 데이터", "의료영상", "임상", "환자 데이터", "의료 AI"],
    },
    {
        "label": "트래킹",
        "any": ["이벤트 트래킹", "트래킹", "로그 품질"],
    },
    {
        "label": "CI/CD",
        "any": ["CI/CD", "씨아이씨디", "릴리스 자동화"],
    },
    {
        "label": "양자화",
        "any": ["양자화", "quantization"],
    },
    {
        "label": "사후학습",
        "any": ["사후학습", "post-training", "alignment"],
    },
]
BROAD_RETRY_FOCUS_LABELS = {
    "의료 데이터",
    "의료",
    "LLM",
    "마케팅",
    "퍼포먼스 마케팅",
    "인사이트",
    "진단",
    "파이프라인",
    "ONNX",
    "TensorFlow",
    "PyTorch",
    "SQL",
    "SDK",
    "API",
    "GPU",
    "고객 관계 관리",
    "CRM",
}

BROAD_FOCUS_LABEL_TERMS = {
    "의료 데이터",
    "LLM",
    "파이프라인",
    "마케팅",
    "의료",
    "검색",
    "추천",
    "데이터 분석",
    "인사이트",
    "ONNX",
    "TensorFlow",
    "PyTorch",
    "SQL",
    "SDK",
    "API",
    "GPU",
    "고객 관계 관리",
    "CRM",
}

FOCUS_KEYWORD_SUPPORT_RULES = {
    "생체신호": [
        (["신호 처리"], "신호 처리"),
        (["노이즈", "노이즈 제거"], "노이즈 제거"),
        (["신뢰도 평가"], "신뢰도 평가"),
    ],
    "심전도": [
        (["의료 데이터"], "의료 데이터"),
        (["임상", "emr"], "임상 데이터"),
        (["코호트"], "코호트 구축"),
    ],
    "그로스 마케팅": [
        (["crm", "고객 관계 관리"], "CRM"),
        (["리텐션"], "리텐션"),
        (["퍼포먼스", "performance"], "퍼포먼스 마케팅"),
        (["a/b 테스트"], "A/B 테스트"),
    ],
    "제품 성장 분석": [
        (["a/b 테스트"], "A/B 테스트"),
        (["코호트"], "코호트 분석"),
        (["sql"], "SQL"),
        (["bigquery"], "BigQuery"),
        (["제품"], "제품 분석"),
        (["성장"], "성장 분석"),
    ],
    "재무 계획 분석": [
        (["손익", "financial planning"], "손익 분석"),
        (["재무 모델", "비용-편익", "roi"], "재무 모델"),
        (["예측", "forecast"], "예측 모델링"),
        (["sql", "엑셀", "excel"], "재무 데이터"),
    ],
    "프로세스 혁신": [
        (["erp"], "ERP"),
        (["crm"], "CRM"),
        (["kpi", "okr"], "성과 관리"),
        (["업무 자동화", "표준 운영 절차", "sop"], "업무 자동화"),
    ],
    "플랫폼 운영": [
        (["플랫폼"], "플랫폼 운영"),
        (["프로모션"], "프로모션"),
        (["작품 운영"], "작품 운영"),
    ],
    "웹툰 플랫폼": [
        (["웹툰", "웹소설"], "콘텐츠 운영"),
        (["프로모션"], "프로모션"),
        (["sql", "태블로"], "운영 데이터"),
    ],
    "광고 데이터": [
        (["광고"], "광고"),
        (["데이터 파이프라인", "거버넌스"], "데이터 파이프라인"),
        (["sql"], "SQL"),
    ],
    "광고 성과 분석": [
        (["광고"], "광고"),
        (["캠페인", "campaign"], "캠페인 최적화"),
        (["a/b 테스트", "통계 분석"], "A/B 테스트"),
        (["sql"], "SQL"),
    ],
    "로보틱스": [
        (["강화학습", "강화 학습"], "강화학습"),
        (["동작 인식"], "동작 인식"),
        (["시뮬레이션", "isaac sim", "ros"], "시뮬레이션"),
    ],
    "모델 최적화": [
        (["onnx"], "ONNX"),
        (["양자화", "quantization"], "양자화"),
        (["컴파일"], "컴파일러"),
        (["온디바이스", "edge"], "온디바이스"),
    ],
    "온디바이스 최적화": [
        (["onnx"], "ONNX"),
        (["양자화", "quantization"], "양자화"),
        (["모델 변환", "최적화"], "모델 최적화"),
    ],
    "디지털 농업": [
        (["gis", "위성", "센서"], "농업 데이터 분석"),
        (["온보딩", "현장"], "현장 온보딩"),
        (["컨설팅"], "기술 컨설팅"),
    ],
    "컴퓨터 비전": [
        (["생성형 ai", "generative ai"], "생성형 AI"),
        (["시공간"], "시공간 데이터"),
        (["3d"], "3D 비전"),
        (["vlm"], "VLM"),
    ],
    "클라우드": [
        (["aws"], "AWS"),
        (["linux", "리눅스"], "리눅스"),
    ],
    "RAG": [
        (["llm"], "LLM"),
        (["nlp"], "NLP"),
        (["mlops"], "MLOps"),
        (["pytorch"], "PyTorch"),
    ],
}

TOOL_LIKE_KEYWORDS = {
    "SQL",
    "BigQuery",
    "PyTorch",
    "TensorFlow",
    "AWS",
    "리눅스",
    "MLOps",
    "EMR",
    "VLM",
    "NLP",
    "LLM",
    "벡터 데이터베이스",
}

STRUCTURED_SIGNAL_RULES = {
    "domainSignals": [
        {"label": "의료", "patterns": ["의료", "헬스케어", "병원", "환자", "임상"]},
        {"label": "재무", "patterns": ["재무", "financial planning", "손익", "회계", "roi"]},
        {"label": "금융", "patterns": ["금융", "핀테크", "fintech", "fraud", "리스크"]},
        {"label": "교육", "patterns": ["교육", "edtech", "에듀"]},
        {"label": "광고", "patterns": ["광고", "adtech", "campaign"]},
        {"label": "커머스", "patterns": ["커머스", "commerce", "이커머스", "상품"]},
        {"label": "콘텐츠", "patterns": ["웹툰", "웹소설", "콘텐츠", "작품"]},
        {"label": "자율주행", "patterns": ["자율주행", "자율 주행"]},
        {"label": "로보틱스", "patterns": ["로보틱스", "robotics", "로봇"]},
        {"label": "디지털 농업", "patterns": ["디지털 농업", "농업", "gis", "위성", "농장"]},
        {"label": "제조", "patterns": ["제조", "공장", "산업 안전", "산업안전"]},
    ],
    "problemSignals": [
        {"label": "RAG", "patterns": ["rag", "검색증강생성", "벡터 데이터베이스", "retrieval"]},
        {"label": "검색", "patterns": ["검색", "search"]},
        {"label": "추천", "patterns": ["추천", "recommend"]},
        {"label": "객체 인식", "patterns": ["객체 인식", "object detection"]},
        {"label": "3D 공간 이해", "patterns": ["3d", "vslam", "isaac sim", "공간 이해"]},
        {"label": "심전도", "patterns": ["심전도", "ecg"]},
        {"label": "생체신호", "patterns": ["생체신호", "신호 처리"]},
        {"label": "음성인식", "patterns": ["음성인식", "speech"]},
        {"label": "모델 해석", "patterns": ["모델 해석", "표현 학습", "스케일링 법칙", "동작 원리", "내부 구조 분석"]},
        {"label": "제품 성장 분석", "patterns": ["제품 성장", "퍼널", "코호트", "aarrr", "aarr", "실험 분석"]},
        {"label": "그로스 마케팅", "patterns": ["그로스 마케팅", "퍼포먼스 마케팅", "crm", "리텐션", "캠페인 운영"]},
        {"label": "재무 계획 분석", "patterns": ["fp&a", "financial planning", "손익", "비용-편익", "재무 모델", "재무 예측"]},
        {"label": "프로세스 혁신", "patterns": ["process innovation", "전사 프로세스", "표준 운영 절차", "sop", "업무 자동화", "kpi", "okr"]},
        {"label": "플랫폼 운영", "patterns": ["플랫폼 운영", "작품 운영", "프로모션", "서비스 운영"]},
        {"label": "광고 데이터", "patterns": ["ads ops", "광고 데이터", "광고 플랫폼", "광고 솔루션"]},
        {"label": "광고 성과 분석", "patterns": ["캠페인 성과", "캠페인 최적화", "모바일 앱 추적", "growth analytics"]},
        {"label": "리스크 모델링", "patterns": ["리스크", "fraud", "적정 한도", "이상거래"]},
        {"label": "테스트 자동화", "patterns": ["테스트 자동화", "testbench", "테스트벤치", "검증 자동화"]},
        {"label": "임베디드 최적화", "patterns": ["임베디드", "포팅", "멀티 스레딩", "파이프라이닝"]},
        {"label": "NPU 적용", "patterns": ["npu", "엔피유", "런타임", "컴파일"]},
        {"label": "모델 최적화", "patterns": ["모델 변환", "연산자 호환성", "메모리 최적화", "양자화"]},
    ],
    "systemSignals": [
        {"label": "하이브리드 인프라", "patterns": ["하이브리드", "온프레미스", "다중 리전", "멀티 클라우드", "gpu 서버"]},
        {"label": "클라우드", "patterns": ["클라우드", "aws", "gcp", "azure"]},
        {"label": "인프라", "patterns": ["인프라", "클러스터", "서버", "쿠버네티스", "kubernetes"]},
        {"label": "모델 서빙", "patterns": ["모델 서빙", "serving", "gpu 스케줄링", "배포 시스템"]},
        {"label": "시스템 아키텍처", "patterns": ["시스템 아키텍처", "아키텍처"]},
        {"label": "온디바이스", "patterns": ["온디바이스", "on-device", "edge"]},
        {"label": "API", "patterns": [" api ", "에이피아이"]},
        {"label": "SDK", "patterns": ["sdk", "에스디케이"]},
        {"label": "컴파일러", "patterns": ["compiler", "컴파일러", "ir 그래프"]},
    ],
    "modelSignals": [
        {"label": "LLM", "patterns": ["llm", "엘엘엠"]},
        {"label": "VLM", "patterns": ["vlm", "브이엘엠"]},
        {"label": "NLP", "patterns": ["nlp", "엔엘피", "자연어"]},
        {"label": "컴퓨터 비전", "patterns": ["컴퓨터 비전", "컴퓨터비전", "vision ai", "vision"]},
        {"label": "멀티모달", "patterns": ["멀티모달", "multimodal"]},
        {"label": "PyTorch", "patterns": ["pytorch", "파이토치"]},
        {"label": "TensorFlow", "patterns": ["tensorflow", "텐서플로"]},
        {"label": "ONNX", "patterns": ["onnx", "오엔엔엑스"]},
    ],
    "dataSignals": [
        {"label": "데이터 파이프라인", "patterns": ["데이터 파이프라인", "etl", "이티엘", "파이프라인"]},
        {"label": "SQL", "patterns": ["sql", "에스큐엘"]},
        {"label": "BigQuery", "patterns": ["bigquery", "빅쿼리"]},
        {"label": "EMR", "patterns": ["emr", "전자의무기록"]},
        {"label": "데이터 마트", "patterns": ["데이터 마트", "마트 데이터", "마트 테이블"]},
        {"label": "의료 데이터", "patterns": ["의료 데이터", "의료영상", "의료기기", "환자 데이터"]},
        {"label": "로그 분석", "patterns": ["로그 분석", "로그 품질", "이벤트 로그"]},
    ],
    "workflowSignals": [
        {"label": "MLOps", "patterns": ["mlops", "엠엘옵스", "실험 추적", "메타데이터", "학습 파이프라인"]},
        {"label": "CI/CD", "patterns": ["ci/cd", "씨아이씨디", "릴리스 자동화"]},
        {"label": "A/B 테스트", "patterns": ["a/b 테스트", "ab 테스트", "실험 설계"]},
        {"label": "모니터링", "patterns": ["모니터링", "monitoring"]},
        {"label": "검증", "patterns": ["검증", "테스트벤치", "testbench", "평가"]},
        {"label": "실증", "patterns": ["실증"]},
        {"label": "배포", "patterns": ["배포", "deploy"]},
    ],
}

STRUCTURED_SIGNAL_LABEL_CATEGORY = {
    rule["label"]: category
    for category, rules in STRUCTURED_SIGNAL_RULES.items()
    for rule in rules
}

STRUCTURED_SIGNAL_LIMITS = {
    "domainSignals": 4,
    "problemSignals": 5,
    "systemSignals": 4,
    "modelSignals": 4,
    "dataSignals": 4,
    "workflowSignals": 4,
    "roleSignals": 3,
    "confidenceNotes": 4,
}

MODEL_STRUCTURED_SIGNAL_KEYS = (
    "domainSignals",
    "problemSignals",
    "systemSignals",
    "modelSignals",
    "dataSignals",
    "workflowSignals",
    "roleSignals",
)

SECTION_SIGNAL_IDS = (
    "detailBody",
    "tasks",
    "requirements",
    "preferred",
    "skills",
)

SECTION_SIGNAL_FACET_KEYS = ("keyword", "tag", "context")

SECTION_SIGNAL_FACET_LIMITS = {
    "keyword": 4,
    "tag": 4,
    "context": 4,
}

SECTION_SIGNAL_CATEGORY_MAP = {
    "detailBody": {
        "keyword": ("problemSignals", "domainSignals"),
        "tag": ("domainSignals", "dataSignals"),
        "context": ("systemSignals", "workflowSignals", "modelSignals"),
    },
    "tasks": {
        "keyword": ("problemSignals", "workflowSignals"),
        "tag": ("domainSignals",),
        "context": ("systemSignals", "workflowSignals"),
    },
    "requirements": {
        "keyword": ("modelSignals", "systemSignals"),
        "tag": ("domainSignals", "dataSignals"),
        "context": ("systemSignals",),
    },
    "preferred": {
        "keyword": ("workflowSignals", "domainSignals"),
        "tag": ("dataSignals", "modelSignals"),
        "context": ("workflowSignals", "systemSignals"),
    },
    "skills": {
        "keyword": ("modelSignals", "dataSignals", "systemSignals"),
        "tag": (),
        "context": ("systemSignals",),
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_store() -> dict:
    return {
        "updatedAt": None,
        "items": {},
    }


def compute_service_scope_signature(record: dict) -> str:
    relevant = {
        "company": record.get("company", ""),
        "title": record.get("title", ""),
        "role": record.get("role", ""),
        "roleDisplay": record.get("roleDisplay", ""),
        "detailBody": record.get("detailBody", ""),
        "tasks": record.get("tasks", []) or [],
        "requirements": record.get("requirements", []) or [],
        "preferred": record.get("preferred", []) or [],
        "skills": record.get("skills", []) or [],
        "jobUrl": record.get("jobUrl", ""),
        "source": record.get("source", ""),
        "sourceUrl": record.get("sourceUrl", ""),
        "experience": record.get("experience", ""),
        "track": record.get("track", ""),
    }
    serialized = json.dumps(relevant, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()


def compute_role_group_signature(record: dict, summary_item: dict | None = None) -> str:
    relevant = {
        "company": record.get("company", ""),
        "title": record.get("title", ""),
        "role": record.get("role", ""),
        "roleDisplay": record.get("roleDisplay", ""),
        "detailBody": record.get("detailBody", ""),
        "tasks": record.get("tasks", []) or [],
        "requirements": record.get("requirements", []) or [],
        "preferred": record.get("preferred", []) or [],
        "skills": record.get("skills", []) or [],
        "jobUrl": record.get("jobUrl", ""),
        "source": record.get("source", ""),
        "sourceUrl": record.get("sourceUrl", ""),
        "experience": record.get("experience", ""),
        "track": record.get("track", ""),
    }
    serialized = json.dumps(relevant, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()


def load_enrichment_store() -> dict:
    if not ENRICHMENTS_PATH.exists():
        return default_store()
    try:
        return json.loads(ENRICHMENTS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_store()


def load_release_config() -> dict:
    if not RELEASE_CONFIG_PATH.exists():
        return {}
    try:
        data = json.loads(RELEASE_CONFIG_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except json.JSONDecodeError:
        return {}


def get_release_prompt_profile(default: str = "field_aware_v3") -> str:
    config = load_release_config()
    prompt_profile = normalize_inline_text(
        ((config.get("summaryChampion") or {}).get("promptProfile", "")) if isinstance(config, dict) else ""
    )
    return normalize_summary_prompt_profile_name(prompt_profile or default)


def save_enrichment_store(store: dict) -> None:
    ENRICHMENTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    store["updatedAt"] = now_iso()
    ENRICHMENTS_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_summary_store() -> dict:
    if not SUMMARIES_PATH.exists():
        return default_store()
    try:
        return json.loads(SUMMARIES_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_store()


def save_summary_store(store: dict) -> None:
    SUMMARIES_PATH.parent.mkdir(parents=True, exist_ok=True)
    store["updatedAt"] = now_iso()
    SUMMARIES_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_tone_legend_store() -> dict:
    if not TONE_LEGEND_PATH.exists():
        return default_store()
    try:
        return json.loads(TONE_LEGEND_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_store()


def load_company_cluster_store() -> dict:
    if not COMPANY_CLUSTERS_PATH.exists():
        return default_store()
    try:
        return json.loads(COMPANY_CLUSTERS_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_store()


def save_tone_legend_store(store: dict) -> None:
    TONE_LEGEND_PATH.parent.mkdir(parents=True, exist_ok=True)
    store["updatedAt"] = now_iso()
    TONE_LEGEND_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def save_company_cluster_store(store: dict) -> None:
    COMPANY_CLUSTERS_PATH.parent.mkdir(parents=True, exist_ok=True)
    store["updatedAt"] = now_iso()
    COMPANY_CLUSTERS_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def get_jobs_payload() -> dict:
    return json.loads(JOBS_PATH.read_text(encoding="utf-8"))


def get_job_map() -> dict:
    payload = get_jobs_payload()
    return {job["id"]: job for job in payload["jobs"]}


def get_job_by_id(job_id: str) -> dict:
    job = get_job_map().get(job_id)
    if not job:
        raise KeyError(f"Unknown job id: {job_id}")
    return job


def compact_lines(values, limit=6):
    lines = []
    for value in values or []:
        cleaned = re.sub(r"\s+", " ", (value or "").strip())
        if cleaned:
            lines.append(cleaned)
    return lines[:limit]


def normalize_inline_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def normalize_signal_text(value: str) -> str:
    text = normalize_inline_text(value)
    if not text:
        return ""
    for pattern, replacement in INLINE_TERM_REPLACEMENTS:
        text = pattern.sub(replacement, text)
    text = re.sub(r"\b([A-Za-z0-9가-힣/+]+)\(\1\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip(" -–—·•▪*")
    return text


def is_summary_noise_line(value: str) -> bool:
    line = normalize_inline_text(value)
    if not line or len(line) <= 2:
        return True
    for pattern in SUMMARY_NOISE_PATTERNS:
        if re.match(pattern, line):
            return True
    if re.match(r"^[은는이가을를]\s", line):
        return True
    return False


def is_detail_noise_line(value: str) -> bool:
    line = normalize_signal_text(value)
    if is_summary_noise_line(line):
        return True
    for pattern in DETAIL_NOISE_PATTERNS:
        if re.match(pattern, line):
            return True
    return False


def is_field_noise_line(value: str) -> bool:
    line = normalize_signal_text(value)
    if not line:
        return True
    if is_detail_noise_line(line) and not contains_signal_hint(line):
        return True
    for pattern in FIELD_LINE_NOISE_PATTERNS:
        if re.match(pattern, line):
            return True
    for pattern in GENERIC_FRAGMENT_PATTERNS:
        if re.match(pattern, line):
            return True
    return False


def contains_signal_hint(value: str) -> bool:
    line = normalize_signal_text(value).lower()
    if not line:
        return False
    if re.search(r"\b(?:LLM|VLM|NLP|RAG|MLOps|ONNX|AWS|SQL|EMR|GIS|SDK|GA)\b", normalize_signal_text(value)):
        return True
    return any(hint.lower() in line for hint in SIGNAL_KEEP_HINTS)


def score_summary_signal_line(value: str, field: str = "detail") -> tuple[float, int]:
    line = normalize_signal_text(value)
    lowered = line.lower()
    score = 0.0

    if contains_signal_hint(line):
        score += 8.0
    if re.search(
        r"(추천 시스템|생성형 인공지능|머신러닝|machine learning|llm|rag|컴퓨터 비전|vision|자율주행|임베디드|추론|모델|파이프라인|서빙|아키텍처|sql|spark|flink|npu|gpu|onnx|mlops|실험|분석|최적화)",
        lowered,
        re.I,
    ):
        score += 4.5
    if re.search(r"(개발|설계|구축|운영|최적화|분석|평가|적용|서빙|배포)", lowered):
        score += 1.6
    if re.search(r"(추천|생성형|프로덕션|실시간|분산|백엔드|server|api)", lowered, re.I):
        score += 1.2

    if field in {"requirements", "preferred"} and re.search(r"(우대|있으면 좋습니다|관심과 경험)", lowered):
        score -= 0.6
    if re.search(r"(영어|의사소통|협업|적응|커뮤니케이션)", lowered) and not contains_signal_hint(line):
        score -= 2.4
    if re.search(r"(학사|석사|박사|학위|경력|전공)", lowered) and not contains_signal_hint(line):
        score -= 1.6

    score += min(len(line), 90) / 90
    return score, len(line)


def split_field_segments(value: str) -> list[str]:
    raw = str(value or "").replace("\r", "\n")
    raw = re.sub(r"\s+[·•▪]\s+", "\n", raw)
    raw = re.sub(
        r"\s+(?=(해외여행에|남성은|취업보호대상자|관련 분야|채용하고 싶은 사람|공고명[:：]|지원 전,|채용 관련 문의사항|[0-9]+년 이상))",
        "\n",
        raw,
    )
    parts = re.split(r"(?:[\n]+|(?<=[.!?])\s+)", raw)
    segments = []
    for part in parts:
        cleaned = normalize_signal_text(part)
        cleaned = re.sub(r"^(?:[·•▪*]+|\-+)\s*", "", cleaned)
        cleaned = re.sub(r"^(공고명|직무내용|주요 연구 영역은 다음과 같습니다|요 연구 영역은 다음과 같습니다)[:：]?\s*", "", cleaned)
        cleaned = normalize_signal_text(cleaned)
        if cleaned:
            segments.append(cleaned)
    return segments


def should_drop_field_segment(field: str, value: str) -> bool:
    line = normalize_signal_text(value)
    if not line:
        return True
    if is_field_noise_line(line) and not contains_signal_hint(line):
        return True

    lowered = line.lower()
    has_signal = contains_signal_hint(line)
    has_degree_or_year = bool(re.search(r"(학사|석사|박사|학위|초대졸|전공|[0-9]+년|경력)", line))
    has_generic_attitude = bool(
        re.search(
            r"(문제 해결|커뮤니케이션|협업|의사결정|주도적|책임감|성실|원활한 소통|빠르게 실행|스스로 방향을 잡고|끝까지 실행)",
            line,
        )
    )
    if re.match(r"^(위한|또는|관련|기본)\b", lowered):
        return True
    if any(line.endswith(suffix) for suffix in WEAK_KEYWORD_SUFFIXES):
        return True
    if re.search(r"(채용 전형|인터뷰|수습기간|복지|처우 협의|최종 입사)", line):
        return True
    if not has_signal and re.search(r"(자율 복장|교육비|도서 구입비|인센티브|팀 활동비|리더소통비|지원금)", line):
        return True

    if field in {"requirements", "preferred"}:
        if has_degree_or_year and not has_signal:
            return True
        if has_generic_attitude and not has_signal:
            return True
        if re.match(r"^(별도|기본|관련 분야)\s", lowered) and not has_signal:
            return True

    if field == "tasks":
        if re.match(r"^(공고|채용|문의|지원)\b", lowered):
            return True
        if len(re.sub(r"[^0-9A-Za-z가-힣]+", "", line)) <= 4:
            return True

    if field == "skills":
        if is_generic_keyword(line):
            return True

    return False


def split_detail_segments(value: str) -> list[str]:
    raw = str(value or "").replace("\r", "\n")
    raw = re.sub(
        r"\s+(?=(해외여행에|남성은|취업보호대상자|관련 분야|채용하고 싶은 사람|[0-9]+년 이상))",
        "\n",
        raw,
    )
    raw = re.sub(r"\s+[·•▪]\s+", "\n", raw)
    parts = re.split(r"(?:[\n]+|(?<=[.!?])\s+)", raw)
    segments = []
    for part in parts:
        cleaned = normalize_signal_text(part)
        if cleaned:
            segments.append(cleaned)
    return segments


def clean_detail_for_summary(value: str, limit=6) -> list[str]:
    candidates = []
    seen = set()
    for index, part in enumerate(split_detail_segments(value)):
        cleaned = normalize_signal_text(part)
        cleaned = re.sub(r"^본 직무는\s*", "", cleaned)
        cleaned = re.sub(r"^채용된 전문가는\s*", "", cleaned)
        cleaned = re.sub(r"^전문가는 아래 업무들을.*$", "", cleaned)
        cleaned = re.sub(r"^직무내용$", "", cleaned)
        cleaned = normalize_signal_text(cleaned)
        if is_field_noise_line(cleaned):
            continue
        compact = re.sub(r"[^0-9A-Za-z가-힣]+", "", cleaned).lower()
        if compact in seen:
            continue
        seen.add(compact)
        score, length = score_summary_signal_line(cleaned, field="detail")
        candidates.append((score, length, index, cleaned))

    candidates.sort(key=lambda item: (-item[0], item[2], -item[1]))
    return [cleaned for _, _, _, cleaned in candidates[:limit]]


def is_generic_keyword(value: str) -> bool:
    cleaned = normalize_signal_text(value).lower()
    if not cleaned:
        return True
    compact = re.sub(r"[^0-9a-z가-힣]+", "", cleaned)
    if len(compact) <= 1:
        return True
    for pattern in GENERIC_KEYWORD_PATTERNS:
        if re.match(pattern, cleaned):
            return True
    if compact.endswith(WEAK_KEYWORD_SUFFIXES):
        return True
    return False


def is_weak_focus_label(value: str) -> bool:
    cleaned = normalize_signal_text(value)
    if not cleaned:
        return True
    lowered = cleaned.lower()
    if is_generic_keyword(cleaned):
        return True
    for pattern in WEAK_FOCUS_LABEL_PATTERNS:
        if re.match(pattern, lowered):
            return True
    compact = re.sub(r"[^0-9a-z가-힣]+", "", lowered)
    if compact in {re.sub(r"[^0-9a-z가-힣]+", "", item.lower()) for item in WEAK_FOCUS_LABEL_TERMS}:
        return True
    return False


def canonicalize_term(value: str) -> str:
    cleaned = normalize_signal_text(value)
    if not cleaned:
        return ""
    lowered = cleaned.lower()
    if lowered in CANONICAL_TERM_MAP:
        return CANONICAL_TERM_MAP[lowered]
    return CANONICAL_TERM_MAP.get(cleaned, cleaned)


def append_unique_signal(bucket: list[str], value: str, limit: int) -> None:
    cleaned = canonicalize_term(value)
    if not cleaned or cleaned in bucket or len(bucket) >= limit:
        return
    bucket.append(cleaned)


def normalize_model_structured_signals(payload: dict) -> dict:
    data = payload if isinstance(payload, dict) else {}
    signals = {
        "quality": "",
        "domainSignals": [],
        "problemSignals": [],
        "systemSignals": [],
        "modelSignals": [],
        "dataSignals": [],
        "workflowSignals": [],
        "roleSignals": [],
        "confidenceNotes": [],
    }

    quality = normalize_inline_text(data.get("quality", "")).lower()
    if quality in {"high", "medium", "low"}:
        signals["quality"] = quality

    for key in MODEL_STRUCTURED_SIGNAL_KEYS:
        limit = STRUCTURED_SIGNAL_LIMITS.get(key, 3)
        values = data.get(key, [])
        if not isinstance(values, list):
            continue
        for value in values:
            cleaned = canonicalize_term(value) if key != "roleSignals" else normalize_signal_text(value)
            if not cleaned:
                continue
            if key != "roleSignals" and is_generic_keyword(cleaned):
                continue
            if cleaned in signals[key] or len(signals[key]) >= limit:
                continue
            signals[key].append(cleaned)

    return signals


def normalize_model_section_signal_facets(payload: dict) -> dict:
    data = payload if isinstance(payload, dict) else {}
    normalized = {
        section_id: {facet: [] for facet in SECTION_SIGNAL_FACET_KEYS}
        for section_id in SECTION_SIGNAL_IDS
    }

    for section_id in SECTION_SIGNAL_IDS:
        section_payload = data.get(section_id, {})
        if not isinstance(section_payload, dict):
            continue
        for facet in SECTION_SIGNAL_FACET_KEYS:
            values = section_payload.get(facet, [])
            if not isinstance(values, list):
                continue
            for value in values:
                cleaned = canonicalize_term(value)
                if not cleaned or is_generic_keyword(cleaned):
                    continue
                if (
                    cleaned in normalized[section_id][facet]
                    or len(normalized[section_id][facet]) >= SECTION_SIGNAL_FACET_LIMITS[facet]
                ):
                    continue
                normalized[section_id][facet].append(cleaned)

    return normalized


def flatten_section_signal_values(signals: dict, keys: tuple[str, ...]) -> list[str]:
    values = []
    for key in keys:
        raw_values = signals.get(key, []) if isinstance(signals.get(key, []), list) else []
        for value in raw_values:
            cleaned = canonicalize_term(value)
            if not cleaned or is_generic_keyword(cleaned) or cleaned in values:
                continue
            values.append(cleaned)
    return values


def text_contains_pattern(text: str, pattern: str) -> bool:
    normalized_text = normalize_signal_text(text).lower()
    normalized_pattern = normalize_signal_text(pattern).lower()
    if not normalized_text or not normalized_pattern:
        return False
    if re.match(r"^[a-z0-9/+.-]+$", normalized_pattern):
        return re.search(rf"(?<![a-z0-9]){re.escape(normalized_pattern)}(?![a-z0-9])", normalized_text) is not None
    return normalized_pattern in normalized_text


def collect_rule_based_signals(text: str, rules: list[dict], limit: int) -> list[str]:
    signals = []
    for rule in rules:
        if any(text_contains_pattern(text, pattern) for pattern in rule["patterns"]):
            append_unique_signal(signals, rule["label"], limit)
    return signals


def build_structured_signals(job: dict, item: dict, compact_job: dict | None = None) -> dict:
    compact = compact_job or compact_job_for_summary(job)
    quality = normalize_inline_text(item.get("quality", "")).lower() or "low"
    model_structured = normalize_model_structured_signals(
        item.get("structuredSignals", {}) or item.get("structured_signals", {})
    )

    signals = {
        "quality": quality,
        "domainSignals": [],
        "problemSignals": [],
        "systemSignals": [],
        "modelSignals": [],
        "dataSignals": [],
        "workflowSignals": [],
        "roleSignals": [],
        "confidenceNotes": [],
    }

    for key in MODEL_STRUCTURED_SIGNAL_KEYS:
        for value in model_structured.get(key, []):
            append_unique_signal(signals[key], value, STRUCTURED_SIGNAL_LIMITS[key])

    for role_value in [
        item.get("role", ""),
        job.get("roleDisplay", ""),
        job.get("role", ""),
    ]:
        cleaned = normalize_signal_text(role_value)
        if not cleaned:
            continue
        if cleaned in signals["roleSignals"] or len(signals["roleSignals"]) >= STRUCTURED_SIGNAL_LIMITS["roleSignals"]:
            continue
        signals["roleSignals"].append(cleaned)

    if quality == "low":
        append_unique_signal(signals["confidenceNotes"], "low_confidence", STRUCTURED_SIGNAL_LIMITS["confidenceNotes"])
        if len(compact.get("detailBody", []) or []) + len(compact.get("tasks", []) or []) <= 1:
            append_unique_signal(
                signals["confidenceNotes"],
                "sparse_input_signal",
                STRUCTURED_SIGNAL_LIMITS["confidenceNotes"],
            )
        return signals

    trusted_source_texts = [
        job.get("title", ""),
        item.get("summary", ""),
        item.get("focusLabel", ""),
        *(item.get("keywords", []) or []),
        *(compact.get("detailBody", []) or []),
        *(compact.get("tasks", []) or []),
        *(compact.get("skills", []) or []),
    ]
    combined_text = normalize_signal_text(" ".join(str(value) for value in trusted_source_texts if value))
    has_model_signal_seed = any(
        signals[key]
        for key in MODEL_STRUCTURED_SIGNAL_KEYS
        if key != "roleSignals"
    )

    for category, rules in STRUCTURED_SIGNAL_RULES.items():
        if has_model_signal_seed and signals[category]:
            continue
        extracted = collect_rule_based_signals(
            combined_text,
            rules,
            STRUCTURED_SIGNAL_LIMITS[category],
        )
        for value in extracted:
            append_unique_signal(signals[category], value, STRUCTURED_SIGNAL_LIMITS[category])

    seeded_values = [
        item.get("focusLabel", ""),
        *(item.get("keywords", []) or []),
        *extract_focus_hints_from_text(item.get("summary", "")),
        *synthesize_focus_candidates(
            summary=item.get("summary", ""),
            keywords=item.get("keywords", []) or [],
        ),
    ]
    for value in seeded_values:
        cleaned = canonicalize_term(value)
        category = STRUCTURED_SIGNAL_LABEL_CATEGORY.get(cleaned)
        if not category:
            continue
        if cleaned in TOOL_LIKE_KEYWORDS and (
            signals["domainSignals"]
            or signals["problemSignals"]
            or signals["systemSignals"]
            or signals["workflowSignals"]
        ):
            continue
        append_unique_signal(signals[category], cleaned, STRUCTURED_SIGNAL_LIMITS[category])

    if quality == "low":
        append_unique_signal(signals["confidenceNotes"], "low_confidence", STRUCTURED_SIGNAL_LIMITS["confidenceNotes"])
    if item.get("focusLabel") and is_broad_focus_label(item.get("focusLabel", "")):
        append_unique_signal(
            signals["confidenceNotes"],
            "broad_focus_input",
            STRUCTURED_SIGNAL_LIMITS["confidenceNotes"],
        )
    if not signals["domainSignals"] and not signals["problemSignals"]:
        append_unique_signal(
            signals["confidenceNotes"],
            "missing_domain_problem_signal",
            STRUCTURED_SIGNAL_LIMITS["confidenceNotes"],
        )
    if (
        signals["systemSignals"]
        and not signals["domainSignals"]
        and not signals["problemSignals"]
    ):
        append_unique_signal(
            signals["confidenceNotes"],
            "system_only_signal",
            STRUCTURED_SIGNAL_LIMITS["confidenceNotes"],
        )
    if len(compact.get("detailBody", []) or []) + len(compact.get("tasks", []) or []) <= 1:
        append_unique_signal(
            signals["confidenceNotes"],
            "sparse_input_signal",
            STRUCTURED_SIGNAL_LIMITS["confidenceNotes"],
        )

    return signals


def build_section_signal_facets(job: dict, item: dict, compact_job: dict | None = None) -> dict:
    _ = compact_job or compact_job_for_summary(job)
    model_section_facets = normalize_model_section_signal_facets(
        item.get("sectionSignalFacets", {}) or item.get("section_signal_facets", {})
    )
    has_model_facets = any(
        model_section_facets[section_id][facet]
        for section_id in SECTION_SIGNAL_IDS
        for facet in SECTION_SIGNAL_FACET_KEYS
    )
    if has_model_facets:
        return model_section_facets

    structured = normalize_model_structured_signals(
        item.get("structuredSignals", {}) or item.get("structured_signals", {})
    )
    projected = {}
    for section_id, category_map in SECTION_SIGNAL_CATEGORY_MAP.items():
        projected[section_id] = {
            facet: flatten_section_signal_values(structured, category_map.get(facet, ()))[: SECTION_SIGNAL_FACET_LIMITS[facet]]
            for facet in SECTION_SIGNAL_FACET_KEYS
        }
    return projected


def backfill_structured_signals(store: dict | None = None, jobs_payload: dict | None = None) -> tuple[dict, int]:
    current_store = store or load_summary_store()
    payload = jobs_payload or get_jobs_payload()
    jobs_by_id = {job["id"]: job for job in payload.get("jobs", [])}
    updated = 0

    for job_id, item in current_store.get("items", {}).items():
        job = jobs_by_id.get(job_id)
        if not job:
            continue
        compact = compact_job_for_summary(job)
        structured_signals = build_structured_signals(job, item, compact_job=compact)
        if item.get("structuredSignals") != structured_signals:
            item["structuredSignals"] = structured_signals
            updated += 1

    return current_store, updated


def extract_focus_hints_from_text(value: str) -> list[str]:
    cleaned = normalize_signal_text(value).lower()
    if not cleaned:
        return []
    hints = []
    seen = set()
    for pattern, label in SUMMARY_HINT_LABELS:
        if pattern in cleaned and label not in seen:
            seen.add(label)
            hints.append(label)
    return hints


def is_broad_focus_label(value: str) -> bool:
    cleaned = canonicalize_term(value)
    return cleaned in BROAD_FOCUS_LABEL_TERMS


def score_focus_candidate(
    value: str,
    summary: str = "",
    role: str = "",
    source: str = "keyword",
) -> float:
    cleaned = canonicalize_term(value)
    if not cleaned:
        return -999.0
    if is_weak_focus_label(cleaned):
        return -999.0

    lowered = cleaned.lower()
    score = min(len(cleaned), 18) / 10
    if " " in cleaned:
        score += 0.6
    if re.search(r"[A-Z0-9]", cleaned):
        score += 0.6
    if any(hint in lowered for hint in FOCUS_SIGNAL_HINTS):
        score += 2.0
    if cleaned in TOOL_LIKE_KEYWORDS:
        score -= 1.6

    summary_clean = normalize_signal_text(summary).lower()
    role_clean = normalize_signal_text(role).lower()
    if summary_clean and lowered in summary_clean:
        score += 0.4
    if source == "summary_hint":
        score += 1.2
    if role_clean and lowered == role_clean:
        score -= 1.5
    if lowered in {"사업 개발", "소프트웨어 개발", "데이터 분석"}:
        score -= 0.8
    return score


def synthesize_focus_candidates(summary: str, keywords: list[str]) -> list[str]:
    combined = " ".join(
        canonicalize_term(value)
        for value in [summary, *keywords]
        if canonicalize_term(value)
    )
    if not combined:
        return []
    candidates = []
    seen = set()
    lowered = combined.lower()
    for rule in FOCUS_COMPOSITE_RULES:
        required = [token.lower() for token in rule.get("all", [])]
        optional = [token.lower() for token in rule.get("any", [])]
        if required and not all(token in lowered for token in required):
            continue
        if optional and not any(token in lowered for token in optional):
            continue
        label = rule["label"]
        if label not in seen:
            seen.add(label)
            candidates.append(label)
    return candidates


def choose_focus_label(
    role: str,
    summary: str,
    focus_label: str,
    keywords: list[str],
    context_text: str = "",
) -> str:
    candidates = []
    seen = set()
    ordered_candidates = []
    if focus_label:
        ordered_candidates.append(("focus", focus_label))
    for keyword in keywords:
        ordered_candidates.append(("keyword", keyword))
    for hint in extract_focus_hints_from_text(summary):
        ordered_candidates.append(("summary_hint", hint))
    for hint in extract_focus_hints_from_text(context_text):
        ordered_candidates.append(("context_hint", hint))
    for candidate in synthesize_focus_candidates(
        summary=f"{summary} {context_text}".strip(),
        keywords=keywords,
    ):
        ordered_candidates.append(("composite_hint", candidate))

    specific_candidates = {
        canonicalize_term(value)
        for _, value in ordered_candidates
        if canonicalize_term(value) and not is_broad_focus_label(value) and not is_weak_focus_label(value)
    }

    for source, value in ordered_candidates:
        cleaned = canonicalize_term(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        score = score_focus_candidate(cleaned, summary=summary, role=role, source=source)
        if source == "composite_hint":
            score += 1.4
        if source == "context_hint":
            score += 0.9
        if source == "focus" and not is_broad_focus_label(cleaned):
            score += 0.9
        if is_broad_focus_label(cleaned) and specific_candidates - {cleaned}:
            score -= 2.3
            if source == "focus":
                score -= 0.6
        if cleaned in TOOL_LIKE_KEYWORDS:
            non_tool_candidates = {candidate for candidate in specific_candidates if candidate not in TOOL_LIKE_KEYWORDS}
            if non_tool_candidates - {cleaned}:
                score -= 2.4
            elif source == "focus":
                score -= 0.4
        if score <= -900:
            continue
        candidates.append((score, cleaned))

    if not candidates:
        return ""

    candidates.sort(key=lambda item: (-item[0], len(item[1]), item[1]))
    return candidates[0][1]


STRUCTURED_FOCUS_PRIORITY = [
    ("problemSignals", 9.2),
    ("domainSignals", 8.1),
    ("dataSignals", 7.4),
    ("systemSignals", 6.6),
    ("workflowSignals", 5.8),
    ("modelSignals", 4.8),
]

RAW_SIGNAL_PROJECTION_BLOCKLIST = {
    "LLM",
    "파이프라인",
    "파이썬",
    "PyTorch",
    "TensorFlow",
    "ONNX",
    "SQL",
    "BigQuery",
    "도커",
    "쿠버네티스",
    "SDK",
    "API",
    "GPU",
}


def project_focus_label_from_structured_signals(
    signals: dict,
    current_focus: str,
    keywords: list[str],
) -> str:
    current = canonicalize_term(current_focus)
    keyword_set = {canonicalize_term(value) for value in keywords if canonicalize_term(value)}
    candidates = []
    specific_exists = False

    for category, base_weight in STRUCTURED_FOCUS_PRIORITY:
        values = signals.get(category, []) if isinstance(signals.get(category, []), list) else []
        for index, value in enumerate(values):
            cleaned = canonicalize_term(value)
            if not cleaned or is_weak_focus_label(cleaned):
                continue
            score = base_weight - (index * 0.18)
            if cleaned in keyword_set:
                score += 0.3
            if current and cleaned == current:
                score += 0.45
            if is_broad_focus_label(cleaned):
                score -= 1.35
            else:
                specific_exists = True
            candidates.append((score, cleaned))

    if current and not is_weak_focus_label(current):
        candidates.append((4.2 if not is_broad_focus_label(current) else 1.9, current))

    if not candidates:
        return current

    ranked = []
    for score, label in candidates:
        adjusted = score
        if specific_exists and is_broad_focus_label(label):
            adjusted -= 1.15
        ranked.append((adjusted, len(label), label))

    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    return ranked[0][2]


def should_apply_structured_focus_projection(
    signals: dict,
    current_focus: str,
    projected_focus: str,
) -> bool:
    current = canonicalize_term(current_focus)
    projected = canonicalize_term(projected_focus)
    if not projected:
        return False
    if projected == current:
        return False

    stronger_signal_count = sum(
        len(signals.get(key, []) if isinstance(signals.get(key, []), list) else [])
        for key in ("problemSignals", "domainSignals", "systemSignals", "workflowSignals")
    )

    if projected in RAW_SIGNAL_PROJECTION_BLOCKLIST and current:
        return False
    if projected in RAW_SIGNAL_PROJECTION_BLOCKLIST and stronger_signal_count == 0:
        return False
    if current and not is_broad_focus_label(current) and is_broad_focus_label(projected):
        return False
    return True


def split_detail_lines(value: str, limit=12) -> list[str]:
    lines = []
    seen = set()
    for part in re.split(r"[\n\r]+", value or ""):
        cleaned = re.sub(r"\s+", " ", part.strip())
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        lines.append(cleaned)
        if len(lines) >= limit:
            break
    return lines


def clean_field_lines(values, field: str, limit=6) -> list[str]:
    lines = []
    seen = set()
    ranked = []
    for outer_index, value in enumerate(values or []):
        for inner_index, part in enumerate(split_field_segments(value)):
            cleaned = normalize_signal_text(part)
            if should_drop_field_segment(field, cleaned):
                continue
            compact = re.sub(r"[^0-9A-Za-z가-힣]+", "", cleaned).lower()
            if compact in seen:
                continue
            seen.add(compact)
            score, length = score_summary_signal_line(cleaned, field=field)
            ranked.append((score, length, outer_index, inner_index, cleaned))

    ranked.sort(key=lambda item: (-item[0], item[2], item[3], -item[1]))
    for _, _, _, _, cleaned in ranked[:limit]:
        lines.append(cleaned)
    return lines


def clean_skill_lines(values, limit=8) -> list[str]:
    items = []
    seen = set()
    for value in values or []:
        cleaned = normalize_signal_text(value)
        cleaned = re.sub(r"\b(경험|활용 능력|전문성|역량)\b$", "", cleaned).strip(" ,/")
        cleaned = normalize_signal_text(cleaned)
        cleaned = canonicalize_term(cleaned)
        if not cleaned or is_generic_keyword(cleaned):
            continue
        compact = re.sub(r"[^0-9A-Za-z가-힣]+", "", cleaned).lower()
        if compact in seen:
            continue
        seen.add(compact)
        items.append(cleaned)
        if len(items) >= limit:
            break
    return items


def compact_job_for_summary(job: dict) -> dict:
    return {
        "id": job.get("id", ""),
        "title": job.get("title", ""),
        "roleDisplay": job.get("roleDisplay", ""),
        "detailBody": clean_detail_for_summary(job.get("detailBody", ""), limit=6),
        "tasks": clean_field_lines(job.get("tasks", []), field="tasks", limit=5),
        "requirements": clean_field_lines(job.get("requirements", []), field="requirements", limit=5),
        "preferred": clean_field_lines(job.get("preferred", []), field="preferred", limit=5),
        "skills": clean_skill_lines(job.get("skills", []), limit=8),
    }


SUMMARY_PROMPT_PROFILES = {
    "baseline_v1": (
        "당신은 배포용 채용 보드에 올릴 공고 정리 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고, 입력에 없는 사실을 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\"}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item을 하나씩 반드시 반환하세요. "
        "summary는 실제 업무를 짧고 구체적으로 식별하는 한국어 구문이어야 하며 48자 이하여야 합니다. "
        "직무명 반복, 회사 소개, 복지, 지원 안내, 포털 문구, 추상 표현은 금지합니다. "
        "keywords는 2~5개, focusLabel은 1개이며 모두 짧은 명사구로 쓰세요. "
        "keywords와 focusLabel은 스택, 모델 종류, 도메인, 데이터, 시스템, 검증 대상처럼 화면에서 묶음 근거로 쓸 수 있어야 합니다. "
        "조사, 접속어, 학력 표현, 경력 표현, 포괄적인 제품/서비스 표현은 keyword나 focusLabel로 쓰지 마세요. "
        "예: '위한', '또는', '학력', '석사', '박사', '경력', '제품', '서비스' 같은 단어는 단독으로 금지합니다. "
        "detailBody가 약하더라도 tasks, requirements, preferred, skills에서 실제 업무/기술 근거가 잡히면 그 내용을 우선 사용하세요. "
        "근거가 약하거나 일반적인 자격 문장만 있으면 summary는 빈 문자열로 두고 keywords는 빈 배열, focusLabel은 빈 문자열, quality는 low로 두세요. "
        "quality는 high, medium, low 중 하나만 사용하세요. "
        "좋은 summary 예시: '멀티모달 검색 파이프라인 구축과 모델 미세조정' "
        "좋은 summary 예시: 'NPU 검증용 테스트벤치 개발과 성능 확인' "
        "나쁜 summary 예시: '인공지능 엔지니어', '연구 지원 프로그램', '채용 문의 안내'."
    ),
    "field_aware_v2": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\"}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "작업 순서: "
        "1) detailBody와 tasks에서 실제 하는 일을 먼저 찾으세요. "
        "2) requirements와 preferred에서는 학력/경력 문구를 버리고 스택, 시스템, 도메인, 업무 유형만 남기세요. "
        "3) skills에서는 기술명만 보강하세요. "
        "summary는 공고가 실제로 하게 될 업무를 18~42자 사이의 한국어 구문 하나로 적으세요. "
        "summary는 역할명 반복, 회사 소개, 제품 홍보, 채용 안내, 복지, 지원 절차를 포함하면 안 됩니다. "
        "focusLabel은 그룹 제목 seed로 사용할 1개의 짧은 명사구입니다. "
        "keywords는 2~5개의 짧은 명사구입니다. "
        "focusLabel과 keywords에는 스택, 데이터/파이프라인, 모델 종류, 도메인, 시스템, 검증 대상, 실험 유형 같은 말만 허용됩니다. "
        "다음 표현은 focusLabel/keywords에서 금지합니다: "
        "'위한', '또는', '대한', '통한', '관련', '학력', '학사', '석사', '박사', '경력', '제품', '서비스', '기술', '업무'. "
        "문장 전체나 조건절도 금지합니다. "
        "예: '인공지능 또는 플랫폼 제품 출시 경험' 같은 문장은 절대 keyword로 쓰지 마세요. "
        "허용 예: 'LLM', 'RAG', '컴퓨터비전', '데이터 파이프라인', '모델 서빙', '헬스케어', '실험 설계', '쿠버네티스'. "
        "근거가 부족하거나 자격 요건 문장만 있을 때는 summary는 빈 문자열, keywords는 빈 배열, focusLabel은 빈 문자열, quality는 low로 두세요. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v3": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\"}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "summary는 실제 하는 일을 보여주는 한국어 구문 하나이며 18~40자 사이로 쓰세요. "
        "summary에 직무명만 반복해서는 안 됩니다. "
        "예를 들어 '인공지능 엔지니어', '데이터 분석가', '연구원'처럼 역할명만 쓰면 안 됩니다. "
        "summary에는 실제 업무 동사 대신 업무 대상과 작업 맥락이 드러나야 합니다. "
        "좋은 예: '의료 데이터 파이프라인 구축과 품질 관리', '온디바이스 추론 최적화와 모델 변환'. "
        "focusLabel은 비워두지 말고, quality가 low가 아닌 경우 반드시 1개를 넣으세요. "
        "focusLabel은 keywords 중 가장 중심이 되는 하나를 그대로 재사용해도 됩니다. "
        "keywords는 2~5개의 짧은 명사구입니다. "
        "focusLabel과 keywords에는 스택, 모델 종류, 도메인, 데이터 유형, 시스템, 파이프라인, 검증 대상, 실험 유형만 허용됩니다. "
        "학력, 경력, 역할명, 제품/서비스 같은 포괄 표현은 금지합니다. "
        "금지 예: '위한', '또는', '관련', '학사', '석사', '박사', '경력', '제품', '서비스', '인공지능 엔지니어', '데이터 분석가'. "
        "작업 순서: detailBody와 tasks에서 실제 하는 일을 먼저 찾고, requirements와 preferred에서는 스택/도메인/업무 신호만 남기고, skills는 기술명을 보강하세요. "
        "근거가 부족한 경우에만 summary는 빈 문자열, keywords는 빈 배열, focusLabel은 빈 문자열, quality는 low로 두세요. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v4": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\"}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "summary는 18~38자의 한국어 명사구 하나로 쓰세요. 문장처럼 끝내지 말고, '~합니다', '~수행합니다', '~담당합니다', '~지원합니다' 같은 종결형을 쓰지 마세요. "
        "summary는 역할명 반복이 아니라 실제 업무 대상과 작업 맥락을 보여줘야 합니다. "
        "focusLabel은 quality가 low가 아닌 경우 반드시 1개를 채우고, keywords 중 가장 중심이 되는 표현 하나와 같아도 됩니다. "
        "focusLabel은 roleDisplay의 반복이 아니라 그룹 제목 seed로 쓸 수 있는 구체 표현이어야 합니다. "
        "keywords는 2~5개의 짧은 명사구입니다. "
        "focusLabel과 keywords에는 스택, 모델 종류, 도메인, 데이터 유형, 시스템, 파이프라인, 검증 대상, 실험 유형만 허용됩니다. "
        "금지 예: '위한', '또는', '관련', '학사', '석사', '박사', '경력', '제품', '서비스', '인공지능 엔지니어', '데이터 분석가'. "
        "작업 순서: detailBody와 tasks에서 실제 하는 일을 먼저 찾고, requirements와 preferred에서는 스택/도메인/업무 신호만 남기고, skills는 기술명을 보강하세요. "
        "근거가 부족한 경우에만 summary는 빈 문자열, keywords는 빈 배열, focusLabel은 빈 문자열, quality는 low로 두세요. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v5": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\"}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "먼저 이 공고가 실제 업무 공고인지, 채용 안내/운영 안내/양식 공고인지 판단하세요. "
        "detailBody와 tasks에 구체적 업무가 거의 없고 공고명, 전형, 병역, 지원 안내, 양식, 복지, 회사 소개가 대부분이면 quality는 low로 두고 summary, keywords, focusLabel은 비웁니다. "
        "summary는 배포 화면에 바로 올릴 게시용 문구입니다. "
        "summary는 16~34자의 한국어 명사구 하나로 쓰고 문장처럼 끝내지 마세요. "
        "summary는 roleDisplay 반복, title 반복, 회사명 반복, 공고명 echo, 직무내용/전반/전문성 같은 메타 단어를 쓰면 안 됩니다. "
        "summary는 반드시 실제 업무 대상과 작업 맥락이 함께 보이게 쓰세요. "
        "좋은 형태 예: '생체신호 처리와 신뢰도 평가 알고리즘 개발', 'LLM 검색 시스템 설계와 성능 개선', '제품 성장 지표 설계와 실험 분석', '디지털 농업 플랫폼 도입과 현장 컨설팅'. "
        "나쁜 형태 예: '인공지능 연구', '앱 성장 데이터 분석가', '직무내용', 'Senior Applied Scientist', 'Talent Pool (R&D)'. "
        "focusLabel은 그룹 제목 seed로 쓸 1개의 짧은 명사구입니다. quality가 low가 아니면 반드시 채우세요. "
        "focusLabel은 role이나 포괄 직무명이 아니라, 가장 중심이 되는 도메인/문제/시스템 축이어야 합니다. "
        "우선순위는 도메인/문제 > 시스템/파이프라인 > 모델 계열 > 스택입니다. "
        "예: '심전도', 'RAG', '제품 성장 분석', '그로스 마케팅', '디지털 농업', '클라우드', '컴퓨터 비전'. "
        "다음 표현은 focusLabel에서 금지합니다: roleDisplay 반복, 회사/조직명, 제품/서비스, 직무내용, 전반, 전문성, 별도, 모든, 검색, 연구, 개발, 분석. "
        "keywords는 3~5개의 짧은 명사구입니다. "
        "keywords의 첫 항목은 가능하면 focusLabel과 같게 두고, 나머지는 다른 축으로 보강하세요. "
        "keywords는 서로 다른 역할을 가져야 합니다: 도메인, 모델/방법, 시스템/파이프라인, 검증/운영, 데이터 중 2개 이상 축이 섞이게 하세요. "
        "프레임워크만 나열하거나 조사형/문장형 표현을 넣으면 안 됩니다. "
        "금지 예: '위한', '또는', '관련', '학사', '석사', '박사', '경력', '제품', '서비스', '직무내용', '전문연구요원', '공고문'. "
        "작업 순서: "
        "1) detailBody와 tasks에서 실제 업무 핵심을 찾으세요. "
        "2) requirements와 preferred에서는 학력/경력/우대 문구를 버리고, 도메인·시스템·실험·데이터 신호만 남기세요. "
        "3) skills는 기술명 보강용으로만 쓰되, 그것만으로 summary를 만들지 마세요. "
        "4) focusLabel은 가장 구체적인 중심 축 하나만 고르세요. "
        "근거가 부족한 경우에만 quality는 low로 두세요. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v6": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\"}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "1) detailBody와 tasks에 구체 업무가 거의 없고 공고명, 전형, 병역, 지원 안내, 양식, 복지, 회사 소개가 대부분이면 quality는 low로 두고 summary, focusLabel, keywords는 비우세요. "
        "2) summary는 16~32자의 한국어 명사구 하나로, 실제 업무 대상과 작업 맥락이 함께 보이게 쓰세요. title이나 roleDisplay를 그대로 복사하지 마세요. "
        "3) focusLabel은 quality가 low가 아니면 반드시 1개를 채우고, 가장 중심이 되는 구체 표현 하나만 쓰세요. role, 회사명, 조직명, 직무내용, 전반, 전문성, 별도, 연구, 개발, 분석 같은 넓은 말은 금지합니다. "
        "4) keywords는 3~5개 짧은 명사구입니다. 첫 keyword는 focusLabel과 같아도 되고, 나머지는 다른 축으로 보강하세요. "
        "허용 축: 도메인, 데이터, 모델/방법, 시스템/파이프라인, 검증/운영. "
        "금지 예: 위한, 또는, 관련, 학사, 석사, 박사, 경력, 제품, 서비스, 직무내용, 공고문, 전문연구요원. "
        "좋은 예: '생체신호 처리와 신뢰도 평가 알고리즘 개발' / focusLabel '생체신호'. "
        "좋은 예: 'LLM 검색 시스템 설계와 성능 개선' / focusLabel 'RAG'. "
        "좋은 예: '제품 성장 지표 설계와 실험 분석' / focusLabel '제품 성장 분석'. "
        "좋은 예: '디지털 농업 플랫폼 도입과 현장 컨설팅' / focusLabel '디지털 농업'. "
        "나쁜 예: '인공지능 연구', 'Talent Pool (R&D)', '직무내용', 'Senior Applied Scientist'. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v7": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\"}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "판단 규칙은 4개만 지키세요. "
        "1) 구체 업무가 없으면 low입니다. 공고명, 전형, 병역, 양식, 우대, 회사 소개가 대부분이면 summary, focusLabel, keywords를 모두 비우고 quality는 low로 두세요. "
        "2) summary는 16~30자의 한국어 게시용 명사구 하나입니다. title이나 roleDisplay를 그대로 반복하지 말고, 실제 업무 대상과 작업 맥락을 함께 써야 합니다. "
        "3) focusLabel은 low가 아니면 반드시 1개를 채우세요. 가장 구체적인 중심 축 하나만 고르세요. 우선순위는 도메인/문제 > 시스템/파이프라인 > 모델/방법 > 스택입니다. "
        "4) keywords는 3~5개의 짧은 명사구입니다. 첫 keyword는 focusLabel과 같아도 되고, 나머지는 다른 축으로 보강하세요. 프레임워크만 나열하지 마세요. "
        "focusLabel과 keywords 금지어: 위한, 또는, 관련, 학사, 석사, 박사, 경력, 제품, 서비스, 직무내용, 전문성, 별도, 모든, 연구, 개발, 분석, 공고문, 전문연구요원, 조직명, 회사명. "
        "summary 금지형: 제목 echo, role echo, '인공지능 연구', '데이터 분석가', 'Senior Applied Scientist', 'Talent Pool (R&D)'. "
        "좋은 예시 1: detailBody가 생체신호 처리, 노이즈 제거, 신뢰도 평가, 환자 모니터링이면 summary는 '생체신호 처리와 신뢰도 평가 알고리즘 개발', focusLabel은 '생체신호', keywords는 ['생체신호','신호 처리','노이즈 제거','신뢰도 평가'] 입니다. "
        "좋은 예시 2: 앱 성장, 퍼널, 코호트, CRM, 리텐션, A/B 테스트가 보이면 summary는 '앱 성장 채널 운영과 리텐션 최적화', focusLabel은 '그로스 마케팅', keywords는 ['그로스 마케팅','퍼포먼스 마케팅','CRM','리텐션','A/B 테스트'] 입니다. "
        "좋은 예시 3: 디지털 농업 플랫폼 도입, 현장 컨설팅, 농업 데이터 분석이 보이면 summary는 '디지털 농업 플랫폼 도입과 현장 컨설팅', focusLabel은 '디지털 농업' 입니다. "
        "좋은 예시 4: LLM, 검색, 성능 개선, MLOps가 보이면 summary는 'LLM 검색 시스템 설계와 성능 개선', focusLabel은 'RAG', keywords는 ['LLM','NLP','RAG','MLOps','PyTorch'] 입니다. "
        "낮은 예시 1: '[AI실증지원사업단] 제4차 사업단 직원 채용', '(양식) 연구계획서' 같은 내용만 있으면 summary='', focusLabel='', keywords=[], quality='low' 입니다. "
        "낮은 예시 2: 'Talent Pool (R&D)', 'Senior Applied Scientist', '전문연구요원 (R&D)'처럼 직무 설명 없이 제목만 있으면 summary='', focusLabel='', keywords=[], quality='low' 입니다. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v8": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\",\"structuredSignals\":{\"domainSignals\":[\"...\"],\"problemSignals\":[\"...\"],\"systemSignals\":[\"...\"],\"modelSignals\":[\"...\"],\"dataSignals\":[\"...\"],\"workflowSignals\":[\"...\"],\"roleSignals\":[\"...\"]}}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "핵심 목표는 화면용 keywords와 그래프용 structuredSignals를 함께 정확하게 만드는 것입니다. "
        "1) detailBody와 tasks에 구체 업무가 거의 없고 공고명, 전형, 지원 안내, 양식, 복지, 회사 소개가 대부분이면 quality는 low로 두고 summary, focusLabel, keywords, structuredSignals를 비우세요. "
        "2) summary는 16~32자의 한국어 명사구 하나이며, 실제 업무 대상과 작업 맥락이 함께 보여야 합니다. title이나 roleDisplay를 그대로 반복하지 마세요. "
        "3) focusLabel은 low가 아니면 반드시 1개를 채우고, 가장 중심이 되는 구체 표현 하나만 쓰세요. role, 회사명, 조직명, 제품, 서비스, 연구, 개발, 분석처럼 넓은 표현은 금지합니다. "
        "4) keywords는 3~5개의 짧은 명사구입니다. 첫 keyword는 focusLabel과 같아도 되고, 나머지는 도메인, 데이터, 모델/방법, 시스템/파이프라인, 검증/운영 중 다른 축으로 보강하세요. "
        "5) keywords와 structuredSignals에는 법/절차/우대/경력/학위/지원 안내 문구를 넣지 마세요. 예: '채용절차법', '이상이신', '경험자', '가능자', '우대합니다', '있습니다'는 절대 금지입니다. "
        "6) 같은 계열의 중복 표현을 동시에 쓰지 마세요. 예: 'LLM'과 '거대 언어 모델' 중 하나만, '컴퓨터 비전'과 '비전' 중 하나만, '고객 관계 관리'와 'CRM' 중 하나만 남기세요. 더 표준적인 하나만 선택하세요. "
        "7) structuredSignals는 다음 카테고리만 사용하세요: domainSignals, problemSignals, systemSignals, modelSignals, dataSignals, workflowSignals, roleSignals. "
        "각 카테고리에는 근거가 있을 때만 0~3개 넣고, 전부 짧은 표준 명사구로 쓰세요. "
        "권장 표준 예시는 'RAG', '제품 성장 분석', '그로스 마케팅', '고객 관계 관리', '컴퓨터 비전', '멀티모달', '의료 데이터', '생체신호', '데이터 파이프라인', '모델 서빙', '클라우드', 'MLOps', '검증', 'A/B 테스트' 입니다. "
        "좋은 예: summary 'LLM 검색 시스템 설계와 성능 개선', focusLabel 'RAG', keywords ['RAG','LLM','검색','모델 서빙'], structuredSignals.problemSignals ['RAG'], modelSignals ['LLM'], systemSignals ['모델 서빙']. "
        "좋은 예: summary '제품 성장 지표 설계와 실험 분석', focusLabel '제품 성장 분석', keywords ['제품 성장 분석','A/B 테스트','고객 관계 관리','SQL'], structuredSignals.problemSignals ['제품 성장 분석'], workflowSignals ['A/B 테스트'], dataSignals ['SQL']. "
        "나쁜 예: '인공지능 연구', 'Talent Pool (R&D)', '직무내용', 'Senior Applied Scientist', '경험자', '이상이신'. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v9": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\",\"structuredSignals\":{\"domainSignals\":[\"...\"],\"problemSignals\":[\"...\"],\"systemSignals\":[\"...\"],\"modelSignals\":[\"...\"],\"dataSignals\":[\"...\"],\"workflowSignals\":[\"...\"],\"roleSignals\":[\"...\"]}}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "1) detailBody와 tasks에 구체 업무가 거의 없고 공고명, 전형, 지원 안내, 양식, 복지, 회사 소개가 대부분이면 quality는 low로 두고 summary, focusLabel, keywords, structuredSignals를 비우세요. "
        "반대로 실제 시스템 개발, 서비스 운영, 데이터 처리, 실험 분석, 도메인 컨설팅 업무가 구체적으로 있으면 AI 신호가 약해도 low로 내리지 마세요. "
        "2) summary는 16~32자의 한국어 명사구 하나이며, 실제 업무 대상과 작업 맥락이 함께 보여야 합니다. title이나 roleDisplay를 그대로 반복하지 마세요. "
        "3) focusLabel은 low가 아니면 반드시 1개를 채우고, 가장 구체적인 중심 축 하나만 고르세요. "
        "focusLabel 우선순위는 도메인/문제 > 시스템/파이프라인 > 모델/방법 > 프레임워크/언어 입니다. "
        "따라서 심전도/생체신호/디지털 농업/컴퓨터 비전/그로스 마케팅/제품 성장 분석 같은 구체 축이 보이면 "
        "'의료 데이터', '데이터 분석', '웹 서비스 개발', 'PyTorch', 'SQL', 'BigQuery', '대시보드', '클라우드' 같은 넓은 표현을 focusLabel로 쓰면 안 됩니다. "
        "4) keywords는 3~5개 짧은 명사구입니다. 첫 keyword는 focusLabel과 같아도 되고, 나머지는 도메인, 데이터, 모델/방법, 시스템/파이프라인, 검증/운영 중 다른 축으로 보강하세요. "
        "5) keywords와 structuredSignals에는 법/절차/우대/경력/학위/지원 안내 문구를 넣지 마세요. 예: '채용절차법', '이상이신', '경험자', '가능자', '우대합니다', '있습니다'는 절대 금지입니다. "
        "6) 같은 계열의 중복 표현을 동시에 쓰지 마세요. 'LLM'과 '거대 언어 모델', '컴퓨터 비전'과 '비전', '고객 관계 관리'와 'CRM'처럼 거의 같은 의미면 더 표준적인 하나만 남기세요. "
        "7) structuredSignals는 domainSignals, problemSignals, systemSignals, modelSignals, dataSignals, workflowSignals, roleSignals 만 사용하고, 각 카테고리에 0~3개만 넣으세요. "
        "8) 구체 예시: 앱 성장, 퍼널, 코호트, CRM, 리텐션, 캠페인 최적화가 보이면 focusLabel은 '그로스 마케팅' 또는 '제품 성장 분석'이어야지 '대시보드'가 아닙니다. "
        "심전도, ECG, 환자 모니터링이 보이면 focusLabel은 '심전도' 또는 '생체신호'여야지 '의료 데이터'가 아닙니다. "
        "컴퓨터 비전, VLM, 비전 솔루션이 보이면 focusLabel은 '컴퓨터 비전'이어야지 'PyTorch'가 아닙니다. "
        "디지털 농업, 위성, GIS, 농업 현장 도입이 보이면 focusLabel은 '디지털 농업'이어야지 '데이터 분석'이 아닙니다. "
        "좋은 예: summary '제품 성장 지표 설계와 실험 분석', focusLabel '제품 성장 분석', keywords ['제품 성장 분석','A/B 테스트','고객 관계 관리','SQL']. "
        "좋은 예: summary '컴퓨터 비전 기반 비전 솔루션 설계와 개발', focusLabel '컴퓨터 비전', keywords ['컴퓨터 비전','VLM','PyTorch','엣지 배포']. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v10": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\",\"structuredSignals\":{\"domainSignals\":[\"...\"],\"problemSignals\":[\"...\"],\"systemSignals\":[\"...\"],\"modelSignals\":[\"...\"],\"dataSignals\":[\"...\"],\"workflowSignals\":[\"...\"],\"roleSignals\":[\"...\"]}}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "1) detailBody와 tasks에 구체 업무가 거의 없고 공고명, 전형, 지원 안내, 양식, 복지, 회사 소개가 대부분이면 quality는 low로 두고 summary, focusLabel, keywords, structuredSignals를 비우세요. "
        "반대로 실제 시스템 개발, 데이터 처리, 성능 검증, 실험 분석, 운영 자동화, 도메인 컨설팅 업무가 구체적이면 AI 신호가 약해도 low로 내리지 마세요. "
        "2) summary는 16~32자의 한국어 명사구 하나이며, 실제 업무 대상과 작업 맥락이 함께 보여야 합니다. title이나 roleDisplay를 그대로 반복하지 마세요. "
        "3) focusLabel은 low가 아니면 반드시 1개를 채우고, 가장 구체적인 중심 축 하나만 고르세요. "
        "focusLabel 우선순위는 도메인/문제 > 시스템/파이프라인 > 모델/방법 > 프레임워크/언어 입니다. "
        "도메인이나 문제 축이 있으면 'Python', 'SQL', 'PyTorch', 'BigQuery', '대시보드', '클라우드', '데이터 분석', '의료 데이터', '컴퓨터 비전'처럼 더 넓은 표현으로 내려가지 마세요. "
        "4) keywords는 3~5개의 짧은 명사구입니다. 첫 keyword는 focusLabel과 같아도 되고, 나머지는 도메인, 데이터, 모델/방법, 시스템/파이프라인, 검증/운영 축에서 보강하세요. "
        "5) keywords와 structuredSignals에는 법/절차/우대/경력/학위/지원 안내 문구를 넣지 마세요. 예: '채용절차법', '이상이신', '경험자', '가능자', '우대합니다', '있습니다'는 절대 금지입니다. "
        "6) 거의 같은 의미의 중복 표현은 하나만 남기세요. 예: 'CRM'과 '고객 관계 관리', '컴퓨터 비전'과 '비전', 'LLM'과 '거대 언어 모델'. 더 표준적이고 구체적인 하나를 선택하세요. "
        "7) structuredSignals는 domainSignals, problemSignals, systemSignals, modelSignals, dataSignals, workflowSignals, roleSignals 만 사용하고, 각 카테고리에 0~3개만 넣으세요. "
        "8) 중요 경계 규칙: "
        "앱 사용자 확보, 활성, 전환, 퍼포먼스 광고, 앱 스토어 최적화, CRM, 리텐션 캠페인, 코호트, 퍼널이 함께 보이면 focusLabel은 '그로스 마케팅' 입니다. "
        "제품 지표 설계, 퍼널 분석, 코호트 분석, A/B 테스트, 실험 설계, 의사결정 지원이 중심이면 focusLabel은 '제품 성장 분석' 입니다. "
        "고객 관계 관리 자체가 중심 업무일 때만 focusLabel을 '고객 관계 관리'로 쓰고, 성장/획득/리텐션 최적화 맥락이면 '그로스 마케팅'을 우선합니다. "
        "의료영상, 영상의학, 의료기기 성능 검증, 임상연구 설계, 임상시험 데이터 분석이 보이면 focusLabel은 '의료영상' 또는 '임상시험'이어야지 '컴퓨터 비전'이나 '파이썬'이 아닙니다. "
        "심전도, ECG, 생체신호, 환자 모니터링이 보이면 focusLabel은 '심전도' 또는 '생체신호'입니다. "
        "컴퓨터 비전, VLM, 비전 솔루션, 실시간 인식, 산업 안전/제조 비전이 보이면 focusLabel은 '컴퓨터 비전'입니다. "
        "디지털 농업, 위성, GIS, 센서, 농업 현장 도입, 농업 컨설팅이 보이면 focusLabel은 '디지털 농업'입니다. "
        "좋은 예: summary '앱 성장 채널 운영과 리텐션 최적화', focusLabel '그로스 마케팅', keywords ['그로스 마케팅','CRM','리텐션','코호트 분석','A/B 테스트']. "
        "좋은 예: summary '제품 성장 지표 설계와 실험 분석', focusLabel '제품 성장 분석', keywords ['제품 성장 분석','A/B 테스트','코호트 분석','SQL']. "
        "좋은 예: summary '의료영상 데이터 처리와 의료기기 성능 검증', focusLabel '의료영상', keywords ['의료영상','임상시험','의료기기','파이썬']. "
        "좋은 예: summary '심전도 신호 기반 딥러닝 모델 실험과 임상 데이터 분석', focusLabel '심전도', keywords ['심전도','의료 데이터','딥러닝','코호트 분석']. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v11": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\",\"structuredSignals\":{\"domainSignals\":[\"...\"],\"problemSignals\":[\"...\"],\"systemSignals\":[\"...\"],\"modelSignals\":[\"...\"],\"dataSignals\":[\"...\"],\"workflowSignals\":[\"...\"],\"roleSignals\":[\"...\"]}}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "1) detailBody와 tasks에 구체 업무가 거의 없고 공고명, 전형, 지원 안내, 양식, 복지, 회사 소개가 대부분이면 quality는 low로 두고 summary, focusLabel, keywords, structuredSignals를 비우세요. "
        "반대로 백엔드 개발, 클라우드 운영, 서비스 배포, 데이터 처리, 품질 관리, 실험 분석처럼 실제 업무가 구체적이면 AI 신호가 약해도 low로 내리지 마세요. "
        "2) summary는 16~32자의 한국어 명사구 하나이며, 실제 업무 대상과 작업 맥락이 함께 보여야 합니다. title이나 roleDisplay를 그대로 반복하지 마세요. "
        "3) focusLabel은 low가 아니면 반드시 1개를 채우고, 문제/도메인 신호가 있으면 반드시 그 축에서 고르세요. "
        "focusLabel 우선순위는 문제/도메인 > 시스템/파이프라인 > 모델/방법 > 프레임워크/도구 입니다. "
        "따라서 '데이터 파이프라인', '클라우드', 'MLOps', 'SQL', 'BigQuery', 'EMR', 'PyTorch'는 보조 keyword로는 가능하지만 문제/도메인 신호가 있을 때 focusLabel로 쓰면 안 됩니다. "
        "4) 생체신호, 심전도, 신호 처리, 환자 모니터링, 신뢰도 평가, 노이즈 제거가 보이면 focusLabel은 '생체신호' 또는 '심전도'만 허용하고 '데이터 파이프라인'으로 일반화하지 마세요. "
        "5) 앱 성장, 리텐션, 퍼널, 코호트, CRM, 캠페인, 유저 행동, A/B 테스트가 보이면 focusLabel은 '그로스 마케팅' 또는 '제품 성장 분석'만 허용하고 '고객 관계 관리', 'SQL', 'BigQuery'로 내리지 마세요. "
        "성장 채널 운영, 획득, 리텐션 최적화가 중심이면 '그로스 마케팅', 지표 설계, 실험 분석, 의사결정 지원이 중심이면 '제품 성장 분석'을 선택하세요. "
        "6) 컴퓨터 비전, 비전, 영상, 생성형 AI, 시공간 데이터, 3D가 함께 보이면 focusLabel은 '컴퓨터 비전'을 우선하고, '3D 공간 이해'나 '시공간 데이터'는 keyword로만 보강하세요. "
        "로봇 제어, 동작 인식, 시뮬레이션, 강화학습이 보이면 focusLabel은 '로보틱스'를 우선하고, 더 좁은 표현은 keyword로만 보강하세요. "
        "7) keywords는 3~5개만 쓰고, 첫 2개 안에 반드시 focusLabel과 그 focus를 직접 설명하는 구체 keyword 1개를 넣으세요. 도구/인프라 keyword는 최대 2개까지만 허용합니다. "
        "8) keywords와 structuredSignals에는 법/절차/우대/경력/학위/지원 안내 문구를 넣지 마세요. 예: '채용절차법', '이상이신', '경험자', '가능자', '우대합니다', '있습니다'는 절대 금지입니다. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v12": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\",\"structuredSignals\":{\"domainSignals\":[\"...\"],\"problemSignals\":[\"...\"],\"systemSignals\":[\"...\"],\"modelSignals\":[\"...\"],\"dataSignals\":[\"...\"],\"workflowSignals\":[\"...\"],\"roleSignals\":[\"...\"]}}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "1) 공고가 실제 JD가 아니라 채용안내, 인재풀 등록, 회사소개, 공고 모음, 행정 공지, 양식 안내면 quality는 low로 두고 summary, focusLabel, keywords, structuredSignals를 비우세요. "
        "2) 반대로 detailBody가 빈약해도 title 자체가 구체 전문 포지션이고, requirements/preferred/skills에 그 전문성을 뒷받침하는 신호가 있으면 low로 내리지 마세요. "
        "예: SoC Verification Engineer, GPU 최적화 엔지니어, 생체신호 FE 개발자, Senior Machine Learning Engineer 처럼 제목만으로도 전문 축이 명확할 수 있습니다. "
        "3) 이 경우 summary는 title을 그대로 복사하지 말고 실제 업무 맥락이 느껴지는 짧은 한국어 명사구로 바꾸세요. "
        "예: 'SoC 검증 환경 구축과 테스트벤치 개발', 'GPU 추론 최적화와 클라우드 운영', '생체신호 기반 의료 제품 프론트엔드 개발'. "
        "4) focusLabel은 low가 아니면 반드시 1개를 채우고, 가장 구체적인 문제/도메인/시스템 축을 선택하세요. "
        "focusLabel 우선순위는 문제/도메인 > 시스템/파이프라인 > 모델/방법 > 도구 입니다. "
        "따라서 생체신호, 심전도, 컴퓨터 비전, 검증, GPU 최적화, 로보틱스 같은 축이 보이면 SQL, Python, PyTorch, BigQuery, 클라우드 같은 넓은 표현을 focusLabel로 쓰면 안 됩니다. "
        "5) keywords는 3~5개 짧은 명사구입니다. 첫 keyword는 focusLabel과 같아도 되고, 나머지는 title/requirements/skills가 지지하는 다른 축으로만 보강하세요. "
        "6) keywords와 structuredSignals에는 법/절차/우대/경력/학위/지원 안내 문구를 넣지 마세요. 예: '채용절차법', '이상이신', '경험자', '가능자', '우대합니다', '있습니다'는 절대 금지입니다. "
        "7) title만 회사명/브랜드명/Recruitment/인재채용/멘토풀/전문연구요원/산업기능요원처럼 실제 업무 축이 부족하면 계속 low가 맞습니다. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v13": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\",\"structuredSignals\":{\"domainSignals\":[\"...\"],\"problemSignals\":[\"...\"],\"systemSignals\":[\"...\"],\"modelSignals\":[\"...\"],\"dataSignals\":[\"...\"],\"workflowSignals\":[\"...\"],\"roleSignals\":[\"...\"]},\"sectionSignalFacets\":{\"detailBody\":{\"keyword\":[\"...\"],\"tag\":[\"...\"],\"context\":[\"...\"]},\"tasks\":{\"keyword\":[\"...\"],\"tag\":[\"...\"],\"context\":[\"...\"]},\"requirements\":{\"keyword\":[\"...\"],\"tag\":[\"...\"],\"context\":[\"...\"]},\"preferred\":{\"keyword\":[\"...\"],\"tag\":[\"...\"],\"context\":[\"...\"]},\"skills\":{\"keyword\":[\"...\"],\"tag\":[\"...\"],\"context\":[\"...\"]}}}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "1) 공고가 실제 JD가 아니라 채용안내, 인재풀 등록, 회사소개, 공고 모음, 행정 공지, 양식 안내면 quality는 low로 두고 summary, focusLabel, keywords, structuredSignals, sectionSignalFacets를 비우세요. "
        "2) 반대로 detailBody가 빈약해도 title 자체가 구체 전문 포지션이고, requirements/preferred/skills에 그 전문성을 뒷받침하는 신호가 있으면 low로 내리지 마세요. "
        "3) summary는 title 복사가 아니라 실제 업무 대상과 작업 맥락이 드러나는 16~32자 한국어 명사구 하나여야 합니다. "
        "4) focusLabel은 low가 아니면 반드시 1개를 채우고, 가장 구체적인 문제/도메인/시스템 축을 선택하세요. 문제/도메인 > 시스템/파이프라인 > 모델/방법 > 도구 순입니다. "
        "5) keywords는 3~5개의 짧은 명사구입니다. 첫 keyword는 focusLabel과 같아도 되고, 나머지는 title/requirements/skills가 지지하는 다른 축으로만 보강하세요. "
        "6) keywords와 structuredSignals와 sectionSignalFacets에는 법/절차/우대/경력/학위/지원 안내 문구를 넣지 마세요. 예: '채용절차법', '이상이신', '경험자', '가능자', '우대합니다', '있습니다', '별도', '미기재'는 절대 금지입니다. "
        "7) sectionSignalFacets는 각 섹션의 의미를 따로 보존하기 위한 값입니다. "
        "detailBody, tasks, requirements, preferred, skills 각각에 대해 keyword/tag/context만 사용하세요. "
        "keyword는 그 섹션의 핵심 문제·업무·자격 축 0~4개, tag는 보조 도메인/데이터/모델 축 0~4개, context는 시스템/운영/검증/파이프라인 맥락 0~4개입니다. "
        "8) 한 섹션이 비어 있거나 '별도 우대사항 미기재' 같은 placeholder면 그 섹션의 keyword/tag/context는 모두 빈 배열이어야 합니다. 억지로 다른 섹션 표현을 복사하지 마세요. "
        "9) 같은 term을 모든 섹션에 반복해서 넣지 마세요. 실제로 그 섹션에 근거가 있을 때만 넣으세요. 예를 들어 requirements는 자격/역량 축, preferred는 우대 배경, tasks는 수행 업무가 드러나야 합니다. "
        "10) 생체신호, 심전도, 컴퓨터 비전, 검증, GPU 최적화, 로보틱스 같은 구체 축이 보이면 SQL, Python, PyTorch, BigQuery, 클라우드 같은 넓은 표현으로 focusLabel을 내리지 마세요. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "field_aware_v14": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\",\"structuredSignals\":{\"domainSignals\":[\"...\"],\"problemSignals\":[\"...\"],\"systemSignals\":[\"...\"],\"modelSignals\":[\"...\"],\"dataSignals\":[\"...\"],\"workflowSignals\":[\"...\"],\"roleSignals\":[\"...\"]},\"sectionSignalFacets\":{\"detailBody\":{\"keyword\":[\"...\"],\"tag\":[\"...\"],\"context\":[\"...\"]},\"tasks\":{\"keyword\":[\"...\"],\"tag\":[\"...\"],\"context\":[\"...\"]},\"requirements\":{\"keyword\":[\"...\"],\"tag\":[\"...\"],\"context\":[\"...\"]},\"preferred\":{\"keyword\":[\"...\"],\"tag\":[\"...\"],\"context\":[\"...\"]},\"skills\":{\"keyword\":[\"...\"],\"tag\":[\"...\"],\"context\":[\"...\"]}}}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "1) 공고가 실제 JD가 아니라 채용안내, 인재풀 등록, 회사소개, 공고 모음, 행정 공지, 양식 안내면 quality는 low로 두고 summary, focusLabel, keywords, structuredSignals, sectionSignalFacets를 비우세요. "
        "2) summary는 title 복사가 아니라 실제 업무 대상과 작업 맥락이 드러나는 16~32자 한국어 명사구 하나여야 합니다. "
        "3) focusLabel은 low가 아니면 반드시 1개를 채우고, 문제/도메인 > 시스템/파이프라인 > 모델/방법 > 도구 순으로 가장 구체적인 중심 축을 선택하세요. "
        "4) ONNX, TensorFlow, PyTorch, SQL, BigQuery, AWS, Linux, Docker, Kubernetes, SDK, API, GPU 는 keyword와 structuredSignals에는 들어갈 수 있지만 focusLabel로는 금지입니다. 단, 다른 문제/도메인/시스템 축이 전혀 없을 때만 예외입니다. "
        "5) FP&A, financial planning, 손익, 예산, ROI, 비용-편익, variance, 실적 예측 문맥이면 로보틱스/컴퓨터 비전/RAG/NPU 같은 deeptech label을 출력하지 마세요. 이런 경우 focusLabel은 재무 계획 분석, 재무 모델, 손익 분석 같은 축이어야 합니다. "
        "6) Process Innovation, ERP/CRM 기반 KPI·OKR 운영 자동화, 표준 운영 절차, SOP, 플랫폼 운영/작품 운영 전략 문맥이면 그로스 마케팅이나 CRM을 자동으로 고르지 마세요. 성장 채널/리텐션/획득/퍼포먼스 광고가 명시될 때만 그로스 마케팅을 쓰세요. "
        "7) 시뮬레이션이라는 단어 하나만 보고 로보틱스로 분류하지 마세요. 로봇, 로보틱스, 제어, 동작 인식, 강화학습, Isaac Sim, ROS 같은 근거가 함께 있을 때만 로보틱스를 쓰세요. "
        "8) 문제/도메인 근거가 없고 시스템/도구 근거만 있으면 domainSignals와 problemSignals는 비워두세요. SQL, BigQuery, Airflow, dbt, AWS, 클라우드, 데이터 파이프라인은 dataSignals/systemSignals로만 기록하세요. "
        "9) keywords는 3~5개의 짧은 명사구입니다. 첫 keyword는 focusLabel과 같아도 되고, 나머지는 다른 축으로 보강하세요. 도구/프레임워크 keyword는 최대 2개까지만 허용합니다. "
        "10) sectionSignalFacets는 각 섹션 의미를 따로 보존하는 값입니다. placeholder 섹션은 빈 배열이어야 하고, 실제 근거가 없는 term을 다른 섹션에서 복사하지 마세요. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
    "gemma_focus_v1": (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 구조화 추출 편집자입니다. "
        "반드시 roleDisplay, title, detailBody, tasks, requirements, preferred, skills만 근거로 쓰고 입력에 없는 사실은 절대 지어내지 마세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"summary\":\"...\",\"keywords\":[\"...\"],\"focusLabel\":\"...\",\"quality\":\"high\"}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "이 작업의 핵심은 focusLabel을 정확히 고르는 것입니다. "
        "focusLabel은 가장 중심이 되는 도메인·문제·업무 축 1개만 써야 하며, low가 아니면 반드시 채우세요. "
        "focusLabel 우선순위는 도메인/문제 > 시스템/파이프라인 > 모델 계열 > 프레임워크/언어 입니다. "
        "따라서 더 구체적인 도메인이나 문제 축이 있으면 Python, SQL, PyTorch, TensorFlow, Linux, AWS, 학습 파이프라인 같은 말은 focusLabel로 쓰면 안 됩니다. "
        "예를 들어 심전도와 임상 데이터가 보이면 focusLabel은 '심전도' 입니다. "
        "LLM, 검색, 벡터 데이터베이스가 보이면 focusLabel은 'RAG' 입니다. "
        "앱 성장, CRM, 리텐션, 퍼포먼스 마케팅이 보이면 focusLabel은 '그로스 마케팅' 입니다. "
        "제품 지표, 퍼널, 코호트, A/B 테스트가 보이면 focusLabel은 '제품 성장 분석' 입니다. "
        "로봇, 강화 학습, 시뮬레이션, 동작 인식이 보이면 focusLabel은 '로보틱스' 입니다. "
        "컴퓨터 비전과 VLM이 보이면 focusLabel은 '컴퓨터 비전' 입니다. "
        "클라우드, AWS, Linux가 함께 보이고 서비스 운영/배포 맥락이 있으면 focusLabel은 '클라우드' 입니다. "
        "summary는 18~40자의 한국어 구문 하나이며 실제 업무 대상을 보여줘야 합니다. "
        "title, roleDisplay, 회사명 반복은 금지합니다. "
        "keywords는 2~5개의 짧은 명사구입니다. "
        "첫 keyword는 focusLabel과 같아도 되고, 나머지는 다른 축으로 보강하세요. "
        "keywords는 풍부해도 되지만, focusLabel은 넓은 스택명보다 더 구체적인 중심 축을 선택해야 합니다. "
        "학력, 경력, 역할명, 조직명, 제품/서비스, 조사형 표현은 summary, keywords, focusLabel에서 금지합니다. "
        "근거가 부족한 경우에만 summary는 빈 문자열, keywords는 빈 배열, focusLabel은 빈 문자열, quality는 low로 두세요. "
        "quality는 high, medium, low 중 하나만 사용하세요."
    ),
}


def normalize_summary_prompt_profile_name(name: str) -> str:
    key = normalize_inline_text(name) or "field_aware_v3"
    return key if key in SUMMARY_PROMPT_PROFILES else "field_aware_v3"


def list_summary_prompt_profiles() -> list[str]:
    return list(SUMMARY_PROMPT_PROFILES.keys())


def get_summary_prompt_profile(name: str) -> str:
    key = normalize_summary_prompt_profile_name(name)
    return SUMMARY_PROMPT_PROFILES.get(key, SUMMARY_PROMPT_PROFILES["baseline_v1"])


def build_messages(job: dict) -> list[dict]:
    system_prompt = (
        "You are a data-normalization assistant for Korean hiring intelligence. "
        "Read a scraped AI/data job posting and return strict JSON only. "
        "Do not explain. "
        "Return an object with exactly these keys: "
        "experience_label, track_labels, focus_labels, skills, reviewer_note. "
        "Rules: experience_label must be one short Korean label. "
        "track_labels and focus_labels must be arrays of short Korean labels. "
        "skills must be an array of canonical English skill names. "
        "If evidence is weak, keep arrays empty instead of hallucinating."
    )

    payload = {
        "company": job.get("company", ""),
        "title": job.get("title", ""),
        "role": job.get("role", ""),
        "raw_experience": job.get("experience", ""),
        "raw_track": job.get("track", ""),
        "raw_focus": job.get("focus", ""),
        "skills_from_scraper": job.get("skills", []),
        "group_summary": job.get("groupSummary", ""),
        "tasks": compact_lines(job.get("tasks", [])),
        "requirements": compact_lines(job.get("requirements", [])),
        "preferred": compact_lines(job.get("preferred", [])),
    }

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def normalize_response(payload: dict) -> dict:
    blocked = {"", "미분류", "unknown", "n/a", "none", "null"}

    def normalize_string(value):
        normalized = re.sub(r"\s+", " ", str(value or "").strip())
        if normalized.lower() in blocked or normalized in blocked:
            return ""
        return normalized

    def normalize_list(values):
        result = []
        seen = set()
        if not isinstance(values, list):
            return result
        for value in values:
            item = normalize_string(value)
            if not item or item in seen:
                continue
            seen.add(item)
            result.append(item)
        return result

    return {
        "experience_label": normalize_string(payload.get("experience_label", "")),
        "track_labels": normalize_list(payload.get("track_labels", [])),
        "focus_labels": normalize_list(payload.get("focus_labels", [])),
        "skills": normalize_list(payload.get("skills", [])),
        "reviewer_note": normalize_string(payload.get("reviewer_note", "")),
    }


def normalize_summary_items(payload: dict) -> list[dict]:
    items = payload.get("items", [])
    if not isinstance(items, list):
        return []

    result = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        job_id = normalize_inline_text(item.get("id", ""))
        role = normalize_inline_text(item.get("role", ""))
        summary = normalize_inline_text(item.get("summary", ""))
        focus_label = canonicalize_term(
            item.get("focusLabel", "") or item.get("focus_label", "")
        )
        quality = normalize_inline_text(item.get("quality", "")).lower()
        structured_signals = normalize_model_structured_signals(item.get("structuredSignals", {}) or item.get("structured_signals", {}))
        section_signal_facets = normalize_model_section_signal_facets(
            item.get("sectionSignalFacets", {}) or item.get("section_signal_facets", {})
        )
        keywords = []
        for keyword in item.get("keywords", []) if isinstance(item.get("keywords", []), list) else []:
            cleaned = canonicalize_term(keyword)
            if cleaned and not is_generic_keyword(cleaned) and cleaned not in keywords:
                keywords.append(cleaned)
        if quality not in {"high", "medium", "low"}:
            quality = "medium" if summary else "low"
        focus_label = choose_focus_label(role=role, summary=summary, focus_label=focus_label, keywords=keywords)
        if quality == "low":
            summary = ""
            keywords = []
            focus_label = ""
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)
        result.append(
            {
                "id": job_id,
                "role": role,
                "summary": summary,
                "keywords": keywords[:6],
                "focusLabel": focus_label[:24],
                "quality": quality,
                "structuredSignals": structured_signals,
                "sectionSignalFacets": section_signal_facets,
            }
        )
    return result


def build_compact_context_text(job: dict) -> str:
    compact = compact_job_for_summary(job)
    parts = []
    for key in ("detailBody", "tasks", "requirements", "preferred", "skills"):
        values = compact.get(key, [])
        if isinstance(values, list):
            parts.extend(values)
    return normalize_signal_text(" ".join(parts))


def build_focus_context_text(job: dict) -> str:
    compact = compact_job_for_summary(job)
    parts = []
    for key in ("detailBody", "tasks"):
        values = compact.get(key, [])
        if isinstance(values, list):
            parts.extend(values)
    return normalize_signal_text(" ".join(parts))


def build_focus_signal_text(job: dict) -> str:
    compact = compact_job_for_summary(job)
    parts = [build_focus_context_text(job)]
    parts.extend((compact.get("skills", []) or [])[:6])
    return normalize_signal_text(" ".join(part for part in parts if part))


def rebuild_keywords_from_focus_and_signals(job: dict, item: dict) -> list[str]:
    focus = canonicalize_term(item.get("focusLabel", ""))
    existing = [canonicalize_term(keyword) for keyword in item.get("keywords", []) or [] if canonicalize_term(keyword)]
    signals = item.get("structuredSignals", {}) or {}
    signal_values = []
    for key in ("problemSignals", "domainSignals", "dataSignals", "workflowSignals", "systemSignals", "modelSignals"):
        values = signals.get(key, []) if isinstance(signals.get(key, []), list) else []
        for value in values:
            cleaned = canonicalize_term(value)
            if cleaned:
                signal_values.append(cleaned)

    combined = normalize_signal_text(
        " ".join(
            [
                build_focus_signal_text(job),
                normalize_signal_text(item.get("summary", "")),
                focus,
                " ".join(existing),
                " ".join(signal_values),
            ]
        )
    )

    keywords: list[str] = []

    def append_keyword(value: str) -> None:
        cleaned = canonicalize_term(value)
        if not cleaned or is_generic_keyword(cleaned) or cleaned in keywords:
            return
        keywords.append(cleaned)

    if focus:
        append_keyword(focus)

    for patterns, label in FOCUS_KEYWORD_SUPPORT_RULES.get(focus, []):
        if contains_any_term(combined, patterns):
            append_keyword(label)

    for value in signal_values:
        append_keyword(value)

    for value in existing:
        append_keyword(value)

    filtered: list[str] = []
    tool_count = 0
    non_tool_count = 0
    for keyword in keywords:
        is_tool = keyword in TOOL_LIKE_KEYWORDS
        if is_tool and non_tool_count >= 2 and tool_count >= 2:
            continue
        filtered.append(keyword)
        if is_tool:
            tool_count += 1
        else:
            non_tool_count += 1
        if len(filtered) >= 5:
            break

    return filtered


def contains_any_term(text: str, terms: list[str]) -> bool:
    lowered = normalize_signal_text(text).lower()
    if not lowered:
        return False
    return any(normalize_signal_text(term).lower() in lowered for term in terms if term)


def override_focus_label_from_context(job: dict, current_focus: str, summary: str, keywords: list[str]) -> str:
    current = canonicalize_term(current_focus)
    signal_text = build_focus_signal_text(job)
    title_text = normalize_signal_text(job.get("title", ""))
    role_text = normalize_signal_text(job.get("roleDisplay", ""))
    summary_text = normalize_signal_text(summary)
    keyword_text = " ".join(canonicalize_term(keyword) for keyword in keywords if canonicalize_term(keyword))
    combined = normalize_signal_text(" ".join([title_text, role_text, signal_text, summary_text, keyword_text]))

    if not current or not combined:
        return current

    rag_terms = ["RAG", "검색증강생성", "하이브리드 검색", "벡터 데이터베이스", "지식 검색", "임베딩"]
    hybrid_terms = ["하이브리드", "온프레미스", "다중 리전", "멀티 클라우드", "쿠버네티스", "GPU 스케줄링"]
    dashboard_terms = ["대시보드", "태블로", "슈퍼셋", "BI", "마트 데이터", "데이터 마트"]
    tracking_terms = ["트래킹", "어트리뷰션", "MMP", "매체 최적화", "캠페인 운영"]
    crm_terms = ["CRM", "고객 관계 관리", "리텐션 캠페인", "푸시", "인앱 리텐션"]
    interpretation_terms = ["모델 해석", "표현 학습", "스케일링 법칙", "작동 원리", "동작 원리", "모델 아키텍처", "내부 구조 분석"]
    npu_terms = ["NPU", "엔피유", "접목", "적용"]
    mlops_terms = [
        "MLOps",
        "엠엘옵스",
        "머신러닝 파이프라인",
        "모델 서빙",
        "실험 추적",
        "메타데이터",
        "학습/추론 자동화",
        "서빙–모니터링",
        "개발–서빙–모니터링",
        "서빙-모니터링",
    ]
    infra_terms = ["인프라", "클라우드", "배포", "운영", "서빙"]
    cloud_terms = ["클라우드", "AWS", "에이더블유에스", "GCP", "지씨피", "멀티 클라우드"]
    data_analysis_terms = ["데이터 분석", "인사이트", "통찰", "센서", "위성", "지아이에스", "실행 가능한 통찰력"]
    document_install_terms = ["설치", "클러스터", "고객사 서버", "서버", "도입", "기술 지원"]
    robotics_terms = ["로봇", "로보틱스", "human-robot", "인간-로봇", "robotics"]
    cv_solution_terms = ["컴퓨터비전", "컴퓨터 비전", "비전 솔루션", "브이엘엠", "VLM"]
    simulation_3d_terms = ["Isaac Sim", "아이작 심", "ROS", "3D", "옴니버스", "시뮬레이션"]
    finance_terms = [
        "FP&A",
        "Financial Planning",
        "재무",
        "손익",
        "비용-편익",
        "ROI",
        "재무 예측",
        "실적",
        "variance",
    ]
    process_terms = [
        "Process Innovation",
        "전사 프로세스",
        "표준 운영 절차",
        "SOP",
        "운영 표준화",
        "업무 자동화",
        "ERP",
        "KPI",
        "OKR",
    ]
    growth_terms = ["리텐션", "퍼널", "코호트", "캠페인", "획득", "활성", "퍼포먼스 마케팅", "앱 스토어 최적화"]
    platform_terms = ["플랫폼 운영", "작품 운영", "웹툰 플랫폼", "프로모션", "서비스 운영"]
    ad_data_terms = ["광고", "Ads Ops", "광고 데이터", "광고 플랫폼", "데이터 파이프라인", "거버넌스"]
    ad_performance_terms = ["광고", "캠페인 성과", "캠페인 최적화", "모바일 앱 추적", "Growth Analytics", "통계 분석", "데이터 시각화"]
    model_optimization_terms = ["모델 변환", "연산자 호환성", "메모리 최적화", "양자화", "컴파일", "최적화"]

    if current in {"로보틱스", "SQL", "TensorFlow", "ONNX", "마케팅", "고객 관계 관리", "CRM", "광고"}:
        if contains_any_term(combined, finance_terms) and not contains_any_term(combined, robotics_terms):
            return "재무 계획 분석"
        if contains_any_term(combined, process_terms) and not contains_any_term(combined, growth_terms):
            return "프로세스 혁신"
        if contains_any_term(combined, platform_terms):
            return "웹툰 플랫폼" if contains_any_term(combined, ["웹툰", "웹소설"]) else "플랫폼 운영"
        if current in {"SQL", "광고", "마케팅"} and contains_any_term(combined, ad_data_terms):
            return "광고 데이터"
        if current in {"SQL", "광고", "마케팅"} and contains_any_term(combined, ad_performance_terms):
            return "광고 성과 분석"
        if current in {"TensorFlow", "ONNX", "PyTorch"} and contains_any_term(combined, model_optimization_terms):
            return "온디바이스 최적화" if contains_any_term(combined, ["온디바이스", "on-device", "edge", "디바이스"]) else "모델 최적화"

    if current in {"시스템 아키텍처", "아키텍처"}:
        if contains_any_term(combined, rag_terms):
            return "RAG"
        if contains_any_term(combined, hybrid_terms):
            return "하이브리드 인프라"
        if contains_any_term(combined, mlops_terms):
            return "MLOps"
        if contains_any_term(combined, ["자율주행"]):
            return "자율주행"
        if contains_any_term(combined, cloud_terms):
            return "클라우드"
        if contains_any_term(combined, infra_terms):
            return "인프라"

    if current in {"의료 데이터", "데이터 분석"} and contains_any_term(combined, rag_terms):
        return "RAG"

    if current == "의료 데이터":
        if contains_any_term(combined, ["심전도", "ECG", "이씨지"]):
            return "심전도"
        if contains_any_term(combined, ["생체신호", "신호 처리", "환자 모니터링"]):
            return "생체신호"

    if current in {"컴퓨터 비전", "인공지능 의료기기"}:
        if contains_any_term(combined, ["임상연구", "clinical research", "임상시험", "인허가", "소프트웨어 의료기기"]):
            if contains_any_term(combined, ["성능 검증", "검증", "validation"]):
                return "의료기기 성능 검증"
            return "임상시험"
        if contains_any_term(combined, ["영상의학", "의료영상", "판독", "의료 영상"]):
            return "의료영상"

    if current in {"최적화", "마케팅"} and contains_any_term(combined, tracking_terms):
        return "트래킹"

    if current in {"고객 관계 관리", "CRM"}:
        if contains_any_term(combined, ["앱", "리텐션", "퍼널", "코호트", "캠페인", "획득", "활성", "그로스"]):
            return "그로스 마케팅"

    if current in {"객체 인식"} and (
        contains_any_term(combined, ["비전 솔루션", "[solution]", "solution"])
        or (
            contains_any_term(combined, ["브이엘엠", "VLM"])
            and contains_any_term(combined, ["교통", "산업 안전", "제조", "실시간 인식", "실시간 분석"])
        )
    ):
        return "컴퓨터 비전"

    if current in {"3D 공간 이해"} and contains_any_term(
        combined,
        ["컴퓨터비전", "컴퓨터 비전", "비전", "영상", "시공간", "브이엘엠", "VLM"],
    ):
        return "컴퓨터 비전"

    if current in {"데이터 파이프라인", "파이프라인"}:
        if contains_any_term(combined, ["심전도", "ECG", "이씨지"]):
            return "심전도"
        if contains_any_term(combined, ["생체신호", "신호 처리", "환자 모니터링", "신뢰도 평가", "노이즈 제거"]):
            return "생체신호"
        if contains_any_term(combined, ["AWS", "리눅스", "Linux", "Node.js", "백엔드", "클라우드", "배포", "운영"]):
            return "클라우드"

    if current in {"LLM", "딥러닝"}:
        if contains_any_term(combined, ["표현 학습", "스케일링 법칙", "내부 구조 분석"]):
            return "모델 해석"
        if contains_any_term(combined, interpretation_terms):
            return "LLM 해석" if contains_any_term(combined, ["LLM", "엘엘엠"]) else "모델 해석"
        if contains_any_term(combined, npu_terms):
            return "NPU 적용"

    if current in {"설치"} and contains_any_term(combined, document_install_terms):
        return "인프라"

    if current in {"모델 서빙", "설치"} and contains_any_term(combined, hybrid_terms):
        return "하이브리드 인프라"

    if current in {"하이브리드 인프라", "인프라"}:
        if contains_any_term(combined, mlops_terms):
            return "MLOps"
        if contains_any_term(combined, cloud_terms):
            return "클라우드"

    if current in {"로보틱스"}:
        return "로보틱스"

    if current in {"로봇 시뮬레이션", "동작 인식", "강화학습", "강화 학습", "로봇 제어"} and contains_any_term(combined, robotics_terms):
        return "로보틱스"

    if current in {"그로스 마케팅", "제품 성장 분석"} and (
        contains_any_term(combined, dashboard_terms)
        or contains_any_term(combined, crm_terms)
        or contains_any_term(combined, tracking_terms)
    ):
        return current

    if current in {"광고", "마케팅"} and contains_any_term(combined, ad_data_terms):
        return "광고 데이터"

    if current in {"광고", "SQL"} and contains_any_term(combined, ad_performance_terms):
        return "광고 성과 분석"

    if current in {"디지털 농업"} and contains_any_term(combined, data_analysis_terms):
        return "디지털 농업"

    if current in {"심전도", "생체신호"} and contains_any_term(combined, ["의료 데이터", "EMR", "임상", "환자 모니터링"]):
        return current

    if current == "컴퓨터 비전" and contains_any_term(combined, cv_solution_terms + simulation_3d_terms):
        return "컴퓨터 비전"

    if current in {"문제 해결"} and not contains_any_term(combined, ["수학", "최적화", "알고리즘"]):
        return ""

    return current


def should_force_low_confidence(job: dict, compact_job: dict, item: dict) -> bool:
    signal_lines = sum(
        len(compact_job.get(key, []) or [])
        for key in ("detailBody", "tasks", "requirements", "preferred")
    )
    skill_count = len(compact_job.get("skills", []) or [])
    title = normalize_signal_text(job.get("title", "")).lower()
    summary = normalize_signal_text(item.get("summary", ""))
    keywords = [canonicalize_term(keyword) for keyword in item.get("keywords", []) or []]

    if signal_lines == 0 and skill_count <= 1:
        return True
    if signal_lines <= 1 and skill_count == 0:
        return True
    if re.search(r"(talent pool|직원\(계약직\) 채용|계약직 공고)", title) and signal_lines <= 1:
        return True
    if re.search(r"(^|\\b)recruitment(\\b|$)", title) and skill_count <= 1 and not re.search(r"(수학|최적화|알고리즘|cuda|pytorch|tensorflow)", summary):
        return True
    if summary and re.search(r"(기반 연구 수행|모델 개발과 테스트|연구 수행)$", summary) and signal_lines <= 1:
        return True
    if not summary and len(keywords) <= 1 and signal_lines <= 1:
        return True
    return False


def has_strong_input_signal(compact_job: dict) -> bool:
    detail_tasks = len(compact_job.get("detailBody", []) or []) + len(compact_job.get("tasks", []) or [])
    support_lines = len(compact_job.get("requirements", []) or []) + len(compact_job.get("preferred", []) or [])
    skills = len(compact_job.get("skills", []) or [])
    return detail_tasks >= 4 or (detail_tasks >= 2 and skills >= 2) or (support_lines >= 2 and skills >= 2) or skills >= 4


def should_retry_single_summary(job: dict, item: dict) -> bool:
    compact = compact_job_for_summary(job)
    if item.get("quality") == "low" and has_strong_input_signal(compact):
        return True

    focus_label = canonicalize_term(item.get("focusLabel", ""))
    keywords = [canonicalize_term(keyword) for keyword in item.get("keywords", []) or []]
    context_text = build_focus_context_text(job)
    synthesized = synthesize_focus_candidates(summary=context_text, keywords=keywords)

    if item.get("quality") != "low" and not focus_label and has_strong_input_signal(compact):
        return True
    if synthesized and focus_label and focus_label not in synthesized:
        if focus_label in BROAD_RETRY_FOCUS_LABELS or is_weak_focus_label(focus_label):
            return True
    if synthesized and not focus_label and item.get("quality") != "low":
        return True
    summary = normalize_signal_text(item.get("summary", ""))
    if summary and re.search(r"(연구 수행|모델 개발과 테스트|데이터 분석과 인사이트 제시)$", summary):
        return True
    return False


def postprocess_summary_items(items: list[dict], jobs: list[dict]) -> list[dict]:
    jobs_by_id = {job.get("id", ""): job for job in jobs}
    processed = []

    for item in items:
        job = jobs_by_id.get(item.get("id", ""))
        if not job:
            processed.append(item)
            continue

        compact = compact_job_for_summary(job)
        context_text = build_focus_context_text(job)
        keywords = [canonicalize_term(keyword) for keyword in item.get("keywords", []) or []]
        focus_label = choose_focus_label(
            role=item.get("role", "") or job.get("roleDisplay", ""),
            summary=item.get("summary", ""),
            focus_label=item.get("focusLabel", ""),
            keywords=keywords,
            context_text=context_text,
        )

        refined = {
            **item,
            "keywords": keywords[:6],
            "focusLabel": focus_label[:24],
        }
        if refined.get("quality") != "low":
            refined["focusLabel"] = override_focus_label_from_context(
                job,
                refined.get("focusLabel", ""),
                refined.get("summary", ""),
                refined.get("keywords", []),
            )[:24]
        if refined.get("quality") == "low":
            refined["summary"] = ""
            refined["keywords"] = []
            refined["focusLabel"] = ""
            refined["structuredSignals"] = build_structured_signals(
                job,
                refined,
                compact_job=compact,
            )
            refined["sectionSignalFacets"] = build_section_signal_facets(
                job,
                refined,
                compact_job=compact,
            )
            processed.append(refined)
            continue
        if refined.get("quality") != "low" and should_force_low_confidence(job, compact, refined):
            refined["summary"] = ""
            refined["keywords"] = []
            refined["focusLabel"] = ""
            refined["quality"] = "low"

        refined["structuredSignals"] = build_structured_signals(
            job,
            refined,
            compact_job=compact,
        )
        projected_focus = project_focus_label_from_structured_signals(
            refined.get("structuredSignals", {}) or {},
            refined.get("focusLabel", ""),
            refined.get("keywords", []) or [],
        )
        if should_apply_structured_focus_projection(
            refined.get("structuredSignals", {}) or {},
            refined.get("focusLabel", ""),
            projected_focus,
        ):
            refined["focusLabel"] = projected_focus[:24]
        refined["sectionSignalFacets"] = build_section_signal_facets(
            job,
            refined,
            compact_job=compact,
        )
        refined["keywords"] = rebuild_keywords_from_focus_and_signals(job, refined)
        processed.append(refined)

    return processed


def normalize_tone_legend_items(payload: dict) -> list[dict]:
    items = payload.get("items", [])
    if not isinstance(items, list):
        return []

    result = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        tone = re.sub(r"\s+", " ", str(item.get("tone", "")).strip())
        description = re.sub(r"\s+", " ", str(item.get("description", "")).strip())
        if not tone or not description or tone in seen:
            continue
        seen.add(tone)
        result.append({"tone": tone, "description": description[:120]})
    return result


def extract_json_object(content: str) -> dict:
    text = (content or "").strip()
    if not text:
        raise ValueError("Empty model response")

    candidates = [text]
    fenced_match = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.DOTALL)
    if fenced_match:
        candidates.insert(0, fenced_match.group(1))

    brace_match = re.search(r"(\{.*\})", text, re.DOTALL)
    if brace_match:
        candidates.insert(0, brace_match.group(1))

    for candidate in candidates:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            continue
    raise ValueError("Model response was not valid JSON")


def request_openai_compatible(config: dict, job: dict) -> dict:
    base_url = (config.get("baseUrl") or "").rstrip("/")
    model = (config.get("model") or "").strip()
    api_key = config.get("apiKey", "")
    temperature = float(config.get("temperature", 0.1))

    if not base_url:
        raise ValueError("baseUrl is required")
    if not model:
        raise ValueError("model is required")

    payload = {
        "model": model,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "messages": build_messages(job),
    }

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    referer = os.environ.get("APP_PUBLIC_URL")
    if referer:
        headers["HTTP-Referer"] = referer
        headers["X-Title"] = "career-dashboard"

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        body = json.loads(response.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    parsed = extract_json_object(content)
    return normalize_response(parsed)


def build_summary_messages(jobs: list[dict], prompt_profile: str = "field_aware_v3") -> list[dict]:
    system_prompt = get_summary_prompt_profile(prompt_profile)
    payload = {"jobs": [compact_job_for_summary(job) for job in jobs]}
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def request_batch_summaries(config: dict, jobs: list[dict], prompt_profile: str = "field_aware_v3") -> list[dict]:
    base_url = (config.get("baseUrl") or "").rstrip("/")
    model = (config.get("model") or "").strip()
    api_key = config.get("apiKey", "")
    temperature = float(config.get("temperature", 0.1))

    if not base_url:
        raise ValueError("baseUrl is required")
    if not model:
        raise ValueError("model is required")

    payload = {
        "model": model,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "messages": build_summary_messages(jobs, prompt_profile=prompt_profile),
    }

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    parsed = extract_json_object(content)
    items = normalize_summary_items(parsed)
    return postprocess_summary_items(items, jobs)


def request_summaries_resilient(config: dict, jobs: list[dict], prompt_profile: str = "field_aware_v3") -> list[dict]:
    jobs_by_id = {job["id"]: job for job in jobs}
    expected_ids = {job["id"] for job in jobs}
    summaries = [
        item
        for item in request_batch_summaries(config, jobs, prompt_profile=prompt_profile)
        if item["id"] in expected_ids
    ]
    returned = {item["id"] for item in summaries}

    suspicious_ids = {
        item["id"]
        for item in summaries
        if len(jobs) > 1 and should_retry_single_summary(jobs_by_id[item["id"]], item)
    }
    if suspicious_ids:
        summaries = [item for item in summaries if item["id"] not in suspicious_ids]
        returned = {item["id"] for item in summaries}

    if len(returned) == len(jobs) and not suspicious_ids:
        return summaries

    for job in jobs:
        if job["id"] in returned:
            continue
        single = request_batch_summaries(config, [job], prompt_profile=prompt_profile)
        valid_single = [item for item in single if item["id"] == job["id"]]
        if not valid_single and len(single) == 1:
            recovered = {**single[0], "id": job["id"]}
            valid_single = [recovered]
        summaries.extend(item for item in valid_single if item["id"] not in returned)
        returned.update(item["id"] for item in valid_single)

    unique = []
    seen = set()
    for item in summaries:
        if item["id"] in seen:
            continue
        seen.add(item["id"])
        unique.append(item)
    return unique


def build_tone_legend_messages(seeds: list[dict]) -> list[dict]:
    system_prompt = (
        "당신은 배포용 채용 인텔리전스 화면의 상단 색상 가이드를 정리하는 한국어 편집자입니다. "
        "입력으로 주어진 네 개의 색상 묶음은 roleDisplay와 detailBody에서 나온 키워드와 요약을 모은 것입니다. "
        "반드시 한국어만 사용하세요. 중국어, 영어, 일본어를 쓰지 마세요. "
        "반드시 strict JSON only 로 "
        "{\"items\":[{\"tone\":\"tone-ai\",\"description\":\"...\"}]} "
        "형태만 반환하세요. "
        "description은 58자 이하의 자연스러운 한국어 한 문장이어야 합니다. "
        "각 색상이 어떤 채용 신호를 묶는지 설명하되, 칭찬이나 추상적 표현은 피하세요. "
        "'채용 신호:', '필요', '채용합니다' 같은 말은 쓰지 마세요. "
        "'... 성격의 공고를 묶습니다.'처럼 끝내면 좋습니다. "
        "예시: '모델 설계·미세조정·추론 최적화 성격의 공고를 묶습니다.' "
        "예시: '데이터 파이프라인·서빙·인프라 구현 성격의 공고를 묶습니다.' "
        "마크다운, 불릿, 추가 키는 금지합니다."
    )
    payload = {"items": seeds}
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def build_single_tone_legend_messages(seed: dict) -> list[dict]:
    system_prompt = (
        "당신은 배포용 채용 인텔리전스 화면의 색상 설명 문구를 쓰는 한국어 편집자입니다. "
        "반드시 한국어만 사용하세요. "
        "strict JSON only 로 {\"description\":\"...\"} 만 반환하세요. "
        "description은 58자 이하의 자연스러운 한국어 한 문장이어야 합니다. "
        "이 색상이 포착하는 채용 신호를 설명하세요. "
        "'채용 신호:', '필요', '채용합니다' 같은 말은 쓰지 마세요. "
        "'... 성격의 공고를 묶습니다.'처럼 간결하게 끝내세요. "
        "입력에 없는 내용을 지어내지 말고, 마크다운과 추가 키는 금지합니다."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(seed, ensure_ascii=False)},
    ]


def request_single_tone_legend(config: dict, seed: dict) -> dict | None:
    base_url = (config.get("baseUrl") or "").rstrip("/")
    model = (config.get("model") or "").strip()
    api_key = config.get("apiKey", "")

    payload = {
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": build_single_tone_legend_messages(seed),
    }

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        body = json.loads(response.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    parsed = extract_json_object(content)
    description = re.sub(r"\s+", " ", str(parsed.get("description", "")).strip())
    if not description:
        return None
    return {"tone": seed["tone"], "description": description[:120]}


def request_tone_legend(config: dict, seeds: list[dict]) -> list[dict]:
    base_url = (config.get("baseUrl") or "").rstrip("/")
    model = (config.get("model") or "").strip()
    api_key = config.get("apiKey", "")

    if not base_url:
        raise ValueError("baseUrl is required")
    if not model:
        raise ValueError("model is required")

    payload = {
        "model": model,
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
        "messages": build_tone_legend_messages(seeds),
    }

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        body = json.loads(response.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    parsed = extract_json_object(content)
    items = normalize_tone_legend_items(parsed)
    returned = {item["tone"] for item in items}

    for seed in seeds:
        if seed["tone"] in returned:
            continue
        single = request_single_tone_legend(config, seed)
        if not single:
            continue
        items.append(single)
        returned.add(single["tone"])

    ordered = []
    seen = set()
    for seed in seeds:
        for item in items:
            if item["tone"] != seed["tone"] or item["tone"] in seen:
                continue
            seen.add(item["tone"])
            ordered.append(item)
    return ordered


def compact_cluster_terms(values) -> set[str]:
    terms = set()
    for value in values or []:
        for part in re.split(r"[·,/()\s]+", normalize_inline_text(value).lower()):
            compact = re.sub(r"[^0-9a-z가-힣]+", "", part)
            if len(compact) >= 2:
                terms.add(compact)
    return terms


def cluster_similarity_score(profile: dict, cluster: dict) -> int:
    profile_terms = compact_cluster_terms(
        [
            *(profile.get("roles", []) or []),
            *(profile.get("focusLabels", []) or []),
            *(profile.get("keywords", []) or []),
            *(profile.get("sampleSummaries", []) or []),
        ]
    )
    cluster_terms = compact_cluster_terms(
        [
            cluster.get("label", ""),
            cluster.get("description", ""),
            cluster.get("reason", ""),
            *(cluster.get("keywords", []) or []),
        ]
    )
    return len(profile_terms & cluster_terms)


def build_company_cluster_messages(company_profiles: list[dict]) -> list[dict]:
    system_prompt = (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 편집자입니다. "
        "입력은 회사별 채용 프로필이며, 이를 몇 개의 의미 있는 회사군으로 묶어야 합니다. "
        "반드시 한국어만 사용하고 strict JSON only 로 "
        "{\"clusters\":[{\"label\":\"...\",\"description\":\"...\",\"reason\":\"...\",\"keywords\":[\"...\"],\"companyIds\":[\"C001\"]}]}"
        " 형태만 반환하세요. "
        "규칙: 4개 이상 7개 이하의 cluster만 만드세요. "
        "모든 회사를 정확히 한 번씩만 companyIds에 포함하세요. "
        "cluster label은 'AI', 'Model', 'Data' 같은 앞머리 일반론보다 실제 반복되는 업무 패턴 중심의 짧은 명사구로 쓰세요. "
        "description은 28자 이하, reason은 52자 이하로 쓰세요. "
        "keywords는 3~6개 짧은 용어로 쓰세요. "
        "한 회사만 들어가는 cluster는 정말 독특한 패턴이 아니면 만들지 마세요. "
        "입력 근거가 약한 회사도 가장 가까운 cluster에 넣되, 없는 사실을 지어내지 마세요."
    )
    payload = {"companies": company_profiles}
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def normalize_company_cluster_items(payload: dict, company_profiles: list[dict]) -> list[dict]:
    items = payload.get("clusters", [])
    if not isinstance(items, list):
        items = []

    id_to_company = {
        profile.get("companyId", ""): profile.get("company", "")
        for profile in company_profiles
        if profile.get("companyId") and profile.get("company")
    }
    valid_companies = list(id_to_company.values())
    valid_ids = set(id_to_company)
    profile_map = {
        profile["company"]: profile
        for profile in company_profiles
        if profile.get("company")
    }
    assigned = set()
    normalized = []

    for item in items:
        if not isinstance(item, dict):
            continue
        companies = []
        source_ids = item.get("companyIds", []) or item.get("company_ids", [])
        if not isinstance(source_ids, list):
            source_ids = []
        for company_id in source_ids:
            cleaned_id = normalize_inline_text(company_id)
            name = id_to_company.get(cleaned_id, "")
            if not cleaned_id or cleaned_id not in valid_ids or not name or name in assigned or name in companies:
                continue
            companies.append(name)
            assigned.add(name)
        if not companies:
            continue
        label = normalize_inline_text(item.get("label", "")) or f"회사군 {len(normalized) + 1}"
        description = normalize_inline_text(item.get("description", ""))[:64]
        reason = normalize_inline_text(item.get("reason", ""))[:96]
        keywords = []
        for keyword in item.get("keywords", []) if isinstance(item.get("keywords", []), list) else []:
            cleaned = normalize_inline_text(keyword)
            if cleaned and not is_generic_keyword(cleaned) and cleaned not in keywords:
                keywords.append(cleaned)
        normalized.append(
            {
                "label": label[:24],
                "description": description or f"{label[:24]} 성격이 반복되는 회사군",
                "reason": reason or f"{label[:24]} 성격의 공고가 반복됩니다.",
                "keywords": keywords[:6],
                "companies": companies,
            }
        )

    if not normalized and valid_companies:
        normalized = [
            {
                "label": "공고 패턴 검토",
                "description": "회사별 채용 패턴을 다시 묶은 묶음",
                "reason": "반복되는 역할과 업무 신호를 기준으로 묶었습니다.",
                "keywords": [],
                "companies": valid_companies[:],
            }
        ]
        assigned = set(valid_companies)

    missing = [company for company in valid_companies if company not in assigned]
    for company in missing:
        if not normalized:
            break
        best = max(
            normalized,
            key=lambda cluster: cluster_similarity_score(profile_map[company], cluster),
        )
        best["companies"].append(company)

    finalized = []
    for index, item in enumerate(normalized, start=1):
        finalized.append(
            {
                "id": f"cluster-{index}",
                "label": item["label"],
                "description": item["description"],
                "reason": item["reason"],
                "keywords": item["keywords"],
                "companies": item["companies"],
            }
        )
    return finalized


def request_company_clusters(config: dict, company_profiles: list[dict]) -> list[dict]:
    base_url = (config.get("baseUrl") or "").rstrip("/")
    model = (config.get("model") or "").strip()
    api_key = config.get("apiKey", "")

    if not base_url:
        raise ValueError("baseUrl is required")
    if not model:
        raise ValueError("model is required")

    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": build_company_cluster_messages(company_profiles),
    }

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        body = json.loads(response.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    parsed = extract_json_object(content)
    return normalize_company_cluster_items(parsed, company_profiles)


def build_cluster_label_messages(cluster_seeds: list[dict]) -> list[dict]:
    system_prompt = (
        "당신은 공식 배포용 채용 인텔리전스 서비스의 회사군 라벨 편집자입니다. "
        "이미 회사군 자체는 정해져 있으니, cluster id별로 label, description, reason만 다시 써주세요. "
        "반드시 한국어만 사용하고 strict JSON only 로 "
        "{\"items\":[{\"id\":\"cluster-1\",\"label\":\"...\",\"description\":\"...\",\"reason\":\"...\"}]}"
        " 형태만 반환하세요. "
        "label은 2~18자, description은 30자 이하, reason은 52자 이하로 쓰세요. "
        "AI, 기술, 엔지니어링, 공고, 회사군 같은 너무 넓은 말은 피하고 실제 반복되는 채용 패턴을 드러내세요. "
        "입력의 keywords, sampleCompanies, sampleSummaries만 근거로 사용하세요."
    )
    payload = {"clusters": cluster_seeds}
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def normalize_cluster_label_items(payload: dict, cluster_seeds: list[dict]) -> list[dict]:
    items = payload.get("items", [])
    if not isinstance(items, list):
        items = []

    seed_map = {seed["id"]: seed for seed in cluster_seeds}
    normalized = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        cluster_id = normalize_inline_text(item.get("id", ""))
        if not cluster_id or cluster_id not in seed_map or cluster_id in seen:
            continue
        seen.add(cluster_id)
        seed = seed_map[cluster_id]
        normalized.append(
            {
                **seed,
                "label": normalize_inline_text(item.get("label", "")) or seed.get("label", ""),
                "description": normalize_inline_text(item.get("description", "")) or seed.get("description", ""),
                "reason": normalize_inline_text(item.get("reason", "")) or seed.get("reason", ""),
            }
        )

    if not normalized:
        return cluster_seeds

    ordered = []
    normalized_map = {item["id"]: item for item in normalized}
    for seed in cluster_seeds:
        ordered.append(normalized_map.get(seed["id"], seed))
    return ordered


def request_cluster_labels(config: dict, cluster_seeds: list[dict]) -> list[dict]:
    base_url = (config.get("baseUrl") or "").rstrip("/")
    model = (config.get("model") or "").strip()
    api_key = config.get("apiKey", "")

    if not base_url:
        raise ValueError("baseUrl is required")
    if not model:
        raise ValueError("model is required")

    payload = {
        "model": model,
        "temperature": 0.2,
        "response_format": {"type": "json_object"},
        "messages": build_cluster_label_messages(cluster_seeds),
    }

    headers = {
        "Content-Type": "application/json",
    }
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=180) as response:
        body = json.loads(response.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    parsed = extract_json_object(content)
    return normalize_cluster_label_items(parsed, cluster_seeds)


def save_enrichment(job_id: str, config: dict, enrichment: dict) -> dict:
    store = load_enrichment_store()
    store["items"][job_id] = {
        "jobId": job_id,
        "appliedAt": now_iso(),
        "provider": {
            "baseUrl": config.get("baseUrl", ""),
            "model": config.get("model", ""),
        },
        "normalized": enrichment,
    }
    save_enrichment_store(store)
    return store["items"][job_id]


def save_summary_batch(
    config: dict,
    summaries: list[dict],
    prompt_profile: str = "field_aware_v3",
) -> dict:
    store = load_summary_store()
    profile_name = normalize_summary_prompt_profile_name(prompt_profile)
    for item in summaries:
        store["items"][item["id"]] = {
            "jobId": item["id"],
            "role": item.get("role", ""),
            "summary": item["summary"],
            "keywords": item.get("keywords", []),
            "focusLabel": item.get("focusLabel", ""),
            "quality": item.get("quality", "medium"),
            "structuredSignals": item.get("structuredSignals", {}),
            "sectionSignalFacets": item.get("sectionSignalFacets", {}),
            "summarizedAt": now_iso(),
            "provider": {
                "baseUrl": config.get("baseUrl", ""),
                "model": config.get("model", ""),
                "promptProfile": profile_name,
            },
        }
    save_summary_store(store)
    return store


def save_tone_legend(config: dict, items: list[dict]) -> dict:
    store = load_tone_legend_store()
    for item in items:
        store["items"][item["tone"]] = {
            "tone": item["tone"],
            "description": item["description"],
            "generatedAt": now_iso(),
            "provider": {
                "baseUrl": config.get("baseUrl", ""),
                "model": config.get("model", ""),
            },
        }
    save_tone_legend_store(store)
    return store


def save_company_clusters(config: dict, items: list[dict]) -> dict:
    store = {
        "updatedAt": now_iso(),
        "provider": {
            "baseUrl": config.get("baseUrl", ""),
            "model": config.get("model", ""),
        },
        "clusters": items,
    }
    save_company_cluster_store(store)
    return store
