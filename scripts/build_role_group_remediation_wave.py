#!/usr/bin/env python3

import csv
import json
import pathlib
from collections import Counter, defaultdict
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
BOARD_PATH = ROOT / "data" / "summary_board.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
OUTPUT_JSON_PATH = ROOT / "data" / "role_group_remediation_wave_001.json"
OUTPUT_CSV_PATH = ROOT / "data" / "role_group_remediation_wave_001.csv"
OUTPUT_MD_PATH = ROOT / "docs" / "role_group_remediation_wave_001.md"


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


def primary_signal_role(row: dict) -> str:
    structured = row.get("structuredSignals", {}) if isinstance(row.get("structuredSignals", {}), dict) else {}
    for value in structured.get("roleSignals", []) if isinstance(structured.get("roleSignals", []), list) else []:
        cleaned = clean(value)
        if cleaned:
            return cleaned
    return ""


def build_item(*, row: dict, job: dict, bucket: str, priority: str, reason: str) -> dict:
    return {
        "id": row.get("id", ""),
        "bucket": bucket,
        "priority": priority,
        "reason": reason,
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "active": bool(row.get("active")),
        "roles": {
            "rawRole": clean(row.get("rawRole", "")),
            "finalRole": clean(row.get("roleGroup", "")),
            "classifierRole": clean(row.get("roleClassifierRole", "")),
            "signalRole": primary_signal_role(row),
        },
        "classifier": {
            "confidence": clean(row.get("roleClassifierConfidence", "")),
            "reason": clean(row.get("roleClassifierReason", "")),
        },
        "current": {
            "summary": clean(row.get("rawSummary", "") or row.get("summary", "")),
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
            "expectedRoleGroup": "",
            "notes": "",
        },
    }


def collect_items(board: dict, jobs_by_id: dict) -> list[dict]:
    rows = board.get("rows", [])
    items = []

    for row in rows:
        row_id = row.get("id", "")
        job = jobs_by_id.get(row_id, {})
        raw_role = clean(row.get("rawRole", ""))
        final_role = clean(row.get("roleGroup", ""))
        classifier_role = clean(row.get("roleClassifierRole", ""))
        classifier_confidence = clean(row.get("roleClassifierConfidence", "")).lower()
        signal_role = primary_signal_role(row)

        if not classifier_role:
            items.append(
                build_item(
                    row=row,
                    job=job,
                    bucket="missing_classifier_output",
                    priority="high",
                    reason="전용 role 분류기 결과가 비어 있음",
                )
            )
            continue

        if classifier_confidence == "low":
            items.append(
                build_item(
                    row=row,
                    job=job,
                    bucket="low_confidence",
                    priority="high",
                    reason="전용 role 분류기가 low confidence 로 판정함",
                )
            )

        if classifier_role != final_role:
            priority = "high" if classifier_confidence == "high" else "medium"
            reason = "전용 role 분류기 결과와 최종 보드 역할이 충돌함"
            if raw_role and signal_role and raw_role == signal_role and classifier_role != raw_role:
                priority = "critical"
                reason = "raw role + signal role 합의와 전용 role 분류기가 충돌함"
            items.append(
                build_item(
                    row=row,
                    job=job,
                    bucket="final_role_conflict",
                    priority=priority,
                    reason=reason,
                )
            )
            continue

        if raw_role and classifier_role and raw_role != classifier_role and classifier_confidence == "high":
            items.append(
                build_item(
                    row=row,
                    job=job,
                    bucket="source_role_disagreement",
                    priority="medium",
                    reason="원본 role 과 전용 role 분류기 결과가 다름",
                )
            )

    return items


def dedupe_items(items: list[dict]) -> list[dict]:
    bucket_rank = {
        "missing_classifier_output": 0,
        "final_role_conflict": 1,
        "low_confidence": 2,
        "source_role_disagreement": 3,
    }
    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    chosen = {}
    for item in sorted(
        items,
        key=lambda value: (
            bucket_rank.get(value["bucket"], 99),
            priority_rank.get(value["priority"], 99),
            value.get("company", ""),
            value.get("title", ""),
        ),
    ):
        if item["id"] not in chosen:
            chosen[item["id"]] = item
    return list(chosen.values())


def write_csv(items: list[dict]) -> None:
    with OUTPUT_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "id",
                "bucket",
                "priority",
                "reason",
                "company",
                "title",
                "rawRole",
                "finalRole",
                "classifierRole",
                "signalRole",
                "confidence",
                "classifierReason",
                "summary",
                "focusLabel",
                "keywords",
                "expectedRoleGroup",
                "notes",
            ],
        )
        writer.writeheader()
        for item in items:
            writer.writerow(
                {
                    "id": item["id"],
                    "bucket": item["bucket"],
                    "priority": item["priority"],
                    "reason": item["reason"],
                    "company": item["company"],
                    "title": item["title"],
                    "rawRole": item["roles"]["rawRole"],
                    "finalRole": item["roles"]["finalRole"],
                    "classifierRole": item["roles"]["classifierRole"],
                    "signalRole": item["roles"]["signalRole"],
                    "confidence": item["classifier"]["confidence"],
                    "classifierReason": item["classifier"]["reason"],
                    "summary": item["current"]["summary"],
                    "focusLabel": item["current"]["focusLabel"],
                    "keywords": ", ".join(item["current"]["keywords"]),
                    "expectedRoleGroup": item["review"]["expectedRoleGroup"],
                    "notes": item["review"]["notes"],
                }
            )


def write_markdown(items: list[dict]) -> None:
    bucket_counts = Counter(item["bucket"] for item in items)
    priority_counts = Counter(item["priority"] for item in items)

    lines = [
        "# Role Group Remediation Wave 001",
        "",
        f"- 총 항목: `{len(items)}`",
        "",
        "## 버킷 분포",
        "",
    ]
    for bucket, count in sorted(bucket_counts.items()):
        lines.append(f"- `{bucket}`: `{count}`")

    lines.extend(["", "## 우선순위 분포", ""])
    for priority, count in sorted(priority_counts.items()):
        lines.append(f"- `{priority}`: `{count}`")

    grouped = defaultdict(list)
    for item in items:
        grouped[item["bucket"]].append(item)

    for bucket in sorted(grouped):
        lines.extend(["", f"## {bucket}", ""])
        sorted_items = sorted(
            grouped[bucket],
            key=lambda item: (item["priority"], item["company"], item["title"]),
        )
        for item in sorted_items[:20]:
            role_info = (
                f"{item['roles']['rawRole']} -> {item['roles']['classifierRole']}"
                if item["roles"]["classifierRole"]
                else item["roles"]["rawRole"]
            )
            lines.append(
                f"- `{item['company']}` | `{item['title']}` | `{item['priority']}` | "
                f"`{role_info}` | `{item['reason']}`"
            )

    OUTPUT_MD_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    board = load_json(BOARD_PATH)
    jobs = load_json(JOBS_PATH).get("jobs", [])
    jobs_by_id = {job.get("id", ""): job for job in jobs}

    items = dedupe_items(collect_items(board, jobs_by_id))
    payload = {
        "generatedAt": now_iso(),
        "counts": {
            "items": len(items),
            "byBucket": dict(Counter(item["bucket"] for item in items)),
            "byPriority": dict(Counter(item["priority"] for item in items)),
        },
        "items": items,
    }
    OUTPUT_JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_csv(items)
    write_markdown(items)
    print(f"Wrote role remediation wave to {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    main()
