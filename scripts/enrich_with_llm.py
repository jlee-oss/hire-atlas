#!/usr/bin/env python3

import json
import os
import pathlib
import urllib.error

from ai_runtime import get_job_by_id, request_openai_compatible, save_enrichment
from build_briefing import build_briefing


ROOT = pathlib.Path(__file__).resolve().parent.parent
BRIEFING_PATH = ROOT / "data" / "briefing.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
OUTPUT_PATH = ROOT / "data" / "ai_enrichment_preview.json"


def main():
    config = {
        "baseUrl": os.environ.get("LLM_BASE_URL", ""),
        "apiKey": os.environ.get("LLM_API_KEY", ""),
        "model": os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-72B-Instruct"),
    }

    if not config["baseUrl"]:
        raise SystemExit("LLM_BASE_URL is required. Example: http://localhost:8000/v1")

    briefing = json.loads(BRIEFING_PATH.read_text(encoding="utf-8"))
    queue = briefing["reviewQueue"][:5]
    results = []

    for item in queue:
        raw_job = get_job_by_id(item["id"])
        try:
            enriched = request_openai_compatible(config, raw_job)
            save_enrichment(item["id"], config, enriched)
            results.append({"job": item, "enrichment": enriched, "status": "ok"})
            print(f"Enriched: {item['company']} / {item['title']}")
        except (urllib.error.URLError, KeyError, json.JSONDecodeError, ValueError) as exc:
            results.append(
                {
                    "job": item,
                    "status": "error",
                    "error": str(exc),
                }
            )
            print(f"Failed: {item['company']} / {item['title']} -> {exc}")

    jobs_payload = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    BRIEFING_PATH.write_text(
        json.dumps(build_briefing(jobs_payload), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    OUTPUT_PATH.write_text(
        json.dumps({"config": config, "results": results}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {len(results)} AI enrichment results to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
