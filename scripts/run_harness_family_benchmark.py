#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from ai_runtime import JOBS_PATH, normalize_summary_prompt_profile_name, request_summaries_resilient
from build_summary_board import OUTPUT_PATH as BOARD_PATH, build_summary_board
from run_full_dataset_validation_harness import collect_anomaly_families


ROOT = JOBS_PATH.parent.parent
DEFAULT_OUTPUT_DIR = ROOT / "data" / "harness_family_benchmarks"
DEFAULT_FAMILIES = [
    "deeptech_in_data_analyst",
    "business_in_engineer_family",
    "tool_first_focus",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_profile_order(primary: str, compare_to: str) -> list[str]:
    order = []
    for name in [primary, compare_to]:
        cleaned = normalize_summary_prompt_profile_name(name)
        if cleaned not in order:
            order.append(cleaned)
    return order


def overlay_candidate_rows(base_rows: list[dict], results_by_id: dict) -> list[dict]:
    rows = []
    for row in base_rows:
        result = results_by_id.get(row.get("id", ""))
        if not result:
            continue
        updated = {
            **row,
            "summary": result.get("summary", ""),
            "focusLabel": result.get("focusLabel", ""),
            "highlightKeywords": result.get("keywords", []) or [],
            "structuredSignals": result.get("structuredSignals", {}) or {},
            "sectionSignalFacets": result.get("sectionSignalFacets", {}) or {},
            "summaryQuality": result.get("quality", ""),
        }
        rows.append(updated)
    return rows


def compute_family_metrics(rows: list[dict], selected_families: list[str]) -> dict:
    families = collect_anomaly_families(rows)
    return {
        "counts": {name: len(families.get(name, [])) for name in selected_families},
        "examples": {
            name: families.get(name, [])[:6]
            for name in selected_families
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--prompt-profile", required=True)
    parser.add_argument("--compare-to", default="field_aware_v3")
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--families", default=",".join(DEFAULT_FAMILIES))
    parser.add_argument("--rebuild-board", action="store_true")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--experiment-id", default="harness_family_benchmark_001")
    args = parser.parse_args()

    jobs_payload = load_json(JOBS_PATH)
    if args.rebuild_board:
        board = build_summary_board(jobs_payload)
        BOARD_PATH.write_text(json.dumps(board, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    else:
        board = load_json(BOARD_PATH)

    rows = board.get("rows", [])
    jobs_by_id = {job.get("id", ""): job for job in jobs_payload.get("jobs", []) if job.get("id")}
    selected_families = [part.strip() for part in args.families.split(",") if part.strip()]
    current_families = collect_anomaly_families(rows)
    selected_job_ids = []
    for family_name in selected_families:
        for item in current_families.get(family_name, []):
            job_id = item.get("id", "")
            if job_id and job_id not in selected_job_ids:
                selected_job_ids.append(job_id)

    eval_jobs = [jobs_by_id[job_id] for job_id in selected_job_ids if job_id in jobs_by_id]
    base_rows = [row for row in rows if row.get("id") in selected_job_ids]
    if not eval_jobs:
        raise SystemExit("No harness-family jobs found.")

    config = {
        "baseUrl": args.base_url,
        "model": args.model,
        "apiKey": args.api_key,
        "temperature": 0.0,
    }

    reports = {}
    for profile_name in build_profile_order(args.prompt_profile, args.compare_to):
        results = request_summaries_resilient(config, eval_jobs, prompt_profile=profile_name)
        result_by_id = {item.get("id", ""): item for item in results if item.get("id")}
        candidate_rows = overlay_candidate_rows(base_rows, result_by_id)
        metrics = compute_family_metrics(candidate_rows, selected_families)
        reports[profile_name] = {
            "promptProfile": profile_name,
            "jobIds": selected_job_ids,
            "metrics": metrics,
        }
        print(f"[{profile_name}] " + " ".join(f"{name}={metrics['counts'][name]}" for name in selected_families))

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{args.experiment_id}.json"
    payload = {
        "generatedAt": now_iso(),
        "provider": {
            "baseUrl": args.base_url,
            "model": args.model,
        },
        "selectedFamilies": selected_families,
        "selectedJobIds": selected_job_ids,
        "results": reports,
    }
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote harness family benchmark to {output_path}")


if __name__ == "__main__":
    main()
