#!/usr/bin/env python3

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SUMMARY_BOARD_PATH = ROOT / "data" / "summary_board.json"
LATEST_STATE_PATH = ROOT / "data" / "quality_iterations" / "latest_state.json"
HARNESS_PATH = ROOT / "data" / "full_dataset_harness_latest.json"
PACKAGE_JSON_PATH = ROOT / "data" / "final_confirmation_package_001.json"
PACKAGE_MD_PATH = ROOT / "docs" / "final_confirmation_package_001.md"
GUARD_JSON_PATH = ROOT / "data" / "service_scope_guard_recovery_candidates_001.json"
GUARD_CSV_PATH = ROOT / "data" / "service_scope_guard_recovery_candidates_001.csv"
GUARD_MD_PATH = ROOT / "docs" / "service_scope_guard_recovery_candidates_001.md"
GOLDSET_JSON_PATH = ROOT / "data" / "service_scope_goldset_001.json"
GOLDSET_MD_PATH = ROOT / "docs" / "service_scope_goldset_001.md"
BENCHMARK_JSON_PATH = ROOT / "data" / "service_scope_model_benchmark_001.json"
BENCHMARK_MD_PATH = ROOT / "docs" / "service_scope_model_benchmark_001.md"
SHADOW_JSON_PATH = ROOT / "data" / "service_scope_shadow_guard_off_001.json"
SHADOW_MD_PATH = ROOT / "docs" / "service_scope_shadow_guard_off_001.md"
MODEL_GATE_JSON_PATH = ROOT / "data" / "model_improvement_gate_latest.json"
MODEL_GATE_MD_PATH = ROOT / "docs" / "model_improvement_gate_latest.md"
ADJUDICATION_JSON_PATH = ROOT / "data" / "service_scope_adjudication_pack_001.json"
ADJUDICATION_CSV_PATH = ROOT / "data" / "service_scope_adjudication_pack_001.csv"
ADJUDICATION_MD_PATH = ROOT / "docs" / "service_scope_adjudication_pack_001.md"
PROPOSED_GOLDSET_JSON_PATH = ROOT / "data" / "service_scope_goldset_proposed_v2.json"
PROPOSED_GOLDSET_MD_PATH = ROOT / "docs" / "service_scope_goldset_proposed_v2.md"
PROPOSED_BENCHMARK_JSON_PATH = ROOT / "data" / "service_scope_model_benchmark_proposed_v2.json"
PROPOSED_BENCHMARK_MD_PATH = ROOT / "docs" / "service_scope_model_benchmark_proposed_v2.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def load_json(path: Path, default):
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


def row_summary(row: dict) -> dict:
    return {
        "id": clean_text(row.get("id", "")),
        "company": clean_text(row.get("company", "")),
        "title": clean_text(row.get("title", "")),
        "rawRole": clean_text(row.get("rawRole", "")),
        "roleGroup": clean_text(row.get("roleGroup", "")),
        "summaryQuality": clean_text(row.get("summaryQuality", "")),
        "focusLabel": clean_text(row.get("focusLabel", "")),
        "keywords": [clean_text(value) for value in row.get("highlightKeywords", []) if clean_text(value)],
        "serviceScopeModelAction": clean_text(row.get("serviceScopeAction", "")),
        "serviceScopeResolvedAction": clean_text(row.get("serviceScopeResolvedAction", "")),
        "serviceScopeReason": clean_text(row.get("serviceScopeReason", "")),
        "serviceScopeConfidence": clean_text(row.get("serviceScopeConfidence", "")),
        "summary": clean_text(row.get("summary", "")),
        "jobUrl": clean_text(row.get("jobUrl", "")),
    }


def build_guard_candidates(rows: list[dict]) -> list[dict]:
    candidates = []
    for row in rows:
        if clean_text(row.get("serviceScopeAction", "")).lower() != "exclude":
            continue
        if clean_text(row.get("serviceScopeResolvedAction", "")).lower() != "include":
            continue
        item = row_summary(row)
        item.update(
            {
                "reviewTarget": "service_scope_guard_recovery",
                "recommendedReview": "confirm_include_or_reclassify_review",
                "confirmServiceScope": "",
                "confirmRoleGroup": "",
                "confirmFocusLabel": "",
                "reviewerNotes": "",
            }
        )
        candidates.append(item)
    candidates.sort(
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(item["summaryQuality"], 9),
            item["company"],
            item["title"],
        )
    )
    return candidates


