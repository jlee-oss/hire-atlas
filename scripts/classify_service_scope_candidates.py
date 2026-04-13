#!/usr/bin/env python3

import argparse
import json
import os
import re
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from ai_runtime import (
    JOBS_PATH,
    compact_job_for_summary,
    compute_service_scope_signature,
    extract_json_object,
)
from build_summary_board import (
    build_base_rows,
    explain_service_scope_row,
    load_service_scope_override_store,
    resolve_service_scope_override,
    save_service_scope_override_store,
)


ROOT = JOBS_PATH.parent.parent
DEFAULT_OUTPUT_PATH = ROOT / "data" / "service_scope_model_review.json"
ALLOWED_ROLES = [
    "인공지능 엔지니어",
    "인공지능 리서처",
    "데이터 사이언티스트",
    "데이터 분석가",
    "기타",
]
PRIMARY_ALLOWED_ROLES = ALLOWED_ROLES[:4]
ANALYST_FAMILY_INCLUDE_PATTERNS = [
    r"\bcrm\b",
    r"\bcx\b",
    r"\bpmo\b",
    r"growth",
    r"performance marketer",
    r"data analyst",
    r"business analyst",
    r"business insight",
    r"user behavior",
    r"monetization analyst",
    r"fraud(?:\s*&\s*|\s+and\s+)?risk",
    r"데이터 분석\s*pm",
    r"\bfp&a\b",
    r"financial planning",
    r"손익",
    r"재무 모델",
    r"process innovation",
    r"전사 프로세스",
    r"프로세스 설계",
    r"\berp\b",
    r"\bkpi\b",
    r"\bokr\b",
    r"플랫폼 운영",
    r"작품 운영",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def is_analyst_family_candidate(candidate: dict) -> bool:
    title = " ".join(
        [
            str(candidate.get("title", "")).strip().lower(),
            str(candidate.get("summary", "")).strip().lower(),
            " ".join(str(value).strip().lower() for value in (candidate.get("keywords") or [])),
        ]
    )
    return any(re.search(pattern, title) for pattern in ANALYST_FAMILY_INCLUDE_PATTERNS)


def normalize_item(item: dict, candidate: dict) -> dict:
    decision = str(item.get("decision", "")).strip().lower()
    if decision not in {"include", "review", "exclude"}:
        decision = "review"

    confidence = str(item.get("confidence", "")).strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    mapped_role = str(item.get("mappedRole", "")).strip()
    if mapped_role not in ALLOWED_ROLES:
        mapped_role = candidate.get("currentRole", "") or "기타"
        if mapped_role not in ALLOWED_ROLES:
            mapped_role = "기타"
    current_role = str(candidate.get("currentRole", "")).strip()
    if is_analyst_family_candidate(candidate):
        decision = "include"
        mapped_role = "데이터 분석가"
        if confidence == "low":
            confidence = "medium"
    if decision == "include" and mapped_role not in PRIMARY_ALLOWED_ROLES:
        fallback_role = candidate.get("currentRole", "")
        mapped_role = fallback_role if fallback_role in PRIMARY_ALLOWED_ROLES else "인공지능 엔지니어"
    if decision == "include" and confidence == "low" and current_role in PRIMARY_ALLOWED_ROLES and mapped_role not in PRIMARY_ALLOWED_ROLES:
        mapped_role = current_role

    reason = " ".join(str(item.get("reason", "")).strip().split())[:80]

    return {
        "id": candidate["id"],
        "decision": decision,
        "confidence": confidence,
        "mappedRole": mapped_role,
        "reason": reason,
        "signature": candidate["signature"],
    }


def build_messages(candidates: list[dict]) -> list[dict]:
    system_prompt = (
        "당신은 한국어 AI/데이터 채용 보드의 직무 범위 분류기입니다. "
        "목표는 데이터 손실을 막는 보수적 3분류입니다. "
        "각 공고가 서비스 범위에 포함되는지와, 포함된다면 어떤 역할군으로 봐야 하는지를 판정하세요. "
        "decision 정책: include / review / exclude 중 하나만 고릅니다. "
        "include 기준: 실제 핵심 업무가 AI 모델 엔지니어링/리서치, AI 플랫폼/서빙/MLOps, 생성형 AI 애플리케이션, 데이터 사이언스, 데이터 분석에 직접 해당합니다. "
        "review 기준: AI/data/deeptech 신호가 있지만 주 업무가 범위 안팎 어디인지 확정하기 어렵거나, exclude가 false negative를 만들 위험이 있으면 review로 둡니다. "
        "exclude 기준: strong non-scope 근거가 명확할 때만 씁니다. PM/PO, 영업, 디자인, 리크루팅, 행정, 보안점검, 일반 QA, 일반 웹/서비스 개발처럼 AI/data/deeptech 신호가 주변 문맥에 그치는 경우입니다. "
        "중요: include/review 대상을 exclude 하는 것은 critical false negative입니다. 애매하면 exclude가 아니라 review입니다. "
        "중요: 직무 정보가 부족하거나 summary/detail/tasks가 비어 있으면 exclude가 아니라 review입니다. 정보 부족은 strong non-scope 근거가 아닙니다. "
        "중요: 제목만 보지 말고 detailBody, tasks, requirements, preferred, skills까지 보고 판단하세요. "
        "AI 플랫폼, LLM 서빙, 추천 시스템, 생성형 AI 애플리케이션, AI Solution Architect, AI DevOps, 모델 배포 인프라는 include 할 수 있습니다. "
        "AI 반도체, NPU, SoC, RTL, SDK, 컴파일러, 드라이버, 펌웨어, 임베디드, IP/SoC 검증은 AI/deeptech 인접성이 있으면 include 또는 review 후보입니다. "
        "의료 AI, SaMD, 의료 영상, 생체신호, 데이터 수집/품질/거버넌스 시스템은 AI/data 적용 맥락이 있으면 include 또는 review 후보입니다. "
        "일반 application engineer, field engineer, DevOps, backend, frontend라도 AI 제품/AI SDK/NPU/의료 AI/데이터 시스템과 직접 연결되면 hard exclude 하지 말고 include 또는 review로 둡니다. "
        "반대로 일반 DevOps, 일반 클라우드 인프라, 일반 백엔드 서버, 일반 SW 검증이 AI/data/deeptech 제품이나 데이터 시스템과 직접 연결되지 않으면 exclude 할 수 있습니다. "
        "중요: CRM, CX, PMO, Growth Marketing, Growth Analytics처럼 데이터 기반 지표 운영·실험·성과분석이 핵심인 포지션은 데이터 분석가 include로 봅니다. "
        "중요: FP&A, financial planning, 손익/예산/ROI 분석, Process Innovation, ERP/CRM 기반 KPI·OKR 운영 자동화, 플랫폼 운영/작품 운영 전략은 데이터 분석가 include로 봅니다. "
        "currentRole은 prior 일 뿐입니다. detail/tasks/summary가 더 강한 근거를 주면 mappedRole을 바꿔도 됩니다. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"decision\":\"include\",\"confidence\":\"high\",\"mappedRole\":\"인공지능 엔지니어\",\"reason\":\"...\"}]}"
        " 형태만 반환하세요. "
        "decision은 include, review, exclude 중 하나만 허용합니다. "
        "confidence는 high, medium, low 중 하나만 허용합니다. "
        "mappedRole은 인공지능 엔지니어, 인공지능 리서처, 데이터 사이언티스트, 데이터 분석가, 기타 중 하나만 허용합니다. "
        "reason은 24자 이하의 짧은 한국어 구문으로 쓰세요. "
        "입력에 없는 사실을 지어내지 마세요."
    )
    payload = {"items": candidates}
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def request_review_batch(config: dict, candidates: list[dict]) -> list[dict]:
    payload = {
        "model": config["model"],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": build_messages(candidates),
    }
    headers = {"Content-Type": "application/json"}
    if config.get("apiKey"):
        headers["Authorization"] = f"Bearer {config['apiKey']}"
    request = urllib.request.Request(
        f"{config['baseUrl'].rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=240) as response:
        body = json.loads(response.read().decode("utf-8"))
    parsed = extract_json_object(body["choices"][0]["message"]["content"])
    items = parsed.get("items", []) if isinstance(parsed, dict) else []
    by_id = {item.get("id"): item for item in items if isinstance(item, dict)}
    return [normalize_item(by_id.get(candidate["id"], {}), candidate) for candidate in candidates]


def build_candidate(job: dict, row: dict, override_items: dict) -> dict:
    decision = explain_service_scope_row(row, override_items=override_items)
    compact = compact_job_for_summary(job)
    existing_override = resolve_service_scope_override(job, override_items=override_items)
    return {
        "id": row["id"],
        "signature": compute_service_scope_signature(job),
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "currentRole": row.get("rawRole", "") or row.get("roleGroup", ""),
        "summaryQuality": row.get("summaryQuality", ""),
        "summary": row.get("summary", ""),
        "focusLabel": row.get("focusLabel", ""),
        "keywords": row.get("highlightKeywords", [])[:5],
        "detailBody": compact.get("detailBody", []),
        "tasks": compact.get("tasks", []),
        "requirements": compact.get("requirements", []),
        "preferred": compact.get("preferred", []),
        "skills": compact.get("skills", []),
        "heuristicAction": decision.get("action", ""),
        "heuristicReasons": [reason.get("label", "") for reason in decision.get("reasons", [])],
        "existingDecision": existing_override.get("action", ""),
        "existingMappedRole": existing_override.get("mappedRole", ""),
        "existingConfidence": existing_override.get("confidence", ""),
    }


def build_candidates(job_ids: list[str] | None = None, mode: str = "missing", limit: int = 0) -> list[dict]:
    payload = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    jobs_by_id = {job.get("id", ""): job for job in payload.get("jobs", []) if job.get("id")}
    rows = build_base_rows(payload)
    override_items = load_service_scope_override_store().get("items", {})
    requested_ids = {job_id for job_id in (job_ids or []) if job_id}

    candidates = []
    for row in rows:
        job = jobs_by_id.get(row.get("id", ""))
        if not job:
            continue
        if requested_ids and row["id"] not in requested_ids:
            continue
        fresh_override = resolve_service_scope_override(job, override_items=override_items)
        if not requested_ids:
            if mode == "review" and explain_service_scope_row(row, override_items=override_items).get("action") != "review":
                continue
            if mode == "missing" and fresh_override:
                continue
        candidates.append(build_candidate(job, row, override_items))

    if limit > 0:
        candidates = candidates[:limit]
    return candidates


def write_review_report(config: dict, candidates: list[dict], results: list[dict], output_path) -> dict:
    result_by_id = {item["id"]: item for item in results}
    include_count = sum(1 for item in results if item["decision"] == "include")
    review_count = sum(1 for item in results if item["decision"] == "review")
    exclude_count = sum(1 for item in results if item["decision"] == "exclude")
    low_confidence_count = sum(1 for item in results if item["confidence"] == "low")
    report = {
        "updatedAt": now_iso(),
        "provider": {
            "baseUrl": config["baseUrl"],
            "model": config["model"],
        },
        "counts": {
            "candidates": len(candidates),
            "include": include_count,
            "review": review_count,
            "exclude": exclude_count,
            "lowConfidence": low_confidence_count,
        },
        "items": [
            {
                **candidate,
                "modelDecision": result_by_id.get(candidate["id"], {}),
            }
            for candidate in candidates
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return report


def apply_model_results(results: list[dict]) -> int:
    override_store = load_service_scope_override_store()
    items = override_store.get("items", {})
    applied = 0
    current_time = now_iso()
    for result in results:
        if not result.get("id"):
            continue
        items[result["id"]] = {
            "action": result["decision"],
            "source": "service_scope_model_pipeline",
            "reason": result.get("reason", ""),
            "mappedRole": result.get("mappedRole", ""),
            "confidence": result.get("confidence", ""),
            "signature": result.get("signature", ""),
            "updatedAt": current_time,
        }
        applied += 1
    override_store["updatedAt"] = current_time
    override_store["items"] = items
    save_service_scope_override_store(override_store)
    return applied


def run_service_scope_model_pipeline(
    config: dict,
    *,
    job_ids: list[str] | None = None,
    mode: str = "missing",
    batch_size: int = 5,
    limit: int = 0,
    output_path=DEFAULT_OUTPUT_PATH,
    apply_results: bool = True,
) -> dict:
    candidates = build_candidates(job_ids=job_ids, mode=mode, limit=limit)
    if not candidates:
        return {
            "candidateCount": 0,
            "processed": 0,
            "applied": 0,
            "include": 0,
            "review": 0,
            "exclude": 0,
            "lowConfidence": 0,
            "reportPath": str(output_path),
        }

    results = []
    for batch in chunked(candidates, max(1, batch_size)):
        results.extend(request_review_batch(config, batch))

    write_review_report(config, candidates, results, output_path)
    applied = apply_model_results(results) if apply_results else 0
    return {
        "candidateCount": len(candidates),
        "processed": len(results),
        "applied": applied,
        "include": sum(1 for item in results if item["decision"] == "include"),
        "review": sum(1 for item in results if item["decision"] == "review"),
        "exclude": sum(1 for item in results if item["decision"] == "exclude"),
        "lowConfidence": sum(1 for item in results if item["confidence"] == "low"),
        "reportPath": str(output_path),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.environ.get("COMPANY_INSIGHT_BASE_URL", ""))
    parser.add_argument("--model", default=os.environ.get("COMPANY_INSIGHT_MODEL", ""))
    parser.add_argument("--api-key", default=os.environ.get("COMPANY_INSIGHT_API_KEY", ""))
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--mode", choices=["review", "missing", "all"], default="missing")
    parser.add_argument("--job-ids", default="")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--no-apply", action="store_true")
    args = parser.parse_args()

    if not args.base_url or not args.model:
        raise SystemExit("base-url and model are required")

    config = {
        "baseUrl": args.base_url,
        "model": args.model,
        "apiKey": args.api_key,
    }
    job_ids = [job_id.strip() for job_id in args.job_ids.split(",") if job_id.strip()]
    output_path = Path(args.output)
    if not output_path.is_absolute():
        output_path = ROOT / output_path
    result = run_service_scope_model_pipeline(
        config,
        job_ids=job_ids or None,
        mode=args.mode,
        batch_size=args.batch_size,
        limit=args.limit,
        output_path=output_path,
        apply_results=not args.no_apply,
    )
    print(f"Reviewed {result['processed']} jobs")
    if args.no_apply:
        print("Applied 0 model decisions (--no-apply)")
    else:
        print(f"Applied {result['applied']} model decisions")
    print(
        f"Include {result['include']} / Review {result['review']} / "
        f"Exclude {result['exclude']} / Low confidence {result['lowConfidence']}"
    )
    print(f"Wrote service scope review to {result['reportPath']}")


if __name__ == "__main__":
    main()
