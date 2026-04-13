#!/usr/bin/env python3

import argparse
import csv
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = ROOT / "data" / "service_scope_adjudication_pack_001.json"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "service_scope_adjudication_decisions_v2.csv"
VALID_DECISIONS = {"include", "review", "exclude"}


def clean_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def normalize_decision(value) -> str:
    decision = clean_text(value).lower()
    return decision if decision in VALID_DECISIONS else ""


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_note(item: dict) -> str:
    priority = clean_text(item.get("reviewPriority", ""))
    reason = clean_text(item.get("suggestedReason", ""))
    model = clean_text(item.get("modelDecision", ""))
    model_reason = clean_text(item.get("modelReason", ""))
    return f"codex_adjudicated; priority={priority}; model={model}; suggestedReason={reason}; modelReason={model_reason}"[
        :500
    ]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT_PATH)
    args = parser.parse_args()

    payload = load_json(args.input)
    items = payload.get("items", []) if isinstance(payload.get("items", []), list) else []
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "id",
        "confirmServiceScope",
        "confirmRoleGroup",
        "confirmFocusLabel",
        "confirmDecisionSource",
        "reviewerNotes",
    ]
    written = 0
    with args.output.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in items:
            job_id = clean_text(item.get("id", ""))
            decision = normalize_decision(item.get("suggestedServiceScope", ""))
            if not job_id or not decision:
                continue
            writer.writerow(
                {
                    "id": job_id,
                    "confirmServiceScope": decision,
                    "confirmRoleGroup": "",
                    "confirmFocusLabel": clean_text(item.get("focusLabel", "")),
                    "confirmDecisionSource": "codex_adjudicated",
                    "reviewerNotes": build_note(item),
                }
            )
            written += 1

    print(
        json.dumps(
            {
                "input": str(args.input),
                "output": str(args.output),
                "written": written,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
