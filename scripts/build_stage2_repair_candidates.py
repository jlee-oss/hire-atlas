#!/usr/bin/env python3

import argparse
import csv
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ai_runtime import extract_json_object
from run_stage2_validation import (
    DEFAULT_SERVICE_ACCOUNT_JSON,
    DEFAULT_STAGE1_GID,
    DEFAULT_STAGE1_SPREADSHEET_ID,
    DEFAULT_STAGE1_TITLE,
    clean,
    pick,
    row_id,
    safe_read_sheet,
    split_terms,
    stage1_focus,
    stage1_keywords,
    stage1_role,
    stage1_summary,
    validate_stage1_row,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VALIDATION_CSV = ROOT / "data" / "stage2_validation_candidates_latest.csv"
DEFAULT_OUTPUT_JSON = ROOT / "data" / "stage2_repair_candidates_latest.json"
DEFAULT_OUTPUT_CSV = ROOT / "data" / "stage2_repair_candidates_latest.csv"
DEFAULT_OUTPUT_MD = ROOT / "docs" / "stage2_repair_candidates_latest.md"

ALLOWED_ROLES = {
    "인공지능 엔지니어",
    "인공지능 리서처",
    "데이터 사이언티스트",
    "데이터 분석가",
}

OUTPUT_FIELDNAMES = [
    "공고키",
    "회사명",
    "공고제목",
    "검증우선순위",
    "이슈코드",
    "repair_group",
    "source",
    "suggested_stage2_분류직무",
    "suggested_stage2_직무초점",
    "suggested_stage2_핵심기술",
    "suggested_stage2_구분요약",
    "confidence",
    "recommended_action",
    "rationale",
    "before_blocking_issues",
    "after_blocking_issues",
    "after_blocking_count",
    "repair_effect",
    "stage1_분류직무",
    "stage1_직무초점",
    "stage1_핵심기술",
    "stage1_구분요약",
    "evidence",
]

KEYWORD_PATTERNS = [
    (r"\bpython\b|파이썬", "Python"),
    (r"\bsql\b|에스큐엘", "SQL"),
    (r"\bspark\b|스파크", "Spark"),
    (r"\bairflow\b|에어플로", "Airflow"),
    (r"\bkafka\b|카프카", "Kafka"),
    (r"\bdbt\b|디비티", "dbt"),
    (r"\bbigquery\b|빅쿼리", "BigQuery"),
    (r"\btableau\b|태블로", "Tableau"),
    (r"\bsuperset\b|슈퍼셋", "Superset"),
    (r"\bkubernetes\b|쿠버네티스", "Kubernetes"),
    (r"\bdocker\b|도커", "Docker"),
    (r"\baws\b|에이더블유에스", "AWS"),
    (r"\bgcp\b|지씨피", "GCP"),
    (r"\bazure\b|애저", "Azure"),
    (r"\bmlops\b|엠엘옵스", "MLOps"),
    (r"machine\s*learning|머신\s*러닝|머신러닝", "머신러닝"),
    (r"\bai\b|인공지능", "AI"),
    (r"\bllm\b|엘엘엠", "LLM"),
    (r"\brag\b|검색증강생성", "RAG"),
    (r"\bvlm\b|브이엘엠", "VLM"),
    (r"\bpytorch\b|파이토치", "PyTorch"),
    (r"\btensorflow\b|텐서플로", "TensorFlow"),
    (r"컴퓨터\s*비전|컴퓨터비전", "컴퓨터비전"),
    (r"멀티모달", "멀티모달"),
    (r"\bgpu\b|지피유", "GPU"),
    (r"\bnpu\b|엔피유", "NPU"),
    (r"\bcuda\b|씨유디에이", "CUDA"),
    (r"\bros\b", "ROS"),
    (r"isaac", "Isaac Sim"),
    (r"로봇|로보틱스", "로보틱스"),
    (r"자율주행|adas", "자율주행"),
    (r"심전도|생체신호", "생체신호"),
    (r"의료|임상|헬스케어|SaMD", "헬스케어"),
    (r"보안|security|offensive|취약점", "보안"),
    (r"pcie|pcb|fpga|rtl|soc|반도체", "AI반도체"),
    (r"digital\s*design|design\s*engineer", "디지털설계"),
    (r"high[-\s]*speed|io\s*ip|interface", "High-Speed IO"),
    (r"\bip\s*design\b|ip\s*설계", "IP 설계"),
    (r"데이터\s*마트|웨어\s*하우스|웨어하우스|\bdw\b", "데이터웨어하우스"),
    (r"이티엘|\betl\b|이엘티|\belt\b", "ETL"),
    (r"react\s*native", "React Native"),
    (r"mobile|모바일", "모바일앱"),
    (r"생산\s*계획|스케줄링|scheduling|scheduler", "스케줄링"),
    (r"제조|production", "제조최적화"),
    (r"\bqa\b|quality|품질|test\s*automation|테스트\s*자동화|테스트자동화", "QA"),
    (r"testing|테스트", "검증"),
    (r"리스크|risk|fraud|부정", "리스크분석"),
]

FOCUS_RULES = [
    (r"로봇|로보틱스|isaac|ros|simulation", "로보틱스 / 시뮬레이션"),
    (r"자율주행|adas", "자율주행 / 시스템"),
    (r"심전도|생체신호", "생체신호 / 헬스케어"),
    (r"임상|의료|헬스케어|SaMD", "헬스케어 / 의료데이터"),
    (r"pcie|pcb|fpga|rtl|soc|npu|gpu|반도체", "AI반도체 / 하드웨어"),
    (r"digital\s*design|design\s*engineer", "AI반도체 / 하드웨어"),
    (r"high[-\s]*speed|io\s*ip|interface", "AI반도체 / 하드웨어"),
    (r"데이터\s*마트|웨어\s*하우스|웨어하우스|\bdw\b|etl|이티엘", "데이터플랫폼 / ETL"),
    (r"bi|business intelligence|대시보드|지표|analytics", "BI / 지표분석"),
    (r"react\s*native|mobile|모바일", "모바일앱 / 프론트엔드"),
    (r"machine\s*learning|머신\s*러닝|머신러닝|\bai\b|인공지능", "모델링 / 최적화"),
    (r"생산\s*계획|스케줄링|scheduling|scheduler", "최적화 / 제조"),
    (r"\bqa\b|quality|품질|test\s*automation|테스트\s*자동화|테스트자동화", "QA / 품질지표"),
    (r"testing|테스트", "검증 / QA"),
    (r"리스크|risk|fraud|부정", "리스크 / 데이터분석"),
    (r"\bllm\b|엘엘엠|rag|검색증강생성", "LLM / RAG"),
    (r"모델\s*서빙|serving", "모델서빙 / 인프라"),
    (r"ai\s*platform|AI\s*플랫폼|인공지능\s*플랫폼|AI\s*인프라|mlops|엠엘옵스", "AI플랫폼 / MLOps"),
    (r"컴퓨터\s*비전|컴퓨터비전|얼굴인식|위조", "컴퓨터비전 / 검증"),
    (r"보안|security|offensive|취약점", "보안연구 / 취약점분석"),
    (r"kubernetes|쿠버네티스|docker|도커|클라우드|aws|gcp|azure", "인프라 / 클라우드"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=OUTPUT_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def issue_codes(row: dict) -> list[str]:
    return [clean(part) for part in clean(row.get("이슈코드", "")).split("|") if clean(part)]


def target_rows(rows: list[dict]) -> list[dict]:
    return [row for row in rows if clean(row.get("검증상태", "")) == "needs_review"]


def combined_text(stage1: dict, candidate: dict) -> str:
    return " ".join(
        [
            pick(stage1, "회사명_표시", "회사명"),
            pick(stage1, "공고제목_표시", "공고제목_raw", "job_title_raw"),
            stage1_role(stage1),
            stage1_focus(stage1),
            stage1_keywords(stage1),
            stage1_summary(stage1),
            pick(stage1, "상세본문_분석용"),
            pick(stage1, "주요업무_표시", "주요업무_분석용"),
            pick(stage1, "자격요건_표시", "자격요건_분석용"),
            pick(stage1, "우대사항_표시", "우대사항_분석용"),
            clean(candidate.get("이슈요약", "")),
        ]
    )


def matches(text: str, pattern: str) -> bool:
    return re.search(pattern, text, re.IGNORECASE) is not None


def suggest_role(title: str, text: str, current_role: str) -> tuple[str, str, str]:
    title_text = title.lower()
    if matches(title_text, r"clinical\s+research\s+scientist|임상\s*연구|data\s+science|data\s+scientist|ds\(data science\)"):
        return "데이터 사이언티스트", "high", "임상/데이터 과학 제목 신호"
    if matches(title_text, r"data\s+analytics\s+engineer|analytics\s+engineer|data\s+analyst|bi\s*/?\s*dw|business intelligence|product analyst|growth|crm|cx|pmo|marketing|데이터\s*분석가|제품\s*분석"):
        return "데이터 분석가", "high", "분석가/BI/Growth 계열 제목 신호"
    if matches(title_text, r"researcher|research scientist|ai\s*research|ml\s*research|리서처|연구원") and matches(text, r"\bai\b|\bml\b|\bllm\b|\bvlm\b|인공지능|머신러닝|딥러닝|컴퓨터\s*비전"):
        return "인공지능 리서처", "medium", "AI 연구자 제목 신호"
    if matches(title_text, r"robotics|로보틱스|isaac|ros|ai|ml|llm|model serving|computer vision|컴퓨터\s*비전"):
        return "인공지능 엔지니어", "medium", "AI/딥테크 엔지니어링 제목 신호"
    if matches(title_text, r"data\s+engineer|data\s+platform|data\s+service|데이터\s*엔지니어|데이터\s*플랫폼"):
        if matches(text, r"bi|대시보드|지표|데이터\s*마트|웨어\s*하우스|웨어하우스|\bdw\b|analytics"):
            return "데이터 분석가", "medium", "BI/데이터마트 중심 데이터 엔지니어링"
        if matches(text, r"\bai\b|\bml\b|\bllm\b|mlops|벡터|모델|인공지능"):
            return "인공지능 엔지니어", "medium", "AI/ML 시스템과 연결된 데이터 엔지니어링"
        return "데이터 분석가", "low", "순수 데이터 엔지니어링은 별도 직군이 없어 검수 필요"
    return current_role if current_role in ALLOWED_ROLES else "", "low", "현재 직군 유지 후보"


def suggest_focus(title: str, text: str, current_focus: str, suggested_role: str) -> tuple[str, str]:
    title_text = title.lower()
    if suggested_role == "데이터 분석가":
        if matches(title_text, r"analytics|bi\s*/?\s*dw|business intelligence|data analyst|product analyst|growth|crm|cx|pmo|marketing|분석가"):
            return "BI / 지표분석", "데이터 분석가 제목 기반 초점"
        if matches(title_text + " " + text, r"데이터\s*마트|웨어\s*하우스|웨어하우스|\bdw\b|etl|이티엘|data\s+platform|data\s+engineer|데이터\s*엔지니어|데이터\s*플랫폼"):
            return "데이터플랫폼 / ETL", "데이터 엔지니어링 제목 기반 초점"
    if suggested_role == "데이터 사이언티스트":
        if matches(title_text + " " + text, r"임상|의료|헬스케어|심전도|생체신호"):
            return "헬스케어 / 의료데이터", "데이터 과학 의료 도메인 초점"
        return "실험설계 / 모델링", "데이터 과학 역할 기반 초점"
    if suggested_role in {"인공지능 엔지니어", "인공지능 리서처"}:
        if matches(title_text, r"ai\s*platform|AI\s*플랫폼|ai\s*devops|devops/ai"):
            return "AI플랫폼 / MLOps", "AI 플랫폼 제목 기반 초점"
        if matches(title_text, r"\bllm\b|엘엘엠"):
            return "LLM / RAG", "LLM 제목 기반 초점"
        if matches(title_text, r"model\s*serving|모델\s*서빙"):
            return "모델서빙 / 인프라", "모델 서빙 제목 기반 초점"
        if matches(title_text, r"ml\s*research|machine learning|머신러닝"):
            return "모델링 / 최적화", "ML 제목 기반 초점"
    for pattern, focus in FOCUS_RULES:
        if matches(title + " " + text, pattern):
            return focus, f"focus rule: {focus}"
    if current_focus:
        return current_focus, "현재 직무초점 유지"
    return "", "초점 후보 부족"


def suggest_keywords(text: str, current_keywords: str) -> tuple[list[str], str]:
    terms = split_terms(current_keywords)
    if terms:
        return terms[:8], "현재 핵심기술 유지"
    keywords = []
    for pattern, label in KEYWORD_PATTERNS:
        if matches(text, pattern) and label not in keywords:
            keywords.append(label)
    return keywords[:8], "본문/필드에서 기술 키워드 추출"


def suggest_summary(stage1: dict, focus: str, current_summary: str) -> tuple[str, str]:
    parts = []
    career = pick(stage1, "경력수준_표시", "경력수준_raw")
    track = pick(stage1, "채용트랙_표시")
    if career:
        parts.append(career)
    if track and track not in parts:
        parts.append(track)
    for part in re.split(r"[/,]+", focus or ""):
        cleaned = clean(part)
        if cleaned and cleaned not in parts:
            parts.append(cleaned)
    if len(parts) >= 2:
        return " / ".join(parts[:4]), "경력/트랙/초점 조합"
    if current_summary:
        return current_summary, "현재 구분요약 유지"
    return "", "구분요약 후보 부족"


def repair_group(codes: list[str]) -> str:
    if any(code.startswith("stage2_") and code != "stage2_pending" for code in codes):
        return "stage2_sync"
    if any(code in {"analytics_engineering_as_ai_role", "data_engineering_as_ai_role", "data_engineering_ai_title_review", "business_focus_in_ai_role", "business_role_as_ai_role", "deeptech_as_analyst", "clinical_scientist_as_analyst"} for code in codes):
        return "role_mismatch"
    if any(code in {"missing_keywords", "missing_focus", "missing_group_summary", "noise_keyword", "duplicate_signal"} for code in codes):
        return "signal_extraction"
    return "other"


def build_heuristic_repair(candidate: dict, stage1: dict) -> dict:
    codes = issue_codes(candidate)
    group = repair_group(codes)
    title = pick(stage1, "공고제목_표시", "공고제목_raw", "job_title_raw") or clean(candidate.get("공고제목_표시", ""))
    text = combined_text(stage1, candidate)
    current_role = stage1_role(stage1) or clean(candidate.get("stage1_분류직무", ""))
    current_focus = stage1_focus(stage1) or clean(candidate.get("stage1_직무초점", ""))
    current_keywords = stage1_keywords(stage1) or clean(candidate.get("stage1_핵심기술", ""))
    current_summary = stage1_summary(stage1) or clean(candidate.get("stage1_구분요약", ""))

    if group == "stage2_sync":
        suggested_role = current_role
        suggested_focus = current_focus
        suggested_keywords = split_terms(current_keywords)
        suggested_summary = current_summary
        confidence = "high"
        recommended_action = "resync_stage2_candidate"
        rationale = "1차 변경해시 기준으로 2차 후보를 다시 맞춰야 합니다."
        evidence = "stage2_stale"
    else:
        suggested_role, role_confidence, role_reason = suggest_role(title, text, current_role)
        suggested_focus, focus_reason = suggest_focus(title, text, current_focus, suggested_role)
        keyword_terms, keyword_reason = suggest_keywords(text, current_keywords)
        suggested_summary, summary_reason = suggest_summary(stage1, suggested_focus, current_summary)
        suggested_keywords = keyword_terms
        confidence = "medium"
        if role_confidence == "high" and suggested_focus and suggested_keywords and suggested_summary:
            confidence = "high"
        if not suggested_focus or not suggested_keywords or not suggested_summary:
            confidence = "low"
        recommended_action = "repair_then_review" if confidence != "low" else "model_or_human_review_required"
        rationale = " / ".join([role_reason, focus_reason, keyword_reason, summary_reason])[:240]
        evidence = text[:500]

    return {
        "공고키": row_id(stage1) or clean(candidate.get("공고키", "")),
        "회사명": pick(stage1, "회사명_표시", "회사명") or clean(candidate.get("회사명_표시", "")),
        "공고제목": title,
        "검증우선순위": clean(candidate.get("검증우선순위", "")),
        "이슈코드": clean(candidate.get("이슈코드", "")),
        "repair_group": group,
        "source": "heuristic",
        "suggested_stage2_분류직무": suggested_role,
        "suggested_stage2_직무초점": suggested_focus,
        "suggested_stage2_핵심기술": ", ".join(suggested_keywords[:8]),
        "suggested_stage2_구분요약": suggested_summary,
        "confidence": confidence,
        "recommended_action": recommended_action,
        "rationale": rationale,
        "stage1_분류직무": current_role,
        "stage1_직무초점": current_focus,
        "stage1_핵심기술": current_keywords,
        "stage1_구분요약": current_summary,
        "evidence": evidence,
    }


def build_model_messages(repairs: list[dict]) -> list[dict]:
    system_prompt = (
        "당신은 한국어 AI/데이터 채용 보드의 2차 검수 보정기입니다. "
        "입력 행은 1차 분류/키워드/요약이 품질 게이트에서 걸린 후보입니다. "
        "목표는 공고를 제거하는 것이 아니라, 배포 전 2차 검수자가 승인할 수 있도록 분류직무, 직무초점, 핵심기술, 구분요약 후보를 더 정확히 제안하는 것입니다. "
        "허용 분류직무는 인공지능 엔지니어, 인공지능 리서처, 데이터 사이언티스트, 데이터 분석가 네 개뿐입니다. "
        "CRM/CX/PMO/Growth/BI/대시보드/퍼널/리텐션 중심이면 데이터 분석가입니다. "
        "임상 연구, 통계 모델링, 실험 설계, 예측/검증 중심이면 데이터 사이언티스트입니다. "
        "LLM, RAG, MLOps, 모델 서빙, AI 플랫폼, 컴퓨터비전, 로보틱스, AI반도체 시스템 구현이면 인공지능 엔지니어입니다. "
        "논문, 알고리즘 연구, foundation/multimodal 연구가 핵심이면 인공지능 리서처입니다. "
        "핵심기술은 기술명/도메인 신호 3~8개만 쓰고, 문장 조각이나 채용절차 표현은 금지합니다. "
        "구분요약은 '경력 / LLM / RAG'처럼 짧은 슬래시 구문으로 쓰세요. "
        "strict JSON only: {\"items\":[{\"id\":\"...\",\"role\":\"...\",\"focus\":\"...\",\"keywords\":[\"...\"],\"summary\":\"...\",\"confidence\":\"high|medium|low\",\"rationale\":\"...\"}]}"
    )
    payload = {
        "items": [
            {
                "id": item["공고키"],
                "company": item["회사명"],
                "title": item["공고제목"],
                "issues": item["이슈코드"],
                "stage1Role": item["stage1_분류직무"],
                "stage1Focus": item["stage1_직무초점"],
                "stage1Keywords": item["stage1_핵심기술"],
                "stage1Summary": item["stage1_구분요약"],
                "heuristicSuggestion": {
                    "role": item["suggested_stage2_분류직무"],
                    "focus": item["suggested_stage2_직무초점"],
                    "keywords": item["suggested_stage2_핵심기술"],
                    "summary": item["suggested_stage2_구분요약"],
                },
                "evidence": item["evidence"],
            }
            for item in repairs
        ]
    }
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def apply_model_repair(config: dict, repairs: list[dict]) -> list[dict]:
    if not repairs:
        return repairs
    payload = {
        "model": config["model"],
        "temperature": float(config.get("temperature", 0.1)),
        "response_format": {"type": "json_object"},
        "messages": build_model_messages(repairs),
    }
    headers = {"Content-Type": "application/json"}
    if config.get("apiKey"):
        headers["Authorization"] = f"Bearer {config['apiKey']}"
    request = urllib.request.Request(
        f"{config['baseUrl'].rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))
    parsed = extract_json_object(body["choices"][0]["message"]["content"])
    items = parsed.get("items", []) if isinstance(parsed, dict) else []
    by_id = {clean(item.get("id", "")): item for item in items if isinstance(item, dict)}
    output = []
    for repair in repairs:
        model_item = by_id.get(repair["공고키"])
        if not model_item:
            output.append(repair)
            continue
        keywords = model_item.get("keywords", [])
        if not isinstance(keywords, list):
            keywords = []
        confidence = clean(model_item.get("confidence", "")).lower()
        if confidence not in {"high", "medium", "low"}:
            confidence = repair["confidence"]
        output.append(
            {
                **repair,
                "source": "model",
                "suggested_stage2_분류직무": clean(model_item.get("role", "")) or repair["suggested_stage2_분류직무"],
                "suggested_stage2_직무초점": clean(model_item.get("focus", "")) or repair["suggested_stage2_직무초점"],
                "suggested_stage2_핵심기술": ", ".join(clean(value) for value in keywords if clean(value)) or repair["suggested_stage2_핵심기술"],
                "suggested_stage2_구분요약": clean(model_item.get("summary", "")) or repair["suggested_stage2_구분요약"],
                "confidence": confidence,
                "recommended_action": "repair_then_review" if confidence in {"high", "medium"} else "human_review_required",
                "rationale": clean(model_item.get("rationale", "")) or repair["rationale"],
            }
        )
    return output


def blocking_codes(issues: list[dict]) -> list[str]:
    return [item["code"] for item in issues if item.get("severity") in {"high", "medium"}]


def annotate_repair_effects(repairs: list[dict], stage1_by_id: dict[str, dict]) -> list[dict]:
    annotated = []
    for repair in repairs:
        stage1 = stage1_by_id.get(repair["공고키"], {})
        before_codes = blocking_codes(validate_stage1_row(stage1)) if stage1 else []
        after_row = dict(stage1)
        after_row["분류직무"] = repair.get("suggested_stage2_분류직무", "")
        after_row["직무초점_표시"] = repair.get("suggested_stage2_직무초점", "")
        after_row["핵심기술_표시"] = repair.get("suggested_stage2_핵심기술", "")
        after_row["구분요약_표시"] = repair.get("suggested_stage2_구분요약", "")
        after_codes = blocking_codes(validate_stage1_row(after_row)) if stage1 else before_codes
        if not after_codes:
            effect = "clears_blocking_issues"
        elif len(after_codes) < len(before_codes):
            effect = "reduces_blocking_issues"
        elif after_codes == before_codes:
            effect = "no_change"
        else:
            effect = "needs_more_review"
        annotated.append(
            {
                **repair,
                "before_blocking_issues": " | ".join(before_codes),
                "after_blocking_issues": " | ".join(after_codes),
                "after_blocking_count": str(len(after_codes)),
                "repair_effect": effect,
            }
        )
    return annotated


def render_md(report: dict) -> str:
    lines = [
        "# Stage2 Repair Candidates Latest",
        "",
        f"- generatedAt: `{report['generatedAt']}`",
        f"- source: `{report['source']}`",
        f"- targetRows: `{report['counts']['targetRows']}`",
        f"- highConfidence: `{report['counts']['highConfidence']}`",
        f"- mediumConfidence: `{report['counts']['mediumConfidence']}`",
        f"- lowConfidence: `{report['counts']['lowConfidence']}`",
        f"- clearsBlockingIssues: `{report['counts']['clearsBlockingIssues']}`",
        f"- reducesBlockingIssues: `{report['counts']['reducesBlockingIssues']}`",
        f"- needsMoreReview: `{report['counts']['needsMoreReview']}`",
        f"- unresolvedAfterRepair: `{report['counts']['unresolvedAfterRepair']}`",
        "",
        "## Groups",
        "",
    ]
    for key, value in sorted(report["groupCounts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Examples", ""])
    for item in report["items"][:30]:
        lines.append(
            f"- `{item['회사명']}` | `{item['공고제목']}` | `{item['repair_group']}` | "
            f"`{item['suggested_stage2_분류직무']}` | `{item['suggested_stage2_직무초점']}` | "
            f"`{item['confidence']}` | `{item.get('repair_effect', '')}`"
        )
    lines.extend(["", "## Outputs", ""])
    for key, value in report["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build local-only stage2 repair candidates.")
    parser.add_argument("--validation-csv", type=Path, default=DEFAULT_VALIDATION_CSV)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-csv", type=Path, default=DEFAULT_OUTPUT_CSV)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--stage1-spreadsheet-id", default=DEFAULT_STAGE1_SPREADSHEET_ID)
    parser.add_argument("--stage1-gid", default=DEFAULT_STAGE1_GID)
    parser.add_argument("--stage1-title", default=DEFAULT_STAGE1_TITLE)
    parser.add_argument("--service-account-json", default=DEFAULT_SERVICE_ACCOUNT_JSON)
    parser.add_argument("--use-model", action="store_true")
    parser.add_argument("--base-url", default=os.environ.get("COMPANY_INSIGHT_BASE_URL", ""))
    parser.add_argument("--model", default=os.environ.get("COMPANY_INSIGHT_MODEL", ""))
    parser.add_argument("--api-key", default=os.environ.get("COMPANY_INSIGHT_API_KEY", ""))
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validation_rows = read_csv(args.validation_csv)
    stage1_rows, stage1_source, stage1_error = safe_read_sheet(
        spreadsheet_id=args.stage1_spreadsheet_id,
        gid=args.stage1_gid,
        title=args.stage1_title,
        service_account_json=args.service_account_json,
        label="stage1",
    )
    if stage1_error:
        raise SystemExit(f"Stage1 sheet is unreadable: {stage1_error}")
    stage1_by_id = {row_id(row): row for row in stage1_rows if row_id(row)}

    repairs = []
    for candidate in target_rows(validation_rows):
        stage1 = stage1_by_id.get(clean(candidate.get("공고키", "")))
        if not stage1:
            continue
        repairs.append(build_heuristic_repair(candidate, stage1))

    source = "heuristic"
    if args.use_model:
        if not args.base_url or not args.model:
            raise SystemExit("Model repair requires --base-url/--model or COMPANY_INSIGHT_BASE_URL/COMPANY_INSIGHT_MODEL.")
        repairs = apply_model_repair(
            {
                "baseUrl": args.base_url,
                "model": args.model,
                "apiKey": args.api_key,
            },
            repairs,
        )
        source = "model"

    repairs = annotate_repair_effects(repairs, stage1_by_id)

    group_counts = {}
    for item in repairs:
        group_counts[item["repair_group"]] = group_counts.get(item["repair_group"], 0) + 1
    counts = {
        "targetRows": len(repairs),
        "highConfidence": sum(1 for item in repairs if item["confidence"] == "high"),
        "mediumConfidence": sum(1 for item in repairs if item["confidence"] == "medium"),
        "lowConfidence": sum(1 for item in repairs if item["confidence"] == "low"),
        "clearsBlockingIssues": sum(1 for item in repairs if item.get("repair_effect") == "clears_blocking_issues"),
        "reducesBlockingIssues": sum(1 for item in repairs if item.get("repair_effect") == "reduces_blocking_issues"),
        "needsMoreReview": sum(1 for item in repairs if item.get("repair_effect") in {"needs_more_review", "no_change"}),
        "unresolvedAfterRepair": sum(1 for item in repairs if clean(item.get("after_blocking_count", "0")) not in {"", "0"}),
    }
    report = {
        "generatedAt": now_iso(),
        "source": source,
        "stage1Source": stage1_source,
        "counts": counts,
        "groupCounts": group_counts,
        "items": repairs,
        "outputs": {
            "json": str(args.output_json),
            "csv": str(args.output_csv),
            "md": str(args.output_md),
        },
    }
    write_json(args.output_json, report)
    write_csv(args.output_csv, repairs)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "source": report["source"],
                "counts": report["counts"],
                "groupCounts": report["groupCounts"],
                "outputs": report["outputs"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
