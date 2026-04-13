#!/usr/bin/env python3

import argparse
import json
import pathlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_JSON_PATH = ROOT / "data" / "review_triage_001.json"
DEFAULT_MD_PATH = ROOT / "docs" / "review_triage_001.md"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def norm_keywords(values) -> set[str]:
    return {clean(value).lower() for value in values or [] if clean(value)}


def classify_item(item: dict) -> tuple[str, str]:
    current = item.get("current", {})
    prefill = item.get("assistantPrefill", {})
    current_summary = clean(current.get("summary", ""))
    current_focus = clean(current.get("focusLabel", ""))
    current_quality = clean(current.get("quality", "")).lower()
    current_keywords = norm_keywords(current.get("keywords", []))

    prefill_summary = clean(prefill.get("summary", ""))
    prefill_focus = clean(prefill.get("focusLabel", ""))
    prefill_quality = clean(prefill.get("quality", "")).lower()
    prefill_keywords = norm_keywords(prefill.get("keywords", []))

    if prefill_quality == "low" and not prefill_summary and not prefill_focus:
        return "keep_low", "프리필도 low로 유지해 저신뢰 공고로 보는 편이 안전합니다."

    if current_quality == "low" and prefill_quality in {"medium", "high"}:
        return "upgrade_review", "현재 결과보다 프리필 제안이 더 구체적이라 우선 검수 가치가 높습니다."

    if current_focus and prefill_focus and current_focus != prefill_focus:
        return "focus_check", "focusLabel이 달라 그룹 기준 검수가 필요합니다."

    if current_summary and prefill_summary and current_summary != prefill_summary:
        return "summary_check", "summary 표현이 달라 게시 문구 검수가 필요합니다."

    if current_keywords and prefill_keywords and current_keywords != prefill_keywords:
        return "keyword_check", "keywords 구성이 달라 묶음 신호 검수가 필요합니다."

    return "quick_confirm", "현재 결과와 프리필이 크게 다르지 않아 빠른 확인 위주로 보면 됩니다."


def build_payload(wave: dict) -> dict:
    items = []
    counts = Counter()
    for item in wave.get("items", []):
        bucket, note = classify_item(item)
        counts[bucket] += 1
        items.append(
            {
                "id": item.get("id", ""),
                "company": item.get("company", ""),
                "title": item.get("title", ""),
                "bucket": bucket,
                "note": note,
                "currentQuality": item.get("current", {}).get("quality", ""),
                "assistantQuality": item.get("assistantPrefill", {}).get("quality", ""),
                "currentFocusLabel": item.get("current", {}).get("focusLabel", ""),
                "assistantFocusLabel": item.get("assistantPrefill", {}).get("focusLabel", ""),
            }
        )
    return {"distribution": dict(counts), "items": items}


def build_markdown(payload: dict) -> str:
    lines = [
        "# 리뷰 트리아지",
        "",
        "## 분포",
        "",
    ]
    for key, value in payload["distribution"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")

    groups = {}
    for item in payload["items"]:
        groups.setdefault(item["bucket"], []).append(item)

    order = ["upgrade_review", "focus_check", "summary_check", "keyword_check", "keep_low", "quick_confirm"]
    for bucket in order:
        bucket_items = groups.get(bucket, [])
        if not bucket_items:
            continue
        lines.extend([f"## {bucket}", ""])
        for item in bucket_items[:12]:
            lines.append(
                f"- {item['company']} | {item['title']} "
                f"(`{item['currentQuality']} -> {item['assistantQuality']}`, "
                f"`{item['currentFocusLabel']} -> {item['assistantFocusLabel']}`)"
            )
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_PATH))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_PATH))
    args = parser.parse_args()

    wave = load_json(pathlib.Path(args.wave))
    payload = build_payload(wave)

    json_path = pathlib.Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_path = pathlib.Path(args.md_output)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(build_markdown(payload), encoding="utf-8")

    print(f"Wrote review triage JSON to {json_path}")
    print(f"Wrote review triage markdown to {md_path}")


if __name__ == "__main__":
    main()
