#!/usr/bin/env python3

import argparse
import json
import pathlib
import re
from collections import Counter
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
BOARD_PATH = ROOT / "data" / "summary_board.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
CORE_EVAL_PATH = ROOT / "data" / "eval_set.json"
INCREMENTAL_EVAL_PATH = ROOT / "data" / "incremental_eval_set.json"
OUTPUT_PATH = ROOT / "data" / "review_wave_001.json"


BROAD_FOCUS_LABELS = {
    "AI",
    "API",
    "MLOps",
    "SQL",
    "TensorFlow",
    "PyTorch",
    "데이터 분석",
    "딥러닝",
    "머신러닝",
    "소프트웨어",
    "인프라",
    "클라우드",
    "컴퓨터 비전",
    "프로그래밍",
}

HANGUL_PARTICLE_SUFFIXES = (
    "을",
    "를",
    "이",
    "가",
    "은",
    "는",
    "의",
    "에",
    "와",
    "과",
    "로",
    "도",
    "만",
    "및",
)

BANNED_TERMS = {
    "위한",
    "또는",
    "대한",
    "통한",
    "학력",
    "학사",
    "석사",
    "박사",
    "경력",
    "제품",
    "서비스",
    "기술",
    "업무",
    "별도",
    "미기재",
    "채용",
    "모집",
    "영입",
    "공고명",
    "공고문",
}

HIRING_TERMS = {
    "채용",
    "모집",
    "영입",
    "전문연구요원",
    "talent pool",
    "full stack",
    "공고문",
    "계약직",
    "신입",
    "경력",
}