def write_guard_csv(candidates: list[dict]) -> None:
    GUARD_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "company",
        "title",
        "rawRole",
        "roleGroup",
        "summaryQuality",
        "focusLabel",
        "keywords",
        "serviceScopeModelAction",
        "serviceScopeResolvedAction",
        "serviceScopeReason",
        "serviceScopeConfidence",
        "summary",
        "jobUrl",
        "recommendedReview",
        "confirmServiceScope",
        "confirmRoleGroup",
        "confirmFocusLabel",
        "reviewerNotes",
    ]
    with GUARD_CSV_PATH.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for item in candidates:
            writer.writerow({**item, "keywords": ", ".join(item.get("keywords", []))})


def render_guard_md(candidates: list[dict]) -> str:
    lines = [
        "# Service Scope Guard Recovery Candidates 001",
        "",
        f"- generatedAt: `{now_iso()}`",
        f"- candidates: `{len(candidates)}`",
        "",
        "이 목록은 모델이 `exclude`로 저장했지만 runtime guard가 `include`로 복구한 row입니다.",
        "최종 모델 개선으로 인정하려면 각 row를 `include / review / exclude`로 검수한 뒤 service scope goldset에 반영해야 합니다.",
        "",
        "| # | company | title | quality | focus | model reason | confirm |",
        "|---:|---|---|---|---|---|---|",
    ]
    for index, item in enumerate(candidates, start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    md_cell(item["company"]),
                    md_cell(item["title"]),
                    md_cell(item["summaryQuality"]),
                    md_cell(item["focusLabel"]),
                    md_cell(item["serviceScopeReason"]),
                    "",
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_package_md(package: dict) -> str:
    metrics = package["metrics"]
    guard = package["guardRecovery"]
    execution = package.get("modelImprovementExecution", {})
    model_improvement_complete = package["status"]["modelImprovement"] == "complete_guard_independent"
    if model_improvement_complete:
        judgment_lines = [
            "- 운영 안정화 버전으로 컴펌 가능합니다.",
            "- 모델 개선 gate도 통과했습니다.",
            "- guard 의존도 없이 service scope 판정 기준을 통과한 상태입니다.",
        ]
    else:
        judgment_lines = [
            "- 운영 안정화 버전으로는 컴펌 가능합니다.",
            "- 모델 개선 완료 버전으로는 컴펌하면 안 됩니다.",
            "- 현재 통과는 guard 기반 안정화이며, guard 복구 row를 평가셋으로 전환해야 모델 개선 검증으로 넘어갈 수 있습니다.",
        ]
    lines = [
        "# Final Confirmation Package 001",
        "",
        f"- version: `{package['version']}`",
        f"- generatedAt: `{package['generatedAt']}`",
        f"- serverUrl: `{package['serverUrl']}`",
        f"- operationalStatus: `{package['status']['operational']}`",
        f"- modelImprovementStatus: `{package['status']['modelImprovement']}`",
        "",
        "## 판정",
        "",
        *judgment_lines,
        "",
        "## 핵심 지표",
        "",
        f"- sourceJobs: `{metrics['sourceJobs']}`",
        f"- boardRows: `{metrics['boardRows']}`",
        f"- excludedJobs: `{metrics['excludedJobs']}`",
        f"- reviewJobs: `{metrics.get('reviewJobs', 0)}`",
        f"- sourceRetentionRate: `{metrics['sourceRetentionRate']}`",
        f"- filteredOutRate: `{metrics['filteredOutRate']}`",
        f"- optimizationScore: `{metrics['optimizationScore']}`",
        f"- excludedHighQualityRows: `{metrics['excludedHighQualityRows']}`",
        f"- excludedAiAdjacentRows: `{metrics['excludedAiAdjacentRows']}`",
        f"- businessInEngineerFamilyRows: `{metrics['businessInEngineerFamilyRows']}`",
        f"- missingSummaryRows: `{metrics['missingSummaryRows']}`",
        "",
        "## Guard 부채",
        "",
        f"- guardRecoveredRows: `{guard['total']}`",
        f"- guardRecoveredHighQualityRows: `{guard['highQuality']}`",
        f"- candidatesJson: `{package['artifacts']['guardCandidatesJson']}`",
        f"- candidatesCsv: `{package['artifacts']['guardCandidatesCsv']}`",
        f"- candidatesMd: `{package['artifacts']['guardCandidatesMd']}`",
        "",
        "## 모델 개선 실행 상태",
        "",
        f"- goldsetStatus: `{execution.get('goldsetStatus', 'missing')}`",
        f"- provisionalGoldsetItems: `{execution.get('provisionalGoldsetItems', 0)}`",
        f"- benchmarkFalseExcludeCount: `{execution.get('benchmarkFalseExcludeCount', 0)}`",
        f"- benchmarkHighQualityFalseExcludeCount: `{execution.get('benchmarkHighQualityFalseExcludeCount', 0)}`",
        f"- shadowGuardRecoveredRows: `{execution.get('shadowGuardRecoveredRows', 0)}`",
        f"- shadowTargetsPassed: `{execution.get('shadowTargetsPassed', False)}`",
        f"- modelBenchmarkPassed: `{execution.get('modelBenchmarkPassed', False)}`",
        f"- modelImprovementEligible: `{execution.get('modelImprovementEligible', False)}`",
        f"- modelImprovementGateStatus: `{execution.get('modelImprovementGateStatus', 'missing')}`",
        f"- modelImprovementGatePassed: `{execution.get('modelImprovementGatePassed', False)}`",
        f"- modelImprovementGateBlockers: `{', '.join(execution.get('modelImprovementGateBlockers', [])) or '-'}`",
        f"- adjudicationItems: `{execution.get('adjudicationItems', 0)}`",
        f"- adjudicationSuggestedDecisions: `{execution.get('adjudicationSuggestedDecisions', {})}`",
        f"- proposedGoldsetDecisions: `{execution.get('proposedGoldsetDecisions', {})}`",
        f"- proposedBenchmarkPassed: `{execution.get('proposedBenchmarkPassed', False)}`",
        f"- proposedBenchmarkFalseExcludeCount: `{execution.get('proposedBenchmarkFalseExcludeCount', 0)}`",
        f"- goldsetJson: `{package['artifacts'].get('serviceScopeGoldsetJson', '')}`",
        f"- benchmarkJson: `{package['artifacts'].get('serviceScopeBenchmarkJson', '')}`",
        f"- shadowJson: `{package['artifacts'].get('serviceScopeShadowGuardOffJson', '')}`",
        f"- modelGateJson: `{package['artifacts'].get('modelImprovementGateJson', '')}`",
        f"- adjudicationCsv: `{package['artifacts'].get('serviceScopeAdjudicationCsv', '')}`",
        f"- proposedBenchmarkJson: `{package['artifacts'].get('serviceScopeProposedBenchmarkJson', '')}`",
        "",
        "## 남은 점검",
        "",
    ]
    for item in package["residualRisks"]:
        lines.append(f"- `{item['severity']}` {item['title']}: {item['detail']}")

    lines.extend(["", "## 컴펌 체크리스트", ""])
    for item in package["confirmationChecklist"]:
        required = "required" if item["required"] else "optional"
        lines.append(f"- [ ] `{required}` {item['title']} - {item['detail']}")

    lines.extend(["", "## 최종 문구", ""])
    if model_improvement_complete:
        lines.append("> 운영 안정화 및 모델 개선 gate 모두 승인 가능.")
    else:
        lines.append("> 운영 안정화 RC는 승인 가능. 모델 개선 완료는 guard recovery goldset 검증 전까지 보류.")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    board = load_json(SUMMARY_BOARD_PATH, {"rows": [], "overview": {}, "diagnostics": {}})
    latest = load_json(LATEST_STATE_PATH, {"metrics": {}, "status": ""})
    harness = load_json(HARNESS_PATH, {"families": {}})
    goldset = load_json(GOLDSET_JSON_PATH, {})
    benchmark = load_json(BENCHMARK_JSON_PATH, {})
    shadow = load_json(SHADOW_JSON_PATH, {})
    model_gate = load_json(MODEL_GATE_JSON_PATH, {})
    adjudication = load_json(ADJUDICATION_JSON_PATH, {})
    proposed_goldset = load_json(PROPOSED_GOLDSET_JSON_PATH, {})
    proposed_benchmark = load_json(PROPOSED_BENCHMARK_JSON_PATH, {})
    model_gate_passed = bool(model_gate.get("passed", False))

    rows = board.get("rows", []) if isinstance(board.get("rows", []), list) else []
    overview = board.get("overview", {}) if isinstance(board.get("overview", {}), dict) else {}
    metrics_state = latest.get("metrics", {}) if isinstance(latest.get("metrics", {}), dict) else {}
    families = harness.get("families", {}) if isinstance(harness.get("families", {}), dict) else {}

    guard_candidates = build_guard_candidates(rows)
    missing_summary_rows = [row_summary(row) for row in rows if not row.get("hasSummary")]
    broad_focus_gap = families.get("broad_focus_specificity_gap", {}) or {}
    deeptech_context = families.get("deeptech_context_present", {}) or {}
    business_context = families.get("business_context_present", {}) or {}

    guard_payload = {
        "generatedAt": now_iso(),
        "source": str(SUMMARY_BOARD_PATH),
        "count": len(guard_candidates),
        "items": guard_candidates,
    }
    write_json(GUARD_JSON_PATH, guard_payload)
    write_guard_csv(guard_candidates)
    write_text(GUARD_MD_PATH, render_guard_md(guard_candidates))

    review_jobs = int(overview.get("serviceScopeReviewCandidates", metrics_state.get("reviewJobs", 0)) or 0)
    residual_risks = []
    if guard_candidates:
        residual_risks.append(
            {
                "severity": "high",
                "title": "guard dependency",
                "detail": f"{len(guard_candidates)}개 row가 모델 판단이 아니라 runtime guard 로 복구되었습니다.",
            }
        )
    else:
        residual_risks.append(
            {
                "severity": "info",
                "title": "guard dependency cleared",
                "detail": "runtime guard 복구 row가 0개입니다.",
            }
        )
    if missing_summary_rows:
        residual_risks.append(
            {
                "severity": "medium",
                "title": "missing summaries",
                "detail": f"{len(missing_summary_rows)}개 표시 row가 summary 없이 low 상태입니다.",
            }
        )
    if int(broad_focus_gap.get("count", 0) or 0):
        residual_risks.append(
            {
                "severity": "medium",
                "title": "broad focus specificity gap",
                "detail": f"{int(broad_focus_gap.get('count', 0) or 0)}개 row에서 더 구체적인 focus 후보가 남아 있습니다.",
            }
        )
    residual_risks.append(
        {
            "severity": "info",
            "title": "context-only families",
            "detail": (
                f"deeptech_context_present={int(deeptech_context.get('count', 0) or 0)}, "
                f"business_context_present={int(business_context.get('count', 0) or 0)}"
            ),
        }
    )

    if model_gate_passed:
        confirmation_checklist = [
            {
                "required": True,
                "title": "운영 및 모델 개선 완료 승인",
                "detail": (
                    f"{len(rows)}개 표시 공고, "
                    f"{int(overview.get('serviceScopeFilteredOutJobs', metrics_state.get('excludedJobs', 0)) or 0)}개 제외 공고, "
                    f"{review_jobs}개 review 공고 구성을 승인합니다."
                ),
            },
            {
                "required": True,
                "title": "confirmed v2 goldset 승인",
                "detail": "service scope confirmed v2 goldset 25개 판정을 모델 개선 기준으로 승인합니다.",
            },
            {
                "required": False,
                "title": f"missing summary {len(missing_summary_rows)}개 보류 승인",
                "detail": "현재 모델 개선 gate와 운영 target에는 영향이 없습니다.",
            },
        ]
    else:
        confirmation_checklist = [
            {
                "required": True,
                "title": "운영 안정화 버전으로 승인",
                "detail": (
                    f"{len(rows)}개 표시 공고와 "
                    f"{int(overview.get('serviceScopeFilteredOutJobs', metrics_state.get('excludedJobs', 0)) or 0)}개 제외 공고 구성을 승인합니다."
                ),
            },
            {
                "required": True,
                "title": "모델 개선 완료 아님을 승인",
                "detail": "guard 복구 또는 goldset blocker 때문에 모델 자체 개선 완료로 기록하지 않습니다.",
            },
            {
                "required": True,
                "title": "guard recovery 검수 착수 승인",
                "detail": "service_scope_guard_recovery_candidates_001 파일을 다음 goldset 입력으로 사용합니다.",
            },
        ]

    package = {
        "version": (
            "final-confirmation-001-model-improvement-complete"
            if model_gate_passed
            else "final-confirmation-001-ops-stabilization-rc"
        ),
        "generatedAt": now_iso(),
        "serverUrl": "http://127.0.0.1:4174/",
        "status": {
            "operational": "ready_for_user_confirmation",
            "modelImprovement": (
                "complete_guard_independent"
                if model_gate_passed
                else "not_complete_guard_debt_exists"
            ),
        },
        "metrics": {
            "sourceJobs": int(overview.get("sourceJobs", metrics_state.get("jobs", 0)) or 0),
            "boardRows": int(len(rows)),
            "excludedJobs": int(overview.get("serviceScopeFilteredOutJobs", metrics_state.get("excludedJobs", 0)) or 0),
            "reviewJobs": review_jobs,
            "sourceRetentionRate": metrics_state.get("sourceRetentionRate", 0),
            "filteredOutRate": metrics_state.get("filteredOutRate", 0),
            "optimizationScore": metrics_state.get("optimizationScore", 0),
            "excludedHighQualityRows": int(metrics_state.get("excludedHighQualityRows", 0) or 0),
            "excludedAiAdjacentRows": int(metrics_state.get("excludedAiAdjacentRows", 0) or 0),
            "businessInEngineerFamilyRows": int(metrics_state.get("businessInEngineerFamilyRows", 0) or 0),
            "missingSummaryRows": len(missing_summary_rows),
        },
        "guardRecovery": {
            "total": len(guard_candidates),
            "highQuality": sum(1 for item in guard_candidates if item.get("summaryQuality") == "high"),
            "mediumQuality": sum(1 for item in guard_candidates if item.get("summaryQuality") == "medium"),
            "lowQuality": sum(1 for item in guard_candidates if item.get("summaryQuality") == "low"),
        },
        "modelImprovementExecution": {
            "goldsetStatus": clean_text(goldset.get("status", "")) or "missing",
            "provisionalGoldsetItems": int(((goldset.get("counts") or {}).get("provisionalItems")) or 0),
            "confirmedGoldsetItems": int(((goldset.get("counts") or {}).get("confirmedItems")) or 0),
            "benchmarkFalseExcludeCount": int(((benchmark.get("metrics") or {}).get("falseExcludeCount")) or 0),
            "benchmarkHighQualityFalseExcludeCount": int(
                ((benchmark.get("metrics") or {}).get("highQualityFalseExcludeCount")) or 0
            ),
            "modelBenchmarkPassed": bool(benchmark.get("modelPassedBenchmark", False)),
            "modelImprovementEligible": bool(benchmark.get("modelImprovementEligible", False)),
            "shadowGuardRecoveredRows": int(((shadow.get("metrics") or {}).get("shadowGuardRecoveredRows")) or 0),
            "shadowGuardRecoveredHighQualityRows": int(
                ((shadow.get("metrics") or {}).get("shadowGuardRecoveredHighQualityRows")) or 0
            ),
            "shadowExcludedAiAdjacentRows": int(
                ((shadow.get("metrics") or {}).get("shadowExcludedAiAdjacentRows")) or 0
            ),
            "shadowTargetsPassed": bool(shadow.get("targetsPassed", False)),
            "modelImprovementGateStatus": clean_text(model_gate.get("status", "")) or "missing",
            "modelImprovementGatePassed": bool(model_gate.get("passed", False)),
            "modelImprovementGateBlockers": [
                clean_text(item)
                for item in model_gate.get("blockers", [])
                if clean_text(item)
            ],
            "adjudicationItems": int(((adjudication.get("counts") or {}).get("items")) or 0),
            "adjudicationSuggestedDecisions": (adjudication.get("counts") or {}).get("suggestedDecisions", {}),
            "adjudicationReviewPriorities": (adjudication.get("counts") or {}).get("reviewPriorities", {}),
            "proposedGoldsetDecisions": ((proposed_goldset.get("counts") or {}).get("decisions")) or {},
            "proposedBenchmarkPassed": bool(proposed_benchmark.get("modelPassedBenchmark", False)),
            "proposedBenchmarkFalseExcludeCount": int(
                ((proposed_benchmark.get("metrics") or {}).get("falseExcludeCount")) or 0
            ),
            "proposedBenchmarkHighQualityFalseExcludeCount": int(
                ((proposed_benchmark.get("metrics") or {}).get("highQualityFalseExcludeCount")) or 0
            ),
            "proposedBenchmarkExactDecisionAccuracy": (
                (proposed_benchmark.get("metrics") or {}).get("exactDecisionAccuracy")
            ),
        },
        "residualRisks": residual_risks,
        "confirmationChecklist": confirmation_checklist,
        "artifacts": {
            "packageJson": str(PACKAGE_JSON_PATH),
            "packageMd": str(PACKAGE_MD_PATH),
            "guardCandidatesJson": str(GUARD_JSON_PATH),
            "guardCandidatesCsv": str(GUARD_CSV_PATH),
            "guardCandidatesMd": str(GUARD_MD_PATH),
            "serviceScopeGoldsetJson": str(GOLDSET_JSON_PATH),
            "serviceScopeGoldsetMd": str(GOLDSET_MD_PATH),
            "serviceScopeBenchmarkJson": str(BENCHMARK_JSON_PATH),
            "serviceScopeBenchmarkMd": str(BENCHMARK_MD_PATH),
            "serviceScopeShadowGuardOffJson": str(SHADOW_JSON_PATH),
            "serviceScopeShadowGuardOffMd": str(SHADOW_MD_PATH),
            "modelImprovementGateJson": str(MODEL_GATE_JSON_PATH),
            "modelImprovementGateMd": str(MODEL_GATE_MD_PATH),
            "serviceScopeAdjudicationJson": str(ADJUDICATION_JSON_PATH),
            "serviceScopeAdjudicationCsv": str(ADJUDICATION_CSV_PATH),
            "serviceScopeAdjudicationMd": str(ADJUDICATION_MD_PATH),
            "serviceScopeProposedGoldsetJson": str(PROPOSED_GOLDSET_JSON_PATH),
            "serviceScopeProposedGoldsetMd": str(PROPOSED_GOLDSET_MD_PATH),
            "serviceScopeProposedBenchmarkJson": str(PROPOSED_BENCHMARK_JSON_PATH),
            "serviceScopeProposedBenchmarkMd": str(PROPOSED_BENCHMARK_MD_PATH),
            "latestQualityState": str(LATEST_STATE_PATH),
        },
    }
    write_json(PACKAGE_JSON_PATH, package)
    write_text(PACKAGE_MD_PATH, render_package_md(package))

    print(
        json.dumps(
            {
                "packageJson": str(PACKAGE_JSON_PATH),
                "packageMd": str(PACKAGE_MD_PATH),
                "guardCandidatesJson": str(GUARD_JSON_PATH),
                "guardCandidatesCsv": str(GUARD_CSV_PATH),
                "guardCandidatesMd": str(GUARD_MD_PATH),
                "guardRecoveredRows": len(guard_candidates),
                "status": package["status"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
