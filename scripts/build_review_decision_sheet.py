#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_QUEUE_PATH = ROOT / "data" / "review_confirm_queue_001.json"
DEFAULT_CSV_PATH = ROOT / "data" / "review_decision_sheet_001.csv"
DEFAULT_MD_PATH = ROOT / "docs" / "review_decision_sheet_001.md"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def recommended_decision(bucket: str) -> str:
    if bucket == "low_confirm":
        return "approve_low"
    return "approve_draft"


def build_markdown(items: list[dict]) -> str:
    lines = [
        "# 리뷰 의사결정 시트",
        "",
        f"- 대상 공고: `{len(items)}`",
        "- 기본 권장값은 `recommendedDecision`에 들어 있습니다.",
        "- 가능한 결정값: `approve_draft`, `approve_low`, `approve_current`, `needs_edit`, `skip`",
        "- `needs_edit`를 쓰는 경우 `manualSummary / manualFocusLabel / manualKeywords / manualQuality`를 같이 채우면 됩니다.",
        "",
        "## 빠른 해석",
        "",
        "- `approve_draft`: assistant draft를 그대로 검수값으로 승인",
        "- `approve_low`: low 유지가 맞다고 승인",
        "- `approve_current`: 현재 모델 출력이 충분히 맞다고 승인",
        "- `needs_edit`: 사람이 직접 수정해서 확정",
        "- `skip`: 지금은 반영하지 않음",
        "",
    ]
    for item in items:
        lines.append(f"- {item['company']} | {item['title']} -> 권장 `{recommended_decision(item.get('handoffBucket', ''))}`")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--queue", default=str(DEFAULT_QUEUE_PATH))
    parser.add_argument("--csv-output", default=str(DEFAULT_CSV_PATH))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_PATH))
    args = parser.parse_args()

    queue = load_json(pathlib.Path(args.queue))
    items = queue.get("items", [])

    fieldnames = [
        "id",
        "handoffBucket",
        "company",
        "title",
        "currentQuality",
        "draftQuality",
        "currentFocusLabel",
        "draftFocusLabel",
        "currentSummary",
        "draftSummary",
        "draftKeywords",
        "recommendedDecision",
        "decision",
        "manualSummary",
        "manualFocusLabel",
        "manualKeywords",
        "manualQuality",
        "confirmNotes",
    ]

    csv_path = pathlib.Path(args.csv_output)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            default_decision = recommended_decision(item.get("handoffBucket", ""))
            writer.writerow(
                {
                    "id": item.get("id", ""),
                    "handoffBucket": item.get("handoffBucket", ""),
                    "company": item.get("company", ""),
                    "title": item.get("title", ""),
                    "currentQuality": item.get("currentQuality", ""),
                    "draftQuality": item.get("draftQuality", ""),
                    "currentFocusLabel": item.get("currentFocusLabel", ""),
                    "draftFocusLabel": item.get("draftFocusLabel", ""),
                    "currentSummary": item.get("currentSummary", ""),
                    "draftSummary": item.get("draftSummary", ""),
                    "draftKeywords": " | ".join(item.get("draftKeywords", [])),
                    "recommendedDecision": default_decision,
                    "decision": default_decision,
                    "manualSummary": "",
                    "manualFocusLabel": "",
                    "manualKeywords": "",
                    "manualQuality": "",
                    "confirmNotes": "",
                }
            )

    md_path = pathlib.Path(args.md_output)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(build_markdown(items) + "\n", encoding="utf-8")

    print(f"Wrote review decision sheet CSV to {csv_path}")
    print(f"Wrote review decision sheet markdown to {md_path}")


if __name__ == "__main__":
    main()
