#!/usr/bin/env python3

import argparse
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_TRIAGE_PATH = ROOT / "data" / "review_triage_001.json"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "review_draft_focus_check_001.json"
DEFAULT_MD_OUTPUT_PATH = ROOT / "docs" / "review_draft_focus_check_001.md"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def values_equal(left, right) -> bool:
    return clean(left) == clean(right)


def build_focus_check_draft(item: dict) -> dict:
    current = item.get("current", {})
    prefill = item.get("assistantPrefill", {})
    current_quality = clean(current.get("quality", "")).lower()
    assistant_quality = clean(prefill.get("quality", "")).lower()
    current_summary = clean(current.get("summary", ""))
    assistant_summary = clean(prefill.get("summary", ""))
    current_focus = clean(current.get("focusLabel", ""))
    assistant_focus = clean(prefill.get("focusLabel", ""))
    current_keywords = current.get("keywords", []) or []
    assistant_keywords = prefill.get("keywords", []) or []

    summary_pass = bool(current_summary and current_quality in {"high", "medium"})
    keywords_pass = current_keywords == assistant_keywords if assistant_keywords else False
    corrected_summary = "" if summary_pass else (assistant_summary or current_summary)
    corrected_quality = current_quality or assistant_quality

    return {
        "summaryPass": summary_pass,
        "focusLabelPass": False if assistant_focus and not values_equal(current_focus, assistant_focus) else True,
        "keywordsPass": keywords_pass,
        "overallPass": False,
        "correctedSummary": corrected_summary,
        "correctedFocusLabel": assistant_focus or current_focus,
        "correctedKeywords": assistant_keywords or current_keywords,
        "correctedQuality": corrected_quality,
        "notes": "현재 summary는 유지하고, focusLabel과 keywords를 중심으로 검수하는 보수적 드래프트입니다.",
    }


def build_payload(wave: dict, triage: dict, bucket: str) -> dict:
    triage_ids = [item["id"] for item in triage.get("items", []) if item.get("bucket") == bucket]
    by_id = {item["id"]: item for item in wave.get("items", [])}
    items = []
    for item_id in triage_ids:
        row = by_id.get(item_id)
        if not row or not row.get("assistantPrefill"):
            continue
        if bucket == "focus_check":
            draft = build_focus_check_draft(row)
        else:
            continue
        items.append(
            {
                "id": item_id,
                "company": row.get("company", ""),
                "title": row.get("title", ""),
                "assistantReviewDraft": draft,
            }
        )
    return {
        "generatedAt": clean(json.dumps({"generated": True})),  # placeholder stable string replaced below
        "source": {
            "wavePath": str(DEFAULT_WAVE_PATH),
            "triagePath": str(DEFAULT_TRIAGE_PATH),
            "bucket": bucket,
            "note": "assistant-generated bucket review draft; not merged into eval-set review fields",
        },
        "items": items,
    }


def build_markdown(payload: dict) -> str:
    lines = [
        f"# 리뷰 드래프트 {payload['source']['bucket']}",
        "",
        f"- 대상 건수: `{len(payload.get('items', []))}`",
        "",
    ]
    for item in payload.get("items", [])[:20]:
        draft = item["assistantReviewDraft"]
        lines.extend(
            [
                f"## {item['company']} | {item['title']}",
                "",
                f"- summaryPass: `{draft.get('summaryPass')}`",
                f"- focusLabelPass: `{draft.get('focusLabelPass')}`",
                f"- keywordsPass: `{draft.get('keywordsPass')}`",
                f"- correctedFocusLabel: `{draft.get('correctedFocusLabel', '')}`",
                f"- correctedKeywords: {', '.join(draft.get('correctedKeywords', []))}",
                f"- notes: {draft.get('notes', '')}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--triage", default=str(DEFAULT_TRIAGE_PATH))
    parser.add_argument("--bucket", default="focus_check")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--markdown-output", default=str(DEFAULT_MD_OUTPUT_PATH))
    args = parser.parse_args()

    wave = load_json(pathlib.Path(args.wave))
    triage = load_json(pathlib.Path(args.triage))
    payload = build_payload(wave, triage, args.bucket)
    payload["generatedAt"] = str(pathlib.Path(args.wave).stat().st_mtime)

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    markdown_output_path = pathlib.Path(args.markdown_output)
    markdown_output_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_output_path.write_text(build_markdown(payload), encoding="utf-8")

    print(f"Wrote bucket review draft to {output_path}")
    print(f"Wrote bucket review markdown to {markdown_output_path}")


if __name__ == "__main__":
    main()
