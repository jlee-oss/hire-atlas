#!/usr/bin/env python3

import csv
import json
import pathlib
from collections import Counter, defaultdict
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
BOARD_PATH = ROOT / "data" / "summary_board.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
RELEASE_CONFIG_PATH = ROOT / "data" / "model_release_config.json"
OUTPUT_JSON_PATH = ROOT / "data" / "release_remediation_wave_001.json"
OUTPUT_CSV_PATH = ROOT / "data" / "release_remediation_wave_001.csv"
OUTPUT_MD_PATH = ROOT / "docs" / "release_remediation_wave_001.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def compact_list(values, limit: int = 8) -> list[str]:
    items = []
    seen = set()
    for value in values or []:
        cleaned = clean(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        items.append(cleaned)
        if len(items) >= limit:
            break
    return items


def load_release_report() -> dict:
    config = load_json(RELEASE_CONFIG_PATH)
    report_path = pathlib.Path((config.get("summaryChampion") or {}).get("reportPath", ""))
    if not report_path.exists():
        raise FileNotFoundError(f"Release gate report not found: {report_path}")
    return load_json(report_path)


def build_item(
    *,
    row: dict,
    job: dict,
    bucket: str,
    reason: str,
    release_failure: dict | None = None,
) -> dict:
    item = {
        "id": row.get("id", ""),
        "bucket": bucket,
        "reason": reason,
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "roleGroup": row.get("roleGroup", ""),
        "clusterLabel": row.get("clusterLabel", ""),
        "summaryQuality": row.get("summaryQuality", ""),
        "active": bool(row.get("active")),
        "serviceScopeAction": row.get("serviceScopeAction", ""),
        "serviceScopeReason": row.get("serviceScopeReason", ""),
        "current": {
            "summary": clean(row.get("summary", "")),
            "focusLabel": clean(row.get("focusLabel", "")),
            "keywords": compact_list(row.get("highlightKeywords", []), limit=6),
        },
        "source": {
            "detailBody": clean(job.get("detailBody", "")),
            "tasks": compact_list(job.get("tasks", []), limit=6),
            "requirements": compact_list(job.get("requirements", []), limit=6),
            "preferred": compact_list(job.get("preferred", []), limit=6),
            "skills": compact_list(job.get("skills", []), limit=8),
        },
        "review": {
            "expectedSummary": "",
            "expectedFocusLabel": "",
            "expectedKeywords": [],
            "expectedQuality": "",
            "notes": "",
        },
    }
    if release_failure:
        item["releaseFailure"] = release_failure
    return item


def collect_board_low_rows(rows_by_id: dict, jobs_by_id: dict) -> list[dict]:
    items = []
    for row_id, row in rows_by_id.items():
        if clean(row.get("summaryQuality", "")).lower() != "low":
            continue
        job = jobs_by_id.get(row_id, {})
        items.append(
            build_item(
                row=row,
                job=job,
                bucket="board_low_quality",
                reason="현재 서비스 보드에서 low 품질로 남아 있음",
            )
        )
    return items


def collect_core_gate_failures(rows_by_id: dict, jobs_by_id: dict, report: dict) -> list[dict]:
    champion_profile = (report.get("champion") or {}).get("promptProfile", "")
    core_metrics = ((report.get("champion") or {}).get("core") or {})
    failures = core_metrics.get("failureExamples", []) or []
    items = []
    for failure in failures:
        row = rows_by_id.get(failure.get("id", ""), {})
        job = jobs_by_id.get(failure.get("id", ""), {})
        if not row:
            continue
        items.append(
            build_item(
                row=row,
                job=job,
                bucket="core_gate_failure",
                reason=f"{champion_profile} core gate failure",
                release_failure={
                    "type": "core",
                    "result": failure.get("result", {}),
                    "target": failure.get("target", {}),
                    "keywordF1": failure.get("keywordF1"),
                    "summaryMatch": failure.get("summaryMatch"),
                    "focusMatch": failure.get("focusMatch"),
                    "qualityMatch": failure.get("qualityMatch"),
                },
            )
        )
    return items


def collect_incremental_gate_failures(rows_by_id: dict, jobs_by_id: dict, report: dict) -> list[dict]:
    champion_profile = (report.get("champion") or {}).get("promptProfile", "")
    incremental_metrics = ((report.get("champion") or {}).get("incremental") or {})
    failures = incremental_metrics.get("failureExamples", []) or []
    items = []
    for failure in failures:
        row = rows_by_id.get(failure.get("id", ""), {})
        job = jobs_by_id.get(failure.get("id", ""), {})
        if not row:
            continue
        items.append(
            build_item(
                row=row,
                job=job,
                bucket="incremental_gate_failure",
                reason=f"{champion_profile} incremental gate failure",
                release_failure={
                    "type": "incremental",
                    "reasons": failure.get("reasons", []),
                    "result": failure.get("result", {}),
                    "current": failure.get("current", {}),
                },
            )
        )
    return items


def pick_balanced(items: list[dict]) -> list[dict]:
    bucket_targets = {
        "board_low_quality": 12,
        "core_gate_failure": 10,
        "incremental_gate_failure": 8,
    }
    bucketed = defaultdict(list)
    for item in items:
        bucketed[item["bucket"]].append(item)

    selected = []
    seen_ids = set()
    for bucket, target in bucket_targets.items():
        rows = bucketed.get(bucket, [])
        rows = sorted(
            rows,
            key=lambda item: (
                0 if item.get("active") else 1,
                clean(item.get("summaryQuality", "")),
                clean(item.get("company", "")),
                clean(item.get("title", "")),
            ),
        )
        count = 0
        for row in rows:
            if row["id"] in seen_ids:
                continue
            selected.append(row)
            seen_ids.add(row["id"])
            count += 1
            if count >= target:
                break

    for item in sorted(items, key=lambda row: (row["bucket"], row["company"], row["title"])):
        if item["id"] in seen_ids:
            continue
        selected.append(item)
        seen_ids.add(item["id"])

    return selected


def write_csv(items: list[dict]) -> None:
    with OUTPUT_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "bucket",
                "reason",
                "company",
                "title",
                "roleGroup",
                "clusterLabel",
                "summaryQuality",
                "active",
                "currentSummary",
                "currentFocusLabel",
                "currentKeywords",
                "expectedSummary",
                "expectedFocusLabel",
                "expectedKeywords",
                "expectedQuality",
                "notes",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "id": item["id"],
                    "bucket": item["bucket"],
                    "reason": item["reason"],
                    "company": item["company"],
                    "title": item["title"],
                    "roleGroup": item["roleGroup"],
                    "clusterLabel": item["clusterLabel"],
                    "summaryQuality": item["summaryQuality"],
                    "active": item["active"],
                    "currentSummary": item["current"]["summary"],
                    "currentFocusLabel": item["current"]["focusLabel"],
                    "currentKeywords": " | ".join(item["current"]["keywords"]),
                    "expectedSummary": item["review"]["expectedSummary"],
                    "expectedFocusLabel": item["review"]["expectedFocusLabel"],
                    "expectedKeywords": " | ".join(item["review"]["expectedKeywords"]),
                    "expectedQuality": item["review"]["expectedQuality"],
                    "notes": item["review"]["notes"],
                }
            )


