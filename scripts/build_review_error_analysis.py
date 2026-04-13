#!/usr/bin/env python3

import argparse
import json
import pathlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
CORE_EVAL_PATH = ROOT / "data" / "eval_set.json"
INCREMENTAL_EVAL_PATH = ROOT / "data" / "incremental_eval_set.json"
DEFAULT_JSON_PATH = ROOT / "data" / "review_error_analysis_001.json"
DEFAULT_MD_PATH = ROOT / "docs" / "review_error_analysis_001.md"

BROAD_FOCUS_LABELS = {
    "인공지능 리서처",
    "인공지능 엔지니어",
    "컴퓨터 비전",
    "의료 데이터",
    "고객 관계 관리",
    "MLOps",
    "검색",
    "별도",
    "컴퓨터 비전",
}


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def is_reviewed(item: dict) -> bool:
    review = item.get("review", {})
    if review.get("overallPass") is not None:
        return True
    if any(review.get(key) is not None for key in ("summaryPass", "focusLabelPass", "keywordsPass")):
        return True
    return any(
        review.get(key)
        for key in (
            "correctedSummary",
            "correctedFocusLabel",
            "correctedKeywords",
            "correctedQuality",
            "notes",
        )
    )


def clean(value) -> str:
    return " ".join(str(value or "").split())


def issue_tags(item: dict) -> list[str]:
    current = item.get("current", {})
    review = item.get("review", {})
    tags = []

    current_summary = clean(current.get("summary", ""))
    corrected_summary = clean(review.get("correctedSummary", ""))
    current_focus = clean(current.get("focusLabel", ""))
    corrected_focus = clean(review.get("correctedFocusLabel", ""))
    current_keywords = [clean(v) for v in current.get("keywords", []) if clean(v)]
    corrected_keywords = [clean(v) for v in review.get("correctedKeywords", []) if clean(v)]

    if review.get("summaryPass") is False:
        tags.append("summary_rewrite")
        if not current_summary:
            tags.append("summary_missing")
        elif len(current_summary) <= 12 or current_summary == item.get("title", ""):
            tags.append("summary_title_like")
        elif corrected_summary and current_summary != corrected_summary:
            tags.append("summary_not_board_ready")

    if review.get("focusLabelPass") is False:
        tags.append("focus_relabel")
        if current_focus in BROAD_FOCUS_LABELS:
            tags.append("focus_too_broad_or_generic")
        if corrected_focus and current_focus and corrected_focus != current_focus:
            tags.append("focus_semantic_mismatch")

    if review.get("keywordsPass") is False:
        tags.append("keywords_rewrite")
        if not current_keywords:
            tags.append("keywords_missing")
        elif corrected_keywords and set(current_keywords) != set(corrected_keywords):
            tags.append("keywords_not_groupable")

    if clean(review.get("correctedQuality", "")).lower() == "low":
        tags.append("keep_low")
        if not clean(item.get("source", {}).get("detailBody", "")) or len(clean(item.get("source", {}).get("detailBody", ""))) < 80:
            tags.append("source_too_sparse")
        else:
            tags.append("source_not_actionable")

    return tags


def collect_reviewed() -> list[dict]:
    rows = []
    for dataset_name, path in [("core", CORE_EVAL_PATH), ("incremental", INCREMENTAL_EVAL_PATH)]:
        payload = load_json(path)
        for item in payload.get("items", []):
            if not is_reviewed(item):
                continue
            review = item.get("review", {})
            rows.append(
                {
                    "dataset": dataset_name,
                    "id": item.get("id", ""),
                    "company": item.get("company", ""),
                    "title": item.get("title", ""),
                    "roleGroup": item.get("roleGroup", ""),
                    "clusterLabel": item.get("clusterLabel", ""),
                    "current": item.get("current", {}),
                    "review": review,
                    "source": item.get("source", {}),
                    "issues": issue_tags(item),
                }
            )
    return rows


def build_payload(rows: list[dict]) -> dict:
    issue_counts = Counter()
    cluster_counts = Counter()
    for row in rows:
        for issue in row["issues"]:
            issue_counts[issue] += 1
        cluster_counts[row.get("clusterLabel", "")] += 1

    return {
        "reviewedCount": len(rows),
        "issueCounts": dict(issue_counts),
        "clusterCounts": dict(cluster_counts),
        "rows": rows,
    }


def build_markdown(payload: dict) -> str:
    lines = [
        "# 리뷰 오류 분석",
        "",
        f"- 검수 반영 공고: `{payload['reviewedCount']}`",
        "",
        "## 주요 오류 축",
        "",
    ]
    for key, value in sorted(payload["issueCounts"].items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(
        [
            "",
            "## 해석",
            "",
            "- `summary_rewrite`가 전건에 걸쳐 발생했다는 것은 현재 모델의 요약문이 게시용 문구로는 거의 통과하지 못한다는 뜻입니다.",
            "- `keywords_rewrite`도 전건에 가깝게 발생해, 현재 keywords는 그룹 기준어보다 보조 신호 수준에 머물러 있습니다.",
            "- `focus_relabel`은 일부만 유지됐고, 나머지는 더 구체적이거나 더 적절한 도메인 축으로 바뀌었습니다.",
            "- `keep_low`는 원문이 빈약하거나 공고 자체가 운영/안내 문구 중심인 케이스라, 억지 요약보다 low 유지 전략이 맞았음을 보여줍니다.",
            "",
            "## 대표 사례",
            "",
        ]
    )
    for row in payload["rows"][:14]:
        lines.append(f"- {row['company']} | {row['title']}")
        lines.append(f"  issues: {', '.join(row['issues'])}")
        current_summary = clean(row['current'].get('summary', ''))
        current_focus = clean(row['current'].get('focusLabel', ''))
        lines.append(f"  current: `{current_summary or '(empty)'}` / `{current_focus or '(empty)'}`")
        lines.append(
            f"  corrected: `{clean(row['review'].get('correctedSummary', '')) or '(empty)'}` / "
            f"`{clean(row['review'].get('correctedFocusLabel', '')) or '(empty)'}`"
        )
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_PATH))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_PATH))
    args = parser.parse_args()

    rows = collect_reviewed()
    payload = build_payload(rows)

    json_path = pathlib.Path(args.json_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_path = pathlib.Path(args.md_output)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(build_markdown(payload), encoding="utf-8")

    print(f"Wrote review error analysis JSON to {json_path}")
    print(f"Wrote review error analysis markdown to {md_path}")


if __name__ == "__main__":
    main()
