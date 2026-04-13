#!/usr/bin/env python3

import json
from collections import Counter

from ai_runtime import JOBS_PATH
from build_summary_board import build_base_rows, explain_service_scope_row


OUTPUT_PATH = JOBS_PATH.parent / "service_scope_audit.json"


def compact_row(row: dict, decision: dict) -> dict:
    return {
        "id": row.get("id", ""),
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "roleGroup": row.get("roleGroup", ""),
        "summaryQuality": row.get("summaryQuality", ""),
        "focusLabel": row.get("focusLabel", ""),
        "summary": row.get("summary", ""),
        "action": decision.get("action", "exclude"),
        "reasons": [reason.get("label", "") for reason in decision.get("reasons", [])],
    }


def main():
    payload = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    rows = build_base_rows(payload)

    included = []
    excluded = []
    for row in rows:
        decision = explain_service_scope_row(row)
        item = compact_row(row, decision)
        if decision.get("included"):
            included.append(item)
        else:
            excluded.append(item)

    actions = Counter(item["action"] for item in excluded)
    reason_counts = Counter(item["reasons"][0] for item in excluded if item.get("reasons"))
    quality_counts = Counter(item["summaryQuality"] for item in excluded)

    audit = {
        "generatedAt": payload.get("generatedAt"),
        "source": payload.get("source", {}),
        "counts": {
            "included": len(included),
            "excluded": len(excluded),
            "reviewCandidates": actions.get("review", 0),
            "strongExcludes": actions.get("exclude", 0),
        },
        "excludedQualityCounts": dict(sorted(quality_counts.items())),
        "primaryReasonCounts": dict(reason_counts.most_common()),
        "reviewCandidates": [item for item in excluded if item["action"] == "review"],
        "excludedItems": excluded,
    }

    OUTPUT_PATH.write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote service scope audit to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
