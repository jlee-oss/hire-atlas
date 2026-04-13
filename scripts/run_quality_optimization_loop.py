#!/usr/bin/env python3

import argparse
import json
import os
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "data" / "quality_optimization_loop_config.json"
SUMMARY_BOARD_PATH = ROOT / "data" / "summary_board.json"
JOBS_PATH = ROOT / "data" / "jobs.json"
JOB_SUMMARIES_PATH = ROOT / "data" / "job_summaries.json"
MODEL_RELEASE_CONFIG_PATH = ROOT / "data" / "model_release_config.json"
RELEASE_REMEDIATION_PATH = ROOT / "data" / "release_remediation_wave_001.json"
ROLE_REMEDIATION_PATH = ROOT / "data" / "role_group_remediation_wave_001.json"
ROLE_GROUP_OVERRIDE_PATH = ROOT / "data" / "role_group_overrides.json"
STRUCTURED_SIGNAL_SCORE_PATH = ROOT / "data" / "structured_signal_validation_score_001.json"
EVAL_SET_PATH = ROOT / "data" / "eval_set.json"
INCREMENTAL_EVAL_SET_PATH = ROOT / "data" / "incremental_eval_set.json"
ITERATION_JSON_DIR = ROOT / "data" / "quality_iterations"
ITERATION_MD_DIR = ROOT / "docs" / "quality_iterations"
LATEST_STATE_PATH = ITERATION_JSON_DIR / "latest_state.json"
SUMMARY_SNAPSHOT_LATEST_PATH = ROOT / "data" / "summary_snapshot_latest.json"
ROLE_BENCHMARK_LATEST_PATH = ROOT / "data" / "role_group_benchmark_latest.json"
MODEL_DECISION_REPORT_PATH = ROOT / "docs" / "model_decision_report.md"
REVIEW_ACCURACY_REPORT_PATH = ROOT / "docs" / "review_accuracy_report.md"
FULL_DATASET_HARNESS_JSON_PATH = ROOT / "data" / "full_dataset_harness_latest.json"
FULL_DATASET_HARNESS_MD_PATH = ROOT / "docs" / "full_dataset_harness_latest.md"
SERVICE_SCOPE_GOLDSET_PATH = ROOT / "data" / "service_scope_goldset_001.json"