def write_markdown(items: list[dict]) -> None:
    bucket_counts = Counter(item["bucket"] for item in items)
    lines = [
        "# Release Remediation Wave 001",
        "",
        f"- 총 항목: `{len(items)}`",
        "",
        "## 버킷 분포",
        "",
    ]
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- `{bucket}`: `{count}`")
    lines.append("")

    grouped = defaultdict(list)
    for item in items:
        grouped[item["bucket"]].append(item)

    for bucket in sorted(grouped):
        lines.append(f"## {bucket}")
        lines.append("")
        for item in grouped[bucket]:
            current_focus = clean(item["current"]["focusLabel"]) or "-"
            lines.append(f"- `{item['company']}` | `{item['title']}` | `{current_focus}`")
        lines.append("")

    OUTPUT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    board = load_json(BOARD_PATH)
    jobs_payload = load_json(JOBS_PATH)
    release_report = load_release_report()

    rows = board.get("rows", [])
    rows_by_id = {row.get("id", ""): row for row in rows if row.get("id")}
    jobs_by_id = {job.get("id", ""): job for job in jobs_payload.get("jobs", []) if job.get("id")}

    items = []
    items.extend(collect_board_low_rows(rows_by_id, jobs_by_id))
    items.extend(collect_core_gate_failures(rows_by_id, jobs_by_id, release_report))
    items.extend(collect_incremental_gate_failures(rows_by_id, jobs_by_id, release_report))
    selected = pick_balanced(items)

    payload = {
        "generatedAt": now_iso(),
        "source": {
            "boardPath": str(BOARD_PATH),
            "jobsPath": str(JOBS_PATH),
            "releaseConfigPath": str(RELEASE_CONFIG_PATH),
            "releaseReportPath": str((release_report.get("champion") or {}).get("reportPath", "")),
        },
        "count": len(selected),
        "distribution": {
            "bucketCounts": dict(Counter(item["bucket"] for item in selected)),
            "qualityCounts": dict(Counter(item["summaryQuality"] for item in selected)),
        },
        "items": selected,
    }
    OUTPUT_JSON_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_csv(selected)
    write_markdown(selected)
    print(f"Wrote JSON to {OUTPUT_JSON_PATH}")
    print(f"Wrote CSV to {OUTPUT_CSV_PATH}")
    print(f"Wrote markdown to {OUTPUT_MD_PATH}")


if __name__ == "__main__":
    main()
