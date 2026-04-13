#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
QUALITY_LOOP_SCRIPT = ROOT / "scripts" / "run_quality_optimization_loop.py"
DEFAULT_CONFIG_PATH = ROOT / "data" / "quality_optimization_loop_config.json"
LATEST_STATE_PATH = ROOT / "data" / "quality_iterations" / "latest_state.json"
CONTINUOUS_STATE_PATH = ROOT / "data" / "quality_iterations" / "continuous_loop_state.json"
CONTINUOUS_LOG_PATH = ROOT / "logs" / "continuous_quality_loop.ndjson"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def append_log(payload: dict) -> None:
    CONTINUOUS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CONTINUOUS_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def all_targets_passed(latest_state: dict) -> bool:
    statuses = (((latest_state.get("metrics") or {}).get("targetStatus")) or {})
    return bool(statuses) and all((item or {}).get("passed") for item in statuses.values())


def run_one_cycle(args: argparse.Namespace, cycle: int) -> dict:
    command = [
        sys.executable,
        str(QUALITY_LOOP_SCRIPT),
        "--config",
        str(args.config),
        "--max-iterations",
        str(args.per_run_iterations),
    ]
    if args.base_url:
        command.extend(["--base-url", args.base_url])
    if args.model:
        command.extend(["--model", args.model])
    if args.api_key:
        command.extend(["--api-key", args.api_key])
    if args.candidate_profile:
        command.extend(["--candidate-profile", args.candidate_profile])
    if args.compare_to:
        command.extend(["--compare-to", args.compare_to])

    started_at = now_iso()
    result = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
    )
    latest_state = load_json(LATEST_STATE_PATH, {}) or {}
    metrics = latest_state.get("metrics", {}) if isinstance(latest_state.get("metrics", {}), dict) else {}
    cycle_state = {
        "cycle": cycle,
        "startedAt": started_at,
        "completedAt": now_iso(),
        "returnCode": result.returncode,
        "qualityLoopStdout": result.stdout.strip(),
        "qualityLoopStderr": result.stderr.strip(),
        "latestIteration": latest_state.get("iteration"),
        "latestStatus": latest_state.get("status", "unknown"),
        "optimizationScore": float(metrics.get("optimizationScore", 0.0) or 0.0),
        "targetsPassed": all_targets_passed(latest_state),
        "latestStatePath": str(LATEST_STATE_PATH),
    }
    return cycle_state


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default=str(DEFAULT_CONFIG_PATH))
    parser.add_argument("--per-run-iterations", type=int, default=3)
    parser.add_argument("--interval-seconds", type=int, default=300)
    parser.add_argument("--min-score", type=float, default=100.0)
    parser.add_argument("--max-cycles", type=int, default=0)
    parser.add_argument("--base-url", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--candidate-profile", default="")
    parser.add_argument("--compare-to", default="")
    args = parser.parse_args()
    args.config = Path(args.config)

    final_state = None
    cycle = 0
    while True:
        cycle += 1
        cycle_state = run_one_cycle(args, cycle)
        should_stop = (
            cycle_state["returnCode"] == 0
            and cycle_state["targetsPassed"]
            and cycle_state["optimizationScore"] >= args.min_score
        )
        cycle_state["stopReason"] = "criteria_met" if should_stop else ""
        if args.max_cycles and cycle >= args.max_cycles and not should_stop:
            should_stop = True
            cycle_state["stopReason"] = "max_cycles_reached"

        write_json(CONTINUOUS_STATE_PATH, cycle_state)
        append_log(cycle_state)
        print(json.dumps(cycle_state, ensure_ascii=False), flush=True)
        final_state = cycle_state

        if should_stop:
            break
        time.sleep(max(1, args.interval_seconds))

    if final_state and final_state["returnCode"] != 0:
        raise SystemExit(final_state["returnCode"])


if __name__ == "__main__":
    main()
