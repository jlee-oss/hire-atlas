#!/usr/bin/env python3

import argparse
import csv
import io
import json
import os
import pathlib
import re
import sys
import urllib.request
from collections import Counter
from datetime import datetime, timezone

from build_briefing import build_briefing
from build_summary_board import build_summary_board
from google_sheets_runtime import fetch_sheet_rows


SPREADSHEET_ID = os.environ.get(
    "GOOGLE_SHEETS_SPREADSHEET_ID",
    "1bG-aT9L_N3SEPT04ZZZ-2jdRqW_agYhrqsn4fNanA5s",
)
GID = os.environ.get("GOOGLE_SHEETS_GID", "2026513640")
SHEET_TITLE = os.environ.get("GOOGLE_SHEETS_SHEET_TITLE", "master 탭")
SERVICE_ACCOUNT_JSON = os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")
CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{SPREADSHEET_ID}/gviz/tq"
    f"?tqx=out:csv&gid={GID}"
)
OUTPUT_PATH = pathlib.Path(__file__).resolve().parent.parent / "data" / "jobs.json"
DEFAULT_STAGE2_DEPLOY_CSV = pathlib.Path(
    os.environ.get(
        "STAGE2_DEPLOY_CSV",
        pathlib.Path(__file__).resolve().parent.parent / "data" / "stage2_deploy_candidates_latest.csv",
    )
)
DEFAULT_MIN_SOURCE_ROWS = int(os.environ.get("GOOGLE_SHEETS_MIN_SOURCE_ROWS", "0") or "0")
DEFAULT_SHRINK_RATIO = float(os.environ.get("GOOGLE_SHEETS_SHRINK_GUARD_RATIO", "0.85") or "0.85")
TRUE_VALUES = {"true", "1", "y", "yes", "active", "활성", "유지"}
PROTECTED_SKILL_PHRASES = [
    "IP Design Verification",
    "Design Verification",
    "Computer Vision",
    "Recommendation System",
    "Vector Database",
    "Embedded System",
    "System Software",
    "Software Testing",
    "Sensor Fusion",
    "Machine Learning",
    "Deep Learning",
    "Data Pipeline",
    "Model Serving",
    "A/B Testing",
    "Time Series",
    "Natural Language Processing",
    "Clinical Data",
    "Survival Analysis",
    "Statistical Analysis",
]


def clean(value: str) -> str:
    return (value or "").strip()


def pick(*values: str) -> str:
    for value in values:
        normalized = clean(value)
        if normalized:
            return normalized
    return ""


def get(row: dict[str, str], *keys: str) -> str:
    return pick(*(row.get(key, "") for key in keys))


def canonical(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", clean(value).lower())


def split_lines(value: str) -> list[str]:
    lines = []
    for part in re.split(r"[\n\r]+", value or ""):
        token = clean(part)
        if token:
            lines.append(token)
    return lines


def split_tags(value: str) -> list[str]:
    tags = []
    seen = set()
    for part in re.split(r"[\n\r,;/|·]+", value or ""):
        token = clean(part)
        if token and token not in seen:
            seen.add(token)
            tags.append(token)
    return tags


def protect_skill_phrases(value: str) -> tuple[str, dict[str, str]]:
    protected = str(value or "")
    replacements = {}
    for index, phrase in enumerate(sorted(PROTECTED_SKILL_PHRASES, key=len, reverse=True)):
        placeholder = f"__SKILL_PHRASE_{index}__"
        pattern = re.compile(rf"(?<!\S){re.escape(phrase)}(?!\S)", re.IGNORECASE)
        if pattern.search(protected):
            protected = pattern.sub(placeholder, protected)
            replacements[placeholder] = phrase
    return protected, replacements


def split_skills(value: str) -> list[str]:
    skills = []
    seen = set()
    has_explicit_delimiter = bool(re.search(r"[\n\r,;/|·]", value or ""))
    for part in re.split(r"[\n\r,;/|·]+", value or ""):
        token = clean(part)
        if not token:
            continue
        # Stage2 deploy CSV is intentionally compact and may collapse model keyword
        # lists into a single whitespace-separated line. Split long compact lines
        # back into chips, but keep short two-word concepts such as "추천 시스템".
        protected, replacements = protect_skill_phrases(token)
        tokens = (
            re.split(r"\s+", protected)
            if not has_explicit_delimiter and len(protected.split()) >= 3
            else [protected]
        )
        for item in tokens:
            normalized = clean(replacements.get(item, item))
            if normalized and normalized not in seen:
                seen.add(normalized)
                skills.append(normalized)
    return skills


def fetch_rows_from_public_csv() -> list[dict[str, str]]:
    request = urllib.request.Request(
        CSV_URL,
        headers={
            "User-Agent": "career-dashboard-prototype/1.0",
        },
    )
    with urllib.request.urlopen(request) as response:
        content = response.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(content)))


