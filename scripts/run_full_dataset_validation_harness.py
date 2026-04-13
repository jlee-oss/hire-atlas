#!/usr/bin/env python3

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ai_runtime import (
    JOBS_PATH,
    compute_role_group_signature,
    compute_service_scope_signature,
    load_summary_store,
)
from build_summary_board import (
    OUTPUT_PATH as SUMMARY_BOARD_PATH,
    build_summary_board,
    load_role_group_override_store,
    load_service_scope_override_store,
)


ROOT = JOBS_PATH.parent.parent
OUTPUT_JSON = ROOT / "data" / "full_dataset_harness_latest.json"
OUTPUT_MD = ROOT / "docs" / "full_dataset_harness_latest.md"

DEEPTECH_PATTERNS = [
    r"로봇",
    r"로보틱스",
    r"자율주행",
    r"컴퓨터 비전",
    r"\bvision\b",
    r"\bvlm\b",
    r"\bllm\b",
    r"임베디드",
    r"\bnpu\b",
    r"반도체",
    r"제어",
    r"미들웨어",
]
BUSINESS_PATTERNS = [
    r"\bcrm\b",
    r"\bcx\b",
    r"\bpmo\b",
    r"growth",
    r"marketing",
    r"재무",
    r"손익",
    r"\bfp&a\b",
    r"finance",
    r"광고",
    r"매출",
    r"퍼널",
    r"리텐션",
    r"캠페인",
]
BUSINESS_DOMINANCE_PATTERNS = [
    r"\bcrm\b",
    r"\bcx\b",
    r"\bpmo\b",
    r"growth",
    r"marketing",
    r"재무",
    r"손익",
    r"\bfp&a\b",
    r"finance",
    r"매출",
    r"퍼널",
    r"리텐션",
    r"캠페인",
    r"광고 성과 분석",
    r"고객 관계 관리",
    r"제품 성장 분석",
    r"그로스 마케팅",
]
TOOL_FOCUS_LABELS = {
    "onnx",
    "pytorch",
    "tensorflow",
    "sql",
    "docker",
    "kubernetes",
    "cad",
    "excel",
    "엑셀",
    "도커",
    "쿠버네티스",
}
FAMILY_SEVERITY = {
    "excluded_leaked_into_display": "high",
    "deeptech_in_data_analyst": "high",
    "deeptech_context_present": "info",
    "business_in_engineer_family": "high",
    "business_context_present": "info",
    "tool_first_focus": "high",
    "service_scope_review_in_display": "high",
    "broad_focus_specificity_gap": "medium",
}
BROAD_FOCUS_LABELS = {
    "클라우드",
    "인프라",
    "시스템 아키텍처",
    "데이터 파이프라인",
    "플랫폼",
}
BROAD_FOCUS_CANONICAL = {re.sub(r"[^0-9a-z가-힣]+", "", value.lower()) for value in BROAD_FOCUS_LABELS}
SPECIFICITY_SIGNAL_BLOCKLIST = {
    "클라우드",
    "인프라",
    "플랫폼",
    "시스템",
    "아키텍처",
    "데이터",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def canonical_text(value) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", clean_text(value).lower())


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def row_text(row: dict) -> str:
    return " ".join(
        [
            clean_text(row.get("company", "")),
            clean_text(row.get("title", "")),
            clean_text(row.get("summary", "")),
            clean_text(row.get("focusLabel", "")),
            " ".join(clean_text(value) for value in (row.get("highlightKeywords") or [])),
            json.dumps(row.get("structuredSignals", {}) or {}, ensure_ascii=False),
            json.dumps(row.get("sectionSignalFacets", {}) or {}, ensure_ascii=False),
        ]
    ).lower()


def row_stub(row: dict, reason: str = "") -> dict:
    return {
        "id": row.get("id", ""),
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "roleGroup": row.get("roleGroup", ""),
        "rawRole": row.get("rawRole", ""),
        "focusLabel": row.get("focusLabel", ""),
        "keywords": row.get("highlightKeywords", []) or [],
        "serviceScopeAction": row.get("serviceScopeResolvedAction", ""),
        "reason": reason,
    }


def matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text) for pattern in patterns)


