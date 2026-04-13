#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_JSON_PATH = ROOT / "data" / "review_handoff_001.json"
DEFAULT_MD_PATH = ROOT / "docs" / "review_handoff_001.md"
DEFAULT_CSV_PATH = ROOT / "data" / "review_handoff_001.csv"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value) -> str:
    return " ".join(str(value or "").split())


def classify(item: dict) -> tuple[str, str, int]:
    current = item.get("current", {})
    draft = item.get("assistantReviewDraft", {})
    current_quality = clean(current.get("quality", "")).lower()
    corrected_quality = clean(draft.get("correctedQuality", "")).lower()

    summary_pass = draft.get("summaryPass")
    focus_pass = draft.get("focusLabelPass")
    keywords_pass = draft.get("keywordsPass")

    corrected_summary = clean(draft.get("correctedSummary", ""))
    corrected_focus = clean(draft.get("correctedFocusLabel", ""))
    corrected_keywords = [clean(value) for value in draft.get("correctedKeywords", []) if clean(value)]

    if corrected_quality == "low" and not corrected_summary and not corrected_focus and not corrected_keywords:
        return (
            "low_confirm",
            "모델 제안도 low 유지입니다. 실제로 low로 둘지만 빠르게 확인하면 됩니다.",
            1,
        )

    if current_quality == "low" and corrected_quality in {"medium", "high"}:
        return (
            "upgrade_review",
            "현재 low 결과를 구체 값으로 끌어올리는 제안이라 우선 검수가 필요합니다.",
            4,
        )

    if summary_pass is True and focus_pass is False:
        return (
            "focus_keyword_check",
            "summary는 유지하고 그룹 기준(focus/keywords)만 확인하면 됩니다.",
            2,
        )

    if summary_pass is False and focus_pass is True:
        return (
            "summary_rewrite_check",
            "그룹 기준은 유지하고 게시 문구(summary)만 확인하면 됩니다.",
            2,
        )

    if summary_pass is False and focus_pass is False:
        return (
            "full_rewrite_check",
            "summary와 그룹 기준을 함께 다시 보는 편이 안전합니다.",
            3,
        )

    return (
        "mixed_check",
        "일부 항목만 수정되므로 한 번에 가볍게 확인하면 됩니다.",
        2,
    )


def build_payload(wave: dict) -> dict:
    items_by_id = {}
    counts = Counter()
    for item in wave.get("items", []):
        draft = item.get("assistantReviewDraft")
        if not draft:
            continue
        bucket, note, weight = classify(item)
        item_id = item.get("id", "")
        if item_id in items_by_id:
            items_by_id[item_id]["rowCount"] += 1
            continue
        counts[bucket] += 1
        items_by_id[item_id] = {
            "id": item_id,
            "company": item.get("company", ""),
            "title": item.get("title", ""),
            "handoffBucket": bucket,
            "reviewWeight": weight,
            "rowCount": 1,
            "note": note,
            "currentQuality": item.get("current", {}).get("quality", ""),
            "draftQuality": draft.get("correctedQuality", ""),
            "currentSummary": item.get("current", {}).get("summary", ""),
            "currentFocusLabel": item.get("current", {}).get("focusLabel", ""),
            "draftSummary": draft.get("correctedSummary", ""),
            "draftFocusLabel": draft.get("correctedFocusLabel", ""),
            "draftKeywords": draft.get("correctedKeywords", []),
        }

    items = list(items_by_id.values())
    items.sort(
        key=lambda item: (
            -item["reviewWeight"],
            item["handoffBucket"],
            item["company"],
            item["title"],
        )
    )
    return {
        "distribution": dict(counts),
        "totalItems": len(items),
        "estimatedHumanLoad": sum(item["reviewWeight"] for item in items),
        "items": items,
    }


def write_csv(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "handoffBucket",
                "reviewWeight",
                "rowCount",
                "company",
                "title",
                "currentQuality",
                "draftQuality",
                "currentSummary",
                "draftSummary",
                "currentFocusLabel",
                "draftFocusLabel",
                "draftKeywords",
                "note",
            ],
        )
        writer.writeheader()
        for item in payload["items"]:
            row = dict(item)
            row["draftKeywords"] = " | ".join(item.get("draftKeywords", []))
            writer.writerow(
                {key: row.get(key, "") for key in writer.fieldnames}
            )


def build_markdown(payload: dict) -> str:
    lines = [
        "# 리뷰 핸드오프",
        "",
        f"- 전체 assistant draft 적용 고유 공고: `{payload['totalItems']}`",
        f"- 추정 검수 부담 점수: `{payload['estimatedHumanLoad']}`",
        "",
        "## 분포",
        "",
    ]
    for key, value in payload["distribution"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")

    groups = {}
    for item in payload["items"]:
        groups.setdefault(item["handoffBucket"], []).append(item)

    order = [
        "upgrade_review",
        "full_rewrite_check",
        "summary_rewrite_check",
        "focus_keyword_check",
        "low_confirm",
        "mixed_check",
    ]
    for bucket in order:
        bucket_items = groups.get(bucket, [])
        if not bucket_items:
            continue
        lines.extend([f"## {bucket}", ""])
        for item in bucket_items[:20]:
            count_suffix = f" (중복 행 {item['rowCount']})" if item.get("rowCount", 1) > 1 else ""
            lines.append(f"- {item['company']} | {item['title']}{count_suffix}")
            lines.append(f"  current: `{item['currentQuality']}` / `{item['currentFocusLabel']}`")
            if item["draftSummary"]:
                lines.append(f"  draft summary: `{item['draftSummary']}`")
            if item["draftFocusLabel"]:
                lines.append(f"  draft focus: `{item['draftFocusLabel']}`")
            if item["draftKeywords"]:
                lines.append(f"  draft keywords: {', '.join(item['draftKeywords'])}")
            lines.append(f"  note: {item['note']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_PATH))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_PATH))
    parser.add_argument("--csv-output", default=str(DEFAULT_CSV_PATH))
    args = parser.parse_args()

    wave = load_json(pathlib.Path(args.wave))
    payload = build_payload(wave)

    json_path = pathlib.Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_path = pathlib.Path(args.md_output)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(build_markdown(payload), encoding="utf-8")

    write_csv(pathlib.Path(args.csv_output), payload)

    print(f"Wrote review handoff JSON to {json_path}")
    print(f"Wrote review handoff markdown to {md_path}")
    print(f"Wrote review handoff CSV to {args.csv_output}")


if __name__ == "__main__":
    main()