def fetch_rows() -> tuple[list[dict[str, str]], dict]:
    service_account_path = pathlib.Path(SERVICE_ACCOUNT_JSON).expanduser() if SERVICE_ACCOUNT_JSON else None
    if service_account_path and service_account_path.exists():
        rows, source = fetch_sheet_rows(
            spreadsheet_id=SPREADSHEET_ID,
            service_account_json_path=service_account_path,
            gid=GID or None,
            sheet_title=SHEET_TITLE or None,
        )
        return rows, {
            "mode": "google_sheets_api",
            "spreadsheetId": SPREADSHEET_ID,
            "gid": source["sheetId"],
            "sheetTitle": source["sheetTitle"],
            "spreadsheetTitle": source["spreadsheetTitle"],
            "serviceAccountEmail": json.loads(service_account_path.read_text(encoding="utf-8")).get("client_email", ""),
            "rowCount": len(rows),
        }

    rows = fetch_rows_from_public_csv()
    return rows, {
        "mode": "public_csv",
        "spreadsheetId": SPREADSHEET_ID,
        "gid": GID,
        "sheetTitle": SHEET_TITLE,
        "csvUrl": CSV_URL,
        "rowCount": len(rows),
    }


def row_key(row: dict[str, str]) -> str:
    return get(row, "공고키", "job_key", "postingId", "jobId", "id")


def row_change_hash(row: dict[str, str]) -> str:
    return get(row, "변경해시", "change_hash", "sourceHash", "hash")


def parse_active(row: dict[str, str]) -> bool:
    raw = get(row, "활성여부", "is_active")
    if not raw:
        return False
    return clean(raw).lower() in TRUE_VALUES