def extract_specificity_candidate(row: dict) -> str:
    structured = row.get("structuredSignals", {}) if isinstance(row.get("structuredSignals", {}), dict) else {}
    confidence_notes = {clean_text(value) for value in structured.get("confidenceNotes", []) or []}
    for value in structured.get("problemSignals", []) or []:
        cleaned = clean_text(value)
        canonical = canonical_text(cleaned)
        if canonical and canonical not in SPECIFICITY_SIGNAL_BLOCKLIST:
            return cleaned
    if "missing_domain_problem_signal" not in confidence_notes:
        for value in structured.get("domainSignals", []) or []:
            cleaned = clean_text(value)
            canonical = canonical_text(cleaned)
            if canonical and canonical not in SPECIFICITY_SIGNAL_BLOCKLIST:
                return cleaned
    return ""


def collect_anomaly_families(rows: list[dict]) -> dict[str, list[dict]]:
    families = {
        "excluded_leaked_into_display": [],
        "deeptech_in_data_analyst": [],
        "deeptech_context_present": [],
        "business_in_engineer_family": [],
        "business_context_present": [],
        "tool_first_focus": [],
        "service_scope_review_in_display": [],
        "broad_focus_specificity_gap": [],
    }

    for row in rows:
        text = row_text(row)
        role = clean_text(row.get("roleGroup", ""))
        service_action = clean_text(row.get("serviceScopeResolvedAction", "")).lower()
        focus_label = canonical_text(row.get("focusLabel", ""))
        focus_dominance_text = " ".join(
            [
                clean_text(row.get("focusLabel", "")),
                " ".join((row.get("highlightKeywords", []) or [])[:1]),
            ]
        )
        specificity_candidate = extract_specificity_candidate(row)

        if not row.get("serviceScopeIncluded", True):
            families["excluded_leaked_into_display"].append(row_stub(row, "display row has serviceScopeIncluded=false"))
        if role == "데이터 분석가" and matches_any(focus_dominance_text, DEEPTECH_PATTERNS):
            families["deeptech_in_data_analyst"].append(row_stub(row, "deeptech focus dominates data analyst"))
        if role == "데이터 분석가" and matches_any(text, DEEPTECH_PATTERNS):
            families["deeptech_context_present"].append(row_stub(row, "deeptech context present under data analyst"))
        if role in {"인공지능 엔지니어", "인공지능 리서처"} and matches_any(focus_dominance_text, BUSINESS_DOMINANCE_PATTERNS):
            families["business_in_engineer_family"].append(row_stub(row, "business focus dominates engineer/research/science"))
        if role in {"인공지능 엔지니어", "인공지능 리서처"} and matches_any(text, BUSINESS_PATTERNS):
            families["business_context_present"].append(row_stub(row, "business/ops context present under engineer/research/science"))
        if focus_label in TOOL_FOCUS_LABELS:
            families["tool_first_focus"].append(row_stub(row, "focus label is a tool/framework"))
        if service_action == "review":
            families["service_scope_review_in_display"].append(row_stub(row, "review candidate still shown in main board"))
        if (
            focus_label in BROAD_FOCUS_CANONICAL
            and specificity_candidate
            and canonical_text(specificity_candidate) != focus_label
        ):
            families["broad_focus_specificity_gap"].append(
                row_stub(
                    row,
                    f"focus is broad but more specific signal exists: {specificity_candidate}",
                )
            )

    return families


