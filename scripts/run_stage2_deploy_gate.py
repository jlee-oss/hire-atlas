#!/usr/bin/env python3

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_VALIDATION_JSON = ROOT / "data" / "stage2_validation_latest.json"
DEFAULT_VALIDATION_CSV = ROOT / "data" / "stage2_validation_candidates_latest.csv"
DEFAULT_OUTPUT_JSON = ROOT / "data" / "stage2_deploy_gate_latest.json"
DEFAULT_OUTPUT_MD = ROOT / "docs" / "stage2_deploy_gate_latest.md"
DEFAULT_DEPLOY_CSV = ROOT / "data" / "stage2_deploy_candidates_latest.csv"

APPROVED_VALUES = {"승인", "approved", "true", "yes", "y", "1"}
ALLOWED_DEPLOY_ROLES = {
    "인공지능 엔지니어",
    "인공지능 리서처",
    "데이터 사이언티스트",
    "데이터 분석가",
}
BLOCKING_STATES = {
    "stage2_missing",
    "stage2_stale",
    "stage2_unreadable",
    "quality_issue",
}
NON_BLOCKING_ISSUE_CODES = {
    "role_diff",
    "focus_diff",
    "keywords_diff",
    "summary_diff",
    "business_context_in_ai_role",
    "data_engineering_ai_context",
    "data_engineering_ai_title_context",
    "summary_too_short",
}
DEPLOY_FIELDNAMES = [
    "공고키",
    "변경해시",
    "분류직무",
    "직무초점",
    "핵심기술",
    "구분요약",
    "회사명_표시",
    "공고제목_표시",
    "공고URL",
    "최종발견시각",
    "승인여부",
    "검증메모",
]
REQUIRED_CANDIDATE_IDENTITY_FIELDS = ["공고키", "변경해시"]
REQUIRED_DEPLOY_FIELDS = [
    "공고키",
    "변경해시",
    "분류직무",
    "직무초점",
    "핵심기술",
    "구분요약",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value) -> str:
    return " ".join(str(value or "").split()).strip()


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=DEPLOY_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def approved(row: dict) -> bool:
    return clean(row.get("승인여부", "")).lower() in APPROVED_VALUES


def state_codes(row: dict) -> list[str]:
    raw = clean(row.get("이슈코드", ""))
    return [clean(part) for part in raw.split("|") if clean(part)]


def deploy_value(row: dict, stage2_key: str, stage1_key: str) -> str:
    return clean(row.get(stage2_key, "")) or clean(row.get(stage1_key, ""))


def build_deploy_row(row: dict) -> dict:
    return {
        "공고키": clean(row.get("공고키", "")),
        "변경해시": clean(row.get("변경해시", "")),
        "분류직무": deploy_value(row, "stage2_분류직무", "stage1_분류직무"),
        "직무초점": deploy_value(row, "stage2_직무초점", "stage1_직무초점"),
        "핵심기술": deploy_value(row, "stage2_핵심기술", "stage1_핵심기술"),
        "구분요약": deploy_value(row, "stage2_구분요약", "stage1_구분요약"),
        "회사명_표시": clean(row.get("회사명_표시", "")),
        "공고제목_표시": clean(row.get("공고제목_표시", "")),
        "공고URL": clean(row.get("공고URL", "")),
        "최종발견시각": clean(row.get("최종발견시각", "")),
        "승인여부": clean(row.get("승인여부", "")),
        "검증메모": clean(row.get("검증메모", "")),
    }


def row_is_deployable(row: dict) -> bool:
    if clean(row.get("검증상태", "")) != "approved":
        return False
    if not approved(row):
        return False
    if any(code in BLOCKING_STATES for code in state_codes(row)):
        return False
    if clean(row.get("검증우선순위", "")) not in {"pass", "low"}:
        return False
    return True


def collect_examples(rows: list[dict], predicate, limit: int = 10) -> list[dict]:
    examples = []
    for row in rows:
        if not predicate(row):
            continue
        examples.append(
            {
                "공고키": clean(row.get("공고키", "")),
                "회사명": clean(row.get("회사명_표시", "")),
                "공고제목": clean(row.get("공고제목_표시", "")),
                "검증상태": clean(row.get("검증상태", "")),
                "검증우선순위": clean(row.get("검증우선순위", "")),
                "이슈코드": clean(row.get("이슈코드", "")),
                "승인여부": clean(row.get("승인여부", "")),
            }
        )
        if len(examples) >= limit:
            break
    return examples


