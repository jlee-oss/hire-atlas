#!/usr/bin/env python3

import csv
import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VALIDATION_JSON = ROOT / "data" / "stage2_validation_latest.json"
DEFAULT_VALIDATION_CSV = ROOT / "data" / "stage2_validation_candidates_latest.csv"
DEFAULT_OUTPUT_JSON = ROOT / "data" / "stage2_quality_triage_latest.json"
DEFAULT_OUTPUT_MD = ROOT / "docs" / "stage2_quality_triage_latest.md"

TRIAGE_GROUPS = {
    "stage2_sync": {
        "codes": {"stage2_stale", "stage2_missing", "stage2_unreadable"},
        "label": "2차 동기화 문제",
        "action": "1차 변경해시와 2차 후보가 맞지 않으므로 2차 후보를 최신 1차 기준으로 재적재해야 합니다.",
    },
    "role_mismatch": {
        "codes": {
            "data_engineering_as_ai_role",
            "data_engineering_ai_title_review",
            "business_focus_in_ai_role",
            "business_role_as_ai_role",
            "deeptech_as_analyst",
            "clinical_scientist_as_analyst",
        },
        "label": "직군/초점 재분류",
        "action": "공고를 제거하지 말고 제목, 주요업무, 자격요건을 기준으로 직군과 직무초점을 다시 산정해야 합니다.",
    },
    "signal_extraction": {
        "codes": {"missing_keywords", "missing_focus", "missing_group_summary", "noise_keyword", "duplicate_signal"},
        "label": "키워드/초점 추출 실패",
        "action": "Gemma 기반 field-aware 재추론 또는 수동 2차 보정으로 핵심기술, 직무초점, 구분요약을 채워야 합니다.",
    },
    "non_blocking_context": {
        "codes": {"business_context_in_ai_role", "summary_too_short", "role_diff", "focus_diff", "keywords_diff", "summary_diff"},
        "label": "비차단 참고 신호",
        "action": "배포 차단 신호가 아니라 검수 참고 정보로만 유지합니다.",
    },
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value) -> str:
    return " ".join(str(value or "").split()).strip()


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def issue_codes(row: dict) -> list[str]:
    raw = clean(row.get("이슈코드", ""))
    return [clean(part) for part in raw.split("|") if clean(part)]


def compact_row(row: dict) -> dict:
    return {
        "공고키": clean(row.get("공고키", "")),
        "회사명": clean(row.get("회사명_표시", "")),
        "공고제목": clean(row.get("공고제목_표시", "")),
        "검증상태": clean(row.get("검증상태", "")),
        "검증우선순위": clean(row.get("검증우선순위", "")),
        "이슈코드": clean(row.get("이슈코드", "")),
        "이슈요약": clean(row.get("이슈요약", "")),
        "stage1_분류직무": clean(row.get("stage1_분류직무", "")),
        "stage1_직무초점": clean(row.get("stage1_직무초점", "")),
        "stage1_핵심기술": clean(row.get("stage1_핵심기술", "")),
    }


def group_rows(rows: list[dict]) -> dict:
    groups = {
        key: {
            "label": value["label"],
            "action": value["action"],
            "count": 0,
            "issueCounts": Counter(),
            "examples": [],
        }
        for key, value in TRIAGE_GROUPS.items()
    }
    for row in rows:
        codes = issue_codes(row)
        for group_key, group_def in TRIAGE_GROUPS.items():
            if group_key == "non_blocking_context" and clean(row.get("검증우선순위", "")) not in {"pass", "low"}:
                continue
            matched_codes = [code for code in codes if code in group_def["codes"]]
            if not matched_codes:
                continue
            groups[group_key]["count"] += 1
            groups[group_key]["issueCounts"].update(matched_codes)
            if len(groups[group_key]["examples"]) < 12:
                groups[group_key]["examples"].append(compact_row(row))
    for item in groups.values():
        item["issueCounts"] = dict(item["issueCounts"])
    return groups


def build_report(validation: dict, rows: list[dict]) -> dict:
    state_counts = validation.get("stateCounts", {}) if isinstance(validation.get("stateCounts"), dict) else {}
    blocking_issue_counts = (
        validation.get("blockingIssueCounts", {})
        if isinstance(validation.get("blockingIssueCounts"), dict)
        else {}
    )
    return {
        "generatedAt": now_iso(),
        "metrics": validation.get("metrics", {}),
        "stateCounts": state_counts,
        "blockingIssueCounts": blocking_issue_counts,
        "severityCounts": validation.get("severityCounts", {}),
        "rowCounts": {
            "total": len(rows),
            "pending": sum(1 for row in rows if clean(row.get("검증상태", "")) == "pending"),
            "needsReview": sum(1 for row in rows if clean(row.get("검증상태", "")) == "needs_review"),
            "stale": sum(1 for row in rows if "stage2_stale" in issue_codes(row)),
            "approved": sum(1 for row in rows if clean(row.get("검증상태", "")) == "approved"),
        },
        "groups": group_rows(rows),
        "outputs": {
            "json": str(DEFAULT_OUTPUT_JSON),
            "md": str(DEFAULT_OUTPUT_MD),
        },
    }


def render_md(report: dict) -> str:
    lines = [
        "# Stage2 Quality Triage Latest",
        "",
        f"- generatedAt: `{report['generatedAt']}`",
        f"- totalRows: `{report['rowCounts']['total']}`",
        f"- pendingRows: `{report['rowCounts']['pending']}`",
        f"- needsReviewRows: `{report['rowCounts']['needsReview']}`",
        f"- staleRows: `{report['rowCounts']['stale']}`",
        "",
        "## Blocking Issue Counts",
        "",
    ]
    for key, value in sorted(report.get("blockingIssueCounts", {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Triage Groups", ""])
    for key, group in report["groups"].items():
        lines.append(f"### {group['label']}")
        lines.append("")
        lines.append(f"- groupKey: `{key}`")
        lines.append(f"- rows: `{group['count']}`")
        lines.append(f"- action: {group['action']}")
        if group["issueCounts"]:
            lines.append(f"- issueCounts: `{group['issueCounts']}`")
        if not group["examples"]:
            lines.append("- examples: none")
            lines.append("")
            continue
        lines.append("")
        for example in group["examples"]:
            lines.append(
                f"- `{example['회사명']}` | `{example['공고제목']}` | `{example['검증우선순위']}` | `{example['이슈코드']}`"
            )
        lines.append("")
    lines.extend(["## Outputs", ""])
    for key, value in report["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    validation = read_json(DEFAULT_VALIDATION_JSON)
    rows = read_csv(DEFAULT_VALIDATION_CSV)
    report = build_report(validation, rows)
    DEFAULT_OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    DEFAULT_OUTPUT_MD.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_MD.write_text(render_md(report), encoding="utf-8")
    print(
        json.dumps(
            {
                "generatedAt": report["generatedAt"],
                "rowCounts": report["rowCounts"],
                "groups": {key: value["count"] for key, value in report["groups"].items()},
                "outputs": report["outputs"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
