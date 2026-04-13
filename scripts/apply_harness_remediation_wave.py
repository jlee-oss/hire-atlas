#!/usr/bin/env python3

import argparse
import json
from pathlib import Path

from ai_runtime import (
    JOBS_PATH,
    get_release_prompt_profile,
    load_summary_store,
    request_summaries_resilient,
    save_summary_batch,
)
from build_summary_board import OUTPUT_PATH as BOARD_PATH, build_summary_board
from classify_role_groups import run_role_group_model_pipeline
from classify_service_scope_candidates import run_service_scope_model_pipeline
from run_full_dataset_validation_harness import OUTPUT_JSON as HARNESS_JSON_PATH, OUTPUT_MD as HARNESS_MD_PATH, main as _unused  # noqa: F401
from run_full_dataset_validation_harness import FAMILY_SEVERITY, collect_anomaly_families, render_md as render_harness_md


ROOT = JOBS_PATH.parent.parent
WAVE_PATH = ROOT / "data" / "harness_remediation_wave_001.json"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def build_harness_report(board: dict, jobs_payload: dict) -> dict:
    rows = board.get("rows", [])
    diagnostics = board.get("diagnostics", {}) if isinstance(board.get("diagnostics", {}), dict) else {}
    excluded_rows = diagnostics.get("excludedRows", []) if isinstance(diagnostics.get("excludedRows", []), list) else []
    review_rows = diagnostics.get("reviewRows", []) if isinstance(diagnostics.get("reviewRows", []), list) else []
    families = collect_anomaly_families(rows)
    report = {
        "generatedAt": board.get("updatedAt", ""),
        "metrics": {
            "sourceJobs": len(jobs_payload.get("jobs", [])),
            "displayJobs": len(rows),
            "excludedJobs": len(excluded_rows),
            "reviewJobs": len(review_rows),
            "summaryCoverage": (board.get("overview", {}) or {}).get("summaryCoverage"),
            "missingSummaries": (board.get("overview", {}) or {}).get("missingSummaries"),
            "staleRoleOverrides": 0,
            "staleServiceScopeOverrides": 0,
        },
        "staleRoleOverrideIds": [],
        "staleServiceScopeOverrideIds": [],
        "families": {
            name: {
                "severity": FAMILY_SEVERITY.get(name, "info"),
                "count": len(items),
                "jobIds": [item["id"] for item in items],
                "examples": items[:12],
            }
            for name, items in families.items()
        },
        "distribution": {
            "displayRoles": {},
            "excludedActions": {},
        },
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--prompt-profile", default=get_release_prompt_profile())
    parser.add_argument("--wave-path", default=str(WAVE_PATH))
    parser.add_argument("--batch-size", type=int, default=4)
    args = parser.parse_args()

    wave = load_json(Path(args.wave_path))
    selected_job_ids = []
    for family in wave.get("families", []):
        for job_id in family.get("jobIds", []):
            if job_id and job_id not in selected_job_ids:
                selected_job_ids.append(job_id)
    if not selected_job_ids:
        raise SystemExit("No remediation-wave job ids found.")

    jobs_payload = load_json(JOBS_PATH)
    jobs_by_id = {job.get("id", ""): job for job in jobs_payload.get("jobs", []) if job.get("id")}
    jobs = [jobs_by_id[job_id] for job_id in selected_job_ids if job_id in jobs_by_id]
    if not jobs:
        raise SystemExit("No remediation jobs resolved from jobs.json.")

    config = {
        "baseUrl": args.base_url,
        "model": args.model,
        "apiKey": args.api_key,
        "temperature": 0.0,
    }

    summaries = request_summaries_resilient(config, jobs, prompt_profile=args.prompt_profile)
    save_summary_batch(config, summaries, prompt_profile=args.prompt_profile)
    run_service_scope_model_pipeline(config, job_ids=selected_job_ids, mode="all", batch_size=max(1, args.batch_size))
    run_role_group_model_pipeline(config, job_ids=selected_job_ids, mode="all", batch_size=max(1, args.batch_size))

    board = build_summary_board(jobs_payload)
    write_json(BOARD_PATH, board)

    harness_report = build_harness_report(board, jobs_payload)
    write_json(HARNESS_JSON_PATH, harness_report)
    write_text(HARNESS_MD_PATH, render_harness_md(harness_report))

    print(
        json.dumps(
            {
                "updatedJobs": len(jobs),
                "promptProfile": args.prompt_profile,
                "boardPath": str(BOARD_PATH),
                "harnessPath": str(HARNESS_JSON_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
