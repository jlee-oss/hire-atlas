#!/usr/bin/env python3

import hashlib
import html
import io
import json
import os
import os
import pathlib
import glob
import ssl
import sys
from collections import Counter
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlparse
import urllib.request


ROOT = pathlib.Path(__file__).resolve().parent
SCRIPTS_DIR = ROOT / "scripts"
for _site_packages in sorted(glob.glob(str(ROOT / ".venv" / "lib" / "python*" / "site-packages"))):
    if _site_packages not in sys.path:
        sys.path.insert(0, _site_packages)

# Load .env file from project root if it exists (keeps secrets out of environment/shell history)
_env_path = ROOT / ".env"
if _env_path.exists():
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip())

# Vercel 환경에서는 파일시스템이 읽기 전용이므로 쓰기는 /tmp로, 읽기는 /tmp 우선 후 data/ 폴백
ON_VERCEL = bool(os.environ.get("VERCEL"))


def _writable(path: pathlib.Path) -> pathlib.Path:
    """Vercel에서는 /tmp로 리다이렉트, 로컬에서는 원래 경로 사용."""
    return pathlib.Path("/tmp") / path.name if ON_VERCEL else path


def _readable(path: pathlib.Path) -> pathlib.Path:
    """Vercel에서는 /tmp의 최신 캐시를 우선, 없으면 배포된 data/ 파일 사용."""
    if ON_VERCEL:
        tmp = pathlib.Path("/tmp") / path.name
        if tmp.exists():
            return tmp
    return path


COMPANY_INSIGHT_CACHE_PATH = ROOT / "data" / "company_hover_insights.json"
COMPANY_INSIGHT_BASE_URL = os.environ.get("COMPANY_INSIGHT_BASE_URL", "https://api.vibemakers.kr/v1")
COMPANY_INSIGHT_MODEL = os.environ.get("COMPANY_INSIGHT_MODEL", "gemma-4-31b")
COMPANY_INSIGHT_API_KEY = os.environ.get("COMPANY_INSIGHT_API_KEY", "")
ROLE_RESUME_GUIDE_CACHE_PATH = ROOT / "data" / "role_resume_guides.json"
ROLE_RESUME_GUIDE_BASE_URL = os.environ.get("ROLE_RESUME_GUIDE_BASE_URL", COMPANY_INSIGHT_BASE_URL)
ROLE_RESUME_GUIDE_MODEL = os.environ.get("ROLE_RESUME_GUIDE_MODEL", "gemma-4-31b")
ROLE_RESUME_GUIDE_API_KEY = os.environ.get("ROLE_RESUME_GUIDE_API_KEY", COMPANY_INSIGHT_API_KEY)
ROLE_RESUME_SCHEMA_VERSION = 4
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

try:  # noqa: E402
    import certifi

    URL_OPEN_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except Exception:  # pragma: no cover - environment dependent
    URL_OPEN_CONTEXT = None

from ai_runtime import (  # noqa: E402
    compute_role_group_signature,
    compute_service_scope_signature,
    get_jobs_payload,
    get_release_prompt_profile,
    load_summary_store,
    request_cluster_labels,
    request_summaries_resilient,
    save_company_clusters,
    save_summary_batch,
    save_summary_store,
)
from build_summary_board import (  # noqa: E402
    OUTPUT_PATH as SUMMARY_BOARD_PATH,
    build_base_rows,
    build_cluster_label_seeds,
    build_company_profiles,
    build_dynamic_cluster_payload,
    build_summary_board,
    load_role_group_override_store,
    load_service_scope_override_store,
)
from classify_role_groups import run_role_group_model_pipeline  # noqa: E402
from classify_service_scope_candidates import run_service_scope_model_pipeline  # noqa: E402
from sync_sheet_snapshot import sync_sheet_snapshot  # noqa: E402

try:  # noqa: E402
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.platypus import HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    REPORTLAB_AVAILABLE = True
except Exception:  # pragma: no cover - environment dependent
    REPORTLAB_AVAILABLE = False


def chunked(items, size):
    for index in range(0, len(items), size):
        yield items[index : index + size]


def urlopen_with_certifi(request, *, timeout: int):
    if URL_OPEN_CONTEXT is not None and str(getattr(request, "full_url", "")).startswith("https://"):
        return urllib.request.urlopen(request, timeout=timeout, context=URL_OPEN_CONTEXT)
    return urllib.request.urlopen(request, timeout=timeout)


def default_model_config() -> dict:
    return {
        "baseUrl": COMPANY_INSIGHT_BASE_URL,
        "model": COMPANY_INSIGHT_MODEL,
        "apiKey": COMPANY_INSIGHT_API_KEY,
        "temperature": 0.0,
    }


def merge_model_config(config: dict | None) -> dict:
    merged = default_model_config()
    for key, value in (config or {}).items():
        if value not in (None, ""):
            merged[key] = value
    return merged


def is_local_model_base_url(base_url: str) -> bool:
    normalized = str(base_url or "").strip().lower()
    return (
        normalized.startswith("http://127.0.0.1")
        or normalized.startswith("http://localhost")
        or normalized.startswith("http://[::1]")
    )


def live_model_configured(config: dict | None) -> bool:
    base_url = str((config or {}).get("baseUrl", "")).strip()
    model = str((config or {}).get("model", "")).strip()
    if not (base_url and model):
        return False
    # 외부 서비스(localhost/127.0.0.1이 아닌 경우)는 apiKey가 반드시 필요
    is_local = "localhost" in base_url or "127.0.0.1" in base_url
    if not is_local:
        api_key = str((config or {}).get("apiKey", "")).strip()
        if not api_key:
            return False
    return True


def summary_needs_refresh(item: dict) -> bool:
    quality = str(item.get("quality", "")).strip().lower()
    return (
        not item.get("summarizedAt")
        or not quality
        or quality == "low"
    )


def default_store() -> dict:
    return {"updatedAt": None, "items": {}}


def now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()


def load_company_insight_cache() -> dict:
    path = _readable(COMPANY_INSIGHT_CACHE_PATH)
    if not path.exists():
        return default_store()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_store()


