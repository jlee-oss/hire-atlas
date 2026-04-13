#!/usr/bin/env python3

import json
import pathlib
import re
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta

from ai_runtime import load_enrichment_store

ROOT = pathlib.Path(__file__).resolve().parent.parent
JOBS_PATH = ROOT / "data" / "jobs.json"
BRIEFING_PATH = ROOT / "data" / "briefing.json"

ROLE_ORDER = [
    "인공지능 엔지니어",
    "인공지능 리서처",
    "데이터 분석가",
    "데이터 사이언티스트",
]

ROLE_KEYS = {
    "인공지능 엔지니어": "ai_engineer",
    "인공지능 리서처": "ai_researcher",
    "데이터 분석가": "data_analyst",
    "데이터 사이언티스트": "data_scientist",
}

SKILL_ALIASES = {
    "파이썬": "Python",
    "python": "Python",
    "엘엘엠": "LLM",
    "llm": "LLM",
    "파이토치": "PyTorch",
    "pytorch": "PyTorch",
    "컴퓨터비전": "Computer Vision",
    "computer vision": "Computer Vision",
    "엠엘옵스": "MLOps",
    "mlops": "MLOps",
    "에이더블유에스": "AWS",
    "aws": "AWS",
    "에스큐엘": "SQL",
    "sql": "SQL",
    "쿠버네티스": "Kubernetes",
    "kubernetes": "Kubernetes",
    "도커": "Docker",
    "docker": "Docker",
    "텐서플로": "TensorFlow",
    "tensorflow": "TensorFlow",
    "지씨피": "GCP",
    "gcp": "GCP",
    "지피유": "GPU",
    "gpu": "GPU",
    "멀티모달": "Multimodal",
    "깃허브": "GitHub",
    "github": "GitHub",
    "검색증강생성": "RAG",
    "rag": "RAG",
    "태블로": "Tableau",
    "tableau": "Tableau",
    "빅쿼리": "BigQuery",
    "bigquery": "BigQuery",
    "이티엘": "ETL",
    "etl": "ETL",
    "엔엘피": "NLP",
    "nlp": "NLP",
    "애저": "Azure",
    "azure": "Azure",
    "카프카": "Kafka",
    "kafka": "Kafka",
    "자바": "Java",
    "java": "Java",
    "스파크": "Spark",
    "spark": "Spark",
    "데이터 분석": "Analytics",
    "추천 시스템": "Recommender Systems",
    "추천시스템": "Recommender Systems",
}

FOCUS_ALIASES = {
    "llm": "LLM",
    "검색": "검색",
    "비전": "비전",
    "로보틱스": "로보틱스",
    "최적화": "최적화",
    "연구": "연구",
    "제품분석": "제품분석",
    "성장분석": "성장분석",
    "광고": "광고",
    "시계열": "시계열",
    "추천": "추천",
    "인프라": "인프라",
    "데이터플랫폼": "데이터플랫폼",
}

GENERIC_TITLE_PATTERNS = [
    re.compile(r"official website", re.IGNORECASE),
    re.compile(r"^채용공고$"),
    re.compile(r"talent pool", re.IGNORECASE),
    re.compile(r"^ai engineer$", re.IGNORECASE),
    re.compile(r"^ai research engineer$", re.IGNORECASE),
]


def read_jobs_payload() -> dict:
    return json.loads(JOBS_PATH.read_text(encoding="utf-8"))


def dedupe(values):
    seen = set()
    result = []
    for value in values:
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result


def normalize_skill(skill: str) -> str:
    raw = (skill or "").strip()
    if not raw:
        return ""
    lowered = raw.lower()
    return SKILL_ALIASES.get(lowered, SKILL_ALIASES.get(raw, raw))


def normalize_focus(focus: str) -> list[str]:
    raw = (focus or "").strip()
    if not raw or raw == "미분류":
        return []

    tokens = []
    for piece in re.split(r"[/,]+", raw):
        token = re.sub(r"\s+", "", piece)
        if not token:
            continue
        normalized = FOCUS_ALIASES.get(token.lower(), FOCUS_ALIASES.get(token, token))
        tokens.append(normalized)
    return dedupe(tokens)


def normalize_track(track: str) -> list[str]:
    raw = (track or "").strip()
    if not raw or raw == "미분류":
        return []

    known = ["일반채용", "학사", "석사", "박사", "전문연구요원", "인턴", "계약직"]
    tokens = [label for label in known if label in raw]
    return dedupe(tokens)