def duplicate_key_rows(rows: list[dict], field: str) -> list[dict]:
    counts = Counter(clean(row.get(field, "")) for row in rows if clean(row.get(field, "")))
    duplicate_values = {value for value, count in counts.items() if count > 1}
    return [row for row in rows if clean(row.get(field, "")) in duplicate_values]


def collect_missing_field_examples(rows: list[dict], fields: list[str], limit: int = 10) -> list[dict]:
    examples = []
    for row in rows:
        missing = [field for field in fields if not clean(row.get(field, ""))]
        if not missing:
            continue
        examples.append(
            {
                "공고키": clean(row.get("공고키", "")),
                "회사명": clean(row.get("회사명_표시", "")),
                "공고제목": clean(row.get("공고제목_표시", "")),
                "missingFields": missing,
            }
        )
        if len(examples) >= limit:
            break
    return examples


def collect_invalid_role_examples(rows: list[dict], limit: int = 10) -> list[dict]:
    examples = []
    for row in rows:
        role = clean(row.get("분류직무", ""))
        if role in ALLOWED_DEPLOY_ROLES:
            continue
        examples.append(
            {
                "공고키": clean(row.get("공고키", "")),
                "회사명": clean(row.get("회사명_표시", "")),
                "공고제목": clean(row.get("공고제목_표시", "")),
                "분류직무": role,
            }
        )
        if len(examples) >= limit:
            break
    return examples


def criterion(actual, target, passed: bool) -> dict:
    return {
        "actual": actual,
        "target": target,
        "passed": bool(passed),
    }


