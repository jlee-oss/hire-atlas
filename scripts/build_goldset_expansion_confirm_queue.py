#!/usr/bin/env python3

import argparse
import csv
import pathlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = ROOT / "data" / "goldset_expansion_decision_sheet_001.csv"
DEFAULT_CSV_OUTPUT = ROOT / "data" / "goldset_expansion_confirm_queue_001.csv"
DEFAULT_MD_OUTPUT = ROOT / "docs" / "goldset_expansion_confirm_queue_001.md"

PRIORITY_DECISIONS = {"needs_edit", "approve_current"}


def load_rows(path: pathlib.Path) -> list[dict]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: pathlib.Path, rows: list[dict], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def build_markdown(rows: list[dict]) -> str:
    decision_counts = Counter(row["recommendedDecision"] for row in rows)
    lines = [
        "# 골드셋 확장 확인 큐 001",
        "",
        f"- 우선 확인 대상: `{len(rows)}`",
        "- 기준: `needs_edit` 또는 `approve_current` 추천 항목",
        "",
        "## 추천 분포",
        "",
    ]
    for key, count in sorted(decision_counts.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.append("")

    for row in rows:
        lines.append(
            f"- `{row['company']}` | `{row['title']}` | raw `{row['currentFocusLabel'] or '-'}` -> board `{row['draftFocusLabel'] or '-'}` | 권장 `{row['recommendedDecision']}`"
        )
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH))
    parser.add_argument("--csv-output", default=str(DEFAULT_CSV_OUTPUT))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_OUTPUT))
    args = parser.parse_args()

    input_path = pathlib.Path(args.input)
    rows = load_rows(input_path)
    filtered = [row for row in rows if row.get("recommendedDecision", "") in PRIORITY_DECISIONS]

    csv_output = pathlib.Path(args.csv_output)
    fieldnames = list(rows[0].keys()) if rows else []
    write_csv(csv_output, filtered, fieldnames)

    md_output = pathlib.Path(args.md_output)
    md_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.write_text(build_markdown(filtered) + "\n", encoding="utf-8")

    print(f"Wrote confirm queue CSV to {csv_output}")
    print(f"Wrote confirm queue markdown to {md_output}")


if __name__ == "__main__":
    main()
