#!/usr/bin/env python3

import argparse
import json
import pathlib
import re
import urllib.request

from ai_runtime import (
    canonicalize_term,
    choose_focus_label,
    extract_json_object,
    is_generic_keyword,
    normalize_inline_text,
)


ROOT = pathlib.Path(__file__).resolve().parent.parent
DEFAULT_WAVE_PATH = ROOT / "data" / "review_wave_001.json"
DEFAULT_OUTPUT_PATH = ROOT / "data" / "review_suggestions_001.json"
DEFAULT_MARKDOWN_PATH = ROOT / "docs" / "review_suggestions_001.md"

FOCUS_HINTS = [
    ("rag", "RAG"),
    ("검색증강생성", "RAG"),
    ("llm", "LLM"),
    ("엘엘엠", "LLM"),
    ("nlp", "NLP"),
    ("엔엘피", "NLP"),
    ("onnx", "ONNX"),
    ("오엔엔엑스", "ONNX"),
    ("npu", "NPU"),
    ("컴파일러", "컴파일러"),
    ("객체 인식", "객체 인식"),
    ("얼굴인식", "얼굴인식"),
    ("위조", "위조 판별"),
    ("영상처리", "영상 처리"),
    ("컴퓨터 비전", "컴퓨터 비전"),
    ("컴퓨터비전", "컴퓨터 비전"),
    ("생체신호", "생체신호"),
    ("심전도", "심전도"),
    ("의료", "의료 데이터"),
    ("임상", "의료 데이터"),
    ("로봇", "로보틱스"),
    ("강화 학습", "강화학습"),
    ("강화학습", "강화학습"),
    ("서빙", "모델 서빙"),
    ("serving", "모델 서빙"),
    ("파이프라인", "데이터 파이프라인"),
    ("mlops", "MLOps"),
    ("엠엘옵스", "MLOps"),
    ("클라우드", "클라우드"),
    ("api", "API"),
    ("검색", "검색"),
    ("추천", "추천"),
    ("자율주행", "자율주행"),
    ("검증", "검증"),
]

SUMMARY_CLEANUPS = (
    (r"^[•·\\-\\s]+", ""),
    (r"^&\\s*", ""),
    (r"^(는|를|을|이|가|및)\\s+", ""),
    (r"^크게\\s+", ""),
    (r"합니다\\.?$", ""),
    (r"수행합니다\\.?$", ""),
    (r"담당합니다\\.?$", ""),
    (r"담당하게 됩니다\\.?$", ""),
    (r"개발합니다\\.?$", "개발"),
    (r"구축합니다\\.?$", "구축"),
    (r"설계합니다\\.?$", "설계"),
    (r"개선합니다\\.?$", "개선"),
    (r"운영합니다\\.?$", "운영"),
    (r"평가합니다\\.?$", "평가"),
    (r"주도합니다\\.?$", "주도"),
    (r"모집$", ""),
    (r"채용$", ""),
    (r"영입$", ""),
)


def compact(values, limit=6) -> list[str]:
    items = []
    seen = set()
    for value in values or []:
        cleaned = normalize_inline_text(value)
        if not cleaned or cleaned in seen:
            continue
        seen.add(cleaned)
        items.append(cleaned)
        if len(items) >= limit:
            break
    return items


def normalize_suggestion_items(payload: dict) -> list[dict]:
    items = payload.get("items", [])
    if not isinstance(items, list):
        return []

    normalized = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        job_id = normalize_inline_text(item.get("id", ""))
        if not job_id or job_id in seen:
            continue
        seen.add(job_id)

        summary = normalize_inline_text(item.get("suggestedSummary", ""))
        focus = canonicalize_term(item.get("suggestedFocusLabel", ""))
        keywords = []
        raw_keywords = item.get("suggestedKeywords", [])
        if isinstance(raw_keywords, list):
            for keyword in raw_keywords:
                cleaned = canonicalize_term(keyword)
                if cleaned and not is_generic_keyword(cleaned) and cleaned not in keywords:
                    keywords.append(cleaned)

        quality = normalize_inline_text(item.get("suggestedQuality", "")).lower()
        if quality not in {"high", "medium", "low"}:
            quality = "medium" if summary else "low"

        focus = choose_focus_label(
            role=normalize_inline_text(item.get("roleGroup", "")),
            summary=summary,
            focus_label=focus,
            keywords=keywords,
        )
        rationale = normalize_inline_text(item.get("rationale", ""))
        normalized.append(
            {
                "id": job_id,
                "suggestedSummary": summary,
                "suggestedFocusLabel": focus,
                "suggestedKeywords": keywords[:6],
                "suggestedQuality": quality,
                "rationale": rationale[:120],
            }
        )
    return normalized