ALLOWED_ROLES = {
    "인공지능 엔지니어",
    "인공지능 리서처",
    "데이터 사이언티스트",
    "데이터 분석가",
}
STRUCTURED_SIGNAL_KEYS = (
    "roleSignals",
    "domainSignals",
    "problemSignals",
    "systemSignals",
    "modelSignals",
    "dataSignals",
    "workflowSignals",
)
PRIORITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3}
AI_ADJACENT_SCOPE_PATTERNS = (
    r"\bai\b",
    r"인공지능",
    r"머신러닝",
    r"\bml\b",
    r"딥러닝",
    r"\bllm\b",
    r"\brag\b",
    r"생성형",
    r"컴퓨터\s*비전",
    r"자율주행",
    r"로보틱스",
    r"\bnpu\b",
    r"\bsoc\b",
    r"반도체",
    r"의료\s*ai",
    r"\bsamd\b",
    r"\bmlops\b",
)
DATA_ADJACENT_SCOPE_PATTERNS = (
    r"데이터\s*분석",
    r"데이터\s*사이언스",
    r"\bdata\s*scien",
    r"\bdata\s*analy",
    r"\banalytics?\b",
    r"\ba/b\b",
    r"에이비\s*테스트",
    r"\bkpi\b",
    r"\bsql\b",
)
AI_ADJACENT_STRONG_NON_SCOPE_PATTERNS = (
    r"product manager|product owner|head of product",
    r"\bpm\b|\bpo\b|\bpl\b",
    r"프로덕트|제품\s*관리",
    r"designer|ux/ui|디자이너|디자인\s*시스템|디자인\s*업무",
    r"영업|sales|세일즈|account executive|영업대표",
    r"브랜드\s*매니저|\bmd\b",
    r"정부지원사업|행정|연구지원|사업\s*운영",
    r"recruit|채용|강사|멘토",
    r"보안점검|모의해킹|취약점",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def canonical_text(value) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", clean_text(value).lower())


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def load_confirmed_service_scope_excludes() -> set[str]:
    payload = load_json(SERVICE_SCOPE_GOLDSET_PATH, {}) or {}
    if clean_text(payload.get("status", "")).lower() != "confirmed":
        return set()
    confirmed_excludes = set()
    for item in payload.get("items", []):
        if not isinstance(item, dict):
            continue
        review = item.get("review", {}) if isinstance(item.get("review", {}), dict) else {}
        target = item.get("target", {}) if isinstance(item.get("target", {}), dict) else {}
        action = clean_text(target.get("serviceScopeAction", "")).lower()
        if action == "exclude" and not bool(review.get("requiresHumanConfirmation", True)):
            confirmed_excludes.add(clean_text(item.get("id", "")))
    return {job_id for job_id in confirmed_excludes if job_id}


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run_script(script_path: Path, args: list[str] | None = None, env_overrides: dict | None = None) -> str:
    command = [sys.executable, str(script_path), *(args or [])]
    env = os.environ.copy()
    if env_overrides:
        env.update({key: value for key, value in env_overrides.items() if value is not None})
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"{script_path.name} failed with code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
    return result.stdout.strip()


def flatten_structured_signals(signals: dict) -> list[str]:
    values = []
    if not isinstance(signals, dict):
        return values
    for key in STRUCTURED_SIGNAL_KEYS:
        raw_values = signals.get(key, [])
        if not isinstance(raw_values, list):
            continue
        for value in raw_values:
            cleaned = clean_text(value)
            if cleaned:
                values.append(cleaned)
    return values


def reviewed_items(items: list[dict]) -> list[dict]:
    reviewed = []
    for item in items:
        review = item.get("review", {}) if isinstance(item.get("review", {}), dict) else {}
        if review.get("overallPass") is not None:
            reviewed.append(item)
            continue
        if any(review.get(key) is not None for key in ("summaryPass", "focusLabelPass", "keywordsPass")):
            reviewed.append(item)
            continue
        if any(
            review.get(key)
            for key in (
                "correctedSummary",
                "correctedFocusLabel",
                "correctedKeywords",
                "correctedQuality",
                "notes",
                "expectedSummary",
                "expectedFocusLabel",
                "expectedKeywords",
                "expectedQuality",
            )
        ):
            reviewed.append(item)
    return reviewed


def normalized_allowed_role(value: str) -> str:
    cleaned = clean_text(value)
    return cleaned if cleaned in ALLOWED_ROLES else ""


def build_summary_snapshot() -> dict:
    jobs_payload = load_json(JOBS_PATH, {"jobs": []}) or {"jobs": []}
    summaries_payload = load_json(JOB_SUMMARIES_PATH, {"items": {}}) or {"items": {}}
    board_payload = load_json(SUMMARY_BOARD_PATH, {"rows": []}) or {"rows": []}
    jobs = jobs_payload.get("jobs", [])
    items = summaries_payload.get("items", {})
    board_rows = board_payload.get("rows", [])

    broad_focus_labels = {
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
    accepted_broad_focus_labels = {
        "컴퓨터 비전",
        "클라우드",
        "데이터 분석",
        "의료",
        "의료 데이터",
        "마케팅",
    }

    summary_present = 0
    focus_present = 0
    low_count = 0
    provider_counter = Counter()
    focus_counter = Counter()
    board_focus_counter = Counter()
    broad_focus_raw = 0
    accepted_broad_raw = 0
    bad_broad_raw = 0
    broad_focus_board = 0
    accepted_broad_board = 0
    bad_broad_board = 0
    low_blank_focus_rows = 0

    for job in jobs:
        item = items.get(job.get("id", ""), {})
        summary = clean_text(item.get("summary", ""))
        focus = clean_text(item.get("focusLabel", ""))
        quality = clean_text(item.get("quality", "")).lower()
        provider = clean_text(((item.get("provider") or {}).get("model")) or "")
        if summary:
            summary_present += 1
        if focus:
            focus_present += 1
            focus_counter[focus] += 1
            if focus in broad_focus_labels:
                broad_focus_raw += 1
                if focus in accepted_broad_focus_labels:
                    accepted_broad_raw += 1
                else:
                    bad_broad_raw += 1
        if quality == "low":
            low_count += 1
        if provider:
            provider_counter[provider] += 1

    for row in board_rows:
        focus = clean_text(row.get("focusLabel", ""))
        quality = clean_text(row.get("summaryQuality", "")).lower()
        if focus:
            board_focus_counter[focus] += 1
            if focus in broad_focus_labels:
                broad_focus_board += 1
                if focus in accepted_broad_focus_labels:
                    accepted_broad_board += 1
                else:
                    bad_broad_board += 1
        if quality == "low" and not focus:
            low_blank_focus_rows += 1

    snapshot = {
        "generatedAt": now_iso(),
        "jobs": len(jobs),
        "summaryPresent": summary_present,
        "focusPresent": focus_present,
        "low": low_count,
        "broadFocusRaw": broad_focus_raw,
        "acceptedBroadRaw": accepted_broad_raw,
        "badBroadRaw": bad_broad_raw,
        "broadFocusBoard": broad_focus_board,
        "acceptedBroadBoard": accepted_broad_board,
        "badBroadBoard": bad_broad_board,
        "lowBlankFocusRows": low_blank_focus_rows,
        "providers": dict(provider_counter),
        "topFocus": [{"label": label, "count": count} for label, count in focus_counter.most_common(15)],
        "topBoardFocus": [{"label": label, "count": count} for label, count in board_focus_counter.most_common(15)],
    }
    write_json(SUMMARY_SNAPSHOT_LATEST_PATH, snapshot)
    return snapshot


def build_role_benchmark_snapshot() -> dict:
    output = run_script(ROOT / "scripts" / "run_role_group_benchmark.py")
    payload = json.loads(output)
    write_json(ROLE_BENCHMARK_LATEST_PATH, payload)
    return payload


def refresh_artifacts(loop_config: dict, model_config: dict) -> tuple[dict, list[str]]:
    artifacts = {}
    errors = []
    auto_repairs = loop_config.get("autoRepairs", {}) if isinstance(loop_config.get("autoRepairs", {}), dict) else {}
    ready_for_model = model_action_ready(model_config)

    if ready_for_model and auto_repairs.get("refreshMissingSummariesBeforeMeasure", False):
        try:
            prompt_profile = load_release_metrics().get("promptProfile") or "field_aware_v3"
            run_script(
                ROOT / "scripts" / "generate_job_summaries.py",
                [
                    "--base-url",
                    model_config.get("baseUrl", ""),
                    "--model",
                    model_config.get("model", ""),
                    "--api-key",
                    model_config.get("apiKey", ""),
                    "--mode",
                    "missing",
                    "--batch-size",
                    "2",
                    "--prompt-profile",
                    prompt_profile,
                ],
            )
            artifacts["preMeasureSummaryRefresh"] = f"missing:{prompt_profile}"
        except Exception as error:
            errors.append(f"pre-measure missing summary refresh failed: {error}")

    if ready_for_model and auto_repairs.get("refreshRoleOverridesBeforeMeasure", False):
        try:
            run_script(
                ROOT / "scripts" / "classify_role_groups.py",
                [
                    "--base-url",
                    model_config.get("baseUrl", ""),
                    "--model",
                    model_config.get("model", ""),
                    "--api-key",
                    model_config.get("apiKey", ""),
                    "--mode",
                    "stale",
                    "--batch-size",
                    "4",
                ],
            )
            artifacts["preMeasureRoleRefresh"] = "stale"
        except Exception as error:
            errors.append(f"pre-measure stale role refresh failed: {error}")

    if ready_for_model and auto_repairs.get("refreshMissingRoleOverridesBeforeMeasure", False):
        try:
            run_script(
                ROOT / "scripts" / "classify_role_groups.py",
                [
                    "--base-url",
                    model_config.get("baseUrl", ""),
                    "--model",
                    model_config.get("model", ""),
                    "--api-key",
                    model_config.get("apiKey", ""),
                    "--mode",
                    "missing",
                    "--batch-size",
                    "4",
                ],
            )
            artifacts["preMeasureRoleRefresh"] = (
                "stale+missing" if artifacts.get("preMeasureRoleRefresh") else "missing"
            )
        except Exception as error:
            errors.append(f"pre-measure missing role refresh failed: {error}")

    try:
        run_script(ROOT / "scripts" / "build_summary_board.py")
        artifacts["summaryBoard"] = str(SUMMARY_BOARD_PATH)
    except Exception as error:
        raise RuntimeError(f"summary board refresh failed: {error}") from error

    try:
        run_script(ROOT / "scripts" / "run_full_dataset_validation_harness.py")
        artifacts["fullDatasetHarness"] = str(FULL_DATASET_HARNESS_JSON_PATH)
    except Exception as error:
        errors.append(f"full dataset harness refresh failed: {error}")

    try:
        snapshot = build_summary_snapshot()
        artifacts["summarySnapshot"] = str(SUMMARY_SNAPSHOT_LATEST_PATH)
        artifacts["summarySnapshotPayload"] = snapshot
    except Exception as error:
        errors.append(f"summary snapshot refresh failed: {error}")

    try:
        role_benchmark = build_role_benchmark_snapshot()
        artifacts["roleBenchmark"] = str(ROLE_BENCHMARK_LATEST_PATH)
        artifacts["roleBenchmarkPayload"] = role_benchmark
    except Exception as error:
        errors.append(f"role benchmark refresh failed: {error}")

    try:
        run_script(ROOT / "scripts" / "score_review_accuracy.py")
        artifacts["reviewAccuracyReport"] = str(REVIEW_ACCURACY_REPORT_PATH)
    except Exception as error:
        errors.append(f"review accuracy refresh failed: {error}")

    if loop_config.get("autoArtifacts", {}).get("releaseRemediationWave", True):
        try:
            run_script(ROOT / "scripts" / "build_release_remediation_wave.py")
            artifacts["releaseRemediationWave"] = str(RELEASE_REMEDIATION_PATH)
        except Exception as error:
            errors.append(f"release remediation wave refresh failed: {error}")

    if loop_config.get("autoArtifacts", {}).get("roleGroupRemediationWave", True):
        try:
            run_script(ROOT / "scripts" / "build_role_group_remediation_wave.py")
            artifacts["roleGroupRemediationWave"] = str(ROLE_REMEDIATION_PATH)
        except Exception as error:
            errors.append(f"role group remediation wave refresh failed: {error}")

    if loop_config.get("autoArtifacts", {}).get("modelDecisionReport", True):
        try:
            run_script(ROOT / "scripts" / "build_model_decision_report.py")
            artifacts["modelDecisionReport"] = str(MODEL_DECISION_REPORT_PATH)
        except Exception as error:
            errors.append(f"model decision report refresh failed: {error}")

    if STRUCTURED_SIGNAL_SCORE_PATH.exists():
        artifacts["structuredSignalScore"] = str(STRUCTURED_SIGNAL_SCORE_PATH)

    summary_champion = load_json(MODEL_RELEASE_CONFIG_PATH, {}) or {}
    report_path = Path(((summary_champion.get("summaryChampion") or {}).get("reportPath")) or "")
    if report_path.exists():
        artifacts["releaseGateReport"] = str(report_path)

    return artifacts, errors


def load_release_metrics() -> dict:
    config = load_json(MODEL_RELEASE_CONFIG_PATH, {}) or {}
    champion = config.get("summaryChampion", {}) if isinstance(config.get("summaryChampion", {}), dict) else {}
    report_path = Path(champion.get("reportPath", "") or "")
    report = load_json(report_path, {}) if report_path.exists() else {}
    report_champion = report.get("champion", {}) if isinstance(report.get("champion", {}), dict) else {}

    core = report_champion.get("core") or champion.get("coreMetrics") or {}
    incremental = report_champion.get("incremental") or champion.get("incrementalMetrics") or {}

    return {
        "promptProfile": champion.get("promptProfile", ""),
        "model": champion.get("model", ""),
        "baseUrl": champion.get("baseUrl", ""),
        "reportPath": str(report_path) if report_path else "",
        "core": {
            "strictPassRate": float(core.get("strictPassRate", 0.0) or 0.0),
            "focusExactRate": float(core.get("focusExactRate", 0.0) or 0.0),
            "avgKeywordF1": float(core.get("avgKeywordF1", 0.0) or 0.0),
            "lowMatchRate": float(core.get("lowMatchRate", 0.0) or 0.0),
        },
        "incremental": {
            "usableItemRate": float(incremental.get("usableItemRate", 0.0) or 0.0),
            "lowRate": float(incremental.get("lowRate", 0.0) or 0.0),
            "emptyFocusLabelRate": float(incremental.get("emptyFocusLabelRate", 0.0) or 0.0),
            "keywordBannedRate": float(incremental.get("keywordBannedRate", 0.0) or 0.0),
        },
    }


def signal_role_leakage_enabled() -> bool:
    app_js = (ROOT / "app.js").read_text(encoding="utf-8")
    match = re.search(r"function signalFirstSeedTerms\(.*?\n\}", app_js, re.S)
    if not match:
        return False
    body = match.group(0)
    leakage_tokens = ("...facets.role", "...clusterFacets.role", "row.roleGroup || \"\"", "row.role || \"\"")
    return any(token in body for token in leakage_tokens)


def diagnostic_row_text(row: dict) -> str:
    return " ".join(
        [
            clean_text(row.get("company", "")),
            clean_text(row.get("title", "")),
            clean_text(row.get("focusLabel", "")),
            clean_text(row.get("serviceScopeReason", "")),
            " ".join(clean_text(value) for value in (row.get("highlightKeywords") or [])),
        ]
    ).lower()


def is_ai_adjacent_scope_risk(row: dict) -> bool:
    quality = clean_text(row.get("summaryQuality", "")).lower()
    if quality not in {"high", "medium"}:
        return False
    text = diagnostic_row_text(row)
    if any(re.search(pattern, text) for pattern in AI_ADJACENT_STRONG_NON_SCOPE_PATTERNS):
        return False
    if any(re.search(pattern, text) for pattern in AI_ADJACENT_SCOPE_PATTERNS):
        return True
    role = clean_text(row.get("rawRole", "") or row.get("roleGroup", ""))
    return role in {"데이터 사이언티스트", "데이터 분석가"} and any(
        re.search(pattern, text) for pattern in DATA_ADJACENT_SCOPE_PATTERNS
    )


def metric_fraction(actual: float, target: float, comparator: str) -> float:
    if comparator == "max":
        if target <= 0:
            return 1.0 if actual <= 0 else 0.0
        if actual <= target:
            return 1.0
        return max(0.0, min(target / actual, 1.0))
    if target <= 0:
        return 1.0
    if actual >= target:
        return 1.0
    return max(0.0, min(actual / target, 1.0))


def compute_optimization_score(metrics: dict, loop_config: dict) -> tuple[float, dict]:
    targets = loop_config.get("targets", {})
    weights = loop_config.get("scoreWeights", {})
    comparators = {
        "boardLowRate": "max",
        "boardMissingSummaryRows": "max",
        "signalMetaLeakRows": "max",
        "mixedClusterRoleLeakRows": "max",
        "roleConflictRows": "max",
        "roleMissingClassifierRows": "max",
        "roleStaleClassifierRows": "max",
        "releaseCoreFocusExact": "min",
        "releaseCoreKeywordF1": "min",
        "releaseIncrementalUsable": "min",
        "releaseIncrementalLowRate": "max",
        "releaseIncrementalBannedKeywordRate": "max",
        "sourceRetentionRate": "min",
        "filteredOutRate": "max",
        "excludedHighQualityRows": "max",
        "excludedAiAdjacentRows": "max",
        "excludedLeakedIntoDisplayRows": "max",
        "deeptechInDataAnalystRows": "max",
        "businessInEngineerFamilyRows": "max",
        "toolFirstFocusRows": "max",
        "serviceScopeStaleRows": "max",
        "guardRecoveredRows": "max",
        "guardRecoveredHighQualityRows": "max",
    }
    target_key_map = {
        "boardLowRate": "boardLowRateMax",
        "boardMissingSummaryRows": "boardMissingSummaryRowsMax",
        "signalMetaLeakRows": "signalMetaLeakRowsMax",
        "mixedClusterRoleLeakRows": "mixedClusterRoleLeakRowsMax",
        "roleConflictRows": "roleConflictRowsMax",
        "roleMissingClassifierRows": "roleMissingClassifierRowsMax",
        "roleStaleClassifierRows": "roleStaleClassifierRowsMax",
        "releaseCoreFocusExact": "releaseCoreFocusExactMin",
        "releaseCoreKeywordF1": "releaseCoreKeywordF1Min",
        "releaseIncrementalUsable": "releaseIncrementalUsableMin",
        "releaseIncrementalLowRate": "releaseIncrementalLowRateMax",
        "releaseIncrementalBannedKeywordRate": "releaseIncrementalBannedKeywordRateMax",
        "sourceRetentionRate": "sourceRetentionRateMin",
        "filteredOutRate": "filteredOutRateMax",
        "excludedHighQualityRows": "excludedHighQualityRowsMax",
        "excludedAiAdjacentRows": "excludedAiAdjacentRowsMax",
        "excludedLeakedIntoDisplayRows": "excludedLeakedIntoDisplayRowsMax",
        "deeptechInDataAnalystRows": "deeptechInDataAnalystRowsMax",
        "businessInEngineerFamilyRows": "businessInEngineerFamilyRowsMax",
        "toolFirstFocusRows": "toolFirstFocusRowsMax",
        "serviceScopeStaleRows": "serviceScopeStaleRowsMax",
        "guardRecoveredRows": "guardRecoveredRowsMax",
        "guardRecoveredHighQualityRows": "guardRecoveredHighQualityRowsMax",
    }

    status = {}
    weighted_sum = 0.0
    total_weight = 0.0
    for metric_name, weight in weights.items():
        if metric_name not in metrics:
            continue
        if metric_name not in comparators or metric_name not in target_key_map:
            continue
        target = float(targets.get(target_key_map[metric_name], 0) or 0)
        comparator = comparators[metric_name]
        actual = float(metrics.get(metric_name, 0) or 0)
        fraction = metric_fraction(actual, target, comparator)
        if comparator == "max":
            passed = actual <= target
        else:
            passed = actual >= target
        status[metric_name] = {
            "actual": actual,
            "target": target,
            "comparator": comparator,
            "passed": passed,
            "scoreFraction": round(fraction, 6),
        }
        weighted_sum += fraction * float(weight)
        total_weight += float(weight)
    optimization_score = round((weighted_sum / total_weight) * 100.0, 4) if total_weight else 0.0
    return optimization_score, status


def build_metrics(loop_config: dict, artifacts: dict) -> dict:
    board = load_json(SUMMARY_BOARD_PATH, {"rows": []}) or {"rows": []}
    rows = board.get("rows", [])
    total_rows = len(rows)
    diagnostics = board.get("diagnostics", {}) if isinstance(board.get("diagnostics", {}), dict) else {}
    excluded_diagnostic_rows = (
        diagnostics.get("excludedRows", [])
        if isinstance(diagnostics.get("excludedRows", []), list)
        else []
    )
    hard_excluded_diagnostic_rows = [
        row
        for row in excluded_diagnostic_rows
        if clean_text(row.get("serviceScopeAction", "")).lower() != "review"
    ]
    confirmed_scope_exclude_ids = load_confirmed_service_scope_excludes()
    jobs_payload = load_json(JOBS_PATH, {"jobs": []}) or {"jobs": []}
    total_jobs = len(jobs_payload.get("jobs", []))
    jobs_by_id = {
        job.get("id", ""): job
        for job in jobs_payload.get("jobs", [])
        if clean_text(job.get("id", ""))
    }
    summary_items = (load_json(JOB_SUMMARIES_PATH, {"items": {}}) or {"items": {}}).get("items", {})
    role_override_items = (load_json(ROLE_GROUP_OVERRIDE_PATH, {"items": {}}) or {"items": {}}).get("items", {})
    signal_leak_keys = {canonical_text(term) for term in loop_config.get("signalLeakTerms", []) if clean_text(term)}
    display_leak_keys = {canonical_text(term) for term in loop_config.get("displayLeakTerms", []) if clean_text(term)}

    low_rows = []
    missing_summary_rows = []
    explicit_low_rows = []
    signal_leak_rows = []
    display_leak_rows = []
    mixed_role_rows = []
    role_conflict_rows = []
    role_low_conflict_rows = []
    role_missing_rows = []
    role_stale_rows = []
    excluded_high_quality_rows = [
        clean_text(row.get("id", ""))
        for row in hard_excluded_diagnostic_rows
        if clean_text(row.get("summaryQuality", "")).lower() == "high"
        and clean_text(row.get("id", "")) not in confirmed_scope_exclude_ids
    ]
    excluded_medium_or_high_quality_rows = [
        clean_text(row.get("id", ""))
        for row in hard_excluded_diagnostic_rows
        if clean_text(row.get("summaryQuality", "")).lower() in {"high", "medium"}
        and clean_text(row.get("id", "")) not in confirmed_scope_exclude_ids
    ]
    excluded_ai_adjacent_rows = [
        clean_text(row.get("id", ""))
        for row in hard_excluded_diagnostic_rows
        if is_ai_adjacent_scope_risk(row)
        and clean_text(row.get("id", "")) not in confirmed_scope_exclude_ids
    ]
    high_confidence_excluded_rows = [
        clean_text(row.get("id", ""))
        for row in hard_excluded_diagnostic_rows
        if clean_text(row.get("serviceScopeConfidence", "")).lower() == "high"
        and clean_text(row.get("id", "")) not in confirmed_scope_exclude_ids
    ]
    guard_recovered_rows = [
        row
        for row in rows
        if clean_text(row.get("serviceScopeAction", "")).lower() == "exclude"
        and clean_text(row.get("serviceScopeResolvedAction", "")).lower() == "include"
    ]
    guard_recovered_high_quality_rows = [
        row for row in guard_recovered_rows if clean_text(row.get("summaryQuality", "")).lower() == "high"
    ]

    for row in rows:
        row_id = row.get("id", "")
        quality = clean_text(row.get("summaryQuality", "")).lower()
        summary_item = summary_items.get(row_id, {}) if isinstance(summary_items, dict) else {}
        summary_item_exists = bool(summary_item)
        if quality == "low":
            low_rows.append(row_id)
            if summary_item_exists:
                explicit_low_rows.append(row_id)
            else:
                missing_summary_rows.append(row_id)

        signal_values = [
            row.get("focusLabel", ""),
            *(row.get("highlightKeywords", []) or []),
            *flatten_structured_signals(row.get("structuredSignals", {})),
        ]
        signal_terms = {canonical_text(value) for value in signal_values if clean_text(value)}
        if signal_terms & signal_leak_keys:
            signal_leak_rows.append(row_id)

        display_values = [
            row.get("summary", ""),
            row.get("detailBody", ""),
            *(row.get("previewLines", []) or []),
            *(row.get("tasks", []) or []),
            *(row.get("requirements", []) or []),
            *(row.get("preferred", []) or []),
        ]
        display_terms = {canonical_text(value) for value in display_values if clean_text(value)}
        if display_terms & display_leak_keys:
            display_leak_rows.append(row_id)

        row_role = normalized_allowed_role(row.get("roleGroup", ""))
        classifier_role = normalized_allowed_role(row.get("roleClassifierRole", ""))
        classifier_confidence = clean_text(row.get("roleClassifierConfidence", "")).lower()
        override = role_override_items.get(row_id, {}) if isinstance(role_override_items, dict) else {}
        override_role = normalized_allowed_role((override or {}).get("roleGroup", ""))
        override_signature = clean_text((override or {}).get("signature", ""))
        computed_signature = ""
        if row_id in jobs_by_id:
            try:
                from ai_runtime import compute_role_group_signature  # local import to keep startup light

                computed_signature = compute_role_group_signature(jobs_by_id[row_id], summary_items.get(row_id, {}))
            except Exception:
                computed_signature = ""
        override_is_stale = bool(override_role and override_signature and computed_signature and override_signature != computed_signature)

        if not classifier_role:
            if override_is_stale:
                role_stale_rows.append(row_id)
            else:
                role_missing_rows.append(row_id)
        elif row_role and classifier_role != row_role:
            if classifier_confidence == "low":
                role_low_conflict_rows.append(row_id)
            else:
                role_conflict_rows.append(row_id)

        if signal_role_leakage_enabled():
            cluster_roles = []
            cluster_role_values = (((row.get("clusterSignalFacets") or {}).get("role")) or [])
            for value in cluster_role_values if isinstance(cluster_role_values, list) else []:
                cleaned = normalized_allowed_role(value)
                if cleaned and cleaned not in cluster_roles:
                    cluster_roles.append(cleaned)
            foreign_roles = [value for value in cluster_roles if value != row_role]
            if row_role and foreign_roles:
                mixed_role_rows.append(row_id)

    release_metrics = load_release_metrics()
    core_review = load_json(EVAL_SET_PATH, {"items": []}) or {"items": []}
    incremental_review = load_json(INCREMENTAL_EVAL_SET_PATH, {"items": []}) or {"items": []}
    core_reviewed_items = reviewed_items(core_review.get("items", []))
    incremental_reviewed_items = reviewed_items(incremental_review.get("items", []))

    role_wave = load_json(ROLE_REMEDIATION_PATH, {"items": []}) or {"items": []}
    release_wave = load_json(RELEASE_REMEDIATION_PATH, {"items": []}) or {"items": []}
    structured_signal_score = load_json(STRUCTURED_SIGNAL_SCORE_PATH, {}) or {}
    harness = load_json(FULL_DATASET_HARNESS_JSON_PATH, {}) or {}
    harness_metrics = harness.get("metrics", {}) if isinstance(harness.get("metrics", {}), dict) else {}
    harness_families = harness.get("families", {}) if isinstance(harness.get("families", {}), dict) else {}

    role_wave_items = role_wave.get("items", []) if isinstance(role_wave.get("items", []), list) else []
    release_wave_items = release_wave.get("items", []) if isinstance(release_wave.get("items", []), list) else []

    metrics = {
        "generatedAt": now_iso(),
        "jobs": total_jobs,
        "boardRows": total_rows,
        "sourceJobs": int(harness_metrics.get("sourceJobs", total_jobs) or total_jobs),
        "displayJobs": int(harness_metrics.get("displayJobs", total_rows) or total_rows),
        "excludedJobs": int(harness_metrics.get("excludedJobs", 0) or 0),
        "reviewJobs": int(harness_metrics.get("reviewJobs", 0) or 0),
        "sourceRetentionRate": round((total_rows / total_jobs), 6) if total_jobs else 0.0,
        "filteredOutRate": round((len(excluded_diagnostic_rows) / total_jobs), 6) if total_jobs else 0.0,
        "excludedHighQualityRows": len(excluded_high_quality_rows),
        "excludedMediumOrHighQualityRows": len(excluded_medium_or_high_quality_rows),
        "excludedAiAdjacentRows": len(excluded_ai_adjacent_rows),
        "highConfidenceExcludedRows": len(high_confidence_excluded_rows),
        "guardRecoveredRows": len(guard_recovered_rows),
        "guardRecoveredHighQualityRows": len(guard_recovered_high_quality_rows),
        "boardLowRows": len(low_rows),
        "boardLowRate": round((len(low_rows) / total_rows), 6) if total_rows else 0.0,
        "boardMissingSummaryRows": len(missing_summary_rows),
        "boardExplicitLowRows": len(explicit_low_rows),
        "signalMetaLeakRows": len(signal_leak_rows),
        "displayMetaLeakRows": len(display_leak_rows),
        "mixedClusterRoleLeakRows": len(mixed_role_rows),
        "excludedLeakedIntoDisplayRows": int(((harness_families.get("excluded_leaked_into_display") or {}).get("count")) or 0),
        "deeptechInDataAnalystRows": int(((harness_families.get("deeptech_in_data_analyst") or {}).get("count")) or 0),
        "businessInEngineerFamilyRows": int(((harness_families.get("business_in_engineer_family") or {}).get("count")) or 0),
        "toolFirstFocusRows": int(((harness_families.get("tool_first_focus") or {}).get("count")) or 0),
        "roleConflictRows": len(role_conflict_rows),
        "roleLowConfidenceConflictRows": len(role_low_conflict_rows),
        "roleMissingClassifierRows": len(role_missing_rows),
        "roleStaleClassifierRows": len(role_stale_rows),
        "serviceScopeStaleRows": int(harness_metrics.get("staleServiceScopeOverrides", 0) or 0),
        "coreReviewed": len(core_reviewed_items),
        "incrementalReviewed": len(incremental_reviewed_items),
        "releaseCoreFocusExact": release_metrics["core"]["focusExactRate"],
        "releaseCoreKeywordF1": release_metrics["core"]["avgKeywordF1"],
        "releaseIncrementalUsable": release_metrics["incremental"]["usableItemRate"],
        "releaseIncrementalLowRate": release_metrics["incremental"]["lowRate"],
        "releaseIncrementalBannedKeywordRate": release_metrics["incremental"]["keywordBannedRate"],
        "releasePromptProfile": release_metrics["promptProfile"],
        "releaseModel": release_metrics["model"],
        "roleSeedLeakageEnabled": signal_role_leakage_enabled(),
        "roleRemediationItems": len(role_wave_items),
        "roleRemediationCritical": sum(1 for item in role_wave_items if clean_text(item.get("priority", "")).lower() == "critical"),
        "releaseRemediationItems": len(release_wave_items),
        "structuredSignalStrictCurrent": float(((structured_signal_score.get("current") or {}).get("strictRate")) or 0.0),
        "structuredSignalStrictSuggested": float(((structured_signal_score.get("suggested") or {}).get("strictRate")) or 0.0),
        "samples": {
            "boardLowRows": low_rows[:10],
            "boardMissingSummaryRows": missing_summary_rows[:10],
            "boardExplicitLowRows": explicit_low_rows[:10],
            "signalMetaLeakRows": signal_leak_rows[:10],
            "displayMetaLeakRows": display_leak_rows[:10],
            "mixedClusterRoleLeakRows": mixed_role_rows[:10],
            "roleConflictRows": role_conflict_rows[:10],
            "roleLowConfidenceConflictRows": role_low_conflict_rows[:10],
            "roleMissingClassifierRows": role_missing_rows[:10],
            "roleStaleClassifierRows": role_stale_rows[:10],
            "deeptechInDataAnalystRows": ((harness_families.get("deeptech_in_data_analyst") or {}).get("examples") or [])[:10],
            "businessInEngineerFamilyRows": ((harness_families.get("business_in_engineer_family") or {}).get("examples") or [])[:10],
            "toolFirstFocusRows": ((harness_families.get("tool_first_focus") or {}).get("examples") or [])[:10],
            "excludedHighQualityRows": excluded_high_quality_rows[:10],
            "excludedAiAdjacentRows": excluded_ai_adjacent_rows[:10],
            "highConfidenceExcludedRows": high_confidence_excluded_rows[:10],
            "guardRecoveredRows": [
                {
                    "id": row.get("id", ""),
                    "company": row.get("company", ""),
                    "title": row.get("title", ""),
                    "roleGroup": row.get("roleGroup", ""),
                    "focusLabel": row.get("focusLabel", ""),
                    "reason": row.get("serviceScopeReason", ""),
                    "summaryQuality": row.get("summaryQuality", ""),
                }
                for row in guard_recovered_rows[:10]
            ],
        },
    }
    optimization_score, target_status = compute_optimization_score(metrics, loop_config)
    metrics["optimizationScore"] = optimization_score
    metrics["targetStatus"] = target_status
    return metrics


def model_action_ready(model_config: dict) -> bool:
    return bool(model_config.get("baseUrl")) and bool(model_config.get("model")) and bool(model_config.get("apiKey"))


def load_role_wave_job_ids(limit: int = 24) -> list[str]:
    payload = load_json(ROLE_REMEDIATION_PATH, {"items": []}) or {"items": []}
    items = payload.get("items", []) if isinstance(payload.get("items", []), list) else []
    ranked = sorted(
        [item for item in items if clean_text(item.get("id", ""))],
        key=lambda item: (
            PRIORITY_RANK.get(clean_text(item.get("priority", "")).lower(), 9),
            clean_text(item.get("bucket", "")),
            clean_text(item.get("company", "")),
            clean_text(item.get("title", "")),
        ),
    )
    job_ids = []
    seen = set()
    for item in ranked:
        job_id = clean_text(item.get("id", ""))
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)
        job_ids.append(job_id)
        if len(job_ids) >= limit:
            break
    return job_ids


def build_next_actions(metrics: dict, loop_config: dict, model_config: dict) -> list[dict]:
    actions = []
    ready_for_model = model_action_ready(model_config)
    optional_gate = loop_config.get("optionalReleaseGate", {})

    if metrics.get("boardMissingSummaryRows", 0) > loop_config.get("targets", {}).get("boardMissingSummaryRowsMax", 0):
        actions.append(
            {
                "id": "backfill_missing_summaries",
                "kind": "auto_model" if ready_for_model else "manual_model",
                "ready": ready_for_model,
                "priority": "critical",
                "title": "missing summary backfill",
                "reason": "현재 low 보드 행의 큰 비중이 모델 품질이 아니라 summary 미생성 상태입니다.",
            }
        )

    if metrics.get("mixedClusterRoleLeakRows", 0) > loop_config.get("targets", {}).get("mixedClusterRoleLeakRowsMax", 0):
        actions.append(
            {
                "id": "seal_role_seed_leakage",
                "kind": "manual_code",
                "ready": False,
                "priority": "critical",
                "title": "섹션 군집 seed 에서 role 누수 제거",
                "reason": "role 신호가 카드 라벨을 다시 만들며 직군 오염을 증폭합니다.",
            }
        )

    if metrics.get("signalMetaLeakRows", 0) > loop_config.get("targets", {}).get("signalMetaLeakRowsMax", 0):
        actions.append(
            {
                "id": "refresh_low_or_missing_summaries",
                "kind": "auto_model" if ready_for_model else "manual_model",
                "ready": ready_for_model,
                "priority": "critical",
                "title": "low/missing 요약 재생성",
                "reason": "meta 표현이 signal 경로에 남아 있어 current champion 으로 low/missing row 를 다시 읽어야 합니다.",
            }
        )

    if metrics.get("roleStaleClassifierRows", 0) > loop_config.get("targets", {}).get("roleStaleClassifierRowsMax", 0):
        actions.append(
            {
                "id": "rerun_stale_role_signatures",
                "kind": "auto_model" if ready_for_model else "manual_model",
                "ready": ready_for_model,
                "priority": "critical",
                "title": "stale role signature 재판정",
                "reason": "요약 재생성 뒤 role override signature 가 stale 해져 보드가 최신 분류를 읽지 못합니다.",
            }
        )

    if (
        metrics.get("roleConflictRows", 0) > loop_config.get("targets", {}).get("roleConflictRowsMax", 0)
        or metrics.get("roleMissingClassifierRows", 0)
        > loop_config.get("targets", {}).get("roleMissingClassifierRowsMax", 0)
    ):
        actions.append(
            {
                "id": "rerun_role_group_wave",
                "kind": "auto_model" if ready_for_model else "manual_model",
                "ready": ready_for_model,
                "priority": "high",
                "title": "role remediation wave 재판정",
                "reason": "전용 role 분류기 충돌 또는 비어 있는 출력이 남아 있습니다.",
            }
        )

    release_failures = []
    for metric_name, status in metrics.get("targetStatus", {}).items():
        if metric_name.startswith("release") and not status.get("passed"):
            release_failures.append(metric_name)
    if release_failures:
        actions.append(
            {
                "id": "run_candidate_release_gate",
                "kind": "auto_benchmark" if (ready_for_model and optional_gate.get("enabled")) else "manual_benchmark",
                "ready": bool(ready_for_model and optional_gate.get("enabled")),
                "priority": "high",
                "title": "candidate prompt release gate 재실행",
                "reason": f"release gate 관련 지표 {', '.join(release_failures)} 가 목표 미달입니다.",
            }
        )

    if metrics.get("excludedAiAdjacentRows", 0) > loop_config.get("targets", {}).get("excludedAiAdjacentRowsMax", 0):
        actions.append(
            {
                "id": "audit_ai_adjacent_scope_exclusions",
                "kind": "manual_review",
                "ready": False,
                "priority": "critical",
                "title": "AI/data 인접 제외 row 검수",
                "reason": "scope gate 가 AI/data 인접 신호를 가진 공고를 제외해 false negative 위험이 큽니다.",
            }
        )

    if metrics.get("businessInEngineerFamilyRows", 0) > loop_config.get("targets", {}).get("businessInEngineerFamilyRowsMax", 0):
        actions.append(
            {
                "id": "remediate_business_focus_dominance",
                "kind": "manual_model",
                "ready": False,
                "priority": "high",
                "title": "business focus dominance 보정",
                "reason": "엔지니어/리서처 공고의 focus 가 제품 성장 분석 같은 비즈니스 축으로 과잉 수렴합니다.",
            }
        )

    if metrics.get("guardRecoveredRows", 0) > 0:
        actions.append(
            {
                "id": "convert_guard_recovery_to_goldset",
                "kind": "manual_review",
                "ready": False,
                "priority": "high",
                "title": "guard 복구 row 를 service scope goldset 으로 전환",
                "reason": "현재 통과는 모델 판단 자체가 아니라 guard 가 복구한 row 에 의존하므로 최종 모델 개선 확인에는 별도 검수가 필요합니다.",
            }
        )

    if metrics.get("coreReviewed", 0) < 30 or metrics.get("incrementalReviewed", 0) < 10:
        actions.append(
            {
                "id": "expand_review_goldset",
                "kind": "manual_review",
                "ready": False,
                "priority": "medium",
                "title": "검수 골드셋 확장",
                "reason": "평가셋 검수 커버리지가 낮아 모델 품질 판단의 신뢰도가 떨어집니다.",
            }
        )

    priority_sort = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    actions.sort(key=lambda action: (priority_sort.get(action["priority"], 9), action["kind"], action["id"]))
    return actions


def execute_action(action: dict, loop_config: dict, model_config: dict) -> dict:
    base_url = model_config.get("baseUrl", "")
    model = model_config.get("model", "")
    api_key = model_config.get("apiKey", "")
    batch_size = str(loop_config.get("optionalReleaseGate", {}).get("batchSize", 4) or 4)

    executed = {
        "id": action["id"],
        "kind": action["kind"],
        "startedAt": now_iso(),
        "status": "completed",
        "details": "",
    }

    if action["id"] in {"backfill_missing_summaries", "refresh_low_or_missing_summaries"}:
        prompt_profile = load_release_metrics().get("promptProfile") or "field_aware_v3"
        args = [
            "--base-url",
            base_url,
            "--model",
            model,
            "--api-key",
            api_key,
            "--batch-size",
            batch_size,
            "--mode",
            "missing",
            "--prompt-profile",
            prompt_profile,
        ]
        run_script(ROOT / "scripts" / "generate_job_summaries.py", args)
        executed["details"] = (
            f"generate_job_summaries.py mode=missing promptProfile={prompt_profile}"
        )
    elif action["id"] == "rerun_stale_role_signatures":
        args = [
            "--base-url",
            base_url,
            "--model",
            model,
            "--api-key",
            api_key,
            "--batch-size",
            batch_size,
            "--mode",
            "stale",
        ]
        run_script(ROOT / "scripts" / "classify_role_groups.py", args)
        run_script(ROOT / "scripts" / "build_summary_board.py")
        executed["details"] = "classify_role_groups.py mode=stale"
    elif action["id"] == "rerun_role_group_wave":
        job_ids = load_role_wave_job_ids()
        if not job_ids:
            executed["status"] = "skipped"
            executed["details"] = "role remediation wave 에 재판정할 job id 가 없어서 건너뜀"
            return executed
        args = [
            "--base-url",
            base_url,
            "--model",
            model,
            "--api-key",
            api_key,
            "--batch-size",
            batch_size,
            "--mode",
            "all",
            "--job-ids",
            ",".join(job_ids),
        ]
        run_script(ROOT / "scripts" / "classify_role_groups.py", args)
        run_script(ROOT / "scripts" / "build_summary_board.py")
        executed["details"] = f"classify_role_groups.py jobIds={len(job_ids)}"
    elif action["id"] == "run_candidate_release_gate":
        optional_gate = loop_config.get("optionalReleaseGate", {})
        experiment_id = f"quality_loop_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        args = [
            "--base-url",
            base_url,
            "--model",
            model,
            "--api-key",
            api_key,
            "--prompt-profile",
            str(optional_gate.get("candidateProfile", "field_aware_v9")),
            "--compare-to",
            str(optional_gate.get("compareTo", load_release_metrics().get("promptProfile") or "field_aware_v3")),
            "--batch-size",
            str(optional_gate.get("batchSize", 4) or 4),
            "--experiment-id",
            experiment_id,
        ]
        if optional_gate.get("autoApplyChampion"):
            args.append("--apply")
        run_script(ROOT / "scripts" / "run_release_gate.py", args)
        executed["details"] = f"run_release_gate.py experimentId={experiment_id}"
    else:
        executed["status"] = "skipped"
        executed["details"] = "지원하지 않는 액션"

    executed["completedAt"] = now_iso()
    return executed


