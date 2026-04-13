#!/usr/bin/env python3

import json
import pathlib
import re
from collections import Counter
from datetime import datetime

from ai_runtime import (
    JOBS_PATH,
    compute_role_group_signature,
    compute_service_scope_signature,
    load_company_cluster_store,
    load_summary_store,
    load_tone_legend_store,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
OUTPUT_PATH = ROOT / "data" / "summary_board.json"
SERVICE_SCOPE_OVERRIDE_PATH = ROOT / "data" / "service_scope_overrides.json"
ROLE_GROUP_OVERRIDE_PATH = ROOT / "data" / "role_group_overrides.json"
ROLE_ORDER = [
    "인공지능 엔지니어",
    "인공지능 리서처",
    "데이터 사이언티스트",
    "데이터 분석가",
]
TONE_ORDER = ["tone-ai", "tone-data", "tone-domain", "tone-analysis"]
TONE_META = {
    "tone-ai": {"label": "Model / AI"},
    "tone-data": {"label": "Data / Infra"},
    "tone-domain": {"label": "Domain"},
    "tone-analysis": {"label": "Research"},
}
CLUSTER_TONES = [
    "cluster-a",
    "cluster-b",
    "cluster-c",
    "cluster-d",
    "cluster-e",
    "cluster-f",
    "cluster-g",
]
CLUSTER_SCHEMAS = [
    {
        "id": "cluster-model",
        "tone": "tone-model",
        "label": "모델 고도화",
        "description": "모델 자체를 만들고 다듬는 채용이 많은 회사들",
        "tokens": [
            "멀티모달",
            "비전",
            "자연어",
            "rag",
            "에이전트",
            "미세조정",
            "파인튜닝",
            "파인 튜닝",
            "추론",
            "학습",
            "훈련",
            "생성형",
            "추천",
            "검색",
        ],
    },
    {
        "id": "cluster-platform",
        "tone": "tone-platform",
        "label": "플랫폼 · 서빙",
        "description": "배포·서빙·파이프라인 운영 비중이 높은 회사들",
        "tokens": [
            "서빙",
            "배포",
            "파이프라인",
            "mlops",
            "llmops",
            "인프라",
            "플랫폼",
            "쿠버네티스",
            "클라우드",
            "데브옵스",
            "devops",
            "온프레미스",
            "api",
            "sdk",
            "ci/cd",
            "씨아이씨디",
        ],
    },
    {
        "id": "cluster-data",
        "tone": "tone-data",
        "label": "데이터 · 실험",
        "description": "데이터 분석과 실험 설계 성격이 강한 회사들",
        "tokens": [
            "데이터 분석",
            "분석",
            "실험",
            "지표",
            "통계",
            "예측",
            "a/b",
            "ab",
            "대시보드",
            "etl",
            "warehouse",
            "리포팅",
            "bi",
            "데이터 사이언티스트",
            "데이터 분석가",
        ],
    },
    {
        "id": "cluster-domain",
        "tone": "tone-domain",
        "label": "도메인 적용",
        "description": "제품·산업 현장 적용과 고객 문제 해결이 중심인 회사들",
        "tokens": [
            "광고",
            "추천",
            "검색",
            "금융",
            "교육",
            "게임",
            "커머스",
            "제조",
            "산업안전",
            "보안",
            "고객",
            "사업",
            "솔루션",
            "현장",
            "서비스",
        ],
    },
    {
        "id": "cluster-edge",
        "tone": "tone-edge",
        "label": "온디바이스 · 검증",
        "description": "최적화·하드웨어·검증 비중이 높은 회사들",
        "tokens": [
            "온디바이스",
            "edge",
            "엔피유",
            "npu",
            "양자화",
            "최적화",
            "컴파일러",
            "검증",
            "테스트벤치",
            "시뮬레이션",
            "하드웨어",
            "디바이스",
            "asic",
            "rtos",
            "그래프",
        ],
    },
]
CLUSTER_ORDER = [schema["id"] for schema in CLUSTER_SCHEMAS]
NOISE_PATTERNS = [
    r"^담당 업무$",
    r"^주요 업무$",
    r"^자격 요건$",
    r"^우대 사항$",
    r"^근무조건$",
    r"^지원 전,? 확인해주세요!?$",
    r"^채용 관련 문의사항.*$",
    r"^읽어보면 도움 되는 관련 자료$",
    r"^제출하신 .*",
    r"^필요 시 .*",
    r"^입사 후 .*",
    r"^로 보내주세요\.?$",
    r"^구체적으로 다음 업무들 중$",
    r"^전문가는 아래 업무들을.*$",
    r"^.*찾고 있습니다\.?$",
    r"^전 분야에 대한 포괄적인 학습 및 이해$",
    r"^\(.*\)$",
    r"^&\s.*$",
    r"^.*로그인.*$",
    r"^.*문의 가능.*$",
    r"^.*포인트.*$",
    r"^.*채용 과정.*$",
    r"^.*근무가 가능합니다.*$",
    r"^.*합격 모두 가능.*$",
    r"^.*누가 만들지.*$",
]
DISPLAY_DROP_PATTERNS = [
    r"^모집 요강$",
    r"^상시채용$",
    r"^경력무관$",
    r"^계약직$",
    r"^정규직$",
    r"^지원하기$",
    r"^근무정보$",
    r"^지원 관련 정보$",
    r"^필수 경험 및 역량$",
    r"^수행 프로젝트$",
    r"^구축 사례 소개$",
    r"^현재 모집 중인 이 공고는 어떠신가요\??$",
    r"^.*채용절차법.*$",
    r"^.*반환 청구.*$",
    r"^.*반환 서류.*$",
    r"^.*서류 반환 절차.*$",
    r"^.*결과 통지일.*$",
    r"^.*레퍼런스 체크.*$",
    r"^.*서류전형.*$",
    r"^.*최종면접.*$",
    r"^.*최종 합격.*$",
    r"^.*처우협의.*$",
    r"^.*수습 기간.*$",
    r"^.*입사지원 서류.*$",
    r"^.*허위사실.*$",
    r"^.*채용이 취소될 수 있습니다.*$",
    r"^.*접수된 서류는 채용과 무관.*$",
    r"^.*우측 지원하기 클릭.*$",
    r"^.*지원하기.*$",
    r"^.*문의하기.*$",
    r"^.*바로가기.*$",
    r"^.*담당자가 빠른 시일 내 연락.*$",
    r"^.*문의 사항을 작성.*$",
    r"^.*다양한 직무로 지원 가능.*$",
    r"^.*모집기간.*$",
    r"^.*모집인원.*$",
    r"^.*근무지.*$",
]
DISPLAY_SIGNAL_LINE_PATTERNS = [
    r"이상이신 분",
    r"이상인 분",
    r"경력\s*\d+\s*년 이상",
    r"경력이\s*\d+\s*년 이상",
    r"있으신 분",
    r"가능하신 분",
    r"보유하신 분",
    r"갖추신 분",
    r"익숙하신 분",
    r"능력이 있으신 분",
    r"이해도가 있으신 분",
    r"우대",
]
DISPLAY_META_ADMIN_TERMS = {
    "모집요강",
    "인재채용",
    "채용공고",
    "채용정보",
    "채용안내",
    "상시채용",
    "경력무관",
    "정규직",
    "계약직",
    "지원하기",
    "바로가기",
    "지원서",
    "접수",
    "문의사항",
    "문의하기",
    "채용절차법",
    "반환",
    "서류 반환",
    "반환 청구",
    "결과 통지",
    "전형",
    "합격발표",
    "recruitment",
    "recruiter",
    "hiring",
    "career",
}
DISPLAY_META_NAV_TERMS = {
    "클릭",
    "링크",
    "자세히 보기",
    "상세 보기",
    "원문 보기",
    "지원하기",
    "바로가기",
    "문의하기",
    "지원서",
    "접수",
}
DISPLAY_DUTY_TERMS = {
    "구축",
    "설계",
    "분석",
    "검증",
    "운영",
    "평가",
    "최적화",
    "자동화",
    "연동",
    "통합",
    "배포",
    "구현",
    "모델링",
    "튜닝",
    "실험",
    "리서치",
    "조사",
    "기획",
    "관리",
    "개선",
    "고도화",
    "테스트",
    "모니터링",
    "서빙",
    "파이프라인",
    "유지보수",
    "리팩토링",
}
DISPLAY_ROLE_NOUN_TERMS = {
    "개발자",
    "엔지니어",
    "분석가",
    "리서처",
    "과학자",
    "기획자",
    "담당자",
    "연구원",
    "매니저",
    "컨설턴트",
    "전문가",
    "오퍼레이터",
    "아키텍트",
}
PREVIEW_DROP_PREFIXES = [
    r"^본 직무는\s*",
    r"^채용된 전문가는\s*",
    r"^전문가는 아래 업무들을.*$",
    r"^은\s+",
    r"^는\s+",
]
SUMMARY_BAD_PATTERNS = [
    r"^인공지능 .* 엔지니어$",
    r"^인공지능 .* 개발 엔지니어$",
    r"^.*엔지니어 찾기$",
    r"^.*역량 요구$",
    r"^.*참여.*$",
    r"^.*(엔지니어|개발자|리서처)$",
]
DISPLAY_BAD_TOKENS = {
    "이상이신",
    "경험자",
    "가능자",
    "채용절차법",
    "우대합니다",
    "있습니다",
}
AI_TERMS = [
    "ai",
    "인공지능",
    "llm",
    "vlm",
    "rag",
    "멀티모달",
    "딥러닝",
    "머신러닝",
    "모델",
    "훈련",
    "최적화",
    "컴퓨터비전",
    "자연어",
    "추천",
    "시계열",
    "비전",
    "onnx",
]
DATA_TERMS = [
    "data",
    "데이터",
    "etl",
    "파이프라인",
    "sql",
    "mlops",
    "infra",
    "인프라",
    "serving",
    "서빙",
    "api",
    "sdk",
    "backend",
    "도커",
    "docker",
    "aws",
    "gcp",
    "azure",
    "쿠버네티스",
]
DOMAIN_TERMS = [
    "금융",
    "교육",
    "커머스",
    "광고",
    "검색",
    "산업안전",
    "자율주행",
    "제조",
    "도메인",
    "제품",
    "commerce",
    "search",
]
ANALYSIS_TERMS = [
    "분석",
    "리서치",
    "연구",
    "실험",
    "평가",
    "검증",
    "지표",
    "통계",
    "예측",
    "research",
    "analysis",
]

BOARD_FOCUS_CANONICAL_MAP = {
    "에스큐엘": "SQL",
    "sql": "SQL",
    "파이토치": "PyTorch",
    "pytorch": "PyTorch",
    "텐서플로": "TensorFlow",
    "tensorflow": "TensorFlow",
    "이티엘": "ETL",
    "etl": "ETL",
    "쿠버네티스": "쿠버네티스",
    "kubernetes": "쿠버네티스",
    "오엔엔엑스": "ONNX",
    "onnx": "ONNX",
    "컴퓨터비전": "컴퓨터 비전",
    "crm": "고객 관계 관리",
    "에스디케이": "SDK",
    "sdk": "SDK",
    "에이피아이": "API",
    "api": "API",
    "브이엘엠": "VLM",
    "vlm": "VLM",
}

BOARD_BROAD_FOCUS_LABELS = {
    "pytorch",
    "tensorflow",
    "sql",
    "파이썬",
    "쿠버네티스",
    "파이프라인",
    "사업개발",
    "소프트웨어개발",
    "인프라엔지니어",
    "데이터분석",
    "마케팅",
    "etl",
    "llm",
    "의료",
    "인사이트",
}

BOARD_FOCUS_HINTS = [
    {"label": "RAG", "patterns": ["rag", "검색증강생성", "retrieval", "벡터 데이터베이스", "검색 시스템"], "weight": 8.8},
    {"label": "고객 관계 관리", "patterns": ["고객 관계 관리", "crm"], "weight": 8.6},
    {"label": "공급망 최적화", "patterns": ["공급망", "scm", "재고", "물류 센터"], "weight": 8.5},
    {"label": "광고 시스템", "patterns": ["광고 시스템", "광고 요청", "실시간 입찰", "rtb"], "weight": 8.5},
    {"label": "객체 인식", "patterns": ["객체 인식", "object detection"], "weight": 8.4},
    {"label": "이상 탐지", "patterns": ["이상 탐지", "anomaly"], "weight": 8.4},
    {"label": "불량 탐지", "patterns": ["불량 탐지", "defect"], "weight": 8.4},
    {"label": "트래킹", "patterns": ["트래킹", "tracking"], "weight": 8.4},
    {"label": "VSLAM", "patterns": ["vslam", "브이에스엘에이엠"], "weight": 8.4},
    {"label": "추론 엔진", "patterns": ["추론 엔진", "inference engine", "runtime"], "weight": 8.3},
    {"label": "임베디드 최적화", "patterns": ["임베디드", "포팅", "멀티 스레딩", "파이프라이닝"], "weight": 8.3},
    {"label": "3D 공간 이해", "patterns": ["실외 환경", "시공간", "3d", "공간 이해"], "weight": 8.2},
    {"label": "비전 인공지능", "patterns": ["비전 인공지능", "vision ai"], "weight": 8.1},
    {"label": "모델 변환", "patterns": ["모델 변환", "변환 구조", "onnx 변환"], "weight": 8.1},
    {"label": "하이브리드 인프라", "patterns": ["하이브리드 인프라", "퍼블릭 클라우드", "gpu 서버"], "weight": 8.3},
    {"label": "컴파일러", "patterns": ["compiler", "컴파일러", "아이알", "ir 그래프", "ir"], "weight": 8.2},
    {"label": "ONNX", "patterns": ["onnx", "오엔엔엑스"], "weight": 8.1},
    {"label": "생체신호", "patterns": ["생체신호"], "weight": 8.0},
    {"label": "음성인식", "patterns": ["음성인식", "speech"], "weight": 8.0},
    {"label": "의료 데이터", "patterns": ["의료 데이터", "의료영상", "의료기기", "임상"], "weight": 7.9},
    {"label": "컴퓨터 비전", "patterns": ["컴퓨터 비전", "컴퓨터비전", "vision", "라이다", "lidar"], "weight": 7.8},
    {"label": "자율주행", "patterns": ["자율주행", "자율 주행"], "weight": 7.8},
    {"label": "멀티모달", "patterns": ["멀티모달", "multimodal"], "weight": 7.7},
    {"label": "MLOps", "patterns": ["mlops"], "weight": 7.4},
    {"label": "LLMOps", "patterns": ["llmops"], "weight": 7.4},
    {"label": "모델 서빙", "patterns": ["모델 서빙", "서빙", "serving"], "weight": 7.2},
    {"label": "데이터 마트", "patterns": ["데이터 마트", "마트 데이터", "mart"], "weight": 7.2},
    {"label": "대시보드", "patterns": ["대시보드", "dashboard"], "weight": 6.9},
    {"label": "인프라", "patterns": ["인프라", "클러스터", "온프레미스"], "weight": 6.8},
    {"label": "클라우드", "patterns": ["클라우드", "aws", "gcp", "azure"], "weight": 6.4},
    {"label": "SDK", "patterns": ["sdk", "에스디케이"], "weight": 6.4},
    {"label": "API", "patterns": [" api ", "에이피아이"], "weight": 6.2},
    {"label": "검증", "patterns": ["검증", "테스트벤치", "testbench"], "weight": 6.1},
    {"label": "검색", "patterns": ["검색", "search"], "weight": 6.0},
    {"label": "추천", "patterns": ["추천", "recommend"], "weight": 6.0},
    {"label": "리스크 모델링", "patterns": ["안정성 평가", "성장성 평가", "적정 한도", "fraud", "risk"], "weight": 5.9},
    {"label": "데이터 분석", "patterns": ["데이터 분석", "통계", "지표"], "weight": 5.4},
    {"label": "마케팅", "patterns": ["마케팅", "campaign", "광고"], "weight": 5.3},
    {"label": "사업 개발", "patterns": ["사업 개발", "사업 기회"], "weight": 5.2},
    {"label": "ETL", "patterns": ["etl", "이티엘"], "weight": 5.1},
    {"label": "PyTorch", "patterns": ["pytorch", "파이토치"], "weight": 3.2},
    {"label": "TensorFlow", "patterns": ["tensorflow", "텐서플로"], "weight": 3.2},
    {"label": "SQL", "patterns": ["sql", "에스큐엘"], "weight": 3.0},
]

ENGINEER_BUSINESS_DOMINANCE_PATTERNS = [
    r"제품\s*성장\s*분석",
    r"성장\s*분석",
    r"제품\s*분석",
    r"\ba/b\b",
    r"에이비\s*테스트",
    r"\bsql\b",
    r"마케팅",
    r"캠페인",
    r"퍼널",
    r"리텐션",
]

ENGINEER_FOCUS_BLOCKLIST = {
    "제품성장분석",
    "성장분석",
    "제품분석",
    "ab테스트",
    "sql",
    "pytorch",
    "tensorflow",
    "onnx",
    "docker",
    "kubernetes",
}

SUMMARY_ENDING_PATTERNS = (
    "합니다",
    "합니다.",
    "수행합니다",
    "수행합니다.",
    "담당합니다",
    "담당합니다.",
    "지원합니다",
    "지원합니다.",
    "구축합니다",
    "구축합니다.",
    "개발합니다",
    "개발합니다.",
    "운영합니다",
    "운영합니다.",
)


def parse_dt(value: str) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return 0.0


def clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip())