def normalize_text_for_match(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", " ", normalize_inline_text(value).lower()).strip()


def title_echo_ratio(summary: str, title: str) -> float:
    left = set(normalize_text_for_match(summary).split())
    right = set(normalize_text_for_match(title).split())
    if not left or not right:
        return 0.0
    return len(left & right) / max(1, min(len(left), len(right)))


def clean_summary_text(value: str) -> str:
    text = normalize_inline_text(value)
    for pattern, replacement in SUMMARY_CLEANUPS:
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        text = normalize_inline_text(text)
    text = text.strip(" -:·,./")
    return normalize_inline_text(text)


def extract_focus_from_source(item: dict) -> str:
    source = item.get("source", {})
    haystacks = [
        normalize_inline_text(item.get("title", "")),
        normalize_inline_text(source.get("detailBody", "")),
        " ".join(compact(source.get("tasks", []), limit=8)),
        " ".join(compact(source.get("requirements", []), limit=8)),
        " ".join(compact(source.get("skills", []), limit=10)),
    ]
    scored = []
    seen = set()
    for haystack in haystacks:
        lowered = haystack.lower()
        for needle, label in FOCUS_HINTS:
            if needle in lowered and label not in seen:
                seen.add(label)
                score = lowered.count(needle)
                if "detailBody" in haystack:
                    score += 1
                scored.append((score, label))
    if not scored:
        current = item.get("current", {}).get("focusLabel", "")
        if current and not is_generic_keyword(current):
            return canonicalize_term(current)
        return ""
    scored.sort(key=lambda entry: (-entry[0], len(entry[1]), entry[1]))
    return scored[0][1]


def extract_summary_from_source(item: dict, focus_label: str) -> str:
    source = item.get("source", {})
    candidates = []
    candidates.extend(compact(source.get("tasks", []), limit=6))
    candidates.extend(compact([source.get("detailBody", "")], limit=1))
    title = normalize_inline_text(item.get("title", ""))

    for candidate in candidates:
        cleaned = clean_summary_text(candidate)
        if not cleaned:
            continue
        if any(term in cleaned for term in ("채용", "모집", "영입", "전형", "지원")):
            continue
        if cleaned.startswith(("모든 포지션", "제출하신", "확인해주세요", "공고명", "양식")):
            continue
        if "근무가 가능" in cleaned or "혜택 및 복지" in cleaned:
            continue
        if title_echo_ratio(cleaned, title) >= 0.7:
            continue
        if len(cleaned) < 8:
            continue
        if len(cleaned) > 36:
            cleaned = cleaned[:36].rstrip(" ,.-")
        if cleaned.startswith(("를 ", "을 ", "이 ", "가 ", "및 ", "는 ")):
            continue
        if focus_label and focus_label not in cleaned and len(cleaned) <= 28:
            if focus_label in {"RAG", "LLM", "NLP", "ONNX", "API", "MLOps"}:
                return f"{focus_label} 기반 {cleaned}"[:36].rstrip(" ,.-")
        return cleaned
    return ""


def extract_keywords_from_source(item: dict, focus_label: str) -> list[str]:
    source = item.get("source", {})
    keywords = []
    if focus_label:
        keywords.append(focus_label)
    for value in compact(source.get("skills", []), limit=8):
        cleaned = canonicalize_term(value)
        if cleaned and not is_generic_keyword(cleaned) and cleaned not in keywords:
            keywords.append(cleaned)
    for needle, label in FOCUS_HINTS:
        lowered = normalize_inline_text(source.get("detailBody", "")).lower()
        if needle in lowered and label not in keywords:
            keywords.append(label)
    return keywords[:5]


def suggestion_is_usable(item: dict, suggestion: dict) -> bool:
    if not suggestion:
        return False
    summary = clean_summary_text(suggestion.get("suggestedSummary", ""))
    focus = canonicalize_term(suggestion.get("suggestedFocusLabel", ""))
    keywords = [canonicalize_term(value) for value in suggestion.get("suggestedKeywords", []) or []]
    title = item.get("title", "")
    if not summary or not focus:
        return False
    if title_echo_ratio(summary, title) >= 0.7:
        return False
    if any(term in summary for term in ("모집", "채용", "영입", "공고")):
        return False
    if is_generic_keyword(focus):
        return False
    if len(keywords) < 2:
        return False
    return True


def heuristic_suggestion(item: dict) -> dict:
    focus = extract_focus_from_source(item)
    summary = extract_summary_from_source(item, focus)
    keywords = extract_keywords_from_source(item, focus)
    quality = "medium" if summary and focus and len(keywords) >= 2 else "low"
    if quality == "low":
        if not summary:
            summary = ""
        if not focus:
            focus = ""
    return {
        "id": item["id"],
        "suggestedSummary": summary,
        "suggestedFocusLabel": focus,
        "suggestedKeywords": keywords,
        "suggestedQuality": quality,
        "rationale": "source 필드 기반으로 초안을 보강했습니다.",
    }


def build_messages(items: list[dict]) -> list[dict]:
    system_prompt = (
        "당신은 채용 인텔리전스 서비스의 리뷰 보조 편집자입니다. "
        "입력으로 주어진 current 결과는 틀릴 수 있으며, source 필드만 근거로 더 나은 교정 초안을 작성하세요. "
        "반드시 strict JSON only 로 "
        "{\"items\":[{\"id\":\"...\",\"suggestedSummary\":\"...\",\"suggestedFocusLabel\":\"...\",\"suggestedKeywords\":[\"...\"],\"suggestedQuality\":\"medium\",\"rationale\":\"...\"}]}"
        " 형태만 반환하세요. "
        "모든 input id에 대해 item 하나를 반드시 반환하세요. "
        "suggestedSummary는 게시용 식별 문구이며 12~36자의 한국어 구문으로 쓰세요. "
        "직무명 반복, 회사 소개, 채용 안내, 복지, 공고 제목 echo는 금지합니다. "
        "suggestedFocusLabel은 그룹 기준으로 쓸 짧은 명사구 1개만 허용합니다. "
        "suggestedKeywords는 2~5개의 짧은 명사구입니다. "
        "조사형, 학력/경력 표현, 제품/서비스 같은 포괄어, 문장 조각은 금지합니다. "
        "input machineIssues는 참고용이며, output에는 반영하지 말고 source 근거만 사용하세요. "
        "근거가 약하면 suggestedQuality는 low로 두고, summary와 focusLabel은 비울 수 있습니다. "
        "rationale은 왜 그렇게 고쳤는지 40자 이내 한국어 한 문장으로 쓰세요."
    )
    payload = {
        "items": [
            {
                "id": item["id"],
                "company": item.get("company", ""),
                "title": item.get("title", ""),
                "roleGroup": item.get("roleGroup", ""),
                "current": item.get("current", {}),
                "machineIssues": [issue.get("code", "") for issue in item.get("machineReview", {}).get("issues", [])],
                "source": {
                    "detailBody": normalize_inline_text(item.get("source", {}).get("detailBody", ""))[:1400],
                    "tasks": compact(item.get("source", {}).get("tasks", []), limit=5),
                    "requirements": compact(item.get("source", {}).get("requirements", []), limit=5),
                    "preferred": compact(item.get("source", {}).get("preferred", []), limit=5),
                    "skills": compact(item.get("source", {}).get("skills", []), limit=8),
                },
            }
            for item in items
        ]
    }
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
    ]


