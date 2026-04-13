#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from ai_runtime import JOBS_PATH
from build_summary_board import (
    build_base_rows,
    clean_text,
    explain_service_scope_row,
    load_service_scope_override_store,
    model_exclude_should_be_recovered,
    resolve_service_scope_override,
    row_has_recoverable_service_scope_signal,
    row_has_strong_non_scope_signal,
)


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT_PATH = ROOT / "data" / "service_scope_shadow_guard_off_001.json"
DEFAULT_MD_PATH = ROOT / "docs" / "service_scope_shadow_guard_off_001.md"
DEFAULT_MODEL_REVIEW_PATH = ROOT / "data" / "service_scope_model_review.json"
DEFAULT_GOLDSET_PATH = ROOT / "data" / "service_scope_goldset_001.json"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def md_cell(value) -> str:
    return clean_text(value).replace("|", "\\|") or "-"


def compact_row(row: dict, decision: dict | None = None) -> dict:
    decision = decision or {}
    reasons = decision.get("reasons", []) if isinstance(decision.get("reasons", []), list) else []
    return {
        "id": clean_text(row.get("id", "")),
        "company": clean_text(row.get("company", "")),
        "title": clean_text(row.get("title", "")),
        "roleGroup": clean_text(row.get("roleGroup", "")),
        "summaryQuality": clean_text(row.get("summaryQuality", "")),
        "focusLabel": clean_text(row.get("focusLabel", "")),
        "serviceScopeAction": clean_text(row.get("serviceScopeAction", "")),
        "serviceScopeResolvedAction": clean_text(row.get("serviceScopeResolvedAction", "")),
        "serviceScopeReason": clean_text(row.get("serviceScopeReason", "")),
        "shadowAction": clean_text(decision.get("action", "")),
        "shadowReasons": [clean_text(reason.get("label", "")) for reason in reasons if isinstance(reason, dict)],
        "jobUrl": clean_text(row.get("jobUrl", "")),
    }


def load_model_review_overrides(path: Path) -> dict:
    report = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"items": []}
    override_items = {}
    for item in report.get("items", []):
        if not isinstance(item, dict):
            continue
        decision = item.get("modelDecision", {})
        if not isinstance(decision, dict):
            continue
        job_id = clean_text(item.get("id", ""))
        action = clean_text(decision.get("decision", "")).lower()
        if not job_id or action not in {"include", "review", "exclude"}:
            continue
        override_items[job_id] = {
            "action": action,
            "source": "service_scope_model_review_report",
            "reason": clean_text(decision.get("reason", "")),
            "mappedRole": clean_text(decision.get("mappedRole", "")),
            "confidence": clean_text(decision.get("confidence", "")),
            "signature": clean_text(decision.get("signature", "")),
        }
    return override_items


