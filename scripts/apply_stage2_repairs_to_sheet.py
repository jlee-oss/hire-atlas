#!/usr/bin/env python3

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

from run_stage2_validation import (
    DEFAULT_SERVICE_ACCOUNT_JSON,
    DEFAULT_STAGE1_GID,
    DEFAULT_STAGE1_SPREADSHEET_ID,
    DEFAULT_STAGE1_TITLE,
    DEFAULT_STAGE2_GID,
    DEFAULT_STAGE2_SPREADSHEET_ID,
    DEFAULT_STAGE2_TITLE,
    STAGE2_FIELDNAMES,
    clean,
    pick,
    row_hash,
    row_id,
    safe_read_sheet,
    stage1_focus,
    stage1_keywords,
    stage1_role,
    stage1_summary,
    stage2_focus,
    stage2_keywords,
    stage2_role,
    stage2_summary,
    write_stage2_sheet,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_REPAIR_CSV = ROOT / "data" / "stage2_repair_candidates_latest.csv"
DEFAULT_OUTPUT_JSON = ROOT / "data" / "stage2_apply_latest.json"
DEFAULT_OUTPUT_MD = ROOT / "docs" / "stage2_apply_latest.md"

MANUAL_KEYWORD_FALLBACKS = {
    "612cf32e38ba66f7ac225ee055f8b7aaa22d3579c39cbaf64e437e8a4eeb022f": "AI 모델링 머신러닝",
    "800c930f817175a5b21d7cd8ebb472b13718b2be83a019d227977ce3c1dc6979": "High Speed IO 반도체 IP 설계",
    "ad9c48113c5ab0ae92997e2a20f7ebca473512af67b83239fa7c9d394d3e6790": "연구개발 제조기술 인공지능",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def row_title(row: dict) -> str:
    return pick(row, "공고제목_표시", "공고제목_raw", "job_title_raw")


def row_company(row: dict) -> str:
    return pick(row, "회사명_표시", "회사명", "company_name")


def row_url(row: dict) -> str:
    return pick(row, "공고URL", "job_url")


def row_seen_at(row: dict) -> str:
    return pick(row, "최종발견시각", "last_seen_at")


def fallback_summary(row: dict, focus: str) -> str:
    current = stage1_summary(row)
    if current and len(current) > 4:
        return current
    parts = []
    career = pick(row, "경력수준_표시", "경력수준_raw")
    track = pick(row, "채용트랙_표시")
    if career:
        parts.append(career)
    if track and track not in parts:
        parts.append(track)
    for part in focus.replace(",", "/").split("/"):
        item = clean(part)
        if item and item not in parts:
            parts.append(item)
    return " / ".join(parts[:4]) or "검수완료"


def repair_by_id(path: Path) -> dict[str, dict]:
    return {clean(row.get("공고키", "")): row for row in read_csv(path) if clean(row.get("공고키", ""))}


def build_stage2_row(stage1: dict, current_stage2: dict | None, repair: dict | None, applied_at: str) -> dict:
    job_id = row_id(stage1)
    role = stage2_role(current_stage2 or {}) or stage1_role(stage1)
    focus = stage2_focus(current_stage2 or {}) or stage1_focus(stage1)
    keywords = stage2_keywords(current_stage2 or {}) or stage1_keywords(stage1)
    summary = stage2_summary(current_stage2 or {}) or stage1_summary(stage1)
    memo_parts = []

    if repair:
        role = clean(repair.get("suggested_stage2_분류직무", "")) or role
        focus = clean(repair.get("suggested_stage2_직무초점", "")) or focus
        keywords = clean(repair.get("suggested_stage2_핵심기술", "")) or keywords
        summary = clean(repair.get("suggested_stage2_구분요약", "")) or summary
        memo_parts.append(f"stage2 repair source={repair.get('source', '')}")
        memo_parts.append(f"confidence={repair.get('confidence', '')}")
        memo_parts.append(f"effect={repair.get('repair_effect', '')}")
    elif current_stage2:
        memo_parts.append("stage2 carry-forward")
    else:
        memo_parts.append("stage2 pass-through from stage1")

    if not keywords and job_id in MANUAL_KEYWORD_FALLBACKS:
        keywords = MANUAL_KEYWORD_FALLBACKS[job_id]
        memo_parts.append("manual keyword fallback")
    if not focus:
        memo_parts.append("missing focus after apply")
    if not summary or len(summary) <= 4:
        summary = fallback_summary(stage1, focus)
        memo_parts.append("summary fallback")

    return {
        "공고키": job_id,
        "변경해시": row_hash(stage1),
        "검증상태": "approved",
        "검증우선순위": "pass",
        "이슈코드": "stage2_applied",
        "이슈요약": "2차 검증 반영 완료",
        "stage1_분류직무": stage1_role(stage1),
        "stage2_분류직무": role,
        "stage1_직무초점": stage1_focus(stage1),
        "stage2_직무초점": focus,
        "stage1_핵심기술": stage1_keywords(stage1),
        "stage2_핵심기술": keywords,
        "stage1_구분요약": stage1_summary(stage1),
        "stage2_구분요약": summary,
        "회사명_표시": row_company(stage1),
        "공고제목_표시": row_title(stage1),
        "공고URL": row_url(stage1),
        "최종발견시각": row_seen_at(stage1),
        "검증메모": f"{applied_at}; " + "; ".join(part for part in memo_parts if part),
        "승인여부": "승인",
    }


def render_md(report: dict) -> str:
    lines = [
        "# Stage2 Apply Latest",
        "",
        f"- appliedAt: `{report['appliedAt']}`",
        f"- rowsBuilt: `{report['rowsBuilt']}`",
        f"- repairRowsApplied: `{report['repairRowsApplied']}`",
        f"- passThroughRows: `{report['passThroughRows']}`",
        f"- manualFallbackRows: `{report['manualFallbackRows']}`",
        f"- stage2WriteStatus: `{report['stage2Write'].get('status', 'written')}`",
        "",
        "## Outputs",
        "",
    ]
    for key, value in report["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply local stage2 repair candidates to the stage2 Google Sheet.")
    parser.add_argument("--repair-csv", type=Path, default=DEFAULT_REPAIR_CSV)
    parser.add_argument("--stage1-spreadsheet-id", default=DEFAULT_STAGE1_SPREADSHEET_ID)
    parser.add_argument("--stage1-gid", default=DEFAULT_STAGE1_GID)
    parser.add_argument("--stage1-title", default=DEFAULT_STAGE1_TITLE)
    parser.add_argument("--stage2-spreadsheet-id", default=DEFAULT_STAGE2_SPREADSHEET_ID)
    parser.add_argument("--stage2-gid", default=DEFAULT_STAGE2_GID)
    parser.add_argument("--stage2-title", default=DEFAULT_STAGE2_TITLE)
    parser.add_argument("--service-account-json", default=DEFAULT_SERVICE_ACCOUNT_JSON)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    applied_at = now_iso()
    stage1_rows, stage1_source, stage1_error = safe_read_sheet(
        spreadsheet_id=args.stage1_spreadsheet_id,
        gid=args.stage1_gid,
        title=args.stage1_title,
        service_account_json=args.service_account_json,
        label="stage1",
    )
    if stage1_error:
        raise SystemExit(f"Stage1 sheet is unreadable: {stage1_error}")
    stage2_rows, stage2_source, stage2_error = safe_read_sheet(
        spreadsheet_id=args.stage2_spreadsheet_id,
        gid=args.stage2_gid,
        title=args.stage2_title,
        service_account_json=args.service_account_json,
        label="stage2",
    )
    if stage2_error:
        raise SystemExit(f"Stage2 sheet is unreadable: {stage2_error}")

    repairs = repair_by_id(args.repair_csv)
    stage2_by_id = {row_id(row): row for row in stage2_rows if row_id(row)}
    rows = []
    applied_repair_ids = set()
    manual_fallback_rows = 0
    for stage1 in stage1_rows:
        job_id = row_id(stage1)
        repair = repairs.get(job_id)
        if repair:
            applied_repair_ids.add(job_id)
        built = build_stage2_row(stage1, stage2_by_id.get(job_id), repair, applied_at)
        if "manual" in built["검증메모"]:
            manual_fallback_rows += 1
        rows.append(built)

    sheet_title = args.stage2_title or "시트1"
    write_result = write_stage2_sheet(
        spreadsheet_id=args.stage2_spreadsheet_id,
        service_account_json=args.service_account_json,
        sheet_title=sheet_title,
        rows=rows,
    )
    report = {
        "appliedAt": applied_at,
        "stage1Source": stage1_source,
        "stage2Source": stage2_source,
        "stage2SpreadsheetId": args.stage2_spreadsheet_id,
        "stage2SheetTitle": sheet_title,
        "rowsBuilt": len(rows),
        "repairRowsApplied": len(applied_repair_ids),
        "passThroughRows": len(rows) - len(applied_repair_ids),
        "manualFallbackRows": manual_fallback_rows,
        "unusedRepairIds": sorted(set(repairs) - applied_repair_ids),
        "stage2Write": {"status": "written", **write_result},
        "outputs": {
            "json": str(args.output_json),
            "md": str(args.output_md),
        },
    }
    write_json(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
