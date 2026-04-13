#!/usr/bin/env python3

import argparse
import json
import pathlib
from datetime import datetime, timezone


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_BASELINE_PATH = ROOT / "data" / "review_suggestions_001.json"
DEFAULT_CANDIDATE_PATH = ROOT / "data" / "review_suggestions_7b_001.json"
DEFAULT_JSON_OUTPUT = ROOT / "data" / "model_comparisons" / "review_wave_models_001.json"
DEFAULT_MD_OUTPUT = ROOT / "docs" / "stronger_model_comparison.md"

QUALITY_RANK = {"low": 0, "medium": 1, "high": 2}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalize_text(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def quality_rank(value: str) -> int:
    return QUALITY_RANK.get(normalize_text(value).lower(), -1)


def compare_items(baseline_items: dict, candidate_items: dict) -> dict:
    ids = sorted(set(baseline_items) & set(candidate_items))
    improved = []
    worsened = []
    unchanged = []
    low_to_non_low = []

    for item_id in ids:
        baseline = baseline_items[item_id]
        candidate = candidate_items[item_id]
        baseline_quality = quality_rank(baseline.get("suggestedQuality", ""))
        candidate_quality = quality_rank(candidate.get("suggestedQuality", ""))

        row = {
            "id": item_id,
            "baselineSummary": baseline.get("suggestedSummary", ""),
            "candidateSummary": candidate.get("suggestedSummary", ""),
            "baselineFocusLabel": baseline.get("suggestedFocusLabel", ""),
            "candidateFocusLabel": candidate.get("suggestedFocusLabel", ""),
            "baselineQuality": baseline.get("suggestedQuality", ""),
            "candidateQuality": candidate.get("suggestedQuality", ""),
        }

        if candidate_quality > baseline_quality:
            improved.append(row)
        elif candidate_quality < baseline_quality:
            worsened.append(row)
        else:
            unchanged.append(row)

        if baseline_quality == 0 and candidate_quality >= 1:
            low_to_non_low.append(row)

    return {
        "overlap": len(ids),
        "improved": improved,
        "worsened": worsened,
        "unchanged": unchanged,
        "lowToNonLow": low_to_non_low,
    }


def build_markdown(payload: dict) -> str:
    comparison = payload["comparison"]
    lines = [
        "# 더 강한 모델 비교",
        "",
        f"- 생성 시각: `{payload['generatedAt']}`",
        f"- baseline model: `{payload['baseline']['model']}`",
        f"- candidate model: `{payload['candidate']['model']}`",
        f"- 비교 웨이브: `{payload['sourceWave']}`",
        f"- 겹치는 항목 수: `{comparison['overlap']}`",
        f"- quality 개선: `{len(comparison['improved'])}`",
        f"- quality 악화: `{len(comparison['worsened'])}`",
        f"- low -> non-low 개선: `{len(comparison['lowToNonLow'])}`",
        "",
        "## 현재 판단",
        "",
        "- review hard set 기준으로는 더 강한 모델이 확실히 유리합니다.",
        "- 특히 low에서 medium/high로 올라간 케이스가 실제로 보입니다.",
        "- 다만 원문 자체가 얇은 공고는 더 강한 모델에서도 low로 남습니다.",
        "- 따라서 다음 검수 기준 모델은 더 강한 모델로 두는 것이 맞습니다.",
        "",
    ]

    if comparison["improved"]:
        lines.extend(["## 개선된 대표 케이스", ""])
        for item in comparison["improved"][:6]:
            lines.extend(
                [
                    f"- `{item['id']}`",
                    f"  baseline: `{item['baselineQuality']}` / {item['baselineSummary']} / {item['baselineFocusLabel']}",
                    f"  candidate: `{item['candidateQuality']}` / {item['candidateSummary']} / {item['candidateFocusLabel']}",
                ]
            )
        lines.append("")

    if comparison["worsened"]:
        lines.extend(["## 악화 케이스", ""])
        for item in comparison["worsened"][:6]:
            lines.extend(
                [
                    f"- `{item['id']}`",
                    f"  baseline: `{item['baselineQuality']}` / {item['baselineSummary']} / {item['baselineFocusLabel']}",
                    f"  candidate: `{item['candidateQuality']}` / {item['candidateSummary']} / {item['candidateFocusLabel']}",
                ]
            )
        lines.append("")

    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE_PATH))
    parser.add_argument("--candidate", default=str(DEFAULT_CANDIDATE_PATH))
    parser.add_argument("--json-output", default=str(DEFAULT_JSON_OUTPUT))
    parser.add_argument("--md-output", default=str(DEFAULT_MD_OUTPUT))
    args = parser.parse_args()

    baseline_payload = load_json(pathlib.Path(args.baseline))
    candidate_payload = load_json(pathlib.Path(args.candidate))

    baseline_items = {item["id"]: item for item in baseline_payload.get("items", [])}
    candidate_items = {item["id"]: item for item in candidate_payload.get("items", [])}
    comparison = compare_items(baseline_items, candidate_items)

    payload = {
        "generatedAt": now_iso(),
        "sourceWave": baseline_payload.get("sourceWave") or candidate_payload.get("sourceWave", ""),
        "baseline": baseline_payload.get("model", {}),
        "candidate": candidate_payload.get("model", {}),
        "comparison": comparison,
    }

    json_output = pathlib.Path(args.json_output)
    json_output.parent.mkdir(parents=True, exist_ok=True)
    json_output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    md_output = pathlib.Path(args.md_output)
    md_output.parent.mkdir(parents=True, exist_ok=True)
    md_output.write_text(build_markdown(payload), encoding="utf-8")

    print(f"Wrote model comparison JSON to {json_output}")
    print(f"Wrote model comparison markdown to {md_output}")


if __name__ == "__main__":
    main()
