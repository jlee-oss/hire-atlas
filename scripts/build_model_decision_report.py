#!/usr/bin/env python3

import argparse
import json
import pathlib
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS_PATH = ROOT / "data" / "jobs.json"
SUMMARIES_PATH = ROOT / "data" / "job_summaries.json"
BOARD_PATH = ROOT / "data" / "summary_board.json"
CORE_EVAL_PATH = ROOT / "data" / "eval_set.json"
INCREMENTAL_EVAL_PATH = ROOT / "data" / "incremental_eval_set.json"
BENCHMARK_DIR = ROOT / "data" / "prompt_benchmarks"
MODEL_COMPARISON_DIR = ROOT / "data" / "model_comparisons"
OUTPUT_PATH = ROOT / "docs" / "model_decision_report.md"

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
    "데이터 분석",
    "컴퓨터 비전",
    "클라우드",
    "의료",
    "의료 데이터",
    "마케팅",
}

ACCEPTED_BROAD_FOCUS_LABELS = {
    "컴퓨터 비전",
    "클라우드",
    "데이터 분석",
    "의료",
    "의료 데이터",
    "마케팅",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def pct(numerator: int, denominator: int) -> str:
    if not denominator:
        return "0.0%"
    return f"{(numerator / denominator) * 100:.1f}%"


def reviewed_count(items: list[dict]) -> int:
    total = 0
    for item in items:
        review = item.get("review", {})
        if review.get("pass") is not None or review.get("overallPass") is not None:
            total += 1
            continue
        if any(review.get(key) is not None for key in ["summaryPass", "focusLabelPass", "keywordsPass"]):
            total += 1
            continue
        if any(
            review.get(key)
            for key in [
                "expectedSummary",
                "expectedFocusLabel",
                "expectedKeywords",
                "expectedQuality",
                "correctedSummary",
                "correctedFocusLabel",
                "correctedKeywords",
                "correctedQuality",
                "notes",
            ]
        ):
            total += 1
    return total


def pass_count(items: list[dict], key: str) -> tuple[int, int]:
    passed = 0
    total = 0
    for item in items:
        review = item.get("review", {})
        value = review.get(key)
        if value is None:
            continue
        total += 1
        if value is True:
            passed += 1
    return passed, total


def latest_suite_report(benchmark_dir: pathlib.Path) -> tuple[pathlib.Path | None, dict | None]:
    candidates = sorted(benchmark_dir.glob("suite_*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        return None, None
    path = candidates[0]
    return path, load_json(path)


def collect_models(benchmark_dir: pathlib.Path) -> set[str]:
    models = set()
    for path in benchmark_dir.glob("*.json"):
        try:
            payload = load_json(path)
        except json.JSONDecodeError:
            continue
        model = payload.get("model", {}).get("model")
        if model:
            models.add(model)
    return models


def latest_model_comparison(comparison_dir: pathlib.Path) -> tuple[pathlib.Path | None, dict | None]:
    candidates = sorted(comparison_dir.glob("*.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    if not candidates:
        return None, None
    path = candidates[0]
    return path, load_json(path)


def build_report() -> str:
    jobs_payload = load_json(JOBS_PATH)
    job_ids = {job["id"] for job in jobs_payload.get("jobs", [])}

    summaries = load_json(SUMMARIES_PATH).get("items", {})
    current_items = [summaries.get(job_id, {}) for job_id in sorted(job_ids)]

    total_jobs = len(job_ids)
    with_summary = sum(1 for item in current_items if item.get("summary"))
    with_focus = sum(1 for item in current_items if item.get("focusLabel"))
    low_count = sum(1 for item in current_items if item.get("quality") == "low")
    raw_broad_focus_count = sum(1 for item in current_items if item.get("focusLabel") in BROAD_FOCUS_LABELS)
    raw_accepted_broad_focus_count = sum(
        1 for item in current_items if item.get("focusLabel") in ACCEPTED_BROAD_FOCUS_LABELS
    )
    raw_bad_broad_focus_count = sum(
        1
        for item in current_items
        if item.get("focusLabel") in BROAD_FOCUS_LABELS and item.get("focusLabel") not in ACCEPTED_BROAD_FOCUS_LABELS
    )

    board = load_json(BOARD_PATH)
    rows = board.get("rows", [])
    broad_focus_count = sum(1 for row in rows if row.get("focusLabel") in BROAD_FOCUS_LABELS)
    accepted_broad_focus_count = sum(
        1
        for row in rows
        if row.get("focusLabel") in BROAD_FOCUS_LABELS and row.get("focusLabel") in ACCEPTED_BROAD_FOCUS_LABELS
    )
    bad_broad_focus_count = sum(
        1
        for row in rows
        if row.get("focusLabel") in BROAD_FOCUS_LABELS and row.get("focusLabel") not in ACCEPTED_BROAD_FOCUS_LABELS
    )

    core_eval = load_json(CORE_EVAL_PATH)
    incremental_eval = load_json(INCREMENTAL_EVAL_PATH)
    core_reviewed = reviewed_count(core_eval.get("items", []))
    incremental_reviewed = reviewed_count(incremental_eval.get("items", []))
    core_overall_passed, core_overall_total = pass_count(core_eval.get("items", []), "overallPass")
    incremental_overall_passed, incremental_overall_total = pass_count(
        incremental_eval.get("items", []), "overallPass"
    )

    suite_path, suite = latest_suite_report(BENCHMARK_DIR)
    suite_status = "없음"
    gate_pass = False
    core_candidate_usable = None
    incremental_candidate_usable = None
    if suite:
        gate_rows = suite.get("gateReport", [])
        gate_pass = bool(gate_rows and all(row.get("pass") for row in gate_rows))
        suite_status = suite_path.name if suite_path else "있음"
        datasets = suite.get("datasets", {})
        if datasets.get("core"):
            profile_order = datasets["core"]["profileOrder"]
            candidate = profile_order[-1]
            core_candidate_usable = datasets["core"]["results"][candidate]["metrics"]["usableItemRate"]
        if datasets.get("incremental"):
            profile_order = datasets["incremental"]["profileOrder"]
            candidate = profile_order[-1]
            incremental_candidate_usable = datasets["incremental"]["results"][candidate]["metrics"][
                "usableItemRate"
            ]

    models_seen = collect_models(BENCHMARK_DIR)
    comparison_path, model_comparison = latest_model_comparison(MODEL_COMPARISON_DIR)
    comparison_status = "없음"
    comparison_improved = None
    comparison_worsened = None
    if model_comparison:
        comparison_status = comparison_path.name if comparison_path else "있음"
        baseline_model = model_comparison.get("baseline", {}).get("model")
        candidate_model = model_comparison.get("candidate", {}).get("model")
        if baseline_model:
            models_seen.add(baseline_model)
        if candidate_model:
            models_seen.add(candidate_model)
        comparison_improved = len(model_comparison.get("comparison", {}).get("improved", []))
        comparison_worsened = len(model_comparison.get("comparison", {}).get("worsened", []))
    stronger_model_compared = len(models_seen) >= 2 and bool(model_comparison)

    blockers = []
    if core_reviewed < 30:
        blockers.append("사람이 검토한 core 골드셋이 부족합니다.")
    if incremental_reviewed < 10:
        blockers.append("사람이 검토한 incremental 골드셋이 부족합니다.")
    if not suite:
        blockers.append("core + incremental benchmark suite가 없습니다.")
    elif not gate_pass:
        blockers.append("현재 후보 프로필이 core + incremental 동시 게이트를 통과하지 못했습니다.")
    if not stronger_model_compared:
        blockers.append("더 강한 모델과의 직접 비교가 아직 없습니다.")

    recommendation = "현재는 파인튜닝 진입 단계가 아닙니다."
    next_priority = "1) 골드셋 검수 2) review pass rate 계산 3) 그 후에만 튜닝 여부 판단"
    if not blockers and low_count > 10:
        recommendation = "파인튜닝 검토 전 단계입니다."
        next_priority = "반복 오류를 유형화한 뒤 stronger-model 결과와 함께 튜닝 필요성을 판단합니다."
    if not blockers and stronger_model_compared and core_reviewed >= 50 and incremental_reviewed >= 20:
        recommendation = "파인튜닝 검토 가능 단계입니다."
        next_priority = "반복 오류군이 남는지 확인한 뒤 structured extraction 전용 튜닝 여부를 결정합니다."

    lines = [
        "# 모델 의사결정 리포트",
        "",
        f"- 생성 시각: `{now_iso()}`",
        f"- 현재 jobs 기준: `{total_jobs}`건",
        "",
        "## 현재 상태",
        "",
        f"- summary 존재: `{with_summary}/{total_jobs}` (`{pct(with_summary, total_jobs)}`)",
        f"- focusLabel 존재: `{with_focus}/{total_jobs}` (`{pct(with_focus, total_jobs)}`)",
        f"- low: `{low_count}/{total_jobs}` (`{pct(low_count, total_jobs)}`)",
        f"- 넓은 focusLabel 잔존(raw): `{raw_broad_focus_count}/{total_jobs}` (`{pct(raw_broad_focus_count, total_jobs)}`)",
        f"- 허용 broad focus(raw): `{raw_accepted_broad_focus_count}/{total_jobs}` (`{pct(raw_accepted_broad_focus_count, total_jobs)}`)",
        f"- 문제 broad focus(raw): `{raw_bad_broad_focus_count}/{total_jobs}` (`{pct(raw_bad_broad_focus_count, total_jobs)}`)",
        f"- 넓은 focusLabel 잔존(board): `{broad_focus_count}/{total_jobs}` (`{pct(broad_focus_count, total_jobs)}`)",
        f"- 허용 broad focus(board): `{accepted_broad_focus_count}/{total_jobs}` (`{pct(accepted_broad_focus_count, total_jobs)}`)",
        f"- 문제 broad focus(board): `{bad_broad_focus_count}/{total_jobs}` (`{pct(bad_broad_focus_count, total_jobs)}`)",
        "",
        "## 평가 체계",
        "",
        f"- core eval set: `{len(core_eval.get('items', []))}`건 / 검수된 항목 `{core_reviewed}`건",
        f"- incremental holdout: `{len(incremental_eval.get('items', []))}`건 / 검수된 항목 `{incremental_reviewed}`건",
        "",
        "## 리뷰 정확도",
        "",
        f"- core overall pass: `{core_overall_passed}/{core_overall_total}` (`{pct(core_overall_passed, core_overall_total)}`)",
        f"- incremental overall pass: `{incremental_overall_passed}/{incremental_overall_total}` (`{pct(incremental_overall_passed, incremental_overall_total)}`)",
        "",
        "## 일반화 확인",
        "",
        f"- 최신 suite benchmark: `{suite_status}`",
        f"- core + incremental 게이트 통과: `{gate_pass}`",
    ]

    if core_candidate_usable is not None:
        lines.append(f"- latest core usable rate: `{core_candidate_usable:.4f}`")
    if incremental_candidate_usable is not None:
        lines.append(f"- latest incremental usable rate: `{incremental_candidate_usable:.4f}`")

    lines.extend(
        [
            "",
            "## 모델 비교 상태",
            "",
            f"- benchmark에 등장한 모델: `{', '.join(sorted(models_seen)) or '(없음)'}`",
            f"- 더 강한 모델 비교 완료: `{stronger_model_compared}`",
            f"- 최신 stronger-model 비교: `{comparison_status}`",
            "",
            "## 현재 판단",
            "",
            f"- 결론: {recommendation}",
            f"- 다음 우선순위: {next_priority}",
            "",
            "## 현재 blocker",
            "",
        ]
    )

    if comparison_improved is not None:
        lines.insert(lines.index("## 현재 판단"), f"- hard set quality 개선: `{comparison_improved}`건")
        lines.insert(lines.index("## 현재 판단"), f"- hard set quality 악화: `{comparison_worsened}`건")
        lines.insert(lines.index("## 현재 판단"), "")

    if blockers:
        lines.extend(f"- {item}" for item in blockers)
    else:
        lines.append("- 현재 blocker 없음")

    lines.extend(
        [
            "",
            "## 튜닝 진입 조건",
            "",
            "- core + incremental 둘 다 통과",
            "- 더 강한 모델 비교 완료",
            "- 반복 오류 유형이 구조적으로 남음",
            "- 검수된 골드셋이 충분함",
            "- 목표가 자유 생성이 아니라 structured extraction으로 명확함",
            "",
        ]
    )

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default=str(OUTPUT_PATH))
    args = parser.parse_args()

    content = build_report()
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote model decision report to {output_path}")


if __name__ == "__main__":
    main()
