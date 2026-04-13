#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from ai_runtime import JOBS_PATH
from build_summary_board import build_base_rows, clean_text


ROOT = JOBS_PATH.parent.parent
DEFAULT_GOLDSET_PATH = ROOT / "data" / "review_goldset_seed_001.json"


def load_goldset(path: Path) -> list[dict]:
    data = json.loads(path.read_text(encoding="utf-8"))
    items = data.get("items", []) if isinstance(data, dict) else data
    results = []
    for item in items if isinstance(items, list) else []:
        if not isinstance(item, dict):
            continue
        expected_role = clean_text(item.get("roleGroup", ""))
        job_id = clean_text(item.get("id", ""))
        if not job_id or not expected_role:
            continue
        results.append(
            {
                "id": job_id,
                "company": clean_text(item.get("company", "")),
                "title": clean_text(item.get("title", "")),
                "expectedRoleGroup": expected_role,
            }
        )
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--goldset", default=str(DEFAULT_GOLDSET_PATH))
    args = parser.parse_args()

    payload = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    rows = build_base_rows(payload)
    rows_by_id = {row["id"]: row for row in rows}
    goldset = load_goldset(Path(args.goldset))

    matched = 0
    raw_matched = 0
    evaluated = 0
    mismatches = []
    for item in goldset:
        row = rows_by_id.get(item["id"])
        if not row:
            continue
        evaluated += 1
        expected = item["expectedRoleGroup"]
        current = clean_text(row.get("roleGroup", ""))
        raw = clean_text(row.get("rawRole", ""))
        if current == expected:
            matched += 1
        else:
            mismatches.append(
                {
                    "id": item["id"],
                    "company": item["company"],
                    "title": item["title"],
                    "expected": expected,
                    "current": current,
                    "raw": raw,
                    "roleClassifierRole": clean_text(row.get("roleClassifierRole", "")),
                    "roleClassifierReason": clean_text(row.get("roleClassifierReason", "")),
                    "roleClassifierConfidence": clean_text(row.get("roleClassifierConfidence", "")),
                }
            )
        if raw == expected:
            raw_matched += 1

    accuracy = (matched / evaluated * 100.0) if evaluated else 0.0
    raw_accuracy = (raw_matched / evaluated * 100.0) if evaluated else 0.0
    report = {
        "goldsetPath": str(args.goldset),
        "evaluated": evaluated,
        "accuracy": round(accuracy, 2),
        "rawAccuracy": round(raw_accuracy, 2),
        "improvement": round(accuracy - raw_accuracy, 2),
        "mismatches": mismatches,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
