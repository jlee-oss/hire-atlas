#!/usr/bin/env python3

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GUARD_PATH = ROOT / "data" / "service_scope_guard_recovery_candidates_001.json"
DEFAULT_MODEL_REVIEW_PATH = ROOT / "data" / "service_scope_model_review.json"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "service_scope_adjudication_pack_001.json"
DEFAULT_CSV_PATH = ROOT / "data" / "service_scope_adjudication_pack_001.csv"
DEFAULT_MD_PATH = ROOT / "docs" / "service_scope_adjudication_pack_001.md"
VALID_DECISIONS = {"include", "review", "exclude"}

STRONG_AI_CONTEXT_PATTERNS = [
    r"\bai\b",
    r"인공지능",
    r"머신러닝",
    r"딥러닝",
    r"\bllm\b",
    r"\brag\b",
    r"컴퓨터\s*비전",
    r"\bnpu\b",
    r"\bsoc\b",
    r"\brtl\b",
    r"\bsdk\b",
    r"드라이버",
    r"펌웨어",
    r"의료\s*ai",
    r"의료\s*영상",
    r"생체신호",
    r"데이터\s*(분석|사이언스|수집|품질|거버넌스|시스템|파이프라인|처리|모델|엔지니어)",
    r"(고객|유저|사용자|서비스|비즈니스)\s*데이터",
    r"실험",
    r"\ba/b\b",
    r"실시간\s*데이터",
    r"제조\s*ai",
]

PERIPHERAL_AI_PATTERNS = [
    r"인공지능\s*기반\s*개발\s*도구",
    r"ai\s*기반\s*개발\s*도구",
    r"생산성\s*향상",
    r"\bcopilot\b",
]

