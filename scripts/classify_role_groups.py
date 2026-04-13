#!/usr/bin/env python3

import argparse
import json
import os
import re
import urllib.request
from datetime import datetime, timezone

from ai_runtime import (
    JOBS_PATH,
    compute_role_group_signature,
    extract_json_object,
    load_summary_store,
)
from build_summary_board import (
    build_base_rows,
    load_role_group_override_store,
    normalize_allowed_role,
    resolve_role_group_override,
    save_role_group_override_store,
)


ROOT = JOBS_PATH.parent.parent
OUTPUT_PATH = ROOT / "data" / "role_group_model_review.json"
ALLOWED_ROLES = [
    "인공지능 엔지니어",
    "인공지능 리서처",
    "데이터 사이언티스트",
    "데이터 분석가",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def analyst_family_boost(title: str, current_role: str) -> str:
    lowered = title.lower()
    patterns = [
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
    return "데이터 분석가" if any(re.search(pattern, lowered) for pattern in patterns) else ""


def normalize_item(item: dict, candidate: dict) -> dict:
    role_group = normalize_allowed_role(item.get("roleGroup", ""))
    if not role_group:
        role_group = normalize_allowed_role(candidate.get("currentRole", ""))
    if not role_group:
        role_group = "인공지능 엔지니어"

    confidence = str(item.get("confidence", "")).strip().lower()
    if confidence not in {"high", "medium", "low"}:
        confidence = "low"

    analyst_override = analyst_family_boost(candidate.get("title", ""), candidate.get("currentRole", ""))
    if analyst_override:
        role_group = analyst_override
        if confidence == "low":
            confidence = "medium"

    reason = " ".join(str(item.get("reason", "")).strip().split())[:80]
    return {
        "id": candidate["id"],
        "roleGroup": role_group,
        "confidence": confidence,
        "reason": reason,
        "signature": candidate["signature"],
    }


def build_messages(candidates: list[dict]) -> list[dict]:
    system_prompt = (
        "당신은 한국어 AI/데이터 채용 보드의 역할 분류기입니다. "
        "각 공고를 정확히 하나의 roleGroup으로 분류하세요. "
        "허용 역할군은 인공지능 엔지니어, 인공지능 리서처, 데이터 사이언티스트, 데이터 분석가 네 개뿐입니다. "
        "제목만 보지 말고 summary, focusLabel, keywords, structuredSignals, detailBody, tasks, requirements, preferred, skills를 함께 보세요. "
        "기준: "
        "인공지능 엔지니어는 모델 구현, 서빙, MLOps, 파이프라인, AI 애플리케이션 개발, 플랫폼, ML 시스템 운영 중심입니다. "
        "인공지능 리서처는 논문, 알고리즘 연구, 벤치마크, foundation model, multimodal, 연구 scientist/researcher 중심입니다. "
        "데이터 사이언티스트는 통계 모델링, 실험 설계, 검증, 예측, 추천, 임상/의료 데이터 과학, 리서치 scientist 중 데이터 과학 성격이 강한 경우입니다. "
        "데이터 분석가는 SQL, BI, CRM, CX, PMO, Growth Marketing, 퍼널, 지표, 리텐션, 대시보드, 운영 성과 분석 중심입니다. "
        "중요: CRM, CX, PMO, Growth Marketing, Growth Analytics는 데이터 분석가로 분류하세요. "
        "중요: FP&A, financial planning, 손익/예산/ROI 분석, Process Innovation, ERP/CRM 기반 KPI·OKR 운영 자동화, 플랫폼 운영/작품 운영 전략은 데이터 분석가로 분류하세요. "
        "중요: Clinical Research Scientist, 임상연구전문가, Data Scientist, Research Scientist가 데이터 과학/임상검증 성격이면 데이터 사이언티스트로 분류하세요. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"roleGroup\":\"데이터 분석가\",\"confidence\":\"high\",\"reason\":\"...\"}]}"
        " 형태만 반환하세요. "
        "confidence는 high, medium, low 중 하나만 허용합니다. "
        "reason은 24자 이하의 짧은 한국어 구문으로 쓰세요. "
        "없는 사실을 지어내지 마세요."
    )
    payload = {"items": candidates}
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def candidate_signal_role(candidate: dict) -> str:
    values = candidate.get("roleSignals", []) if isinstance(candidate.get("roleSignals", []), list) else []
    for value in values:
        cleaned = normalize_allowed_role(value)
        if cleaned:
            return cleaned
    return ""


def needs_role_adjudication(candidate: dict, result: dict) -> bool:
    current_role = normalize_allowed_role(candidate.get("currentRole", ""))
    signal_role = candidate_signal_role(candidate)
    decided_role = normalize_allowed_role(result.get("roleGroup", ""))
    confidence = str(result.get("confidence", "")).strip().lower()

    if confidence != "high":
        return True
    if current_role and signal_role and current_role == signal_role and decided_role and decided_role != current_role:
        return True
    if current_role and signal_role and decided_role and decided_role not in {current_role, signal_role}:
        return True
    return False


def build_adjudication_messages(candidates: list[dict]) -> list[dict]:
    system_prompt = (
        "당신은 한국어 AI/데이터 채용 보드의 역할 분류 재판정기입니다. "
        "각 공고에 대해 1차 판정과 원본 직무 힌트가 충돌하는 케이스만 다시 판단합니다. "
        "허용 역할군은 인공지능 엔지니어, 인공지능 리서처, 데이터 사이언티스트, 데이터 분석가 네 개뿐입니다. "
        "currentRole 과 structured roleSignals 는 강한 prior 로 취급하세요. "
        "이 둘이 같은 역할을 가리키면, 상세 업무가 명확히 반대 방향을 말하지 않는 한 그 역할을 유지하세요. "
        "특히 다음 구분을 엄격히 지키세요. "
        "인공지능 엔지니어: 모델/시스템 구현, 서빙, 플랫폼, MLOps, application 개발, productization 중심. "
        "인공지능 리서처: researcher/scientist, 논문, 벤치마크, 새로운 알고리즘/파운데이션 모델 연구가 핵심 산출물일 때. "
        "연구 engineer 라고 적혀 있어도 실제 책임이 구현·배포·최적화 중심이면 인공지능 엔지니어로 남길 수 있습니다. "
        "데이터 사이언티스트: 통계 모델링, 실험 설계, 예측/추천, 검증, 의료/임상 데이터 과학, growth analytics 중 통계적 모델링 중심. "
        "데이터 분석가: CRM, CX, PMO, Growth Marketing, BI, SQL, 대시보드, 운영 지표 분석, 퍼널/리텐션 중심. "
        "FP&A, financial planning, 손익·예산·ROI 분석, Process Innovation, ERP/CRM 기반 KPI/OKR 운영 자동화, 플랫폼 운영/작품 운영 전략은 데이터 분석가로 분류하세요. "
        "Product Manager, Product Owner, Project Manager, Business Developer, Strategy Manager, Operations Manager, Enterprise Manager, AX Manager, Consultant 는 "
        "AI 회사 안에 있어도 자동으로 데이터 분석가가 아닙니다. "
        "currentRole 과 roleSignals 가 인공지능 엔지니어이고, summary/tasks 에 LLM, RAG, MLOps, serving, architecture, pipeline, 솔루션 구현, 시스템 구축이 보이면 "
        "우선 인공지능 엔지니어를 유지하세요. "
        "Research Engineer, Quantization Engineer, Path Planning Algorithm Engineer, Machine Learning Engineer, Agents & Workflows engineer 는 "
        "논문 우대나 연구 표현이 있어도 구현/최적화/파이프라인 책임이 핵심이면 인공지능 엔지니어로 유지하세요. "
        "반대로 AI Researcher, Research Scientist, Foundation Model, VLM, Multimodal research 처럼 title 자체가 researcher/scientist 이고 "
        "연구/학회/논문이 핵심 산출물이면 인공지능 리서처로 분류하세요. "
        "Growth Analytics 라도 통계 분석, 검증, 모델링이 핵심이면 데이터 사이언티스트로 둘 수 있습니다. "
        "Business Developer, Product Manager, PMO, Enterprise Manager, Operations Manager 같은 제목은 AI 회사 안에 있어도 자동으로 분석가가 아닙니다. "
        "strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"roleGroup\":\"인공지능 엔지니어\",\"confidence\":\"high\",\"reason\":\"...\"}]}"
        " 형태만 반환하세요. "
        "confidence는 high, medium, low 중 하나만 허용합니다. "
        "reason은 24자 이하의 짧은 한국어 구문으로 쓰세요. "
        "없는 사실을 지어내지 마세요."
    )
    payload = {"items": candidates}
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def request_role_batch(config: dict, candidates: list[dict]) -> list[dict]:
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


def request_role_adjudication_batch(config: dict, candidates: list[dict]) -> list[dict]:
    payload = {
        "model": config["model"],
        "temperature": 0.0,
        "response_format": {"type": "json_object"},
        "messages": build_adjudication_messages(candidates),
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


def build_candidate(job: dict, row: dict, summary_item: dict, override_items: dict) -> dict:
    existing_override = resolve_role_group_override(job, summary_item, override_items=override_items)
    structured = row.get("structuredSignals", {}) if isinstance(row.get("structuredSignals", {}), dict) else {}
    return {
        "id": row["id"],
        "signature": compute_role_group_signature(job, summary_item),
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "currentRole": row.get("rawRole", "") or row.get("roleGroup", ""),
        "summary": row.get("summary", ""),
        "focusLabel": row.get("focusLabel", ""),
        "keywords": row.get("highlightKeywords", [])[:5],
        "roleSignals": structured.get("roleSignals", [])[:3],
        "problemSignals": structured.get("problemSignals", [])[:3],
        "dataSignals": structured.get("dataSignals", [])[:3],
        "workflowSignals": structured.get("workflowSignals", [])[:3],
        "detailBody": row.get("detailBody", ""),
        "tasks": row.get("tasks", [])[:6],
        "requirements": row.get("requirements", [])[:5],
        "preferred": row.get("preferred", [])[:5],
        "skills": row.get("skills", [])[:8],
        "existingRoleGroup": existing_override.get("roleGroup", ""),
        "existingConfidence": existing_override.get("confidence", ""),
    }


def build_candidates(job_ids: list[str] | None = None, mode: str = "missing", limit: int = 0) -> list[dict]:
    payload = json.loads(JOBS_PATH.read_text(encoding="utf-8"))
    rows = build_base_rows(payload)
    rows_by_id = {row["id"]: row for row in rows}
    summary_items = load_summary_store().get("items", {})
    override_items = load_role_group_override_store().get("items", {})
    requested_ids = {job_id for job_id in (job_ids or []) if job_id}

    candidates = []
    for job in payload.get("jobs", []):
        job_id = job.get("id", "")
        row = rows_by_id.get(job_id)
        if not row:
            continue
        if requested_ids and job_id not in requested_ids:
            continue
        summary_item = summary_items.get(job_id, {})
        fresh_override = resolve_role_group_override(job, summary_item, override_items=override_items)
        if not requested_ids:
            if mode == "missing" and fresh_override:
                continue
            if mode == "stale":
                if fresh_override and fresh_override.get("signature") == compute_role_group_signature(job, summary_item):
                    continue
        candidates.append(build_candidate(job, row, summary_item, override_items))

    if limit > 0:
        candidates = candidates[:limit]
    return candidates


def write_review_report(config: dict, candidates: list[dict], results: list[dict]) -> dict:
    result_by_id = {item["id"]: item for item in results}
    counts = {}
    for role in ALLOWED_ROLES:
        counts[role] = sum(1 for item in results if item["roleGroup"] == role)
    report = {
        "updatedAt": now_iso(),
        "provider": {
            "baseUrl": config["baseUrl"],
            "model": config["model"],
        },
        "counts": {
            "candidates": len(candidates),
            **counts,
            "lowConfidence": sum(1 for item in results if item["confidence"] == "low"),
        },
        "items": [
            {
                **candidate,
                "modelDecision": result_by_id.get(candidate["id"], {}),
            }
            for candidate in candidates
        ],
    }
    OUTPUT_PATH.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return report


def apply_model_results(results: list[dict]) -> int:
    override_store = load_role_group_override_store()
    items = override_store.get("items", {})
    applied = 0
    current_time = now_iso()
    for result in results:
        if not result.get("id"):
            continue
        items[result["id"]] = {
            "roleGroup": result.get("roleGroup", ""),
            "source": "role_group_model_pipeline",
            "reason": result.get("reason", ""),
            "confidence": result.get("confidence", ""),
            "signature": result.get("signature", ""),
            "updatedAt": current_time,
        }
        applied += 1
    override_store["updatedAt"] = current_time
    override_store["items"] = items
    save_role_group_override_store(override_store)
    return applied


def run_role_group_model_pipeline(
    config: dict,
    *,
    job_ids: list[str] | None = None,
    mode: str = "missing",
    batch_size: int = 5,
    limit: int = 0,
    announce_progress: bool = False,
) -> dict:
    candidates = build_candidates(job_ids=job_ids, mode=mode, limit=limit)
    if not candidates:
        return {
            "candidateCount": 0,
            "processed": 0,
            "applied": 0,
            "lowConfidence": 0,
            "reportPath": str(OUTPUT_PATH),
        }

    results = []
    total = len(candidates)
    processed = 0
    applied = 0
    for batch in chunked(candidates, max(1, batch_size)):
        batch_results = request_role_batch(config, batch)
        results.extend(batch_results)
        applied += apply_model_results(batch_results)
        processed += len(batch)
        if announce_progress:
            print(f"Processed {processed}/{total}", flush=True)

    result_by_id = {item["id"]: item for item in results}
    adjudication_candidates = []
    for candidate in candidates:
        decided = result_by_id.get(candidate["id"])
        if decided and needs_role_adjudication(candidate, decided):
            adjudication_candidates.append(
                {
                    **candidate,
                    "firstPassRoleGroup": decided.get("roleGroup", ""),
                    "firstPassConfidence": decided.get("confidence", ""),
                    "firstPassReason": decided.get("reason", ""),
                }
            )

    adjudicated = 0
    if adjudication_candidates:
        adjudication_batches = max(1, min(batch_size, 4))
        total_adjudication = len(adjudication_candidates)
        processed_adjudication = 0
        for batch in chunked(adjudication_candidates, adjudication_batches):
            batch_results = request_role_adjudication_batch(config, batch)
            applied += apply_model_results(batch_results)
            adjudicated += len(batch_results)
            processed_adjudication += len(batch)
            for item in batch_results:
                result_by_id[item["id"]] = item
            if announce_progress:
                print(
                    f"Adjudicated {processed_adjudication}/{total_adjudication}",
                    flush=True,
                )

    final_results = [result_by_id[candidate["id"]] for candidate in candidates if candidate["id"] in result_by_id]
    write_review_report(config, candidates, final_results)
    output = {
        "candidateCount": len(candidates),
        "processed": len(final_results),
        "applied": applied,
        "adjudicated": adjudicated,
        "lowConfidence": sum(1 for item in final_results if item["confidence"] == "low"),
        "reportPath": str(OUTPUT_PATH),
    }
    for role in ALLOWED_ROLES:
        output[role] = sum(1 for item in final_results if item["roleGroup"] == role)
    return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=os.environ.get("COMPANY_INSIGHT_BASE_URL", ""))
    parser.add_argument("--model", default=os.environ.get("COMPANY_INSIGHT_MODEL", ""))
    parser.add_argument("--api-key", default=os.environ.get("COMPANY_INSIGHT_API_KEY", ""))
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--mode", choices=["missing", "all", "stale"], default="missing")
    parser.add_argument("--job-ids", default="")
    parser.add_argument("--limit", type=int, default=0)
    args = parser.parse_args()

    if not args.base_url or not args.model:
        raise SystemExit("base-url and model are required")

    config = {
        "baseUrl": args.base_url,
        "model": args.model,
        "apiKey": args.api_key,
    }
    job_ids = [job_id.strip() for job_id in args.job_ids.split(",") if job_id.strip()]
    result = run_role_group_model_pipeline(
        config,
        job_ids=job_ids or None,
        mode=args.mode,
        batch_size=args.batch_size,
        limit=args.limit,
        announce_progress=True,
    )
    print(f"Reviewed {result['processed']} jobs")
    print(f"Applied {result['applied']} model decisions")
    print(f"Adjudicated {result.get('adjudicated', 0)} jobs")
    print(
        "Roles "
        f"AE {result.get('인공지능 엔지니어', 0)} / "
        f"AR {result.get('인공지능 리서처', 0)} / "
        f"DS {result.get('데이터 사이언티스트', 0)} / "
        f"DA {result.get('데이터 분석가', 0)} / "
        f"Low {result['lowConfidence']}"
    )
    print(f"Wrote role review to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
