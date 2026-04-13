#!/usr/bin/env python3

import argparse
import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GOLDSET_PATH = ROOT / "data" / "service_scope_goldset_001.json"
DEFAULT_MODEL_REVIEW_OUTPUT = ROOT / "data" / "service_scope_model_review_incremental_latest.json"
DEFAULT_BENCHMARK_OUTPUT = ROOT / "data" / "service_scope_model_benchmark_incremental_latest.json"
DEFAULT_BENCHMARK_MD_OUTPUT = ROOT / "docs" / "service_scope_model_benchmark_incremental_latest.md"
DEFAULT_SHADOW_OUTPUT = ROOT / "data" / "service_scope_shadow_guard_off_incremental_latest.json"
DEFAULT_SHADOW_MD_OUTPUT = ROOT / "docs" / "service_scope_shadow_guard_off_incremental_latest.md"
DEFAULT_GATE_OUTPUT = ROOT / "data" / "model_improvement_gate_incremental_latest.json"
DEFAULT_GATE_MD_OUTPUT = ROOT / "docs" / "model_improvement_gate_incremental_latest.md"
DEFAULT_SUMMARY_OUTPUT = ROOT / "data" / "incremental_service_scope_pipeline_latest.json"
DEFAULT_SUMMARY_MD_OUTPUT = ROOT / "docs" / "incremental_service_scope_pipeline_latest.md"
SERVICE_SCOPE_OVERRIDES_PATH = ROOT / "data" / "service_scope_overrides.json"
BACKUP_DIR = ROOT / "data" / "model_improvement_backups"
LATEST_STATE_PATH = ROOT / "data" / "quality_iterations" / "latest_state.json"
FINAL_PACKAGE_JSON_PATH = ROOT / "data" / "final_confirmation_package_001.json"
FINAL_PACKAGE_MD_PATH = ROOT / "docs" / "final_confirmation_package_001.md"


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean_text(value) -> str:
    return " ".join(str(value or "").split()).strip()


def resolve_path(value: str | Path) -> Path:
    path = Path(value)
    return path if path.is_absolute() else ROOT / path


def load_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_stdout_json(stdout: str) -> dict:
    text = stdout.strip()
    if not text:
        return {}
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end < start:
        return {}
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return {}