def build_iteration_markdown(iteration_payload: dict) -> str:
    metrics = iteration_payload["metrics"]
    target_status = metrics.get("targetStatus", {})
    lines = [
        f"# Quality Iteration {iteration_payload['iteration']:03d}",
        "",
        f"- 상태: `{iteration_payload['status']}`",
        f"- 생성 시각: `{iteration_payload['generatedAt']}`",
        f"- optimization score: `{metrics.get('optimizationScore', 0)}`",
        f"- release champion: `{metrics.get('releaseModel', '')} / {metrics.get('releasePromptProfile', '')}`",
        "",
        "## 핵심 지표",
        "",
        f"- boardLowRate: `{metrics.get('boardLowRate', 0)}`",
        f"- boardMissingSummaryRows: `{metrics.get('boardMissingSummaryRows', 0)}`",
        f"- boardExplicitLowRows: `{metrics.get('boardExplicitLowRows', 0)}`",
        f"- sourceRetentionRate: `{metrics.get('sourceRetentionRate', 0)}`",
        f"- filteredOutRate: `{metrics.get('filteredOutRate', 0)}`",
        f"- excludedHighQualityRows: `{metrics.get('excludedHighQualityRows', 0)}`",
        f"- excludedAiAdjacentRows: `{metrics.get('excludedAiAdjacentRows', 0)}`",
        f"- highConfidenceExcludedRows: `{metrics.get('highConfidenceExcludedRows', 0)}`",
        f"- guardRecoveredRows: `{metrics.get('guardRecoveredRows', 0)}`",
        f"- guardRecoveredHighQualityRows: `{metrics.get('guardRecoveredHighQualityRows', 0)}`",
        f"- signalMetaLeakRows: `{metrics.get('signalMetaLeakRows', 0)}`",
        f"- mixedClusterRoleLeakRows: `{metrics.get('mixedClusterRoleLeakRows', 0)}`",
        f"- roleConflictRows: `{metrics.get('roleConflictRows', 0)}`",
        f"- roleLowConfidenceConflictRows: `{metrics.get('roleLowConfidenceConflictRows', 0)}`",
        f"- roleMissingClassifierRows: `{metrics.get('roleMissingClassifierRows', 0)}`",
        f"- roleStaleClassifierRows: `{metrics.get('roleStaleClassifierRows', 0)}`",
        f"- releaseCoreFocusExact: `{metrics.get('releaseCoreFocusExact', 0)}`",
        f"- releaseCoreKeywordF1: `{metrics.get('releaseCoreKeywordF1', 0)}`",
        f"- releaseIncrementalUsable: `{metrics.get('releaseIncrementalUsable', 0)}`",
        f"- releaseIncrementalLowRate: `{metrics.get('releaseIncrementalLowRate', 0)}`",
        f"- releaseIncrementalBannedKeywordRate: `{metrics.get('releaseIncrementalBannedKeywordRate', 0)}`",
        "",
        "## Target Checks",
        "",
    ]
    for metric_name, status in target_status.items():
        lines.append(
            f"- `{metric_name}`: "
            f"`actual={status['actual']}` / `target={status['target']}` / "
            f"`{status['comparator']}` / `pass={status['passed']}`"
        )

    lines.extend(["", "## 샘플", ""])
    for sample_name, sample_values in metrics.get("samples", {}).items():
        rendered_values = []
        for value in sample_values[:10] if isinstance(sample_values, list) else []:
            if isinstance(value, dict):
                rendered_values.append(
                    " | ".join(
                        clean_text(value.get(key, ""))
                        for key in ("company", "title", "roleGroup", "focusLabel", "reason")
                        if clean_text(value.get(key, ""))
                    )
                )
            else:
                rendered_values.append(clean_text(value))
        lines.append(f"- `{sample_name}`: `{', '.join(rendered_values) if rendered_values else '없음'}`")

    if iteration_payload.get("artifactErrors"):
        lines.extend(["", "## Artifact Errors", ""])
        for error in iteration_payload["artifactErrors"]:
            lines.append(f"- {error}")

    executed_action = iteration_payload.get("executedAction")
    if executed_action:
        lines.extend(["", "## Executed Action", ""])
        lines.append(f"- `{executed_action['id']}` / `{executed_action['status']}`")
        if executed_action.get("details"):
            lines.append(f"- {executed_action['details']}")

    lines.extend(["", "## Next Actions", ""])
    next_actions = iteration_payload.get("nextActions", [])
    if not next_actions:
        lines.append("- 없음")
    else:
        for action in next_actions:
            lines.append(
                f"- `{action['priority']}` `{action['kind']}` `{action['id']}`: "
                f"{action['title']} ({action['reason']})"
            )
    return "\n".join(lines) + "\n"