def canonical_text(value: str) -> str:
    return re.sub(r"[^0-9A-Za-z가-힣]+", "", clean_text(value)).lower()


def canonical_focus_label(value: str) -> str:
    cleaned = clean_text(value)
    compact = canonical_text(cleaned)
    if compact in BOARD_FOCUS_CANONICAL_MAP:
        return BOARD_FOCUS_CANONICAL_MAP[compact]
    return cleaned


def focus_label_is_broad(value: str) -> bool:
    return canonical_text(value) in BOARD_BROAD_FOCUS_LABELS


def focus_label_is_invalid(value: str) -> bool:
    cleaned = clean_text(value)
    compact = canonical_text(cleaned)
    if not cleaned or not compact:
        return True
    if len(cleaned) > 28:
        return True
    if re.search(r"[|_()]", cleaned):
        return True
    if re.search(r"(engineer|developer|manager|analyst|researcher)$", cleaned, re.IGNORECASE):
        return True
    if compact in {
        canonical_text("인공지능 엔지니어"),
        canonical_text("인공지능 리서처"),
        canonical_text("데이터 사이언티스트"),
        canonical_text("데이터 분석가"),
    }:
        return True
    return False


def focus_label_is_business_dominant(value: str) -> bool:
    text = clean_text(value).lower()
    if not text:
        return False
    if canonical_text(value) in ENGINEER_FOCUS_BLOCKLIST:
        return True
    return any(re.search(pattern, text) for pattern in ENGINEER_BUSINESS_DOMINANCE_PATTERNS)


def focus_label_is_engineer_scope_candidate(value: str) -> bool:
    cleaned = canonical_focus_label(value)
    if focus_label_is_invalid(cleaned):
        return False
    if focus_label_is_business_dominant(cleaned):
        return False
    compact = canonical_text(cleaned)
    if compact in ENGINEER_FOCUS_BLOCKLIST:
        return False
    if compact in {canonical_text("LLM"), canonical_text("인프라"), canonical_text("클라우드")}:
        return False
    return True


def collect_focus_hint_scores(job: dict, summary: str, preview_lines: list[str], keywords: list[str]) -> dict:
    texts = [
        summary,
        *preview_lines[:3],
        job.get("title", ""),
        job.get("detailBody", ""),
        *(job.get("tasks") or [])[:4],
        *(job.get("requirements") or [])[:3],
        *(job.get("preferred") or [])[:3],
        *(job.get("skills") or [])[:8],
        *keywords[:5],
    ]
    lowered = " ".join(clean_text(value).lower() for value in texts if clean_text(value))
    scores = {}
    for hint in BOARD_FOCUS_HINTS:
        if any(pattern.lower() in lowered for pattern in hint["patterns"]):
            label = hint["label"]
            scores[label] = max(scores.get(label, 0.0), hint["weight"])
    return scores


def refine_focus_label(
    job: dict,
    current_focus: str,
    keywords: list[str],
    summary: str,
    preview_lines: list[str],
) -> str:
    current = canonical_focus_label(current_focus)
    hint_scores = collect_focus_hint_scores(job, summary, preview_lines, keywords)
    candidates = {}

    def add_candidate(label: str, score: float) -> None:
        cleaned = canonical_focus_label(label)
        if focus_label_is_invalid(cleaned):
            return
        candidates[cleaned] = max(candidates.get(cleaned, -999.0), score)

    if current and not focus_label_is_invalid(current):
        add_candidate(current, 4.2 if not focus_label_is_broad(current) else 2.0)

    for keyword in keywords[:5]:
        cleaned = canonical_focus_label(keyword)
        if focus_label_is_invalid(cleaned):
            continue
        add_candidate(cleaned, 2.6 if not focus_label_is_broad(cleaned) else 1.2)

    for label, score in hint_scores.items():
        add_candidate(label, score)

    if not candidates:
        return ""

    summary_clean = clean_text(summary).lower()
    ranked = []
    for label, score in candidates.items():
        adjusted = score
        compact = canonical_text(label)
        if summary_clean and label.lower() in summary_clean:
            adjusted += 0.45
        if focus_label_is_broad(label) and any(
            not focus_label_is_broad(other) and other != label for other in candidates
        ):
            adjusted -= 1.6
        if compact in {canonical_text("마케팅"), canonical_text("데이터 분석")} and any(
            canonical_text(other)
            in {
                canonical_text("고객 관계 관리"),
                canonical_text("데이터 마트"),
                canonical_text("대시보드"),
                canonical_text("리스크 모델링"),
            }
            for other in candidates
        ):
            adjusted -= 0.8
        ranked.append((adjusted, len(label), label))

    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    return ranked[0][2]


def rebalance_engineer_business_focus(
    *,
    role: str,
    job: dict,
    structured_signals: dict,
    focus_label: str,
    keywords: list[str],
    summary: str,
    preview_lines: list[str],
) -> tuple[str, list[str]]:
    if role not in {"인공지능 엔지니어", "인공지능 리서처"}:
        return focus_label, keywords
    first_keyword = keywords[0] if keywords else ""
    if not (focus_label_is_business_dominant(focus_label) or focus_label_is_business_dominant(first_keyword)):
        return focus_label, keywords

    evidence = " ".join(
        [
            clean_text(job.get("title", "")),
            clean_text(summary),
            " ".join(clean_text(value) for value in preview_lines[:4]),
        ]
    ).lower()
    priority = [
        ("problemSignals", 9.4),
        ("modelSignals", 9.2),
        ("systemSignals", 8.4),
        ("workflowSignals", 7.5),
        ("domainSignals", 6.4),
    ]
    candidates = []
    for category, base_score in priority:
        values = structured_signals.get(category, []) if isinstance(structured_signals.get(category, []), list) else []
        for index, value in enumerate(values):
            cleaned = canonical_focus_label(value)
            if not focus_label_is_engineer_scope_candidate(cleaned):
                continue
            score = base_score - (index * 0.2)
            if clean_text(cleaned).lower() and clean_text(cleaned).lower() in evidence:
                score += 1.2
            candidates.append((score, len(cleaned), cleaned))

    if not candidates:
        hint_scores = collect_focus_hint_scores(job, summary, preview_lines, keywords)
        for label, score in hint_scores.items():
            cleaned = canonical_focus_label(label)
            if focus_label_is_engineer_scope_candidate(cleaned):
                candidates.append((score, len(cleaned), cleaned))

    if not candidates:
        return focus_label, keywords

    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    next_focus = candidates[0][2]
    next_keywords = [next_focus]
    for keyword in keywords:
        cleaned = canonical_focus_label(keyword)
        if not focus_label_is_engineer_scope_candidate(cleaned):
            continue
        if canonical_text(cleaned) == canonical_text(next_focus):
            continue
        next_keywords.append(cleaned)
        if len(next_keywords) >= 5:
            break
    return next_focus, next_keywords


def select_low_confidence_focus(job: dict, preview_lines: list[str]) -> str:
    hint_scores = collect_focus_hint_scores(job, "", preview_lines, [])
    if not hint_scores:
        return ""

    ranked = []
    for label, score in hint_scores.items():
        cleaned = canonical_focus_label(label)
        if focus_label_is_invalid(cleaned):
            continue
        if focus_label_is_broad(cleaned):
            score -= 1.5
        ranked.append((score, len(cleaned), cleaned))

    if not ranked:
        return ""

    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    top_score, _, top_label = ranked[0]
    if top_score < 7.8:
        return ""
    if focus_label_is_broad(top_label):
        return ""
    return top_label


def split_detail_lines(value: str) -> list[str]:
    lines = []
    seen = set()
    for part in re.split(r"[\n\r]+", value or ""):
        cleaned = clean_text(part)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        lines.append(cleaned)
    return lines


def split_sentences(value: str) -> list[str]:
    parts = []
    for chunk in split_detail_lines(value):
        fragments = re.split(r"(?<=[.!?])\s+|(?<=다\.)\s+", chunk)
        for fragment in fragments:
            cleaned = clean_text(fragment)
            if cleaned:
                parts.append(cleaned)
    return parts


def is_noise_line(line: str) -> bool:
    if not line:
        return True
    if len(line) <= 2:
        return True
    if re.match(r"^[은는이가을를]\s", line):
        return True
    for pattern in NOISE_PATTERNS:
        if re.match(pattern, line):
            return True
    return False


def looks_like_title_echo(line: str, job: dict) -> bool:
    compact = canonical_text(line)
    if not compact:
        return True

    title = canonical_text(job.get("title", ""))
    role = canonical_text(job.get("roleDisplay", "") or job.get("role", ""))

    if len(compact) <= 7:
        return True
    if title and compact in title and len(compact) <= 28:
        return True
    if role and compact == role:
        return True
    return False


def compress_preview_line(line: str) -> str:
    candidate = clean_text(line)
    for pattern in PREVIEW_DROP_PREFIXES:
        candidate = re.sub(pattern, "", candidate)
    candidate = re.sub(r"찾고 있습니다\.?$", "", candidate)
    candidate = re.sub(r"우대합니다\.?$", "", candidate)
    candidate = re.sub(r"전문가를\s*$", "", candidate)
    candidate = re.sub(r"역할입니다\.?$", "", candidate)
    candidate = clean_text(candidate)
    if not candidate:
        return ""

    if len(candidate) > 88:
        clauses = re.split(r",| 및 | 그리고 |하며 |하여 |후,? |기반으로 ", candidate)
        scored = []
        for clause in (clean_text(part) for part in clauses):
            if not clause or not re.search(r"(구축|개발|설계|검증|분석|최적화|운영|연동|통합|배포|평가)", clause):
                continue
            verb_hits = len(re.findall(r"(구축|개발|설계|검증|분석|최적화|운영|연동|통합|배포|평가)", clause))
            length_penalty = abs(len(clause) - 32) / 100
            score = (verb_hits * 3) + (1 if 14 <= len(clause) <= 56 else 0) - length_penalty
            scored.append((score, clause))
        if scored:
            candidate = max(scored, key=lambda item: item[0])[1]

    candidate = re.sub(r"(하고|하며|하여|한 후|하는)$", "", candidate)
    candidate = re.sub(
        r"(합니다|수행합니다|담당합니다|지원합니다|구축합니다|개발합니다|운영합니다|설계합니다|검증합니다|평가합니다)\.?$",
        "",
        candidate,
    )
    candidate = re.sub(r"(을|를)\s+담당$", "", candidate)
    candidate = clean_text(candidate)
    candidate = candidate.rstrip(" ,.")

    if len(candidate) > 72:
        candidate = candidate[:70].rstrip(" ,.") + "…"
    return candidate


def is_display_drop_line(line: str) -> bool:
    cleaned = clean_text(line)
    if not cleaned:
        return True
    for pattern in DISPLAY_DROP_PATTERNS:
        if re.match(pattern, cleaned):
            return True
    return False


def signalize_display_line(line: str, company: str) -> str:
    terms = clean_keyword_candidates(
        unique_non_generic(signal_terms_from_text(line, company), limit=6),
        limit=3,
    )
    if not terms:
        return ""
    return " · ".join(terms[:3])


def normalize_display_line(line: str, company: str, field: str) -> str:
    candidate = compress_preview_line(line)
    candidate = re.sub(r"^[•·▪■□◦●\\-–>]+\\s*", "", candidate)
    candidate = clean_text(candidate)
    if not candidate or is_noise_line(candidate) or is_display_drop_line(candidate):
        return ""
    candidate_lower = candidate.lower()
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{1,}|[가-힣]{2,}", candidate)
    meta_hits = sum(1 for term in DISPLAY_META_ADMIN_TERMS if term in candidate_lower)
    meta_hits += sum(1 for term in DISPLAY_META_NAV_TERMS if term in candidate_lower)
    duty_hits = sum(1 for term in DISPLAY_DUTY_TERMS if term in candidate_lower)
    role_noun_hits = sum(1 for term in DISPLAY_ROLE_NOUN_TERMS if term in candidate_lower)
    company_compact = canonical_text(company)
    if company_compact and company_compact in canonical_text(candidate):
        meta_hits += 1
    if re.search(r"(모집|채용|지원하기|바로가기|문의하기|접수|반환|전형)", candidate_lower):
        meta_hits += 1
    if re.search(r"(구축|개발|설계|분석|검증|운영|평가|최적화|자동화|연동|통합|배포|구현|모델링|튜닝|실험|리서치|조사|기획|관리|개선|고도화|테스트|모니터링|서빙|파이프라인|유지보수|리팩토링)", candidate_lower):
        duty_hits += 1
    if role_noun_hits:
        meta_hits += 1
    if meta_hits >= 2 and duty_hits == 0:
        return ""
    if (meta_hits + role_noun_hits) >= 2 and duty_hits <= 1 and len(tokens) <= 8:
        return ""
    if meta_hits >= 1 and role_noun_hits and duty_hits <= 1 and len(tokens) <= 8:
        return ""
    if re.match(r"^.*(모집|채용)$", candidate) and len(candidate) <= 32:
        return ""
    if re.match(r"^[가-힣]{2,}(지사|센터|오피스)$", candidate) or candidate in {"과천"}:
        return ""
    if re.search(r"(지원 가능|지원 가능합니다)", candidate):
        return ""

    compact = canonical_text(candidate)
    if any(token in compact for token in DISPLAY_BAD_TOKENS) or any(
        re.search(pattern, candidate) for pattern in DISPLAY_SIGNAL_LINE_PATTERNS
    ):
        signalized = signalize_display_line(candidate, company)
        if signalized:
            return signalized
        return ""

    if field in {"requirements", "preferred"} and len(candidate) > 72:
        signalized = signalize_display_line(candidate, company)
        if signalized:
            return signalized

    return candidate


def has_duty_signal(line: str) -> bool:
    normalized = clean_text(line).lower()
    if not normalized:
        return False
    return any(term in normalized for term in DISPLAY_DUTY_TERMS)


def is_structural_meta_line(line: str, job: dict | None = None) -> bool:
    candidate = clean_text(line)
    if not candidate:
        return True
    normalized = candidate.lower()
    tokens = re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{1,}|[가-힣]{2,}", candidate)
    meta_hits = sum(1 for term in DISPLAY_META_ADMIN_TERMS if term in normalized)
    meta_hits += sum(1 for term in DISPLAY_META_NAV_TERMS if term in normalized)
    duty_hits = sum(1 for term in DISPLAY_DUTY_TERMS if term in normalized)
    role_noun_hits = sum(1 for term in DISPLAY_ROLE_NOUN_TERMS if term in normalized)
    if job and looks_like_title_echo(candidate, job):
        meta_hits += 2
    if re.search(r"(모집|채용|지원하기|바로가기|문의하기|접수|반환|전형|결과 통지|합격발표)", normalized):
        meta_hits += 1
    if re.search(r"(지사|센터|오피스|지점)", normalized) and duty_hits == 0:
        meta_hits += 1
    if role_noun_hits:
        meta_hits += 1
    if meta_hits >= 2 and duty_hits == 0:
        return True
    if (meta_hits + role_noun_hits) >= 2 and duty_hits <= 1 and len(tokens) <= 8:
        return True
    if meta_hits >= 1 and duty_hits == 0 and len(tokens) <= 5:
        return True
    return False


def sanitize_display_list(values: list[str], company: str, field: str, limit: int = 12) -> list[str]:
    lines = []
    seen = set()
    for value in values or []:
        cleaned = normalize_display_line(value, company, field)
        compact = canonical_text(cleaned)
        if not cleaned or not compact or compact in seen:
            continue
        seen.add(compact)
        lines.append(cleaned)
        if len(lines) >= limit:
            break
    return lines


def sanitize_display_detail_body(value: str, company: str, limit: int = 18) -> str:
    lines = sanitize_display_list(split_detail_lines(value), company, "detailBody", limit=limit)
    return "\n".join(lines)


def row_is_sparse_recruitment_row(job: dict, summary_quality: str, detail_lines: list[str], preview_lines: list[str] | None = None) -> bool:
    preview_lines = preview_lines or []
    title = clean_display_title(job.get("title", ""))
    if is_generic_recruitment_title(title):
        return True

    sample_lines = [line for line in detail_lines[:8] if clean_text(line)]
    if not sample_lines:
        sample_lines = [line for line in preview_lines[:3] if clean_text(line)]

    if not sample_lines:
        return summary_quality == "low"

    meta_hits = sum(1 for line in sample_lines if is_structural_meta_line(line, job))
    duty_hits = sum(1 for line in sample_lines if has_duty_signal(line))

    if summary_quality == "low" and meta_hits >= 2 and duty_hits == 0:
        return True
    if meta_hits >= 3 and duty_hits <= 1:
        return True
    if summary_quality == "low" and meta_hits >= 1 and duty_hits == 0 and len(sample_lines) <= 4:
        return True
    return False


def build_display_job(job: dict) -> dict:
    company = job.get("company", "")
    return {
        **job,
        "detailBody": sanitize_display_detail_body(job.get("detailBody", ""), company),
        "tasks": sanitize_display_list(job.get("tasks") or [], company, "tasks", limit=12),
        "requirements": sanitize_display_list(job.get("requirements") or [], company, "requirements", limit=12),
        "preferred": sanitize_display_list(job.get("preferred") or [], company, "preferred", limit=12),
    }


