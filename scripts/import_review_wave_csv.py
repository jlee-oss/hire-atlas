#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_CSV_PATH = ROOT / "data" / "review_wave_001.csv"


TRUE_VALUES = {"true", "1", "yes", "y", "pass", "ok"}
FALSE_VALUES = {"false", "0", "no", "n", "fail", "x"}


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def parse_bool(value: str):
    normalized = str(value or "").strip().lower()
    if not normalized:
        return None
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


def parse_keywords(value: str) -> list[str]:
    return [item.strip() for item in str(value or "").split("|") if item.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH))
    args = parser.parse_args()

    wave_path = pathlib.Path(args.wave)
    csv_path = pathlib.Path(args.csv)

    wave = load_json(wave_path)
    items_by_id = {item["id"]: item for item in wave.get("items", [])}
    updated = 0

    with csv_path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item = items_by_id.get(row.get("id", ""))
            if not item:
                continue
            review = item.setdefault("review", {})
            review["summaryPass"] = parse_bool(row.get("reviewSummaryPass"))
            review["focusLabelPass"] = parse_bool(row.get("reviewFocusLabelPass"))
            review["keywordsPass"] = parse_bool(row.get("reviewKeywordsPass"))
            review["overallPass"] = parse_bool(row.get("reviewOverallPass"))
            review["correctedSummary"] = str(row.get("correctedSummary", "")).strip()
            review["correctedFocusLabel"] = str(row.get("correctedFocusLabel", "")).strip()
            review["correctedKeywords"] = parse_keywords(row.get("correctedKeywords", ""))
            review["correctedQuality"] = str(row.get("correctedQuality", "")).strip()
            review["notes"] = str(row.get("reviewNotes", "")).strip()
            updated += 1

    write_json(wave_path, wave)
    print(f"Imported CSV review data into {wave_path} ({updated} rows scanned)")


if __name__ == "__main__":
    main()
