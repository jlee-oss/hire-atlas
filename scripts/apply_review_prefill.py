#!/usr/bin/env python3

import argparse
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_PREFILL_PATH = ROOT / "data" / "review_prefill_001.json"
DEFAULT_SUGGESTIONS_PATH = ROOT / "data" / "review_suggestions_full_7b_001.json"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: pathlib.Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--prefill", default=str(DEFAULT_PREFILL_PATH))
    parser.add_argument("--suggestions", default=str(DEFAULT_SUGGESTIONS_PATH))
    args = parser.parse_args()

    wave_path = pathlib.Path(args.wave)
    prefill_path = pathlib.Path(args.prefill)
    suggestions_path = pathlib.Path(args.suggestions)

    wave = load_json(wave_path)
    prefill = load_json(prefill_path)
    proposals = {item["id"]: item.get("assistantProposal", {}) for item in prefill.get("items", [])}
    suggestions = {}
    if suggestions_path.exists():
        suggestion_payload = load_json(suggestions_path)
        for item in suggestion_payload.get("items", []):
            suggestions[item["id"]] = {
                "summary": item.get("suggestedSummary", ""),
                "focusLabel": item.get("suggestedFocusLabel", ""),
                "keywords": item.get("suggestedKeywords", []),
                "quality": item.get("suggestedQuality", ""),
                "notes": item.get("rationale", ""),
            }

    applied_manual = 0
    applied_suggestions = 0
    for item in wave.get("items", []):
        proposal = proposals.get(item.get("id"))
        if proposal:
            item["assistantPrefill"] = {
                "summary": proposal.get("summary", ""),
                "focusLabel": proposal.get("focusLabel", ""),
                "keywords": proposal.get("keywords", []),
                "quality": proposal.get("quality", ""),
                "notes": proposal.get("notes", ""),
                "source": "manual_prefill",
            }
            applied_manual += 1
            continue
        suggestion = suggestions.get(item.get("id"))
        if not suggestion:
            continue
        item["assistantPrefill"] = {
            "summary": suggestion.get("summary", ""),
            "focusLabel": suggestion.get("focusLabel", ""),
            "keywords": suggestion.get("keywords", []),
            "quality": suggestion.get("quality", ""),
            "notes": suggestion.get("notes", ""),
            "source": "model_suggestion",
        }
        applied_suggestions += 1

    wave.setdefault("prefill", {})
    wave["prefill"]["sourcePath"] = str(prefill_path)
    wave["prefill"]["suggestionsPath"] = str(suggestions_path) if suggestions_path.exists() else ""
    wave["prefill"]["manualAppliedCount"] = applied_manual
    wave["prefill"]["suggestionAppliedCount"] = applied_suggestions
    wave["prefill"]["appliedCount"] = applied_manual + applied_suggestions

    write_json(wave_path, wave)
    print(
        f"Applied assistant prefill to {wave_path} "
        f"(manual={applied_manual}, suggestions={applied_suggestions}, total={applied_manual + applied_suggestions})"
    )


if __name__ == "__main__":
    main()
