#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib
from collections import defaultdict

from ai_runtime import build_structured_signals, get_jobs_payload, load_summary_store


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_REVIEW_PATH = ROOT / "data" / "goldset_expansion_review_001.json"
DEFAULT_JSON_OUTPUT = ROOT / "data" / "structured_signal_validation_wave_001.json"
DEFAULT_CSV_OUTPUT = ROOT / "data" / "structured_signal_validation_wave_001.csv"
DEFAULT_MD_OUTPUT = ROOT / "docs" / "structured_signal_validation_wave_001.md"

TARGET_BY_REASON = {
    "broad_focus": 8,
    "domain_specific": 5,
    "low_or_empty": 4,
    "focus_keyword_conflict": 3,
}


def clean_list(values):
    result = []
    for value in values or []:
        cleaned = str(value or "").strip()
        if not cleaned or cleaned in result:
            continue
        result.append(cleaned)
    return result


def stringify(values):
    return " | ".join(clean_list(values))


def make_wave_item(review_item: dict, job: dict, current_item: dict) -> dict:
    expected = review_item.get("expected", {})
    current_signals = current_item.get("structuredSignals", {}) or {}
    expected_projection = {
        "summary": expected.get("summary", ""),
        "focusLabel": expected.get("focusLabel", ""),
        "keywords": expected.get("keywords", []) or [],
        "quality": expected.get("quality", "low"),
        "role": current_item.get("role", "") or job.get("roleDisplay", ""),
    }
    suggested_expected = build_structured_signals(job, expected_projection)

    recommended = "approve_suggested"
    if expected.get("quality") == "low":
        recommended = "approve_low"

    return {
        "id": review_item["id"],
        "reason": review_item.get("reason", ""),
        "company": review_item.get("company", ""),
        "title": review_item.get("title", ""),
        "roleDisplay": review_item.get("roleDisplay", ""),
        "currentSummary": current_item.get("summary", ""),
        "expectedSummary": expected.get("summary", ""),
        "currentFocusLabel": current_item.get("focusLabel", ""),
        "expectedFocusLabel": expected.get("focusLabel", ""),
        "currentQuality": current_item.get("quality", ""),
        "expectedQuality": expected.get("quality", ""),
        "currentDomainSignals": clean_list(current_signals.get("domainSignals", [])),
        "currentProblemSignals": clean_list(current_signals.get("problemSignals", [])),
        "currentSystemSignals": clean_list(current_signals.get("systemSignals", [])),
        "currentDataSignals": clean_list(current_signals.get("dataSignals", [])),
        "currentWorkflowSignals": clean_list(current_signals.get("workflowSignals", [])),
        "suggestedDomainSignals": clean_list(suggested_expected.get("domainSignals", [])),
        "suggestedProblemSignals": clean_list(suggested_expected.get("problemSignals", [])),
        "suggestedSystemSignals": clean_list(suggested_expected.get("systemSignals", [])),
        "suggestedDataSignals": clean_list(suggested_expected.get("dataSignals", [])),
        "suggestedWorkflowSignals": clean_list(suggested_expected.get("workflowSignals", [])),
        "recommendedDecision": recommended,
        "decision": recommended,
        "manualDomainSignals": "",
        "manualProblemSignals": "",
        "manualSystemSignals": "",
        "manualDataSignals": "",
        "manualWorkflowSignals": "",
        "notes": "",
    }


def select_items(review_items: list[dict], limit: int) -> list[dict]:
    buckets = defaultdict(list)
    for item in review_items:
        buckets[item.get("reason", "other")].append(item)

    selected = []
    seen = set()
    for reason, target in TARGET_BY_REASON.items():
        for item in buckets.get(reason, [])[:target]:
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            selected.append(item)

    if len(selected) < limit:
        for item in review_items:
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            selected.append(item)
            if len(selected) >= limit:
                break

    return selected[:limit]


def write_csv(path: pathlib.Path, rows: list[dict]) -> None:
    fieldnames = [
        "id",
        "reason",
        "company",
        "title",
        "roleDisplay",
        "currentSummary",
        "expectedSummary",
        "currentFocusLabel",
        "expectedFocusLabel",
        "currentQuality",
        "expectedQuality",
        "currentDomainSignals",
        "currentProblemSignals",
        "currentSystemSignals",
        "currentDataSignals",
        "currentWorkflowSignals",
        "suggestedDomainSignals",
        "suggestedProblemSignals",
        "suggestedSystemSignals",
        "suggestedDataSignals",
        "suggestedWorkflowSignals",
        "recommendedDecision",
        "decision",
        "manualDomainSignals",
        "manualProblemSignals",
        "manualSystemSignals",
        "manualDataSignals",
        "manualWorkflowSignals",
        "notes",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            serializable = {}
            for key in fieldnames:
                value = row.get(key, "")
                serializable[key] = stringify(value) if isinstance(value, list) else value
            writer.writerow(serializable)


def write_md(path: pathlib.Path, rows: list[dict]) -> None:
    lines = [
        "# Structured Signal 검증 웨이브 001",
        "",
        f"- 총 검증 대상: `{len(rows)}건`",
        "- 목적: `summary/focusLabel` 아래의 structuredSignals(domain/problem/system 중심)를 최소 샘플로 검증",
        "- 확인 우선: `problemSignals -> domainSignals -> systemSignals`",
        "- decision:",
        "  - `approve_suggested`: suggested 신호를 채택",
        "  - `approve_low`: low 유지",
        "  - `approve_current`: 현재 structuredSignals 유지",
        "  - `needs_edit`: 직접 수정",
        "",
        "## 샘플",
        "",
    ]
    for item in rows[:10]:
        lines.extend(
            [
                f"- `{item['company']} | {item['title']}`",
                f"  - reason: `{item['reason']}`",
                f"  - expected focus: `{item['expectedFocusLabel']}`",
                f"  - current problem/domain/system: `{stringify(item['currentProblemSignals'])}` / `{stringify(item['currentDomainSignals'])}` / `{stringify(item['currentSystemSignals'])}`",
                f"  - suggested problem/domain/system: `{stringify(item['suggestedProblemSignals'])}` / `{stringify(item['suggestedDomainSignals'])}` / `{stringify(item['suggestedSystemSignals'])}`",
            ]
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--review", default=str(DEFAULT_REVIEW_PATH))
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT))
    parser.add_argument("--csv-output", default=str(DEFAULT_CSV_OUTPUT))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_OUTPUT))
    args = parser.parse_args()

    review_payload = json.loads(pathlib.Path(args.review).read_text(encoding="utf-8"))
    review_items = review_payload.get("items", [])
    selected = select_items(review_items, args.limit)

    jobs_payload = get_jobs_payload()
    jobs_by_id = {job["id"]: job for job in jobs_payload.get("jobs", [])}
    summary_store = load_summary_store().get("items", {})

    rows = []
    for item in selected:
        job = jobs_by_id.get(item["id"])
        current = summary_store.get(item["id"])
        if not job or not current:
            continue
        rows.append(make_wave_item(item, job, current))

    output_payload = {
        "generatedAt": review_payload.get("generatedAt"),
        "sourceReviewPath": str(pathlib.Path(args.review)),
        "count": len(rows),
        "items": rows,
    }

    json_path = pathlib.Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    write_csv(pathlib.Path(args.csv_output), rows)
    write_md(pathlib.Path(args.md_output), rows)

    print(f"Wrote structured signal validation JSON to {args.json_output}")
    print(f"Wrote structured signal validation CSV to {args.csv_output}")
    print(f"Wrote structured signal validation MD to {args.md_output}")


if __name__ == "__main__":
    main()