GENERIC_KEYWORDS = {
    "단위",
    "단계부터",
    "전반을",
    "별도",
    "우대사항",
    "미기재",
    "공고문",
    "직무내용",
    "사용자",
    "인간",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def compact_list(values, limit=8) -> list[str]:
    items = []
    seen = set()
    for value in values or []:
        item = clean(value)
        if not item or item in seen:
            continue
        seen.add(item)
        items.append(item)
        if len(items) >= limit:
            break
    return items


def normalize_for_match(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", " ", clean(value).lower()).strip()


def tokenize(value: str) -> list[str]:
    normalized = normalize_for_match(value)
    return [token for token in normalized.split() if token]


def overlap_ratio(left: str, right: str) -> float:
    left_tokens = set(tokenize(left))
    right_tokens = set(tokenize(right))
    if not left_tokens or not right_tokens:
        return 0.0
    return len(left_tokens & right_tokens) / max(1, min(len(left_tokens), len(right_tokens)))


def contains_hiring_term(value: str) -> bool:
    lowered = clean(value).lower()
    return any(term in lowered for term in HIRING_TERMS)


def contains_company_echo(value: str, company: str) -> bool:
    normalized_value = normalize_for_match(value)
    normalized_company = normalize_for_match(company)
    if not normalized_value or not normalized_company:
        return False
    return normalized_company in normalized_value


def looks_noisy_keyword(keyword: str) -> bool:
    token = clean(keyword)
    if not token:
        return True
    lowered = token.lower()
    if lowered in BANNED_TERMS or lowered in HIRING_TERMS or lowered in GENERIC_KEYWORDS:
        return True
    if len(token) <= 1:
        return True
    if len(token) >= 2 and token.endswith(HANGUL_PARTICLE_SUFFIXES):
        return True
    if len(tokenize(token)) >= 5:
        return True
    return False


def issue(code: str, severity: str, note: str) -> dict:
    return {"code": code, "severity": severity, "note": note}


def detect_issues(item: dict) -> list[dict]:
    current = item["current"]
    source = item["source"]
    issues = []

    summary = clean(current.get("summary", ""))
    focus_label = clean(current.get("focusLabel", ""))
    keywords = compact_list(current.get("keywords", []), limit=8)
    title = clean(item.get("title", ""))
    company = clean(item.get("company", ""))
    quality = clean(current.get("quality", ""))

    if quality == "low":
        issues.append(issue("low_quality", "high", "현재 결과가 low 품질로 분류되었습니다."))

    if not summary:
        issues.append(issue("summary_missing", "high", "게시용 summary가 비어 있습니다."))
    elif len(summary) >= 56:
        issues.append(issue("summary_too_long", "low", "summary가 길어 게시용 식별 문구로는 늘어져 보일 수 있습니다."))

    if not focus_label:
        issues.append(issue("focus_missing", "high", "focusLabel이 비어 있습니다."))
    elif focus_label in BROAD_FOCUS_LABELS:
        issues.append(issue("focus_too_broad", "medium", "focusLabel이 넓어서 그룹 기준으로 쓰기 어렵습니다."))
    elif contains_hiring_term(focus_label):
        issues.append(issue("focus_hiring_echo", "high", "focusLabel이 채용/영입 같은 공고 표현을 따라갔습니다."))
    elif contains_company_echo(focus_label, company):
        issues.append(issue("focus_company_echo", "high", "focusLabel이 회사명이나 조직명을 따라갔습니다."))

    if summary and overlap_ratio(summary, title) >= 0.8:
        issues.append(issue("summary_title_echo", "high", "summary가 제목을 거의 그대로 반복합니다."))
    elif summary and contains_hiring_term(summary):
        issues.append(issue("summary_hiring_echo", "medium", "summary에 채용 안내성 표현이 남아 있습니다."))
    elif summary and contains_company_echo(summary, company):
        issues.append(issue("summary_company_echo", "medium", "summary가 회사명이나 조직명을 그대로 반복합니다."))

    noisy_keywords = [keyword for keyword in keywords if looks_noisy_keyword(keyword)]
    if len(noisy_keywords) >= 2:
        issues.append(
            issue(
                "keyword_noise",
                "medium",
                "키워드에 조사형·채용형·문장형 잡음이 섞여 있습니다: " + ", ".join(noisy_keywords[:3]),
            )
        )

    source_signal_count = 0
    if clean(source.get("detailBody", "")):
        source_signal_count += 1
    for field in ("tasks", "requirements", "preferred", "skills"):
        if source.get(field):
            source_signal_count += 1
    if source_signal_count <= 1:
        issues.append(issue("source_thin", "low", "원문 신호가 얇아 모델이 흔들릴 가능성이 높습니다."))

    return issues


def issue_score(issues: list[dict]) -> int:
    weights = {"high": 100, "medium": 45, "low": 15}
    return sum(weights[item["severity"]] for item in issues)


def priority_label(score: int) -> str:
    if score >= 100:
        return "high"
    if score >= 45:
        return "medium"
    return "low"


def merge_current(eval_item: dict, row: dict | None, job: dict | None, dataset: str) -> dict:
    current = dict(eval_item.get("current", {}))
    source = dict(eval_item.get("source", {}))

    if row:
        current = {
            "summary": clean(row.get("summary", "")),
            "focusLabel": clean(row.get("focusLabel", "")),
            "keywords": compact_list(row.get("highlightKeywords", []), limit=6),
            "quality": clean(row.get("summaryQuality", "")),
        }
    else:
        current = {
            "summary": clean(current.get("summary", "")),
            "focusLabel": clean(current.get("focusLabel", "")),
            "keywords": compact_list(current.get("keywords", []), limit=6),
            "quality": clean(eval_item.get("summaryQuality", current.get("quality", ""))),
        }

    if job:
        source = {
            "detailBody": clean(job.get("detailBody", "")),
            "tasks": compact_list(job.get("tasks", []), limit=6),
            "requirements": compact_list(job.get("requirements", []), limit=6),
            "preferred": compact_list(job.get("preferred", []), limit=6),
            "skills": compact_list(job.get("skills", []), limit=8),
        }
    else:
        source = {
            "detailBody": clean(source.get("detailBody", "")),
            "tasks": compact_list(source.get("tasks", []), limit=6),
            "requirements": compact_list(source.get("requirements", []), limit=6),
            "preferred": compact_list(source.get("preferred", []), limit=6),
            "skills": compact_list(source.get("skills", []), limit=8),
        }

    merged = {
        "sourceDataset": dataset,
        "id": eval_item["id"],
        "company": clean(eval_item.get("company", "")),
        "title": clean(eval_item.get("title", "")),
        "roleGroup": clean(eval_item.get("roleGroup", "")),
        "clusterId": clean(eval_item.get("clusterId", "")),
        "clusterLabel": clean(eval_item.get("clusterLabel", "")),
        "active": bool(eval_item.get("active")),
        "current": current,
        "source": source,
    }
    issues = detect_issues(merged)
    merged["machineReview"] = {
        "priority": priority_label(issue_score(issues)),
        "score": issue_score(issues),
        "issues": issues,
        "controlSample": False,
    }
    merged["review"] = {
        "summaryPass": None,
        "focusLabelPass": None,
        "keywordsPass": None,
        "overallPass": None,
        "correctedSummary": "",
        "correctedFocusLabel": "",
        "correctedKeywords": [],
        "correctedQuality": "",
        "notes": "",
    }
    return merged


def select_problem_cases(items: list[dict], target: int) -> list[dict]:
    problem_items = [item for item in items if item["machineReview"]["issues"]]
    problem_items.sort(
        key=lambda item: (
            -item["machineReview"]["score"],
            item["current"].get("quality", "") != "low",
            item["roleGroup"],
            item["company"],
            item["title"],
        )
    )
    return problem_items[:target]


def select_control_cases(items: list[dict], target: int, excluded_ids: set[str]) -> list[dict]:
    controls = [
        item
        for item in items
        if not item["machineReview"]["issues"] and item["id"] not in excluded_ids
    ]
    controls.sort(
        key=lambda item: (
            item["current"].get("quality", "") != "high",
            not item["active"],
            item["roleGroup"],
            item["company"],
            item["title"],
        )
    )
    chosen = controls[:target]
    for item in chosen:
        item["machineReview"]["controlSample"] = True
    return chosen


def summarize(items: list[dict]) -> dict:
    issue_counts = Counter()
    priority_counts = Counter()
    dataset_counts = Counter()
    role_counts = Counter()
    quality_counts = Counter()

    for item in items:
        dataset_counts[item["sourceDataset"]] += 1
        priority_counts[item["machineReview"]["priority"]] += 1
        role_counts[item["roleGroup"]] += 1
        quality_counts[item["current"].get("quality", "")] += 1
        for issue_item in item["machineReview"]["issues"]:
            issue_counts[issue_item["code"]] += 1

    return {
        "datasets": dict(dataset_counts),
        "priorities": dict(priority_counts),
        "roles": dict(role_counts),
        "qualities": dict(quality_counts),
        "issues": dict(issue_counts),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--core-problem-target", type=int, default=24)
    parser.add_argument("--incremental-problem-target", type=int, default=12)
    parser.add_argument("--core-control-target", type=int, default=4)
    parser.add_argument("--incremental-control-target", type=int, default=2)
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    board = load_json(BOARD_PATH)
    jobs = load_json(JOBS_PATH)
    core_eval = load_json(CORE_EVAL_PATH)
    incremental_eval = load_json(INCREMENTAL_EVAL_PATH)

    rows_by_id = {row["id"]: row for row in board.get("rows", [])}
    jobs_by_id = {job["id"]: job for job in jobs.get("jobs", [])}

    core_items = [
        merge_current(item, rows_by_id.get(item["id"]), jobs_by_id.get(item["id"]), "core")
        for item in core_eval.get("items", [])
    ]
    incremental_items = [
        merge_current(item, rows_by_id.get(item["id"]), jobs_by_id.get(item["id"]), "incremental")
        for item in incremental_eval.get("items", [])
    ]

    selected = []
    selected.extend(select_problem_cases(core_items, args.core_problem_target))
    selected.extend(select_problem_cases(incremental_items, args.incremental_problem_target))

    excluded_ids = {item["id"] for item in selected}
    selected.extend(select_control_cases(core_items, args.core_control_target, excluded_ids))
    excluded_ids.update(item["id"] for item in selected)
    selected.extend(select_control_cases(incremental_items, args.incremental_control_target, excluded_ids))

    selected.sort(
        key=lambda item: (
            0 if item["machineReview"]["priority"] == "high" else 1 if item["machineReview"]["priority"] == "medium" else 2,
            1 if item["machineReview"]["controlSample"] else 0,
            0 if item["sourceDataset"] == "incremental" else 1,
            item["current"].get("quality", "") != "low",
            item["company"],
            item["title"],
        )
    )

    payload = {
        "generatedAt": now_iso(),
        "source": {
            "boardPath": str(BOARD_PATH),
            "jobsPath": str(JOBS_PATH),
            "coreEvalPath": str(CORE_EVAL_PATH),
            "incrementalEvalPath": str(INCREMENTAL_EVAL_PATH),
        },
        "selection": {
            "strategy": "current-output issue scoring + control samples",
            "notes": [
                "현재 보드 결과를 기준으로 low, broad focus, title echo, keyword noise 같은 문제를 우선 잡습니다.",
                "core eval과 incremental holdout을 함께 섞어, 현재 품질과 최근 유입 일반화를 동시에 검수합니다.",
                "무조건 문제 케이스만 보지 않도록 control sample을 일부 포함합니다.",
            ],
            "targets": {
                "coreProblem": args.core_problem_target,
                "incrementalProblem": args.incremental_problem_target,
                "coreControl": args.core_control_target,
                "incrementalControl": args.incremental_control_target,
            },
        },
        "distribution": summarize(selected),
        "items": selected,
    }

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote review wave to {output_path}")
    print(json.dumps(payload["distribution"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
