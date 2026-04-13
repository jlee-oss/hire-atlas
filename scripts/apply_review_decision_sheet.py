#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_CSV_PATH = ROOT / "data" / "review_decision_sheet_001.csv"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_keywords(value: str) -> list[str]:
    return [part.strip() for part in str(value or "").split("|") if part.strip()]


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


def manual_review(row: dict, notes: str) -> dict:
    return {
        "summaryPass": False,
        "focusLabelPass": False,
        "keywordsPass": False,
        "overallPass": False,
        "correctedSummary": str(row.get("manualSummary", "")).strip(),
        "correctedFocusLabel": str(row.get("manualFocusLabel", "")).strip(),
        "correctedKeywords": parse_keywords(row.get("manualKeywords", "")),
        "correctedQuality": str(row.get("manualQuality", "")).strip(),
        "notes": notes or "수동 수정안 반영",
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH))
    args = parser.parse_args()

    wave_path = pathlib.Path(args.wave)
    csv_path = pathlib.Path(args.csv)

    wave = load_json(wave_path)
    items_by_id = {item["id"]: item for item in wave.get("items", [])}

    applied = 0
    unresolved = 0

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item = items_by_id.get(row.get("id", ""))
            if not item:
                continue
            decision = (row.get("decision") or row.get("recommendedDecision") or "").strip().lower()
            notes = str(row.get("confirmNotes", "")).strip()

            if decision in {"approve_draft", "approve_low"}:
                draft = item.get("assistantReviewDraft")
                if not draft:
                    unresolved += 1
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
                applied += 1
                continue

            if decision == "approve_current":
                item["review"] = approved_current_review(item, notes)
                applied += 1
                continue

            if decision == "needs_edit":
                manual = manual_review(row, notes)
                if not any(
                    [
                        manual["correctedSummary"],
                        manual["correctedFocusLabel"],
                        manual["correctedKeywords"],
                        manual["correctedQuality"],
                    ]
                ):
                    unresolved += 1
                    continue
                item["review"] = manual
                applied += 1
                continue

            if decision == "skip" or not decision:
                unresolved += 1
                continue

            unresolved += 1

    wave.setdefault("confirmSheet", {})
    wave["confirmSheet"]["sourcePath"] = str(csv_path)
    wave["confirmSheet"]["appliedCount"] = applied
    wave["confirmSheet"]["unresolvedCount"] = unresolved
    write_json(wave_path, wave)
    print(f"Applied review decision sheet to {wave_path} (applied={applied}, unresolved={unresolved})")


if __name__ == "__main__":
    main()