def build_gate_report(validation: dict, rows: list[dict], deploy_rows: list[dict]) -> dict:
    metrics = validation.get("metrics", {}) if isinstance(validation.get("metrics", {}), dict) else {}
    state_counts = validation.get("stateCounts", {}) if isinstance(validation.get("stateCounts", {}), dict) else {}
    issue_counts = validation.get("issueCounts", {}) if isinstance(validation.get("issueCounts", {}), dict) else {}
    has_blocking_issue_counts = isinstance(validation.get("blockingIssueCounts"), dict)
    blocking_issue_counts = validation.get("blockingIssueCounts", {}) if has_blocking_issue_counts else {}

    approved_rows = [row for row in rows if approved(row)]
    pending_rows = [row for row in rows if clean(row.get("검증상태", "")) == "pending"]
    needs_review_rows = [row for row in rows if clean(row.get("검증상태", "")) == "needs_review"]
    missing_candidate_identity_rows = [
        row
        for row in rows
        if any(not clean(row.get(field, "")) for field in REQUIRED_CANDIDATE_IDENTITY_FIELDS)
    ]
    duplicate_candidate_key_rows = duplicate_key_rows(rows, "공고키")
    missing_deploy_field_rows = [
        row
        for row in deploy_rows
        if any(not clean(row.get(field, "")) for field in REQUIRED_DEPLOY_FIELDS)
    ]
    invalid_deploy_role_rows = [
        row
        for row in deploy_rows
        if clean(row.get("분류직무", "")) not in ALLOWED_DEPLOY_ROLES
    ]
    blocking_state_count = sum(int(state_counts.get(state, 0) or 0) for state in BLOCKING_STATES)
    issue_count_total = sum(int(value or 0) for value in issue_counts.values())
    if has_blocking_issue_counts:
        blocking_issue_count = sum(int(value or 0) for value in blocking_issue_counts.values())
    else:
        blocking_issue_count = sum(
            int(value or 0)
            for key, value in issue_counts.items()
            if key not in NON_BLOCKING_ISSUE_CODES
        )
    high_or_medium_rows = [
        row
        for row in rows
        if clean(row.get("검증우선순위", "")) in {"high", "medium"}
    ]

    stage1_rows = int(metrics.get("stage1Rows", 0) or 0)
    stage2_rows = int(metrics.get("stage2Rows", 0) or 0)
    candidate_rows = int(metrics.get("candidateRows", 0) or 0)
    removed_from_stage1 = int(metrics.get("removedFromStage1", 0) or 0)

    criteria = {
        "stage2Readable": criterion(bool(not validation.get("stage2AccessError")), True, not validation.get("stage2AccessError")),
        "rowCountAligned": criterion(
            {"stage1": stage1_rows, "stage2": stage2_rows, "candidates": candidate_rows},
            "stage1 == stage2 == candidates > 0",
            stage1_rows > 0 and stage1_rows == stage2_rows == candidate_rows == len(rows),
        ),
        "noRemovedFromStage1": criterion(removed_from_stage1, 0, removed_from_stage1 == 0),
        "noBlockingStates": criterion(blocking_state_count, 0, blocking_state_count == 0),
        "noBlockingIssueCounts": criterion(blocking_issue_count, 0, blocking_issue_count == 0),
        "noPendingRows": criterion(len(pending_rows), 0, len(pending_rows) == 0),
        "noNeedsReviewRows": criterion(len(needs_review_rows), 0, len(needs_review_rows) == 0),
        "allRowsApproved": criterion(len(approved_rows), len(rows), bool(rows) and len(approved_rows) == len(rows)),
        "deployRowsMatchStage1": criterion(len(deploy_rows), stage1_rows, stage1_rows > 0 and len(deploy_rows) == stage1_rows),
        "candidateIdentityComplete": criterion(
            len(missing_candidate_identity_rows),
            0,
            len(missing_candidate_identity_rows) == 0,
        ),
        "candidateKeysUnique": criterion(
            len(duplicate_candidate_key_rows),
            0,
            len(duplicate_candidate_key_rows) == 0,
        ),
        "deployFieldsComplete": criterion(
            len(missing_deploy_field_rows),
            0,
            len(missing_deploy_field_rows) == 0,
        ),
        "deployRolesAllowed": criterion(
            len(invalid_deploy_role_rows),
            0,
            len(invalid_deploy_role_rows) == 0,
        ),
    }
    blockers = [name for name, item in criteria.items() if not item["passed"]]
    return {
        "generatedAt": now_iso(),
        "status": "passed" if not blockers else "blocked",
        "passed": not blockers,
        "criteria": criteria,
        "blockers": blockers,
        "metrics": {
            "stage1Rows": stage1_rows,
            "stage2Rows": stage2_rows,
            "candidateRows": candidate_rows,
            "approvedRows": len(approved_rows),
            "deployableRows": len(deploy_rows),
            "pendingRows": len(pending_rows),
            "needsReviewRows": len(needs_review_rows),
            "highOrMediumPriorityRows": len(high_or_medium_rows),
            "candidateIdentityMissingRows": len(missing_candidate_identity_rows),
            "duplicateCandidateKeyRows": len(duplicate_candidate_key_rows),
            "deployMissingRequiredFieldRows": len(missing_deploy_field_rows),
            "deployInvalidRoleRows": len(invalid_deploy_role_rows),
            "blockingStateRows": blocking_state_count,
            "blockingIssueCount": blocking_issue_count,
            "issueCountTotal": issue_count_total,
        },
        "stateCounts": state_counts,
        "issueCounts": issue_counts,
        "blockingIssueCounts": blocking_issue_counts,
        "severityCounts": validation.get("severityCounts", {}),
        "approvalCounts": dict(Counter(clean(row.get("승인여부", "")) or "(blank)" for row in rows)),
        "examples": {
            "pending": collect_examples(rows, lambda row: clean(row.get("검증상태", "")) == "pending"),
            "needsReview": collect_examples(rows, lambda row: clean(row.get("검증상태", "")) == "needs_review"),
            "unapproved": collect_examples(rows, lambda row: not approved(row)),
            "blocking": collect_examples(rows, lambda row: any(code in BLOCKING_STATES for code in state_codes(row))),
        },
        "integrityExamples": {
            "missingCandidateIdentity": collect_missing_field_examples(
                rows,
                REQUIRED_CANDIDATE_IDENTITY_FIELDS,
            ),
            "duplicateCandidateKeys": collect_examples(
                rows,
                lambda row: row in duplicate_candidate_key_rows,
            ),
            "missingDeployFields": collect_missing_field_examples(
                deploy_rows,
                REQUIRED_DEPLOY_FIELDS,
            ),
            "invalidDeployRoles": collect_invalid_role_examples(deploy_rows),
        },
        "inputs": {
            "validationJson": str(DEFAULT_VALIDATION_JSON),
            "validationCsv": str(DEFAULT_VALIDATION_CSV),
        },
        "outputs": {
            "gateJson": str(DEFAULT_OUTPUT_JSON),
            "gateMd": str(DEFAULT_OUTPUT_MD),
            "deployCsv": str(DEFAULT_DEPLOY_CSV),
        },
    }


