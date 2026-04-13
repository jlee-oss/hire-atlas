#!/usr/bin/env python3

import argparse
import json
import pathlib


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_OUTPUT_PATH = ROOT / "docs" / "review_wave_001_brief.md"


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def clean(value: str) -> str:
    return " ".join(str(value or "").strip().split())


def compact(values, limit=5) -> str:
    seen = []
    for value in values or []:
        item = clean(value)
        if not item or item in seen:
            continue
        seen.append(item)
        if len(seen) >= limit:
            break
    return ", ".join(seen)


def issue_line(item: dict) -> str:
    return ", ".join(issue.get("code", "") for issue in item.get("machineReview", {}).get("issues", []))


def build_content(wave: dict, topn: int) -> str:
    items = wave.get("items", [])[:topn]
    lines = [
        "# 리뷰 웨이브 브리프",
        "",
        f"- generatedAt: `{wave.get('generatedAt', '')}`",
        f"- 총 검수 대상: `{len(wave.get('items', []))}`",
        f"- 브리프 표시 수: `{len(items)}`",
        "",
    ]
    for index, item in enumerate(items, start=1):
        lines.extend(
            [
                f"## {index}. {item.get('company', '')} | {item.get('title', '')}",
                "",
                f"- dataset: `{item.get('sourceDataset', '')}`",
                f"- role: `{item.get('roleGroup', '')}`",
                f"- priority: `{item.get('machineReview', {}).get('priority', '')}`",
                f"- current quality: `{item.get('current', {}).get('quality', '')}`",
                f"- current focus: `{item.get('current', {}).get('focusLabel', '')}`",
                f"- current summary: {item.get('current', {}).get('summary', '')}",
                f"- current keywords: {compact(item.get('current', {}).get('keywords', []), limit=6)}",
                f"- machine issues: {issue_line(item)}",
                f"- tasks: {compact(item.get('source', {}).get('tasks', []), limit=4)}",
                f"- requirements: {compact(item.get('source', {}).get('requirements', []), limit=4)}",
                f"- skills: {compact(item.get('source', {}).get('skills', []), limit=6)}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--topn", type=int, default=12)
    args = parser.parse_args()

    wave = load_json(pathlib.Path(args.wave))
    content = build_content(wave, args.topn)
    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")
    print(f"Wrote review brief to {output_path}")


if __name__ == "__main__":
    main()
