#!/usr/bin/env python3

import argparse
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE_EVAL_PATH = ROOT / "data" / "eval_set.json"
INCREMENTAL_EVAL_PATH = ROOT / "data" / "incremental_eval_set.json"
DEFAULT_JSON_PATH = ROOT / "data" / "review_goldset_seed_001.json"
DEFAULT_JSONL_PATH = ROOT / "data" / "review_goldset_seed_001.jsonl"
DEFAULT_MD_PATH = ROOT / "docs" / "review_goldset_seed_001.md"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_reviewed(item: dict) -> bool:
    review = item.get("review", {})
    if review.get("overallPass") is not None:
        return True
    if any(review.get(key) is not None for key in ("summaryPass", "focusLabelPass", "keywordsPass")):
        return True
    return any(
        review.get(key)
        for key in (
            "correctedSummary",
            "correctedFocusLabel",
            "correctedKeywords",
            "correctedQuality",
            "notes",
        )
    )


def normalized_target(item: dict) -> dict:
    current = item.get("current", {})
    review = item.get("review", {})

    summary = review.get("correctedSummary", "")
    if review.get("summaryPass") is True and not summary:
        summary = current.get("summary", "")

    focus = review.get("correctedFocusLabel", "")
    if review.get("focusLabelPass") is True and not focus:
        focus = current.get("focusLabel", "")

    keywords = review.get("correctedKeywords", [])
    if review.get("keywordsPass") is True and not keywords:
        keywords = current.get("keywords", [])

    quality = review.get("correctedQuality", "")
    if not quality:
        quality = item.get("summaryQuality", "")

    return {
        "summary": summary,
        "focusLabel": focus,
        "keywords": keywords,
        "quality": quality,
    }


def build_rows() -> list[dict]:
    rows = []
    seen = set()
    for dataset_name, path in [("core", CORE_EVAL_PATH), ("incremental", INCREMENTAL_EVAL_PATH)]:
        payload = load_json(path)
        for item in payload.get("items", []):
            if not is_reviewed(item):
                continue
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            rows.append(
                {
                    "id": item.get("id", ""),
                    "dataset": dataset_name,
                    "company": item.get("company", ""),
                    "title": item.get("title", ""),
                    "roleGroup": item.get("roleGroup", ""),
                    "clusterLabel": item.get("clusterLabel", ""),
                    "input": item.get("source", {}),
                    "current": item.get("current", {}),
                    "target": normalized_target(item),
                    "review": item.get("review", {}),
                }
            )
    return rows


def build_markdown(rows: list[dict]) -> str:
    lines = [
        "# 리뷰 골드셋 Seed",
        "",
        f"- 고유 공고 수: `{len(rows)}`",
        "- 목적: 첫 검수 결과를 다음 프롬프트 개선과 구조화 추출 평가의 seed로 사용합니다.",
        "- 주의: 아직 작은 seed이며, 최종 학습셋으로 보기엔 부족합니다.",
        "",
    ]
    for row in rows:
        lines.extend(
            [
                f"## {row['company']} | {row['title']}",
                "",
                f"- dataset: `{row['dataset']}`",
                f"- current summary: `{row['current'].get('summary', '')}`",
                f"- current focus: `{row['current'].get('focusLabel', '')}`",
                f"- target summary: `{row['target'].get('summary', '')}`",
                f"- target focus: `{row['target'].get('focusLabel', '')}`",
                f"- target keywords: {', '.join(row['target'].get('keywords', []))}",
                "",
            ]
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_PATH))
    parser.add_argument("--jsonl-output", default=str(DEFAULT_JSONL_PATH))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_PATH))
    args = parser.parse_args()

    rows = build_rows()

    json_path = pathlib.Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps({"items": rows}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    jsonl_path = pathlib.Path(args.jsonl_output)
    jsonl_path.parent.mkdir(parents=True, exist_ok=True)
    with jsonl_path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")

    md_path = pathlib.Path(args.md_output)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(build_markdown(rows) + "\n", encoding="utf-8")

    print(f"Wrote review goldset seed JSON to {json_path}")
    print(f"Wrote review goldset seed JSONL to {jsonl_path}")
    print(f"Wrote review goldset seed markdown to {md_path}")


if __name__ == "__main__":
    main()