def save_company_insight_cache(store: dict) -> None:
    path = _writable(COMPANY_INSIGHT_CACHE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    store["updatedAt"] = now_iso()
    path.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def load_role_resume_guide_cache() -> dict:
    path = _readable(ROLE_RESUME_GUIDE_CACHE_PATH)
    if not path.exists():
        return default_store()
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return default_store()


def save_role_resume_guide_cache(store: dict) -> None:
    path = _writable(ROLE_RESUME_GUIDE_CACHE_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    store["updatedAt"] = now_iso()
    path.write_text(
        json.dumps(store, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def safe_get_jobs_payload() -> dict:
    try:
        return get_jobs_payload()
    except FileNotFoundError:
        return {"generatedAt": None, "source": {}, "jobs": []}


def job_signature(job: dict) -> str:
    relevant = {
        "company": job.get("company", ""),
        "title": job.get("title", ""),
        "role": job.get("role", ""),
        "roleDisplay": job.get("roleDisplay", ""),
        "groupSummary": job.get("groupSummary", ""),
        "detailBody": job.get("detailBody", ""),
        "tasks": job.get("tasks", []) or [],
        "requirements": job.get("requirements", []) or [],
        "preferred": job.get("preferred", []) or [],
        "skills": job.get("skills", []) or [],
        "active": bool(job.get("active")),
        "jobUrl": job.get("jobUrl", ""),
        "lastSeenAt": job.get("lastSeenAt", ""),
    }
    serialized = json.dumps(relevant, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()


def compute_sync_delta(before_payload: dict, after_payload: dict) -> dict:
    before_jobs = {job["id"]: job for job in before_payload.get("jobs", []) if job.get("id")}
    after_jobs = {job["id"]: job for job in after_payload.get("jobs", []) if job.get("id")}

    before_ids = set(before_jobs)
    after_ids = set(after_jobs)
    added_ids = sorted(after_ids - before_ids)
    removed_ids = sorted(before_ids - after_ids)
    changed_ids = sorted(
        job_id
        for job_id in (before_ids & after_ids)
        if job_signature(before_jobs[job_id]) != job_signature(after_jobs[job_id])
    )
    unchanged_count = len(after_ids) - len(added_ids) - len(changed_ids)

    return {
        "addedIds": added_ids,
        "changedIds": changed_ids,
        "removedIds": removed_ids,
        "added": len(added_ids),
        "changed": len(changed_ids),
        "removed": len(removed_ids),
        "unchanged": max(0, unchanged_count),
    }


def prune_summary_items(job_ids: list[str]) -> int:
    if not job_ids:
        return 0
    store = load_summary_store()
    removed = 0
    for job_id in job_ids:
        if job_id in store.get("items", {}):
            del store["items"][job_id]
            removed += 1
    if removed:
        save_summary_store(store)
    return removed


def normalize_inline_text(value: str) -> str:
    return " ".join(str(value or "").split())


ROLE_RESUME_PDF_FONT_STATE = {"registered": False, "regular": "Helvetica", "bold": "Helvetica-Bold"}
ROLE_RESUME_PDF_FONT_CANDIDATES = [
    {
        "regular": pathlib.Path.home() / "Library" / "Fonts" / "Pretendard-Regular.otf",
        "bold": pathlib.Path.home() / "Library" / "Fonts" / "Pretendard-Bold.otf",
        "family": "PretendardPDF",
    },
    {
        "regular": pathlib.Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
        "bold": pathlib.Path("/System/Library/Fonts/Supplemental/AppleGothic.ttf"),
        "family": "AppleGothicPDF",
    },
    {
        "regular": pathlib.Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        "bold": pathlib.Path("/System/Library/Fonts/Supplemental/Arial Unicode.ttf"),
        "family": "ArialUnicodePDF",
    },
]


def ensure_role_resume_pdf_fonts() -> tuple[str, str]:
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("PDF renderer가 준비되지 않았습니다.")
    if ROLE_RESUME_PDF_FONT_STATE["registered"]:
        return ROLE_RESUME_PDF_FONT_STATE["regular"], ROLE_RESUME_PDF_FONT_STATE["bold"]

    for candidate in ROLE_RESUME_PDF_FONT_CANDIDATES:
        regular_path = candidate["regular"]
        bold_path = candidate["bold"]
        if not regular_path.exists() or not bold_path.exists():
            continue
        regular_name = f'{candidate["family"]}-Regular'
        bold_name = f'{candidate["family"]}-Bold'
        try:
            if regular_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(regular_name, str(regular_path)))
            if bold_name not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont(bold_name, str(bold_path)))
            ROLE_RESUME_PDF_FONT_STATE.update({"registered": True, "regular": regular_name, "bold": bold_name})
            return regular_name, bold_name
        except Exception:
            continue

    ROLE_RESUME_PDF_FONT_STATE.update({"registered": True, "regular": "Helvetica", "bold": "Helvetica-Bold"})
    return ROLE_RESUME_PDF_FONT_STATE["regular"], ROLE_RESUME_PDF_FONT_STATE["bold"]


def compact_lines(values, limit=4, line_limit=120) -> list[str]:
    lines = []
    for value in values or []:
        cleaned = normalize_inline_text(value)
        if not cleaned:
            continue
        lines.append(cleaned[:line_limit])
        if len(lines) >= limit:
            break
    return lines


def find_board_row(job_id: str) -> dict | None:
    board = get_summary_board(force=False)
    for row in board.get("rows", []):
        if row.get("id") == job_id:
            return row
    return None


def company_insight_signature(row: dict) -> str:
    relevant = {
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "summary": row.get("summary", ""),
        "focusLabel": row.get("focusLabel", ""),
        "highlightKeywords": row.get("highlightKeywords", []) or [],
        "companyHeadline": row.get("companyHeadline", ""),
        "companyReason": row.get("companyReason", ""),
        "detailBody": row.get("detailBody", ""),
        "tasks": row.get("tasks", []) or [],
        "requirements": row.get("requirements", []) or [],
        "preferred": row.get("preferred", []) or [],
        "skills": row.get("skills", []) or [],
        "structuredSignals": row.get("structuredSignals", {}) or {},
        "lastSeenAt": row.get("lastSeenAt", ""),
    }
    serialized = json.dumps(relevant, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()


def build_company_insight_fallback(row: dict) -> str:
    company = row.get("company", "") or "이 회사"
    headline = normalize_inline_text(row.get("companyHeadline", ""))
    reason = normalize_inline_text(row.get("companyReason", ""))
    if headline and reason:
        return f"{company}는 현재 {headline} 축 채용이 강합니다. {reason}"
    if reason:
        return reason
    summary = normalize_inline_text(row.get("summary", ""))
    if summary:
        return f"{company} 공고에서는 {summary} 흐름이 핵심으로 보입니다."
    return f"{company} 공고의 핵심 신호를 아직 충분히 읽지 못했습니다."


def normalize_signal_value_list(values, *, limit=2) -> list[str]:
    items = []
    for value in values or []:
        cleaned = normalize_inline_text(value)
        if not cleaned or cleaned in items:
            continue
        items.append(cleaned[:44])
        if len(items) >= limit:
            break
    return items


def build_company_insight_fallback_card(row: dict) -> dict:
    company = row.get("company", "") or "이 공고"
    structured = row.get("structuredSignals", {}) or {}
    problem = normalize_signal_value_list(structured.get("problemSignals", []), limit=1)
    domain = normalize_signal_value_list(structured.get("domainSignals", []), limit=1)
    system = normalize_signal_value_list(structured.get("systemSignals", []), limit=1)
    data = normalize_signal_value_list(structured.get("dataSignals", []), limit=1)
    workflow = normalize_signal_value_list(structured.get("workflowSignals", []), limit=1)
    keywords = normalize_signal_value_list(row.get("highlightKeywords", []), limit=3)
    summary = normalize_inline_text(row.get("summary", ""))
    focus = normalize_inline_text(row.get("focusLabel", ""))
    role = normalize_inline_text(row.get("roleGroup", "") or row.get("role", ""))

    headline = problem[0] if problem else focus or role or "핵심 채용 포인트"
    if summary:
        summary_text = summary[:140]
    else:
        fragments = [problem[0] if problem else "", domain[0] if domain else "", system[0] if system else ""]
        fragments = [fragment for fragment in fragments if fragment]
        if fragments:
            summary_text = f"{company} 공고는 {' · '.join(fragments[:2])} 축 역량을 중심으로 읽힙니다."
        else:
            summary_text = build_company_insight_fallback(row)

    signals = []
    if problem:
        signals.append(f"핵심 과업: {problem[0]}")
    if domain:
        signals.append(f"업무 맥락: {domain[0]}")
    if system:
        signals.append(f"기술 환경: {system[0]}")
    elif data:
        signals.append(f"데이터 맥락: {data[0]}")
    elif workflow:
        signals.append(f"업무 흐름: {workflow[0]}")
    if keywords:
        joined = " · ".join(keywords[:2])
        if joined:
            signals.append(f"주요 키워드: {joined}")

    return {
        "headline": headline[:32] or "핵심 채용 포인트",
        "summary": summary_text[:160],
        "paragraphs": [summary_text[:160]],
        "signals": signals[:3],
    }


def normalize_company_insight_card(card: dict, fallback: dict) -> dict:
    if not isinstance(card, dict):
        return fallback

    headline = normalize_inline_text(card.get("headline", ""))[:32]
    summary = normalize_inline_text(card.get("summary", ""))[:180]
    paragraphs = [
        normalize_inline_text(item)[:120]
        for item in card.get("paragraphs", []) or []
        if normalize_inline_text(item)
    ][:3]
    signals = normalize_signal_value_list(card.get("signals", []), limit=3)
    if not paragraphs and summary:
        paragraphs = [summary]
    if not paragraphs:
        paragraphs = fallback.get("paragraphs", []) or [fallback.get("summary", "")]

    return {
        "headline": headline or fallback.get("headline", "핵심 채용 포인트"),
        "summary": summary or fallback.get("summary", ""),
        "paragraphs": paragraphs,
        "signals": signals or fallback.get("signals", []),
    }


def flatten_company_insight_card(card: dict) -> str:
    if not isinstance(card, dict):
        return ""
    parts = [card.get("headline", "")]
    parts.extend((card.get("paragraphs", []) or [])[:2])
    if not card.get("paragraphs"):
        parts.append(card.get("summary", ""))
    parts.extend((card.get("signals", []) or [])[:2])
    return normalize_inline_text(" ".join(part for part in parts if part))[:220]


def build_company_insight_messages(row: dict) -> list[dict]:
    payload = {
        "company": row.get("company", ""),
        "title": row.get("title", ""),
        "role": row.get("roleGroup", "") or row.get("role", ""),
        "focusLabel": row.get("focusLabel", ""),
        "summary": row.get("summary", ""),
        "highlightKeywords": row.get("highlightKeywords", []) or [],
        "structuredSignals": row.get("structuredSignals", {}) or {},
        "tasks": compact_lines(row.get("tasks", []), limit=3),
        "requirements": compact_lines(row.get("requirements", []), limit=2),
        "preferred": compact_lines(row.get("preferred", []), limit=2),
        "skills": compact_lines(row.get("skills", []), limit=4),
        "detailBody": normalize_inline_text(row.get("detailBody", ""))[:500],
    }
    system_prompt = (
        "당신은 채용 인사이트 보드의 hover 카드 해설자입니다. "
        "공고 1건을 읽고 사용자가 회사명 위에 마우스를 올렸을 때 3초 안에 핵심을 파악할 수 있는 한국어 설명을 만드세요. "
        "회사 일반 소개나 과장 표현은 금지하고, 이 공고에서 실제로 눈에 띄는 역할의 중심축을 보수적으로 요약하세요. "
        "반드시 JSON only로 응답하고, 아래 스키마만 반환하세요. "
        "{\"headline\":\"8~22자 명사구\",\"paragraphs\":[\"문단1\",\"문단2\"],\"signals\":[\"라벨: 내용\",\"라벨: 내용\"]}. "
        "paragraphs는 1~3개, 각 문단은 30~90자 정도의 완결 문장으로 작성하세요. "
        "signals는 2~3개, 각 항목은 12~36자 이내, 라벨 뒤에 콜론을 붙이세요. "
        "스택 이름만 나열하지 말고 역할/맥락/읽을 포인트를 우선하세요."
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def extract_json_object(raw: str) -> dict:
    content = str(raw or "").strip()
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
    start = content.find("{")
    end = content.rfind("}")
    if start != -1 and end != -1 and end > start:
        return json.loads(content[start : end + 1])
    raise ValueError("Model did not return valid JSON")


def iter_sse_data_lines(response) -> str:
    while True:
        raw_line = response.readline()
        if not raw_line:
            break
        line = raw_line.decode("utf-8", "ignore").strip()
        if not line or not line.startswith("data:"):
            continue
        data = line[5:].strip()
        if not data:
            continue
        yield data


def request_company_insight_from_model(row: dict, config: dict | None = None) -> dict:
    merged = merge_model_config(config)
    if not company_insight_model_configured(merged):
        raise RuntimeError("Company insight model config is missing")

    fallback_card = build_company_insight_fallback_card(row)
    payload = {
        "model": merged["model"],
        "temperature": 0.2,
        "max_tokens": 260,
        "response_format": {"type": "json_object"},
        "messages": build_company_insight_messages(row),
    }
    headers = {
        "Content-Type": "application/json",
    }
    if merged.get("apiKey"):
        headers["Authorization"] = f"Bearer {merged['apiKey']}"
    request = urllib.request.Request(
        f"{str(merged['baseUrl']).rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urlopen_with_certifi(request, timeout=80) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    parsed = extract_json_object(content)
    card = normalize_company_insight_card(parsed, fallback_card)
    insight = flatten_company_insight_card(card)
    if not insight or not card.get("paragraphs"):
        raise ValueError("Model returned empty company insight card")
    return {
        "insight": insight[:220],
        "card": card,
        "provider": {
            "baseUrl": merged.get("baseUrl", ""),
            "model": merged.get("model", ""),
        },
    }


def company_insight_model_configured(config: dict | None = None) -> bool:
    return live_model_configured(merge_model_config(config))


def find_stale_company_cached_entry(job_id: str, row: dict, cache: dict) -> tuple[dict, str]:
    items = cache.get("items", {}) if isinstance(cache, dict) else {}
    if not isinstance(items, dict):
        return {}, ""

    direct = items.get(job_id, {})
    if isinstance(direct, dict) and (direct.get("insight") or direct.get("card")):
        return direct, "exact"

    company = row.get("company", "")
    if not company:
        return {}, ""

    board = get_summary_board(force=False)
    for board_row in board.get("rows", []):
        candidate_id = board_row.get("id", "")
        if candidate_id == job_id or board_row.get("company") != company:
            continue
        candidate = items.get(candidate_id, {})
        if isinstance(candidate, dict) and (candidate.get("insight") or candidate.get("card")):
            return candidate, "company"
    return {}, ""


def get_company_insight(job_id: str, config: dict | None = None) -> dict:
    row = find_board_row(job_id)
    if not row:
        raise KeyError(f"Unknown job id: {job_id}")

    merged_config = merge_model_config(config)
    signature = company_insight_signature(row)
    fallback = build_company_insight_fallback(row)
    fallback_card = build_company_insight_fallback_card(row)
    cache = load_company_insight_cache()
    cached = cache.get("items", {}).get(job_id, {})
    cached_card = normalize_company_insight_card(cached.get("card", {}), fallback_card)
    cached_insight = normalize_inline_text(cached.get("insight", "")) or flatten_company_insight_card(cached_card)
    if cached.get("signature") == signature and cached_insight:
        return {
            "jobId": job_id,
            "company": row.get("company", ""),
            "insight": cached_insight,
            "card": cached_card,
            "cached": True,
            "provider": cached.get("provider", {}),
        }

    stale_cached, stale_source = find_stale_company_cached_entry(job_id, row, cache)
    stale_card = normalize_company_insight_card(stale_cached.get("card", {}), fallback_card)
    stale_insight = normalize_inline_text(stale_cached.get("insight", "")) or flatten_company_insight_card(stale_card)

    if not company_insight_model_configured(merged_config):
        if stale_insight:
            return {
                "jobId": job_id,
                "company": row.get("company", ""),
                "insight": stale_insight,
                "card": stale_card,
                "cached": True,
                "stale": True,
                "staleSource": stale_source,
                "provider": stale_cached.get("provider", {}),
            }
        return {
            "jobId": job_id,
            "company": row.get("company", ""),
            "insight": flatten_company_insight_card(fallback_card),
            "card": fallback_card,
            "cached": False,
            "stale": True,
            "provider": {
                "baseUrl": merged_config.get("baseUrl", ""),
                "model": merged_config.get("model", ""),
            },
        }

    try:
        live_result = request_company_insight_from_model(row, merged_config)
    except Exception:
        if stale_insight:
            return {
                "jobId": job_id,
                "company": row.get("company", ""),
                "insight": stale_insight,
                "card": stale_card,
                "cached": True,
                "stale": True,
                "staleSource": stale_source,
                "provider": stale_cached.get("provider", {}),
            }
        return {
            "jobId": job_id,
            "company": row.get("company", ""),
            "insight": flatten_company_insight_card(fallback_card),
            "card": fallback_card,
            "cached": False,
            "stale": True,
            "provider": {
                "baseUrl": merged_config.get("baseUrl", ""),
                "model": merged_config.get("model", ""),
            },
        }

    cache.setdefault("items", {})[job_id] = {
        "jobId": job_id,
        "company": row.get("company", ""),
        "signature": signature,
        "insight": live_result["insight"],
        "card": live_result.get("card", fallback_card),
        "provider": live_result.get("provider", {}),
        "fallback": fallback,
        "updatedAt": now_iso(),
    }
    save_company_insight_cache(cache)
    return {
        "jobId": job_id,
        "company": row.get("company", ""),
        "insight": live_result["insight"],
        "card": live_result.get("card", fallback_card),
        "cached": False,
        "provider": live_result.get("provider", {}),
    }


ROLE_RESUME_LINE_NOISE_SNIPPETS = (
    "채용절차법",
    "반환 청구",
    "반환 서류",
    "반환 청구 기간",
    "복지포인트",
    "건강검진",
    "생일 반차",
    "장기근속 휴가",
    "오피스 간식",
    "유급휴가",
    "중소기업 청년",
    "서류 전형",
    "면접 전형",
    "처우협의",
    "최종합격",
    "혜택 및 복지",
    "복리후생",
    "재택근무",
    "유연출근",
    "간식 제공",
    "레퍼런스 체크",
)
ROLE_RESUME_GENERIC_HEADERS = {
    "모집요강",
    "자격 요건",
    "우대 사항",
    "우대사항",
    "지원 자격",
    "지원자격",
    "필수 역량",
    "기본 요건",
    "직무내용",
}
ROLE_RESUME_SIGNAL_CATEGORIES = (
    "problemSignals",
    "domainSignals",
    "systemSignals",
    "modelSignals",
    "dataSignals",
    "workflowSignals",
)


def stable_signature(payload: dict) -> str:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(serialized.encode("utf-8")).hexdigest()


def role_resume_cache_key(role: str, activity_filter: str) -> str:
    return f"{normalize_inline_text(role)}::{normalize_inline_text(activity_filter or 'all')}"


def role_resume_cached_document(entry: dict) -> dict:
    if not isinstance(entry, dict):
        return {}
    payload = entry.get("payload", {})
    if not isinstance(payload, dict):
        return {}
    document = payload.get("document", {})
    return document if isinstance(document, dict) else {}


def role_resume_cached_payload(entry: dict) -> dict:
    if not isinstance(entry, dict):
        return {}
    payload = entry.get("payload", {})
    return payload if isinstance(payload, dict) else {}


def has_role_resume_cached_document(entry: dict) -> bool:
    return bool(role_resume_cached_document(entry).get("headline"))


def find_role_resume_cached_entry(cache: dict, role: str, activity_filter: str) -> dict:
    items = cache.get("items", {}) if isinstance(cache, dict) else {}
    if not isinstance(items, dict):
        return {}

    normalized_role = normalize_inline_text(role)
    normalized_activity = normalize_inline_text(activity_filter or "all") or "all"
    candidate_keys = [role_resume_cache_key(normalized_role, normalized_activity)]
    if normalized_activity != "all":
        candidate_keys.append(role_resume_cache_key(normalized_role, "all"))

    for key in candidate_keys:
        entry = items.get(key, {})
        if has_role_resume_cached_document(entry):
            return entry

    for entry in items.values():
        if normalize_inline_text(entry.get("role", "")) == normalized_role and has_role_resume_cached_document(entry):
            return entry

    return {}


def default_role_resume_model_config() -> dict:
    return {
        "baseUrl": ROLE_RESUME_GUIDE_BASE_URL,
        "model": ROLE_RESUME_GUIDE_MODEL,
        "apiKey": ROLE_RESUME_GUIDE_API_KEY,
        "temperature": 0.3,
    }


def merge_role_resume_model_config(config: dict | None) -> dict:
    merged = default_role_resume_model_config()
    for key, value in (config or {}).items():
        if value not in (None, ""):
            merged[key] = value
    return merged


def role_resume_model_configured(config: dict | None = None) -> bool:
    merged = merge_role_resume_model_config(config)
    return live_model_configured(merged)


def role_resume_provider_differs(left: dict | None, right: dict | None) -> bool:
    left = left or {}
    right = right or {}
    return (
        str(left.get("baseUrl", "")).rstrip("/") != str(right.get("baseUrl", "")).rstrip("/")
        or str(left.get("model", "")) != str(right.get("model", ""))
        or bool(left.get("apiKey")) != bool(right.get("apiKey"))
    )


def normalize_count_items(counter: Counter, *, limit: int = 8, width: int = 64) -> list[dict]:
    items = []
    for label, count in counter.most_common(limit):
        cleaned = normalize_inline_text(label)
        if not cleaned:
            continue
        items.append({"label": cleaned[:width], "count": int(count)})
    return items


def is_role_resume_noise_line(value: str) -> bool:
    cleaned = normalize_inline_text(value)
    if not cleaned:
        return True
    if cleaned in ROLE_RESUME_GENERIC_HEADERS:
        return True
    if cleaned == "별도 우대사항 미기재":
        return True
    if len(cleaned) <= 3:
        return True
    lowered = cleaned.lower()
    if any(snippet.lower() in lowered for snippet in ROLE_RESUME_LINE_NOISE_SNIPPETS):
        return True
    if cleaned.startswith("*") or cleaned.startswith("•"):
        return True
    return False


def collect_role_resume_terms(rows: list[dict], key: str, *, limit: int = 10, width: int = 44) -> list[dict]:
    counts = Counter()
    for row in rows:
        for value in row.get(key, []) or []:
            cleaned = normalize_inline_text(value)
            if not cleaned:
                continue
            counts[cleaned[:width]] += 1
    return normalize_count_items(counts, limit=limit, width=width)


def collect_role_resume_lines(rows: list[dict], key: str, *, limit: int = 8, width: int = 140) -> list[dict]:
    counts = Counter()
    for row in rows:
        for value in row.get(key, []) or []:
            cleaned = normalize_inline_text(value)
            if is_role_resume_noise_line(cleaned):
                continue
            counts[cleaned[:width]] += 1
    return normalize_count_items(counts, limit=limit, width=width)


def collect_role_resume_scalar_counts(rows: list[dict], key: str, *, limit: int = 8, width: int = 40) -> list[dict]:
    counts = Counter()
    for row in rows:
        cleaned = normalize_inline_text(row.get(key, ""))
        if cleaned:
            counts[cleaned[:width]] += 1
    return normalize_count_items(counts, limit=limit, width=width)


def collect_role_resume_structured_counts(rows: list[dict]) -> dict:
    result = {}
    for category in ROLE_RESUME_SIGNAL_CATEGORIES:
        counts = Counter()
        for row in rows:
            structured = row.get("structuredSignals", {}) or {}
            for value in structured.get(category, []) or []:
                cleaned = normalize_inline_text(value)
                if cleaned:
                    counts[cleaned[:44]] += 1
        result[category] = normalize_count_items(counts, limit=8, width=44)
    return result


def role_resume_signal_density(row: dict) -> int:
    structured = row.get("structuredSignals", {}) or {}
    density = len(row.get("highlightKeywords", []) or [])
    density += len(row.get("skills", []) or [])
    for category in ROLE_RESUME_SIGNAL_CATEGORIES:
        density += len(structured.get(category, []) or [])
    if normalize_inline_text(row.get("summary", "")):
        density += 4
    if normalize_inline_text(row.get("focusLabel", "")):
        density += 2
    return density


def build_role_resume_posting_samples(rows: list[dict], *, limit: int = 7) -> list[dict]:
    ordered = sorted(
        rows,
        key=lambda row: (
            str(row.get("summaryQuality", "")).lower() == "low",
            -role_resume_signal_density(row),
            row.get("company", ""),
            row.get("title", ""),
        ),
    )
    samples = []
    seen = set()
    for row in ordered:
        row_id = row.get("id", "")
        if not row_id or row_id in seen:
            continue
        seen.add(row_id)
        structured = row.get("structuredSignals", {}) or {}
        samples.append(
            {
                "company": normalize_inline_text(row.get("company", ""))[:28],
                "title": normalize_inline_text(row.get("title", ""))[:72],
                "focusLabel": normalize_inline_text(row.get("focusLabel", ""))[:32],
                "summary": normalize_inline_text(row.get("summary", ""))[:140],
                "keywords": normalize_signal_value_list(row.get("highlightKeywords", []), limit=5),
                "problemSignals": normalize_signal_value_list(structured.get("problemSignals", []), limit=3),
                "systemSignals": normalize_signal_value_list(structured.get("systemSignals", []), limit=3),
                "workflowSignals": normalize_signal_value_list(structured.get("workflowSignals", []), limit=3),
            }
        )
        if len(samples) >= limit:
            break
    return samples


def build_role_resume_market_profile(role: str, activity_filter: str = "all") -> dict:
    normalized_role = normalize_inline_text(role)
    if not normalized_role or normalized_role in {"전체", "기타"}:
        raise ValueError("specific role is required")

    normalized_activity = "active" if normalize_inline_text(activity_filter) == "active" else "all"
    board = get_summary_board(force=False)
    rows = [
        row
        for row in board.get("rows", [])
        if normalize_inline_text(row.get("roleGroup", "")) == normalized_role
    ]
    if normalized_activity == "active":
        rows = [row for row in rows if row.get("active")]

    if not rows:
        raise ValueError("No postings found for the selected role")

    company_counts = Counter(
        normalize_inline_text(row.get("company", ""))
        for row in rows
        if normalize_inline_text(row.get("company", ""))
    )
    keyword_counts = Counter()
    for row in rows:
        for value in row.get("highlightKeywords", []) or []:
            cleaned = normalize_inline_text(value)
            if cleaned:
                keyword_counts[cleaned[:44]] += 1

    return {
        "role": normalized_role,
        "activityFilter": normalized_activity,
        "activityLabel": "활성 공고 기준" if normalized_activity == "active" else "전체 공고 기준",
        "generatedFromBoardAt": board.get("generatedAt", ""),
        "analyzedJobs": len(rows),
        "companyCount": len(company_counts),
        "focusCounts": collect_role_resume_scalar_counts(rows, "focusLabel", limit=10, width=36),
        "keywordCounts": normalize_count_items(keyword_counts, limit=14, width=44),
        "skillCounts": collect_role_resume_terms(rows, "skills", limit=14, width=32),
        "companyCounts": normalize_count_items(company_counts, limit=12, width=24),
        "taskEvidence": collect_role_resume_lines(rows, "tasks", limit=10),
        "requirementEvidence": collect_role_resume_lines(rows, "requirements", limit=10),
        "preferredEvidence": collect_role_resume_lines(rows, "preferred", limit=6),
        "structuredSignalCounts": collect_role_resume_structured_counts(rows),
        "postingSamples": build_role_resume_posting_samples(rows, limit=4),
    }


def build_role_resume_messages(market_profile: dict) -> list[dict]:
    compact_profile = {
        "role": market_profile.get("role", ""),
        "activityLabel": market_profile.get("activityLabel", ""),
        "analyzedJobs": market_profile.get("analyzedJobs", 0),
        "companyCount": market_profile.get("companyCount", 0),
        "focusCounts": market_profile.get("focusCounts", [])[:8],
        "keywordCounts": market_profile.get("keywordCounts", [])[:12],
        "skillCounts": market_profile.get("skillCounts", [])[:12],
        "companyCounts": market_profile.get("companyCounts", [])[:10],
        "taskEvidence": market_profile.get("taskEvidence", [])[:8],
        "requirementEvidence": market_profile.get("requirementEvidence", [])[:8],
        "preferredEvidence": market_profile.get("preferredEvidence", [])[:5],
        "structuredSignalCounts": {
            key: (value or [])[:8]
            for key, value in (market_profile.get("structuredSignalCounts", {}) or {}).items()
        },
    }
    system_prompt = (
        "당신은 채용시장 분석을 바탕으로 목표 지향 이력서 한 장을 설계하는 편집자입니다. "
        "대상은 해당 분야에 처음 진입하거나 커리어 전환을 시도하는 사람입니다. "
        "목적은 '멋있어 보이는 글'이 아니라, 현재 시장이 실제로 반복해서 요구하는 역량과 프로젝트 방향을 정직하게 전달하는 것입니다. "
        "아래 입력은 일부 샘플 공고가 아니라 전체 공고를 집계한 결과입니다. 반드시 전체 분포를 우선적으로 해석하세요. "
        "입력은 실제 채용 데이터에서 집계한 시장 요약입니다. 입력에 없는 기술, 도메인, 학위, 경력, 자격증, 회사명, 연도, 수치 성과를 지어내지 마세요. "
        "특히 실제 근무 이력처럼 보이는 허구의 회사/연차/성과를 만들면 안 됩니다. "
        "반드시 하나의 강한 문서만 만드세요. 3안 비교나 여러 카드 제안은 금지합니다. "
        "문서는 실제로 한 페이지짜리 이력서처럼 읽혀야 하며, 보고서나 설명 카드처럼 쓰면 안 됩니다. "
        "정직한 경력 기술이 어렵다면 Career History 대신 Selected Projects 혹은 Project Experience로 구성하세요. "
        "Education 섹션도 실제 학교명을 지어내지 말고, 필요한 학습 배경 또는 준비 방향을 정직하게 표현하세요. "
        "한국어만 사용하고 JSON only로 아래 스키마만 반환하세요. "
        "{\"panelTitle\":\"...\",\"panelSubtitle\":\"...\",\"marketReality\":\"...\",\"honestyMessage\":\"...\","
        "\"document\":{\"headline\":\"...\",\"subheadline\":\"...\","
        "\"summary\":\"...\","
        "\"projects\":[{\"title\":\"...\",\"meta\":\"...\",\"overview\":\"...\","
        "\"responsibilities\":[\"...\"],\"achievements\":[\"...\"]}],"
        "\"education\":[{\"title\":\"...\",\"meta\":\"...\"}],"
        "\"skills\":[\"...\"],"
        "\"portfolio\":[\"...\"],"
        "\"footerNote\":\"...\"}} "
        "projects는 반드시 2~3개, responsibilities는 각 프로젝트당 2~3개, achievements는 각 프로젝트당 2~3개로 작성하세요. "
        "education은 1~2개, skills는 8~12개, portfolio는 3~5개로 작성하세요. "
        "headline은 문서 최상단에 크게 들어가는 짧은 한 줄 제목입니다. 가능하면 14~26자 안팎으로 쓰고, 길게 설명하지 마세요. "
        "subheadline은 그 아래 역할 정체성을 보여주는 짧은 한 줄이며 가능하면 40자 안팎으로 유지하세요. "
        "headline이나 subheadline에 '시장 분석 기반 설계', 'AI가 작성한', '목표 이력서', '샘플' 같은 메타 표현을 넣지 마세요. "
        "summary는 2~3문장으로 짧고 밀도 있게 씁니다. "
        "marketReality와 honestyMessage는 문서 바깥의 보조 설명이므로 1~2문장으로 짧게 유지하세요."
    )
    payload = {"marketProfile": compact_profile}
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def normalize_role_resume_text_list(values, *, limit: int, width: int) -> list[str]:
    items = []
    for value in values or []:
        cleaned = normalize_inline_text(value)
        if not cleaned or cleaned in items:
            continue
        items.append(cleaned[:width])
        if len(items) >= limit:
            break
    return items


def normalize_role_resume_guides(payload: dict, market_profile: dict) -> dict:
    document = payload.get("document", {})
    if not isinstance(document, dict):
        document = {}

    projects = []
    for index, item in enumerate(document.get("projects", []) or [], start=1):
        if not isinstance(item, dict):
            continue
        title = normalize_inline_text(item.get("title", ""))[:56]
        meta = normalize_inline_text(item.get("meta", ""))[:84]
        overview = normalize_inline_text(item.get("overview", ""))[:180]
        responsibilities = normalize_role_resume_text_list(
            item.get("responsibilities", []),
            limit=3,
            width=100,
        )
        achievements = normalize_role_resume_text_list(
            item.get("achievements", []),
            limit=3,
            width=100,
        )
        if not title:
            continue
        projects.append(
            {
                "title": title or f"프로젝트 {index}",
                "meta": meta,
                "overview": overview,
                "responsibilities": responsibilities,
                "achievements": achievements,
            }
        )
        if len(projects) >= 3:
            break

    education_items = []
    for item in document.get("education", []) or []:
        if not isinstance(item, dict):
            continue
        title = normalize_inline_text(item.get("title", ""))[:72]
        meta = normalize_inline_text(item.get("meta", ""))[:120]
        if not title and not meta:
            continue
        education_items.append({"title": title, "meta": meta})
        if len(education_items) >= 2:
            break

    if len(projects) < 2:
        raise ValueError("Model returned incomplete resume document")

    role = market_profile.get("role", "선택 직무")
    activity_label = market_profile.get("activityLabel", "시장 기준")
    analyzed_jobs = market_profile.get("analyzedJobs", 0)
    return {
        "schemaVersion": ROLE_RESUME_SCHEMA_VERSION,
        "panelTitle": normalize_inline_text(payload.get("panelTitle", ""))[:56]
        or f"{role} 시장 기준 목표 이력서",
        "panelSubtitle": normalize_inline_text(payload.get("panelSubtitle", ""))[:120]
        or f"{activity_label} {analyzed_jobs}건을 바탕으로 압축한 AI 생성 목표 이력서",
        "marketReality": normalize_inline_text(payload.get("marketReality", ""))[:220],
        "honestyMessage": normalize_inline_text(payload.get("honestyMessage", ""))[:220],
        "document": {
            "headline": normalize_inline_text(document.get("headline", ""))[:56] or f"{role} 목표 이력서",
            "subheadline": normalize_inline_text(document.get("subheadline", ""))[:92],
            "summary": normalize_inline_text(document.get("summary", ""))[:360],
            "projects": projects,
            "education": education_items,
            "skills": normalize_role_resume_text_list(document.get("skills", []), limit=12, width=28),
            "portfolio": normalize_role_resume_text_list(document.get("portfolio", []), limit=5, width=96),
            "footerNote": normalize_inline_text(document.get("footerNote", ""))[:160],
        },
    }


def normalize_role_resume_document_for_pdf(role: str, payload: dict | None) -> dict:
    container = payload if isinstance(payload, dict) else {}
    document = container.get("document", container) if isinstance(container, dict) else {}
    if not isinstance(document, dict):
        document = {}

    projects = []
    for index, item in enumerate(document.get("projects", []) or [], start=1):
        if not isinstance(item, dict):
            continue
        title = normalize_inline_text(item.get("title", ""))[:80] or f"프로젝트 {index}"
        meta = normalize_inline_text(item.get("meta", ""))[:120]
        overview = normalize_inline_text(item.get("overview", ""))[:280]
        responsibilities = normalize_role_resume_text_list(item.get("responsibilities", []), limit=4, width=120)
        achievements = normalize_role_resume_text_list(item.get("achievements", []), limit=4, width=120)
        projects.append(
            {
                "title": title,
                "meta": meta,
                "overview": overview,
                "responsibilities": responsibilities,
                "achievements": achievements,
            }
        )
        if len(projects) >= 4:
            break

    education = []
    for item in document.get("education", []) or []:
        if not isinstance(item, dict):
            continue
        title = normalize_inline_text(item.get("title", ""))[:100]
        meta = normalize_inline_text(item.get("meta", ""))[:160]
        if not title and not meta:
            continue
        education.append({"title": title, "meta": meta})
        if len(education) >= 3:
            break

    return {
        "role": normalize_inline_text(role) or "선택 직무",
        "headline": normalize_inline_text(document.get("headline", ""))[:80] or normalize_inline_text(role) or "목표 이력서",
        "subheadline": normalize_inline_text(document.get("subheadline", ""))[:140],
        "summary": normalize_inline_text(document.get("summary", ""))[:600],
        "projects": projects,
        "education": education,
        "skills": normalize_role_resume_text_list(document.get("skills", []), limit=16, width=40),
        "portfolio": normalize_role_resume_text_list(document.get("portfolio", []), limit=6, width=140),
        "footerNote": normalize_inline_text(document.get("footerNote", ""))[:240],
    }


def safe_pdf_filename(value: str) -> str:
    cleaned = "".join(
        ch if ch.isascii() and (ch.isalnum() or ch in {"-", "_"}) else "-"
        for ch in normalize_inline_text(value)
    )
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned[:64] or "role-resume"


def build_role_resume_pdf_bytes(role: str, payload: dict | None) -> tuple[bytes, str]:
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("서버 PDF renderer를 사용할 수 없습니다.")

    document = normalize_role_resume_document_for_pdf(role, payload)
    regular_font, bold_font = ensure_role_resume_pdf_fonts()
    styles = getSampleStyleSheet()
    body_style = ParagraphStyle(
        "ResumeBody",
        parent=styles["BodyText"],
        fontName=regular_font,
        fontSize=10.6,
        leading=16,
        textColor=colors.HexColor("#222222"),
        alignment=TA_LEFT,
        splitLongWords=True,
    )
    subtle_style = ParagraphStyle(
        "ResumeSubtle",
        parent=body_style,
        fontSize=9.3,
        leading=14,
        textColor=colors.HexColor("#666666"),
    )
    title_style = ParagraphStyle(
        "ResumeTitle",
        parent=body_style,
        fontName=bold_font,
        fontSize=23,
        leading=28,
        textColor=colors.HexColor("#111111"),
        spaceAfter=2,
    )
    subtitle_style = ParagraphStyle(
        "ResumeSubtitle",
        parent=body_style,
        fontSize=10.4,
        leading=15,
        textColor=colors.HexColor("#444444"),
    )
    section_label_style = ParagraphStyle(
        "ResumeSectionLabel",
        parent=body_style,
        fontName=bold_font,
        fontSize=12.5,
        leading=16,
        textColor=colors.HexColor("#111111"),
    )
    project_title_style = ParagraphStyle(
        "ResumeProjectTitle",
        parent=body_style,
        fontName=bold_font,
        fontSize=11.6,
        leading=15,
        textColor=colors.HexColor("#111111"),
    )
    small_heading_style = ParagraphStyle(
        "ResumeSmallHeading",
        parent=body_style,
        fontName=bold_font,
        fontSize=9.7,
        leading=13,
        textColor=colors.HexColor("#111111"),
    )
    bullet_style = ParagraphStyle(
        "ResumeBullet",
        parent=body_style,
        leftIndent=10,
        firstLineIndent=-8,
        bulletIndent=0,
        spaceBefore=1,
    )
    footer_style = ParagraphStyle(
        "ResumeFooter",
        parent=subtle_style,
        fontSize=8.8,
        leading=13,
    )

    def paragraph(text: str, style: ParagraphStyle):
        return Paragraph(html.escape(normalize_inline_text(text)).replace("\n", "<br/>"), style)

    def bullet_lines(items: list[str]) -> list:
        return [paragraph(f"• {item}", bullet_style) for item in items if normalize_inline_text(item)]

    def build_section(label: str, body_flowables: list, *, top_border: bool = True) -> Table:
        table = Table([[paragraph(label, section_label_style), body_flowables]], colWidths=[112, 388])
        table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 0),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                    ("TOPPADDING", (0, 0), (-1, -1), 16),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 16),
                    ("LINEABOVE", (0, 0), (-1, -1), 1 if top_border else 0, colors.HexColor("#d8d8d8")),
                ]
            )
        )
        return table

    story = [
        paragraph(document["headline"], title_style),
    ]
    if document["subheadline"]:
        story.append(paragraph(document["subheadline"], subtitle_style))
    story.append(Spacer(1, 14))
    story.append(HRFlowable(width="100%", thickness=1.6, color=colors.HexColor("#111111"), spaceBefore=0, spaceAfter=0))

    summary_body = [paragraph(document["summary"] or document["role"], body_style)]
    story.append(build_section("Summary", summary_body, top_border=False))

    project_flowables = []
    for index, item in enumerate(document["projects"]):
        if index:
            project_flowables.append(Spacer(1, 10))
        project_flowables.append(paragraph(item["title"], project_title_style))
        if item["meta"]:
            project_flowables.append(paragraph(item["meta"], subtle_style))
        if item["overview"]:
            project_flowables.append(Spacer(1, 4))
            project_flowables.append(paragraph(item["overview"], body_style))
        if item["responsibilities"]:
            project_flowables.append(Spacer(1, 6))
            project_flowables.append(paragraph("Key responsibilities", small_heading_style))
            project_flowables.extend(bullet_lines(item["responsibilities"]))
        if item["achievements"]:
            project_flowables.append(Spacer(1, 6))
            project_flowables.append(paragraph("Achievements", small_heading_style))
            project_flowables.extend(bullet_lines(item["achievements"]))
    story.append(build_section("Selected Projects", project_flowables or [paragraph("프로젝트 정보가 없습니다.", subtle_style)]))

    education_flowables = []
    for item in document["education"]:
        if education_flowables:
            education_flowables.append(Spacer(1, 8))
        if item["title"]:
            education_flowables.append(paragraph(item["title"], body_style if not item["meta"] else project_title_style))
        if item["meta"]:
            education_flowables.append(paragraph(item["meta"], subtle_style))
    story.append(build_section("Education / Preparation", education_flowables or [paragraph("학습 배경 정보가 없습니다.", subtle_style)]))

    skills_text = ", ".join(document["skills"]) if document["skills"] else "핵심 기술 정보가 없습니다."
    story.append(build_section("Key Skills", [paragraph(skills_text, body_style)]))

    portfolio_flowables = bullet_lines(document["portfolio"]) or [paragraph("포트폴리오 안내 정보가 없습니다.", subtle_style)]
    story.append(build_section("Portfolio", portfolio_flowables))

    if document["footerNote"]:
        story.append(Spacer(1, 2))
        story.append(paragraph(document["footerNote"], footer_style))

    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=38,
        rightMargin=38,
        topMargin=34,
        bottomMargin=28,
        title=document["headline"],
        author="Hire Atlas",
    )
    pdf.build(story)
    filename = f'{safe_pdf_filename(document["role"])}_{safe_pdf_filename(document["headline"])}.pdf'
    return buffer.getvalue(), filename