def has_distinctive_keywords(keywords: list[str]) -> bool:
    generic = {
        "ai",
        "인공지능",
        "엔지니어",
        "리서처",
        "모델",
        "개발",
        "데이터",
        "연구",
        "분석",
        "최적화",
        "설계",
        "운영",
        "서비스",
    }
    for keyword in keywords:
        compact = canonical_text(keyword)
        if compact and compact not in generic and len(compact) >= 3:
            return True
    return False


def summary_needs_override(summary: str, keywords: list[str]) -> bool:
    cleaned = clean_text(summary)
    if not cleaned:
        return True
    if len(cleaned) > 42:
        return True
    if cleaned.endswith(SUMMARY_ENDING_PATTERNS):
        return True
    if any(re.match(pattern, cleaned) for pattern in SUMMARY_BAD_PATTERNS):
        return True
    if not has_distinctive_keywords(keywords) and len(cleaned) <= 18:
        return True
    return False


def build_preview_lines(job: dict) -> list[str]:
    detail_lines = split_sentences(job.get("detailBody", ""))
    filtered = [
        compress_preview_line(line)
        for line in detail_lines
        if not is_noise_line(line)
        and not looks_like_title_echo(line, job)
        and not is_structural_meta_line(line, job)
    ]
    filtered = [line for line in filtered if line and not is_noise_line(line) and not is_structural_meta_line(line, job)]
    if filtered:
        unique = []
        for line in filtered:
            if line not in unique:
                unique.append(line)
            if len(unique) >= 3:
                break
        return unique

    fallback_lines = []
    for key in ["tasks", "requirements", "preferred"]:
        for value in job.get(key, []):
            cleaned = compress_preview_line(value)
            if cleaned and not is_noise_line(cleaned) and not is_structural_meta_line(cleaned, job):
                fallback_lines.append(cleaned)
            if len(fallback_lines) >= 3:
                return fallback_lines
    return fallback_lines


def build_detail_line_count(job: dict) -> int:
    detail_lines = split_detail_lines(job.get("detailBody", ""))
    filtered = [line for line in detail_lines if not is_noise_line(line)]
    if filtered:
        return len(filtered)

    fallback = 0
    for key in ["tasks", "requirements", "preferred"]:
        fallback += len([value for value in job.get(key, []) if clean_text(value)])
    return fallback


def role_sort_key(name: str) -> tuple[int, str]:
    if name in ROLE_ORDER:
        return (ROLE_ORDER.index(name), name)
    return (len(ROLE_ORDER), name)


def build_role_filters(rows: list[dict]) -> list[dict]:
    counts = {}
    for row in rows:
        role = row["roleGroup"]
        counts[role] = counts.get(role, 0) + 1

    filters = [{"name": "전체", "count": len(rows)}]
    for role in sorted(counts, key=role_sort_key):
        filters.append({"name": role, "count": counts[role]})
    return filters


def summarize_diagnostic_row(row: dict) -> dict:
    return {
        "id": row.get("id", ""),
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "roleGroup": row.get("roleGroup", ""),
        "rawRole": row.get("rawRole", ""),
        "serviceScopeAction": row.get("serviceScopeResolvedAction", ""),
        "serviceScopeReason": row.get("serviceScopeReason", ""),
        "serviceScopeConfidence": row.get("serviceScopeConfidence", ""),
        "serviceScopeSource": row.get("serviceScopeSource", ""),
        "focusLabel": row.get("focusLabel", ""),
        "highlightKeywords": row.get("highlightKeywords", []) or [],
        "summaryQuality": row.get("summaryQuality", ""),
        "active": bool(row.get("active")),
    }


def split_group_tags(value: str) -> list[str]:
    tags = []
    seen = set()
    for part in str(value or "").split("/"):
        cleaned = clean_text(part)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        tags.append(cleaned)
    return tags[:4]


def clean_display_title(title: str) -> str:
    cleaned = clean_text(re.sub(r"^\[[^\]]+\]\s*", "", title or ""))
    cleaned = re.sub(r"\s*채용\s*$", "", cleaned)
    cleaned = re.sub(r"\s*모집중?\s*$", "", cleaned)
    return cleaned[:64]


