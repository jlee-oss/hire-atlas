#!/usr/bin/env python3

import argparse
import json
import pathlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = ROOT / "data" / "goldset_expansion_review_001.json"
DEFAULT_OUTPUT_PATH = ROOT / "docs" / "goldset_expansion_provisional_report_001.md"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def build_report(payload: dict) -> str:
    items = payload.get("items", [])
    decision_counts = Counter(item.get("decision", "") for item in items)
    reason_counts = Counter(item.get("reason", "") for item in items)
    resolved = [item for item in items if item.get("resolved")]
    unresolved = [item for item in items if not item.get("resolved")]

    lines = [
        "# 골드셋 확장 가정 반영 리포트 001",
        "",
        "- 이 문서는 현재 `goldset_expansion_decision_sheet_001.csv`의 결정값을 그대로 적용했을 때의 미리보기입니다.",
        f"- 전체 항목: `{len(items)}`",
        f"- resolved: `{len(resolved)}`",
        f"- unresolved: `{len(unresolved)}`",
        "",
        "## 결정 분포",
        "",
    ]
    for key, count in sorted(decision_counts.items()):
        lines.append(f"- `{key}`: `{count}`")
    lines.extend(["", "## 이유 분포", ""])
    for key, count in sorted(reason_counts.items()):
        lines.append(f"- `{key}`: `{count}`")

    if unresolved:
        lines.extend(["", "## unresolved", ""])
        for item in unresolved:
            lines.append(
                f"- `{item['company']}` | `{item['title']}` | 권장 `{item.get('recommendedDecision', '')}` | 현재 결정 `{item.get('decision', '')}`"
            )

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
    output_path.write_text(content, encoding="utf-8")
    print(content)
    print(f"Wrote provisional report to {output_path}")


if __name__ == "__main__":
    main()