def count_labels(items: list[dict], limit: int = 4) -> list[str]:
    labels = []
    for item in items or []:
        label = normalize_inline_text(item.get("label", "")) if isinstance(item, dict) else ""
        if not label or label in labels:
            continue
        labels.append(label)
        if len(labels) >= limit:
            break
    return labels


def first_available_label(market_profile: dict, *paths: tuple[str, ...], default: str = "") -> str:
    for path in paths:
        if len(path) == 1:
            labels = count_labels(market_profile.get(path[0], []), limit=1)
        else:
            branch = market_profile
            for key in path:
                branch = branch.get(key, {}) if isinstance(branch, dict) else {}
            labels = count_labels(branch if isinstance(branch, list) else [], limit=1)
        if labels:
            return labels[0]
    return default


def build_fallback_role_resume_guides(market_profile: dict) -> dict:
    role = market_profile.get("role", "선택 직무")
    analyzed_jobs = int(market_profile.get("analyzedJobs", 0) or 0)
    activity_label = market_profile.get("activityLabel", "시장 기준")
    primary_focus = first_available_label(market_profile, ("focusCounts",), default="핵심 역량")
    primary_problem = first_available_label(market_profile, ("structuredSignalCounts", "problemSignals"), default=primary_focus)
    secondary_problem = count_labels(market_profile.get("structuredSignalCounts", {}).get("problemSignals", []), limit=2)
    secondary_problem = secondary_problem[1] if len(secondary_problem) > 1 else primary_focus
    primary_system = first_available_label(market_profile, ("structuredSignalCounts", "systemSignals"), default="배포·운영")
    primary_workflow = first_available_label(market_profile, ("structuredSignalCounts", "workflowSignals"), default="검증")
    primary_domain = first_available_label(market_profile, ("structuredSignalCounts", "domainSignals"), default="")
    primary_data = first_available_label(market_profile, ("structuredSignalCounts", "dataSignals"), default="데이터 파이프라인")
    top_skills = count_labels(market_profile.get("skillCounts", []), limit=8)
    top_keywords = count_labels(market_profile.get("keywordCounts", []), limit=6)
    task_lines = count_labels(market_profile.get("taskEvidence", []), limit=4)
    requirement_lines = count_labels(market_profile.get("requirementEvidence", []), limit=4)
    signal_phrase = " · ".join(item for item in [primary_problem, primary_system, primary_domain or primary_data] if item)

    return {
        "schemaVersion": ROLE_RESUME_SCHEMA_VERSION,
        "panelTitle": f"{role} 시장 기준 목표 이력서",
        "panelSubtitle": f"{activity_label} {analyzed_jobs}건을 바탕으로 압축한 목표 이력서 초안",
        "marketReality": f"현재 시장에서는 {signal_phrase or primary_focus} 축이 반복됩니다. 그래서 이력서는 관심 표현보다 어떤 문제를 어떤 프로젝트로 증명했는지 보여주는 쪽이 더 설득력 있습니다.",
        "honestyMessage": "이 문서는 규칙 기반 임시 초안입니다. 실제 사용 전에는 AI 생성 결과로 교체하는 편이 맞습니다.",
        "document": {
            "badge": "Market Blueprint",
            "headline": f"{role} 진입을 준비하는 문제 해결형 지원자",
            "subheadline": signal_phrase or primary_focus,
            "summary": f"{activity_label} {analyzed_jobs}건 기준으로 {signal_phrase or primary_focus} 축이 반복됩니다. 따라서 이 문서는 추상적 관심보다 프로젝트 기반 증거, 검증 방식, 실행 결과를 전면에 두는 방향으로 압축했습니다.",
            "projects": [
                {
                    "title": f"{primary_problem or primary_focus} 프로젝트",
                    "meta": "핵심 문제 정의 · 실험 설계 · 결과 검증",
                    "overview": f"{primary_problem or primary_focus} 요구를 실제 사용자 흐름이나 업무 맥락 안에서 구현하고, 왜 이 접근이 유효한지 검증하는 프로젝트입니다.",
                    "responsibilities": [
                        task_lines[0] if task_lines else "문제 정의와 입력·출력 구조를 먼저 설계합니다.",
                        task_lines[1] if len(task_lines) > 1 else "실행 기준과 평가 기준을 문서로 먼저 고정합니다.",
                    ],
                    "achievements": [
                        requirement_lines[0] if requirement_lines else "결과를 화면, 로그, 비교표로 함께 제시합니다.",
                        "실패 케이스와 개선 전후 차이를 숨기지 않고 함께 설명합니다.",
                    ],
                },
                {
                    "title": f"{primary_system} 기반 운영 프로젝트",
                    "meta": "배포 가능 구조 · 재현 절차 · 모니터링 관점",
                    "overview": f"{primary_problem or primary_focus} 기능을 {primary_system} 관점에서 운영 가능한 구조로 정리하고, 다시 실행 가능한 형태로 남기는 프로젝트입니다.",
                    "responsibilities": [
                        requirement_lines[1] if len(requirement_lines) > 1 else "배포 방법과 재현 절차를 명확히 문서화합니다.",
                        f"{primary_workflow} 관점에서 필요한 지표와 로그 포인트를 정의합니다.",
                    ],
                    "achievements": [
                        "아키텍처와 데이터 흐름을 한 장의 그림으로 설명할 수 있습니다.",
                        "개인 프로젝트 범위를 넘는 운영 경험은 과장하지 않고 경계를 분명히 둡니다.",
                    ],
                },
            ],
            "education": [
                {
                    "title": f"{primary_data or primary_problem} 중심 학습 트랙",
                    "meta": "실제 전공, 수강 과정, 부트캠프, 독학 기록으로 정직하게 교체",
                }
            ],
            "skills": unique_nonempty([*top_skills[:8], *top_keywords[:4]])[:10],
            "portfolio": [
                "문제 정의 문서와 평가 기준",
                "실행 화면 또는 데모 링크",
                "실험 로그와 개선 전후 비교",
                "한계와 다음 개선 방향 정리",
            ],
            "footerNote": "실제 지원 시에는 직접 구현·검증한 범위만 남기고, 허구의 회사명·성과·연차는 추가하지 않습니다.",
        },
    }


