#!/usr/bin/env python3

import argparse
import json
import pathlib
from collections import Counter


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_INPUT_PATH = ROOT / "data" / "structured_signal_validation_review_001.json"
DEFAULT_OUTPUT_PATH = ROOT / "docs" / "structured_signal_validation_comparison_report_001.md"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def normalized(payload: dict) -> tuple[tuple[str, ...], ...]:
    return (
        tuple(payload.get("domainSignals", []) or []),
        tuple(payload.get("problemSignals", []) or []),
        tuple(payload.get("systemSignals", []) or []),
        tuple(payload.get("dataSignals", []) or []),
        tuple(payload.get("workflowSignals", []) or []),
    )


def classify(item: dict) -> str:
    if not item.get("resolved"):
        return "unresolved"
    expected = normalized(item.get("expected", {}))
    current = normalized(item.get("current", {}))
    suggested = normalized(item.get("suggested", {}))

    if expected == suggested:
        return "suggested_signals"
    if expected == current:
        return "current_signals"
    if expected == ((), (), (), (), ()):
        return "keep_low"
    return "manual_override"


def build_report(payload: dict) -> str:
    items = payload.get("items", [])
    classifications = Counter(classify(item) for item in items)
    reason_counts = Counter(item.get("reason", "") for item in items if item.get("resolved"))

    lines = [
        "# Structured Signal 비교 리포트 001",
        "",
        f"- 전체 항목: `{len(items)}`",
        f"- resolved: `{len([item for item in items if item.get('resolved')])}`",
        f"- unresolved: `{classifications['unresolved']}`",
        "",
        "## 채택 기준 분포",
        "",
        f"- `suggested_signals`: `{classifications['suggested_signals']}`",
        f"- `current_signals`: `{classifications['current_signals']}`",
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
    if classifications["suggested_signals"] > classifications["current_signals"]:
        lines.append("- 현재 표본에서는 새 structured signal 제안이 현재 저장 신호보다 더 자주 채택됩니다.")
    else:
        lines.append("- 현재 표본에서는 suggested와 current의 우열이 아직 분명하지 않습니다.")
    if classifications["keep_low"]:
        lines.append("- 신호를 억지로 채우지 말아야 하는 low 케이스가 분명히 존재합니다.")
    if classifications["unresolved"]:
        lines.append("- unresolved 항목은 사람이 직접 structured signal을 확정해야 합니다.")
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
    print(f"Wrote structured signal comparison report to {output_path}")


if __name__ == "__main__":
    main()
