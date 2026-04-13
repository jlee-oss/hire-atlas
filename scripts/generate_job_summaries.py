#!/usr/bin/env python3

import argparse
import json

from ai_runtime import (
    get_jobs_payload,
    get_release_prompt_profile,
    load_summary_store,
    request_cluster_labels,
    request_summaries_resilient,
    save_company_clusters,
    save_summary_batch,
)
from build_summary_board import (
    OUTPUT_PATH,
    build_base_rows,
    build_cluster_label_seeds,
    build_company_profiles,
    build_dynamic_cluster_payload,
    build_summary_board,
)
from classify_service_scope_candidates import run_service_scope_model_pipeline
from classify_role_groups import run_role_group_model_pipeline


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def summary_needs_refresh(item: dict) -> bool:
    quality = str(item.get("quality", "")).strip().lower()
    return (
        not item.get("summarizedAt")
        or not quality
        or quality == "low"
    )


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--batch-size", type=int, default=2)
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--mode", choices=["missing", "all", "stale"], default="missing")
    parser.add_argument("--prompt-profile", default=get_release_prompt_profile())
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--skip-service-scope", action="store_true")
    parser.add_argument("--skip-role-groups", action="store_true")
    args = parser.parse_args()

    config = {
        "baseUrl": args.base_url,
        "model": args.model,
        "apiKey": args.api_key,
        "temperature": args.temperature,
    }

    payload = get_jobs_payload()
    store = load_summary_store()
    summary_items = store.get("items", {})

    jobs = payload["jobs"]

    if args.mode == "missing":
        jobs = [
            job
            for job in jobs
            if job["id"] not in summary_items
            or summary_needs_refresh(summary_items[job["id"]])
        ]
    elif args.mode == "stale":
        jobs = [
            job
            for job in jobs
            if job["id"] not in summary_items
            or summary_items[job["id"]].get("provider", {}).get("promptProfile") != args.prompt_profile
            or summary_needs_refresh(summary_items[job["id"]])
        ]
    if args.limit > 0:
        jobs = jobs[: args.limit]

    total = len(jobs)
    if not total:
        print("No jobs to summarize.")
        return

    done = 0
    processed_ids = []
    for batch in chunked(jobs, max(1, args.batch_size)):
        summaries = request_summaries_resilient(
            config,
            batch,
            prompt_profile=args.prompt_profile,
        )
        save_summary_batch(
            config,
            summaries,
            prompt_profile=args.prompt_profile,
        )
        done += len(batch)
        processed_ids.extend(job["id"] for job in batch)
        print(f"Processed {done}/{total}")

    if processed_ids and not args.skip_service_scope:
        scope_result = run_service_scope_model_pipeline(
            config,
            job_ids=processed_ids,
            mode="all",
            batch_size=max(1, args.batch_size),
        )
        print(
            "Service scope: "
            f"{scope_result['processed']} processed / "
            f"{scope_result['include']} include / "
            f"{scope_result['exclude']} exclude / "
            f"{scope_result['lowConfidence']} low-confidence"
        )

    if processed_ids and not args.skip_role_groups:
        role_result = run_role_group_model_pipeline(
            config,
            job_ids=processed_ids,
            mode="all",
            batch_size=max(1, args.batch_size),
        )
        print(
            "Role groups: "
            f"{role_result['processed']} processed / "
            f"AE {role_result.get('인공지능 엔지니어', 0)} / "
            f"AR {role_result.get('인공지능 리서처', 0)} / "
            f"DS {role_result.get('데이터 사이언티스트', 0)} / "
            f"DA {role_result.get('데이터 분석가', 0)} / "
            f"low {role_result['lowConfidence']}"
        )

    rows = build_base_rows(payload)
    company_profiles = build_company_profiles(rows)
    cluster_items = build_dynamic_cluster_payload(rows, company_profiles)
    cluster_items = request_cluster_labels(
        config,
        build_cluster_label_seeds(cluster_items, company_profiles),
    )
    if cluster_items:
        save_company_clusters(config, cluster_items)
    board = build_summary_board(payload)
    OUTPUT_PATH.write_text(
        json.dumps(board, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote summary board to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
