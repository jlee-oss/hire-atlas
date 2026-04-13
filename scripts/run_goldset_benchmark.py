#!/usr/bin/env python3

import argparse
import json
import pathlib
from collections import Counter
from datetime import datetime, timezone

from ai_runtime import (
    canonicalize_term,
    list_summary_prompt_profiles,
    normalize_inline_text,
    normalize_summary_prompt_profile_name,
    request_summaries_resilient,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
GOLDSET_PATH = ROOT / "data" / "review_goldset_seed_001.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
OUTPUT_DIR = ROOT / "data" / "prompt_benchmarks"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return normalize_inline_text(value)


def canonical_list(values) -> list[str]:
    items = []
    seen = set()
    for value in values or []:
        cleaned = canonicalize_term(value)
        cleaned = clean(cleaned)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        items.append(cleaned)
    return items


def load_goldset_jobs(path: pathlib.Path, limit: int) -> list[dict]:
    items = load_json(path).get("items", [])
    if limit > 0:
        items = items[:limit]

    jobs_payload = load_json(JOBS_PATH)
    jobs_by_id = {job["id"]: job for job in jobs_payload.get("jobs", [])}

    jobs = []
    for item in items:
        source = item.get("input")
        if not isinstance(source, dict):
            source_job = jobs_by_id.get(item.get("id", ""), {})
            source = {
                "detailBody": source_job.get("detailBody", ""),
                "tasks": source_job.get("tasks", []),
                "requirements": source_job.get("requirements", []),
                "preferred": source_job.get("preferred", []),
                "skills": source_job.get("skills", []),
            }

        target = item.get("target")
        if not isinstance(target, dict):
            target = item.get("expected", {})

        jobs.append(
            {
                "id": item.get("id", ""),
                "company": item.get("company", ""),
                "title": item.get("title", ""),
                "roleDisplay": item.get("roleDisplay", "") or item.get("roleGroup", ""),
                "detailBody": source.get("detailBody", ""),
                "tasks": source.get("tasks", []),
                "requirements": source.get("requirements", []),
                "preferred": source.get("preferred", []),
                "skills": source.get("skills", []),
                "target": target,
            }
        )
    return jobs


def run_profile(config: dict, jobs: list[dict], prompt_profile: str, batch_size: int) -> list[dict]:
    results = []
    for index in range(0, len(jobs), max(1, batch_size)):
        batch = jobs[index : index + max(1, batch_size)]
        results.extend(
            request_summaries_resilient(
                config,
                batch,
                prompt_profile=normalize_summary_prompt_profile_name(prompt_profile),
            )
        )
    by_id = {item["id"]: item for item in results}
    merged = []
    for job in jobs:
        result = by_id.get(job["id"], {})
        merged.append(
            {
                "id": job["id"],
                "company": job["company"],
                "title": job["title"],
                "target": job["target"],
                "result": {
                    "summary": clean(result.get("summary", "")),
                    "focusLabel": clean(result.get("focusLabel", "")),
                    "keywords": canonical_list(result.get("keywords", [])),
                    "quality": clean(result.get("quality", "low")).lower() or "low",
                },
            }
        )
    return merged


def keyword_f1(target_keywords: list[str], result_keywords: list[str]) -> float:
    target_set = set(canonical_list(target_keywords))
    result_set = set(canonical_list(result_keywords))
    if not target_set and not result_set:
        return 1.0
    if not target_set or not result_set:
        return 0.0
    overlap = len(target_set & result_set)
    precision = overlap / len(result_set)
    recall = overlap / len(target_set)
    if not precision and not recall:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def compute_metrics(rows: list[dict]) -> dict:
    total = len(rows)
    summary_exact = 0
    focus_exact = 0
    quality_exact = 0
    low_target = 0
    low_matched = 0
    strict_pass = 0
    keyword_f1_sum = 0.0
    summary_empty_mismatch = 0
    focus_empty_mismatch = 0
    quality_counter = Counter()
    failure_examples = []

    for row in rows:
        target = row["target"]
        result = row["result"]

        target_summary = clean(target.get("summary", ""))
        result_summary = clean(result.get("summary", ""))
        target_focus = clean(target.get("focusLabel", ""))
        result_focus = clean(result.get("focusLabel", ""))
        target_quality = clean(target.get("quality", "low")).lower() or "low"
        result_quality = clean(result.get("quality", "low")).lower() or "low"
        f1 = keyword_f1(target.get("keywords", []), result.get("keywords", []))

        quality_counter[result_quality] += 1
        keyword_f1_sum += f1

        summary_match = target_summary == result_summary
        focus_match = target_focus == result_focus
        quality_match = target_quality == result_quality

        if summary_match:
            summary_exact += 1
        if focus_match:
            focus_exact += 1
        if quality_match:
            quality_exact += 1
        if target_quality == "low":
            low_target += 1
            if result_quality == "low":
                low_matched += 1
        if (not target_summary) != (not result_summary):
            summary_empty_mismatch += 1
        if (not target_focus) != (not result_focus):
            focus_empty_mismatch += 1

        if summary_match and focus_match and quality_match and f1 >= 0.8:
            strict_pass += 1
        else:
            failure_examples.append(
                {
                    "id": row["id"],
                    "company": row["company"],
                    "title": row["title"],
                    "target": target,
                    "result": result,
                    "keywordF1": round(f1, 3),
                    "summaryMatch": summary_match,
                    "focusMatch": focus_match,
                    "qualityMatch": quality_match,
                }
            )

    failure_examples.sort(
        key=lambda row: (
            row["summaryMatch"],
            row["focusMatch"],
            row["qualityMatch"],
            row["keywordF1"],
            row["company"],
        )
    )

    return {
        "requestedItems": total,
        "summaryExactRate": round(summary_exact / total, 4) if total else 0,
        "focusExactRate": round(focus_exact / total, 4) if total else 0,
        "qualityExactRate": round(quality_exact / total, 4) if total else 0,
        "lowMatchRate": round(low_matched / low_target, 4) if low_target else 0,
        "avgKeywordF1": round(keyword_f1_sum / total, 4) if total else 0,
        "strictPassRate": round(strict_pass / total, 4) if total else 0,
        "summaryEmptyMismatchRate": round(summary_empty_mismatch / total, 4) if total else 0,
        "focusEmptyMismatchRate": round(focus_empty_mismatch / total, 4) if total else 0,
        "qualityCounts": dict(quality_counter),
        "failureExamples": failure_examples[:10],
    }


def build_profile_order(primary: str, compare_to: str) -> list[str]:
    profiles = []
    for part in (compare_to or "").split(","):
        cleaned = normalize_summary_prompt_profile_name(part)
        if cleaned and cleaned not in profiles:
            profiles.append(cleaned)
    primary_name = normalize_summary_prompt_profile_name(primary)
    if primary_name not in profiles:
        profiles.append(primary_name)
    return profiles


def build_comparison(results_by_profile: dict) -> list[dict]:
    ordered = list(results_by_profile.keys())
    if len(ordered) < 2:
        return []
    baseline_name = ordered[0]
    baseline = results_by_profile[baseline_name]["metrics"]
    rows = []
    for candidate_name in ordered[1:]:
        current = results_by_profile[candidate_name]["metrics"]
        rows.append(
            {
                "baseline": baseline_name,
                "candidate": candidate_name,
                "diff": {
                    "summaryExactRate": round(current["summaryExactRate"] - baseline["summaryExactRate"], 4),
                    "focusExactRate": round(current["focusExactRate"] - baseline["focusExactRate"], 4),
                    "qualityExactRate": round(current["qualityExactRate"] - baseline["qualityExactRate"], 4),
                    "avgKeywordF1": round(current["avgKeywordF1"] - baseline["avgKeywordF1"], 4),
                    "strictPassRate": round(current["strictPassRate"] - baseline["strictPassRate"], 4),
                    "summaryEmptyMismatchRate": round(
                        current["summaryEmptyMismatchRate"] - baseline["summaryEmptyMismatchRate"], 4
                    ),
                },
            }
        )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--prompt-profile", default="field_aware_v5")
    parser.add_argument("--compare-to", default="field_aware_v3")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--goldset", default=str(GOLDSET_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--experiment-id", default="goldset_001")
    args = parser.parse_args()

    jobs = load_goldset_jobs(pathlib.Path(args.goldset), args.limit)
    if not jobs:
        raise SystemExit("No goldset jobs found.")

    config = {
        "baseUrl": args.base_url,
        "model": args.model,
        "apiKey": args.api_key,
        "temperature": args.temperature,
    }

    profile_order = build_profile_order(args.prompt_profile, args.compare_to)
    results_by_profile = {}
    for profile_name in profile_order:
        rows = run_profile(config=config, jobs=jobs, prompt_profile=profile_name, batch_size=args.batch_size)
        metrics = compute_metrics(rows)
        results_by_profile[profile_name] = {
            "promptProfile": profile_name,
            "items": rows,
            "metrics": metrics,
        }
        print(
            f"[{profile_name}] summary={metrics['summaryExactRate']:.2%} "
            f"focus={metrics['focusExactRate']:.2%} "
            f"kw_f1={metrics['avgKeywordF1']:.2%} "
            f"strict={metrics['strictPassRate']:.2%} "
            f"low_match={metrics['lowMatchRate']:.2%}"
        )

    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.experiment_id}.json"
    payload = {
        "generatedAt": now_iso(),
        "experimentId": args.experiment_id,
        "dataset": {
            "goldsetPath": str(pathlib.Path(args.goldset)),
            "requestedCount": len(jobs),
            "jobIds": [job["id"] for job in jobs],
        },
        "model": {
            "baseUrl": args.base_url,
            "model": args.model,
            "temperature": args.temperature,
        },
        "profiles": list_summary_prompt_profiles(),
        "profileOrder": profile_order,
        "results": results_by_profile,
        "comparisons": build_comparison(results_by_profile),
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote goldset benchmark report to {output_path}")


if __name__ == "__main__":
    main()