def load_goldset_expectations(path: Path) -> tuple[str, dict[str, str]]:
    if not path.exists():
        return "missing", {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    status = clean_text(payload.get("status", "")) or "missing"
    expectations = {}
    for item in payload.get("items", []):
        if not isinstance(item, dict):
            continue
        job_id = clean_text(item.get("id", ""))
        target = item.get("target", {}) if isinstance(item.get("target", {}), dict) else {}
        action = clean_text(target.get("serviceScopeAction", "")).lower()
        if job_id and action in {"include", "review", "exclude"}:
            expectations[job_id] = action
    return status, expectations


def explain_guard_off(row: dict, override_items: dict) -> dict:
    override = resolve_service_scope_override(row, override_items=override_items)
    override_action = clean_text(override.get("action", "")).lower()
    if override_action == "include":
        return {
            "included": True,
            "action": "include",
            "reasons": [{"type": "override", "label": f"override:{override.get('source', 'manual')}"}],
        }
    if override_action == "review":
        return {
            "included": False,
            "action": "review",
            "reasons": [{"type": "override", "label": f"override:{override.get('source', 'manual')}"}],
        }
    if override_action == "exclude":
        return {
            "included": False,
            "action": "exclude",
            "reasons": [{"type": "override", "label": f"override:{override.get('source', 'manual')}"}],
        }
    return explain_service_scope_row(row, override_items=override_items)


def target_status(metrics: dict) -> dict:
    definitions = {
        "shadowGuardRecoveredRows": ("max", 0),
        "shadowGuardRecoveredHighQualityRows": ("max", 0),
        "shadowExcludedAiAdjacentRows": ("max", 0),
        "shadowExcludedHighQualityRows": ("max", 10),
        "shadowSourceRetentionRate": ("min", 0.8),
        "shadowFilteredOutRate": ("max", 0.2),
    }
    status = {}
    for key, (comparator, target) in definitions.items():
        actual = metrics.get(key, 0)
        passed = actual <= target if comparator == "max" else actual >= target
        status[key] = {
            "actual": actual,
            "target": target,
            "comparator": comparator,
            "passed": passed,
        }
    return status


def render_md(report: dict) -> str:
    metrics = report["metrics"]
    lines = [
        "# Service Scope Shadow Guard-Off 001",
        "",
        f"- generatedAt: `{report['generatedAt']}`",
        f"- predictionSource: `{report.get('predictionSource', 'existing-overrides')}`",
        f"- goldsetStatus: `{report.get('goldsetStatus', 'missing')}`",
        f"- targetsPassed: `{report['targetsPassed']}`",
        "",
        "## Metrics",
        "",
        f"- sourceJobs: `{metrics['sourceJobs']}`",
        f"- shadowBoardRows: `{metrics['shadowBoardRows']}`",
        f"- shadowExcludedRows: `{metrics['shadowExcludedRows']}`",
        f"- shadowReviewRows: `{metrics.get('shadowReviewRows', 0)}`",
        f"- shadowHardExcludedRows: `{metrics.get('shadowHardExcludedRows', 0)}`",
        f"- shadowSourceRetentionRate: `{metrics['shadowSourceRetentionRate']}`",
        f"- shadowFilteredOutRate: `{metrics['shadowFilteredOutRate']}`",
        f"- shadowGuardRecoveredRows: `{metrics['shadowGuardRecoveredRows']}`",
        f"- shadowGuardRecoveredHighQualityRows: `{metrics['shadowGuardRecoveredHighQualityRows']}`",
        f"- shadowExcludedAiAdjacentRows: `{metrics['shadowExcludedAiAdjacentRows']}`",
        f"- shadowExcludedHighQualityRows: `{metrics['shadowExcludedHighQualityRows']}`",
        "",
        "## Target Status",
        "",
    ]
    for key, item in report["targetStatus"].items():
        lines.append(f"- `{key}` actual `{item['actual']}` target `{item['target']}` passed `{item['passed']}`")

    lines.extend(
        [
            "",
            "## Rows Lost Without Guard",
            "",
            "| # | company | title | quality | focus | model reason |",
            "|---:|---|---|---|---|---|",
        ]
    )
    for index, row in enumerate(report["guardRecoveredRows"], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    md_cell(row["company"]),
                    md_cell(row["title"]),
                    md_cell(row["summaryQuality"]),
                    md_cell(row["focusLabel"]),
                    md_cell(row["serviceScopeReason"]),
                ]
            )
            + " |"
        )
    if not report["guardRecoveredRows"]:
        lines.append("| - | - | - | - | - | - |")
    return "\n".join(lines).rstrip() + "\n"


def expected_false_hard_exclude(row: dict, action: str, expectations: dict[str, str]) -> bool:
    if action != "exclude":
        return False
    expected = expectations.get(clean_text(row.get("id", "")))
    if expected:
        return expected in {"include", "review"}
    return row_has_recoverable_service_scope_signal(row) and not row_has_strong_non_scope_signal(row)


