#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "goldset_expansion_wave_001.json"
DEFAULT_SUMMARIES_PATH = ROOT / "data" / "job_summaries.json"
DEFAULT_BOARD_PATH = ROOT / "data" / "summary_board.json"
DEFAULT_CSV_PATH = ROOT / "data" / "goldset_expansion_decision_sheet_001.csv"
DEFAULT_MD_PATH = ROOT / "docs" / "goldset_expansion_decision_sheet_001.md"

BROAD_LABELS = {
    "LLM",
    "파이프라인",
    "PyTorch",
    "TensorFlow",
    "SQL",
    "컴퓨터 비전",
    "클라우드",
    "의료",
    "마케팅",
    "인사이트",
}


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def join_keywords(values) -> str:
    return " | ".join(clean(value) for value in (values or []) if clean(value))


def pick_recommended_decision(reason: str, raw_focus: str, board_focus: str, raw_quality: str) -> tuple[str, str]:
    raw_quality = clean(raw_quality).lower()
    raw_focus = clean(raw_focus)
    board_focus = clean(board_focus)

    if reason == "low_or_empty":
        return "approve_low", "원문 신호가 약해 low 유지가 우선입니다."

    if board_focus and board_focus != raw_focus:
        if raw_focus in BROAD_LABELS and board_focus not in BROAD_LABELS:
            return "approve_draft", "보드 projection이 더 구체적인 대표 라벨로 좁혔습니다."
        return "approve_draft", "보드 projection 결과를 우선 검토하는 것이 좋습니다."

    if raw_quality == "low" and not board_focus:
        return "approve_low", "현재도 low이고 보드에서도 구조화 신호를 살리지 않았습니다."

    if reason == "domain_specific":
        return "approve_current", "현재 라벨이 도메인 특화 신호를 이미 담고 있습니다."

    if reason == "focus_keyword_conflict":
        if board_focus and board_focus != raw_focus:
            return "approve_draft", "보드 projection이 키워드와 더 잘 맞는 중심 라벨을 제안했습니다."
        return "needs_edit", "키워드와 대표 라벨의 충돌 여부를 직접 확인하는 것이 좋습니다."

    if reason == "broad_focus":
        if board_focus and board_focus not in BROAD_LABELS:
            return "approve_draft", "넓은 raw focus를 보드 projection이 더 구체적으로 좁혔습니다."
        return "needs_edit", "여전히 넓은 라벨일 가능성이 높아 직접 확인이 필요합니다."

    return "approve_current", "현재 값을 우선 기준으로 두고 검토하면 됩니다."


def build_markdown(rows: list[dict]) -> str:
    decision_counts = Counter(row["recommendedDecision"] for row in rows)
    reason_counts = Counter(row["reason"] for row in rows)

    lines = [
        "# 골드셋 확장 의사결정 시트 001",
        "",
        f"- 대상 공고: `{len(rows)}`",
        "- 이 시트는 `raw extractor 결과(current)`와 `board projection 결과(draft)`를 함께 비교합니다.",
        "- 가능한 결정값: `approve_draft`, `approve_low`, `approve_current`, `needs_edit`, `skip`",
        "- `needs_edit`일 때만 `manualSummary / manualFocusLabel / manualKeywords / manualQuality`를 채우면 됩니다.",
        "",
        "## 추천 결정 분포",
        "",
    ]
    for key, count in sorted(decision_counts.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(
        [
            "",
            "## 이유 분포",
            "",
        ]
    )
    for key, count in sorted(reason_counts.items()):
        lines.append(f"- `{key}`: `{count}`")

    grouped = {}
    for row in rows:
        grouped.setdefault(row["reason"], []).append(row)

    for reason in sorted(grouped):
        lines.extend(["", f"## {reason}", ""])
        for row in grouped[reason]:
            lines.append(
                f"- `{row['company']}` | `{row['title']}` | raw `{row['currentFocusLabel'] or '-'}` -> board `{row['draftFocusLabel'] or '-'}` | 권장 `{row['recommendedDecision']}`"
            )

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--summaries", default=str(DEFAULT_SUMMARIES_PATH))
    parser.add_argument("--board", default=str(DEFAULT_BOARD_PATH))
    parser.add_argument("--csv-output", default=str(DEFAULT_CSV_PATH))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_PATH))
    args = parser.parse_args()

    wave = load_json(pathlib.Path(args.wave))
    summaries = load_json(pathlib.Path(args.summaries))
    board = load_json(pathlib.Path(args.board))

    summary_items = summaries.get("items", {})
    board_rows = {row["id"]: row for row in board.get("rows", [])}

    rows = []
    for item in wave.get("items", []):
        job_id = item["id"]
        raw = summary_items.get(job_id, {})
        projected = board_rows.get(job_id, {})

        recommended_decision, note = pick_recommended_decision(
            reason=clean(item.get("reason", "")),
            raw_focus=clean(raw.get("focusLabel", "")),
            board_focus=clean(projected.get("focusLabel", "")),
            raw_quality=clean(raw.get("quality", "")),
        )

        rows.append(
            {
                "id": job_id,
                "reason": clean(item.get("reason", "")),
                "company": clean(item.get("company", "")),
                "title": clean(item.get("title", "")),
                "roleDisplay": clean(item.get("roleDisplay", "")),
                "currentQuality": clean(raw.get("quality", "")),
                "draftQuality": clean(projected.get("summaryQuality", "")),
                "currentFocusLabel": clean(raw.get("focusLabel", "")),
                "draftFocusLabel": clean(projected.get("focusLabel", "")),
                "currentSummary": clean(raw.get("summary", "")),
                "draftSummary": clean(projected.get("summary", "")),
                "currentKeywords": join_keywords(raw.get("keywords", [])),
                "draftKeywords": join_keywords(projected.get("highlightKeywords", [])),
                "recommendedDecision": recommended_decision,
                "decision": recommended_decision,
                "assistantNotes": note,
                "manualSummary": "",
                "manualFocusLabel": "",
                "manualKeywords": "",
                "manualQuality": "",
                "confirmNotes": "",
            }
        )

    fieldnames = [
        "id",
        "reason",
        "company",
        "title",
        "roleDisplay",
        "currentQuality",
        "draftQuality",
        "currentFocusLabel",
        "draftFocusLabel",
        "currentSummary",
        "draftSummary",
        "currentKeywords",
        "draftKeywords",
        "recommendedDecision",
        "decision",
        "assistantNotes",
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
        for row in rows:
            writer.writerow(row)

    md_path = pathlib.Path(args.md_output)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(build_markdown(rows) + "\n", encoding="utf-8")

    print(f"Wrote goldset expansion decision CSV to {csv_path}")
    print(f"Wrote goldset expansion decision markdown to {md_path}")


if __name__ == "__main__":
    main()
