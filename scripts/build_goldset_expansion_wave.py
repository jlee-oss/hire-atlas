#!/usr/bin/env python3

import csv
import json
import pathlib
from collections import Counter, defaultdict
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
CANDIDATES_PATH = ROOT / "data" / "goldset_expansion_candidates.json"
OUTPUT_JSON_PATH = ROOT / "data" / "goldset_expansion_wave_001.json"
OUTPUT_CSV_PATH = ROOT / "data" / "goldset_expansion_wave_001.csv"
OUTPUT_MD_PATH = ROOT / "docs" / "goldset_expansion_wave_001.md"

TARGET_BY_BUCKET = {
    "broad_focus": 20,
    "domain_specific": 12,
    "low_or_empty": 10,
    "focus_keyword_conflict": 6,
}


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def score_row(row: dict, company_counts: Counter) -> tuple:
    quality = clean(row.get("quality", "")).lower()
    quality_rank = {"low": 0, "medium": 1, "high": 2}.get(quality, 3)
    keyword_count = len(row.get("keywords", []) or [])
    company_density = company_counts[clean(row.get("company", ""))]
    focus = clean(row.get("focusLabel", ""))
    return (quality_rank, company_density, -keyword_count, focus, clean(row.get("title", "")))


def pick_balanced(rows: list[dict], target: int) -> list[dict]:
    company_counts = Counter(clean(row.get("company", "")) for row in rows)
    rows_sorted = sorted(rows, key=lambda row: score_row(row, company_counts))

    picked = []
    seen_ids = set()
    seen_company = Counter()
    seen_role = Counter()

    for row in rows_sorted:
        if len(picked) >= target:
            break
        row_id = row.get("id")
        if row_id in seen_ids:
            continue
        company = clean(row.get("company", ""))
        role = clean(row.get("roleDisplay", ""))

        if seen_company[company] >= 2:
            continue
        if role and seen_role[role] >= max(4, target // 3):
            continue

        picked.append(row)
        seen_ids.add(row_id)
        seen_company[company] += 1
        if role:
            seen_role[role] += 1

    if len(picked) < target:
        for row in rows_sorted:
            if len(picked) >= target:
                break
            row_id = row.get("id")
            if row_id in seen_ids:
                continue
            picked.append(row)
            seen_ids.add(row_id)

    return picked


def main() -> None:
    payload = load_json(CANDIDATES_PATH)
    candidates = payload.get("items", [])

    bucketed = defaultdict(list)
    for row in candidates:
        bucketed[clean(row.get("reason", ""))].append(row)

    selected = []
    for bucket, target in TARGET_BY_BUCKET.items():
        selected.extend(pick_balanced(bucketed.get(bucket, []), target))

    selected = sorted(
        selected,
        key=lambda row: (
            clean(row.get("reason", "")),
            clean(row.get("roleDisplay", "")),
            clean(row.get("company", "")),
            clean(row.get("title", "")),
        ),
    )

    output_payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(selected),
        "items": selected,
    }
    OUTPUT_JSON_PATH.write_text(
        json.dumps(output_payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    with OUTPUT_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "reason",
                "company",
                "title",
                "roleDisplay",
                "summary",
                "focusLabel",
                "keywords",
                "quality",
            ],
        )
        writer.writeheader()
        for row in selected:
            writer.writerow(
                {
                    "id": row.get("id", ""),
                    "reason": row.get("reason", ""),
                    "company": row.get("company", ""),
                    "title": row.get("title", ""),
                    "roleDisplay": row.get("roleDisplay", ""),
                    "summary": row.get("summary", ""),
                    "focusLabel": row.get("focusLabel", ""),
                    "keywords": " | ".join(row.get("keywords", []) or []),
                    "quality": row.get("quality", ""),
                }
            )

    reason_counts = Counter(clean(row.get("reason", "")) for row in selected)
    role_counts = Counter(clean(row.get("roleDisplay", "")) for row in selected)
    lines = [
        "# 골드셋 확장 웨이브 001",
        "",
        f"- 총 항목: `{len(selected)}`",
        "",
        "## 분포",
        "",
    ]
    for reason, count in sorted(reason_counts.items()):
        lines.append(f"- `{reason}`: `{count}`")
    lines.append("")
    lines.append("## 직무 분포")
    lines.append("")
    for role, count in role_counts.most_common():
        lines.append(f"- `{role or '-'}`: `{count}`")
    lines.append("")

    grouped = defaultdict(list)
    for row in selected:
        grouped[clean(row.get("reason", ""))].append(row)

    for reason in sorted(grouped):
        lines.append(f"## {reason}")
        lines.append("")
        for row in grouped[reason]:
            focus = clean(row.get("focusLabel", "")) or "-"
            lines.append(
                f"- `{row.get('company', '')}` | `{row.get('title', '')}` | `{focus}`"
            )
        lines.append("")

    OUTPUT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")

    print(f"Wrote JSON to {OUTPUT_JSON_PATH}")
    print(f"Wrote CSV to {OUTPUT_CSV_PATH}")
    print(f"Wrote markdown to {OUTPUT_MD_PATH}")


if __name__ == "__main__":
    main()
