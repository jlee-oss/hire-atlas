#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "goldset_expansion_wave_001.json"
DEFAULT_CSV_PATH = ROOT / "data" / "goldset_expansion_decision_sheet_001.csv"
DEFAULT_SUMMARIES_PATH = ROOT / "data" / "job_summaries.json"
DEFAULT_BOARD_PATH = ROOT / "data" / "summary_board.json"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "goldset_expansion_review_001.json"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def parse_keywords(value: str) -> list[str]:
    if isinstance(value, list):
        return [clean(item) for item in value if clean(item)]
    return [clean(part) for part in str(value or "").split("|") if clean(part)]


def chosen_payload(decision: str, row: dict, raw: dict, draft: dict) -> tuple[dict | None, bool]:
    decision = clean(decision).lower()
    if decision == "approve_draft":
        return (
            {
                "summary": clean(draft.get("summary", "")),
                "focusLabel": clean(draft.get("focusLabel", "")),
                "keywords": parse_keywords(draft.get("highlightKeywords", [])),
                "quality": clean(draft.get("summaryQuality", "")),
            },
            True,
        )
    if decision == "approve_current":
        return (
            {
                "summary": clean(raw.get("summary", "")),
                "focusLabel": clean(raw.get("focusLabel", "")),
                "keywords": parse_keywords(raw.get("keywords", [])),
                "quality": clean(raw.get("quality", "")),
            },
            True,
        )
    if decision == "approve_low":
        return (
            {
                "summary": "",
                "focusLabel": "",
                "keywords": [],
                "quality": "low",
            },
            True,
        )
    if decision == "needs_edit":
        payload = {
            "summary": clean(row.get("manualSummary", "")),
            "focusLabel": clean(row.get("manualFocusLabel", "")),
            "keywords": parse_keywords(row.get("manualKeywords", "")),
            "quality": clean(row.get("manualQuality", "")),
        }
        has_content = any([payload["summary"], payload["focusLabel"], payload["keywords"], payload["quality"]])
        return (payload if has_content else None, has_content)
    return None, False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH))
    parser.add_argument("--summaries", default=str(DEFAULT_SUMMARIES_PATH))
    parser.add_argument("--board", default=str(DEFAULT_BOARD_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    args = parser.parse_args()

    wave = load_json(pathlib.Path(args.wave))
    summaries = load_json(pathlib.Path(args.summaries))
    board = load_json(pathlib.Path(args.board))
    summary_items = summaries.get("items", {})
    board_rows = {row["id"]: row for row in board.get("rows", [])}
    wave_items = {item["id"]: item for item in wave.get("items", [])}

    reviewed_items = []
    applied = 0
    unresolved = 0

    with pathlib.Path(args.csv).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item_id = row.get("id", "")
            wave_item = wave_items.get(item_id, {})
            raw = summary_items.get(item_id, {})
            draft = board_rows.get(item_id, {})
            decision = row.get("decision") or row.get("recommendedDecision") or ""
            expected, resolved = chosen_payload(decision, row, raw, draft)
            if resolved and expected is not None:
                applied += 1
            else:
                unresolved += 1

            reviewed_items.append(
                {
                    "id": item_id,
                    "reason": clean(row.get("reason", "")) or clean(wave_item.get("reason", "")),
                    "company": clean(row.get("company", "")) or clean(wave_item.get("company", "")),
                    "title": clean(row.get("title", "")) or clean(wave_item.get("title", "")),
                    "roleDisplay": clean(row.get("roleDisplay", "")) or clean(wave_item.get("roleDisplay", "")),
                    "current": {
                        "summary": clean(raw.get("summary", "")),
                        "focusLabel": clean(raw.get("focusLabel", "")),
                        "keywords": parse_keywords(raw.get("keywords", [])),
                        "quality": clean(raw.get("quality", "")),
                    },
                    "draft": {
                        "summary": clean(draft.get("summary", "")),
                        "focusLabel": clean(draft.get("focusLabel", "")),
                        "keywords": parse_keywords(draft.get("highlightKeywords", [])),
                        "quality": clean(draft.get("summaryQuality", "")),
                    },
                    "decision": clean(decision),
                    "recommendedDecision": clean(row.get("recommendedDecision", "")),
                    "assistantNotes": clean(row.get("assistantNotes", "")),
                    "confirmNotes": clean(row.get("confirmNotes", "")),
                    "resolved": resolved,
                    "expected": expected or {
                        "summary": "",
                        "focusLabel": "",
                        "keywords": [],
                        "quality": "",
                    },
                }
            )

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceWavePath": str(pathlib.Path(args.wave)),
        "sourceDecisionSheetPath": str(pathlib.Path(args.csv)),
        "count": len(reviewed_items),
        "resolvedCount": applied,
        "unresolvedCount": unresolved,
        "items": reviewed_items,
    }
    write_json(pathlib.Path(args.output), payload)
    print(
        f"Wrote goldset expansion review set to {args.output} "
        f"(resolved={applied}, unresolved={unresolved})"
    )


if __name__ == "__main__":
    main()
