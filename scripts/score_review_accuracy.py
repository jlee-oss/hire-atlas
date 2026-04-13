#!/usr/bin/env python3

import argparse
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE_EVAL_PATH = ROOT / "data" / "eval_set.json"
INCREMENTAL_EVAL_PATH = ROOT / "data" / "incremental_eval_set.json"
OUTPUT_PATH = ROOT / "docs" / "review_accuracy_report.md"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(numerator: int, denominator: int) -> str:
    if not denominator:
        return "0.0%"
    return f"{(numerator / denominator) * 100:.1f}%"


def reviewed_items(items: list[dict]) -> list[dict]:
    reviewed = []
    for item in items:
        review = item.get("review", {})
        if review.get("overallPass") is not None:
            reviewed.append(item)
            continue
        if any(review.get(key) is not None for key in ("summaryPass", "focusLabelPass", "keywordsPass")):
            reviewed.append(item)
            continue
        if any(
            review.get(key)
            for key in (
                "correctedSummary",
                "correctedFocusLabel",
                "correctedKeywords",
                "correctedQuality",
                "notes",
                "expectedSummary",
                "expectedFocusLabel",
                "expectedKeywords",
                "expectedQuality",
            )
        ):
            reviewed.append(item)
    return reviewed


def pass_count(items: list[dict], key: str) -> tuple[int, int]:
    total = 0
    passed = 0
    for item in items:
        review = item.get("review", {})
        value = review.get(key)
        if value is None:
            continue
        total += 1
        if value is True:
            passed += 1
    return passed, total


def summarize_dataset(label: str, payload: dict) -> dict:
    items = payload.get("items", [])
    reviewed = reviewed_items(items)
    summary_passed, summary_total = pass_count(reviewed, "summaryPass")
    focus_passed, focus_total = pass_count(reviewed, "focusLabelPass")
    keyword_passed, keyword_total = pass_count(reviewed, "keywordsPass")
    overall_passed, overall_total = pass_count(reviewed, "overallPass")
    return {
        "label": label,
        "totalItems": len(items),
        "reviewedItems": len(reviewed),
        "summary": (summary_passed, summary_total),
        "focusLabel": (focus_passed, focus_total),
        "keywords": (keyword_passed, keyword_total),
        "overall": (overall_passed, overall_total),
    }


def build_report(core: dict, incremental: dict) -> str:
    lines = ["# 리뷰 정확도 리포트", ""]
    for dataset in (core, incremental):
        lines.extend(
            [
                f"## {dataset['label']}",
                "",
                f"- 전체 항목: `{dataset['totalItems']}`",
                f"- 검수된 항목: `{dataset['reviewedItems']}`",
                f"- summary pass: `{dataset['summary'][0]}/{dataset['summary'][1]}` (`{pct(dataset['summary'][0], dataset['summary'][1])}`)",
                f"- focusLabel pass: `{dataset['focusLabel'][0]}/{dataset['focusLabel'][1]}` (`{pct(dataset['focusLabel'][0], dataset['focusLabel'][1])}`)",
                f"- keywords pass: `{dataset['keywords'][0]}/{dataset['keywords'][1]}` (`{pct(dataset['keywords'][0], dataset['keywords'][1])}`)",
                f"- overall pass: `{dataset['overall'][0]}/{dataset['overall'][1]}` (`{pct(dataset['overall'][0], dataset['overall'][1])}`)",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    core = summarize_dataset("core eval", load_json(CORE_EVAL_PATH))
    incremental = summarize_dataset("incremental holdout", load_json(INCREMENTAL_EVAL_PATH))
    content = build_report(core, incremental)
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(content)
    print(f"Wrote review accuracy report to {output_path}")


if __name__ == "__main__":
    main()
