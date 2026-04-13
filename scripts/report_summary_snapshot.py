#!/usr/bin/env python3

import json
import pathlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
SUMMARIES_PATH = ROOT / "data" / "job_summaries.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
BOARD_PATH = ROOT / "data" / "summary_board.json"

BROAD_FOCUS_LABELS = {
    "LLM",
    "파이프라인",
    "파이썬",
    "PyTorch",
    "TensorFlow",
    "SQL",
    "도커",
    "쿠버네티스",
    "사업 개발",
    "소프트웨어 개발",
    "인프라 엔지니어",
    "컴퓨터 비전",
    "클라우드",
    "의료",
    "의료 데이터",
    "마케팅",
    "데이터 분석",
    "인사이트",
}

ACCEPTED_BROAD_FOCUS_LABELS = {
    "컴퓨터 비전",
    "클라우드",
    "데이터 분석",
    "의료",
    "의료 데이터",
    "마케팅",
}


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    jobs_payload = load_json(JOBS_PATH)
    summaries_payload = load_json(SUMMARIES_PATH)
    board_payload = load_json(BOARD_PATH) if BOARD_PATH.exists() else {"rows": []}

    jobs = jobs_payload.get("jobs", [])
    items = summaries_payload.get("items", {})
    board_rows = board_payload.get("rows", [])

    total_jobs = len(jobs)
    summary_present = 0
    focus_present = 0
    low_count = 0
    broad_focus_count = 0
    accepted_broad_focus_count = 0
    bad_broad_focus_count = 0
    provider_counter = Counter()
    focus_counter = Counter()
    board_focus_counter = Counter()
    board_broad_focus_count = 0
    board_accepted_broad_focus_count = 0
    board_bad_broad_focus_count = 0
    low_blank_focus_rows = 0

    for job in jobs:
        item = items.get(job["id"], {})
        summary = (item.get("summary") or "").strip()
        focus = (item.get("focusLabel") or "").strip()
        quality = (item.get("quality") or "").strip().lower()
        provider = (((item.get("provider") or {}).get("model")) or "").strip()

        if summary:
            summary_present += 1
        if focus:
            focus_present += 1
            focus_counter[focus] += 1
            if focus in BROAD_FOCUS_LABELS:
                broad_focus_count += 1
                if focus in ACCEPTED_BROAD_FOCUS_LABELS:
                    accepted_broad_focus_count += 1
                else:
                    bad_broad_focus_count += 1
        if quality == "low":
            low_count += 1
        if provider:
            provider_counter[provider] += 1

    for row in board_rows:
        focus = (row.get("focusLabel") or "").strip()
        quality = (row.get("summaryQuality") or "").strip().lower()
        if focus:
            board_focus_counter[focus] += 1
            if focus in BROAD_FOCUS_LABELS:
                board_broad_focus_count += 1
                if focus in ACCEPTED_BROAD_FOCUS_LABELS:
                    board_accepted_broad_focus_count += 1
                else:
                    board_bad_broad_focus_count += 1
        if quality == "low" and not focus:
            low_blank_focus_rows += 1

    payload = {
        "jobs": total_jobs,
        "summaryPresent": summary_present,
        "focusPresent": focus_present,
        "low": low_count,
        "broadFocusRaw": broad_focus_count,
        "acceptedBroadRaw": accepted_broad_focus_count,
        "badBroadRaw": bad_broad_focus_count,
        "broadFocusBoard": board_broad_focus_count,
        "acceptedBroadBoard": board_accepted_broad_focus_count,
        "badBroadBoard": board_bad_broad_focus_count,
        "lowBlankFocusRows": low_blank_focus_rows,
        "providers": dict(provider_counter),
        "topFocus": [
            {"label": label, "count": count}
            for label, count in focus_counter.most_common(15)
        ],
        "topBoardFocus": [
            {"label": label, "count": count}
            for label, count in board_focus_counter.most_common(15)
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