def build_report(source: str, model_review_path: Path, goldset_path: Path) -> dict:
    payload = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    all_rows = build_base_rows(payload)
    override_items = load_service_scope_override_store().get("items", {})
    if source == "model-review":
        override_items = {
            **override_items,
            **load_model_review_overrides(model_review_path),
        }
    goldset_status, expectations = load_goldset_expectations(goldset_path)

    guard_on_included = []
    guard_off_included = []
    guard_off_excluded = []
    guard_off_review = []
    guard_off_hard_excluded = []
    guard_recovered = []
    guard_recovered_high = []
    ai_adjacent_excluded = []
    high_quality_excluded = []

    for row in all_rows:
        guard_on_decision = explain_service_scope_row(row, override_items=override_items)
        guard_off_decision = explain_guard_off(row, override_items=override_items)
        if guard_on_decision.get("included"):
            guard_on_included.append(row)
        if guard_off_decision.get("included"):
            guard_off_included.append(row)
        else:
            guard_off_excluded.append((row, guard_off_decision))
            action = clean_text(guard_off_decision.get("action", "")).lower()
            if action == "review":
                guard_off_review.append((row, guard_off_decision))
            if action == "exclude":
                guard_off_hard_excluded.append((row, guard_off_decision))

        override = resolve_service_scope_override(row, override_items=override_items)
        override_action = clean_text(override.get("action", "")).lower()
        expected = expectations.get(clean_text(row.get("id", "")))
        if model_exclude_should_be_recovered(row, override) and expected != "exclude":
            guard_recovered.append(compact_row(row, guard_off_decision))
            if clean_text(row.get("summaryQuality", "")).lower() == "high":
                guard_recovered_high.append(compact_row(row, guard_off_decision))
        elif override_action == "exclude" and expected in {"include", "review"}:
            guard_recovered.append(compact_row(row, guard_off_decision))
            if clean_text(row.get("summaryQuality", "")).lower() == "high":
                guard_recovered_high.append(compact_row(row, guard_off_decision))

    for row, decision in guard_off_hard_excluded:
        quality = clean_text(row.get("summaryQuality", "")).lower()
        if quality == "high" and expected_false_hard_exclude(row, "exclude", expectations):
            high_quality_excluded.append(compact_row(row, decision))
        if expected_false_hard_exclude(row, "exclude", expectations):
            ai_adjacent_excluded.append(compact_row(row, decision))

    total = len(all_rows)
    shadow_excluded_count = len(guard_off_excluded)
    metrics = {
        "sourceJobs": total,
        "currentGuardOnBoardRows": len(guard_on_included),
        "shadowBoardRows": len(guard_off_included),
        "shadowExcludedRows": shadow_excluded_count,
        "shadowReviewRows": len(guard_off_review),
        "shadowHardExcludedRows": len(guard_off_hard_excluded),
        "shadowSourceRetentionRate": round(len(guard_off_included) / total, 6) if total else 0,
        "shadowFilteredOutRate": round(shadow_excluded_count / total, 6) if total else 0,
        "shadowGuardRecoveredRows": len(guard_recovered),
        "shadowGuardRecoveredHighQualityRows": len(guard_recovered_high),
        "shadowExcludedAiAdjacentRows": len(ai_adjacent_excluded),
        "shadowExcludedHighQualityRows": len(high_quality_excluded),
    }
    targets = target_status(metrics)
    return {
        "generatedAt": now_iso(),
        "source": str(JOBS_PATH),
        "predictionSource": source,
        "modelReviewPath": str(model_review_path) if source == "model-review" else None,
        "goldsetPath": str(goldset_path),
        "goldsetStatus": goldset_status,
        "metrics": metrics,
        "targetStatus": targets,
        "targetsPassed": all(item["passed"] for item in targets.values()),
        "guardRecoveredRows": guard_recovered,
        "shadowExcludedAiAdjacentRows": ai_adjacent_excluded,
        "shadowExcludedHighQualityRows": high_quality_excluded,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", choices=["existing-overrides", "model-review"], default="existing-overrides")
    parser.add_argument("--model-review-path", type=Path, default=DEFAULT_MODEL_REVIEW_PATH)
    parser.add_argument("--goldset", type=Path, default=DEFAULT_GOLDSET_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_PATH)
    args = parser.parse_args()

    report = build_report(args.source, args.model_review_path, args.goldset)
    write_json(args.output, report)
    write_text(args.md_output, render_md(report))
    print(
        json.dumps(
            {
                "shadowJson": str(args.output),
                "shadowMd": str(args.md_output),
                "targetsPassed": report["targetsPassed"],
                "metrics": report["metrics"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
