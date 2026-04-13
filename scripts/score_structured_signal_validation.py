#!/usr/bin/env python3

import argparse
import json
import pathlib
from statistics import mean


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = ROOT / "data" / "structured_signal_validation_review_001.json"
DEFAULT_JSON_OUTPUT = ROOT / "data" / "structured_signal_validation_score_001.json"
DEFAULT_MD_OUTPUT = ROOT / "docs" / "structured_signal_validation_score_001.md"

CATEGORIES = [
    "domainSignals",
    "problemSignals",
    "systemSignals",
    "dataSignals",
    "workflowSignals",
]


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(values) -> tuple[str, ...]:
    items = []
    for value in values or []:
        cleaned = " ".join(str(value or "").split()).strip()
        if not cleaned or cleaned in items:
            continue
        items.append(cleaned)
    return tuple(items)


def f1_score(expected: tuple[str, ...], predicted: tuple[str, ...]) -> float:
    expected_set = set(expected)
    predicted_set = set(predicted)
    if not expected_set and not predicted_set:
        return 1.0
    if not expected_set or not predicted_set:
        return 0.0
    overlap = len(expected_set & predicted_set)
    if overlap == 0:
        return 0.0
    precision = overlap / len(predicted_set)
    recall = overlap / len(expected_set)
    return (2 * precision * recall) / (precision + recall)


def hit(expected: tuple[str, ...], predicted: tuple[str, ...]) -> bool:
    expected_set = set(expected)
    predicted_set = set(predicted)
    if not expected_set and not predicted_set:
        return True
    if not expected_set or not predicted_set:
        return False
    return bool(expected_set & predicted_set)


def score_items(items: list[dict], key: str) -> dict:
    per_category = {}
    strict_hits = []

    for category in CATEGORIES:
        exact_hits = []
        overlap_hits = []
        f1_values = []
        non_empty_expected = 0
        for item in items:
            expected = normalize(item.get("expected", {}).get(category, []))
            predicted = normalize(item.get(key, {}).get(category, []))
            if expected:
                non_empty_expected += 1
            exact_hits.append(1 if expected == predicted else 0)
            overlap_hits.append(1 if hit(expected, predicted) else 0)
            f1_values.append(f1_score(expected, predicted))
        per_category[category] = {
            "exactRate": round(mean(exact_hits), 4) if exact_hits else 0.0,
            "hitRate": round(mean(overlap_hits), 4) if overlap_hits else 0.0,
            "avgF1": round(mean(f1_values), 4) if f1_values else 0.0,
            "nonEmptyExpected": non_empty_expected,
        }

    for item in items:
        is_strict = True
        for category in CATEGORIES:
            expected = normalize(item.get("expected", {}).get(category, []))
            predicted = normalize(item.get(key, {}).get(category, []))
            if expected != predicted:
                is_strict = False
                break
        strict_hits.append(1 if is_strict else 0)

    return {
        "count": len(items),
        "strictRate": round(mean(strict_hits), 4) if strict_hits else 0.0,
        "categories": per_category,
    }


def build_markdown(payload: dict) -> str:
    current = payload["current"]
    suggested = payload["suggested"]

    lines = [
        "# Structured Signal 정확도 리포트 001",
        "",
        f"- 평가 표본: `{payload['count']}건`",
        f"- strictRate(current): `{current['strictRate']}`",
        f"- strictRate(suggested): `{suggested['strictRate']}`",
        "",
        "## Category Scores",
        "",
    ]
    for category in CATEGORIES:
        cur = current["categories"][category]
        sug = suggested["categories"][category]
        lines.extend(
            [
                f"### {category}",
                "",
                f"- current exact/hit/F1: `{cur['exactRate']} / {cur['hitRate']} / {cur['avgF1']}`",
                f"- suggested exact/hit/F1: `{sug['exactRate']} / {sug['hitRate']} / {sug['avgF1']}`",
                f"- non-empty expected: `{sug['nonEmptyExpected']}`",
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_OUTPUT))
    args = parser.parse_args()

    payload = load_json(pathlib.Path(args.input))
    items = [item for item in payload.get("items", []) if item.get("resolved")]

    result = {
        "generatedAt": payload.get("generatedAt"),
        "sourceReviewPath": str(pathlib.Path(args.input)),
        "count": len(items),
        "current": score_items(items, "current"),
        "suggested": score_items(items, "suggested"),
    }

    json_path = pathlib.Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_content = build_markdown(result)
    md_path = pathlib.Path(args.md_output)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(md_content, encoding="utf-8")

    print(md_content)
    print(f"Wrote structured signal score JSON to {json_path}")
    print(f"Wrote structured signal score MD to {md_path}")


if __name__ == "__main__":
    main()