def title_needs_override(title: str) -> bool:
    cleaned = clean_display_title(title)
    if not cleaned:
        return True
    compact = canonical_text(cleaned)
    if len(compact) <= 6:
        return True
    if re.search(r"(채용|모집)", cleaned):
        return True
    if re.search(r"\b(sr\.?|staff|senior|principal)\b", cleaned, re.IGNORECASE):
        return True
    if re.search(r"(engineer|developer|researcher|scientist|analyst)", cleaned, re.IGNORECASE):
        ascii_chars = sum(1 for ch in cleaned if ord(ch) < 128 and ch.isalpha())
        if ascii_chars >= max(6, len(cleaned) // 4):
            return True
    if re.search(r"(engineer|developer|researcher|scientist|analyst)$", cleaned, re.IGNORECASE):
        return True
    return False


def is_generic_recruitment_title(title: str) -> bool:
    cleaned = clean_display_title(title)
    compact = canonical_text(cleaned)
    if compact in {
        canonical_text("채용"),
        canonical_text("인재채용"),
        canonical_text("상시채용"),
        canonical_text("채용공고"),
    }:
        return True
    if re.search(r"(채용|모집)$", cleaned) and len(cleaned) <= 20:
        return True
    return False


def choose_display_summary(
    summary: str,
    preview_lines: list[str],
    keywords: list[str],
    role: str,
    title: str,
) -> str:
    cleaned_summary = clean_text(summary)
    if not summary_needs_override(cleaned_summary, keywords):
        return cleaned_summary

    for line in preview_lines:
        candidate = compress_preview_line(line)
        if candidate and len(candidate) >= 10 and re.search(
            r"(구축|개발|설계|검증|분석|최적화|운영|연동|통합|배포|평가|자동화|지원)",
            candidate,
        ):
            return candidate

    keyword_phrase = " · ".join(clean_text(keyword) for keyword in keywords[:2] if clean_text(keyword))
    if keyword_phrase and title_needs_override(title):
        return keyword_phrase

    cleaned_title = clean_display_title(title)
    if cleaned_title and not title_needs_override(cleaned_title):
        return cleaned_title
    if keyword_phrase:
        return keyword_phrase
    return clean_text(role) or cleaned_summary


def clean_keyword_candidates(values: list[str], limit: int = 5) -> list[str]:
    result = []
    for value in unique_non_generic(values, limit=limit * 2):
        cleaned = clean_text(value)
        if (
            not cleaned
            or len(cleaned) > 18
            or " 또는 " in cleaned
            or cleaned.endswith("경험")
            or cleaned.endswith("소통")
        ):
            continue
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


SEMANTIC_NOISE_TERMS = {
    "미분류",
    "미기재",
    "경력",
    "신입",
    "인턴",
    "시니어",
    "주니어",
    "학사",
    "석사",
    "박사",
    "학위",
    "학력",
    "전공",
    "채용",
    "일반채용",
    "전문연구요원",
    "기타",
}
SEMANTIC_NOISE_KEYS = {canonical_text(term) for term in SEMANTIC_NOISE_TERMS}
SEMANTIC_ALIAS_MAP = {
    canonical_text("엘엘엠"): "LLM",
    canonical_text("지피유"): "GPU",
    canonical_text("엔피유"): "NPU",
    canonical_text("검색증강생성"): "RAG",
    canonical_text("컴퓨터비전"): "Computer Vision",
    canonical_text("컴퓨터 비전"): "Computer Vision",
    canonical_text("추천 시스템"): "추천",
    canonical_text("Recommendation System"): "추천",
    canonical_text("에이더블유에스"): "AWS",
    canonical_text("지씨피"): "GCP",
    canonical_text("쿠버네티스"): "Kubernetes",
    canonical_text("파이토치"): "PyTorch",
    canonical_text("텐서플로"): "TensorFlow",
    canonical_text("에스큐엘"): "SQL",
    canonical_text("머신러닝"): "Machine Learning",
    canonical_text("딥러닝"): "Deep Learning",
    canonical_text("시계열"): "시계열",
}
SEMANTIC_SKILL_AXIS_TERMS = {
    "LLM",
    "RAG",
    "MLOps",
    "LLOps",
    "PyTorch",
    "TensorFlow",
    "Kubernetes",
    "Docker",
    "AWS",
    "GCP",
    "GPU",
    "NPU",
    "CUDA",
    "Triton",
    "ONNX",
    "SQL",
    "Spark",
    "Airflow",
    "Computer Vision",
    "NLP",
    "VLM",
    "OCR",
    "추천",
    "시계열",
    "통계모델링",
    "A/B Testing",
    "Vector Database",
    "Model Serving",
    "Data Pipeline",
}
SEMANTIC_SKILL_AXIS_KEYS = {canonical_text(term) for term in SEMANTIC_SKILL_AXIS_TERMS}
SEMANTIC_TEMPLATE_SPECS = [
    (
        ("LLM", "검색"),
        "LLM 검색 서비스화",
        "LLM을 검색, RAG, 서빙 흐름과 연결해 제품 안에서 답을 찾게 만드는 채용군입니다.",
    ),
    (
        ("LLM", "RAG"),
        "LLM 검색 서비스화",
        "LLM을 검색, RAG, 서빙 흐름과 연결해 제품 안에서 답을 찾게 만드는 채용군입니다.",
    ),
    (
        ("AI반도체", "최적화"),
        "AI반도체 추론 최적화",
        "가속기, 런타임, 모델 최적화를 함께 다뤄 추론 성능을 끌어올리는 채용군입니다.",
    ),
    (
        ("AI반도체", "검증"),
        "AI반도체 검증 자동화",
        "AI 반도체 설계와 검증 신호가 함께 나타나 칩 품질과 테스트 체계를 맡는 채용군입니다.",
    ),
    (
        ("AI반도체", "GPU"),
        "AI반도체 가속 인프라",
        "GPU/NPU 가속 환경과 AI 반도체 구현 요구가 함께 나타나는 채용군입니다.",
    ),
    (
        ("인프라", "MLOps"),
        "AI 플랫폼 운영화",
        "모델을 서비스까지 안정적으로 옮기기 위한 배포, 관측, 파이프라인 역량이 묶인 채용군입니다.",
    ),
    (
        ("인프라", "LLM"),
        "LLM 플랫폼 운영화",
        "LLM 모델을 서비스 인프라 위에서 배포, 확장, 운영하는 요구가 함께 나타나는 채용군입니다.",
    ),
    (
        ("인프라", "Kubernetes"),
        "AI 플랫폼 운영화",
        "모델을 서비스까지 안정적으로 옮기기 위한 배포, 관측, 파이프라인 역량이 묶인 채용군입니다.",
    ),
    (
        ("인프라", "GPU"),
        "GPU 인프라 운영",
        "GPU 자원, 배포 환경, 모델 실행 요구를 함께 다뤄 학습·추론 기반을 맡는 채용군입니다.",
    ),
    (
        ("인프라", "AI반도체"),
        "AI반도체 플랫폼 인프라",
        "AI 반도체와 운영 인프라가 함께 등장해 가속 환경을 서비스 기반으로 연결하는 채용군입니다.",
    ),
    (
        ("데이터플랫폼", "인프라"),
        "데이터 플랫폼 인프라",
        "데이터 파이프라인과 운영 인프라를 함께 설계해 모델과 분석의 기반을 만드는 채용군입니다.",
    ),
    (
        ("데이터플랫폼", "ETL"),
        "데이터 파이프라인 운영",
        "ETL, 저장소, 처리 흐름을 함께 다뤄 분석과 모델링에 쓰이는 데이터를 안정화하는 채용군입니다.",
    ),
    (
        ("BI", "지표분석"),
        "제품 지표 분석",
        "BI와 지표 분석이 함께 등장해 제품 의사결정과 실험 해석을 지원하는 채용군입니다.",
    ),
    (
        ("제품분석", "SQL"),
        "제품 데이터 분석",
        "SQL 기반 분석과 제품 지표 해석이 함께 요구되어 성장·실험 판단을 맡는 채용군입니다.",
    ),
    (
        ("LLM", "PyTorch"),
        "LLM 모델 엔지니어링",
        "LLM 개발과 PyTorch 구현 역량이 함께 요구되어 모델 학습·평가·응용을 맡는 채용군입니다.",
    ),
    (
        ("최적화", "PyTorch"),
        "모델 최적화 엔지니어링",
        "PyTorch 기반 모델을 성능, 비용, 추론 속도 관점에서 개선하는 채용군입니다.",
    ),
    (
        ("AI반도체", "하드웨어"),
        "AI반도체 하드웨어 구현",
        "하드웨어 설계 신호와 AI 반도체 요구가 함께 나타나 칩 구현에 가까운 채용군입니다.",
    ),
    (
        ("추천", "시계열"),
        "추천 모델 운영",
        "개인화, 예측, 실험 지표를 함께 다뤄 추천 성능을 실제 서비스에서 검증하는 채용군입니다.",
    ),
    (
        ("추천", "A/B Testing"),
        "추천 실험 고도화",
        "추천 모델과 실험 설계가 함께 요구되어 성능 개선을 지표로 증명하는 채용군입니다.",
    ),
    (
        ("헬스케어", "통계모델링"),
        "헬스케어 통계 모델링",
        "의료 데이터와 통계 모델링을 함께 다뤄 임상·생체 신호 해석을 맡는 채용군입니다.",
    ),
    (
        ("자율주행", "시스템구현"),
        "자율주행 시스템 구현",
        "인지, 제어, 시스템 통합 신호가 함께 나타나 실제 주행 환경 구현에 가까운 채용군입니다.",
    ),
    (
        ("비전", "문서AI"),
        "문서·비전 자동화",
        "이미지와 문서 이해 기술을 결합해 추출, 검수, 자동화 문제를 푸는 채용군입니다.",
    ),
    (
        ("비전", "Computer Vision"),
        "컴퓨터 비전 응용",
        "시각 인식 모델과 서비스 적용 요구가 함께 나타나는 채용군입니다.",
    ),
    (
        ("문서AI", "Computer Vision"),
        "문서·비전 자동화",
        "문서 이해와 시각 인식 기술을 함께 써서 추출, 검수, 자동화 문제를 푸는 채용군입니다.",
    ),
    (
        ("문서AI", "검색"),
        "문서 검색 자동화",
        "문서 이해와 검색 흐름을 결합해 지식 추출과 탐색을 자동화하는 채용군입니다.",
    ),
    (
        ("검증", "LLM"),
        "LLM 검증 체계",
        "LLM 결과를 평가하고 검증하는 절차와 도구를 함께 다루는 채용군입니다.",
    ),
    (
        ("헬스케어", "비전"),
        "헬스케어 비전 모델링",
        "의료·생체 데이터 맥락에서 이미지 인식과 모델 검증을 함께 다루는 채용군입니다.",
    ),
]
SEMANTIC_BUNDLE_TEMPLATES = [
    (frozenset(canonical_text(term) for term in terms), label, thesis)
    for terms, label, thesis in SEMANTIC_TEMPLATE_SPECS
]


def split_semantic_source_terms(value) -> list[str]:
    if isinstance(value, list):
        values = value
    else:
        values = re.split(r"[\n\r,;/|·]+", str(value or ""))
    return [clean_text(item) for item in values if clean_text(item)]


def normalize_semantic_term(value: str) -> str:
    cleaned = canonical_focus_label(clean_text(value))
    compact = canonical_text(cleaned)
    if not cleaned or not compact or compact in SEMANTIC_NOISE_KEYS:
        return ""
    if re.search(r"(경력|신입|인턴|[0-9]+년|\d+\+)", cleaned):
        return ""
    normalized = SEMANTIC_ALIAS_MAP.get(compact, cleaned)
    if len(normalized) > 24 or canonical_text(normalized) in SEMANTIC_NOISE_KEYS:
        return ""
    return normalized


def unique_semantic_terms(values, limit: int = 10) -> list[str]:
    terms = []
    seen = set()
    for value in values or []:
        normalized = normalize_semantic_term(value)
        key = canonical_text(normalized)
        if not key or key in seen:
            continue
        seen.add(key)
        terms.append(normalized)
        if len(terms) >= limit:
            break
    return terms


def semantic_skill_is_axis(term: str) -> bool:
    return canonical_text(term) in SEMANTIC_SKILL_AXIS_KEYS


def semantic_profile(row: dict) -> dict:
    raw_axes = (
        split_semantic_source_terms(row.get("stage2FocusAxes"))
        or split_semantic_source_terms(row.get("stage2Focus"))
        or split_semantic_source_terms(row.get("focusLabel"))
    )
    axes = unique_semantic_terms(raw_axes, limit=6)
    summary_tags = unique_semantic_terms(row.get("stage2SummaryTags") or row.get("groupTags") or [], limit=6)
    skills = unique_semantic_terms(row.get("stage2SkillTerms") or row.get("skills") or [], limit=12)
    if not axes:
        axes = unique_semantic_terms([row.get("focusLabel", "")], limit=3)
    return {
        "axes": axes,
        "summaryTags": summary_tags,
        "skills": skills,
        "skillAxes": [skill for skill in skills if semantic_skill_is_axis(skill)],
    }


def semantic_pair_key(left: str, right: str) -> tuple[str, str]:
    return tuple(sorted([canonical_text(left), canonical_text(right)]))


def semantic_pair_candidates(profile: dict) -> list[tuple[str, str]]:
    axes = profile.get("axes", [])[:5]
    skills = profile.get("skillAxes", [])[:8]
    candidates = []

    for index, left in enumerate(axes):
        for right in axes[index + 1 :]:
            if canonical_text(left) != canonical_text(right):
                candidates.append((left, right))

    for axis in axes:
        for skill in skills:
            if canonical_text(axis) != canonical_text(skill):
                candidates.append((axis, skill))

    if not candidates:
        for index, left in enumerate(skills[:6]):
            for right in skills[index + 1 : 6]:
                if canonical_text(left) != canonical_text(right):
                    candidates.append((left, right))

    deduped = []
    seen = set()
    for left, right in candidates:
        key = semantic_pair_key(left, right)
        if key in seen:
            continue
        seen.add(key)
        deduped.append((left, right))
    return deduped


def describe_semantic_pair(pair: tuple[str, str]) -> tuple[str, str, bool]:
    pair_keys = frozenset(canonical_text(term) for term in pair)
    for required, label, thesis in SEMANTIC_BUNDLE_TEMPLATES:
        if required.issubset(pair_keys):
            return label, thesis, True

    label = f"{pair[0]} · {pair[1]}"
    thesis = f"{pair[0]} 축의 공고가 {pair[1]} 역량과 함께 설명되는 채용군입니다."
    return label, thesis, False


def semantic_term_counter(profile: dict) -> Counter:
    counter = Counter()
    for term in [*profile.get("axes", []), *profile.get("summaryTags", []), *profile.get("skills", [])]:
        normalized = normalize_semantic_term(term)
        if normalized:
            counter[normalized] += 1
    return counter


def build_semantic_bundles(rows: list[dict], max_bundles: int = 12) -> list[dict]:
    profiles = {row.get("id", ""): semantic_profile(row) for row in rows}
    stats = {}
    row_lookup = {row.get("id", ""): row for row in rows}
    row_order = {row.get("id", ""): index for index, row in enumerate(rows)}

    for row in rows:
        row_id = row.get("id", "")
        if not row_id:
            continue
        profile = profiles.get(row_id, {})
        for left, right in semantic_pair_candidates(profile):
            key = semantic_pair_key(left, right)
            if not all(key):
                continue
            bucket = stats.setdefault(
                key,
                {
                    "pair": (left, right),
                    "rowIds": set(),
                    "companies": Counter(),
                    "termCounter": Counter(),
                    "activeCount": 0,
                },
            )
            bucket["rowIds"].add(row_id)
            if row.get("company"):
                bucket["companies"][row["company"]] += 1
            if row.get("active"):
                bucket["activeCount"] += 1
            bucket["termCounter"].update(semantic_term_counter(profile))

    candidates = []
    for bucket in stats.values():
        posting_count = len(bucket["rowIds"])
        company_count = len(bucket["companies"])
        if posting_count < 3 or company_count < 2:
            continue
        label, thesis, templated = describe_semantic_pair(bucket["pair"])
        score = posting_count * 5 + company_count * 3 + bucket["activeCount"] + (18 if templated else 0)
        candidates.append({**bucket, "label": label, "thesis": thesis, "templated": templated, "score": score})

    if len(candidates) < max_bundles:
        for bucket in stats.values():
            if len(bucket["rowIds"]) < 2 or len(bucket["companies"]) < 2:
                continue
            label, thesis, templated = describe_semantic_pair(bucket["pair"])
            if any(candidate["label"] == label and candidate["pair"] == bucket["pair"] for candidate in candidates):
                continue
            score = len(bucket["rowIds"]) * 5 + len(bucket["companies"]) * 3 + bucket["activeCount"] + (18 if templated else 0)
            candidates.append({**bucket, "label": label, "thesis": thesis, "templated": templated, "score": score})

    selected = []
    seen_labels = set()
    covered_row_ids = set()
    remaining = candidates[:]
    while remaining and len(selected) < max_bundles:
        best_index = None
        best_score = None
        for index, candidate in enumerate(remaining):
            label_key = canonical_text(candidate["label"])
            if label_key in seen_labels:
                continue
            new_rows = candidate["rowIds"] - covered_row_ids
            if selected and len(new_rows) < 2:
                continue
            diversity_score = (
                len(new_rows) * 12
                + min(len(candidate["rowIds"]), 18) * 2
                + len(candidate["companies"]) * 3
                + (22 if candidate["templated"] else 0)
                + candidate["score"] * 0.2
            )
            sort_key = (diversity_score, len(new_rows), len(candidate["rowIds"]), len(candidate["companies"]))
            if best_score is None or sort_key > best_score:
                best_score = sort_key
                best_index = index
        if best_index is None:
            break
        candidate = remaining.pop(best_index)
        label_key = canonical_text(candidate["label"])
        seen_labels.add(label_key)
        selected.append(candidate)
        covered_row_ids.update(candidate["rowIds"])

    bundles = []
    for index, candidate in enumerate(selected, start=1):
        pair = list(candidate["pair"])
        row_ids = sorted(candidate["rowIds"], key=lambda row_id: row_order.get(row_id, 9999))
        sample_companies = [company for company, _count in candidate["companies"].most_common(4)]
        evidence_terms = unique_semantic_terms(
            [*pair, *(term for term, _count in candidate["termCounter"].most_common(10))],
            limit=7,
        )
        sample_postings = [
            {
                "id": row_lookup[row_id].get("id", ""),
                "company": row_lookup[row_id].get("company", ""),
                "title": row_lookup[row_id].get("title", ""),
            }
            for row_id in row_ids[:4]
            if row_id in row_lookup
        ]
        company_count = len(candidate["companies"])
        posting_count = len(row_ids)
        confidence = min(
            0.95,
            0.42
            + min(posting_count, 14) * 0.026
            + min(company_count, 10) * 0.025
            + (0.12 if candidate["templated"] else 0),
        )
        bundles.append(
            {
                "id": f"semantic-{index:02d}",
                "label": candidate["label"],
                "thesis": candidate["thesis"],
                "axes": [term for term in pair if not semantic_skill_is_axis(term)],
                "skills": [term for term in evidence_terms if semantic_skill_is_axis(term)][:5],
                "evidenceTerms": evidence_terms,
                "postingCount": posting_count,
                "activePostingCount": sum(1 for row_id in row_ids if row_lookup.get(row_id, {}).get("active")),
                "companyCount": company_count,
                "sampleCompanies": sample_companies,
                "samplePostings": sample_postings,
                "postingIds": row_ids,
                "confidence": round(confidence, 3),
                "method": "stage2_semantic_graph",
                "usesTemplate": bool(candidate["templated"]),
            }
        )
    return bundles


def build_role_semantic_bundles(rows: list[dict]) -> dict[str, list[dict]]:
    grouped = {}
    for row in rows:
        role = clean_text(row.get("roleGroup", ""))
        if not role:
            continue
        grouped.setdefault(role, []).append(row)
    return {
        role: build_semantic_bundles(role_rows, max_bundles=8)
        for role, role_rows in grouped.items()
    }


def normalize_structured_signals(payload: dict) -> dict:
    data = payload if isinstance(payload, dict) else {}

    def clean_list(key: str, limit: int) -> list[str]:
        values = []
        for value in data.get(key, []) if isinstance(data.get(key, []), list) else []:
            cleaned = clean_text(value)
            if not cleaned or cleaned in values:
                continue
            values.append(cleaned)
            if len(values) >= limit:
                break
        return values

    return {
        "quality": clean_text(data.get("quality", "")),
        "domainSignals": clean_list("domainSignals", 4),
        "problemSignals": clean_list("problemSignals", 5),
        "systemSignals": clean_list("systemSignals", 4),
        "modelSignals": clean_list("modelSignals", 4),
        "dataSignals": clean_list("dataSignals", 4),
        "workflowSignals": clean_list("workflowSignals", 4),
        "roleSignals": clean_list("roleSignals", 3),
        "confidenceNotes": clean_list("confidenceNotes", 4),
    }


def normalize_section_signal_facets(payload: dict) -> dict:
    data = payload if isinstance(payload, dict) else {}
    normalized = {}
    for section_id in ("detailBody", "tasks", "requirements", "preferred", "skills"):
        section_payload = data.get(section_id, {})
        if not isinstance(section_payload, dict):
            normalized[section_id] = {"keyword": [], "tag": [], "context": []}
            continue
        normalized[section_id] = {
            "keyword": clean_keyword_candidates(section_payload.get("keyword", []), limit=4),
            "tag": clean_keyword_candidates(section_payload.get("tag", []), limit=4),
            "context": clean_keyword_candidates(section_payload.get("context", []), limit=4),
        }
    return normalized


def normalize_allowed_role(value: str) -> str:
    cleaned = clean_text(value)
    return cleaned if cleaned in ROLE_ORDER else ""


def role_signal_primary(signals: dict) -> str:
    values = signals.get("roleSignals", []) if isinstance(signals.get("roleSignals", []), list) else []
    for value in values:
        cleaned = normalize_allowed_role(value)
        if cleaned:
            return cleaned
    return ""


def add_role_score(scores: dict[str, float], role: str, weight: float) -> None:
    cleaned = normalize_allowed_role(role)
    if not cleaned:
        return
    scores[cleaned] = scores.get(cleaned, 0.0) + weight


def role_classifier_weight(confidence: str) -> float:
    normalized = clean_text(confidence).lower()
    if normalized == "high":
        return 5.25
    if normalized == "medium":
        return 3.75
    if normalized == "low":
        return 2.0
    return 0.0


def resolve_role_group(
    job: dict,
    summary_item: dict,
    structured_signals: dict,
    override: dict,
    role_override: dict | None = None,
) -> str:
    raw_role = normalize_allowed_role(job.get("roleDisplay", "") or job.get("role", ""))
    summary_role = normalize_allowed_role(summary_item.get("role", ""))
    signal_role = role_signal_primary(structured_signals)
    override_action = clean_text(override.get("action", "")).lower()
    mapped_role = normalize_allowed_role(override.get("mappedRole", "")) if override_action == "include" else ""
    role_override = role_override if isinstance(role_override, dict) else {}
    classifier_role = normalize_allowed_role(role_override.get("roleGroup", ""))
    classifier_confidence = clean_text(role_override.get("confidence", "")).lower()
    role_sources = [raw_role, summary_role, signal_role]
    non_classifier_counts: dict[str, int] = {}
    for source_role in role_sources:
        cleaned = normalize_allowed_role(source_role)
        if not cleaned:
            continue
        non_classifier_counts[cleaned] = non_classifier_counts.get(cleaned, 0) + 1
    consensus_role = ""
    consensus_count = 0
    if non_classifier_counts:
        consensus_role, consensus_count = sorted(
            non_classifier_counts.items(),
            key=lambda item: (-item[1], role_sort_key(item[0])),
        )[0]

    # Prefer the fresh model role. High-confidence classifier output is authoritative;
    # medium-confidence output should only yield to a full three-way upstream consensus.
    if classifier_role:
        if classifier_confidence == "high":
            return classifier_role
        if classifier_confidence == "medium":
            if not consensus_role or consensus_role == classifier_role or consensus_count < 3:
                return classifier_role

    title = clean_text(job.get("title", "")).lower()
    evidence_text = " ".join(
        [
            title,
            clean_text(summary_item.get("summary", "")).lower(),
            " ".join(clean_text(value).lower() for value in (summary_item.get("keywords") or [])),
            " ".join(clean_text(value).lower() for value in structured_signals.get("modelSignals", [])),
            " ".join(clean_text(value).lower() for value in structured_signals.get("workflowSignals", [])),
            " ".join(clean_text(value).lower() for value in structured_signals.get("dataSignals", [])),
        ]
    )

    scores: dict[str, float] = {}
    add_role_score(scores, raw_role, 3.0)
    add_role_score(scores, summary_role, 3.5)
    add_role_score(scores, signal_role, 4.0)
    # Service-scope output stays as a low-weight hint; it should not freely override the display role.
    add_role_score(scores, mapped_role, 1.25)
    add_role_score(scores, classifier_role, role_classifier_weight(classifier_confidence))

    # When independent signals agree, keep that consensus stable even if a single stage disagrees.
    if raw_role and raw_role == signal_role:
        add_role_score(scores, raw_role, 2.25)
    if raw_role and raw_role == summary_role:
        add_role_score(scores, raw_role, 1.5)
    if signal_role and signal_role == summary_role:
        add_role_score(scores, signal_role, 1.75)
    if classifier_role and classifier_role == signal_role:
        add_role_score(scores, classifier_role, 1.0)
    if classifier_role and classifier_role == raw_role:
        add_role_score(scores, classifier_role, 0.75)

    if re.search(r"data scientist|데이터 사이언티스트|clinical research scientist|임상연구", title):
        add_role_score(scores, "데이터 사이언티스트", 6.5)
    if (
        re.search(
            r"data analyst|business analyst|\banalyst\b|insight|crm|cx|pmo|growth marketing|performance marketer|fp&a|financial planning|process innovation|플랫폼 운영|작품 운영",
            title,
        )
        and not re.search(r"data scientist|clinical research scientist|임상연구", title)
    ):
        add_role_score(scores, "데이터 분석가", 6.0)
    if re.search(r"research scientist|researcher|research engineer|\br&d\b|연구", title):
        if re.search(r"clinical research scientist|임상연구|data scientist", title):
            add_role_score(scores, "데이터 사이언티스트", 5.5)
        else:
            add_role_score(scores, "인공지능 리서처", 6.0)
    if re.search(r"\bengineer\b|엔지니어|mlops|platform|serving|backend|infra|solution architect|architect", title):
        if not re.search(r"research engineer", title):
            add_role_score(scores, "인공지능 엔지니어", 5.0)

    if re.search(r"모델|llm|vlm|비전|vision|multimodal|foundation|파운데이션|학습|추론|파이토치|pytorch|tensorflow", evidence_text):
        add_role_score(scores, "인공지능 엔지니어", 1.0)
    if re.search(r"논문|학회|benchmark|벤치마크|연구", evidence_text):
        add_role_score(scores, "인공지능 리서처", 1.0)
    if re.search(r"통계|가설|실험|시계열|회귀|clinical|임상|의료영상|헬스케어|검증", evidence_text):
        add_role_score(scores, "데이터 사이언티스트", 1.0)
    if re.search(r"대시보드|리포트|report|bi|sql|지표|마케팅|캠페인|사용자 행동", evidence_text):
        add_role_score(scores, "데이터 분석가", 1.0)

    if not scores:
        return raw_role or summary_role or signal_role or mapped_role or "기타"

    ranked = sorted(scores.items(), key=lambda item: (-item[1], role_sort_key(item[0])))
    return ranked[0][0]


def flatten_structured_signals(signals: dict, keys: list[str]) -> list[str]:
    flattened = []
    for key in keys:
        for value in signals.get(key, []) if isinstance(signals.get(key, []), list) else []:
            cleaned = clean_text(value)
            if not cleaned or cleaned in flattened:
                continue
            flattened.append(cleaned)
    return flattened


def unique_clean_values(values: list[str], limit: int = 5) -> list[str]:
    result = []
    for value in values:
        cleaned = clean_text(value)
        if not cleaned or cleaned in result:
            continue
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


STRUCTURED_FOCUS_PRIORITY = [
    ("problemSignals", 9.2),
    ("domainSignals", 8.1),
    ("dataSignals", 7.4),
    ("systemSignals", 6.6),
    ("workflowSignals", 5.8),
    ("modelSignals", 4.8),
]


def project_keywords_from_structured_signals(signals: dict, limit: int = 5) -> list[str]:
    projected = []
    for key, _weight in STRUCTURED_FOCUS_PRIORITY:
        for value in signals.get(key, []) if isinstance(signals.get(key, []), list) else []:
            cleaned = canonical_focus_label(value)
            if focus_label_is_invalid(cleaned):
                continue
            if cleaned in projected:
                continue
            projected.append(cleaned)
            if len(projected) >= limit:
                return projected
    return projected


def project_focus_label_from_structured_signals(
    signals: dict,
    current_focus: str,
    keywords: list[str],
) -> str:
    current = canonical_focus_label(current_focus)
    keyword_set = {canonical_text(value) for value in keywords if clean_text(value)}
    candidates = []
    specific_exists = False

    for category, base_weight in STRUCTURED_FOCUS_PRIORITY:
        values = signals.get(category, []) if isinstance(signals.get(category, []), list) else []
        for index, value in enumerate(values):
            cleaned = canonical_focus_label(value)
            if focus_label_is_invalid(cleaned):
                continue
            score = base_weight - (index * 0.18)
            if canonical_text(cleaned) in keyword_set:
                score += 0.3
            if current and cleaned == current:
                score += 0.45
            if focus_label_is_broad(cleaned):
                score -= 1.35
            else:
                specific_exists = True
            candidates.append((score, cleaned))

    if current and not focus_label_is_invalid(current):
        candidates.append((4.2 if not focus_label_is_broad(current) else 1.9, current))

    if not candidates:
        return current

    ranked = []
    for score, label in candidates:
        adjusted = score
        if specific_exists and focus_label_is_broad(label):
            adjusted -= 1.15
        ranked.append((adjusted, len(label), label))

    ranked.sort(key=lambda item: (-item[0], item[1], item[2]))
    return ranked[0][2]


def build_base_rows(payload: dict) -> list[dict]:
    summary_store = load_summary_store()
    summary_items = summary_store.get("items", {})
    override_items = load_service_scope_override_store().get("items", {})
    role_override_items = load_role_group_override_store().get("items", {})
    stage2_deploy_enabled = bool(payload.get("source", {}).get("stage2Deploy", {}).get("enabled"))

    rows = []
    for job in payload["jobs"]:
        display_job = build_display_job(job)
        summary_item = summary_items.get(job["id"], {})
        override = resolve_service_scope_override(job, override_items=override_items)
        summary_quality = clean_text(summary_item.get("quality", "")).lower() or (
            "medium" if summary_item.get("summary") else "low"
        )
        raw_summary_keywords = summary_item.get("keywords", []) if summary_quality != "low" else []
        summary_keywords = clean_keyword_candidates(raw_summary_keywords, limit=5)
        focus_label = clean_text(summary_item.get("focusLabel", ""))
        structured_signals = normalize_structured_signals(summary_item.get("structuredSignals", {}))
        section_signal_facets = normalize_section_signal_facets(summary_item.get("sectionSignalFacets", {}))
        has_structured_signal = any(
            structured_signals.get(key)
            for key in [
                "domainSignals",
                "problemSignals",
                "systemSignals",
                "modelSignals",
                "dataSignals",
                "workflowSignals",
            ]
        )
        raw_detail_lines = split_detail_lines(job.get("detailBody", ""))
        sparse_row = row_is_sparse_recruitment_row(job, summary_quality, raw_detail_lines)
        if sparse_row:
            display_job = {
                **display_job,
                "detailBody": "",
                "tasks": [],
                "requirements": [],
                "preferred": [],
            }
            preview_lines = []
        else:
            preview_lines = build_preview_lines(display_job)
        override_action = clean_text(override.get("action", "")).lower()
        mapped_role = clean_text(override.get("mappedRole", "")) if override_action == "include" else ""
        raw_role = clean_text(job.get("roleDisplay", "") or job.get("role", ""))
        role_signature = compute_role_group_signature(job, summary_item)
        role_override = resolve_role_group_override(
            {"id": job["id"], "roleGroupSignature": role_signature, **job},
            summary_item,
            override_items=role_override_items,
        )
        resolved_role = resolve_role_group(
            job,
            summary_item,
            structured_signals,
            override,
            role_override=role_override,
        )
        if stage2_deploy_enabled and raw_role:
            resolved_role = raw_role
        structured_keywords = project_keywords_from_structured_signals(structured_signals, limit=5)

        if summary_quality == "low":
            focus_label = project_focus_label_from_structured_signals(
                structured_signals,
                "",
                summary_keywords,
            )
            summary_keywords = structured_keywords
        else:
            trusted_focus = canonical_focus_label(focus_label)
            should_project_focus = (
                not trusted_focus
                or focus_label_is_invalid(trusted_focus)
                or focus_label_is_broad(trusted_focus)
            )
            if should_project_focus:
                focus_label = project_focus_label_from_structured_signals(
                    structured_signals,
                    trusted_focus,
                    summary_keywords,
                ) or trusted_focus
            else:
                focus_label = trusted_focus
            if not summary_keywords:
                summary_keywords = structured_keywords
            elif len(summary_keywords) < 2 and structured_keywords:
                summary_keywords = clean_keyword_candidates(
                    [*summary_keywords, *structured_keywords],
                    limit=5,
                )
            if not focus_label and summary_keywords:
                primary_keyword_focus = canonical_focus_label(summary_keywords[0])
                if not focus_label_is_invalid(primary_keyword_focus):
                    focus_label = primary_keyword_focus
            if (should_project_focus or not focus_label) and not has_structured_signal and summary_keywords:
                focus_label = refine_focus_label(
                    job=display_job,
                    current_focus=focus_label,
                    keywords=summary_keywords,
                    summary=summary_item.get("summary", ""),
                    preview_lines=preview_lines,
                ) or focus_label
        focus_label, summary_keywords = rebalance_engineer_business_focus(
            role=resolved_role,
            job=display_job,
            structured_signals=structured_signals,
            focus_label=focus_label,
            keywords=summary_keywords,
            summary=summary_item.get("summary", ""),
            preview_lines=preview_lines,
        )
        if stage2_deploy_enabled:
            source_focus = canonical_focus_label(job.get("focus", ""))
            source_keywords = clean_keyword_candidates(job.get("skills") or [], limit=5)
            if source_focus and not focus_label_is_invalid(source_focus):
                focus_label = source_focus
            if source_keywords:
                summary_keywords = source_keywords
        display_summary = choose_display_summary(
            summary_item.get("summary", ""),
            preview_lines,
            summary_keywords,
            resolved_role,
            job.get("title", ""),
        )
        if summary_quality == "low":
            if focus_label:
                display_summary = choose_display_summary(
                    "",
                    preview_lines,
                    [focus_label, *summary_keywords],
                    resolved_role,
                    job.get("title", ""),
                ) or display_summary
            else:
                display_summary = ""
        if (
            summary_quality == "low"
            and not focus_label
            and not summary_keywords
            and is_generic_recruitment_title(job.get("title", ""))
        ):
            display_job = {
                **display_job,
                "detailBody": "",
                "tasks": [],
                "requirements": [],
                "preferred": [],
            }
            preview_lines = []
        row = {
            "id": job["id"],
            "company": job.get("company", ""),
            "title": job.get("title", ""),
            "sourceRole": raw_role,
            "displayRole": resolved_role,
            "role": resolved_role,
            "roleGroup": resolved_role,
            "rawRole": raw_role,
            "roleDisplay": raw_role,
            "roleGroupSignature": role_signature,
            "classifierRole": normalize_allowed_role(role_override.get("roleGroup", "")),
            "roleClassifierRole": normalize_allowed_role(role_override.get("roleGroup", "")),
            "roleClassifierReason": clean_text(role_override.get("reason", "")) or "",
            "roleClassifierConfidence": clean_text(role_override.get("confidence", "")) or "",
            "roleClassifierSource": clean_text(role_override.get("source", "")) or "",
            "serviceScopeSignature": compute_service_scope_signature(job),
            "serviceScopeAction": clean_text(override.get("action", "")) or "",
            "serviceScopeReason": clean_text(override.get("reason", "")) or "",
            "serviceScopeConfidence": clean_text(override.get("confidence", "")) or "",
            "serviceScopeMappedRole": mapped_role,
            "serviceScopeSource": clean_text(override.get("source", "")) or "",
            "stage2Role": raw_role if stage2_deploy_enabled else "",
            "stage2Focus": job.get("focus", "") if stage2_deploy_enabled else "",
            "stage2FocusAxes": job.get("focusAxes") or split_semantic_source_terms(job.get("focus", "")),
            "stage2SkillTerms": job.get("skills") or [],
            "stage2SummaryTags": job.get("summaryTags") or split_group_tags(job.get("groupSummary", "")),
            "experience": job.get("experience", ""),
            "summary": display_summary,
            "rawSummary": summary_item.get("summary", ""),
            "summaryQuality": summary_quality,
            "focusLabel": focus_label,
            "highlightKeywords": summary_keywords,
            "structuredSignals": structured_signals,
            "sectionSignalFacets": section_signal_facets,
            "hasSummary": bool(summary_item.get("summary")),
            "summarizedAt": summary_item.get("summarizedAt"),
            "model": summary_item.get("provider", {}).get("model", ""),
            "detailBody": display_job.get("detailBody", "") or "",
            "tasks": display_job.get("tasks") or [],
            "requirements": display_job.get("requirements") or [],
            "preferred": display_job.get("preferred") or [],
            "skills": job.get("skills") or [],
            "previewLines": preview_lines,
            "displaySourceKind": "sparse_recruitment" if sparse_row else "normal",
            "detailLineCount": build_detail_line_count(display_job),
            "groupSummary": job.get("groupSummary", ""),
            "groupTags": split_group_tags(job.get("groupSummary", "")),
            "source": job.get("source", ""),
            "jobUrl": job.get("jobUrl", ""),
            "sourceUrl": job.get("sourceUrl", ""),
            "lastSeenAt": job.get("lastSeenAt", ""),
            "firstSeenAt": job.get("firstSeenAt", ""),
            "active": job.get("active", False),
        }
        service_scope = explain_service_scope_row(row, override_items=override_items)
        row["serviceScopeIncluded"] = service_scope["included"]
        row["serviceScopeResolvedAction"] = service_scope["action"]
        rows.append(row)
    return rows


def build_company_profiles(rows: list[dict]) -> dict:
    grouped = {}
    for row in rows:
        company = row.get("company") or "미상 회사"
        grouped.setdefault(
            company,
            {
                "company": company,
                "postings": 0,
                "activePostings": 0,
                "usablePostings": 0,
                "roles": [],
                "focusLabels": [],
                "keywords": [],
                "sampleSummaries": [],
                "previewSignals": [],
                "signalTexts": [],
            },
        )
        profile = grouped[company]
        sparse_row = row.get("displaySourceKind") == "sparse_recruitment"
        profile["postings"] += 1
        if row.get("active"):
            profile["activePostings"] += 1
        add_unique_sample(profile["roles"], row.get("roleGroup", ""), limit=6)
        if row.get("summaryQuality") != "low":
            profile["usablePostings"] += 1
        if row.get("focusLabel"):
            add_unique_sample(profile["focusLabels"], row.get("focusLabel", ""), limit=5)
        for keyword in row.get("highlightKeywords", []):
            add_unique_sample(profile["keywords"], keyword, limit=8)
        for value in flatten_structured_signals(
            row.get("structuredSignals", {}),
            ["problemSignals", "domainSignals", "systemSignals", "dataSignals", "workflowSignals", "modelSignals"],
        ):
            add_unique_sample(profile["keywords"], value, limit=8)
        if row.get("summaryQuality") != "low":
            add_unique_sample(profile["sampleSummaries"], row.get("summary", ""), limit=4)
        signal_texts = [
            row.get("focusLabel", ""),
            *row.get("highlightKeywords", []),
            *flatten_structured_signals(
                row.get("structuredSignals", {}),
                ["problemSignals", "domainSignals", "systemSignals", "dataSignals", "workflowSignals", "modelSignals"],
            ),
            row.get("roleGroup", ""),
        ]
        if row.get("summaryQuality") != "low":
            signal_texts.append(row.get("summary", ""))
        profile["signalTexts"].extend(signal_texts)

    for company, profile in grouped.items():
        company_compact = canonical_text(company)
        keywords = [
            keyword
            for keyword in unique_non_generic(profile["focusLabels"] + profile["keywords"], limit=8)
            if canonical_text(keyword) != company_compact and canonical_text(keyword) not in company_compact
        ][:5]
        if not keywords:
            keywords = unique_non_generic(profile["roles"], limit=3)
        profile["keywords"] = keywords
        if keywords:
            profile["reason"] = f"{' · '.join(keywords[:3])} 중심 공고가 반복됩니다."
        elif profile["roles"]:
            profile["reason"] = f"{' · '.join(profile['roles'][:2])} 채용이 반복됩니다."
        else:
            profile["reason"] = "같은 회사 공고를 한 묶음으로 정리했습니다."
        profile["headline"] = keywords[0] if keywords else (profile["roles"][0] if profile["roles"] else "공고 묶음")
    return grouped


SIGNAL_STOPWORDS = {
    "인공지능",
    "ai",
    "엔지니어",
    "리서처",
    "인공지능엔지니어",
    "인공지능리서처",
    "데이터엔지니어",
    "데이터사이언티스트",
    "데이터분석가",
    "연구",
    "개발",
    "구축",
    "설계",
    "운영",
    "분석",
    "최적화",
    "서비스",
    "시스템",
    "플랫폼",
    "공고",
    "직무",
    "역할",
    "지원",
    "채용",
    "업무",
    "데이터",
    "모델",
    "기반",
    "활용",
    "구현",
    "담당",
    "기능",
    "성능",
    "경험",
    "프로젝트",
    "산업",
    "향상",
    "문제",
    "확장",
    "적용",
    "회사",
    "여러",
    "반복",
    "직원",
    "계약직",
    "사업단",
    "엔드",
    "기술",
    "스택",
    "경력",
    "엔지니어링",
    "사이언티스트",
    "개발자",
    "공고명",
    "가능성을",
    "거치도록",
    "고객사의",
    "위한",
    "또는",
    "학력",
    "학위",
    "학사",
    "석사",
    "박사",
    "사이언스",
    "학과",
    "유관학과",
    "전공",
    "필수",
    "우대",
    "기반",
    "관련",
    "대한",
    "통한",
    "분야",
    "이상",
    "가능",
    "제품",
    "서비스",
    "이상이신",
    "경험자",
    "가능자",
    "채용절차법",
    "상시채용",
    "경력무관",
    "계약직",
    "정규직",
    "모집",
    "채용",
    "모집요강",
    "인재채용",
    "기획자",
    "담당자",
    "광주지사",
    "과천",
    "지원하기",
    "우대합니다",
    "있습니다",
}

SERVICE_SCOPE_ALLOWED_ROLES = {
    "인공지능 엔지니어",
    "인공지능 리서처",
    "데이터 사이언티스트",
    "데이터 분석가",
}

SERVICE_SCOPE_EXCLUDED_TITLE_PATTERNS = [
    r"frontend|프론트엔드",
    r"backend|백엔드",
    r"web backend",
    r"full[- ]?stack|풀스택",
    r"devops",
    r"\bsre\b",
    r"product manager",
    r"product owner",
    r"technical product owner",
    r"project manager",
    r"\bpl\b",
    r"\bpm\b",
    r"operations manager",
    r"strategy manager",
    r"business developer",
    r"marketer|마케터",
    r"growth manager|growth lead",
    r"designer",
    r"qa engineer",
    r"qa engineering",
    r"verification engineer",
    r"design verification",
    r"service developer",
    r"process innovation",
    r"field application engineer",
    r"application engineer",
    r"solution architect",
    r"security engineer",
    r"soc design",
    r"technical operations",
    r"\bax manager\b",
    r"talent pool",
    r"recruitment",
    r"official website",
    r"recruiter",
    r"강사",
    r"멘토",
    r"전자정부",
    r"크로스 플랫폼",
    r"전문연구요원\s*\(r&d\)",
    r"전문연구요원 및 산업기능요원",
]

SERVICE_SCOPE_LOW_CONFIDENCE_TITLE_PATTERNS = [
    r"^ai engineer$",
    r"^software engineer intern(?:\s*\(.+\))?$",
]

SERVICE_SCOPE_REVIEW_TITLE_PATTERNS = [
    r"devops",
    r"full[- ]?stack|풀스택",
    r"frontend|프론트엔드",
    r"backend|백엔드",
    r"application engineer",
    r"solution architect",
]

SERVICE_SCOPE_STRONG_EXCLUDE_TITLE_PATTERNS = [
    r"product manager",
    r"product owner",
    r"project manager",
    r"\bpm\b",
    r"\bpl\b",
    r"business developer",
    r"marketer|마케터",
    r"operations manager",
    r"strategy manager",
    r"designer",
    r"qa engineer",
    r"qa engineering",
    r"verification engineer",
    r"soc design",
    r"recruiter",
    r"recruitment",
    r"official website",
    r"강사",
    r"process innovation",
]

SERVICE_SCOPE_ANALYST_FAMILY_INCLUDE_PATTERNS = [
    r"\bcrm\b",
    r"\bcx\b",
    r"\bpmo\b",
    r"growth",
    r"performance marketer",
    r"data analyst",
    r"analytics engineer",
    r"business analyst",
    r"business insight",
    r"user behavior",
    r"monetization analyst",
    r"fraud(?:\s*&\s*|\s+and\s+)?risk",
    r"데이터 분석\s*pm",
]

SERVICE_SCOPE_RECOVERABLE_AI_PATTERNS = [
    r"\bai\b",
    r"인공지능",
    r"머신러닝",
    r"\bml\b",
    r"딥러닝",
    r"\bllm\b",
    r"\brag\b",
    r"생성형",
    r"컴퓨터\s*비전",
    r"의료\s*ai",
    r"\bsamd\b",
    r"\bmlops\b",
]

SERVICE_SCOPE_RECOVERABLE_DEEPTECH_PATTERNS = [
    r"자율주행",
    r"로보틱스",
    r"\bnpu\b",
    r"\bsoc\b",
    r"반도체",
    r"\brtl\b",
    r"\bsdk\b",
    r"펌웨어",
    r"임베디드",
]

SERVICE_SCOPE_RECOVERABLE_DATA_PATTERNS = [
    r"데이터\s*분석",
    r"데이터\s*사이언스",
    r"\bdata\s*scien",
    r"\bdata\s*analy",
    r"\banalytics?\b",
    r"\ba/b\b",
    r"에이비\s*테스트",
    r"\bkpi\b",
    r"\bsql\b",
]

SERVICE_SCOPE_MODEL_EXCLUDE_STRONG_NON_SCOPE_PATTERNS = [
    r"product manager|product owner|head of product",
    r"\bpm\b|\bpo\b|\bpl\b",
    r"프로덕트|제품\s*관리",
    r"designer|ux/ui|디자이너|디자인\s*시스템|디자인\s*업무",
    r"영업|sales|세일즈|account executive|영업대표",
    r"브랜드\s*매니저|\bmd\b",
    r"정부지원사업|행정|연구지원|사업\s*운영",
    r"recruit|채용|강사|멘토",
    r"보안점검|모의해킹|취약점",
]

SERVICE_SCOPE_LOW_EVIDENCE_TITLE_PATTERNS = [
    r"^ai engineer$",
    r"전문연구요원",
    r"인재채용",
]


def row_is_in_service_scope(row: dict) -> bool:
    return explain_service_scope_row(row)["included"]


def service_scope_evidence_text(row: dict) -> str:
    values = [
        row.get("company", ""),
        row.get("title", ""),
        row.get("sourceRole", ""),
        row.get("rawRole", ""),
        row.get("roleDisplay", ""),
        row.get("roleGroup", ""),
        row.get("summary", ""),
        row.get("rawSummary", ""),
        row.get("focusLabel", ""),
        row.get("detailBody", ""),
        " ".join(row.get("highlightKeywords", []) or []),
        " ".join(row.get("previewLines", []) or []),
        " ".join(row.get("tasks", []) or []),
        " ".join(row.get("requirements", []) or []),
        " ".join(row.get("preferred", []) or []),
        " ".join(row.get("skills", []) or []),
        json.dumps(row.get("structuredSignals", {}) or {}, ensure_ascii=False),
        json.dumps(row.get("sectionSignalFacets", {}) or {}, ensure_ascii=False),
    ]
    return " ".join(clean_text(value) for value in values).lower()


def service_scope_decision_text(row: dict) -> str:
    values = [
        row.get("title", ""),
        row.get("focusLabel", ""),
        row.get("serviceScopeReason", ""),
        " ".join((row.get("highlightKeywords", []) or [])[:2]),
    ]
    return " ".join(clean_text(value) for value in values).lower()


def matches_service_scope_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def row_has_recoverable_service_scope_signal(row: dict) -> bool:
    text = service_scope_evidence_text(row)
    role = clean_text(row.get("rawRole", "") or row.get("roleGroup", ""))
    has_ai_signal = matches_service_scope_pattern(text, SERVICE_SCOPE_RECOVERABLE_AI_PATTERNS)
    has_deeptech_signal = matches_service_scope_pattern(text, SERVICE_SCOPE_RECOVERABLE_DEEPTECH_PATTERNS)
    has_data_signal = matches_service_scope_pattern(text, SERVICE_SCOPE_RECOVERABLE_DATA_PATTERNS)
    if has_ai_signal or has_deeptech_signal:
        return True
    return role in {"데이터 사이언티스트", "데이터 분석가"} and has_data_signal


def row_has_strong_non_scope_signal(row: dict) -> bool:
    return matches_service_scope_pattern(
        service_scope_decision_text(row),
        SERVICE_SCOPE_MODEL_EXCLUDE_STRONG_NON_SCOPE_PATTERNS,
    )


def model_exclude_should_be_recovered(row: dict, override: dict) -> bool:
    source = clean_text(override.get("source", "")).lower()
    if not source.startswith("service_scope_model"):
        return False
    if clean_text(override.get("action", "")).lower() != "exclude":
        return False
    if row_has_strong_non_scope_signal(row):
        return False
    if not row_has_recoverable_service_scope_signal(row):
        return False
    quality = clean_text(row.get("summaryQuality", "")).lower()
    if quality != "low":
        return True
    title = clean_text(row.get("title", "")).lower()
    return not matches_service_scope_pattern(title, SERVICE_SCOPE_LOW_EVIDENCE_TITLE_PATTERNS)


def load_service_scope_override_store() -> dict:
    if not SERVICE_SCOPE_OVERRIDE_PATH.exists():
        return {"updatedAt": None, "items": {}}
    try:
        data = json.loads(SERVICE_SCOPE_OVERRIDE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"updatedAt": None, "items": {}}
    items = data.get("items", {})
    return {
        "updatedAt": data.get("updatedAt"),
        "items": items if isinstance(items, dict) else {},
    }


def save_service_scope_override_store(store: dict) -> None:
    SERVICE_SCOPE_OVERRIDE_PATH.parent.mkdir(parents=True, exist_ok=True)
    SERVICE_SCOPE_OVERRIDE_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_role_group_override_store() -> dict:
    if not ROLE_GROUP_OVERRIDE_PATH.exists():
        return {"updatedAt": None, "items": {}}
    try:
        data = json.loads(ROLE_GROUP_OVERRIDE_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"updatedAt": None, "items": {}}
    items = data.get("items", {})
    return {
        "updatedAt": data.get("updatedAt"),
        "items": items if isinstance(items, dict) else {},
    }


def save_role_group_override_store(store: dict) -> None:
    ROLE_GROUP_OVERRIDE_PATH.parent.mkdir(parents=True, exist_ok=True)
    ROLE_GROUP_OVERRIDE_PATH.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def resolve_role_group_override(record: dict, summary_item: dict | None = None, override_items: dict | None = None) -> dict:
    override_items = override_items if override_items is not None else load_role_group_override_store().get("items", {})
    record_id = record.get("id", "")
    if not record_id:
        return {}
    override = override_items.get(record_id, {})
    if not isinstance(override, dict):
        return {}
    role_group = normalize_allowed_role(override.get("roleGroup", ""))
    if not role_group:
        return {}
    expected_signature = clean_text(override.get("signature", ""))
    if expected_signature:
        actual_signature = (
            clean_text(record.get("roleGroupSignature", ""))
            or compute_role_group_signature(record, summary_item)
        )
        if expected_signature != actual_signature:
            return {}
    source = clean_text(override.get("source", "")).lower()
    return override


def resolve_service_scope_override(record: dict, override_items: dict | None = None) -> dict:
    override_items = override_items if override_items is not None else load_service_scope_override_store().get("items", {})
    record_id = record.get("id", "")
    if not record_id:
        return {}
    override = override_items.get(record_id, {})
    if not isinstance(override, dict):
        return {}
    action = clean_text(override.get("action", "")).lower()
    if action not in {"include", "review", "exclude"}:
        return {}
    expected_signature = clean_text(override.get("signature", ""))
    if expected_signature:
        actual_signature = clean_text(record.get("serviceScopeSignature", "")) or compute_service_scope_signature(record)
        if expected_signature != actual_signature:
            return {}
    source = clean_text(override.get("source", "")).lower()
    confidence = clean_text(override.get("confidence", "")).lower()
    if source.startswith("service_scope_model") and confidence == "low":
        return {}
    return override


def explain_service_scope_row(row: dict, override_items: dict | None = None) -> dict:
    title = clean_text(row.get("title", "")).lower()
    role = clean_text(
        row.get("sourceRole", "")
        or row.get("rawRole", "")
        or row.get("roleDisplay", "")
        or row.get("roleGroup", "")
        or row.get("role", "")
    )
    quality = clean_text(row.get("summaryQuality", "")).lower()
    override_items = override_items if override_items is not None else load_service_scope_override_store().get("items", {})
    override = resolve_service_scope_override(row, override_items=override_items)

    override_action = clean_text(override.get("action", "")).lower()
    if override_action == "include":
        return {
            "included": True,
            "action": "include",
            "reasons": [
                {
                    "type": "override",
                    "pattern": override.get("source", "manual"),
                    "label": f"override:{override.get('source', 'manual')}",
                }
            ],
        }
    if override_action == "review":
        return {
            "included": False,
            "action": "review",
            "reasons": [
                {
                    "type": "override",
                    "pattern": override.get("source", "manual"),
                    "label": f"override:{override.get('source', 'manual')}",
                }
            ],
        }
    if override_action == "exclude":
        if model_exclude_should_be_recovered(row, override):
            return {
                "included": True,
                "action": "include",
                "reasons": [
                    {
                        "type": "override_guard",
                        "pattern": override.get("source", "service_scope_model"),
                        "label": "override_guard:model_exclude_recovered",
                    }
                ],
            }
        return {
            "included": False,
            "action": "exclude",
            "reasons": [
                {
                    "type": "override",
                    "pattern": override.get("source", "manual"),
                    "label": f"override:{override.get('source', 'manual')}",
                }
            ],
        }

    analyst_family_include = (
        role == "데이터 분석가"
        and any(re.search(pattern, title) for pattern in SERVICE_SCOPE_ANALYST_FAMILY_INCLUDE_PATTERNS)
    )
    if analyst_family_include:
        return {
            "included": True,
            "action": "include",
            "reasons": [
                {
                    "type": "analyst_family",
                    "pattern": "analyst_family",
                    "label": "analyst_family:data_analyst",
                }
            ],
        }

    reasons = []

    if role not in SERVICE_SCOPE_ALLOWED_ROLES:
        reasons.append({"type": "role", "pattern": role or "empty", "label": f"role:{role or 'empty'}"})

    matched_excluded = [
        pattern for pattern in SERVICE_SCOPE_EXCLUDED_TITLE_PATTERNS if re.search(pattern, title)
    ]
    reasons.extend(
        {"type": "pattern", "pattern": pattern, "label": f"pattern:{pattern}"}
        for pattern in matched_excluded
    )

    matched_low_title = []
    if quality == "low":
        matched_low_title = [
            pattern for pattern in SERVICE_SCOPE_LOW_CONFIDENCE_TITLE_PATTERNS if re.search(pattern, title)
        ]
        reasons.extend(
            {"type": "low_title", "pattern": pattern, "label": f"low_title:{pattern}"}
            for pattern in matched_low_title
        )

    included = not reasons
    action = "include"
    if not included:
        review_candidate = (
            quality in {"high", "medium"}
            and any(re.search(pattern, title) for pattern in SERVICE_SCOPE_REVIEW_TITLE_PATTERNS)
            and not any(re.search(pattern, title) for pattern in SERVICE_SCOPE_STRONG_EXCLUDE_TITLE_PATTERNS)
            and not matched_low_title
        )
        action = "review" if review_candidate else "exclude"

    return {
        "included": included,
        "action": action,
        "reasons": reasons,
    }


def filter_service_scope_rows(rows: list[dict]) -> tuple[list[dict], list[dict]]:
    override_items = load_service_scope_override_store().get("items", {})
    filtered = []
    excluded = []
    for row in rows:
        if explain_service_scope_row(row, override_items=override_items)["included"]:
            filtered.append(row)
        else:
            excluded.append(row)
    return filtered, excluded
SIGNAL_BAD_SUFFIXES = (
    "에서",
    "으로",
    "에게",
    "적인",
    "하며",
    "하고",
    "하는",
    "하기",
    "하여",
    "한다",
    "합니다",
    "위한",
    "통한",
    "처럼",
    "중심",
    "기반",
    "문제로",
    "향상을",
)


def signal_terms_from_text(value: str, company: str) -> list[str]:
    company_compact = canonical_text(company)
    company_tokens = {
        canonical_text(part)
        for part in re.findall(r"[A-Za-z][A-Za-z0-9]+|[가-힣]{2,}", company or "")
    }
    terms = []
    for piece in re.findall(r"[A-Za-z][A-Za-z0-9+#./-]{1,}|[가-힣]{2,}", value or ""):
        normalized = clean_text(piece)
        compact = canonical_text(normalized)
        if (
            not compact
            or compact in SIGNAL_STOPWORDS
            or compact == company_compact
            or compact in company_tokens
            or len(compact) < 2
            or compact.endswith(SIGNAL_BAD_SUFFIXES)
        ):
            continue
        terms.append(normalized.lower() if re.search(r"[A-Za-z]", normalized) else normalized)
    return terms


def row_model_signal_terms(row: dict, *, include_role: bool = True, limit: int = 18) -> list[str]:
    structured_signals = row.get("structuredSignals", {}) if isinstance(row.get("structuredSignals", {}), dict) else {}
    values = [
        row.get("focusLabel", ""),
        *(row.get("highlightKeywords", []) or []),
        *flatten_structured_signals(
            structured_signals,
            ["problemSignals", "domainSignals", "dataSignals", "systemSignals", "workflowSignals", "modelSignals"],
        ),
    ]
    if include_role:
        values.extend([row.get("role", ""), row.get("roleGroup", "")])
    return unique_non_generic(values, limit=limit)


def build_company_signal_vectors(rows: list[dict], company_profiles: dict) -> dict:
    doc_freq = {}
    raw_vectors = {}

    for company, profile in company_profiles.items():
        weights = {}
        company_rows = [row for row in rows if row.get("company") == company]
        for row in company_rows:
            keyword_weight = 3.4 if row.get("summaryQuality") != "low" else 2.2
            for term in row_model_signal_terms(row, include_role=False, limit=18):
                weights[term] = weights.get(term, 0) + keyword_weight
            role_term = clean_text(row.get("roleGroup", ""))
            if role_term:
                weights[role_term] = weights.get(role_term, 0) + 0.25

        if not weights:
            for keyword in profile.get("keywords", []):
                cleaned = clean_text(keyword)
                if cleaned:
                    weights[cleaned] = weights.get(cleaned, 0) + 0.6

        raw_vectors[company] = weights
        for term in weights:
            doc_freq[term] = doc_freq.get(term, 0) + 1

    total_companies = max(len(company_profiles), 1)
    vectors = {}
    for company, weights in raw_vectors.items():
        scored = {}
        for term, weight in weights.items():
            idf = 1.0 + (total_companies / max(doc_freq.get(term, 1), 1))
            scored[term] = round(weight * idf, 3)
        vectors[company] = dict(
            sorted(
                scored.items(),
                key=lambda item: (-item[1], item[0]),
            )[:10]
        )
    return vectors


def vector_similarity(left: dict, right: dict) -> float:
    if not left or not right:
        return 0.0
    left_keys = set(left)
    right_keys = set(right)
    union = left_keys | right_keys
    if not union:
        return 0.0
    overlap = sum(min(left.get(term, 0.0), right.get(term, 0.0)) for term in left_keys & right_keys)
    total = sum(max(left.get(term, 0.0), right.get(term, 0.0)) for term in union)
    return overlap / total if total else 0.0


def merge_cluster_vectors(items: list[dict]) -> dict:
    merged = {}
    for item in items:
        for term, score in item.items():
            merged[term] = merged.get(term, 0.0) + score
    count = max(len(items), 1)
    averaged = {term: round(score / count, 3) for term, score in merged.items()}
    return dict(sorted(averaged.items(), key=lambda entry: (-entry[1], entry[0]))[:12])


DISPLAY_CLUSTER_THEMES = [
    {
        "id": "edge",
        "tone": "cluster-a",
        "label": "추론 최적화 · 컴퓨팅",
        "description": "온디바이스 추론과 시스템 최적화가 중심인 회사군",
        "tokens": {"엔피유", "npu", "onnx", "엔피아이알", "포팅", "컴파일러", "컴파일", "컴퓨팅", "최적화", "배포"},
    },
    {
        "id": "health",
        "tone": "cluster-b",
        "label": "헬스케어 · 진단 지원",
        "description": "의료 해석과 환자 모니터링 성격이 강한 회사군",
        "tokens": {"헬스케어", "의료", "환자", "진료", "모니터링", "영상", "병원"},
    },
    {
        "id": "data",
        "tone": "cluster-c",
        "label": "데이터 분석 · 실험 운영",
        "description": "지표 분석과 실험 설계 비중이 높은 회사군",
        "tokens": {"데이터분석", "데이터 분석", "머신러닝", "지표", "실험", "유저", "growth", "crm", "분석"},
    },
    {
        "id": "industrial",
        "tone": "cluster-d",
        "label": "산업 현장 · 설계 자동화",
        "description": "제조·설계·현장 자동화 성격이 보이는 회사군",
        "tokens": {"cad", "씨에이디", "제조", "자율제조", "주차", "공장", "로봇", "설계", "산업"},
    },
    {
        "id": "service",
        "tone": "cluster-e",
        "label": "AI 제품화 · 서비스 적용",
        "description": "언어·추천·검색 기반 제품 적용이 중심인 회사군",
        "tokens": {"nlp", "엘엘엠", "llm", "rag", "검색", "추천", "에이전트", "멀티모달", "금융", "교육"},
    },
    {
        "id": "enterprise",
        "tone": "cluster-f",
        "label": "기업 업무 · 솔루션 구축",
        "description": "고객사 환경에 맞춘 솔루션 구축이 많은 회사군",
        "tokens": {"고객", "고객사", "솔루션", "엔터프라이즈", "업무", "자동화", "플랫폼"},
    },
]


def resolve_cluster_copy(keywords: list[str]) -> tuple[str, str]:
    compact_keywords = {canonical_text(keyword) for keyword in keywords}
    best_theme = None
    best_score = -1
    for theme in DISPLAY_CLUSTER_THEMES:
        score = 0
        for token in theme["tokens"]:
            token_compact = canonical_text(token)
            if token_compact in compact_keywords:
                score += 3
            elif any(token_compact in keyword or keyword in token_compact for keyword in compact_keywords):
                score += 1
        if score > best_score:
            best_score = score
            best_theme = theme
    if best_theme and best_score > 0:
        return best_theme["label"], best_theme["description"]
    return "AI 제품화 · 서비스 적용", "제품 안에서 AI 기능을 구현하고 다듬는 회사군"


def build_dynamic_cluster_payload(rows: list[dict], company_profiles: dict) -> list[dict]:
    if not company_profiles:
        return []

    buckets = {
        theme["id"]: {
            "theme": theme,
            "companies": [],
            "keywords": [],
            "postings": 0,
        }
        for theme in DISPLAY_CLUSTER_THEMES
    }

    for company, profile in sorted(company_profiles.items()):
        keyword_terms = [canonical_text(keyword) for keyword in profile.get("keywords", [])]
        signal_terms = [canonical_text(value) for value in profile.get("signalTexts", [])]

        best_theme = None
        best_score = -1
        for theme in DISPLAY_CLUSTER_THEMES:
            score = 0
            for token in theme["tokens"]:
                compact_token = canonical_text(token)
                score += sum(3 for keyword in keyword_terms if compact_token and compact_token in keyword)
                score += sum(1 for value in signal_terms if compact_token and compact_token in value)
            if score > best_score:
                best_score = score
                best_theme = theme

        if not best_theme or best_score <= 0:
            best_theme = next(theme for theme in DISPLAY_CLUSTER_THEMES if theme["id"] == "service")

        bucket = buckets[best_theme["id"]]
        bucket["companies"].append(company)
        bucket["postings"] += profile["postings"]
        for keyword in profile.get("keywords", []):
            if keyword not in bucket["keywords"]:
                bucket["keywords"].append(keyword)

    ordered_buckets = [
        bucket
        for bucket in sorted(
            buckets.values(),
            key=lambda bucket: (-bucket["postings"], bucket["theme"]["label"]),
        )
        if bucket["companies"]
    ]

    payload = []
    for index, bucket in enumerate(ordered_buckets, start=1):
        keywords = unique_non_generic(bucket["keywords"], limit=6)
        payload.append(
            {
                "id": f"cluster-{index}",
                "tone": CLUSTER_TONES[(index - 1) % len(CLUSTER_TONES)],
                "label": bucket["theme"]["label"],
                "description": bucket["theme"]["description"],
                "reason": (
                    f"{' · '.join(keywords[:4])} 같은 신호가 여러 회사에서 반복됩니다."
                    if keywords
                    else "공고 요약과 핵심 신호가 비슷한 회사들을 함께 묶었습니다."
                ),
                "keywords": keywords,
                "companies": sorted(bucket["companies"]),
            }
        )
    return payload


def build_cluster_label_seeds(clusters: list[dict], company_profiles: dict) -> list[dict]:
    seeds = []
    for cluster in clusters:
        sample_companies = cluster.get("companies", [])[:6]
        sample_summaries = []
        for company in sample_companies:
            for summary in company_profiles.get(company, {}).get("sampleSummaries", [])[:2]:
                add_unique_sample(sample_summaries, summary, limit=4)
        seeds.append(
            {
                "id": cluster["id"],
                "label": cluster["label"],
                "description": cluster["description"],
                "reason": cluster["reason"],
                "keywords": cluster.get("keywords", [])[:6],
                "companies": cluster.get("companies", []),
                "sampleCompanies": sample_companies,
                "sampleSummaries": sample_summaries,
            }
        )
    return seeds


def posting_signal_terms(row: dict) -> list[str]:
    return row_model_signal_terms(row, include_role=True, limit=20)


def assign_posting_clusters(rows: list[dict]) -> list[dict]:
    theme_map = {theme["id"]: theme for theme in DISPLAY_CLUSTER_THEMES}
    default_theme = theme_map["service"]
    cluster_rows = {theme["id"]: [] for theme in DISPLAY_CLUSTER_THEMES}

    for row in rows:
        row_terms = posting_signal_terms(row)
        keyword_terms = {
            canonical_text(value)
            for value in [row.get("focusLabel", ""), *row.get("highlightKeywords", [])]
            if clean_text(value)
        }

        best_theme = default_theme
        best_score = -1
        for theme in DISPLAY_CLUSTER_THEMES:
            score = 0
            for token in theme["tokens"]:
                compact = canonical_text(token)
                score += sum(3 for term in keyword_terms if compact and (compact in term or term in compact))
                score += sum(1 for term in row_terms if compact and (compact in canonical_text(term) or canonical_text(term) in compact))
            if theme["id"] == "edge" and any(term in keyword_terms for term in {canonical_text("엔피유"), canonical_text("엔피아이알")}):
                score += 4
            if theme["id"] == "health" and any(term in keyword_terms for term in {canonical_text("의료"), canonical_text("헬스케어")}):
                score += 4
            if theme["id"] == "data" and row.get("roleGroup") in {"데이터 분석가", "데이터 사이언티스트"}:
                score += 4
            if score > best_score:
                best_score = score
                best_theme = theme

        row["clusterId"] = best_theme["id"]
        row["clusterTone"] = best_theme["tone"]
        row["clusterLabel"] = best_theme["label"]
        row["clusterDescription"] = best_theme["description"]
        cluster_rows[best_theme["id"]].append(row)

    clusters = []
    for theme in DISPLAY_CLUSTER_THEMES:
        items = cluster_rows[theme["id"]]
        if not items:
            continue
        keywords = unique_non_generic(
            [
                value
                for row in items
                for value in [row.get("focusLabel", ""), *row.get("highlightKeywords", [])]
            ],
            limit=6,
        )
        if not keywords:
            keywords = unique_non_generic(
                [term for row in items for term in posting_signal_terms(row)],
                limit=6,
            )
        cluster_reason = (
            f"{' · '.join(keywords[:4])} 같은 신호가 여러 공고에서 반복됩니다."
            if keywords
            else "유사한 역할과 업무 신호를 가진 공고들을 함께 묶었습니다."
        )
        for row in items:
            row["clusterKeywords"] = keywords
            row["clusterReason"] = cluster_reason
        clusters.append(
            {
                "id": theme["id"],
                "tone": theme["tone"],
                "label": theme["label"],
                "description": theme["description"],
                "reason": cluster_reason,
                "count": len(items),
                "companyCount": len({row.get("company") for row in items if row.get("company")}),
                "keywords": keywords,
            }
        )
    return clusters


def fallback_cluster_payload(company_profiles: dict) -> list[dict]:
    companies = sorted(company_profiles)
    if not companies:
        return []
    return [
        {
            "id": "cluster-1",
            "tone": CLUSTER_TONES[0],
            "label": "공고 패턴 검토",
            "description": "회사별 채용 신호를 다시 정리한 묶음",
            "reason": "AI 기반 회사군 분류를 준비하는 동안 같은 회사 공고를 먼저 모았습니다.",
            "keywords": unique_non_generic(
                [keyword for company in companies for keyword in company_profiles[company]["keywords"]],
                limit=6,
            ),
            "companies": companies,
        }
    ]


def load_cluster_payload(rows: list[dict], company_profiles: dict) -> list[dict]:
    store = load_company_cluster_store()
    raw_clusters = store.get("clusters", [])
    if not isinstance(raw_clusters, list) or len(raw_clusters) <= 1:
        return build_dynamic_cluster_payload(rows, company_profiles) or fallback_cluster_payload(company_profiles)

    valid_companies = set(company_profiles)
    clusters = []
    assigned = set()
    for index, cluster in enumerate(raw_clusters):
        if not isinstance(cluster, dict):
            continue
        companies = []
        for company in cluster.get("companies", []) if isinstance(cluster.get("companies", []), list) else []:
            cleaned = clean_text(company)
            if not cleaned or cleaned not in valid_companies or cleaned in assigned or cleaned in companies:
                continue
            companies.append(cleaned)
            assigned.add(cleaned)
        if not companies:
            continue
        clusters.append(
            {
                "id": clean_text(cluster.get("id", "")) or f"cluster-{len(clusters) + 1}",
                "tone": CLUSTER_TONES[len(clusters) % len(CLUSTER_TONES)],
                "label": clean_text(cluster.get("label", "")) or f"회사군 {len(clusters) + 1}",
                "description": clean_text(cluster.get("description", "")) or "반복되는 공고 패턴을 가진 회사 묶음",
                "reason": clean_text(cluster.get("reason", "")) or "유사한 공고 신호가 반복되어 함께 묶였습니다.",
                "keywords": unique_non_generic(cluster.get("keywords", []), limit=6),
                "companies": companies,
            }
        )

    missing = [company for company in sorted(valid_companies) if company not in assigned]
    if missing:
        if not clusters:
            return build_dynamic_cluster_payload(rows, company_profiles) or fallback_cluster_payload(company_profiles)
        clusters[0]["companies"].extend(missing)
        for company in missing:
            if company_profiles.get(company):
                for keyword in company_profiles[company]["keywords"]:
                    if keyword not in clusters[0]["keywords"] and len(clusters[0]["keywords"]) < 6:
                        clusters[0]["keywords"].append(keyword)
    return clusters


def build_cluster_lookup(rows: list[dict], company_profiles: dict) -> tuple[list[dict], dict]:
    clusters = load_cluster_payload(rows, company_profiles)
    company_map = {}
    for cluster in clusters:
        for company in cluster.get("companies", []):
            company_map[company] = cluster
    return clusters, company_map


def build_cluster_summaries_from_payload(clusters: list[dict], company_profiles: dict) -> list[dict]:
    items = []
    for cluster in clusters:
        companies = [company for company in cluster.get("companies", []) if company in company_profiles]
        if not companies:
            continue
        posting_count = sum(company_profiles[company]["postings"] for company in companies)
        keywords = unique_non_generic(
            cluster.get("keywords", [])
            + [keyword for company in companies for keyword in company_profiles[company]["keywords"]],
            limit=6,
        )
        items.append(
            {
                "id": cluster["id"],
                "tone": cluster["tone"],
                "label": cluster["label"],
                "description": cluster["description"],
                "reason": cluster["reason"],
                "count": posting_count,
                "companyCount": len(companies),
                "keywords": keywords,
            }
        )
    return items


def tone_for_keyword(value: str) -> str | None:
    normalized = clean_text(value).lower()
    if any(term in normalized for term in AI_TERMS):
        return "tone-ai"
    if any(term in normalized for term in DATA_TERMS):
        return "tone-data"
    if any(term in normalized for term in DOMAIN_TERMS):
        return "tone-domain"
    if any(term in normalized for term in ANALYSIS_TERMS):
        return "tone-analysis"
    return None


def tone_for_text(value: str) -> str | None:
    normalized = clean_text(value).lower()
    if any(term in normalized for term in AI_TERMS):
        return "tone-ai"
    if any(term in normalized for term in DATA_TERMS):
        return "tone-data"
    if any(term in normalized for term in DOMAIN_TERMS):
        return "tone-domain"
    if any(term in normalized for term in ANALYSIS_TERMS):
        return "tone-analysis"
    return None


def add_unique_sample(values: list[str], value: str, limit: int = 3) -> None:
    cleaned = clean_text(value)
    if not cleaned or cleaned in values or len(values) >= limit:
        return
    values.append(cleaned)


def build_tone_legend_seeds(rows: list[dict]) -> list[dict]:
    buckets = {
        tone: {
            "tone": tone,
            "label": TONE_META[tone]["label"],
            "count": 0,
            "keywordCounts": {},
            "samples": [],
        }
        for tone in TONE_ORDER
    }

    for row in rows:
        tone_hits = set()
        keywords = row.get("highlightKeywords", [])

        for keyword in keywords:
            tone = tone_for_keyword(keyword)
            if not tone:
                continue
            bucket = buckets[tone]
            bucket["keywordCounts"][keyword] = bucket["keywordCounts"].get(keyword, 0) + 1
            tone_hits.add(tone)

        if not tone_hits:
            fallback_tone = tone_for_text(
                " ".join(
                    [
                        row.get("role", ""),
                        row.get("summary", ""),
                        " ".join(row.get("previewLines", [])),
                    ]
                )
            )
            if fallback_tone:
                tone_hits.add(fallback_tone)

        for tone in tone_hits:
            bucket = buckets[tone]
            bucket["count"] += 1
            add_unique_sample(bucket["samples"], row.get("summary", ""))
            for line in row.get("previewLines", []):
                add_unique_sample(bucket["samples"], line)

    seeds = []
    for tone in TONE_ORDER:
        bucket = buckets[tone]
        top_keywords = sorted(
            bucket["keywordCounts"].items(),
            key=lambda item: (-item[1], item[0]),
        )
        seeds.append(
            {
                "tone": tone,
                "label": bucket["label"],
                "count": bucket["count"],
                "keywords": [keyword for keyword, _count in top_keywords[:5]],
                "samples": bucket["samples"][:3],
            }
        )
    return seeds


def fallback_tone_description(seed: dict) -> str:
    keywords = seed.get("keywords", [])
    if keywords:
        return f"{', '.join(keywords[:3])} 중심의 공고 신호를 모아 보여줍니다."
    return "이 색상군에 해당하는 공고 신호를 모아 보여줍니다."


def unique_non_generic(values: list[str], limit: int = 5) -> list[str]:
    generic_tokens = {
        canonical_text("인공지능"),
        canonical_text("ai"),
        canonical_text("엔지니어"),
        canonical_text("리서처"),
        canonical_text("모델"),
        canonical_text("개발"),
        canonical_text("연구"),
        canonical_text("분석"),
        canonical_text("데이터"),
        canonical_text("구축"),
        canonical_text("설계"),
        canonical_text("운영"),
        canonical_text("최적화"),
        canonical_text("서비스"),
        canonical_text("인공지능 엔지니어"),
        canonical_text("인공지능 리서처"),
        canonical_text("데이터 엔지니어"),
        canonical_text("데이터 사이언티스트"),
        canonical_text("데이터 분석가"),
        canonical_text("위한"),
        canonical_text("또는"),
        canonical_text("학력"),
        canonical_text("학위"),
        canonical_text("학사"),
        canonical_text("석사"),
        canonical_text("박사"),
        canonical_text("사이언스"),
        canonical_text("학과"),
        canonical_text("유관학과"),
        canonical_text("전공"),
        canonical_text("필수"),
        canonical_text("우대"),
        canonical_text("기반"),
        canonical_text("관련"),
        canonical_text("제품"),
        canonical_text("서비스"),
        canonical_text("이상이신"),
        canonical_text("경험자"),
        canonical_text("가능자"),
        canonical_text("채용절차법"),
        canonical_text("상시채용"),
        canonical_text("경력무관"),
        canonical_text("계약직"),
        canonical_text("정규직"),
        canonical_text("모집"),
        canonical_text("채용"),
        canonical_text("모집요강"),
        canonical_text("인재채용"),
        canonical_text("기획자"),
        canonical_text("담당자"),
        canonical_text("광주지사"),
        canonical_text("과천"),
        canonical_text("지원하기"),
        canonical_text("우대합니다"),
        canonical_text("있습니다"),
    }
    result = []
    for value in values:
        cleaned = clean_text(value)
        compact = canonical_text(cleaned)
        if (
            not cleaned
            or not compact
            or compact in generic_tokens
            or compact.endswith(SIGNAL_BAD_SUFFIXES)
            or cleaned in result
        ):
            continue
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def company_cluster_fallback(roles: list[str]) -> dict:
    joined = " ".join(roles)
    if "데이터 분석가" in joined or "데이터 사이언티스트" in joined:
        schema = next(schema for schema in CLUSTER_SCHEMAS if schema["id"] == "cluster-data")
    else:
        schema = next(schema for schema in CLUSTER_SCHEMAS if schema["id"] == "cluster-model")
    return {
        "id": schema["id"],
        "tone": schema["tone"],
        "label": schema["label"],
        "description": schema["description"],
        "keywords": [],
        "reason": "같은 회사 안에서 반복되는 역할과 업무 신호를 기준으로 묶었습니다.",
    }


def build_company_cluster_map(rows: list[dict]) -> dict:
    grouped = {}
    for row in rows:
        company = row.get("company") or "미상 회사"
        grouped.setdefault(
            company,
            {
                "texts": [],
                "roles": [],
                "keywords": [],
            },
        )
        profile = grouped[company]
        profile["texts"].extend(
            [
                row.get("role", ""),
                row.get("summary", ""),
                row.get("groupSummary", ""),
                *row_model_signal_terms(row, include_role=False, limit=12),
            ]
        )
        profile["roles"].append(row.get("roleGroup", ""))
        profile["keywords"].extend(row_model_signal_terms(row, include_role=False, limit=10))

    result = {}
    for company, profile in grouped.items():
        text_blob = " ".join(clean_text(value).lower() for value in profile["texts"] if clean_text(value))
        scored = []
        for schema in CLUSTER_SCHEMAS:
            matches = {}
            score = 0
            for token in schema["tokens"]:
                count = text_blob.count(token.lower())
                if count:
                    matches[token] = count
                    score += count * 2
            if schema["id"] == "cluster-data" and any("데이터" in role for role in profile["roles"]):
                score += 4
            if schema["id"] == "cluster-edge" and any("검증" in value or "최적화" in value for value in profile["texts"]):
                score += 3
            if schema["id"] == "cluster-platform" and any("인프라" in value or "서빙" in value for value in profile["texts"]):
                score += 3
            if schema["id"] == "cluster-model" and any("리서처" in role for role in profile["roles"]):
                score += 2
            scored.append((score, schema, matches))

        best_score, best_schema, best_matches = max(scored, key=lambda item: item[0])
        if best_score <= 0:
            best_schema = company_cluster_fallback(profile["roles"])
            best_matches = {}

        keywords = unique_non_generic(
            [token for token, _count in sorted(best_matches.items(), key=lambda item: (-item[1], item[0]))]
            + profile["keywords"],
            limit=5,
        )
        reason = (
            f"{' · '.join(keywords[:4])} 신호가 여러 공고에서 반복됩니다."
            if keywords
            else "같은 회사 안에서 반복되는 역할과 업무 신호를 기준으로 묶었습니다."
        )
        result[company] = {
            "id": best_schema["id"],
            "tone": best_schema["tone"],
            "label": best_schema["label"],
            "description": best_schema["description"],
            "keywords": keywords,
            "reason": reason,
        }
    return result


def build_cluster_summaries(rows: list[dict], company_clusters: dict) -> list[dict]:
    summaries = []
    for schema in CLUSTER_SCHEMAS:
        cluster_rows = [row for row in rows if row.get("clusterId") == schema["id"]]
        if not cluster_rows:
            continue
        companies = sorted({row["company"] for row in cluster_rows if row.get("company")})
        keywords = unique_non_generic(
            [
                keyword
                for company in companies
                for keyword in company_clusters.get(company, {}).get("keywords", [])
            ],
            limit=6,
        )
        summaries.append(
            {
                "id": schema["id"],
                "tone": schema["tone"],
                "label": schema["label"],
                "description": schema["description"],
                "reason": (
                    f"{' · '.join(keywords[:4])} 같은 신호가 여러 회사에서 반복됩니다."
                    if keywords
                    else "반복되는 역할과 업무 신호를 기준으로 같은 묶음으로 정리했습니다."
                ),
                "count": len(cluster_rows),
                "companyCount": len(companies),
                "keywords": keywords,
            }
        )
    return summaries


def build_tone_legend(rows: list[dict]) -> list[dict]:
    seeds = build_tone_legend_seeds(rows)
    stored_items = load_tone_legend_store().get("items", {})

    legend = []
    for seed in seeds:
        stored = stored_items.get(seed["tone"], {})
        legend.append(
            {
                "tone": seed["tone"],
                "label": seed["label"],
                "description": stored.get("description") or fallback_tone_description(seed),
                "keywords": seed["keywords"],
                "count": seed["count"],
                "model": stored.get("provider", {}).get("model", ""),
            }
        )
    return legend


def base_row_order_key(row: dict) -> tuple:
    return (
        0 if row.get("active") else 1,
        role_sort_key(row.get("roleGroup", "")),
        -parse_dt(row.get("lastSeenAt", "")),
        clean_text(row.get("company", "")).lower(),
        clean_text(row.get("title", "")).lower(),
    )


def row_connection_signals(row: dict) -> dict[str, dict]:
    weighted_values = []
    structured_signals = row.get("structuredSignals", {})
    weighted_values.extend(
        (value, 7)
        for value in flatten_structured_signals(structured_signals, ["problemSignals"])[:5]
    )
    weighted_values.extend(
        (value, 6)
        for value in flatten_structured_signals(structured_signals, ["domainSignals", "dataSignals"])[:5]
    )
    weighted_values.extend(
        (value, 5)
        for value in flatten_structured_signals(structured_signals, ["systemSignals", "workflowSignals", "modelSignals"])[:6]
    )
    weighted_values.extend((keyword, 6) for keyword in row.get("highlightKeywords", [])[:6])
    weighted_values.append((row.get("focusLabel", ""), 5))
    weighted_values.append((row.get("role", ""), 4))
    weighted_values.append((row.get("roleGroup", ""), 4))

    signals = {}
    for value, weight in weighted_values:
        cleaned = clean_text(value)
        compact = canonical_text(cleaned)
        if (
            not cleaned
            or not compact
            or compact.endswith(SIGNAL_BAD_SUFFIXES)
            or cleaned not in unique_non_generic([cleaned], limit=1)
        ):
            continue
        existing = signals.get(compact)
        if not existing or weight > existing["weight"]:
            signals[compact] = {"label": cleaned, "weight": weight}

    return signals


def row_similarity(left: dict, right: dict, signal_cache: dict[str, dict]) -> float:
    left_signals = signal_cache.get(left["id"], {})
    right_signals = signal_cache.get(right["id"], {})
    score = 0.0

    for key in set(left_signals) & set(right_signals):
        score += min(left_signals[key]["weight"], right_signals[key]["weight"])

    if clean_text(left.get("focusLabel", "")) and clean_text(left.get("focusLabel", "")) == clean_text(
        right.get("focusLabel", "")
    ):
        score += 4

    if clean_text(left.get("role", "")) and clean_text(left.get("role", "")) == clean_text(
        right.get("role", "")
    ):
        score += 5

    if left.get("summaryQuality") != "low" and right.get("summaryQuality") != "low":
        score += 1

    return score


def order_cluster_rows(cluster_rows: list[dict]) -> list[dict]:
    if len(cluster_rows) <= 1:
        return cluster_rows

    ordered_pool = sorted(cluster_rows, key=base_row_order_key)
    signal_cache = {row["id"]: row_connection_signals(row) for row in ordered_pool}

    def richness(row: dict) -> int:
        return sum(signal["weight"] for signal in signal_cache[row["id"]].values())

    start = max(
        ordered_pool,
        key=lambda row: (
            richness(row),
            1 if row.get("active") else 0,
            -parse_dt(row.get("lastSeenAt", "")),
            clean_text(row.get("company", "")).lower(),
            clean_text(row.get("title", "")).lower(),
        ),
    )

    remaining = [row for row in ordered_pool if row["id"] != start["id"]]
    ordered = [start]

    while remaining:
        previous = ordered[-1]
        next_row = max(
            remaining,
            key=lambda row: (
                row_similarity(previous, row, signal_cache),
                richness(row),
                1 if row.get("active") else 0,
                -parse_dt(row.get("lastSeenAt", "")),
                clean_text(row.get("company", "")).lower(),
                clean_text(row.get("title", "")).lower(),
            ),
        )
        ordered.append(next_row)
        remaining = [row for row in remaining if row["id"] != next_row["id"]]
    return ordered


def build_row_signal_facets(row: dict) -> dict[str, list[str]]:
    structured_signals = row.get("structuredSignals", {})
    role_signals = unique_clean_values(
        [
            *flatten_structured_signals(structured_signals, ["roleSignals"]),
            row.get("role", ""),
            row.get("roleGroup", ""),
        ],
        limit=4,
    )
    keyword_signals = unique_non_generic(
        [
            *flatten_structured_signals(structured_signals, ["problemSignals", "modelSignals"]),
            row.get("focusLabel", ""),
            *row.get("highlightKeywords", []),
        ],
        limit=6,
    )
    tag_signals = unique_non_generic(
        [
            *flatten_structured_signals(structured_signals, ["domainSignals", "dataSignals"]),
        ],
        limit=4,
    )
    context_signals = unique_non_generic(
        [
            *flatten_structured_signals(structured_signals, ["systemSignals", "workflowSignals"]),
        ],
        limit=6,
    )
    return {
        "role": role_signals,
        "keyword": keyword_signals,
        "tag": tag_signals,
        "context": context_signals,
    }


SECTION_SIGNAL_STRUCTURED_MAP = {
    "detailBody": {
        "keyword": ["problemSignals", "domainSignals"],
        "tag": ["domainSignals", "dataSignals"],
        "context": ["systemSignals", "workflowSignals", "modelSignals"],
    },
    "tasks": {
        "keyword": ["problemSignals", "workflowSignals"],
        "tag": ["domainSignals"],
        "context": ["systemSignals", "workflowSignals"],
    },
    "requirements": {
        "keyword": ["modelSignals", "systemSignals"],
        "tag": ["domainSignals", "dataSignals"],
        "context": ["systemSignals"],
    },
    "preferred": {
        "keyword": ["workflowSignals", "domainSignals"],
        "tag": ["dataSignals", "modelSignals"],
        "context": ["workflowSignals", "systemSignals"],
    },
    "skills": {
        "keyword": ["modelSignals", "dataSignals", "systemSignals"],
        "tag": [],
        "context": ["systemSignals"],
    },
}


def section_field_values(row: dict, section_id: str) -> list[str]:
    if section_id == "detailBody":
        return split_detail_lines(row.get("detailBody", ""))
    values = row.get(section_id, [])
    return values if isinstance(values, list) else []


def collect_section_signal_terms(row: dict, section_id: str, limit: int = 8) -> list[str]:
    values = section_field_values(row, section_id)
    collected = []
    if section_id == "skills":
        collected.extend(unique_clean_values(values, limit=limit))
    for value in values:
        cleaned = clean_text(value)
        if not cleaned:
            continue
        collected.extend(signal_terms_from_text(cleaned, row.get("company", "")))
    return unique_non_generic(collected, limit=limit)


def build_row_section_signal_facets(row: dict) -> dict[str, dict[str, list[str]]]:
    structured_signals = row.get("structuredSignals", {}) if isinstance(row.get("structuredSignals", {}), dict) else {}
    stored_section_facets = normalize_section_signal_facets(row.get("sectionSignalFacets", {}))
    section_facets = {}

    for section_id, category_map in SECTION_SIGNAL_STRUCTURED_MAP.items():
        stored = stored_section_facets.get(section_id, {"keyword": [], "tag": [], "context": []})
        raw_terms = collect_section_signal_terms(row, section_id, limit=8)
        keyword_signals = unique_non_generic(
            flatten_structured_signals(structured_signals, category_map.get("keyword", [])),
            limit=6,
        )
        if section_id == "skills" and not keyword_signals:
            keyword_signals = unique_non_generic(raw_terms, limit=6)

        derived_facets = {
            "keyword": keyword_signals,
            "tag": unique_non_generic(
                flatten_structured_signals(structured_signals, category_map.get("tag", [])),
                limit=4,
            ),
            "context": unique_non_generic(
                flatten_structured_signals(structured_signals, category_map.get("context", [])),
                limit=6,
            ),
        }
        section_facets[section_id] = {
            facet: stored.get(facet, []) or derived_facets[facet]
            for facet in ("keyword", "tag", "context")
        }

    return section_facets


def build_graph_payload(rows: list[dict], clusters: list[dict]) -> dict:
    cluster_nodes = []
    signal_nodes = {}
    posting_nodes = []
    cluster_signal_weights = {}
    posting_signal_edges = []

    cluster_lookup = {cluster["id"]: cluster for cluster in clusters}
    for cluster in clusters:
        cluster_nodes.append(
            {
                "id": f"cluster:{cluster['id']}",
                "clusterId": cluster["id"],
                "label": cluster["label"],
                "tone": cluster["tone"],
                "count": cluster["count"],
                "companyCount": cluster["companyCount"],
            }
        )

    facet_weights = {
        "role": 6,
        "keyword": 5,
        "tag": 3,
        "context": 2,
    }

    for row in rows:
        cluster_id = row.get("clusterId", "cluster")
        row_facets = row.get("signalFacets", {})
        posting_id = f"posting:{row['id']}"
        posting_nodes.append(
            {
                "id": posting_id,
                "postingId": row["id"],
                "clusterId": cluster_id,
                "company": row.get("company", ""),
                "title": row.get("title", ""),
                "role": row.get("role", ""),
                "active": row.get("active", False),
            }
        )

        for facet, labels in row_facets.items():
            for rank, label in enumerate(labels[:4]):
                compact = canonical_text(label)
                if not compact:
                    continue
                signal_id = f"signal:{facet}:{compact}"
                if signal_id not in signal_nodes:
                    signal_nodes[signal_id] = {
                        "id": signal_id,
                        "label": clean_text(label),
                        "facet": facet,
                    }
                cluster_key = (cluster_id, signal_id)
                cluster_signal_weights[cluster_key] = cluster_signal_weights.get(cluster_key, 0) + facet_weights.get(
                    facet, 1
                )
                posting_signal_edges.append(
                    {
                        "source": posting_id,
                        "target": signal_id,
                        "facet": facet,
                        "weight": max(facet_weights.get(facet, 1) - rank, 1),
                    }
                )

    cluster_signal_edges = []
    for (cluster_id, signal_id), weight in sorted(
        cluster_signal_weights.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1]),
    ):
        cluster_signal_edges.append(
            {
                "source": f"cluster:{cluster_id}",
                "target": signal_id,
                "weight": weight,
            }
        )

    cluster_signal_summary = {}
    for cluster in clusters:
        cluster_id = cluster["id"]
        summary = {"role": [], "keyword": [], "tag": [], "context": []}
        related_edges = [
            edge
            for edge in cluster_signal_edges
            if edge["source"] == f"cluster:{cluster_id}"
        ]
        related_edges.sort(key=lambda edge: (-edge["weight"], edge["target"]))
        for edge in related_edges:
            signal = signal_nodes.get(edge["target"])
            if not signal:
                continue
            facet = signal["facet"]
            if facet not in summary or len(summary[facet]) >= 6:
                continue
            summary[facet].append(signal["label"])
        cluster_signal_summary[cluster_id] = summary
        cluster["signalFacets"] = summary

    for row in rows:
        cluster = cluster_lookup.get(row.get("clusterId"))
        if cluster:
            row["clusterSignalFacets"] = cluster_signal_summary.get(cluster["id"], {})

    return {
        "summary": {
            "clusterCount": len(cluster_nodes),
            "postingCount": len(posting_nodes),
            "signalCount": len(signal_nodes),
        },
        "nodes": {
            "clusters": cluster_nodes,
            "signals": list(signal_nodes.values()),
            "postings": posting_nodes,
        },
        "edges": {
            "clusterToSignal": cluster_signal_edges,
            "postingToSignal": posting_signal_edges,
        },
        "clusterSignals": cluster_signal_summary,
    }


