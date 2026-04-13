#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "structured_signal_validation_wave_001.json"
DEFAULT_CSV_PATH = ROOT / "data" / "structured_signal_validation_wave_001.csv"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "structured_signal_validation_review_001.json"

SIGNAL_KEYS = [
    "DomainSignals",
    "ProblemSignals",
    "SystemSignals",
    "DataSignals",
    "WorkflowSignals",
]


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def clean(value: str) -> str:
    return " ".join(str(value or "").split()).strip()


def parse_pipe_list(value) -> list[str]:
    if isinstance(value, list):
        return [clean(item) for item in value if clean(item)]
    return [clean(part) for part in str(value or "").split("|") if clean(part)]


def build_signal_payload(prefix: str, row: dict) -> dict:
    return {
        "domainSignals": parse_pipe_list(row.get(f"{prefix}DomainSignals", "")),
        "problemSignals": parse_pipe_list(row.get(f"{prefix}ProblemSignals", "")),
        "systemSignals": parse_pipe_list(row.get(f"{prefix}SystemSignals", "")),
        "dataSignals": parse_pipe_list(row.get(f"{prefix}DataSignals", "")),
        "workflowSignals": parse_pipe_list(row.get(f"{prefix}WorkflowSignals", "")),
    }


def choose_expected(decision: str, row: dict) -> tuple[dict | None, bool]:
    normalized = clean(decision).lower()
    current = build_signal_payload("current", row)
    suggested = build_signal_payload("suggested", row)
    manual = {
        "domainSignals": parse_pipe_list(row.get("manualDomainSignals", "")),
        "problemSignals": parse_pipe_list(row.get("manualProblemSignals", "")),
        "systemSignals": parse_pipe_list(row.get("manualSystemSignals", "")),
        "dataSignals": parse_pipe_list(row.get("manualDataSignals", "")),
        "workflowSignals": parse_pipe_list(row.get("manualWorkflowSignals", "")),
    }

    if normalized == "approve_suggested":
        return suggested, True
    if normalized == "approve_current":
        return current, True
    if normalized == "approve_low":
        return {
            "domainSignals": [],
            "problemSignals": [],
            "systemSignals": [],
            "dataSignals": [],
            "workflowSignals": [],
        }, True
    if normalized == "needs_edit":
        if any(manual.values()):
            return manual, True
    return None, False


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--csv", default=str(DEFAULT_CSV_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    args = parser.parse_args()

    wave = load_json(pathlib.Path(args.wave))
    wave_items = {item["id"]: item for item in wave.get("items", [])}

    reviewed_items = []
    resolved = 0
    unresolved = 0

    with pathlib.Path(args.csv).open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            item_id = clean(row.get("id", ""))
            source = wave_items.get(item_id, {})
            decision = clean(row.get("decision", "")) or clean(row.get("recommendedDecision", ""))
            expected, is_resolved = choose_expected(decision, row)
            if is_resolved:
                resolved += 1
            else:
                unresolved += 1

            reviewed_items.append(
                {
                    "id": item_id,
                    "reason": clean(row.get("reason", "")) or clean(source.get("reason", "")),
                    "company": clean(row.get("company", "")) or clean(source.get("company", "")),
                    "title": clean(row.get("title", "")) or clean(source.get("title", "")),
                    "roleDisplay": clean(row.get("roleDisplay", "")) or clean(source.get("roleDisplay", "")),
                    "current": build_signal_payload("current", row),
                    "suggested": build_signal_payload("suggested", row),
                    "decision": decision,
                    "recommendedDecision": clean(row.get("recommendedDecision", "")),
                    "notes": clean(row.get("notes", "")),
                    "resolved": is_resolved,
                    "expected": expected
                    or {
                        "domainSignals": [],
                        "problemSignals": [],
                        "systemSignals": [],
                        "dataSignals": [],
                        "workflowSignals": [],
                    },
                }
            )

    payload = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "sourceWavePath": str(pathlib.Path(args.wave)),
        "sourceDecisionSheetPath": str(pathlib.Path(args.csv)),
        "count": len(reviewed_items),
        "resolvedCount": resolved,
        "unresolvedCount": unresolved,
        "items": reviewed_items,
    }
    write_json(pathlib.Path(args.output), payload)
    print(
        f"Wrote structured signal review set to {args.output} "
        f"(resolved={resolved}, unresolved={unresolved})"
    )


if __name__ == "__main__":
    main()
