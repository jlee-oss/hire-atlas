#!/usr/bin/env python3

import argparse
import json
import pathlib
from collections import Counter, defaultdict
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
BOARD_PATH = ROOT / "data" / "summary_board.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
OUTPUT_PATH = ROOT / "data" / "eval_set.json"


QUALITY_PRIORITY = {"high": 0, "medium": 1, "low": 2, "": 3}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def row_sort_key(row: dict) -> tuple:
    return (
        QUALITY_PRIORITY.get(row.get("summaryQuality", ""), 9),
        0 if row.get("active") else 1,
        clean(row.get("roleGroup", "")),
        clean(row.get("clusterId", "")),
        clean(row.get("company", "")),
        clean(row.get("title", "")),
        row.get("id", ""),
    )


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


def build_eval_record(row: dict, job: dict) -> dict:
    return {
        "id": row["id"],
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "roleGroup": row.get("roleGroup", ""),
        "clusterId": row.get("clusterId", ""),
        "clusterLabel": row.get("clusterLabel", ""),
        "summaryQuality": row.get("summaryQuality", ""),
        "active": bool(row.get("active")),
        "current": {
            "summary": row.get("summary", ""),
            "focusLabel": row.get("focusLabel", ""),
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
            "pass": None,
            "notes": "",
        },
    }


def cycle_sample(pool: list[dict], target_count: int) -> list[dict]:
    if target_count <= 0 or not pool:
        return []

    buckets = defaultdict(list)
    for row in sorted(pool, key=row_sort_key):
        key = (
            row.get("roleGroup", "기타"),
            row.get("clusterId", "other"),
            "active" if row.get("active") else "inactive",
        )
        buckets[key].append(row)

    ordered_keys = sorted(
        buckets,
        key=lambda key: (
            len(buckets[key]),
            key[0],
            key[1],
            key[2],
        ),
    )

    selected = []
    seen = set()
    while len(selected) < target_count:
        progressed = False
        for key in ordered_keys:
            bucket = buckets[key]
            while bucket and bucket[0]["id"] in seen:
                bucket.pop(0)
            if not bucket:
                continue
            row = bucket.pop(0)
            selected.append(row)
            seen.add(row["id"])
            progressed = True
            if len(selected) >= target_count:
                break
        if not progressed:
            break
    return selected


def build_eval_set(rows: list[dict], jobs_by_id: dict, target_size: int) -> dict:
    total_rows = len(rows)
    target_size = min(max(target_size, 1), total_rows)

    by_quality = defaultdict(list)
    for row in rows:
        by_quality[row.get("summaryQuality", "")].append(row)

    high_rows = sorted(by_quality.get("high", []), key=row_sort_key)
    medium_rows = sorted(by_quality.get("medium", []), key=row_sort_key)
    low_rows = sorted(by_quality.get("low", []), key=row_sort_key)
    other_rows = sorted(by_quality.get("", []), key=row_sort_key)

    quotas = {
        "high": min(len(high_rows), max(4, round(target_size * 0.08))),
        "medium": min(len(medium_rows), max(24, round(target_size * 0.32))),
    }
    used = quotas["high"] + quotas["medium"]
    quotas["low"] = min(len(low_rows), max(target_size - used, 0))

    selected = []
    selected.extend(cycle_sample(high_rows, quotas["high"]))
    selected.extend(cycle_sample(medium_rows, quotas["medium"]))
    selected.extend(cycle_sample(low_rows, quotas["low"]))

    if len(selected) < target_size:
        already = {row["id"] for row in selected}
        remainder = [
            *medium_rows,
            *low_rows,
            *high_rows,
            *other_rows,
        ]
        for row in sorted(remainder, key=row_sort_key):
            if row["id"] in already:
                continue
            selected.append(row)
            already.add(row["id"])
            if len(selected) >= target_size:
                break

    records = []
    for row in selected:
        job = jobs_by_id.get(row["id"], {})
        records.append(build_eval_record(row, job))

    role_counts = Counter(item["roleGroup"] for item in records)
    quality_counts = Counter(item["summaryQuality"] for item in records)
    cluster_counts = Counter(item["clusterId"] for item in records)
    active_counts = Counter("active" if item["active"] else "inactive" for item in records)

    return {
        "generatedAt": now_iso(),
        "source": {
            "boardPath": str(BOARD_PATH),
            "jobsPath": str(JOBS_PATH),
        },
        "targetSize": target_size,
        "selection": {
            "strategy": "quality-aware stratified round robin",
            "notes": [
                "summaryQuality, roleGroup, clusterId, active 상태를 함께 고려해 샘플을 분산합니다.",
                "low 품질 공고를 충분히 포함해 prompt/후처리 개선 전후 비교가 가능하게 합니다.",
                "희소한 role/cluster 조합이 먼저 들어오도록 작은 bucket 우선 순서를 사용합니다.",
            ],
        },
        "distribution": {
            "roles": dict(role_counts),
            "qualities": dict(quality_counts),
            "clusters": dict(cluster_counts),
            "activity": dict(active_counts),
        },
        "items": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-size", type=int, default=96)
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    board = load_json(BOARD_PATH)
    jobs = load_json(JOBS_PATH)
    rows = board.get("rows", [])
    jobs_by_id = {job["id"]: job for job in jobs.get("jobs", [])}

    payload = build_eval_set(rows, jobs_by_id, args.target_size)
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote eval set to {output_path}")


if __name__ == "__main__":
    main()