def build_summary_board(payload: dict) -> dict:
    all_rows = build_base_rows(payload)
    stage2_deploy = payload.get("source", {}).get("stage2Deploy", {})
    stage2_deploy_enabled = bool(stage2_deploy.get("enabled"))
    if stage2_deploy_enabled:
        # Stage2 deploy gate is the final pre-release approval surface. Once a
        # row passes that gate, the dashboard should not silently hide it again
        # through older service-scope review/exclude overrides.
        included_rows, excluded_rows = all_rows, []
    else:
        included_rows, excluded_rows = filter_service_scope_rows(all_rows)
    review_candidates = [
        row
        for row in excluded_rows
        if explain_service_scope_row(row)["action"] == "review"
    ]
    rows = included_rows
    company_profiles = build_company_profiles(rows)
    clusters = assign_posting_clusters(rows)
    legend = build_tone_legend(rows)

    for row in rows:
        company_profile = company_profiles.get(row["company"], {})
        row["companyReason"] = company_profile.get("reason", "")
        row["companyKeywords"] = company_profile.get("keywords", [])
        row["companyHeadline"] = company_profile.get("headline", "")
        row["signalFacets"] = build_row_signal_facets(row)
        row["sectionSignalFacets"] = build_row_section_signal_facets(row)

    grouped_by_cluster = {}
    for row in rows:
        grouped_by_cluster.setdefault(row.get("clusterId", "cluster"), []).append(row)

    ordered_rows = []
    seen_cluster_ids = set()
    for cluster in clusters:
        cluster_id = cluster["id"]
        seen_cluster_ids.add(cluster_id)
        ordered_rows.extend(order_cluster_rows(grouped_by_cluster.get(cluster_id, [])))

    for cluster_id, cluster_rows in grouped_by_cluster.items():
        if cluster_id in seen_cluster_ids:
            continue
        ordered_rows.extend(order_cluster_rows(cluster_rows))

    rows = ordered_rows

    graph = build_graph_payload(rows, clusters)
    display_coverage = sum(1 for row in rows if clean_text(row.get("summary", "")))
    model_coverage = sum(
        1
        for row in rows
        if row.get("hasSummary") and clean_text(row.get("summaryQuality", "")).lower() != "low"
    )
    service_scope_model_applied = sum(
        1 for row in all_rows if clean_text(row.get("serviceScopeSource", "")).startswith("service_scope_model")
    )
    service_scope_model_low_confidence = sum(
        1
        for row in all_rows
        if clean_text(row.get("serviceScopeSource", "")).startswith("service_scope_model")
        and clean_text(row.get("serviceScopeConfidence", "")).lower() == "low"
    )
    active_count = sum(1 for row in rows if row["active"])
    semantic_bundles = build_semantic_bundles(rows)
    semantic_bundles_by_role = build_role_semantic_bundles(rows)
    return {
        "generatedAt": payload["generatedAt"],
        "source": payload["source"],
        "legend": legend,
        "clusters": clusters,
        "graph": graph,
        "semanticBundles": semantic_bundles,
        "semanticBundlesByRole": semantic_bundles_by_role,
        "overview": {
            "totalJobs": len(rows),
            "sourceJobs": len(all_rows),
            "activeJobs": active_count,
            "inactiveJobs": len(rows) - active_count,
            "summaryCoverage": model_coverage,
            "displaySummaryCoverage": display_coverage,
            "missingSummaries": len(rows) - model_coverage,
            "companyCount": len(company_profiles),
            "clusterCount": len(clusters),
            "semanticBundleCount": len(semantic_bundles),
            "serviceScopeIncludedJobs": len(included_rows),
            "serviceScopeFilteredOutJobs": len(excluded_rows),
            "serviceScopeReviewCandidates": len(review_candidates),
            "serviceScopeModelAppliedJobs": service_scope_model_applied,
            "serviceScopeModelLowConfidence": service_scope_model_low_confidence,
            "serviceScopeBypassedByStage2Deploy": stage2_deploy_enabled,
            "roleFilters": build_role_filters(rows),
        },
        "diagnostics": {
            "excludedRows": [summarize_diagnostic_row(row) for row in excluded_rows],
            "reviewRows": [summarize_diagnostic_row(row) for row in review_candidates],
        },
        "rows": rows,
    }


def main():
    payload = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    board = build_summary_board(payload)
    OUTPUT_PATH.write_text(
        json.dumps(board, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote summary board to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