def normalize_experience(experience: str) -> tuple[str, str]:
    raw = (experience or "").strip()
    if not raw or raw == "미기재":
        return "미기재", "unknown"
    if "인턴" in raw:
        return "인턴", "intern"
    if "신입" in raw:
        return "신입", "entry"
    if "주니어" in raw:
        return "주니어", "junior"
    if "리드" in raw:
        return "리드", "lead"
    if "스태프" in raw:
        return "스태프", "staff"
    if "시니어" in raw:
        return "시니어", "senior"

    year_match = re.search(r"(\d+)\s*년\+?", raw)
    if year_match:
        years = int(year_match.group(1))
        if years <= 2:
            return f"경력 {years}년+", "junior"
        if years <= 5:
            return f"경력 {years}년+", "mid"
        if years <= 8:
            return f"경력 {years}년+", "senior"
        return f"경력 {years}년+", "lead"

    if "경력" in raw:
        return "경력(연차 미기재)", "mid"
    return raw, "unknown"


def score_quality(job: dict) -> tuple[int, list[str]]:
    issues = []
    if job["experienceLabel"] == "미기재":
        issues.append("경력수준 불명확")
    if not job["trackLabels"]:
        issues.append("채용트랙 불명확")
    if not job["focusLabels"]:
        issues.append("직무초점 미정리")
    if len(job["normalizedSkills"]) < 2:
        issues.append("핵심기술 부족")
    if len(job["tasks"]) < 2:
        issues.append("주요업무 부족")
    if len(job["requirements"]) < 2:
        issues.append("자격요건 부족")
    if is_generic_title(job["title"]):
        issues.append("제목이 지나치게 포괄적")

    score = 100 - len(issues) * 12
    if job["active"]:
        score += 4
    return max(28, min(score, 100)), issues


def is_generic_title(title: str) -> bool:
    raw = (title or "").strip()
    if not raw:
        return True
    return any(pattern.search(raw) for pattern in GENERIC_TITLE_PATTERNS)


def parse_date(value: str):
    if not value:
        return None
    try:
        return date.fromisoformat(value[:10])
    except ValueError:
        return None


def top_labels(items, count=3):
    return [label for label, _ in items[:count]]


def percent(part: int, whole: int) -> int:
    if whole <= 0:
        return 0
    return round(part / whole * 100)


def apply_enrichment(raw: dict, enrichment_item: dict) -> dict:
    if not enrichment_item:
        return {**raw}

    normalized = enrichment_item.get("normalized", {})
    enriched = {**raw}

    if normalized.get("experience_label"):
        enriched["experience"] = normalized["experience_label"]
    if normalized.get("track_labels"):
        enriched["track"] = " / ".join(normalized["track_labels"])
    if normalized.get("focus_labels"):
        enriched["focus"] = " / ".join(normalized["focus_labels"])
    if normalized.get("skills"):
        enriched["skills"] = normalized["skills"]

    enriched["_ai"] = {
        "appliedAt": enrichment_item.get("appliedAt"),
        "provider": enrichment_item.get("provider", {}),
        "reviewerNote": normalized.get("reviewer_note", ""),
    }
    return enriched


def role_summary(role: str, jobs: list[dict], latest_date: date) -> dict:
    active_jobs = [job for job in jobs if job["active"]]
    recent_cutoff = latest_date - timedelta(days=6)
    recent_jobs = [
        job for job in jobs if job["firstSeenDate"] and job["firstSeenDate"] >= recent_cutoff
    ]
    companies = Counter(job["company"] for job in jobs)
    tiers = Counter(job["companyTier"] for job in jobs if job["companyTier"])
    focuses = Counter(focus for job in jobs for focus in job["focusLabels"])
    tracks = Counter(track for job in jobs for track in job["trackLabels"])
    skills = Counter(skill for job in jobs for skill in job["normalizedSkills"])
    experiences = Counter(job["experienceLabel"] for job in jobs if job["experienceLabel"] != "미기재")
    review_needed = [job for job in jobs if job["needsAiReview"]]

    company_lead = tiers.most_common(1)[0][0] if tiers else "기업군 미상"
    top_track = tracks.most_common(1)[0][0] if tracks else "트랙 미상"
    top_focus = focuses.most_common(1)[0][0] if focuses else "초점 미상"
    top_experience = experiences.most_common(1)[0][0] if experiences else "경력수준 미상"
    top_skills = top_labels(skills.most_common(5), 5)

    narrative = (
        f"{company_lead} 채용이 중심이고, {top_experience} 수요가 가장 두드러집니다. "
        f"{top_track} 트랙 비중이 높으며, {', '.join(top_skills[:3]) or '핵심기술 정보'} "
        f"스택과 {top_focus} 초점이 반복적으로 나타납니다."
    )

    coverage = {
        "experience": percent(sum(1 for job in jobs if job["experienceLabel"] != "미기재"), len(jobs)),
        "track": percent(sum(1 for job in jobs if job["trackLabels"]), len(jobs)),
        "focus": percent(sum(1 for job in jobs if job["focusLabels"]), len(jobs)),
        "skills": percent(sum(1 for job in jobs if len(job["normalizedSkills"]) >= 2), len(jobs)),
        "tasks": percent(sum(1 for job in jobs if len(job["tasks"]) >= 2), len(jobs)),
        "requirements": percent(sum(1 for job in jobs if len(job["requirements"]) >= 2), len(jobs)),
    }

    return {
        "roleKey": ROLE_KEYS[role],
        "roleLabel": role,
        "totalJobs": len(jobs),
        "activeJobs": len(active_jobs),
        "activeRate": percent(len(active_jobs), len(jobs)),
        "recentJobs7d": len(recent_jobs),
        "companyCount": len(companies),
        "topExperience": top_experience,
        "topTracks": top_labels(tracks.most_common(4), 4),
        "topFocuses": top_labels(focuses.most_common(4), 4),
        "topSkills": top_skills,
        "topCompanies": [
            {"name": name, "count": count} for name, count in companies.most_common(4)
        ],
        "qualityCoverage": coverage,
        "averageQualityScore": round(sum(job["qualityScore"] for job in jobs) / max(len(jobs), 1)),
        "reviewNeeded": len(review_needed),
        "narrative": narrative,
    }


