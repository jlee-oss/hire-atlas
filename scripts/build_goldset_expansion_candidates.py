#!/usr/bin/env python3

import json
import pathlib
from collections import defaultdict
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS_PATH = ROOT / "data" / "jobs.json"
SUMMARIES_PATH = ROOT / "data" / "job_summaries.json"
OUTPUT_JSON_PATH = ROOT / "data" / "goldset_expansion_candidates.json"
OUTPUT_MD_PATH = ROOT / "docs" / "goldset_expansion_candidates.md"

BROAD_FOCUS_LABELS = {
    "LLM",
    "파이프라인",
    "PyTorch",
    "TensorFlow",
    "SQL",
    "컴퓨터 비전",
    "클라우드",
    "의료",
    "마케팅",
    "인사이트",
}

DOMAIN_SIGNAL_TERMS = {
    "심전도": "medical",
    "생체신호": "medical",
    "EMR": "medical",
    "의료": "medical",
    "헬스케어": "medical",
    "로봇": "robotics",
    "로보틱스": "robotics",
    "강화 학습": "robotics",
    "시뮬레이션": "robotics",
    "자율주행": "autonomy",
    "컴퓨터 비전": "vision",
    "VLM": "vision",
    "RAG": "llm",
    "LLM": "llm",
    "그로스 마케팅": "growth",
    "리텐션": "growth",
    "CRM": "growth",
    "제품 성장 분석": "product-analytics",
    "A/B 테스트": "product-analytics",
    "디지털 농업": "agri",
    "농업 데이터": "agri",
    "클라우드": "cloud",
    "AWS": "cloud",
}


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def infer_domain_bucket(summary: str, focus: str, keywords: list[str]) -> str:
    text = " ".join([focus, summary, *keywords])
    for token, bucket in DOMAIN_SIGNAL_TERMS.items():
        if token in text:
            return bucket
    return "general"


def build_candidate(job: dict, item: dict, reason: str, bucket: str) -> dict:
    return {
        "id": job["id"],
        "company": clean(job.get("company", "")),
        "title": clean(job.get("title", "")),
        "roleDisplay": clean(job.get("roleDisplay", "")),
        "summary": clean(item.get("summary", "")),
        "focusLabel": clean(item.get("focusLabel", "")),
        "keywords": [clean(keyword) for keyword in item.get("keywords", []) if clean(keyword)],
        "quality": clean(item.get("quality", "")),
        "reason": reason,
        "bucket": bucket,
    }


def main() -> None:
    jobs_payload = load_json(JOBS_PATH)
    summaries_payload = load_json(SUMMARIES_PATH)
    jobs = jobs_payload.get("jobs", [])
    items = summaries_payload.get("items", {})

    candidates = []
    seen = set()

    # 1) broad focus
    for job in jobs:
        item = items.get(job["id"], {})
        focus = clean(item.get("focusLabel", ""))
        if focus and focus in BROAD_FOCUS_LABELS:
            candidate = build_candidate(job, item, reason="broad_focus", bucket="broad_focus")
            if candidate["id"] not in seen:
                seen.add(candidate["id"])
                candidates.append(candidate)

    # 2) low quality but with some extracted signal
    for job in jobs:
        item = items.get(job["id"], {})
        quality = clean(item.get("quality", "")).lower()
        summary = clean(item.get("summary", ""))
        keywords = [clean(keyword) for keyword in item.get("keywords", []) if clean(keyword)]
        if quality == "low" or not summary:
            candidate = build_candidate(job, item, reason="low_or_empty", bucket="low_or_empty")
            if candidate["id"] not in seen:
                seen.add(candidate["id"])
                candidates.append(candidate)

    # 3) rare domain / special domain
    bucketed = defaultdict(list)
    for job in jobs:
        item = items.get(job["id"], {})
        candidate = build_candidate(
            job,
            item,
            reason="domain_specific",
            bucket=infer_domain_bucket(
                clean(item.get("summary", "")),
                clean(item.get("focusLabel", "")),
                [clean(keyword) for keyword in item.get("keywords", []) if clean(keyword)],
            ),
        )
        bucketed[candidate["bucket"]].append(candidate)

    for bucket, rows in bucketed.items():
        if bucket == "general":
            continue
        rows = sorted(rows, key=lambda row: (row["focusLabel"], row["company"], row["title"]))
        for row in rows[:6]:
            if row["id"] not in seen:
                seen.add(row["id"])
                candidates.append(row)

    # 4) confusable labels
    for job in jobs:
        item = items.get(job["id"], {})
        focus = clean(item.get("focusLabel", ""))
        keywords = [clean(keyword) for keyword in item.get("keywords", []) if clean(keyword)]
        if focus and focus not in keywords and len(keywords) >= 3:
            candidate = build_candidate(job, item, reason="focus_keyword_conflict", bucket="confusable")
            if candidate["id"] not in seen:
                seen.add(candidate["id"])
                candidates.append(candidate)

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "count": len(candidates),
        "items": candidates,
    }
    OUTPUT_JSON_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        "# 골드셋 확장 후보",
        "",
        f"- 총 후보: `{len(candidates)}`",
        "",
    ]
    by_reason = defaultdict(list)
    for candidate in candidates:
        by_reason[candidate["reason"]].append(candidate)
    for reason in sorted(by_reason):
        lines.append(f"## {reason}")
        lines.append("")
        for candidate in by_reason[reason][:20]:
            lines.append(f"- `{candidate['company']}` | `{candidate['title']}` | `{candidate['focusLabel'] or '-'}`")
        lines.append("")
    OUTPUT_MD_PATH.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote candidate JSON to {OUTPUT_JSON_PATH}")
    print(f"Wrote candidate markdown to {OUTPUT_MD_PATH}")


if __name__ == "__main__":
    main()
