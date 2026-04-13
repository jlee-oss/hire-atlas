#!/usr/bin/env python3

import argparse
import json
import pathlib
from collections import Counter
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS_PATH = ROOT / "data" / "jobs.json"
BOARD_PATH = ROOT / "data" / "summary_board.json"
OUTPUT_PATH = ROOT / "data" / "incremental_eval_set.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def parse_dt(value: str) -> float:
    if not value:
        return 0.0
    try:
        return datetime.fromisoformat(value).timestamp()
    except ValueError:
        return 0.0


def compact_list(values, limit=8) -> list[str]:
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


def build_record(row: dict, job: dict) -> dict:
    return {
        "id": row.get("id", ""),
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "roleGroup": row.get("roleGroup", ""),
        "clusterId": row.get("clusterId", ""),
        "clusterLabel": row.get("clusterLabel", ""),
        "summaryQuality": row.get("summaryQuality", ""),
        "active": bool(row.get("active")),
        "firstSeenAt": job.get("firstSeenAt", ""),
        "lastSeenAt": job.get("lastSeenAt", ""),
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
            "notes": "",
            "pass": None,
        },
    }


def newest_rows(rows: list[dict], jobs_by_id: dict, holdout_size: int) -> list[dict]:
    def row_key(row: dict) -> tuple:
        job = jobs_by_id.get(row.get("id", ""), {})
        return (
            parse_dt(job.get("firstSeenAt", "")),
            parse_dt(job.get("lastSeenAt", "")),
            clean(row.get("company", "")),
            clean(row.get("title", "")),
            row.get("id", ""),
        )

    ordered = sorted(rows, key=row_key, reverse=True)
    return ordered[:holdout_size]


def build_payload(rows: list[dict], jobs_by_id: dict, holdout_size: int) -> dict:
    selected_rows = newest_rows(rows, jobs_by_id, holdout_size)
    items = [build_record(row, jobs_by_id.get(row.get("id", ""), {})) for row in selected_rows]

    role_counts = Counter(item["roleGroup"] for item in items)
    quality_counts = Counter(item["summaryQuality"] for item in items)
    cluster_counts = Counter(item["clusterId"] for item in items)
    active_counts = Counter("active" if item["active"] else "inactive" for item in items)

    first_dates = [item["firstSeenAt"] for item in items if item["firstSeenAt"]]
    last_dates = [item["lastSeenAt"] for item in items if item["lastSeenAt"]]

    return {
        "generatedAt": now_iso(),
        "source": {
            "boardPath": str(BOARD_PATH),
            "jobsPath": str(JOBS_PATH),
        },
        "selection": {
            "strategy": "most-recent firstSeenAt holdout",
            "holdoutSize": len(items),
            "notes": [
                "가장 최근에 유입된 공고를 별도 검증셋으로 고정합니다.",
                "이 셋은 prompt/후처리 튜닝의 직접 근거가 아니라, 일반화 확인용으로 사용합니다.",
            ],
        },
        "dateRange": {
            "firstSeenMin": min(first_dates) if first_dates else "",
            "firstSeenMax": max(first_dates) if first_dates else "",
            "lastSeenMin": min(last_dates) if last_dates else "",
            "lastSeenMax": max(last_dates) if last_dates else "",
        },
        "distribution": {
            "roles": dict(role_counts),
            "qualities": dict(quality_counts),
            "clusters": dict(cluster_counts),
            "activity": dict(active_counts),
        },
        "items": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--holdout-size", type=int, default=48)
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    board = load_json(BOARD_PATH)
    jobs = load_json(JOBS_PATH)
    rows = board.get("rows", [])
    jobs_by_id = {job["id"]: job for job in jobs.get("jobs", [])}

    payload = build_payload(rows, jobs_by_id, max(1, args.holdout_size))
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote incremental holdout to {output_path}")


if __name__ == "__main__":
    main()