def build_briefing(payload: dict) -> dict:
    raw_jobs = payload["jobs"]
    enrichment_store = load_enrichment_store()
    enrichment_items = enrichment_store.get("items", {})
    normalized_jobs = []

    for raw in raw_jobs:
        enriched_raw = apply_enrichment(raw, enrichment_items.get(raw["id"]))
        normalized_skills = dedupe(
            normalize_skill(skill) for skill in enriched_raw.get("skills", [])
        )
        experience_label, experience_band = normalize_experience(
            enriched_raw.get("experience", "")
        )
        track_labels = normalize_track(enriched_raw.get("track", ""))
        focus_labels = normalize_focus(enriched_raw.get("focus", ""))

        job = {
            **enriched_raw,
            "normalizedSkills": [skill for skill in normalized_skills if skill],
            "experienceLabel": experience_label,
            "experienceBand": experience_band,
            "trackLabels": track_labels,
            "focusLabels": focus_labels,
            "firstSeenDate": parse_date(enriched_raw.get("firstSeenAt", "")),
            "lastSeenDate": parse_date(enriched_raw.get("lastSeenAt", "")),
            "aiEnriched": bool(enriched_raw.get("_ai")),
            "aiReviewerNote": enriched_raw.get("_ai", {}).get("reviewerNote", ""),
            "aiAppliedAt": enriched_raw.get("_ai", {}).get("appliedAt"),
            "aiProvider": enriched_raw.get("_ai", {}).get("provider", {}),
        }
        quality_score, issues = score_quality(job)
        job["qualityScore"] = quality_score
        job["reviewIssues"] = issues
        job["needsAiReview"] = len(issues) >= 2
        if is_generic_title(job["title"]) or len(issues) >= 3:
            review_priority = "high"
        elif len(issues) == 2:
            review_priority = "medium"
        else:
            review_priority = "low"
        job["reviewPriority"] = review_priority
        job["aiInstruction"] = ", ".join(issues[:3]) if issues else "검수 필요 없음"
        normalized_jobs.append(job)

    latest_date = max(
        (job["firstSeenDate"] for job in normalized_jobs if job["firstSeenDate"]),
        default=date.today(),
    )

    overview = {
        "totalJobs": len(normalized_jobs),
        "activeJobs": sum(1 for job in normalized_jobs if job["active"]),
        "companies": len({job["company"] for job in normalized_jobs}),
        "recentJobs7d": sum(
            1
            for job in normalized_jobs
            if job["firstSeenDate"] and job["firstSeenDate"] >= latest_date - timedelta(days=6)
        ),
        "aiEnriched": sum(1 for job in normalized_jobs if job["aiEnriched"]),
        "aiReviewNeeded": sum(1 for job in normalized_jobs if job["needsAiReview"]),
        "highPriorityReview": sum(
            1 for job in normalized_jobs if job["reviewPriority"] == "high"
        ),
        "normalizedCoverage": {
            "experience": percent(
                sum(1 for job in normalized_jobs if job["experienceLabel"] != "미기재"),
                len(normalized_jobs),
            ),
            "track": percent(sum(1 for job in normalized_jobs if job["trackLabels"]), len(normalized_jobs)),
            "focus": percent(sum(1 for job in normalized_jobs if job["focusLabels"]), len(normalized_jobs)),
            "skills": percent(
                sum(1 for job in normalized_jobs if len(job["normalizedSkills"]) >= 2),
                len(normalized_jobs),
            ),
            "tasks": percent(sum(1 for job in normalized_jobs if len(job["tasks"]) >= 2), len(normalized_jobs)),
            "requirements": percent(
                sum(1 for job in normalized_jobs if len(job["requirements"]) >= 2),
                len(normalized_jobs),
            ),
        },
    }

    role_groups = defaultdict(list)
    for job in normalized_jobs:
        role_groups[job["role"]].append(job)

    role_briefs = [
        role_summary(role, role_groups.get(role, []), latest_date)
        for role in ROLE_ORDER
        if role_groups.get(role)
    ]

    review_queue = sorted(
        (
            {
                "id": job["id"],
                "company": job["company"],
                "title": job["title"],
                "roleLabel": job["role"],
                "reviewPriority": job["reviewPriority"],
                "reviewIssues": job["reviewIssues"],
                "qualityScore": job["qualityScore"],
                "firstSeenAt": job["firstSeenAt"],
                "lastSeenAt": job["lastSeenAt"],
                "aiInstruction": job["aiInstruction"],
                "aiEnriched": job["aiEnriched"],
                "aiAppliedAt": job["aiAppliedAt"],
                "aiReviewerNote": job["aiReviewerNote"],
            }
            for job in normalized_jobs
            if job["needsAiReview"]
        ),
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item["reviewPriority"]],
            item["qualityScore"],
        ),
    )

    publish_jobs = sorted(
        (
            {
                "id": job["id"],
                "company": job["company"],
                "title": job["title"],
                "roleLabel": job["role"],
                "companyTier": job["companyTier"],
                "active": job["active"],
                "recordState": job["recordState"],
                "experienceLabel": job["experienceLabel"],
                "trackLabels": job["trackLabels"],
                "focusLabels": job["focusLabels"],
                "skills": job["normalizedSkills"],
                "qualityScore": job["qualityScore"],
                "reviewPriority": job["reviewPriority"],
                "needsAiReview": job["needsAiReview"],
                "reviewIssues": job["reviewIssues"],
                "firstSeenAt": job["firstSeenAt"],
                "lastSeenAt": job["lastSeenAt"],
                "jobUrl": job["jobUrl"],
                "aiEnriched": job["aiEnriched"],
                "aiAppliedAt": job["aiAppliedAt"],
                "aiReviewerNote": job["aiReviewerNote"],
            }
            for job in normalized_jobs
        ),
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}[item["reviewPriority"]],
            -datetime.fromisoformat(item["lastSeenAt"]).timestamp() if item["lastSeenAt"] else 0,
        ),
    )

    return {
        "generatedAt": payload["generatedAt"],
        "source": payload["source"],
        "overview": overview,
        "pipeline": {
            "stages": [
                {
                    "label": "원본 수집",
                    "count": overview["totalJobs"],
                    "description": "스크래핑된 공고 원문",
                },
                {
                    "label": "규칙 정규화",
                    "count": overview["totalJobs"],
                    "description": "직무/경력/트랙/스킬 표준 태그 정리",
                },
                {
                    "label": "AI 보정 필요",
                    "count": overview["aiReviewNeeded"],
                    "description": "Qwen 같은 저비용 모델로 우선 재해석할 후보",
                },
                {
                    "label": "AI 반영 완료",
                    "count": overview["aiEnriched"],
                    "description": "보정 결과가 브리핑에 반영된 공고",
                },
                {
                    "label": "고우선 검수",
                    "count": overview["highPriorityReview"],
                    "description": "제목이 모호하거나 필드 누락이 많은 공고",
                },
            ],
            "notes": [
                "경력수준, 트랙, 초점, 기술, 주요업무, 자격요건을 우선 보정 대상으로 봅니다.",
                "직무명은 4개 메인 역할로 고정해 교육회사 관점의 벤치마킹이 가능하도록 맞췄습니다.",
                "AI 보정은 OpenAI 호환 엔드포인트에 연결하면 즉시 적용 가능한 구조로 준비했습니다.",
            ],
        },
        "roleBriefs": role_briefs,
        "reviewQueue": review_queue[:14],
        "jobs": publish_jobs,
    }


def main():
    payload = read_jobs_payload()
    briefing = build_briefing(payload)
    BRIEFING_PATH.write_text(
        json.dumps(briefing, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote briefing to {BRIEFING_PATH}")


if __name__ == "__main__":
    main()
