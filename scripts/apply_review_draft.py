#!/usr/bin/env python3

import argparse
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_DRAFT_PATH = ROOT / "data" / "review_draft_001.json"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--draft", default=str(DEFAULT_DRAFT_PATH))
    args = parser.parse_args()

    wave_path = pathlib.Path(args.wave)
    draft_path = pathlib.Path(args.draft)

    wave = load_json(wave_path)
    draft = load_json(draft_path)
    draft_items = {item["id"]: item.get("assistantReviewDraft", {}) for item in draft.get("items", [])}

    applied = 0
    for item in wave.get("items", []):
        suggestion = draft_items.get(item.get("id"))
        if not suggestion:
            continue
        item["assistantReviewDraft"] = {
            "summaryPass": suggestion.get("summaryPass"),
            "focusLabelPass": suggestion.get("focusLabelPass"),
            "keywordsPass": suggestion.get("keywordsPass"),
            "overallPass": suggestion.get("overallPass"),
            "correctedSummary": suggestion.get("correctedSummary", ""),
            "correctedFocusLabel": suggestion.get("correctedFocusLabel", ""),
            "correctedKeywords": suggestion.get("correctedKeywords", []),
            "correctedQuality": suggestion.get("correctedQuality", ""),
            "notes": suggestion.get("notes", ""),
        }
        applied += 1

    wave.setdefault("draft", {})
    wave["draft"]["sourcePath"] = str(draft_path)
    wave["draft"]["appliedCount"] = applied
    write_json(wave_path, wave)
    print(f"Applied assistant review draft to {wave_path} ({applied} items)")


if __name__ == "__main__":
    main()