LOW_INFORMATION_PATTERNS = [
    r"정보\s*부족",
    r"직무\s*정보\s*부족",
    r"상세\s*내용\s*없음",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def normalize_decision(value) -> str:
    decision = clean_text(value).lower()
    return decision if decision in VALID_DECISIONS else ""


def load_json(path: Path, default):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def md_cell(value) -> str:
    return clean_text(value).replace("|", "\\|") or "-"


def combined_text(candidate: dict, review_item: dict) -> str:
    parts = [
        candidate.get("company", ""),
        candidate.get("title", ""),
        candidate.get("summary", ""),
        candidate.get("focusLabel", ""),
        " ".join(candidate.get("keywords", []) or []),
        clean_text((review_item.get("modelDecision", {}) or {}).get("reason", "")),
    ]
    for key in ("detailBody", "tasks", "requirements", "preferred", "skills"):
        values = review_item.get(key, [])
        if isinstance(values, list):
            parts.append(" ".join(clean_text(value) for value in values))
    return clean_text(" ".join(parts)).lower()


def has_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def has_strong_ai_context(text: str) -> bool:
    peripheral = has_pattern(text, PERIPHERAL_AI_PATTERNS)
    strong = has_pattern(text, STRONG_AI_CONTEXT_PATTERNS)
    if peripheral and not any(
        re.search(pattern, text, flags=re.IGNORECASE)
        for pattern in STRONG_AI_CONTEXT_PATTERNS
        if pattern not in {r"\bai\b", r"인공지능"}
    ):
        return False
    return strong


def infer_suggestion(candidate: dict, review_item: dict) -> tuple[str, str, str]:
    model_decision = normalize_decision((review_item.get("modelDecision", {}) or {}).get("decision", ""))
    model_reason = clean_text((review_item.get("modelDecision", {}) or {}).get("reason", ""))
    quality = clean_text(candidate.get("summaryQuality", "")).lower()
    summary = clean_text(candidate.get("summary", ""))
    text = combined_text(candidate, review_item)

    if model_decision == "include":
        return "include", "confirm_positive", "후보 모델과 guard가 모두 범위 내 신호를 봄"
    if model_decision == "review":
        return "review", "human_boundary_review", "후보 모델이 hard exclude를 피했으므로 사람이 경계 판정"
    if quality == "low" or not summary or has_pattern(model_reason, LOW_INFORMATION_PATTERNS):
        return "review", "critical_prompt_failure", "정보 부족은 exclude 대신 review로 보류"
    if has_strong_ai_context(text):
        return "review", "critical_prompt_failure", "AI/data/deeptech 신호가 있어 hard exclude 금지"
    return "exclude", "goldset_conflict_review", "일반 non-scope 가능성이 커 goldset 과포함 여부 확인"


def build_pack(guard_path: Path, model_review_path: Path) -> dict:
    guard = load_json(guard_path, {"items": []}) or {"items": []}
    model_review = load_json(model_review_path, {"items": []}) or {"items": []}
    review_by_id = {
        clean_text(item.get("id", "")): item
        for item in model_review.get("items", [])
        if isinstance(item, dict) and clean_text(item.get("id", ""))
    }

    items = []
    for candidate in guard.get("items", []):
        job_id = clean_text(candidate.get("id", ""))
        if not job_id:
            continue
        review_item = review_by_id.get(job_id, {})
        model_decision = review_item.get("modelDecision", {}) if isinstance(review_item, dict) else {}
        suggested_decision, priority, suggested_reason = infer_suggestion(candidate, review_item)
        provisional_target = normalize_decision(candidate.get("serviceScopeResolvedAction", "")) or "include"
        model_action = normalize_decision(model_decision.get("decision", ""))
        items.append(
            {
                "id": job_id,
                "company": clean_text(candidate.get("company", "")),
                "title": clean_text(candidate.get("title", "")),
                "jobUrl": clean_text(candidate.get("jobUrl", "")),
                "summaryQuality": clean_text(candidate.get("summaryQuality", "")),
                "focusLabel": clean_text(candidate.get("focusLabel", "")),
                "keywords": [clean_text(value) for value in candidate.get("keywords", []) if clean_text(value)],
                "summary": clean_text(candidate.get("summary", "")),
                "provisionalTarget": provisional_target,
                "modelDecision": model_action or "missing",
                "modelConfidence": clean_text(model_decision.get("confidence", "")),
                "modelReason": clean_text(model_decision.get("reason", "")),
                "suggestedServiceScope": suggested_decision,
                "suggestedReason": suggested_reason,
                "reviewPriority": priority,
                "confirmServiceScope": "",
                "confirmRoleGroup": "",
                "confirmFocusLabel": "",
                "reviewerNotes": "",
            }
        )

    priority_order = {
        "critical_prompt_failure": 0,
        "goldset_conflict_review": 1,
        "human_boundary_review": 2,
        "confirm_positive": 3,
    }
    items.sort(
        key=lambda item: (
            priority_order.get(item["reviewPriority"], 9),
            {"high": 0, "medium": 1, "low": 2}.get(item["summaryQuality"], 9),
            item["company"],
            item["title"],
        )
    )
    return {
        "generatedAt": now_iso(),
        "source": {
            "guardCandidates": str(guard_path),
            "modelReview": str(model_review_path),
        },
        "counts": {
            "items": len(items),
            "modelDecisions": dict(sorted(Counter(item["modelDecision"] for item in items).items())),
            "suggestedDecisions": dict(sorted(Counter(item["suggestedServiceScope"] for item in items).items())),
            "reviewPriorities": dict(sorted(Counter(item["reviewPriority"] for item in items).items())),
        },
        "policy": {
            "confirmationRule": "Only confirmServiceScope is treated as human-confirmed input.",
            "suggestedServiceScope": "Draft helper only; do not treat as confirmed.",
        },
        "items": items,
    }


def write_csv(path: Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "company",
        "title",
        "summaryQuality",
        "focusLabel",
        "modelDecision",
        "modelConfidence",
        "modelReason",
        "provisionalTarget",
        "suggestedServiceScope",
        "suggestedReason",
        "reviewPriority",
        "confirmServiceScope",
        "confirmRoleGroup",
        "confirmFocusLabel",
        "reviewerNotes",
        "summary",
        "keywords",
        "jobUrl",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in items:
            writer.writerow({**item, "keywords": ", ".join(item.get("keywords", []))})


def render_md(payload: dict) -> str:
    counts = payload["counts"]
    lines = [
        "# Service Scope Adjudication Pack 001",
        "",
        f"- generatedAt: `{payload['generatedAt']}`",
        f"- items: `{counts['items']}`",
        f"- modelDecisions: `{counts['modelDecisions']}`",
        f"- suggestedDecisions: `{counts['suggestedDecisions']}`",
        f"- reviewPriorities: `{counts['reviewPriorities']}`",
        "",
        "이 문서는 confirmed goldset이 아닙니다.",
        "`suggestedServiceScope`는 검수 보조값이며, 최종 확정은 `confirmServiceScope`에 사람이 입력해야 합니다.",
        "",
        "## Critical / Conflict Rows",
        "",
        "| # | priority | company | title | quality | model | suggested | reason |",
        "|---:|---|---|---|---|---|---|---|",
    ]
    highlighted = [
        item
        for item in payload["items"]
        if item["reviewPriority"] in {"critical_prompt_failure", "goldset_conflict_review"}
    ]
    for index, item in enumerate(highlighted, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    md_cell(item["reviewPriority"]),
                    md_cell(item["company"]),
                    md_cell(item["title"]),
                    md_cell(item["summaryQuality"]),
                    md_cell(item["modelDecision"]),
                    md_cell(item["suggestedServiceScope"]),
                    md_cell(item["suggestedReason"]),
                ]
            )
            + " |"
        )
    if not highlighted:
        lines.append("| - | - | - | - | - | - | - | - |")

    lines.extend(
        [
            "",
            "## All Rows",
            "",
            "| # | company | title | quality | model | suggested | confirm |",
            "|---:|---|---|---|---|---|---|",
        ]
    )
    for index, item in enumerate(payload["items"], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    md_cell(item["company"]),
                    md_cell(item["title"]),
                    md_cell(item["summaryQuality"]),
                    md_cell(item["modelDecision"]),
                    md_cell(item["suggestedServiceScope"]),
                    "",
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--guard", type=Path, default=DEFAULT_GUARD_PATH)
    parser.add_argument("--model-review", type=Path, default=DEFAULT_MODEL_REVIEW_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_CSV_PATH)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_PATH)
    args = parser.parse_args()

    payload = build_pack(args.guard, args.model_review)
    write_json(args.output, payload)
    write_csv(args.csv_output, payload["items"])
    write_text(args.md_output, render_md(payload))
    print(
        json.dumps(
            {
                "adjudicationJson": str(args.output),
                "adjudicationCsv": str(args.csv_output),
                "adjudicationMd": str(args.md_output),
                "counts": payload["counts"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
