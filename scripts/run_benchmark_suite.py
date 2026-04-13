#!/usr/bin/env python3

import argparse
import json
import pathlib
from datetime import datetime, timezone

from ai_runtime import list_summary_prompt_profiles, normalize_summary_prompt_profile_name
from run_prompt_benchmark import (
    EVAL_SET_PATH,
    JOBS_PATH,
    OUTPUT_DIR,
    build_comparison,
    build_profile_order,
    compute_metrics,
    load_eval_jobs,
    run_profile,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
INCREMENTAL_EVAL_SET_PATH = ROOT / "data" / "incremental_eval_set.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def run_dataset_benchmark(
    *,
    config: dict,
    dataset_label: str,
    eval_set_path: pathlib.Path,
    jobs_path: pathlib.Path,
    profile_order: list[str],
    batch_size: int,
    limit: int,
) -> dict:
    jobs, eval_by_id = load_eval_jobs(eval_set_path, jobs_path, limit)
    if not jobs:
        raise ValueError(f"No jobs found for dataset: {dataset_label}")

    results_by_profile = {}
    for profile_name in profile_order:
        run_result = run_profile(
            config=config,
            jobs=jobs,
            prompt_profile=profile_name,
            batch_size=batch_size,
        )
        metrics = compute_metrics(run_result["items"], jobs, eval_by_id)
        results_by_profile[profile_name] = {
            "promptProfile": profile_name,
            "items": run_result["items"],
            "metrics": metrics,
        }
        print(
            f"[{dataset_label}] [{profile_name}] "
            f"usable={metrics['usableItemRate']:.2%} "
            f"low={metrics['lowRate']:.2%} "
            f"focus_empty={metrics['emptyFocusLabelRate']:.2%} "
            f"banned_kw={metrics['keywordBannedRate']:.2%}"
        )

    return {
        "label": dataset_label,
        "evalSetPath": str(eval_set_path),
        "requestedCount": len(jobs),
        "jobIds": [job["id"] for job in jobs],
        "profileOrder": profile_order,
        "results": results_by_profile,
        "comparisons": build_comparison(results_by_profile),
    }


def build_gate_report(dataset_reports: dict) -> list[dict]:
    labels = list(dataset_reports.keys())
    if not labels:
        return []

    first_label = labels[0]
    first_order = dataset_reports[first_label]["profileOrder"]
    if len(first_order) < 2:
        return []

    baseline_name = first_order[0]
    candidates = first_order[1:]
    gate_rows = []

    for candidate in candidates:
        checks = []
        for label in labels:
            report = dataset_reports[label]
            baseline = report["results"][baseline_name]["metrics"]
            current = report["results"][candidate]["metrics"]
            checks.append(
                {
                    "dataset": label,
                    "usable_not_worse": current["usableItemRate"] >= baseline["usableItemRate"],
                    "low_not_worse": current["lowRate"] <= baseline["lowRate"],
                    "banned_not_worse": current["keywordBannedRate"] <= baseline["keywordBannedRate"],
                    "focus_empty_not_worse": current["emptyFocusLabelRate"]
                    <= baseline["emptyFocusLabelRate"],
                }
            )
        gate_rows.append(
            {
                "baseline": baseline_name,
                "candidate": candidate,
                "pass": all(
                    all(check[key] for key in check if key != "dataset") for check in checks
                ),
                "checks": checks,
            }
        )
    return gate_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--prompt-profile", default="field_aware_v3")
    parser.add_argument("--compare-to", default="baseline_v1")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--core-eval-set", default=str(EVAL_SET_PATH))
    parser.add_argument("--incremental-eval-set", default=str(INCREMENTAL_EVAL_SET_PATH))
    parser.add_argument("--jobs-path", default=str(JOBS_PATH))
    parser.add_argument("--core-limit", type=int, default=0)
    parser.add_argument("--incremental-limit", type=int, default=0)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--experiment-id", default="suite_001_smoke")
    args = parser.parse_args()

    profile_order = build_profile_order(args.prompt_profile, args.compare_to)
    config = {
        "baseUrl": args.base_url,
        "model": args.model,
        "apiKey": args.api_key,
        "temperature": args.temperature,
    }

    dataset_reports = {}
    dataset_reports["core"] = run_dataset_benchmark(
        config=config,
        dataset_label="core",
        eval_set_path=pathlib.Path(args.core_eval_set),
        jobs_path=pathlib.Path(args.jobs_path),
        profile_order=profile_order,
        batch_size=args.batch_size,
        limit=args.core_limit,
    )
    dataset_reports["incremental"] = run_dataset_benchmark(
        config=config,
        dataset_label="incremental",
        eval_set_path=pathlib.Path(args.incremental_eval_set),
        jobs_path=pathlib.Path(args.jobs_path),
        profile_order=profile_order,
        batch_size=args.batch_size,
        limit=args.incremental_limit,
    )

    output_dir = pathlib.Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.experiment_id}.json"

    payload = {
        "generatedAt": now_iso(),
        "experimentId": args.experiment_id,
        "model": {
            "baseUrl": args.base_url,
            "model": args.model,
            "temperature": args.temperature,
        },
        "profiles": list_summary_prompt_profiles(),
        "profileOrder": [normalize_summary_prompt_profile_name(name) for name in profile_order],
        "datasets": dataset_reports,
        "gateReport": build_gate_report(dataset_reports),
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote benchmark suite report to {output_path}")


if __name__ == "__main__":
    main()