def render_md(report: dict) -> str:
    lines = [
        "# Full Dataset Validation Harness",
        "",
        f"- generatedAt: `{report['generatedAt']}`",
        f"- sourceJobs: `{report['metrics']['sourceJobs']}`",
        f"- displayJobs: `{report['metrics']['displayJobs']}`",
        f"- excludedJobs: `{report['metrics']['excludedJobs']}`",
        f"- reviewJobs: `{report['metrics']['reviewJobs']}`",
        f"- summaryCoverage: `{report['metrics']['summaryCoverage']}`",
        f"- missingSummaries: `{report['metrics']['missingSummaries']}`",
        f"- staleRoleOverrides: `{report['metrics']['staleRoleOverrides']}`",
        f"- staleServiceScopeOverrides: `{report['metrics']['staleServiceScopeOverrides']}`",
        "",
        "## Anomaly Families",
        "",
    ]
    for name, family in report["families"].items():
        lines.append(f"### {name}")
        lines.append("")
        lines.append(f"- severity: `{family['severity']}`")
        lines.append(f"- count: `{family['count']}`")
        for item in family["examples"]:
            lines.append(
                f"- `{item['company']}` | `{item['title']}` | `{item['roleGroup']}` | `{item['focusLabel']}`"
                + (f" | {item['reason']}" if item.get("reason") else "")
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rebuild-board", action="store_true")
    args = parser.parse_args()

    jobs_payload = load_json(JOBS_PATH, {"jobs": []}) or {"jobs": []}
    if args.rebuild_board:
        board = build_summary_board(jobs_payload)
        write_json(SUMMARY_BOARD_PATH, board)
    else:
        board = load_json(SUMMARY_BOARD_PATH, {"rows": [], "overview": {}, "diagnostics": {}}) or {
            "rows": [],
            "overview": {},
            "diagnostics": {},
        }

    summary_store = load_summary_store().get("items", {})
    role_override_items = load_role_group_override_store().get("items", {})
    scope_override_items = load_service_scope_override_store().get("items", {})

    jobs = jobs_payload.get("jobs", [])
    jobs_by_id = {job.get("id", ""): job for job in jobs if job.get("id")}
    rows = board.get("rows", [])
    diagnostics = board.get("diagnostics", {}) if isinstance(board.get("diagnostics", {}), dict) else {}
    excluded_rows = diagnostics.get("excludedRows", []) if isinstance(diagnostics.get("excludedRows", []), list) else []
    review_rows = diagnostics.get("reviewRows", []) if isinstance(diagnostics.get("reviewRows", []), list) else []

    stale_role_ids = []
    stale_scope_ids = []
    for job_id, override in role_override_items.items():
        if not isinstance(override, dict) or not override.get("signature") or job_id not in jobs_by_id:
            continue
        actual = compute_role_group_signature(jobs_by_id[job_id], summary_store.get(job_id, {}))
        if clean_text(override.get("signature", "")) != actual:
            stale_role_ids.append(job_id)
    for job_id, override in scope_override_items.items():
        if not isinstance(override, dict) or not override.get("signature") or job_id not in jobs_by_id:
            continue
        actual = compute_service_scope_signature(jobs_by_id[job_id])
        if clean_text(override.get("signature", "")) != actual:
            stale_scope_ids.append(job_id)

    families = collect_anomaly_families(rows)

    metrics = {
        "sourceJobs": len(jobs),
        "displayJobs": len(rows),
        "excludedJobs": len(excluded_rows),
        "reviewJobs": len(review_rows),
        "summaryCoverage": (board.get("overview", {}) or {}).get("summaryCoverage"),
        "missingSummaries": (board.get("overview", {}) or {}).get("missingSummaries"),
        "staleRoleOverrides": len(stale_role_ids),
        "staleServiceScopeOverrides": len(stale_scope_ids),
    }

    report = {
        "generatedAt": now_iso(),
        "metrics": metrics,
        "staleRoleOverrideIds": stale_role_ids[:64],
        "staleServiceScopeOverrideIds": stale_scope_ids[:64],
        "families": {
            name: {
                "severity": FAMILY_SEVERITY.get(name, "info"),
                "count": len(items),
                "jobIds": [item["id"] for item in items],
                "examples": items[:12],
            }
            for name, items in families.items()
        },
        "distribution": {
            "displayRoles": Counter(row.get("roleGroup", "") for row in rows if clean_text(row.get("roleGroup", ""))),
            "excludedActions": Counter(row.get("serviceScopeAction", "") for row in excluded_rows if clean_text(row.get("serviceScopeAction", ""))),
        },
    }
    report["distribution"]["displayRoles"] = dict(report["distribution"]["displayRoles"])
    report["distribution"]["excludedActions"] = dict(report["distribution"]["excludedActions"])

    write_json(OUTPUT_JSON, report)
    write_text(OUTPUT_MD, render_md(report))

    print(json.dumps({"json": str(OUTPUT_JSON), "md": str(OUTPUT_MD), "metrics": metrics}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
