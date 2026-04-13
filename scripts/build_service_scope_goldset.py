#!/usr/bin/env python3

import argparse
import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from ai_runtime import JOBS_PATH, compact_job_for_summary, compute_service_scope_signature


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = ROOT / "data" / "service_scope_guard_recovery_candidates_001.json"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "service_scope_goldset_001.json"
DEFAULT_MD_PATH = ROOT / "docs" / "service_scope_goldset_001.md"
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


def load_decision_csv(path: Path | None) -> dict[str, dict]:
    if not path or not path.exists():
        return {}
    with path.open("r", encoding="utf-8", newline="") as handle:
        return {
            clean_text(row.get("id", "")): row
            for row in csv.DictReader(handle)
            if clean_text(row.get("id", ""))
        }


def merge_decision(candidate: dict, decision_row: dict | None) -> dict:
    if not decision_row:
        return candidate
    merged = dict(candidate)
    for key in (
        "confirmServiceScope",
        "confirmRoleGroup",
        "confirmFocusLabel",
        "confirmDecisionSource",
        "reviewerNotes",
    ):
        value = clean_text(decision_row.get(key, ""))
        if value:
            merged[key] = value
    return merged


def build_gold_item(
    candidate: dict,
    job: dict,
    allow_provisional: bool,
    provisional_decision_field: str = "serviceScopeResolvedAction",
) -> dict:
    confirmed_decision = normalize_decision(candidate.get("confirmServiceScope", ""))
    if confirmed_decision:
        decision = confirmed_decision
        decision_source = clean_text(candidate.get("confirmDecisionSource", "")) or "human_confirmed"
        requires_confirmation = False
    elif allow_provisional:
        decision = (
            normalize_decision(candidate.get(provisional_decision_field, ""))
            or normalize_decision(candidate.get("serviceScopeResolvedAction", ""))
            or "review"
        )
        decision_source = (
            "adjudication_suggestion_provisional"
            if provisional_decision_field == "suggestedServiceScope"
            else "guard_recovery_provisional"
        )
        requires_confirmation = True
    else:
        decision = ""
        decision_source = "unconfirmed"
        requires_confirmation = True

    compact = compact_job_for_summary(job) if job else {}
    role_group = clean_text(candidate.get("confirmRoleGroup", "")) or clean_text(candidate.get("roleGroup", ""))
    focus_label = clean_text(candidate.get("confirmFocusLabel", "")) or clean_text(candidate.get("focusLabel", ""))

    return {
        "id": clean_text(candidate.get("id", "")),
        "company": clean_text(candidate.get("company", "")),
        "title": clean_text(candidate.get("title", "")),
        "jobUrl": clean_text(candidate.get("jobUrl", "")),
        "summaryQuality": clean_text(candidate.get("summaryQuality", "")),
        "input": {
            "currentRole": clean_text(candidate.get("rawRole", "")) or role_group,
            "summary": clean_text(candidate.get("summary", "")),
            "focusLabel": clean_text(candidate.get("focusLabel", "")),
            "keywords": [clean_text(value) for value in candidate.get("keywords", []) if clean_text(value)],
            "detailBody": compact.get("detailBody", []),
            "tasks": compact.get("tasks", []),
            "requirements": compact.get("requirements", []),
            "preferred": compact.get("preferred", []),
            "skills": compact.get("skills", []),
        },
        "target": {
            "serviceScopeAction": decision,
            "roleGroup": role_group,
            "focusLabel": focus_label,
        },
        "currentModel": {
            "action": normalize_decision(candidate.get("serviceScopeModelAction", "")),
            "resolvedAction": normalize_decision(candidate.get("serviceScopeResolvedAction", "")),
            "reason": clean_text(candidate.get("serviceScopeReason", "")),
            "confidence": clean_text(candidate.get("serviceScopeConfidence", "")),
        },
        "review": {
            "decisionSource": decision_source,
            "requiresHumanConfirmation": requires_confirmation,
            "reviewerNotes": clean_text(candidate.get("reviewerNotes", "")),
        },
        "signature": compute_service_scope_signature(job) if job else "",
    }


