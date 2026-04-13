#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib
from collections import Counter
from copy import deepcopy


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_DECISION_CSV_PATH = ROOT / "data" / "review_decision_sheet_001.csv"
CORE_EVAL_PATH = ROOT / "data" / "eval_set.json"
INCREMENTAL_EVAL_PATH = ROOT / "data" / "incremental_eval_set.json"
DEFAULT_OUTPUT_PATH = ROOT / "docs" / "provisional_review_report.md"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_keywords(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").split("|") if part.strip()]


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
            )
        ):
            reviewed.append(item)
    return reviewed


def pass_count(items: list[dict], key: str) -> tuple[int, int]:
    total = 0
    passed = 0
    for item in items:
        value = item.get("review", {}).get(key)
        if value is None:
            continue
        total += 1
        if value is True:
            passed += 1
    return passed, total


def pct(n: int, d: int) -> str:
    if not d:
        return "0.0%"
    return f"{(n / d) * 100:.1f}%"


def approved_current_review(item: dict, notes: str) -> dict:
    current = item.get("current", {})
    return {
        "summaryPass": True,
        "focusLabelPass": True,
        "keywordsPass": True,
        "overallPass": True,
        "correctedSummary": "",
        "correctedFocusLabel": "",
        "correctedKeywords": [],
        "correctedQuality": current.get("quality", ""),
        "notes": notes or "현재 모델 출력을 유지합니다.",
    }


def apply_decisions_to_wave(wave: dict, decision_csv: pathlib.Path) -> tuple[dict, Counter]:
    shadow = deepcopy(wave)
    items_by_id = {item["id"]: item for item in shadow.get("items", [])}
    stats = Counter()

    with decision_csv.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            item = items_by_id.get(row.get("id", ""))
            if not item:
                continue
            decision = (row.get("decision") or row.get("recommendedDecision") or "").strip().lower()
            notes = str(row.get("confirmNotes", "")).strip()

            if decision in {"approve_draft", "approve_low"}:
                draft = item.get("assistantReviewDraft")
                if not draft:
                    stats["unresolved"] += 1
                    continue
                item["review"] = {
                    "summaryPass": draft.get("summaryPass"),
                    "focusLabelPass": draft.get("focusLabelPass"),
                    "keywordsPass": draft.get("keywordsPass"),
                    "overallPass": draft.get("overallPass"),
                    "correctedSummary": draft.get("correctedSummary", ""),
                    "correctedFocusLabel": draft.get("correctedFocusLabel", ""),
                    "correctedKeywords": draft.get("correctedKeywords", []),
                    "correctedQuality": draft.get("correctedQuality", ""),
                    "notes": notes or draft.get("notes", ""),
                }
                stats[decision] += 1
                continue

            if decision == "approve_current":
                item["review"] = approved_current_review(item, notes)
                stats[decision] += 1
                continue

            if decision == "needs_edit":
                manual_summary = str(row.get("manualSummary", "")).strip()
                manual_focus = str(row.get("manualFocusLabel", "")).strip()
                manual_keywords = parse_keywords(row.get("manualKeywords", ""))
                manual_quality = str(row.get("manualQuality", "")).strip()
                if not any([manual_summary, manual_focus, manual_keywords, manual_quality]):
                    stats["unresolved"] += 1
                    continue
                item["review"] = {
                    "summaryPass": False,
                    "focusLabelPass": False,
                    "keywordsPass": False,
                    "overallPass": False,
                    "correctedSummary": manual_summary,
                    "correctedFocusLabel": manual_focus,
                    "correctedKeywords": manual_keywords,
                    "correctedQuality": manual_quality,
                    "notes": notes or "수동 수정안 반영",
                }
                stats[decision] += 1
                continue

            stats["unresolved"] += 1
    return shadow, stats


def merge_shadow_reviews(wave: dict, core_eval: dict, incremental_eval: dict) -> tuple[dict, dict]:
    core_shadow = deepcopy(core_eval)
    incremental_shadow = deepcopy(incremental_eval)
    targets = {
        "core": {item["id"]: item for item in core_shadow.get("items", [])},
        "incremental": {item["id"]: item for item in incremental_shadow.get("items", [])},
    }
    for item in wave.get("items", []):
        dataset = item.get("sourceDataset")
        review = item.get("review", {})
        if dataset not in targets:
            continue
        target = targets[dataset].get(item["id"])
        if not target:
            continue
        target["review"] = review
    return core_shadow, incremental_shadow


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


def build_report(stats: Counter, core: dict, incremental: dict) -> str:
    lines = [
        "# Provisional Review Report",
        "",
        "- 이 문서는 `review_decision_sheet_001.csv`의 현재 결정값을 **가정 적용**했을 때의 미리보기입니다.",
        "- 실제 사람 검수 완료로 간주하면 안 됩니다.",
        "",
        "## 결정 시트 적용 가정",
        "",
        f"- `approve_draft`: `{stats.get('approve_draft', 0)}`",
        f"- `approve_low`: `{stats.get('approve_low', 0)}`",
        f"- `approve_current`: `{stats.get('approve_current', 0)}`",
        f"- `needs_edit`: `{stats.get('needs_edit', 0)}`",
        f"- unresolved: `{stats.get('unresolved', 0)}`",
        "",
    ]
    for dataset in (core, incremental):
        lines.extend(
            [
                f"## {dataset['label']}",
                "",
                f"- 전체 항목: `{dataset['totalItems']}`",
                f"- provisional reviewed: `{dataset['reviewedItems']}`",
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
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--decision-csv", default=str(DEFAULT_DECISION_CSV_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    args = parser.parse_args()

    wave = load_json(pathlib.Path(args.wave))
    core_eval = load_json(CORE_EVAL_PATH)
    incremental_eval = load_json(INCREMENTAL_EVAL_PATH)

    shadow_wave, stats = apply_decisions_to_wave(wave, pathlib.Path(args.decision_csv))
    core_shadow, incremental_shadow = merge_shadow_reviews(shadow_wave, core_eval, incremental_eval)

    core_summary = summarize_dataset("core eval (provisional)", core_shadow)
    incremental_summary = summarize_dataset("incremental holdout (provisional)", incremental_shadow)

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_report(stats, core_summary, incremental_summary), encoding="utf-8")
    print(f"Wrote provisional review report to {output_path}")


if __name__ == "__main__":
    main()