def run_command(
    args: list[str],
    *,
    env: dict[str, str] | None = None,
    check: bool = True,
    sensitive: bool = False,
) -> dict:
    started_at = now_iso()
    result = subprocess.run(
        args,
        cwd=ROOT,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    record = {
        "command": [Path(args[0]).name, *args[1:]] if sensitive else args,
        "startedAt": started_at,
        "finishedAt": now_iso(),
        "returnCode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }
    if check and result.returncode != 0:
        raise RuntimeError(json.dumps(record, ensure_ascii=False, indent=2))
    return record


def split_job_ids(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


def load_job_ids(args) -> list[str]:
    job_ids = split_job_ids(args.job_ids or "")
    if args.job_ids_file:
        path = resolve_path(args.job_ids_file)
        if path.exists():
            for line in path.read_text(encoding="utf-8").splitlines():
                cleaned = clean_text(line)
                if cleaned and not cleaned.startswith("#"):
                    job_ids.extend(split_job_ids(cleaned))
    seen = set()
    unique = []
    for job_id in job_ids:
        if job_id not in seen:
            seen.add(job_id)
            unique.append(job_id)
    return unique


def ensure_model_review(args, job_ids: list[str], commands: list[dict]) -> dict:
    model_review_output = resolve_path(args.model_review_output)
    if args.skip_model_review:
        if not model_review_output.exists():
            raise SystemExit(f"--skip-model-review requires existing model review output: {model_review_output}")
        return {
            "ran": False,
            "reason": "skip_model_review",
            "output": str(model_review_output),
        }

    if not job_ids:
        raise SystemExit("Refusing to call model API without --job-ids or --job-ids-file. Use --skip-model-review for report-only.")

    base_url = args.base_url or os.environ.get("COMPANY_INSIGHT_BASE_URL", "")
    model = args.model or os.environ.get("COMPANY_INSIGHT_MODEL", "")
    api_key = os.environ.get(args.api_key_env, "")
    if not base_url or not model or not api_key:
        raise SystemExit(
            "Model review requires COMPANY_INSIGHT_BASE_URL, COMPANY_INSIGHT_MODEL, "
            f"and {args.api_key_env} in the environment."
        )

    env = os.environ.copy()
    env["COMPANY_INSIGHT_BASE_URL"] = base_url
    env["COMPANY_INSIGHT_MODEL"] = model
    env["COMPANY_INSIGHT_API_KEY"] = api_key
    if args.ssl_cert_file:
        env["SSL_CERT_FILE"] = args.ssl_cert_file

    command = [
        sys.executable,
        str(ROOT / "scripts" / "classify_service_scope_candidates.py"),
        "--base-url",
        base_url,
        "--model",
        model,
        "--mode",
        "all",
        "--job-ids",
        ",".join(job_ids),
        "--batch-size",
        str(args.batch_size),
        "--output",
        str(model_review_output),
        "--no-apply",
    ]
    record = run_command(command, env=env, sensitive=True)
    commands.append(record)
    return {
        "ran": True,
        "candidateJobIds": job_ids,
        "output": str(model_review_output),
        "stdout": record["stdout"],
    }


def run_reports(args, commands: list[dict]) -> dict:
    goldset = resolve_path(args.goldset)
    model_review = resolve_path(args.model_review_output)
    benchmark_output = resolve_path(args.benchmark_output)
    benchmark_md_output = resolve_path(args.benchmark_md_output)
    shadow_output = resolve_path(args.shadow_output)
    shadow_md_output = resolve_path(args.shadow_md_output)
    gate_output = resolve_path(args.gate_output)
    gate_md_output = resolve_path(args.gate_md_output)

    report_commands = [
        [
            sys.executable,
            str(ROOT / "scripts" / "run_service_scope_goldset_benchmark.py"),
            "--source",
            "model-review",
            "--goldset",
            str(goldset),
            "--model-review-path",
            str(model_review),
            "--output",
            str(benchmark_output),
            "--md-output",
            str(benchmark_md_output),
        ],
        [
            sys.executable,
            str(ROOT / "scripts" / "run_service_scope_shadow_guard_off.py"),
            "--source",
            "model-review",
            "--model-review-path",
            str(model_review),
            "--goldset",
            str(goldset),
            "--output",
            str(shadow_output),
            "--md-output",
            str(shadow_md_output),
        ],
        [sys.executable, str(ROOT / "scripts" / "run_quality_optimization_loop.py")],
        [
            sys.executable,
            str(ROOT / "scripts" / "run_model_improvement_gate.py"),
            "--latest-state",
            str(LATEST_STATE_PATH),
            "--goldset",
            str(goldset),
            "--benchmark",
            str(benchmark_output),
            "--shadow",
            str(shadow_output),
            "--output",
            str(gate_output),
            "--md-output",
            str(gate_md_output),
        ],
        [sys.executable, str(ROOT / "scripts" / "build_final_confirmation_package.py")],
    ]
    for command in report_commands:
        commands.append(run_command(command))

    return {
        "goldset": str(goldset),
        "modelReview": str(model_review),
        "benchmarkJson": str(benchmark_output),
        "benchmarkMd": str(benchmark_md_output),
        "shadowJson": str(shadow_output),
        "shadowMd": str(shadow_md_output),
        "gateJson": str(gate_output),
        "gateMd": str(gate_md_output),
        "latestState": str(LATEST_STATE_PATH),
        "finalPackageJson": str(FINAL_PACKAGE_JSON_PATH),
        "finalPackageMd": str(FINAL_PACKAGE_MD_PATH),
    }


def apply_dry_run(goldset: Path, commands: list[dict]) -> dict:
    command = [
        sys.executable,
        str(ROOT / "scripts" / "apply_service_scope_goldset.py"),
        "--goldset",
        str(goldset),
    ]
    record = run_command(command, check=False)
    commands.append(record)
    return {
        "passed": record["returnCode"] == 0,
        "returnCode": record["returnCode"],
        "result": parse_stdout_json(record["stdout"]),
        "stderr": record["stderr"],
    }


def gate_passed(gate_path: Path) -> bool:
    gate = load_json(gate_path, {}) or {}
    return bool(gate.get("passed", False))


def quality_passed() -> bool:
    latest = load_json(LATEST_STATE_PATH, {}) or {}
    metrics = latest.get("metrics", {}) if isinstance(latest.get("metrics", {}), dict) else {}
    return latest.get("status") == "converged" and float(metrics.get("optimizationScore", 0) or 0) >= 100.0


def canonical_goldset(path: Path) -> bool:
    return path.resolve() == DEFAULT_GOLDSET_PATH.resolve()


def apply_if_allowed(args, artifacts: dict, dry_run: dict, commands: list[dict]) -> dict:
    if not args.apply:
        return {
            "requested": False,
            "applied": False,
            "reason": "default_no_apply",
        }

    goldset = resolve_path(args.goldset)
    gate_path = resolve_path(args.gate_output)
    if not canonical_goldset(goldset) and not args.allow_noncanonical_apply:
        return {
            "requested": True,
            "applied": False,
            "blocked": True,
            "reason": "noncanonical_goldset",
            "detail": "Refusing --apply with non-canonical --goldset. Pass --allow-noncanonical-apply to override.",
        }
    if not dry_run.get("passed"):
        return {
            "requested": True,
            "applied": False,
            "blocked": True,
            "reason": "apply_dry_run_failed",
        }
    if not gate_passed(gate_path):
        return {
            "requested": True,
            "applied": False,
            "blocked": True,
            "reason": "model_gate_failed",
        }
    if not quality_passed():
        return {
            "requested": True,
            "applied": False,
            "blocked": True,
            "reason": "quality_not_converged",
        }

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"service_scope_overrides_before_incremental_apply_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.json"
    shutil.copy2(SERVICE_SCOPE_OVERRIDES_PATH, backup_path)

    apply_record = run_command(
        [
            sys.executable,
            str(ROOT / "scripts" / "apply_service_scope_goldset.py"),
            "--goldset",
            str(goldset),
            "--apply",
        ],
        check=False,
    )
    commands.append(apply_record)
    if apply_record["returnCode"] != 0:
        return {
            "requested": True,
            "applied": False,
            "blocked": True,
            "reason": "apply_command_failed",
            "stderr": apply_record["stderr"],
            "backupPath": str(backup_path),
        }

    try:
        post_artifacts = run_reports(args, commands)
        if not gate_passed(resolve_path(args.gate_output)) or not quality_passed():
            shutil.copy2(backup_path, SERVICE_SCOPE_OVERRIDES_PATH)
            run_command([sys.executable, str(ROOT / "scripts" / "run_quality_optimization_loop.py")], check=False)
            run_command([sys.executable, str(ROOT / "scripts" / "build_final_confirmation_package.py")], check=False)
            return {
                "requested": True,
                "applied": False,
                "blocked": True,
                "rolledBack": True,
                "reason": "post_apply_gate_failed",
                "backupPath": str(backup_path),
            }
    except Exception as exc:
        if SERVICE_SCOPE_OVERRIDES_PATH.exists() and backup_path.exists():
            shutil.copy2(backup_path, SERVICE_SCOPE_OVERRIDES_PATH)
        run_command([sys.executable, str(ROOT / "scripts" / "run_quality_optimization_loop.py")], check=False)
        run_command([sys.executable, str(ROOT / "scripts" / "build_final_confirmation_package.py")], check=False)
        return {
            "requested": True,
            "applied": False,
            "blocked": True,
            "rolledBack": True,
            "reason": "post_apply_exception",
            "detail": str(exc),
            "backupPath": str(backup_path),
        }

    return {
        "requested": True,
        "applied": True,
        "backupPath": str(backup_path),
        "applyResult": parse_stdout_json(apply_record["stdout"]),
        "postApplyArtifacts": post_artifacts,
    }


def render_summary_md(summary: dict) -> str:
    gate = summary.get("gate", {})
    quality = summary.get("quality", {})
    apply = summary.get("apply", {})
    artifacts = summary.get("artifacts", {})
    lines = [
        "# Incremental Service Scope Pipeline Latest",
        "",
        f"- generatedAt: `{summary['generatedAt']}`",
        f"- status: `{summary['status']}`",
        f"- mode: `{summary['mode']}`",
        f"- gatePassed: `{gate.get('passed', False)}`",
        f"- qualityStatus: `{quality.get('status', 'missing')}`",
        f"- optimizationScore: `{quality.get('optimizationScore', 0)}`",
        f"- applyRequested: `{apply.get('requested', False)}`",
        f"- applied: `{apply.get('applied', False)}`",
        "",
        "## Artifacts",
        "",
    ]
    for key, value in artifacts.items():
        lines.append(f"- {key}: `{value}`")
    blockers = gate.get("blockers", [])
    if blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            lines.append(f"- {blocker}")
    return "\n".join(lines).rstrip() + "\n"


def build_summary(args, model_review_step, artifacts, dry_run, apply_result, commands) -> dict:
    gate = load_json(resolve_path(args.gate_output), {}) or {}
    latest = load_json(LATEST_STATE_PATH, {}) or {}
    metrics = latest.get("metrics", {}) if isinstance(latest.get("metrics", {}), dict) else {}
    status = "passed"
    if args.apply and not apply_result.get("applied"):
        status = "blocked"
    elif not bool(gate.get("passed", False)):
        status = "blocked"
    return {
        "generatedAt": now_iso(),
        "status": status,
        "mode": "apply" if args.apply else "dry-run",
        "defaultNoApply": not args.apply,
        "jobIds": load_job_ids(args),
        "modelReviewStep": model_review_step,
        "artifacts": artifacts,
        "quality": {
            "status": latest.get("status", "missing"),
            "iteration": latest.get("iteration"),
            "optimizationScore": metrics.get("optimizationScore"),
            "boardRows": metrics.get("boardRows"),
            "excludedJobs": metrics.get("excludedJobs"),
            "reviewJobs": metrics.get("reviewJobs"),
            "guardRecoveredRows": metrics.get("guardRecoveredRows"),
            "guardRecoveredHighQualityRows": metrics.get("guardRecoveredHighQualityRows"),
        },
        "gate": {
            "status": gate.get("status", "missing"),
            "passed": bool(gate.get("passed", False)),
            "blockers": gate.get("blockers", []),
        },
        "applyDryRun": dry_run,
        "apply": apply_result,
        "commands": commands,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-ids", default="")
    parser.add_argument("--job-ids-file")
    parser.add_argument("--changed-since", help="Reserved for future sheet/job diff discovery.")
    parser.add_argument("--skip-model-review", action="store_true")
    parser.add_argument("--model-review-output", default=str(DEFAULT_MODEL_REVIEW_OUTPUT))
    parser.add_argument("--goldset", default=str(DEFAULT_GOLDSET_PATH))
    parser.add_argument("--benchmark-output", default=str(DEFAULT_BENCHMARK_OUTPUT))
    parser.add_argument("--benchmark-md-output", default=str(DEFAULT_BENCHMARK_MD_OUTPUT))
    parser.add_argument("--shadow-output", default=str(DEFAULT_SHADOW_OUTPUT))
    parser.add_argument("--shadow-md-output", default=str(DEFAULT_SHADOW_MD_OUTPUT))
    parser.add_argument("--gate-output", default=str(DEFAULT_GATE_OUTPUT))
    parser.add_argument("--gate-md-output", default=str(DEFAULT_GATE_MD_OUTPUT))
    parser.add_argument("--summary-output", default=str(DEFAULT_SUMMARY_OUTPUT))
    parser.add_argument("--summary-md-output", default=str(DEFAULT_SUMMARY_MD_OUTPUT))
    parser.add_argument("--base-url", default=os.environ.get("COMPANY_INSIGHT_BASE_URL", ""))
    parser.add_argument("--model", default=os.environ.get("COMPANY_INSIGHT_MODEL", ""))
    parser.add_argument("--api-key-env", default="COMPANY_INSIGHT_API_KEY")
    parser.add_argument("--ssl-cert-file", default=os.environ.get("SSL_CERT_FILE", ""))
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--allow-noncanonical-apply", action="store_true")
    args = parser.parse_args()

    if args.changed_since:
        raise SystemExit("--changed-since is reserved until changed-job discovery is implemented.")

    commands = []
    job_ids = load_job_ids(args)
    model_review_step = ensure_model_review(args, job_ids, commands)
    artifacts = run_reports(args, commands)
    dry_run = apply_dry_run(resolve_path(args.goldset), commands)
    apply_result = apply_if_allowed(args, artifacts, dry_run, commands)
    summary = build_summary(args, model_review_step, artifacts, dry_run, apply_result, commands)

    summary_output = resolve_path(args.summary_output)
    summary_md_output = resolve_path(args.summary_md_output)
    write_json(summary_output, summary)
    write_text(summary_md_output, render_summary_md(summary))
    print(
        json.dumps(
            {
                "summaryJson": str(summary_output),
                "summaryMd": str(summary_md_output),
                "status": summary["status"],
                "mode": summary["mode"],
                "gatePassed": summary["gate"]["passed"],
                "applied": summary["apply"].get("applied", False),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    if summary["status"] != "passed":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
