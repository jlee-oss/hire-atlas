#!/usr/bin/env python3

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GOLDSET_PATH = ROOT / "data" / "service_scope_goldset_001.json"
DEFAULT_OVERRIDE_PATH = ROOT / "data" / "service_scope_overrides.json"
DEFAULT_MODEL_REVIEW_PATH = ROOT / "data" / "service_scope_model_review.json"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "service_scope_model_benchmark_001.json"
DEFAULT_MD_PATH = ROOT / "docs" / "service_scope_model_benchmark_001.md"
VALID_DECISIONS = {"include", "review", "exclude"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def normalize_decision(value) -> str:
    decision = clean_text(value).lower()
    return decision if decision in VALID_DECISIONS else ""


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def md_cell(value) -> str:
    return clean_text(value).replace("|", "\\|") or "-"


def load_predictions(args) -> tuple[str, dict[str, dict]]:
    if args.source == "existing-overrides":
        store = load_json(args.override_path, {"items": {}}) or {"items": {}}
        predictions = {}
        for job_id, item in store.get("items", {}).items():
            if not isinstance(item, dict):
                continue
            predictions[job_id] = {
                "decision": normalize_decision(item.get("action", "")),
                "confidence": clean_text(item.get("confidence", "")),
                "reason": clean_text(item.get("reason", "")),
                "source": clean_text(item.get("source", "")),
            }
        return str(args.override_path), predictions

    report = load_json(args.model_review_path, {"items": []}) or {"items": []}
    predictions = {}
    for item in report.get("items", []):
        decision = item.get("modelDecision", {})
        if not isinstance(decision, dict):
            continue
        job_id = clean_text(item.get("id", ""))
        if not job_id:
            continue
        predictions[job_id] = {
            "decision": normalize_decision(decision.get("decision", "")),
            "confidence": clean_text(decision.get("confidence", "")),
            "reason": clean_text(decision.get("reason", "")),
            "source": "service_scope_model_review_report",
        }
    return str(args.model_review_path), predictions


def score_rows(goldset: dict, predictions: dict[str, dict]) -> tuple[dict, list[dict]]:
    rows = []
    expected_counts = Counter()
    predicted_counts = Counter()
    false_exclude_rows = []
    high_quality_false_exclude_rows = []
    exact_count = 0
    valid_schema_count = 0
    missing_prediction_count = 0
    include_or_review_expected = 0

    for item in goldset.get("items", []):
        job_id = clean_text(item.get("id", ""))
        expected = normalize_decision((item.get("target", {}) or {}).get("serviceScopeAction", ""))
        prediction = predictions.get(job_id, {})
        actual = normalize_decision(prediction.get("decision", ""))
        quality = clean_text(item.get("summaryQuality", ""))
        expected_counts[expected or "unconfirmed"] += 1
        predicted_counts[actual or "missing"] += 1

        schema_valid = actual in VALID_DECISIONS
        if schema_valid:
            valid_schema_count += 1
        else:
            missing_prediction_count += 1
        exact = bool(expected and actual and expected == actual)
        if exact:
            exact_count += 1

        false_exclude = expected in {"include", "review"} and actual == "exclude"
        if expected in {"include", "review"}:
            include_or_review_expected += 1
        row = {
            "id": job_id,
            "company": clean_text(item.get("company", "")),
            "title": clean_text(item.get("title", "")),
            "summaryQuality": quality,
            "expected": expected,
            "actual": actual or "missing",
            "confidence": clean_text(prediction.get("confidence", "")),
            "reason": clean_text(prediction.get("reason", "")),
            "predictionSource": clean_text(prediction.get("source", "")),
            "decisionSource": clean_text((item.get("review", {}) or {}).get("decisionSource", "")),
            "schemaValid": schema_valid,
            "exact": exact,
            "falseExclude": false_exclude,
        }
        rows.append(row)
        if false_exclude:
            false_exclude_rows.append(row)
            if quality == "high":
                high_quality_false_exclude_rows.append(row)

    total = len(rows)
    schema_rate = valid_schema_count / total if total else 0.0
    exact_rate = exact_count / total if total else 0.0
    include_or_review_recall = (
        (include_or_review_expected - len(false_exclude_rows)) / include_or_review_expected
        if include_or_review_expected
        else 0.0
    )
    review_usage_rate = predicted_counts["review"] / valid_schema_count if valid_schema_count else 0.0

    metrics = {
        "evaluated": total,
        "expectedCounts": dict(sorted(expected_counts.items())),
        "predictedCounts": dict(sorted(predicted_counts.items())),
        "schemaValidRate": round(schema_rate, 4),
        "exactDecisionAccuracy": round(exact_rate, 4),
        "includeOrReviewRecall": round(include_or_review_recall, 4),
        "reviewUsageRate": round(review_usage_rate, 4),
        "falseExcludeCount": len(false_exclude_rows),
        "highQualityFalseExcludeCount": len(high_quality_false_exclude_rows),
        "missingPredictionCount": missing_prediction_count,
    }
    return metrics, rows


def render_md(report: dict) -> str:
    metrics = report["metrics"]
    criteria = report["criteria"]
    lines = [
        "# Service Scope Model Benchmark 001",
        "",
        f"- generatedAt: `{report['generatedAt']}`",
        f"- source: `{report['predictionSource']}`",
        f"- goldsetStatus: `{report['goldsetStatus']}`",
        f"- modelImprovementEligible: `{report['modelImprovementEligible']}`",
        "",
        "## Metrics",
        "",
        f"- evaluated: `{metrics['evaluated']}`",
        f"- exactDecisionAccuracy: `{metrics['exactDecisionAccuracy']}`",
        f"- includeOrReviewRecall: `{metrics['includeOrReviewRecall']}`",
        f"- schemaValidRate: `{metrics['schemaValidRate']}`",
        f"- reviewUsageRate: `{metrics['reviewUsageRate']}`",
        f"- falseExcludeCount: `{metrics['falseExcludeCount']}`",
        f"- highQualityFalseExcludeCount: `{metrics['highQualityFalseExcludeCount']}`",
        f"- missingPredictionCount: `{metrics['missingPredictionCount']}`",
        "",
        "## Criteria",
        "",
    ]
    for key, item in criteria.items():
        lines.append(f"- `{key}` actual `{item['actual']}` target `{item['target']}` passed `{item['passed']}`")

    false_excludes = [row for row in report["rows"] if row["falseExclude"]]
    lines.extend(
        [
            "",
            "## False Excludes",
            "",
            "| # | company | title | quality | expected | actual | reason |",
            "|---:|---|---|---|---|---|---|",
        ]
    )
    for index, row in enumerate(false_excludes, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    md_cell(row["company"]),
                    md_cell(row["title"]),
                    md_cell(row["summaryQuality"]),
                    md_cell(row["expected"]),
                    md_cell(row["actual"]),
                    md_cell(row["reason"]),
                ]
            )
            + " |"
        )
    if not false_excludes:
        lines.append("| - | - | - | - | - | - | - |")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goldset", type=Path, default=DEFAULT_GOLDSET_PATH)
    parser.add_argument("--source", choices=["existing-overrides", "model-review"], default="existing-overrides")
    parser.add_argument("--override-path", type=Path, default=DEFAULT_OVERRIDE_PATH)
    parser.add_argument("--model-review-path", type=Path, default=DEFAULT_MODEL_REVIEW_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_PATH)
    args = parser.parse_args()

    goldset = load_json(args.goldset, {"items": [], "status": "missing"}) or {"items": [], "status": "missing"}
    prediction_source, predictions = load_predictions(args)
    metrics, rows = score_rows(goldset, predictions)

    criteria = {
        "falseExcludeCount": {
            "actual": metrics["falseExcludeCount"],
            "target": 0,
            "passed": metrics["falseExcludeCount"] == 0,
        },
        "highQualityFalseExcludeCount": {
            "actual": metrics["highQualityFalseExcludeCount"],
            "target": 0,
            "passed": metrics["highQualityFalseExcludeCount"] == 0,
        },
        "includeOrReviewRecall": {
            "actual": metrics["includeOrReviewRecall"],
            "target": 1.0,
            "passed": metrics["includeOrReviewRecall"] >= 1.0,
        },
        "schemaValidRate": {
            "actual": metrics["schemaValidRate"],
            "target": 1.0,
            "passed": metrics["schemaValidRate"] >= 1.0,
        },
    }
    model_passed = all(item["passed"] for item in criteria.values())
    model_improvement_eligible = model_passed and goldset.get("status") == "confirmed"

    report = {
        "generatedAt": now_iso(),
        "goldsetPath": str(args.goldset),
        "goldsetStatus": clean_text(goldset.get("status", "")),
        "predictionSource": prediction_source,
        "sourceMode": args.source,
        "metrics": metrics,
        "criteria": criteria,
        "modelPassedBenchmark": model_passed,
        "modelImprovementEligible": model_improvement_eligible,
        "rows": rows,
    }
    write_json(args.output, report)
    write_text(args.md_output, render_md(report))
    print(
        json.dumps(
            {
                "benchmarkJson": str(args.output),
                "benchmarkMd": str(args.md_output),
                "goldsetStatus": report["goldsetStatus"],
                "modelPassedBenchmark": model_passed,
                "modelImprovementEligible": model_improvement_eligible,
                "metrics": metrics,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
