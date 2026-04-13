#!/usr/bin/env python3

import argparse
import json
import pathlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = ROOT / "data" / "goldset_expansion_review_001.json"
DEFAULT_OUTPUT_PATH = ROOT / "docs" / "goldset_expansion_comparison_report_001.md"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized_payload(payload: dict) -> tuple[str, str, tuple[str, ...], str]:
    return (
        " ".join(str(payload.get("summary", "")).split()).strip(),
        " ".join(str(payload.get("focusLabel", "")).split()).strip(),
        tuple(" ".join(str(item).split()).strip() for item in (payload.get("keywords", []) or []) if str(item).strip()),
        " ".join(str(payload.get("quality", "")).split()).strip().lower(),
    )


def classify(item: dict) -> str:
    if not item.get("resolved"):
        return "unresolved"
    expected = normalized_payload(item.get("expected", {}))
    current = normalized_payload(item.get("current", {}))
    draft = normalized_payload(item.get("draft", {}))

    if expected == draft:
        return "board_projection"
    if expected == current:
        return "raw_extractor"
    if expected[3] == "low" and expected[0] == "" and expected[1] == "" and not expected[2]:
        return "keep_low"
    return "manual_override"


def build_report(payload: dict) -> str:
    items = payload.get("items", [])
    classifications = Counter(classify(item) for item in items)
    reason_counts = Counter(item.get("reason", "") for item in items if item.get("resolved"))

    lines = [
        "# 골드셋 확장 비교 리포트 001",
        "",
        f"- 전체 항목: `{len(items)}`",
        f"- resolved: `{classifications['board_projection'] + classifications['raw_extractor'] + classifications['keep_low'] + classifications['manual_override']}`",
        f"- unresolved: `{classifications['unresolved']}`",
        "",
        "## 채택 기준 분포",
        "",
        f"- `board_projection`: `{classifications['board_projection']}`",
        f"- `raw_extractor`: `{classifications['raw_extractor']}`",
        f"- `keep_low`: `{classifications['keep_low']}`",
        f"- `manual_override`: `{classifications['manual_override']}`",
        f"- `unresolved`: `{classifications['unresolved']}`",
        "",
        "## resolved 이유 분포",
        "",
    ]

    for key, count in sorted(reason_counts.items()):
        lines.append(f"- `{key}`: `{count}`")

    lines.extend(["", "## 해석", ""])
    if classifications["board_projection"] > classifications["raw_extractor"]:
        lines.append("- 현재 확장 골드셋에서는 `board projection`이 `raw extractor`보다 더 자주 채택되고 있습니다.")
    else:
        lines.append("- 현재 확장 골드셋에서는 `raw extractor`와 `board projection`의 우열이 아직 분명하지 않습니다.")
    if classifications["keep_low"]:
        lines.append("- low 유지가 필요한 공고가 분명히 존재하므로, 억지로 대표 라벨을 채우지 않는 전략을 유지해야 합니다.")
    if classifications["unresolved"]:
        lines.append("- unresolved 항목은 수동 결정이 필요하므로, 이 항목들이 다음 품질 개선의 핵심 샘플입니다.")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default=str(DEFAULT_INPUT_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    args = parser.parse_args()

    payload = load_json(pathlib.Path(args.input))
    content = build_report(payload)
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content + "\n", encoding="utf-8")
    print(content)
    print(f"Wrote comparison report to {output_path}")


if __name__ == "__main__":
    main()
