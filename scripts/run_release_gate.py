#!/usr/bin/env python3

import argparse
import json
import pathlib
from datetime import datetime, timezone

from ai_runtime import (
    RELEASE_CONFIG_PATH,
    list_summary_prompt_profiles,
    normalize_summary_prompt_profile_name,
)
from run_goldset_benchmark import (
    GOLDSET_PATH,
    JOBS_PATH,
    build_profile_order as build_goldset_profile_order,
    compute_metrics as compute_goldset_metrics,
    load_goldset_jobs,
    run_profile as run_goldset_profile,
)
from run_prompt_benchmark import (
    EVAL_SET_PATH,
    build_profile_order as build_prompt_profile_order,
    compute_metrics as compute_incremental_metrics,
    load_eval_jobs,
    run_profile as run_incremental_profile,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
INCREMENTAL_EVAL_SET_PATH = ROOT / "data" / "incremental_eval_set.json"
OUTPUT_DIR = ROOT / "data" / "release_gates"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def unique_profile_order(primary: str, compare_to: str) -> list[str]:
    profiles = []
    for builder in (build_goldset_profile_order, build_prompt_profile_order):
        for name in builder(primary, compare_to):
            normalized = normalize_summary_prompt_profile_name(name)
            if normalized not in profiles:
                profiles.append(normalized)
    return profiles


def build_core_dataset_report(
    *,
    config: dict,
    goldset_path: pathlib.Path,
    limit: int,
    profile_order: list[str],
    batch_size: int,
) -> dict:
    jobs = load_goldset_jobs(goldset_path, limit)
    if not jobs:
        raise ValueError("No goldset jobs found")

    results = {}
    for profile_name in profile_order:
        rows = run_goldset_profile(config, jobs, profile_name, batch_size)
        metrics = compute_goldset_metrics(rows)
        results[profile_name] = {
            "promptProfile": profile_name,
            "metrics": metrics,
        }
        print(
            f"[core] [{profile_name}] "
            f"strict={metrics['strictPassRate']:.2%} "
            f"focus={metrics['focusExactRate']:.2%} "
            f"kw_f1={metrics['avgKeywordF1']:.2%} "
            f"low_match={metrics['lowMatchRate']:.2%}"
        )

    return {
        "label": "core",
        "evalSetPath": str(goldset_path),
        "requestedCount": len(jobs),
        "jobIds": [job["id"] for job in jobs],
        "profileOrder": profile_order,
        "results": results,
    }


def build_incremental_dataset_report(
    *,
    config: dict,
    eval_set_path: pathlib.Path,
    jobs_path: pathlib.Path,
    limit: int,
    profile_order: list[str],
    batch_size: int,
) -> dict:
    jobs, eval_by_id = load_eval_jobs(eval_set_path, jobs_path, limit)
    if not jobs:
        raise ValueError("No incremental eval jobs found")

    results = {}
    for profile_name in profile_order:
        run_result = run_incremental_profile(
            config=config,
            jobs=jobs,
            prompt_profile=profile_name,
            batch_size=batch_size,
        )
        metrics = compute_incremental_metrics(run_result["items"], jobs, eval_by_id)
        results[profile_name] = {
            "promptProfile": profile_name,
            "metrics": metrics,
        }
        print(
            f"[incremental] [{profile_name}] "
            f"usable={metrics['usableItemRate']:.2%} "
            f"low={metrics['lowRate']:.2%} "
            f"focus_empty={metrics['emptyFocusLabelRate']:.2%} "
            f"banned_kw={metrics['keywordBannedRate']:.2%}"
        )

    return {
        "label": "incremental",
        "evalSetPath": str(eval_set_path),
        "requestedCount": len(jobs),
        "jobIds": [job["id"] for job in jobs],
        "profileOrder": profile_order,
        "results": results,
    }


def build_gate_report(dataset_reports: dict) -> list[dict]:
    first_dataset = dataset_reports["core"]
    profile_order = first_dataset["profileOrder"]
    if len(profile_order) < 2:
        return []

    baseline_name = profile_order[0]
    rows = []
    for candidate in profile_order[1:]:
        core_baseline = dataset_reports["core"]["results"][baseline_name]["metrics"]
        core_current = dataset_reports["core"]["results"][candidate]["metrics"]
        incremental_baseline = dataset_reports["incremental"]["results"][baseline_name]["metrics"]
        incremental_current = dataset_reports["incremental"]["results"][candidate]["metrics"]
        checks = {
            "core_strict_not_worse": core_current["strictPassRate"] >= core_baseline["strictPassRate"],
            "core_focus_not_worse": core_current["focusExactRate"] >= core_baseline["focusExactRate"],
            "core_keyword_f1_not_worse": core_current["avgKeywordF1"] >= core_baseline["avgKeywordF1"],
            "core_low_match_not_worse": core_current["lowMatchRate"] >= core_baseline["lowMatchRate"],
            "incremental_usable_not_worse": incremental_current["usableItemRate"]
            >= incremental_baseline["usableItemRate"],
            "incremental_low_not_worse": incremental_current["lowRate"] <= incremental_baseline["lowRate"],
            "incremental_banned_not_worse": incremental_current["keywordBannedRate"]
            <= incremental_baseline["keywordBannedRate"],
            "incremental_focus_empty_not_worse": incremental_current["emptyFocusLabelRate"]
            <= incremental_baseline["emptyFocusLabelRate"],
        }
        rows.append(
            {
                "baseline": baseline_name,
                "candidate": candidate,
                "pass": all(checks.values()),
                "checks": checks,
            }
        )
    return rows


def score_candidate(core_metrics: dict, incremental_metrics: dict) -> float:
    return round(
        (core_metrics["strictPassRate"] * 5.0)
        + (core_metrics["focusExactRate"] * 3.0)
        + (core_metrics["avgKeywordF1"] * 2.5)
        + (core_metrics["lowMatchRate"] * 1.5)
        + (incremental_metrics["usableItemRate"] * 2.0)
        - (incremental_metrics["lowRate"] * 1.5)
        - (incremental_metrics["keywordBannedRate"] * 2.0)
        - (incremental_metrics["emptyFocusLabelRate"] * 1.0),
        6,
    )


def select_champion(dataset_reports: dict, gate_rows: list[dict]) -> dict:
    profile_order = dataset_reports["core"]["profileOrder"]
    baseline_name = profile_order[0]
    passed_candidates = [row["candidate"] for row in gate_rows if row["pass"]]
    pool = passed_candidates or [baseline_name]

    ranked = []
    for profile_name in pool:
        core_metrics = dataset_reports["core"]["results"][profile_name]["metrics"]
        incremental_metrics = dataset_reports["incremental"]["results"][profile_name]["metrics"]
        ranked.append(
            {
                "promptProfile": profile_name,
                "score": score_candidate(core_metrics, incremental_metrics),
                "core": core_metrics,
                "incremental": incremental_metrics,
            }
        )
    ranked.sort(
        key=lambda item: (
            -item["score"],
            -item["core"]["strictPassRate"],
            -item["incremental"]["usableItemRate"],
            item["promptProfile"],
        )
    )
    champion = ranked[0]
    return {
        "promptProfile": champion["promptProfile"],
        "score": champion["score"],
        "gatePassed": champion["promptProfile"] in passed_candidates,
        "usedFallbackBaseline": champion["promptProfile"] == baseline_name and not passed_candidates,
        "core": champion["core"],
        "incremental": champion["incremental"],
    }


def write_release_config(*, champion: dict, config: dict, report_path: pathlib.Path) -> pathlib.Path:
    payload = {
        "updatedAt": now_iso(),
        "summaryChampion": {
            "promptProfile": champion["promptProfile"],
            "model": config["model"],
            "baseUrl": config["baseUrl"],
            "score": champion["score"],
            "gatePassed": champion["gatePassed"],
            "usedFallbackBaseline": champion["usedFallbackBaseline"],
            "reportPath": str(report_path),
            "coreMetrics": champion["core"],
            "incrementalMetrics": champion["incremental"],
        },
    }
    RELEASE_CONFIG_PATH.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return RELEASE_CONFIG_PATH


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--prompt-profile", default="field_aware_v3")
    parser.add_argument("--compare-to", default="baseline_v1")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--core-eval-set", default=str(GOLDSET_PATH))
    parser.add_argument("--incremental-eval-set", default=str(INCREMENTAL_EVAL_SET_PATH))
    parser.add_argument("--jobs-path", default=str(JOBS_PATH))
    parser.add_argument("--core-limit", type=int, default=0)
    parser.add_argument("--incremental-limit", type=int, default=0)
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--experiment-id", default="release_gate_001")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    profile_order = unique_profile_order(args.prompt_profile, args.compare_to)
    config = {
        "baseUrl": args.base_url,
        "model": args.model,
        "apiKey": args.api_key,
        "temperature": args.temperature,
    }
    dataset_reports = {
        "core": build_core_dataset_report(
            config=config,
            goldset_path=pathlib.Path(args.core_eval_set),
            limit=args.core_limit,
            profile_order=profile_order,
            batch_size=args.batch_size,
        ),
        "incremental": build_incremental_dataset_report(
            config=config,
            eval_set_path=pathlib.Path(args.incremental_eval_set),
            jobs_path=pathlib.Path(args.jobs_path),
            limit=args.incremental_limit,
            profile_order=profile_order,
            batch_size=args.batch_size,
        ),
    }
    gate_rows = build_gate_report(dataset_reports)
    champion = select_champion(dataset_reports, gate_rows)

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
        "profileOrder": profile_order,
        "datasets": dataset_reports,
        "gateReport": gate_rows,
        "champion": champion,
    }
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote release gate report to {output_path}")
    print(
        "Champion: "
        f"{champion['promptProfile']} "
        f"(gatePassed={champion['gatePassed']}, score={champion['score']})"
    )

    if args.apply:
        config_path = write_release_config(champion=champion, config=config, report_path=output_path)
        print(f"Wrote release config to {config_path}")


if __name__ == "__main__":
    main()