def render_md(report: dict) -> str:
    lines = [
        "# Stage2 Deploy Gate Latest",
        "",
        f"- generatedAt: `{report['generatedAt']}`",
        f"- status: `{report['status']}`",
        f"- passed: `{report['passed']}`",
        "",
        "## Metrics",
        "",
    ]
    for key, value in report["metrics"].items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Criteria", ""])
    for key, item in report["criteria"].items():
        lines.append(f"- `{key}` actual `{item['actual']}` target `{item['target']}` passed `{item['passed']}`")
    if report["blockers"]:
        lines.extend(["", "## Blockers", ""])
        for blocker in report["blockers"]:
            lines.append(f"- `{blocker}`")
    lines.extend(["", "## Blocking Issue Counts", ""])
    for key, value in sorted(report.get("blockingIssueCounts", {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Severity Counts", ""])
    for key, value in sorted(report.get("severityCounts", {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Examples", ""])
    for group, examples in report["examples"].items():
        lines.append(f"### {group}")
        lines.append("")
        if not examples:
            lines.append("- none")
        for item in examples:
            lines.append(
                f"- `{item['회사명']}` | `{item['공고제목']}` | `{item['검증상태']}` | `{item['이슈코드'] or '-'}`"
            )
        lines.append("")
    lines.extend(["## Integrity Examples", ""])
    for group, examples in report.get("integrityExamples", {}).items():
        lines.append(f"### {group}")
        lines.append("")
        if not examples:
            lines.append("- none")
        for item in examples:
            if item.get("missingFields"):
                detail = ", ".join(item["missingFields"])
            elif item.get("분류직무") is not None:
                detail = item.get("분류직무") or "-"
            else:
                detail = item.get("이슈코드") or "-"
            lines.append(
                f"- `{item.get('회사명', '')}` | `{item.get('공고제목', '')}` | `{item.get('공고키', '') or '-'}` | `{detail}`"
            )
        lines.append("")
    lines.extend(["## Outputs", ""])
    for key, value in report["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fail-closed deploy gate for stage2 validation results.")
    parser.add_argument("--validation-json", type=Path, default=DEFAULT_VALIDATION_JSON)
    parser.add_argument("--validation-csv", type=Path, default=DEFAULT_VALIDATION_CSV)
    parser.add_argument("--output-json", type=Path, default=DEFAULT_OUTPUT_JSON)
    parser.add_argument("--output-md", type=Path, default=DEFAULT_OUTPUT_MD)
    parser.add_argument("--deploy-csv", type=Path, default=DEFAULT_DEPLOY_CSV)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    validation = load_json(args.validation_json)
    rows = read_csv(args.validation_csv)
    deploy_rows = [build_deploy_row(row) for row in rows if row_is_deployable(row)]
    report = build_gate_report(validation, rows, deploy_rows)
    report["inputs"] = {
        "validationJson": str(args.validation_json),
        "validationCsv": str(args.validation_csv),
    }
    report["outputs"] = {
        "gateJson": str(args.output_json),
        "gateMd": str(args.output_md),
        "deployCsv": str(args.deploy_csv),
    }

    write_json(args.output_json, report)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    write_csv(args.deploy_csv, deploy_rows)
    print(
        json.dumps(
            {
                "status": report["status"],
                "passed": report["passed"],
                "blockers": report["blockers"],
                "metrics": report["metrics"],
                "outputs": report["outputs"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