def read_stage2_deploy_rows(path: pathlib.Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def set_override_if_changed(
    row: dict[str, str],
    *,
    deploy_value: str,
    source_keys: list[str],
    target_keys: list[str],
) -> bool:
    value = clean(deploy_value)
    if not value:
        return False
    source_value = get(row, *source_keys)
    if canonical(source_value) == canonical(value):
        return False
    for key in target_keys:
        row[key] = value
    return True


def apply_stage2_deploy_overrides(
    rows: list[dict[str, str]],
    deploy_csv_path: pathlib.Path,
) -> tuple[list[dict[str, str]], dict]:
    deploy_rows = read_stage2_deploy_rows(deploy_csv_path)
    source_by_id = {row_key(row): row for row in rows if row_key(row)}
    deploy_by_id = {clean(row.get("공고키", "")): row for row in deploy_rows if clean(row.get("공고키", ""))}
    missing_from_source = sorted(set(deploy_by_id) - set(source_by_id))
    missing_from_deploy = sorted(set(source_by_id) - set(deploy_by_id))
    if missing_from_source or missing_from_deploy:
        raise RuntimeError(
            "Refusing to apply stage2 deploy overlay: source/deploy row IDs differ "
            f"(missingFromSource={len(missing_from_source)}, missingFromDeploy={len(missing_from_deploy)})."
        )

    changed_fields = Counter()
    merged_rows = []
    for source_row in rows:
        job_id = row_key(source_row)
        deploy_row = deploy_by_id[job_id]
        row = dict(source_row)
        field_specs = [
            (
                "role",
                deploy_row.get("분류직무", ""),
                ["분류직무", "job_role", "직무명_표시"],
                ["분류직무", "job_role", "직무명_표시"],
            ),
            (
                "focus",
                deploy_row.get("직무초점", ""),
                ["직무초점_표시"],
                ["직무초점_표시"],
            ),
            (
                "keywords",
                deploy_row.get("핵심기술", ""),
                ["핵심기술_표시", "핵심기술_분석용"],
                ["핵심기술_표시"],
            ),
            (
                "summary",
                deploy_row.get("구분요약", ""),
                ["구분요약_표시"],
                ["구분요약_표시"],
            ),
            (
                "company",
                deploy_row.get("회사명_표시", ""),
                ["회사명_표시", "회사명", "company_name"],
                ["회사명_표시"],
            ),
            (
                "title",
                deploy_row.get("공고제목_표시", ""),
                ["공고제목_표시", "공고제목_raw", "job_title_raw"],
                ["공고제목_표시"],
            ),
            (
                "url",
                deploy_row.get("공고URL", ""),
                ["공고URL", "job_url"],
                ["공고URL", "job_url"],
            ),
            (
                "lastSeenAt",
                deploy_row.get("최종발견시각", ""),
                ["최종발견시각", "last_seen_at"],
                ["최종발견시각", "last_seen_at"],
            ),
            (
                "changeHash",
                deploy_row.get("변경해시", ""),
                ["변경해시", "change_hash"],
                ["변경해시", "change_hash"],
            ),
        ]
        for name, deploy_value, source_keys, target_keys in field_specs:
            if set_override_if_changed(
                row,
                deploy_value=deploy_value,
                source_keys=source_keys,
                target_keys=target_keys,
            ):
                changed_fields[name] += 1
        merged_rows.append(row)

    return merged_rows, {
        "enabled": True,
        "deployCsvPath": str(deploy_csv_path),
        "deployRows": len(deploy_rows),
        "sourceRows": len(rows),
        "mergedRows": len(merged_rows),
        "changedFields": dict(changed_fields),
    }


def transform(row: dict[str, str]) -> dict[str, object]:
    return {
        "id": row_key(row),
        "company": get(row, "회사명_표시", "회사명", "company_name"),
        "companyTier": pick(get(row, "기업층", "company_tier"), "미분류"),
        "source": get(row, "소스명_표시", "소스명", "source_name"),
        "title": get(row, "공고제목_표시", "공고제목_raw", "job_title_raw"),
        "experience": pick(get(row, "경력수준_표시", "경력수준_raw", "experience_level_raw"), "미기재"),
        "track": pick(row.get("채용트랙_표시", ""), "미분류"),
        "focus": pick(row.get("직무초점_표시", ""), "미분류"),
        "focusAxes": split_tags(row.get("직무초점_표시", "")),
        "role": pick(get(row, "분류직무", "job_role", "직무명_표시"), "기타"),
        "roleDisplay": pick(get(row, "직무명_표시", "분류직무", "job_role"), "기타"),
        "groupSummary": clean(row.get("구분요약_표시", "")),
        "summaryTags": split_tags(row.get("구분요약_표시", "")),
        "detailBody": clean(row.get("상세본문_분석용", "")),
        "recordState": pick(get(row, "레코드상태", "record_status"), "미분류"),
        "active": parse_active(row),
        "jobUrl": get(row, "공고URL", "job_url"),
        "sourceUrl": get(row, "소스URL", "source_url"),
        "snapshotDate": get(row, "스냅샷일자", "snapshot_date"),
        "firstSeenAt": get(row, "최초발견시각", "first_seen_at"),
        "lastSeenAt": get(row, "최종발견시각", "last_seen_at"),
        "tasks": split_lines(
            pick(row.get("주요업무_표시", ""), row.get("주요업무_분석용", ""))
        ),
        "requirements": split_lines(
            pick(row.get("자격요건_표시", ""), row.get("자격요건_분석용", ""))
        ),
        "preferred": split_lines(
            pick(row.get("우대사항_표시", ""), row.get("우대사항_분석용", ""))
        ),
        "skills": split_skills(
            pick(row.get("핵심기술_표시", ""), row.get("핵심기술_분석용", ""))
        ),
    }


def existing_job_count(path: pathlib.Path = OUTPUT_PATH) -> int:
    if not path.exists():
        return 0
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    jobs = payload.get("jobs", [])
    return len(jobs) if isinstance(jobs, list) else 0


def validate_source_size(
    row_count: int,
    *,
    min_source_rows: int = DEFAULT_MIN_SOURCE_ROWS,
    allow_shrink: bool = False,
    shrink_ratio: float = DEFAULT_SHRINK_RATIO,
) -> dict:
    previous_count = existing_job_count()
    checks = {
        "rowCount": row_count,
        "previousJobCount": previous_count,
        "minSourceRows": min_source_rows,
        "shrinkRatio": shrink_ratio,
        "allowShrink": allow_shrink,
    }
    if min_source_rows and row_count < min_source_rows:
        raise RuntimeError(
            "Refusing to sync Google Sheet snapshot: "
            f"source rows {row_count} < required minimum {min_source_rows}. "
            "Set --allow-shrink only after confirming the source tab is intentionally smaller."
        )
    if previous_count and not allow_shrink:
        minimum_allowed = int(previous_count * shrink_ratio)
        checks["minimumAllowedFromPrevious"] = minimum_allowed
        if row_count < minimum_allowed:
            raise RuntimeError(
                "Refusing to sync Google Sheet snapshot: "
                f"source rows {row_count} would shrink previous local jobs {previous_count} "
                f"below guard ratio {shrink_ratio:.2f}. "
                "Use --allow-shrink only after confirming this is intentional."
            )
    return checks


def sync_sheet_snapshot(
    *,
    dry_run: bool = False,
    min_source_rows: int = DEFAULT_MIN_SOURCE_ROWS,
    allow_shrink: bool = False,
    use_stage2_deploy: bool = False,
    stage2_deploy_csv_path: pathlib.Path = DEFAULT_STAGE2_DEPLOY_CSV,
) -> dict:
    rows, source = fetch_rows()
    stage2_deploy = {"enabled": False}
    if use_stage2_deploy:
        rows, stage2_deploy = apply_stage2_deploy_overrides(rows, stage2_deploy_csv_path)
        source["stage2Deploy"] = stage2_deploy
    size_checks = validate_source_size(
        len(rows),
        min_source_rows=min_source_rows,
        allow_shrink=allow_shrink,
    )
    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "source": source,
        "jobs": [transform(row) for row in rows],
    }

    if dry_run:
        return {
            "payload": payload,
            "rowCount": len(rows),
            "outputPath": str(OUTPUT_PATH),
            "briefingPath": str(OUTPUT_PATH.parent / "briefing.json"),
            "summaryBoardPath": str(OUTPUT_PATH.parent / "summary_board.json"),
            "dryRun": True,
            "sizeChecks": size_checks,
            "stage2Deploy": stage2_deploy,
        }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    briefing_path = OUTPUT_PATH.parent / "briefing.json"
    briefing_path.write_text(
        json.dumps(build_briefing(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    summary_board_path = OUTPUT_PATH.parent / "summary_board.json"
    summary_board_path.write_text(
        json.dumps(build_summary_board(payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return {
        "payload": payload,
        "rowCount": len(rows),
        "outputPath": str(OUTPUT_PATH),
        "briefingPath": str(briefing_path),
        "summaryBoardPath": str(summary_board_path),
        "dryRun": False,
        "sizeChecks": size_checks,
        "stage2Deploy": stage2_deploy,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Read the configured Google Sheet tab and rebuild local dashboard JSON files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Read and validate the sheet but do not write local JSON files.",
    )
    parser.add_argument(
        "--min-source-rows",
        type=int,
        default=DEFAULT_MIN_SOURCE_ROWS,
        help="Abort if the selected sheet has fewer data rows than this value.",
    )
    parser.add_argument(
        "--allow-shrink",
        action="store_true",
        help="Allow syncing even when the selected sheet is much smaller than the current local jobs.json.",
    )
    parser.add_argument(
        "--use-stage2-deploy",
        action="store_true",
        help="Overlay the stage2 deploy CSV on top of the source sheet and sync only gate-approved rows.",
    )
    parser.add_argument(
        "--stage2-deploy-csv",
        type=pathlib.Path,
        default=DEFAULT_STAGE2_DEPLOY_CSV,
        help="Path to the stage2 deploy candidate CSV generated by run_stage2_deploy_gate.py.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    try:
        result = sync_sheet_snapshot(
            dry_run=args.dry_run,
            min_source_rows=args.min_source_rows,
            allow_shrink=args.allow_shrink,
            use_stage2_deploy=args.use_stage2_deploy,
            stage2_deploy_csv_path=args.stage2_deploy_csv,
        )
    except RuntimeError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1) from error
    payload = result["payload"]
    action = "Would write" if result.get("dryRun") else "Wrote"
    print(f"{action} {result['rowCount']} jobs to {result['outputPath']}")
    print(f"{action} briefing to {result['briefingPath']}")
    print(f"{action} summary board to {result['summaryBoardPath']}")
    print(
        "Loaded sheet:",
        payload["source"].get("sheetTitle") or payload["source"].get("gid"),
        f"via {payload['source'].get('mode', 'unknown')}",
    )
    print("Size checks:", json.dumps(result.get("sizeChecks", {}), ensure_ascii=False))


if __name__ == "__main__":
    main()