def request_suggestions(config: dict, items: list[dict]) -> list[dict]:
    base_url = (config.get("baseUrl") or "").rstrip("/")
    model = (config.get("model") or "").strip()
    api_key = config.get("apiKey", "")
    temperature = float(config.get("temperature", 0.0))

    payload = {
        "model": model,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
        "messages": build_messages(items),
    }
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"

    request = urllib.request.Request(
        f"{base_url}/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        body = json.loads(response.read().decode("utf-8"))
    content = body["choices"][0]["message"]["content"]
    parsed = extract_json_object(content)
    return normalize_suggestion_items(parsed)


def request_suggestions_resilient(config: dict, items: list[dict], batch_size: int) -> list[dict]:
    collected = []
    seen = set()
    for start in range(0, len(items), batch_size):
        batch = items[start : start + batch_size]
        try:
            response_items = request_suggestions(config, batch)
        except Exception:
            response_items = []
            for item in batch:
                try:
                    response_items.extend(request_suggestions(config, [item]))
                except Exception:
                    continue
        for item in response_items:
            if item["id"] in seen:
                continue
            seen.add(item["id"])
            collected.append(item)
    return collected


def build_markdown(items: list[dict], suggestions_by_id: dict) -> str:
    lines = ["# 리뷰 수정 제안 초안", ""]
    for index, item in enumerate(items, start=1):
        suggestion = suggestions_by_id.get(item["id"], {})
        lines.extend(
            [
                f"## {index}. {item.get('company', '')} | {item.get('title', '')}",
                "",
                f"- current summary: {item.get('current', {}).get('summary', '')}",
                f"- current focus: `{item.get('current', {}).get('focusLabel', '')}`",
                f"- current keywords: {', '.join(item.get('current', {}).get('keywords', []))}",
                f"- suggested summary: {suggestion.get('suggestedSummary', '')}",
                f"- suggested focus: `{suggestion.get('suggestedFocusLabel', '')}`",
                f"- suggested keywords: {', '.join(suggestion.get('suggestedKeywords', []))}",
                f"- suggested quality: `{suggestion.get('suggestedQuality', '')}`",
                f"- rationale: {suggestion.get('rationale', '')}",
                "",
            ]
        )
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--wave", default=str(DEFAULT_WAVE_PATH))
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT_PATH))
    parser.add_argument("--markdown-output", default=str(DEFAULT_MARKDOWN_PATH))
    parser.add_argument("--base-url", default="http://127.0.0.1:11434/v1")
    parser.add_argument("--model", default="qwen2.5:7b")
    parser.add_argument("--api-key", default="")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--topn", type=int, default=10)
    parser.add_argument("--batch-size", type=int, default=4)
    parser.add_argument("--skip-model", action="store_true")
    args = parser.parse_args()

    wave = json.loads(pathlib.Path(args.wave).read_text(encoding="utf-8"))
    candidates = wave.get("items", [])[: args.topn]
    config = {
        "baseUrl": args.base_url,
        "model": args.model,
        "apiKey": args.api_key,
        "temperature": args.temperature,
    }
    suggestions = []
    suggestions_by_id = {}
    if not args.skip_model:
        suggestions = request_suggestions_resilient(config, candidates, batch_size=max(1, args.batch_size))
        suggestions_by_id = {item["id"]: item for item in suggestions}

    finalized = []
    for item in candidates:
        suggestion = suggestions_by_id.get(item["id"], {})
        if not suggestion_is_usable(item, suggestion):
            suggestion = heuristic_suggestion(item)
        else:
            suggestion["suggestedSummary"] = clean_summary_text(suggestion.get("suggestedSummary", ""))
        if not suggestion.get("suggestedFocusLabel"):
            suggestion["suggestedFocusLabel"] = extract_focus_from_source(item)
        if not suggestion.get("suggestedKeywords"):
            suggestion["suggestedKeywords"] = extract_keywords_from_source(item, suggestion.get("suggestedFocusLabel", ""))
        if suggestion.get("suggestedQuality") not in {"high", "medium", "low"}:
            suggestion["suggestedQuality"] = "medium" if suggestion.get("suggestedSummary") else "low"
        finalized.append(suggestion)
    suggestions_by_id = {item["id"]: item for item in finalized}

    payload = {
        "generatedAt": pathlib.Path(args.wave).stat().st_mtime,
        "sourceWave": str(pathlib.Path(args.wave)),
        "model": {"baseUrl": args.base_url, "model": args.model, "temperature": args.temperature},
        "items": finalized,
    }

    output_path = pathlib.Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    markdown = build_markdown(candidates, suggestions_by_id)
    markdown_path = pathlib.Path(args.markdown_output)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(markdown, encoding="utf-8")

    print(f"Wrote review suggestions to {output_path}")
    print(f"Wrote review suggestions markdown to {markdown_path}")


if __name__ == "__main__":
    main()
