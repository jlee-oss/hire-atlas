#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from ai_runtime import JOBS_PATH
from build_summary_board import OUTPUT_PATH as BOARD_PATH, build_summary_board
from run_full_dataset_validation_harness import FAMILY_SEVERITY, collect_anomaly_families


ROOT = JOBS_PATH.parent.parent
OUTPUT_JSON = ROOT / "data" / "harness_remediation_wave_001.json"
OUTPUT_MD = ROOT / "docs" / "harness_remediation_wave_001.md"
DEFAULT_FAMILIES = [
    "deeptech_in_data_analyst",
    "business_in_engineer_family",
    "tool_first_focus",
    "broad_focus_specificity_gap",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def compact_lines(values, limit: int = 3) -> list[str]:
    result = []
    for value in values or []:
        cleaned = " ".join(str(value or "").split()).strip()
        if not cleaned or cleaned in result:
            continue
        result.append(cleaned)
        if len(result) >= limit:
            break
    return result


def render_md(payload: dict) -> str:
    lines = [
        "# Harness Remediation Wave 001",
        "",
        f"- generatedAt: `{payload['generatedAt']}`",
        f"- boardRows: `{payload['boardRows']}`",
        f"- selectedFamilies: `{', '.join(payload['selectedFamilies'])}`",
        f"- items: `{payload['counts']['items']}`",
        "",
    ]
    for family in payload["families"]:
        lines.append(f"## {family['name']}")
        lines.append("")
        lines.append(f"- severity: `{family['severity']}`")
        lines.append(f"- count: `{family['count']}`")
        for item in family["items"][:12]:
            lines.append(
                f"- `{item['company']}` | `{item['title']}` | `{item['roleGroup']}` | `{item['focusLabel']}` | {item['reason']}"
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--families", default=",".join(DEFAULT_FAMILIES))
    parser.add_argument("--rebuild-board", action="store_true")
    args = parser.parse_args()

    jobs_payload = load_json(JOBS_PATH)
    if args.rebuild_board:
        board = build_summary_board(jobs_payload)
        write_json(BOARD_PATH, board)
    else:
        board = load_json(BOARD_PATH)

    rows = board.get("rows", [])
    jobs_by_id = {job.get("id", ""): job for job in jobs_payload.get("jobs", []) if job.get("id")}
    families = collect_anomaly_families(rows)
    selected_families = [part.strip() for part in args.families.split(",") if part.strip()]

    family_payloads = []
    total_items = 0
    for family_name in selected_families:
        items = families.get(family_name, [])
        enriched = []
        for item in items:
            row = next((row for row in rows if row.get("id") == item.get("id")), {})
            job = jobs_by_id.get(item.get("id", ""), {})
            enriched.append(
                {
                    **item,
                    "summary": row.get("summary", ""),
                    "structuredSignals": row.get("structuredSignals", {}),
                    "tasks": compact_lines(job.get("tasks", [])),
                    "requirements": compact_lines(job.get("requirements", [])),
                    "preferred": compact_lines(job.get("preferred", [])),
                    "skills": compact_lines(job.get("skills", []), limit=6),
                }
            )
        total_items += len(enriched)
        family_payloads.append(
            {
                "name": family_name,
                "severity": FAMILY_SEVERITY.get(family_name, "info"),
                "count": len(enriched),
                "jobIds": [item["id"] for item in enriched],
                "items": enriched,
            }
        )

    payload = {
        "generatedAt": now_iso(),
        "boardRows": len(rows),
        "selectedFamilies": selected_families,
        "counts": {
            "items": total_items,
        },
        "families": family_payloads,
    }
    write_json(OUTPUT_JSON, payload)
    write_text(OUTPUT_MD, render_md(payload))
    print(json.dumps({"json": str(OUTPUT_JSON), "md": str(OUTPUT_MD), "items": total_items}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
