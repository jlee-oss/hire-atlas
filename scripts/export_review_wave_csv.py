#!/usr/bin/env python3

import argparse
import csv
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "review_wave_001.csv"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compact(values) -> str:
    if isinstance(values, list):
        return " | ".join(str(value) for value in values if str(value).strip())
    return str(values or "")


def issues_text(issues: list[dict]) -> str:
    return " | ".join(
        f"{item.get('code','')}[{item.get('severity','')}]: {item.get('note','')}"
        for item in issues or []
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    args = parser.parse_args()

    wave = load_json(pathlib.Path(args.wave))
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "sourceDataset",
        "id",
        "company",
        "title",
        "roleGroup",
        "clusterId",
        "clusterLabel",
        "active",
        "currentSummary",
        "currentFocusLabel",
        "currentKeywords",
        "currentQuality",
        "detailBody",
        "tasks",
        "requirements",
        "preferred",
        "skills",
        "machinePriority",
        "machineScore",
        "machineIssues",
        "controlSample",
        "assistantSummary",
        "assistantFocusLabel",
        "assistantKeywords",
        "assistantQuality",
        "assistantNotes",
        "assistantDraftSummaryPass",
        "assistantDraftFocusLabelPass",
        "assistantDraftKeywordsPass",
        "assistantDraftOverallPass",
        "assistantDraftCorrectedSummary",
        "assistantDraftCorrectedFocusLabel",
        "assistantDraftCorrectedKeywords",
        "assistantDraftCorrectedQuality",
        "assistantDraftNotes",
        "reviewSummaryPass",
        "reviewFocusLabelPass",
        "reviewKeywordsPass",
        "reviewOverallPass",
        "correctedSummary",
        "correctedFocusLabel",
        "correctedKeywords",
        "correctedQuality",
        "reviewNotes",
    ]

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for item in wave.get("items", []):
            assistant_prefill = item.get("assistantPrefill", {})
            assistant_draft = item.get("assistantReviewDraft", {})
            writer.writerow(
                {
                    "sourceDataset": item.get("sourceDataset", ""),
                    "id": item.get("id", ""),
                    "company": item.get("company", ""),
                    "title": item.get("title", ""),
                    "roleGroup": item.get("roleGroup", ""),
                    "clusterId": item.get("clusterId", ""),
                    "clusterLabel": item.get("clusterLabel", ""),
                    "active": "TRUE" if item.get("active") else "FALSE",
                    "currentSummary": item.get("current", {}).get("summary", ""),
                    "currentFocusLabel": item.get("current", {}).get("focusLabel", ""),
                    "currentKeywords": compact(item.get("current", {}).get("keywords", [])),
                    "currentQuality": item.get("current", {}).get("quality", ""),
                    "detailBody": item.get("source", {}).get("detailBody", ""),
                    "tasks": compact(item.get("source", {}).get("tasks", [])),
                    "requirements": compact(item.get("source", {}).get("requirements", [])),
                    "preferred": compact(item.get("source", {}).get("preferred", [])),
                    "skills": compact(item.get("source", {}).get("skills", [])),
                    "machinePriority": item.get("machineReview", {}).get("priority", ""),
                    "machineScore": item.get("machineReview", {}).get("score", ""),
                    "machineIssues": issues_text(item.get("machineReview", {}).get("issues", [])),
                    "controlSample": "TRUE" if item.get("machineReview", {}).get("controlSample") else "FALSE",
                    "assistantSummary": assistant_prefill.get("summary", ""),
                    "assistantFocusLabel": assistant_prefill.get("focusLabel", ""),
                    "assistantKeywords": compact(assistant_prefill.get("keywords", [])),
                    "assistantQuality": assistant_prefill.get("quality", ""),
                    "assistantNotes": assistant_prefill.get("notes", ""),
                    "assistantDraftSummaryPass": assistant_draft.get("summaryPass", ""),
                    "assistantDraftFocusLabelPass": assistant_draft.get("focusLabelPass", ""),
                    "assistantDraftKeywordsPass": assistant_draft.get("keywordsPass", ""),
                    "assistantDraftOverallPass": assistant_draft.get("overallPass", ""),
                    "assistantDraftCorrectedSummary": assistant_draft.get("correctedSummary", ""),
                    "assistantDraftCorrectedFocusLabel": assistant_draft.get("correctedFocusLabel", ""),
                    "assistantDraftCorrectedKeywords": compact(assistant_draft.get("correctedKeywords", [])),
                    "assistantDraftCorrectedQuality": assistant_draft.get("correctedQuality", ""),
                    "assistantDraftNotes": assistant_draft.get("notes", ""),
                    "reviewSummaryPass": item.get("review", {}).get("summaryPass", ""),
                    "reviewFocusLabelPass": item.get("review", {}).get("focusLabelPass", ""),
                    "reviewKeywordsPass": item.get("review", {}).get("keywordsPass", ""),
                    "reviewOverallPass": item.get("review", {}).get("overallPass", ""),
                    "correctedSummary": item.get("review", {}).get("correctedSummary", ""),
                    "correctedFocusLabel": item.get("review", {}).get("correctedFocusLabel", ""),
                    "correctedKeywords": compact(item.get("review", {}).get("correctedKeywords", [])),
                    "correctedQuality": item.get("review", {}).get("correctedQuality", ""),
                    "reviewNotes": item.get("review", {}).get("notes", ""),
                }
            )

    print(f"Wrote review CSV to {output_path}")


if __name__ == "__main__":
    main()
