#!/usr/bin/env python3

import argparse
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE_EVAL_PATH = ROOT / "data" / "eval_set.json"
INCREMENTAL_EVAL_PATH = ROOT / "data" / "incremental_eval_set.json"
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def has_review_content(review: dict) -> bool:
    if review.get("overallPass") is not None:
        return True
    return any(
        review.get(key)
        for key in (
            "summaryPass",
            "focusLabelPass",
            "keywordsPass",
            "correctedSummary",
            "correctedFocusLabel",
            "correctedKeywords",
            "correctedQuality",
            "notes",
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    args = parser.parse_args()

    wave = load_json(pathlib.Path(args.wave))
    core_eval = load_json(CORE_EVAL_PATH)
    incremental_eval = load_json(INCREMENTAL_EVAL_PATH)

    targets = {
        "core": {item["id"]: item for item in core_eval.get("items", [])},
        "incremental": {item["id"]: item for item in incremental_eval.get("items", [])},
    }

    updated_counts = {"core": 0, "incremental": 0}
    for item in wave.get("items", []):
        dataset = item.get("sourceDataset")
        review = item.get("review", {})
        if dataset not in targets or not has_review_content(review):
            continue
        target = targets[dataset].get(item["id"])
        if not target:
            continue
        target["review"] = review
        updated_counts[dataset] += 1

    write_json(CORE_EVAL_PATH, core_eval)
    write_json(INCREMENTAL_EVAL_PATH, incremental_eval)
    print(f"Applied review wave: core={updated_counts['core']} incremental={updated_counts['incremental']}")


if __name__ == "__main__":
    main()
