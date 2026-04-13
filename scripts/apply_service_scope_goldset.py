#!/usr/bin/env python3

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


from ai_runtime import JOBS_PATH, compute_service_scope_signature
from build_summary_board import load_service_scope_override_store, save_service_scope_override_store


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GOLDSET_PATH = ROOT / "data" / "service_scope_goldset_001.json"
VALID_ACTIONS = {"include", "review", "exclude"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def normalize_action(value) -> str:
    action = clean_text(value).lower()
    return action if action in VALID_ACTIONS else ""


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def build_override(item: dict, job: dict, updated_at: str) -> dict:
    target = item.get("target", {}) if isinstance(item.get("target", {}), dict) else {}
    action = normalize_action(target.get("serviceScopeAction", ""))
    if not action:
        raise ValueError(f"{item.get('id', '')}: missing target serviceScopeAction")

    mapped_role = clean_text(target.get("roleGroup", ""))
    reason = clean_text((item.get("review", {}) or {}).get("reviewerNotes", ""))
    if not reason:
        reason = f"service scope goldset confirmed {action}"

    return {
        "action": action,
        "source": "service_scope_goldset_001",
        "reason": reason[:80],
        "mappedRole": mapped_role if action == "include" else "",
        "confidence": "high",
        "signature": compute_service_scope_signature(job),
        "updatedAt": updated_at,
    }


def collect_confirmed_items(goldset: dict, allow_provisional: bool) -> list[dict]:
    items = goldset.get("items", []) if isinstance(goldset.get("items", []), list) else []
    selected = []
    blocked = []
    for item in items:
        review = item.get("review", {}) if isinstance(item.get("review", {}), dict) else {}
        requires_confirmation = bool(review.get("requiresHumanConfirmation", True))
        if requires_confirmation and not allow_provisional:
            blocked.append(clean_text(item.get("id", "")))
            continue
        selected.append(item)
    if blocked:
        raise SystemExit(
            f"Refusing to apply {len(blocked)} provisional goldset items. "
            "Fill confirmServiceScope and rebuild goldset, or rerun with --allow-provisional."
        )
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--goldset", type=Path, default=DEFAULT_GOLDSET_PATH)
    parser.add_argument("--apply", action="store_true", help="write changes; default is dry-run")
    parser.add_argument(
        "--allow-provisional",
        action="store_true",
        help="allow applying provisional guard-recovery decisions",
    )
    args = parser.parse_args()

    goldset = load_json(args.goldset, {"items": []}) or {"items": []}
    selected = collect_confirmed_items(goldset, allow_provisional=args.allow_provisional)
    jobs_payload = load_json(JOBS_PATH, {"jobs": []}) or {"jobs": []}
    jobs_by_id = {job.get("id", ""): job for job in jobs_payload.get("jobs", []) if clean_text(job.get("id", ""))}

    updated_at = now_iso()
    overrides = {}
    missing_jobs = []
    for item in selected:
        job_id = clean_text(item.get("id", ""))
        job = jobs_by_id.get(job_id)
        if not job:
            missing_jobs.append(job_id)
            continue
        overrides[job_id] = build_override(item, job, updated_at)

    if missing_jobs:
        raise SystemExit(f"Missing jobs for {len(missing_jobs)} goldset items: {', '.join(missing_jobs[:5])}")

    if args.apply:
        store = load_service_scope_override_store()
        existing_items = store.get("items", {}) if isinstance(store.get("items", {}), dict) else {}
        existing_items.update(overrides)
        store["items"] = existing_items
        store["updatedAt"] = updated_at
        save_service_scope_override_store(store)

    print(
        json.dumps(
            {
                "goldset": str(args.goldset),
                "status": goldset.get("status", ""),
                "dryRun": not args.apply,
                "allowProvisional": args.allow_provisional,
                "selectedItems": len(selected),
                "wouldApply": len(overrides),
                "applied": len(overrides) if args.apply else 0,
                "sampleIds": list(overrides)[:10],
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
