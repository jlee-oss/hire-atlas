#!/usr/bin/env python3

import argparse
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PATH = ROOT / "data" / "service_scope_guard_recovery_candidates_001.json"


def clean_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def load_ids(path: Path) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    ids = []
    seen = set()
    for item in payload.get("items", []):
        job_id = clean_text(item.get("id", ""))
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)
        ids.append(job_id)
    return ids


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", type=Path, default=DEFAULT_PATH)
    parser.add_argument("--format", choices=["csv", "lines", "json"], default="csv")
    args = parser.parse_args()

    ids = load_ids(args.path)
    if args.format == "lines":
        print("\n".join(ids))
        return
    if args.format == "json":
        print(json.dumps(ids, ensure_ascii=False, indent=2))
        return
    print(",".join(ids))


if __name__ == "__main__":
    main()