def next_iteration_index() -> int:
    ITERATION_JSON_DIR.mkdir(parents=True, exist_ok=True)
    existing = sorted(ITERATION_JSON_DIR.glob("iteration_*.json"))
    if not existing:
        return 1
    latest = max(int(path.stem.split("_")[-1]) for path in existing if path.stem.split("_")[-1].isdigit())
    return latest + 1


def write_iteration(iteration_index: int, payload: dict) -> tuple[Path, Path]:
    json_path = ITERATION_JSON_DIR / f"iteration_{iteration_index:03d}.json"
    md_path = ITERATION_MD_DIR / f"iteration_{iteration_index:03d}.md"
    write_json(json_path, payload)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text(build_iteration_markdown(payload), encoding="utf-8")
    return json_path, md_path


def load_model_config(args: argparse.Namespace) -> dict:
    release = load_release_metrics()
    base_url = args.base_url or release.get("baseUrl", "") or os.environ.get("COMPANY_INSIGHT_BASE_URL", "")
    model = args.model or release.get("model", "") or os.environ.get("COMPANY_INSIGHT_MODEL", "")
    api_key = args.api_key or os.environ.get("COMPANY_INSIGHT_API_KEY", "")
    return {
        "baseUrl": clean_text(base_url),
        "model": clean_text(model),
        "apiKey": clean_text(api_key),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(CONFIG_PATH))
    parser.add_argument("--base-url", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--candidate-profile", default="")
    parser.add_argument("--compare-to", default="")
    parser.add_argument("--max-iterations", type=int, default=0)
    args = parser.parse_args()

    loop_config = load_json(Path(args.config), {}) or {}
    if args.max_iterations > 0:
        loop_config["maxIterations"] = args.max_iterations
    if args.candidate_profile:
        loop_config.setdefault("optionalReleaseGate", {})["candidateProfile"] = args.candidate_profile
    if args.compare_to:
        loop_config.setdefault("optionalReleaseGate", {})["compareTo"] = args.compare_to

    model_config = load_model_config(args)
    max_iterations = int(loop_config.get("maxIterations", 3) or 3)
    plateau_delta = float(((loop_config.get("plateauPolicy") or {}).get("minScoreDelta")) or 0.25)
    plateau_patience = int(((loop_config.get("plateauPolicy") or {}).get("patienceIterations")) or 1)

    iteration_index = next_iteration_index()
    previous_score = None
    plateau_hits = 0
    attempted_actions = Counter()
    final_payload = None

    for offset in range(max_iterations):
        current_index = iteration_index + offset
        artifacts, artifact_errors = refresh_artifacts(loop_config, model_config)
        metrics = build_metrics(loop_config, artifacts)
        next_actions = build_next_actions(metrics, loop_config, model_config)

        status = "measured"
        executed_action = None

        if all(status_item.get("passed") for status_item in metrics.get("targetStatus", {}).values()):
            status = "converged"
        else:
            auto_actions = [action for action in next_actions if action["kind"].startswith("auto") and action["ready"]]
            fresh_auto_actions = [action for action in auto_actions if attempted_actions[action["id"]] == 0]
            if previous_score is not None and abs(metrics["optimizationScore"] - previous_score) < plateau_delta:
                plateau_hits += 1
            else:
                plateau_hits = 0

            if plateau_hits > plateau_patience and not fresh_auto_actions:
                status = "plateaued"
            elif offset == max_iterations - 1:
                status = "iteration_limit_reached"
            elif not auto_actions:
                status = "manual_intervention_required"
            else:
                action = fresh_auto_actions[0] if fresh_auto_actions else auto_actions[0]
                try:
                    executed_action = execute_action(action, loop_config, model_config)
                    attempted_actions[action["id"]] += 1
                    status = "action_applied"
                except Exception as error:
                    executed_action = {
                        "id": action["id"],
                        "kind": action["kind"],
                        "status": "failed",
                        "details": str(error),
                        "completedAt": now_iso(),
                    }
                    attempted_actions[action["id"]] += 1
                    status = "action_failed"

        payload = {
            "iteration": current_index,
            "generatedAt": now_iso(),
            "status": status,
            "configPath": str(Path(args.config)),
            "modelConfig": {
                "baseUrl": model_config.get("baseUrl", ""),
                "model": model_config.get("model", ""),
                "apiKeyPresent": bool(model_config.get("apiKey")),
            },
            "artifacts": artifacts,
            "artifactErrors": artifact_errors,
            "metrics": metrics,
            "nextActions": next_actions,
            "executedAction": executed_action,
        }
        json_path, md_path = write_iteration(current_index, payload)
        payload["jsonPath"] = str(json_path)
        payload["markdownPath"] = str(md_path)
        final_payload = payload
        write_json(LATEST_STATE_PATH, payload)

        previous_score = metrics["optimizationScore"]

        if status in {
            "converged",
            "manual_intervention_required",
            "plateaued",
            "iteration_limit_reached",
            "action_failed",
        }:
            break

    if not final_payload:
        raise RuntimeError("No iteration payload was produced.")

    print(
        json.dumps(
            {
                "status": final_payload["status"],
                "iteration": final_payload["iteration"],
                "optimizationScore": final_payload["metrics"]["optimizationScore"],
                "jsonPath": final_payload["jsonPath"],
                "markdownPath": final_payload["markdownPath"],
                "latestStatePath": str(LATEST_STATE_PATH),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
