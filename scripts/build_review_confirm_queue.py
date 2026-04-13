#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_HANDOFF_PATH = ROOT / "data" / "review_handoff_001.json"
DEFAULT_JSON_PATH = ROOT / "data" / "review_confirm_queue_001.json"
DEFAULT_CSV_PATH = ROOT / "data" / "review_confirm_queue_001.csv"
DEFAULT_MD_PATH = ROOT / "docs" / "review_confirm_queue_001.md"
DEFAULT_BACKLOG_JSON_PATH = ROOT / "data" / "review_focus_backlog_001.json"
DEFAULT_BACKLOG_CSV_PATH = ROOT / "data" / "review_focus_backlog_001.csv"
DEFAULT_BACKLOG_MD_PATH = ROOT / "docs" / "review_focus_backlog_001.md"

CONFIRM_BUCKETS = {
    "upgrade_review",
    "full_rewrite_check",
    "summary_rewrite_check",
    "low_confirm",
}


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: pathlib.Path, items: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
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
                "note",
                "confirmDecision",
                "confirmNotes",
            ],
        )
        writer.writeheader()
        for item in items:
            row = dict(item)
            row["draftKeywords"] = " | ".join(item.get("draftKeywords", []))
            row["confirmDecision"] = ""
            row["confirmNotes"] = ""
            writer.writerow({key: row.get(key, "") for key in writer.fieldnames})


def build_markdown(title: str, items: list[dict], distribution: Counter, extra_lines: list[str]) -> str:
    lines = [f"# {title}", ""]
    lines.extend(extra_lines)
    lines.extend(["", "## 분포", ""])
    for key, value in distribution.items():
        lines.append(f"- `{key}`: `{value}`")
    lines.append("")

    groups = {}
    for item in items:
        groups.setdefault(item["handoffBucket"], []).append(item)

    for bucket, bucket_items in groups.items():
        lines.extend([f"## {bucket}", ""])
        for item in bucket_items:
            lines.append(f"- {item['company']} | {item['title']}")
            lines.append(f"  current: `{item['currentQuality']}` / `{item['currentFocusLabel']}`")
            if item.get("draftSummary"):
                lines.append(f"  draft summary: `{item['draftSummary']}`")
            if item.get("draftFocusLabel"):
                lines.append(f"  draft focus: `{item['draftFocusLabel']}`")
            if item.get("draftKeywords"):
                lines.append(f"  draft keywords: {', '.join(item['draftKeywords'])}")
            lines.append(f"  note: {item['note']}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--handoff", default=str(DEFAULT_HANDOFF_PATH))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_PATH))
    parser.add_argument("--csv-output", default=str(DEFAULT_CSV_PATH))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_PATH))
    parser.add_argument("--backlog-json-output", default=str(DEFAULT_BACKLOG_JSON_PATH))
    parser.add_argument("--backlog-csv-output", default=str(DEFAULT_BACKLOG_CSV_PATH))
    parser.add_argument("--backlog-md-output", default=str(DEFAULT_BACKLOG_MD_PATH))
    args = parser.parse_args()

    handoff = load_json(pathlib.Path(args.handoff))
    items = handoff.get("items", [])

    confirm_items = [item for item in items if item.get("handoffBucket") in CONFIRM_BUCKETS]
    backlog_items = [item for item in items if item.get("handoffBucket") not in CONFIRM_BUCKETS]

    confirm_distribution = Counter(item["handoffBucket"] for item in confirm_items)
    backlog_distribution = Counter(item["handoffBucket"] for item in backlog_items)

    confirm_payload = {
        "totalItems": len(confirm_items),
        "distribution": dict(confirm_distribution),
        "items": confirm_items,
        "note": "human confirm queue only; no review fields applied yet",
    }
    backlog_payload = {
        "totalItems": len(backlog_items),
        "distribution": dict(backlog_distribution),
        "items": backlog_items,
        "note": "deferred backlog for lower-priority focus/keyword adjustments",
    }

    write_json(pathlib.Path(args.json_output), confirm_payload)
    write_json(pathlib.Path(args.backlog_json_output), backlog_payload)
    write_csv(pathlib.Path(args.csv_output), confirm_items)
    write_csv(pathlib.Path(args.backlog_csv_output), backlog_items)

    pathlib.Path(args.md_output).write_text(
        build_markdown(
            "리뷰 확인 큐",
            confirm_items,
            confirm_distribution,
            [
                f"- 즉시 확인 대상: `{len(confirm_items)}`",
                "- 범위: `upgrade_review`, `full_rewrite_check`, `summary_rewrite_check`, `low_confirm`",
                "- 목적: 사람이 실제로 한 번은 봐야 하는 고위험/결정형 항목만 남깁니다.",
            ],
        ),
        encoding="utf-8",
    )
    pathlib.Path(args.backlog_md_output).write_text(
        build_markdown(
            "리뷰 백로그",
            backlog_items,
            backlog_distribution,
            [
                f"- 후순위 검토 대상: `{len(backlog_items)}`",
                "- 범위: 주로 `focus_keyword_check`",
                "- 목적: 당장 정확도 판정에 직접 영향이 덜한 그룹 기준 조정을 뒤로 미룹니다.",
            ],
        ),
        encoding="utf-8",
    )

    print(f"Wrote confirm queue JSON to {args.json_output}")
    print(f"Wrote confirm queue CSV to {args.csv_output}")
    print(f"Wrote confirm queue markdown to {args.md_output}")
    print(f"Wrote backlog JSON to {args.backlog_json_output}")
    print(f"Wrote backlog CSV to {args.backlog_csv_output}")
    print(f"Wrote backlog markdown to {args.backlog_md_output}")


if __name__ == "__main__":
    main()
