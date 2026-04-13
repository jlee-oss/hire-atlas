#!/usr/bin/env python3

import json

from ai_runtime import (
    backfill_structured_signals,
    get_jobs_payload,
    save_summary_store,
)
from build_summary_board import OUTPUT_PATH, build_summary_board


def main():
    payload = get_jobs_payload()
    store, updated = backfill_structured_signals(jobs_payload=payload)
    save_summary_store(store)

    board = build_summary_board(payload)
    OUTPUT_PATH.write_text(
        json.dumps(board, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Updated structured signals for {updated} summary items")
    print(f"Wrote summary board to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
