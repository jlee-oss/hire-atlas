#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
LATEST_STATE_PATH = ROOT / "data" / "quality_iterations" / "latest_state.json"
GOLDSET_PATH = ROOT / "data" / "service_scope_goldset_001.json"
BENCHMARK_PATH = ROOT / "data" / "service_scope_model_benchmark_001.json"
SHADOW_PATH = ROOT / "data" / "service_scope_shadow_guard_off_001.json"
OUTPUT_PATH = ROOT / "data" / "model_improvement_gate_latest.json"
MD_OUTPUT_PATH = ROOT / "docs" / "model_improvement_gate_latest.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def criterion(actual, target, passed: bool) -> dict:
    return {
        "actual": actual,
        "target": target,
        "passed": bool(passed),
    }


def render_md(report: dict) -> str:
    lines = [
        "# Model Improvement Gate Latest",
        "",
        f"- generatedAt: `{report['generatedAt']}`",
        f"- status: `{report['status']}`",
        f"- passed: `{report['passed']}`",
        "",
        "## Criteria",
        "",
    ]
    for key, item in report["criteria"].items():
        lines.append(f"- `{key}` actual `{item['actual']}` target `{item['target']}` passed `{item['passed']}`")

    lines.extend(["", "## Inputs", ""])
    for key, value in report["inputs"].items():
        lines.append(f"- {key}: `{value}`")

    if report["blockers"]:
        lines.extend(["", "## Blockers", ""])
        for blocker in report["blockers"]:
            lines.append(f"- {blocker}")
    return "\n".join(lines).rstrip() + "\n"


def build_report(latest_path: Path, goldset_path: Path, benchmark_path: Path, shadow_path: Path) -> dict:
    latest = load_json(latest_path, {}) or {}
    goldset = load_json(goldset_path, {}) or {}
    benchmark = load_json(benchmark_path, {}) or {}
    shadow = load_json(shadow_path, {}) or {}

    metrics = latest.get("metrics", {}) if isinstance(latest.get("metrics", {}), dict) else {}
    gold_counts = goldset.get("counts", {}) if isinstance(goldset.get("counts", {}), dict) else {}
    benchmark_metrics = benchmark.get("metrics", {}) if isinstance(benchmark.get("metrics", {}), dict) else {}
    shadow_metrics = shadow.get("metrics", {}) if isinstance(shadow.get("metrics", {}), dict) else {}

    criteria = {
        "operationalLoopConverged": criterion(latest.get("status", ""), "converged", latest.get("status") == "converged"),
        "goldsetConfirmed": criterion(
            goldset.get("status", ""),
            "confirmed",
            goldset.get("status") == "confirmed"
            and int(gold_counts.get("provisionalItems", 0) or 0) == 0
            and int(gold_counts.get("confirmedItems", 0) or 0) > 0,
        ),
        "benchmarkFalseExcludeCount": criterion(
            int(benchmark_metrics.get("falseExcludeCount", 0) or 0),
            0,
            int(benchmark_metrics.get("falseExcludeCount", 0) or 0) == 0,
        ),
        "benchmarkHighQualityFalseExcludeCount": criterion(
            int(benchmark_metrics.get("highQualityFalseExcludeCount", 0) or 0),
            0,
            int(benchmark_metrics.get("highQualityFalseExcludeCount", 0) or 0) == 0,
        ),
        "benchmarkSchemaValidRate": criterion(
            float(benchmark_metrics.get("schemaValidRate", 0) or 0),
            1.0,
            float(benchmark_metrics.get("schemaValidRate", 0) or 0) >= 1.0,
        ),
        "benchmarkIncludeOrReviewRecall": criterion(
            float(benchmark_metrics.get("includeOrReviewRecall", 0) or 0),
            1.0,
            float(benchmark_metrics.get("includeOrReviewRecall", 0) or 0) >= 1.0,
        ),
        "modelBenchmarkPassed": criterion(
            bool(benchmark.get("modelPassedBenchmark", False)),
            True,
            bool(benchmark.get("modelPassedBenchmark", False)),
        ),
        "modelImprovementEligible": criterion(
            bool(benchmark.get("modelImprovementEligible", False)),
            True,
            bool(benchmark.get("modelImprovementEligible", False)),
        ),
        "shadowGuardOffTargetsPassed": criterion(
            bool(shadow.get("targetsPassed", False)),
            True,
            bool(shadow.get("targetsPassed", False)),
        ),
        "guardRecoveredRows": criterion(
            int(metrics.get("guardRecoveredRows", 0) or 0),
            0,
            int(metrics.get("guardRecoveredRows", 0) or 0) == 0,
        ),
        "guardRecoveredHighQualityRows": criterion(
            int(metrics.get("guardRecoveredHighQualityRows", 0) or 0),
            0,
            int(metrics.get("guardRecoveredHighQualityRows", 0) or 0) == 0,
        ),
    }

    blockers = [
        key
        for key, item in criteria.items()
        if not item["passed"]
    ]
    passed = not blockers
    report = {
        "generatedAt": now_iso(),
        "status": "passed" if passed else "blocked",
        "passed": passed,
        "criteria": criteria,
        "blockers": blockers,
        "metrics": {
            "latestIteration": latest.get("iteration"),
            "latestOptimizationScore": metrics.get("optimizationScore"),
            "goldsetItems": gold_counts.get("items", 0),
            "goldsetConfirmedItems": gold_counts.get("confirmedItems", 0),
            "goldsetProvisionalItems": gold_counts.get("provisionalItems", 0),
            "shadowGuardRecoveredRows": shadow_metrics.get("shadowGuardRecoveredRows", 0),
            "shadowExcludedAiAdjacentRows": shadow_metrics.get("shadowExcludedAiAdjacentRows", 0),
        },
        "inputs": {
            "latestState": str(latest_path),
            "goldset": str(goldset_path),
            "benchmark": str(benchmark_path),
            "shadowGuardOff": str(shadow_path),
        },
    }
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latest-state", type=Path, default=LATEST_STATE_PATH)
    parser.add_argument("--goldset", type=Path, default=GOLDSET_PATH)
    parser.add_argument("--benchmark", type=Path, default=BENCHMARK_PATH)
    parser.add_argument("--shadow", type=Path, default=SHADOW_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--md-output", type=Path, default=MD_OUTPUT_PATH)
    args = parser.parse_args()

    report = build_report(args.latest_state, args.goldset, args.benchmark, args.shadow)
    write_json(args.output, report)
    write_text(args.md_output, render_md(report))
    print(
        json.dumps(
            {
                "gateJson": str(args.output),
                "gateMd": str(args.md_output),
                "status": report["status"],
                "passed": report["passed"],
                "blockers": report["blockers"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
