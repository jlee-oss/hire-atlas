#!/usr/bin/env python3

import importlib.util
import json
import os
import pathlib
import sys

from build_summary_board import build_summary_board, canonical_text


ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS_PATH = ROOT / "data" / "jobs.json"


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def detect_dl_runtime() -> dict:
    return {
        "numpy": module_available("numpy"),
        "torch": module_available("torch"),
        "sentenceTransformers": module_available("sentence_transformers"),
        "sklearn": module_available("sklearn"),
        "embeddingApiConfigured": bool(
            os.environ.get("OPENAI_API_KEY")
            or os.environ.get("SEMANTIC_EMBEDDING_API_KEY")
            or os.environ.get("SEMANTIC_EMBEDDING_BASE_URL")
        ),
    }


def find_stage2_role_mismatches(rows: list[dict]) -> list[dict]:
    mismatches = []
    for row in rows:
        stage2_role = row.get("stage2Role", "")
        role_group = row.get("roleGroup", "")
        if stage2_role and role_group and canonical_text(stage2_role) != canonical_text(role_group):
            mismatches.append(
                {
                    "id": row.get("id", ""),
                    "company": row.get("company", ""),
                    "title": row.get("title", ""),
                    "stage2Role": stage2_role,
                    "roleGroup": role_group,
                }
            )
    return mismatches


def find_compound_skill_split_issues(rows: list[dict]) -> list[dict]:
    issues = []
    for row in rows:
        skills = row.get("skills") or []
        skill_keys = {canonical_text(skill) for skill in skills}
        if "computer" in skill_keys and "vision" in skill_keys and "computervision" not in skill_keys:
            issues.append(
                {
                    "id": row.get("id", ""),
                    "company": row.get("company", ""),
                    "title": row.get("title", ""),
                    "skills": skills,
                }
            )
    return issues


def build_report(board: dict) -> dict:
    rows = board.get("rows") or []
    bundles = board.get("semanticBundles") or []
    role_bundles = board.get("semanticBundlesByRole") or {}
    total_rows = len(rows)
    covered_ids = {
        posting_id
        for bundle in bundles
        for posting_id in bundle.get("postingIds", [])
        if posting_id
    }
    active_ids = {row.get("id") for row in rows if row.get("active")}
    covered_active_ids = covered_ids & active_ids
    multi_company_bundles = [bundle for bundle in bundles if int(bundle.get("companyCount", 0) or 0) >= 2]
    confidence_values = [float(bundle.get("confidence", 0) or 0) for bundle in bundles]
    role_mismatches = find_stage2_role_mismatches(rows)
    compound_skill_split_issues = find_compound_skill_split_issues(rows)
    role_specific_singletons = [
        {"role": role, "label": bundle.get("label", ""), "postingCount": bundle.get("postingCount", 0)}
        for role, bundles_for_role in role_bundles.items()
        for bundle in bundles_for_role
        if int(bundle.get("postingCount", 0) or 0) < 2 or int(bundle.get("companyCount", 0) or 0) < 2
    ]

    coverage_rate = len(covered_ids) / total_rows if total_rows else 0
    active_coverage_rate = len(covered_active_ids) / len(active_ids) if active_ids else 0
    multi_company_rate = len(multi_company_bundles) / len(bundles) if bundles else 0
    average_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0

    gates = {
        "bundleCount": {"pass": len(bundles) >= 6, "actual": len(bundles), "expected": ">= 6"},
        "coverageRate": {"pass": coverage_rate >= 0.55, "actual": round(coverage_rate, 3), "expected": ">= 0.55"},
        "activeCoverageRate": {
            "pass": active_coverage_rate >= 0.55,
            "actual": round(active_coverage_rate, 3),
            "expected": ">= 0.55",
        },
        "multiCompanyBundleRate": {
            "pass": multi_company_rate >= 0.75,
            "actual": round(multi_company_rate, 3),
            "expected": ">= 0.75",
        },
        "averageConfidence": {
            "pass": average_confidence >= 0.55,
            "actual": round(average_confidence, 3),
            "expected": ">= 0.55",
        },
        "stage2RoleMismatches": {
            "pass": len(role_mismatches) == 0,
            "actual": len(role_mismatches),
            "expected": "0",
        },
        "compoundSkillSplitIssues": {
            "pass": len(compound_skill_split_issues) == 0,
            "actual": len(compound_skill_split_issues),
            "expected": "0",
        },
        "roleSpecificSingletonBundles": {
            "pass": len(role_specific_singletons) == 0,
            "actual": len(role_specific_singletons),
            "expected": "0",
        },
    }
    return {
        "ok": all(item["pass"] for item in gates.values()),
        "method": "stage2_semantic_graph",
        "dlRuntime": detect_dl_runtime(),
        "metrics": {
            "totalRows": total_rows,
            "activeRows": len(active_ids),
            "bundleCount": len(bundles),
            "coveredRows": len(covered_ids),
            "coverageRate": round(coverage_rate, 3),
            "coveredActiveRows": len(covered_active_ids),
            "activeCoverageRate": round(active_coverage_rate, 3),
            "multiCompanyBundleRate": round(multi_company_rate, 3),
            "averageConfidence": round(average_confidence, 3),
            "roleBundleCounts": {role: len(bundles_for_role) for role, bundles_for_role in role_bundles.items()},
        },
        "topBundles": [
            {
                "label": bundle.get("label", ""),
                "postingCount": bundle.get("postingCount", 0),
                "companyCount": bundle.get("companyCount", 0),
                "confidence": bundle.get("confidence", 0),
                "evidenceTerms": bundle.get("evidenceTerms", []),
            }
            for bundle in bundles[:8]
        ],
        "gates": gates,
        "samples": {
            "stage2RoleMismatches": role_mismatches[:10],
            "compoundSkillSplitIssues": compound_skill_split_issues[:10],
            "roleSpecificSingletonBundles": role_specific_singletons[:10],
        },
    }


def main() -> int:
    payload = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    board = build_summary_board(payload)
    report = build_report(board)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