def unique_nonempty(values: list[str]) -> list[str]:
    items = []
    for value in values:
        cleaned = normalize_inline_text(value)
        if not cleaned or cleaned in items:
            continue
        items.append(cleaned)
    return items


def request_role_resume_guides_from_model(market_profile: dict, config: dict | None = None) -> dict:
    merged = merge_role_resume_model_config(config)
    payload = {
        "model": merged["model"],
        "temperature": float(merged.get("temperature", 0.45)),
        "max_tokens": 1600,
        "response_format": {"type": "json_object"},
        "messages": build_role_resume_messages(market_profile),
    }
    headers = {
        "Content-Type": "application/json",
    }
    if merged.get("apiKey"):
        headers["Authorization"] = f"Bearer {merged['apiKey']}"
    request = urllib.request.Request(
        f"{str(merged['baseUrl']).rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urlopen_with_certifi(request, timeout=75) as response:
        body = json.loads(response.read().decode("utf-8"))

    content = body["choices"][0]["message"]["content"]
    parsed = extract_json_object(content)
    guides = normalize_role_resume_guides(parsed, market_profile)
    return {
        "guides": guides,
        "provider": {
            "baseUrl": merged.get("baseUrl", ""),
            "model": merged.get("model", ""),
        },
    }


def request_role_resume_guides_from_model_streaming(
    market_profile: dict,
    config: dict | None,
    emit,
) -> dict:
    merged = merge_role_resume_model_config(config)
    payload = {
        "model": merged["model"],
        "temperature": float(merged.get("temperature", 0.45)),
        "max_tokens": 1600,
        "stream": True,
        "response_format": {"type": "json_object"},
        "messages": build_role_resume_messages(market_profile),
    }
    headers = {
        "Content-Type": "application/json",
    }
    if merged.get("apiKey"):
        headers["Authorization"] = f"Bearer {merged['apiKey']}"

    emit("status", {"message": "AI 연결을 시작하고 있습니다."})
    request = urllib.request.Request(
        f"{str(merged['baseUrl']).rstrip('/')}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    chunks = []
    received_any_chunk = False
    with urlopen_with_certifi(request, timeout=120) as response:
        emit("status", {"message": "AI 응답 스트림을 수신하고 있습니다."})
        for data in iter_sse_data_lines(response):
            if data == "[DONE]":
                break
            parsed = json.loads(data)
            choice = (parsed.get("choices") or [{}])[0] or {}
            delta = choice.get("delta") or {}
            chunk = delta.get("content")
            if not chunk:
                continue
            if not received_any_chunk:
                emit("status", {"message": "모델이 실시간으로 문서를 작성하고 있습니다."})
                received_any_chunk = True
            chunks.append(chunk)
            emit("token", {"text": chunk})

    emit("status", {"message": "스트림을 정리하고 문서 형식으로 변환하고 있습니다."})
    content = "".join(chunks)
    parsed = extract_json_object(content)
    guides = normalize_role_resume_guides(parsed, market_profile)
    return {
        "guides": guides,
        "provider": {
            "baseUrl": merged.get("baseUrl", ""),
            "model": merged.get("model", ""),
        },
    }


def get_role_resume_guides(
    role: str,
    activity_filter: str = "all",
    config: dict | None = None,
    *,
    force_refresh: bool = False,
) -> dict:
    market_profile = build_role_resume_market_profile(role, activity_filter=activity_filter)
    merged_config = merge_role_resume_model_config(config)
    default_config = default_role_resume_model_config()
    cache_key = role_resume_cache_key(market_profile["role"], market_profile["activityFilter"])
    signature = stable_signature(
        {
            "schemaVersion": ROLE_RESUME_SCHEMA_VERSION,
            "marketProfile": market_profile,
            "provider": {
                "baseUrl": merged_config.get("baseUrl", ""),
                "model": merged_config.get("model", ""),
            },
        }
    )

    cache = load_role_resume_guide_cache()
    cached = cache.get("items", {}).get(cache_key, {})
    cached_payload = role_resume_cached_payload(cached)
    cached_document = role_resume_cached_document(cached)
    cached_version = cached_payload.get("schemaVersion") if isinstance(cached_payload, dict) else None
    fallback_cached = cached if has_role_resume_cached_document(cached) else find_role_resume_cached_entry(
        cache,
        market_profile["role"],
        market_profile["activityFilter"],
    )
    fallback_payload = role_resume_cached_payload(fallback_cached)
    fallback_document = role_resume_cached_document(fallback_cached)
    if (
        not force_refresh
        and (
        cached.get("signature") == signature
        and cached_version == ROLE_RESUME_SCHEMA_VERSION
        and isinstance(cached_document, dict)
        and cached_document.get("headline")
        )
    ):
        return {
            "role": market_profile["role"],
            "activityFilter": market_profile["activityFilter"],
            "marketProfile": market_profile,
            "payload": cached_payload,
            "cached": True,
            "provider": cached.get("provider", {}),
        }

    if not role_resume_model_configured(merged_config):
        if not force_refresh and isinstance(fallback_document, dict) and fallback_document.get("headline"):
            return {
                "role": market_profile["role"],
                "activityFilter": market_profile["activityFilter"],
                "marketProfile": market_profile,
                "payload": fallback_payload,
                "cached": True,
                "stale": True,
                "provider": fallback_cached.get("provider", {}),
            }
        raise ValueError("AI resume endpoint와 model 설정이 필요합니다.")

    try:
        live_result = request_role_resume_guides_from_model(market_profile, merged_config)
    except Exception as exc:
        if role_resume_model_configured(default_config) and role_resume_provider_differs(merged_config, default_config):
            try:
                live_result = request_role_resume_guides_from_model(market_profile, default_config)
                cache.setdefault("items", {})[cache_key] = {
                    "role": market_profile["role"],
                    "activityFilter": market_profile["activityFilter"],
                    "signature": signature,
                    "payload": live_result["guides"],
                    "provider": live_result.get("provider", {}),
                    "updatedAt": now_iso(),
                }
                save_role_resume_guide_cache(cache)
                return {
                    "role": market_profile["role"],
                    "activityFilter": market_profile["activityFilter"],
                    "marketProfile": market_profile,
                    "payload": live_result["guides"],
                    "cached": False,
                    "provider": live_result.get("provider", {}),
                }
            except Exception:
                pass
        if not force_refresh and isinstance(fallback_document, dict) and fallback_document.get("headline"):
            return {
                "role": market_profile["role"],
                "activityFilter": market_profile["activityFilter"],
                "marketProfile": market_profile,
                "payload": fallback_payload,
                "cached": True,
                "stale": True,
                "provider": fallback_cached.get("provider", {}),
            }
        if "Connection refused" in str(exc):
            raise RuntimeError("AI endpoint에 연결할 수 없습니다. resume 전용 모델 주소를 확인해주세요.") from exc
        raise RuntimeError(f"AI resume generation failed: {exc}") from exc

    cache.setdefault("items", {})[cache_key] = {
        "role": market_profile["role"],
        "activityFilter": market_profile["activityFilter"],
        "signature": signature,
        "payload": live_result["guides"],
        "provider": live_result.get("provider", {}),
        "updatedAt": now_iso(),
    }
    save_role_resume_guide_cache(cache)
    return {
        "role": market_profile["role"],
        "activityFilter": market_profile["activityFilter"],
        "marketProfile": market_profile,
        "payload": live_result["guides"],
        "cached": False,
        "provider": live_result.get("provider", {}),
    }


def incremental_summary_target_ids(
    payload: dict,
    delta: dict,
) -> list[str]:
    store = load_summary_store()
    summary_items = store.get("items", {})
    targets = []
    seen = set()
    preferred_ids = delta.get("addedIds", []) + delta.get("changedIds", [])
    for job_id in preferred_ids:
        if job_id and job_id not in seen:
            seen.add(job_id)
            targets.append(job_id)

    for job in payload.get("jobs", []):
        job_id = job.get("id", "")
        item = summary_items.get(job_id, {})
        if not job_id or job_id in seen:
            continue
        if summary_needs_refresh(item):
            seen.add(job_id)
            targets.append(job_id)
    return targets


def append_unique_job_id(targets: list[str], seen: set[str], job_id: str) -> None:
    if job_id and job_id not in seen:
        seen.add(job_id)
        targets.append(job_id)


def incremental_service_scope_target_ids(payload: dict, delta: dict) -> list[str]:
    """Refresh changed rows plus stale model-scope decisions for unchanged rows."""
    targets: list[str] = []
    seen: set[str] = set()
    for job_id in delta.get("addedIds", []) + delta.get("changedIds", []):
        append_unique_job_id(targets, seen, job_id)

    override_items = load_service_scope_override_store().get("items", {})
    for job in payload.get("jobs", []):
        job_id = job.get("id", "")
        if not job_id or job_id in seen:
            continue
        override = override_items.get(job_id, {})
        signature = str(override.get("signature", "")).strip()
        if signature and signature != compute_service_scope_signature(job):
            append_unique_job_id(targets, seen, job_id)
    return targets


def incremental_role_group_target_ids(payload: dict, delta: dict) -> list[str]:
    """Refresh changed rows plus stale role classifier decisions for unchanged rows."""
    targets: list[str] = []
    seen: set[str] = set()
    for job_id in delta.get("addedIds", []) + delta.get("changedIds", []):
        append_unique_job_id(targets, seen, job_id)

    summary_items = load_summary_store().get("items", {})
    override_items = load_role_group_override_store().get("items", {})
    for job in payload.get("jobs", []):
        job_id = job.get("id", "")
        if not job_id or job_id in seen:
            continue
        override = override_items.get(job_id, {})
        signature = str(override.get("signature", "")).strip()
        if signature and signature != compute_role_group_signature(job, summary_items.get(job_id, {})):
            append_unique_job_id(targets, seen, job_id)
    return targets


def refresh_company_clusters(config: dict) -> int:
    rows = build_base_rows(get_jobs_payload())
    company_profiles = build_company_profiles(rows)
    cluster_items = build_dynamic_cluster_payload(rows, company_profiles)
    cluster_items = request_cluster_labels(
        config,
        build_cluster_label_seeds(cluster_items, company_profiles),
    )
    if cluster_items:
        save_company_clusters(config, cluster_items)
    return len(cluster_items or [])


def run_incremental_summary_refresh(
    config: dict,
    job_ids: list[str],
    batch_size: int,
    prompt_profile: str,
) -> dict:
    payload = get_jobs_payload()
    jobs_by_id = {job["id"]: job for job in payload.get("jobs", []) if job.get("id")}
    jobs = [jobs_by_id[job_id] for job_id in job_ids if job_id in jobs_by_id]
    jobs.sort(key=lambda job: job.get("lastSeenAt", ""), reverse=True)

    processed = 0
    saved = 0
    errors = []

    for batch in chunked(jobs, max(1, batch_size)):
        summaries = request_summaries_resilient(
            config,
            batch,
            prompt_profile=prompt_profile,
        )
        returned = {item["id"] for item in summaries}
        missing_ids = [job["id"] for job in batch if job["id"] not in returned]

        if summaries:
            save_summary_batch(
                config,
                summaries,
                prompt_profile=prompt_profile,
            )
            saved += len(summaries)

        if missing_ids:
            errors.append(
                {
                    "batchJobIds": missing_ids,
                    "error": "Model returned incomplete summary set",
                }
            )
        processed += len(batch)

    return {
        "processed": processed,
        "saved": saved,
        "errors": errors,
    }


def refresh_service_scope(config: dict, job_ids: list[str], batch_size: int) -> dict:
    return run_service_scope_model_pipeline(
        config,
        job_ids=job_ids or None,
        mode="missing" if not job_ids else "all",
        batch_size=max(1, batch_size),
    )


def refresh_role_groups(config: dict, job_ids: list[str], batch_size: int) -> dict:
    return run_role_group_model_pipeline(
        config,
        job_ids=job_ids or None,
        mode="missing" if not job_ids else "all",
        batch_size=max(1, batch_size),
    )


def rebuild_summary_board() -> dict:
    board = build_summary_board(get_jobs_payload())
    out = _writable(SUMMARY_BOARD_PATH)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(board, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return board


def get_summary_board(force=False) -> dict:
    path = _readable(SUMMARY_BOARD_PATH)
    if force or not path.exists():
        return rebuild_summary_board()
    return json.loads(path.read_text(encoding="utf-8"))


class AppHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):
        return

    def end_headers(self):
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def send_json(self, status_code: int, payload: dict):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_bytes(self, status_code: int, body: bytes, *, content_type: str, filename: str | None = None):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        if filename:
            ascii_name = safe_pdf_filename(pathlib.Path(filename).stem) + pathlib.Path(filename).suffix
            utf8_name = quote(filename)
            self.send_header(
                "Content-Disposition",
                f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_name}",
            )
        self.end_headers()
        self.wfile.write(body)

    def send_sse_headers(self, status_code: int = HTTPStatus.OK):
        self.send_response(status_code)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Connection", "close")
        self.end_headers()

    def send_sse_event(self, event: str, payload: dict):
        body = [f"event: {event}"]
        serialized = json.dumps(payload, ensure_ascii=False)
        for line in serialized.splitlines() or ["{}"]:
            body.append(f"data: {line}")
        chunk = ("\n".join(body) + "\n\n").encode("utf-8")
        self.wfile.write(chunk)
        self.wfile.flush()

    def parse_json_body(self) -> dict:
        content_length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(content_length) if content_length else b"{}"
        try:
            return json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON body: {exc}") from exc

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/summary-board":
            query = parse_qs(parsed.query)
            board = get_summary_board(force=query.get("refresh") == ["1"])
            return self.send_json(HTTPStatus.OK, board)

        if parsed.path == "/api/health":
            board = get_summary_board(force=False)
            return self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "jobs": board["overview"]["totalJobs"],
                    "summaryCoverage": board["overview"]["summaryCoverage"],
                    "missingSummaries": board["overview"]["missingSummaries"],
                },
            )

        return super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path == "/api/summaries/run":
            return self.handle_summaries_run()
        if parsed.path == "/api/source/sync":
            return self.handle_source_sync()
        if parsed.path == "/api/role-resume-guides/pdf":
            return self.handle_role_resume_guides_pdf()
        if parsed.path == "/api/role-resume-guides/stream":
            return self.handle_role_resume_guides_stream()
        if parsed.path == "/api/role-resume-guides":
            return self.handle_role_resume_guides()
        if parsed.path == "/api/company-insight":
            return self.handle_company_insight()
        if parsed.path == "/api/rebuild":
            board = rebuild_summary_board()
            return self.send_json(HTTPStatus.OK, {"ok": True, "board": board})

        return self.send_json(HTTPStatus.NOT_FOUND, {"ok": False, "error": "Not found"})

    def handle_summaries_run(self):
        try:
            body = self.parse_json_body()
            config = merge_model_config(body.get("config"))
            batch_size = max(1, int(body.get("batchSize", 8)))
            limit_jobs = max(0, int(body.get("limitJobs", batch_size)))
            mode = body.get("mode", "missing")
            requested_ids = body.get("jobIds") or []
            prompt_profile = body.get("promptProfile") or get_release_prompt_profile()

            payload = get_jobs_payload()
            jobs = payload["jobs"]
            summary_store = load_summary_store()
            summary_items = summary_store.get("items", {})

            if requested_ids:
                requested_set = set(requested_ids)
                jobs = [job for job in jobs if job["id"] in requested_set]
            elif mode == "missing":
                jobs = [
                    job
                    for job in jobs
                    if job["id"] not in summary_items
                    or summary_needs_refresh(summary_items[job["id"]])
                ]

            jobs.sort(key=lambda job: job.get("lastSeenAt", ""), reverse=True)
            if limit_jobs > 0:
                jobs = jobs[:limit_jobs]

            if not jobs:
                board = get_summary_board(force=False)
                return self.send_json(
                    HTTPStatus.OK,
                    {
                        "ok": True,
                        "processed": 0,
                        "saved": 0,
                        "errors": [],
                        "overview": board["overview"],
                    },
                )

            processed = 0
            saved = 0
            errors = []
            processed_ids = []

            for batch in chunked(jobs, batch_size):
                summaries = request_summaries_resilient(
                    config,
                    batch,
                    prompt_profile=prompt_profile,
                )
                returned = {item["id"] for item in summaries}
                missing_ids = [job["id"] for job in batch if job["id"] not in returned]

                if summaries:
                    save_summary_batch(
                        config,
                        summaries,
                        prompt_profile=prompt_profile,
                    )
                    saved += len(summaries)

                if missing_ids:
                    errors.append(
                        {
                            "batchJobIds": missing_ids,
                            "error": "Model returned incomplete summary set",
                        }
                    )
                processed += len(batch)
                processed_ids.extend(job["id"] for job in batch)

            service_scope = {
                "enabled": False,
                "ok": False,
                "candidateCount": 0,
                "processed": 0,
                "applied": 0,
                "include": 0,
                "exclude": 0,
                "lowConfidence": 0,
            }
            role_groups = {
                "enabled": False,
                "ok": False,
                "candidateCount": 0,
                "processed": 0,
                "applied": 0,
                "lowConfidence": 0,
            }
            if processed_ids and config.get("baseUrl") and config.get("model"):
                service_scope["enabled"] = True
                try:
                    scope_result = refresh_service_scope(config, processed_ids, batch_size)
                    service_scope.update(scope_result)
                    service_scope["ok"] = True
                except Exception as scope_error:
                    service_scope["error"] = str(scope_error)
                role_groups["enabled"] = True
                try:
                    role_result = refresh_role_groups(config, processed_ids, batch_size)
                    role_groups.update(role_result)
                    role_groups["ok"] = True
                except Exception as role_error:
                    role_groups["error"] = str(role_error)

            try:
                rows = build_base_rows(get_jobs_payload())
                company_profiles = build_company_profiles(rows)
                cluster_items = build_dynamic_cluster_payload(rows, company_profiles)
                cluster_items = request_cluster_labels(
                    config,
                    build_cluster_label_seeds(cluster_items, company_profiles),
                )
                if cluster_items:
                    save_company_clusters(config, cluster_items)
            except Exception as cluster_error:
                errors.append({"clusters": str(cluster_error)})
            board = rebuild_summary_board()
            return self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "processed": processed,
                    "saved": saved,
                    "errors": errors,
                    "serviceScope": service_scope,
                    "roleGroups": role_groups,
                    "overview": board["overview"],
                },
            )
        except Exception as exc:
            return self.send_json(
                HTTPStatus.BAD_GATEWAY,
                {"ok": False, "error": str(exc)},
            )

    def handle_source_sync(self):
        try:
            body = self.parse_json_body()
            before_payload = safe_get_jobs_payload()
            use_stage2_deploy = body.get("useStage2Deploy", True) is not False
            result = sync_sheet_snapshot(
                use_stage2_deploy=use_stage2_deploy,
                allow_shrink=use_stage2_deploy,
            )
            payload = result["payload"]
            delta = compute_sync_delta(before_payload, payload)
            pruned = prune_summary_items(delta["removedIds"])

            config = merge_model_config(body.get("config"))
            batch_size = max(1, int(body.get("batchSize", 2)))
            prompt_profile = body.get("promptProfile") or get_release_prompt_profile()
            # Source sync is the deployment handoff from the external sheet pipeline.
            # Model enrichment must stay opt-in so this project does not overwrite
            # sheet-authored increment results during review/deploy sync.
            auto_enrich = bool(body.get("autoEnrich", False))

            summaries = {
                "enabled": False,
                "ok": False,
                "targetCount": 0,
                "processed": 0,
                "saved": 0,
                "errors": [],
                "pruned": pruned,
            }
            clusters = {
                "enabled": False,
                "ok": False,
                "saved": 0,
            }
            service_scope = {
                "enabled": False,
                "ok": False,
                "candidateCount": 0,
                "processed": 0,
                "applied": 0,
                "include": 0,
                "exclude": 0,
                "lowConfidence": 0,
            }
            role_groups = {
                "enabled": False,
                "ok": False,
                "candidateCount": 0,
                "processed": 0,
                "applied": 0,
                "lowConfidence": 0,
            }

            has_model_config = bool(config.get("baseUrl") and config.get("model"))
            if auto_enrich and has_model_config:
                target_ids = incremental_summary_target_ids(payload, delta)
                summaries["enabled"] = True
                summaries["targetCount"] = len(target_ids)
                try:
                    if target_ids:
                        refresh_result = run_incremental_summary_refresh(
                            config,
                            target_ids,
                            batch_size,
                            prompt_profile,
                        )
                        summaries.update(refresh_result)
                    summaries["ok"] = True
                except Exception as summary_error:
                    summaries["error"] = str(summary_error)

                scope_target_ids = incremental_service_scope_target_ids(payload, delta)
                role_target_ids = incremental_role_group_target_ids(payload, delta)
                if scope_target_ids:
                    service_scope["enabled"] = True
                    try:
                        scope_result = refresh_service_scope(config, scope_target_ids, batch_size)
                        service_scope.update(scope_result)
                        service_scope["ok"] = True
                    except Exception as scope_error:
                        service_scope["error"] = str(scope_error)
                if role_target_ids:
                    role_groups["enabled"] = True
                    try:
                        role_result = refresh_role_groups(config, role_target_ids, batch_size)
                        role_groups.update(role_result)
                        role_groups["ok"] = True
                    except Exception as role_error:
                        role_groups["error"] = str(role_error)

                if delta["added"] or delta["changed"] or delta["removed"]:
                    clusters["enabled"] = True
                    try:
                        clusters["saved"] = refresh_company_clusters(config)
                        clusters["ok"] = True
                    except Exception as cluster_error:
                        clusters["error"] = str(cluster_error)

            board = get_summary_board(force=True)
            return self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "rowCount": result["rowCount"],
                    "source": result["payload"]["source"],
                    "delta": delta,
                    "summaries": summaries,
                    "serviceScope": service_scope,
                    "roleGroups": role_groups,
                    "clusters": clusters,
                    "overview": board["overview"],
                },
            )
        except Exception as exc:
            return self.send_json(
                HTTPStatus.BAD_GATEWAY,
                {"ok": False, "error": str(exc)},
            )

    def handle_role_resume_guides(self):
        try:
            body = self.parse_json_body()
            role = normalize_inline_text(body.get("role", ""))
            activity_filter = normalize_inline_text(body.get("activityFilter", "")) or "all"
            config = body.get("config") if isinstance(body.get("config"), dict) else None
            force_refresh = bool(body.get("forceRefresh"))
            if not role or role == "전체":
                return self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "error": "직무를 하나 선택한 뒤 다시 시도해주세요."},
                )
            if role == "기타":
                return self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "error": "기타 묶음은 시장 신호가 섞여 있어 목표 이력서를 생성하지 않습니다."},
                )

            result = get_role_resume_guides(
                role,
                activity_filter=activity_filter,
                config=config,
                force_refresh=force_refresh,
            )
            return self.send_json(
                HTTPStatus.OK,
                {
                    "ok": True,
                    "role": result["role"],
                    "activityFilter": result["activityFilter"],
                    "marketProfile": result["marketProfile"],
                    "payload": result["payload"],
                    "cached": result.get("cached", False),
                    "stale": result.get("stale", False),
                    "provider": result.get("provider", {}),
                },
            )
        except ValueError as exc:
            return self.send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": str(exc)},
            )
        except Exception as exc:
            return self.send_json(
                HTTPStatus.BAD_GATEWAY,
                {"ok": False, "error": str(exc)},
            )

    def handle_role_resume_guides_pdf(self):
        try:
            body = self.parse_json_body()
            role = normalize_inline_text(body.get("role", ""))
            payload = body.get("payload") if isinstance(body.get("payload"), dict) else {}
            if not role:
                role = normalize_inline_text(payload.get("role", ""))
            pdf_bytes, filename = build_role_resume_pdf_bytes(role, payload)
            return self.send_bytes(
                HTTPStatus.OK,
                pdf_bytes,
                content_type="application/pdf",
                filename=filename,
            )
        except ValueError as exc:
            return self.send_json(
                HTTPStatus.BAD_REQUEST,
                {"ok": False, "error": str(exc)},
            )
        except Exception as exc:
            return self.send_json(
                HTTPStatus.BAD_GATEWAY,
                {"ok": False, "error": str(exc)},
            )

    def handle_role_resume_guides_stream(self):
        try:
            body = self.parse_json_body()
            role = normalize_inline_text(body.get("role", ""))
            activity_filter = normalize_inline_text(body.get("activityFilter", "")) or "all"
            config = body.get("config") if isinstance(body.get("config"), dict) else None
            force_refresh = bool(body.get("forceRefresh"))
            if not role or role == "전체":
                return self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "error": "직무를 하나 선택한 뒤 다시 시도해주세요."},
                )
            if role == "기타":
                return self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "error": "기타 묶음은 시장 신호가 섞여 있어 목표 이력서를 생성하지 않습니다."},
                )

            self.send_sse_headers()

            def emit(event: str, payload: dict):
                self.send_sse_event(event, payload)

            emit("status", {"message": "시장 신호를 집계하고 있습니다."})
            market_profile = build_role_resume_market_profile(role, activity_filter=activity_filter)
            merged_config = merge_role_resume_model_config(config)
            default_config = default_role_resume_model_config()
            cache_key = role_resume_cache_key(market_profile["role"], market_profile["activityFilter"])
            signature = stable_signature(
                {
                    "schemaVersion": ROLE_RESUME_SCHEMA_VERSION,
                    "marketProfile": market_profile,
                    "provider": {
                        "baseUrl": merged_config.get("baseUrl", ""),
                        "model": merged_config.get("model", ""),
                    },
                }
            )
            cache = load_role_resume_guide_cache()
            cached = cache.get("items", {}).get(cache_key, {})
            cached_payload = role_resume_cached_payload(cached)
            cached_document = role_resume_cached_document(cached)
            cached_version = cached_payload.get("schemaVersion") if isinstance(cached_payload, dict) else None
            fallback_cached = cached if has_role_resume_cached_document(cached) else find_role_resume_cached_entry(
                cache,
                market_profile["role"],
                market_profile["activityFilter"],
            )
            fallback_payload = role_resume_cached_payload(fallback_cached)
            fallback_document = role_resume_cached_document(fallback_cached)

            if (
                not force_refresh
                and cached.get("signature") == signature
                and cached_version == ROLE_RESUME_SCHEMA_VERSION
                and isinstance(cached_document, dict)
                and cached_document.get("headline")
            ):
                return emit(
                    "final",
                    {
                        "ok": True,
                        "role": market_profile["role"],
                        "activityFilter": market_profile["activityFilter"],
                        "marketProfile": market_profile,
                        "payload": cached_payload,
                        "cached": True,
                        "provider": cached.get("provider", {}),
                    },
                )

            if not role_resume_model_configured(merged_config):
                if not force_refresh and isinstance(fallback_document, dict) and fallback_document.get("headline"):
                    emit(
                        "final",
                        {
                            "ok": True,
                            "role": market_profile["role"],
                            "activityFilter": market_profile["activityFilter"],
                            "marketProfile": market_profile,
                            "payload": fallback_payload,
                            "cached": True,
                            "stale": True,
                            "provider": fallback_cached.get("provider", {}),
                        },
                    )
                    return
                emit("error", {"error": "AI resume endpoint와 model 설정이 필요합니다."})
                return

            try:
                live_result = request_role_resume_guides_from_model_streaming(market_profile, merged_config, emit)
            except Exception as exc:
                if role_resume_model_configured(default_config) and role_resume_provider_differs(merged_config, default_config):
                    try:
                        emit("status", {"message": "기본 AI 설정으로 다시 시도하고 있습니다."})
                        live_result = request_role_resume_guides_from_model_streaming(market_profile, default_config, emit)
                    except Exception:
                        live_result = None
                else:
                    live_result = None

                if not live_result:
                    if not force_refresh and isinstance(fallback_document, dict) and fallback_document.get("headline"):
                        emit(
                            "final",
                            {
                                "ok": True,
                                "role": market_profile["role"],
                                "activityFilter": market_profile["activityFilter"],
                                "marketProfile": market_profile,
                                "payload": fallback_payload,
                                "cached": True,
                                "stale": True,
                                "provider": fallback_cached.get("provider", {}),
                            },
                        )
                        return
                    if "Connection refused" in str(exc):
                        emit("error", {"error": "AI endpoint에 연결할 수 없습니다. resume 전용 모델 주소를 확인해주세요."})
                    else:
                        emit("error", {"error": f"AI resume generation failed: {exc}"})
                    return

            cache.setdefault("items", {})[cache_key] = {
                "role": market_profile["role"],
                "activityFilter": market_profile["activityFilter"],
                "signature": signature,
                "payload": live_result["guides"],
                "provider": live_result.get("provider", {}),
                "updatedAt": now_iso(),
            }
            save_role_resume_guide_cache(cache)
            emit(
                "final",
                {
                    "ok": True,
                    "role": market_profile["role"],
                    "activityFilter": market_profile["activityFilter"],
                    "marketProfile": market_profile,
                    "payload": live_result["guides"],
                    "cached": False,
                    "provider": live_result.get("provider", {}),
                },
            )
        except BrokenPipeError:
            return
        except Exception as exc:
            try:
                self.send_sse_headers(HTTPStatus.OK)
                self.send_sse_event("error", {"error": str(exc)})
            except Exception:
                return

    def handle_company_insight(self):
        try:
            body = self.parse_json_body()
            job_id = str(body.get("jobId", "")).strip()
            if not job_id:
                return self.send_json(
                    HTTPStatus.BAD_REQUEST,
                    {"ok": False, "error": "jobId is required"},
                )
            config = body.get("config") if isinstance(body.get("config"), dict) else None
            result = get_company_insight(job_id, config=config)
            return self.send_json(HTTPStatus.OK, {"ok": True, **result})
        except Exception as exc:
            return self.send_json(
                HTTPStatus.BAD_GATEWAY,
                {"ok": False, "error": str(exc)},
            )


def main():
    host = os.environ.get("CAREER_DASHBOARD_HOST", "0.0.0.0")
    port = int(os.environ.get("CAREER_DASHBOARD_PORT", "4173"))
    server = ThreadingHTTPServer((host, port), AppHandler)
    print(f"Serving summary table on http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