def render_md(payload: dict) -> str:
    counts = payload["counts"]
    lines = [
        "# Service Scope Goldset 001",
        "",
        f"- generatedAt: `{payload['generatedAt']}`",
        f"- status: `{payload['status']}`",
        f"- items: `{counts['items']}`",
        f"- confirmedItems: `{counts['confirmedItems']}`",
        f"- provisionalItems: `{counts['provisionalItems']}`",
        f"- include: `{counts['decisions'].get('include', 0)}`",
        f"- review: `{counts['decisions'].get('review', 0)}`",
        f"- exclude: `{counts['decisions'].get('exclude', 0)}`",
        "",
        "이 파일은 guard recovery 25개를 모델 개선 평가셋으로 고정하기 위한 산출물입니다.",
        "`guard_recovery_provisional` 항목은 아직 사람 검수 완료가 아니므로 최종 모델 개선 완료 판정에 단독으로 쓰면 안 됩니다.",
        "",
        "| # | company | title | quality | expected | source | current model |",
        "|---:|---|---|---|---|---|---|",
    ]
    for index, item in enumerate(payload["items"], start=1):
        lines.append(
            "| "
            + " | ".join(
                [
                    str(index),
                    md_cell(item["company"]),
                    md_cell(item["title"]),
                    md_cell(item["summaryQuality"]),
                    md_cell(item["target"]["serviceScopeAction"]),
                    md_cell(item["review"]["decisionSource"]),
                    md_cell(item["currentModel"]["action"]),
                ]
            )
            + " |"
        )
    return "\n".join(lines).rstrip() + "\n"


def build_goldset(
    input_path: Path,
    allow_provisional: bool,
    decisions_csv: Path | None = None,
    use_suggestions_as_provisional: bool = False,
) -> dict:
    candidate_payload = load_json(input_path, {"items": []}) or {"items": []}
    jobs_payload = load_json(JOBS_PATH, {"jobs": []}) or {"jobs": []}
    jobs_by_id = {job.get("id", ""): job for job in jobs_payload.get("jobs", []) if job.get("id")}
    decisions_by_id = load_decision_csv(decisions_csv)

    items = []
    for candidate in candidate_payload.get("items", []):
        job_id = clean_text(candidate.get("id", ""))
        if not job_id:
            continue
        candidate = merge_decision(candidate, decisions_by_id.get(job_id))
        items.append(
            build_gold_item(
                candidate,
                jobs_by_id.get(job_id, {}),
                allow_provisional,
                provisional_decision_field=(
                    "suggestedServiceScope" if use_suggestions_as_provisional else "serviceScopeResolvedAction"
                ),
            )
        )

    decisions = Counter(item["target"]["serviceScopeAction"] or "unconfirmed" for item in items)
    provisional_count = sum(1 for item in items if item["review"]["requiresHumanConfirmation"])
    confirmed_count = len(items) - provisional_count
    status = "confirmed" if provisional_count == 0 else "provisional_requires_human_confirmation"

    return {
        "generatedAt": now_iso(),
        "source": str(input_path),
        "decisionsCsv": str(decisions_csv) if decisions_csv else None,
        "status": status,
        "policy": {
            "validDecisions": sorted(VALID_DECISIONS),
            "criticalError": "include/review target predicted as exclude",
            "provisionalDecisionRule": (
                "defaults to suggestedServiceScope until confirmServiceScope is filled"
                if use_suggestions_as_provisional
                else "defaults to serviceScopeResolvedAction until confirmServiceScope is filled"
            ),
        },
        "counts": {
            "items": len(items),
            "confirmedItems": confirmed_count,
            "provisionalItems": provisional_count,
            "decisions": dict(sorted(decisions.items())),
        },
        "items": items,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    parser.add_argument("--md-output", type=Path, default=DEFAULT_MD_PATH)
    parser.add_argument("--decisions-csv", type=Path)
    parser.add_argument("--use-suggestions-as-provisional", action="store_true")
    parser.add_argument("--confirmed-only", action="store_true")
    args = parser.parse_args()

    payload = build_goldset(
        args.input,
        allow_provisional=not args.confirmed_only,
        decisions_csv=args.decisions_csv,
        use_suggestions_as_provisional=args.use_suggestions_as_provisional,
    )
    if args.confirmed_only and payload["counts"]["provisionalItems"]:
        raise SystemExit("goldset still has unconfirmed service-scope decisions")

    write_json(args.output, payload)
    write_text(args.md_output, render_md(payload))
    print(
        json.dumps(
            {
                "goldsetJson": str(args.output),
                "goldsetMd": str(args.md_output),
                "status": payload["status"],
                "counts": payload["counts"],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
