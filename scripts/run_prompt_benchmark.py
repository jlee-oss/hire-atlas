#!/usr/bin/env python3

import argparse
import json
import pathlib
import re
from collections import Counter
from datetime import datetime, timezone

from ai_runtime import (
    is_generic_keyword,
    list_summary_prompt_profiles,
    normalize_inline_text,
    normalize_summary_prompt_profile_name,
    request_summaries_resilient,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
EVAL_SET_PATH = ROOT / "data" / "eval_set.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
OUTPUT_DIR = ROOT / "data" / "prompt_benchmarks"

SENTENCE_ENDINGS = (
    "합니다",
    "됩니다",
    "있습니다",
    "하세요",
    "십시오",
    "입니다",
)
KEYWORD_BANNED_PATTERNS = [
    r"\b(위한|또는|대한|통한|관련)\b",
    r"\b(학력|학위|학사|석사|박사|경력)\b",
    r"\b(제품|서비스|기술|업무)\b",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return normalize_inline_text(value)


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


def compact_job(job: dict) -> dict:
    return {
        "id": job.get("id", ""),
        "company": clean(job.get("company", "")),
        "title": clean(job.get("title", "")),
        "roleDisplay": clean(job.get("roleDisplay", "")),
        "detailBody": clean(job.get("detailBody", "")),
        "tasks": compact_list(job.get("tasks", []), limit=6),
        "requirements": compact_list(job.get("requirements", []), limit=6),
        "preferred": compact_list(job.get("preferred", []), limit=6),
        "skills": compact_list(job.get("skills", []), limit=8),
    }


def load_eval_jobs(eval_set_path: pathlib.Path, jobs_path: pathlib.Path, limit: int) -> tuple[list[dict], dict]:
    eval_payload = load_json(eval_set_path)
    jobs_payload = load_json(jobs_path)
    jobs_by_id = {job["id"]: job for job in jobs_payload.get("jobs", [])}

    items = eval_payload.get("items", [])
    if limit > 0:
        items = items[:limit]

    selected_jobs = []
    eval_by_id = {}
    for item in items:
        job_id = item.get("id", "")
        job = jobs_by_id.get(job_id)
        if not job:
            continue
        selected_jobs.append(job)
        eval_by_id[job_id] = item
    return selected_jobs, eval_by_id


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def looks_sentence_like(value: str) -> bool:
    cleaned = clean(value)
    if not cleaned:
        return False
    if len(cleaned) >= 28:
        return True
    if any(cleaned.endswith(ending) for ending in SENTENCE_ENDINGS):
        return True
    if cleaned.count(" ") >= 4:
        return True
    if re.search(r"[,.:;()]", cleaned):
        return True
    return False


def has_banned_pattern(value: str) -> bool:
    cleaned = clean(value)
    if not cleaned:
        return False
    if is_generic_keyword(cleaned):
        return True
    return any(re.search(pattern, cleaned) for pattern in KEYWORD_BANNED_PATTERNS)


def summarize_failures(results_by_id: dict, eval_by_id: dict, limit: int = 8) -> list[dict]:
    failures = []
    for job_id, result in results_by_id.items():
        item = eval_by_id.get(job_id, {})
        keywords = result.get("keywords", [])
        reasons = []
        if result.get("quality") == "low":
            reasons.append("quality=low")
        if not result.get("summary"):
            reasons.append("empty_summary")
        if not result.get("focusLabel"):
            reasons.append("empty_focus_label")
        if any(has_banned_pattern(keyword) for keyword in keywords):
            reasons.append("banned_keyword")
        if any(looks_sentence_like(keyword) for keyword in keywords):
            reasons.append("sentence_like_keyword")
        if not reasons:
            continue
        failures.append(
            {
                "id": job_id,
                "company": item.get("company", ""),
                "title": item.get("title", ""),
                "reasons": reasons,
                "result": {
                    "summary": result.get("summary", ""),
                    "focusLabel": result.get("focusLabel", ""),
                    "keywords": keywords,
                    "quality": result.get("quality", ""),
                },
                "current": item.get("current", {}),
            }
        )
    failures.sort(
        key=lambda row: (
            0 if "banned_keyword" in row["reasons"] else 1,
            0 if "sentence_like_keyword" in row["reasons"] else 1,
            0 if "quality=low" in row["reasons"] else 1,
            row["company"],
            row["title"],
        )
    )
    return failures[:limit]


def compute_metrics(results: list[dict], requested_jobs: list[dict], eval_by_id: dict) -> dict:
    requested_ids = [job["id"] for job in requested_jobs]
    results_by_id = {item["id"]: item for item in results}
    returned_ids = [job_id for job_id in requested_ids if job_id in results_by_id]

    quality_counts = Counter()
    total_keywords = 0
    banned_keywords = 0
    sentence_like_keywords = 0
    long_keywords = 0
    focus_banned = 0
    empty_summary = 0
    empty_focus = 0
    usable_items = 0
    suspicious_counter = Counter()
    average_keyword_lengths = []

    for job_id in requested_ids:
        result = results_by_id.get(job_id)
        if not result:
            continue

        summary = clean(result.get("summary", ""))
        focus_label = clean(result.get("focusLabel", ""))
        keywords = compact_list(result.get("keywords", []), limit=6)
        quality = clean(result.get("quality", "low")).lower() or "low"
        quality_counts[quality] += 1

        if not summary:
            empty_summary += 1
        if not focus_label:
            empty_focus += 1

        if focus_label and has_banned_pattern(focus_label):
            focus_banned += 1
            suspicious_counter[focus_label] += 1

        if summary and focus_label and len(keywords) >= 2 and quality != "low":
            usable_items += 1

        for keyword in keywords:
            total_keywords += 1
            average_keyword_lengths.append(len(keyword))
            if has_banned_pattern(keyword):
                banned_keywords += 1
                suspicious_counter[keyword] += 1
            if looks_sentence_like(keyword):
                sentence_like_keywords += 1
                suspicious_counter[keyword] += 1
            if len(keyword) >= 18:
                long_keywords += 1

    requested_total = len(requested_ids)
    returned_total = len(returned_ids)
    missing_ids = [job_id for job_id in requested_ids if job_id not in results_by_id]

    return {
        "requestedItems": requested_total,
        "returnedItems": returned_total,
        "coverageRate": round(returned_total / requested_total, 4) if requested_total else 0,
        "missingIds": missing_ids,
        "qualityCounts": dict(quality_counts),
        "emptySummaryRate": round(empty_summary / returned_total, 4) if returned_total else 0,
        "emptyFocusLabelRate": round(empty_focus / returned_total, 4) if returned_total else 0,
        "lowRate": round(quality_counts.get("low", 0) / returned_total, 4) if returned_total else 0,
        "usableItemRate": round(usable_items / returned_total, 4) if returned_total else 0,
        "avgKeywordsPerItem": round(total_keywords / returned_total, 2) if returned_total else 0,
        "avgKeywordLength": round(sum(average_keyword_lengths) / len(average_keyword_lengths), 2)
        if average_keyword_lengths
        else 0,
        "keywordBannedRate": round(banned_keywords / total_keywords, 4) if total_keywords else 0,
        "focusLabelBannedRate": round(focus_banned / returned_total, 4) if returned_total else 0,
        "sentenceLikeKeywordRate": round(sentence_like_keywords / total_keywords, 4) if total_keywords else 0,
        "longKeywordRate": round(long_keywords / total_keywords, 4) if total_keywords else 0,
        "suspiciousTerms": [
            {"term": term, "count": count}
            for term, count in suspicious_counter.most_common(12)
        ],
        "failureExamples": summarize_failures(results_by_id, eval_by_id, limit=8),
    }


def run_profile(config: dict, jobs: list[dict], prompt_profile: str, batch_size: int) -> dict:
    normalized_profile = normalize_summary_prompt_profile_name(prompt_profile)
    results = []
    for batch in chunked(jobs, max(1, batch_size)):
        results.extend(
            request_summaries_resilient(
                config,
                batch,
                prompt_profile=normalized_profile,
            )
        )
    unique = []
    seen = set()
    for item in results:
        job_id = item.get("id", "")
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)
        unique.append(
            {
                "id": job_id,
                "summary": clean(item.get("summary", "")),
                "focusLabel": clean(item.get("focusLabel", "")),
                "keywords": compact_list(item.get("keywords", []), limit=6),
                "quality": clean(item.get("quality", "low")).lower() or "low",
            }
        )
    return {"promptProfile": normalized_profile, "items": unique}


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
    ordered_profiles = list(results_by_profile.keys())
    if len(ordered_profiles) < 2:
        return []
    baseline_name = ordered_profiles[0]
    baseline = results_by_profile[baseline_name]["metrics"]
    comparisons = []
    for profile_name in ordered_profiles[1:]:
        current = results_by_profile[profile_name]["metrics"]
        comparisons.append(
            {
                "baseline": baseline_name,
                "candidate": profile_name,
                "diff": {
                    "coverageRate": round(current["coverageRate"] - baseline["coverageRate"], 4),
                    "usableItemRate": round(current["usableItemRate"] - baseline["usableItemRate"], 4),
                    "lowRate": round(current["lowRate"] - baseline["lowRate"], 4),
                    "keywordBannedRate": round(
                        current["keywordBannedRate"] - baseline["keywordBannedRate"], 4
                    ),
                    "sentenceLikeKeywordRate": round(
                        current["sentenceLikeKeywordRate"] - baseline["sentenceLikeKeywordRate"], 4
                    ),
                    "emptySummaryRate": round(
                        current["emptySummaryRate"] - baseline["emptySummaryRate"], 4
                    ),
                },
            }
        )
    return comparisons


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--prompt-profile", default="field_aware_v2")
    parser.add_argument("--compare-to", default="baseline_v1")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--eval-set", default=str(EVAL_SET_PATH))
    parser.add_argument("--jobs-path", default=str(JOBS_PATH))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--experiment-id", default="experiment_001")
    args = parser.parse_args()

    available_profiles = list_summary_prompt_profiles()
    profile_order = build_profile_order(args.prompt_profile, args.compare_to)
    jobs, eval_by_id = load_eval_jobs(
        pathlib.Path(args.eval_set),
        pathlib.Path(args.jobs_path),
        args.limit,
    )
    if not jobs:
        raise SystemExit("No eval jobs found for benchmark.")

    config = {
        "baseUrl": args.base_url,
        "model": args.model,
        "apiKey": args.api_key,
        "temperature": args.temperature,
    }

    results_by_profile = {}
    for profile_name in profile_order:
        run_result = run_profile(
            config=config,
            jobs=jobs,
            prompt_profile=profile_name,
            batch_size=args.batch_size,
        )
        metrics = compute_metrics(run_result["items"], jobs, eval_by_id)
        results_by_profile[profile_name] = {
            "promptProfile": profile_name,
            "items": run_result["items"],
            "metrics": metrics,
        }
        print(
            f"[{profile_name}] coverage={metrics['coverageRate']:.2%} "
            f"usable={metrics['usableItemRate']:.2%} "
            f"low={metrics['lowRate']:.2%} "
            f"banned_kw={metrics['keywordBannedRate']:.2%} "
            f"sentence_kw={metrics['sentenceLikeKeywordRate']:.2%}"
        )

    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.experiment_id}.json"

    payload = {
        "generatedAt": now_iso(),
        "experimentId": args.experiment_id,
        "dataset": {
            "evalSetPath": str(pathlib.Path(args.eval_set)),
            "jobsPath": str(pathlib.Path(args.jobs_path)),
            "requestedCount": len(jobs),
            "jobIds": [job["id"] for job in jobs],
        },
        "model": {
            "baseUrl": args.base_url,
            "model": args.model,
            "temperature": args.temperature,
        },
        "profiles": available_profiles,
        "profileOrder": profile_order,
        "results": results_by_profile,
        "comparisons": build_comparison(results_by_profile),
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote benchmark report to {output_path}")


if __name__ == "__main__":
    main()
