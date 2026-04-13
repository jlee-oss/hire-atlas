#!/usr/bin/env python3

import argparse
import csv
import io
import json
import os
import re
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from google_sheets_runtime import clear_sheet_values, fetch_sheet_rows, update_sheet_values


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SERVICE_ACCOUNT_JSON = os.environ.get(
    "GOOGLE_SERVICE_ACCOUNT_JSON",
    "/Users/junheelee/Downloads/scraper-491619-a85f7518accf.json",
)
DEFAULT_STAGE1_SPREADSHEET_ID = os.environ.get(
    "GOOGLE_SHEETS_SPREADSHEET_ID",
    "1bG-aT9L_N3SEPT04ZZZ-2jdRqW_agYhrqsn4fNanA5s",
)
DEFAULT_STAGE1_GID = os.environ.get("GOOGLE_SHEETS_GID", "2026513640")
DEFAULT_STAGE1_TITLE = os.environ.get("GOOGLE_SHEETS_SHEET_TITLE", "master 탭")
DEFAULT_STAGE2_SPREADSHEET_ID = os.environ.get(
    "STAGE2_SHEETS_SPREADSHEET_ID",
    "1z8nDYl0y7IDy4iXe1njrmdHzu0bv_6_zBC6gV7Vjqd0",
)
DEFAULT_STAGE2_GID = os.environ.get("STAGE2_SHEETS_GID", "0")
DEFAULT_STAGE2_TITLE = os.environ.get("STAGE2_SHEETS_SHEET_TITLE", "")
OUTPUT_JSON = ROOT / "data" / "stage2_validation_latest.json"
OUTPUT_CSV = ROOT / "data" / "stage2_validation_candidates_latest.csv"
OUTPUT_MD = ROOT / "docs" / "stage2_validation_latest.md"

ALLOWED_ROLES = {
    "인공지능 엔지니어",
    "인공지능 리서처",
    "데이터 사이언티스트",
    "데이터 분석가",
}

NOISE_TERMS = {
    "이상이신",
    "있습니다",
    "채용절차법",
    "광주지사",
    "상세채용",
    "상시채용",
    "경력무관",
    "계약직",
    "정규직",
    "회사내규",
    "우대사항",
    "자격요건",
    "주요업무",
    "검수완료",
    "검수필요",
}

DEEPTECH_PATTERNS = [
    r"로봇",
    r"로보틱스",
    r"자율주행",
    r"컴퓨터\s*비전",
    r"\bvision\b",
    r"\bvlm\b",
    r"\bllm\b",
    r"임베디드",
    r"\bnpu\b",
    r"반도체",
    r"제어",
    r"미들웨어",
]

BUSINESS_CONTEXT_PATTERNS = [
    r"\bcrm\b",
    r"\bcx\b",
    r"\bpmo\b",
    r"growth",
    r"marketing",
    r"그로스",
    r"마케팅",
    r"퍼널",
    r"리텐션",
    r"캠페인",
    r"지표",
    r"대시보드",
    r"\bbi\b",
]

BUSINESS_DOMINANCE_PATTERNS = [
    r"\bcrm\b",
    r"\bcx\b",
    r"\bpmo\b",
    r"growth",
    r"marketing",
    r"그로스\s*마케팅",
    r"제품\s*분석",
    r"제품\s*성장\s*분석",
    r"광고\s*성과\s*분석",
    r"고객\s*관계\s*관리",
    r"퍼널",
    r"리텐션",
    r"캠페인",
]

DATA_ENGINEERING_TITLE_PATTERNS = [
    r"\bdata\s+analytics\s+engineer\b",
    r"\banalytics\s+engineer\b",
    r"\bdata\s+analyst\b",
    r"\bdata\s+engineer\b",
    r"\bdata\s+platform\b",
    r"\bdata\s+service\b",
    r"\betl\b",
    r"\bdw\b",
    r"\bbi\s*/?\s*dw\b",
    r"\bbusiness\s+intelligence\b",
    r"\bproduct\s+analyst\b",
    r"데이터\s*엔지니어",
    r"데이터\s*분석가",
    r"데이터\s*플랫폼",
    r"데이터\s*서비스",
    r"데이터\s*마트",
    r"데이터\s*웨어\s*하우스",
    r"데이터\s*웨어하우스",
    r"비즈니스\s*인텔리전스",
    r"제품\s*분석가",
]

DATA_ANALYTICS_TITLE_PATTERNS = [
    r"\bdata\s+analytics\s+engineer\b",
    r"\banalytics\s+engineer\b",
    r"\bdata\s+analyst\b",
    r"\bbusiness\s+intelligence\b",
    r"\bproduct\s+analyst\b",
    r"\bbi\s*/?\s*dw\b",
    r"데이터\s*분석가",
    r"제품\s*분석가",
]

AI_DOMINANCE_PATTERNS = [
    r"\bai\b",
    r"\bml\b",
    r"\bllm\b",
    r"\bvlm\b",
    r"\bros\b",
    r"\bisaac\b",
    r"robotics",
    r"simulation",
    r"autonomous",
    r"인공지능",
    r"머신러닝",
    r"딥러닝",
    r"mlops",
    r"엠엘옵스",
    r"검색증강생성",
    r"로봇",
    r"로보틱스",
    r"모델\s*(학습|서빙|최적화|평가|검증)",
    r"모델\s*서빙",
    r"모델\s*최적화",
    r"컴퓨터\s*비전",
    r"멀티모달",
    r"AI\s*반도체",
    r"\bnpu\b",
    r"\bgpu\b",
]

CLINICAL_SCIENCE_PATTERNS = [
    r"clinical\s+research\s+scientist",
    r"임상\s*연구",
    r"의료\s*영상",
]

STAGE2_FIELDNAMES = [
    "공고키",
    "변경해시",
    "검증상태",
    "검증우선순위",
    "이슈코드",
    "이슈요약",
    "stage1_분류직무",
    "stage2_분류직무",
    "stage1_직무초점",
    "stage2_직무초점",
    "stage1_핵심기술",
    "stage2_핵심기술",
    "stage1_구분요약",
    "stage2_구분요약",
    "회사명_표시",
    "공고제목_표시",
    "공고URL",
    "최종발견시각",
    "검증메모",
    "승인여부",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value) -> str:
    return " ".join(str(value or "").split()).strip()


def canonical(value) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", clean(value).lower())


NOISE_TERM_KEYS = {canonical(value) for value in NOISE_TERMS}


def pick(row: dict, *keys: str) -> str:
    for key in keys:
        value = clean(row.get(key, ""))
        if value:
            return value
    return ""


def split_terms(value: str) -> list[str]:
    terms = []
    seen = set()
    for part in re.split(r"[\n\r,;/|·]+", value or ""):
        term = clean(part)
        key = canonical(term)
        if term and key and key not in seen:
            seen.add(key)
            terms.append(term)
    return terms


def matches_any(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def issue(code: str, severity: str, message: str) -> dict:
    return {"code": code, "severity": severity, "message": message}


def public_csv_rows(spreadsheet_id: str, gid: str) -> tuple[list[dict], dict]:
    url = f"https://docs.google.com/spreadsheets/d/{spreadsheet_id}/gviz/tq?tqx=out:csv&gid={gid}"
    request = urllib.request.Request(url, headers={"User-Agent": "career-dashboard-prototype/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        text = response.read().decode("utf-8")
    rows = list(csv.DictReader(io.StringIO(text)))
    return rows, {
        "mode": "public_csv",
        "spreadsheetId": spreadsheet_id,
        "gid": gid,
        "rowCount": len(rows),
    }


def read_sheet(
    *,
    spreadsheet_id: str,
    gid: str,
    title: str,
    service_account_json: str,
    label: str,
) -> tuple[list[dict], dict]:
    service_path = Path(service_account_json).expanduser()
    if service_path.exists():
        rows, source = fetch_sheet_rows(
            spreadsheet_id=spreadsheet_id,
            service_account_json_path=service_path,
            gid=gid or None,
            sheet_title=title or None,
        )
        source = {
            "label": label,
            "mode": "google_sheets_api",
            "spreadsheetId": spreadsheet_id,
            "gid": source.get("sheetId", gid),
            "sheetTitle": source.get("sheetTitle", title),
            "spreadsheetTitle": source.get("spreadsheetTitle", ""),
            "rowCount": len(rows),
        }
        return rows, source
    rows, source = public_csv_rows(spreadsheet_id, gid)
    source["label"] = label
    source["sheetTitle"] = title
    return rows, source


def safe_read_sheet(**kwargs) -> tuple[list[dict], dict, str]:
    try:
        rows, source = read_sheet(**kwargs)
        return rows, source, ""
    except Exception as error:
        return [], {
            "label": kwargs.get("label", ""),
            "spreadsheetId": kwargs.get("spreadsheet_id", ""),
            "gid": kwargs.get("gid", ""),
            "sheetTitle": kwargs.get("title", ""),
            "rowCount": 0,
            "mode": "unreadable",
        }, str(error)


def row_id(row: dict) -> str:
    return pick(row, "공고키", "job_key", "postingId", "jobId", "id")


def row_hash(row: dict) -> str:
    return pick(row, "변경해시", "change_hash", "sourceHash", "hash")


def stage1_role(row: dict) -> str:
    return pick(row, "분류직무", "job_role", "직무명_표시", "stage1_분류직무")


def stage2_role(row: dict) -> str:
    return pick(row, "stage2_분류직무", "검증_분류직무", "2차_분류직무", "분류직무")


def stage1_focus(row: dict) -> str:
    return pick(row, "직무초점_표시", "stage1_직무초점")


def stage2_focus(row: dict) -> str:
    return pick(row, "stage2_직무초점", "검증_직무초점", "2차_직무초점", "직무초점_표시")


def stage1_keywords(row: dict) -> str:
    return pick(row, "핵심기술_표시", "stage1_핵심기술")


def stage2_keywords(row: dict) -> str:
    return pick(row, "stage2_핵심기술", "검증_핵심기술", "2차_핵심기술", "핵심기술_표시")


def stage1_summary(row: dict) -> str:
    return pick(row, "구분요약_표시", "stage1_구분요약")


def stage2_summary(row: dict) -> str:
    return pick(row, "stage2_구분요약", "검증_구분요약", "2차_구분요약", "구분요약_표시")


def effective_validation_row(stage1: dict, stage2: dict | None) -> dict:
    if not stage2:
        return stage1
    effective = dict(stage1)
    overrides = {
        "분류직무": stage2_role(stage2),
        "직무초점_표시": stage2_focus(stage2),
        "핵심기술_표시": stage2_keywords(stage2),
        "구분요약_표시": stage2_summary(stage2),
    }
    for key, value in overrides.items():
        if value:
            effective[key] = value
    return effective


def validate_stage1_row(row: dict) -> list[dict]:
    issues = []
    job_id = row_id(row)
    source_hash = row_hash(row)
    role = stage1_role(row)
    focus = stage1_focus(row)
    summary = stage1_summary(row)
    keywords = split_terms(stage1_keywords(row))
    title = pick(row, "공고제목_표시", "공고제목_raw", "job_title_raw")
    text = " ".join(
        [
            pick(row, "회사명_표시", "회사명", "company_name"),
            title,
            role,
            focus,
            summary,
            " ".join(keywords),
            pick(row, "상세본문_분석용"),
            pick(row, "주요업무_표시", "주요업무_분석용"),
            pick(row, "자격요건_표시", "자격요건_분석용"),
            pick(row, "우대사항_표시", "우대사항_분석용"),
        ]
    )
    # Do not include the already-assigned role in dominance evidence. Including
    # "인공지능 엔지니어" here makes AI-role mistakes self-validating.
    dominance_text = " ".join([title, focus, summary, " ".join(keywords[:6])])
    ai_evidence_text = " ".join(
        [
            title,
            focus,
            summary,
            " ".join(keywords),
            pick(row, "상세본문_분석용"),
            pick(row, "주요업무_표시", "주요업무_분석용"),
            pick(row, "자격요건_표시", "자격요건_분석용"),
            pick(row, "우대사항_표시", "우대사항_분석용"),
        ]
    )

    if not job_id:
        issues.append(issue("missing_job_id", "high", "공고키가 비어 있습니다."))
    if not source_hash:
        issues.append(issue("missing_change_hash", "high", "변경해시가 비어 있어 증분 stale 판정을 할 수 없습니다."))
    if role not in ALLOWED_ROLES:
        issues.append(issue("invalid_role", "high", f"분류직무가 허용 직군이 아닙니다: {role or '-'}"))
    if not focus:
        issues.append(issue("missing_focus", "medium", "직무초점_표시가 비어 있습니다."))
    if not summary:
        issues.append(issue("missing_group_summary", "medium", "구분요약_표시가 비어 있습니다."))
    if not keywords:
        issues.append(issue("missing_keywords", "medium", "핵심기술_표시가 비어 있습니다."))

    noisy = sorted({term for term in [focus, summary, *keywords] if canonical(term) in NOISE_TERM_KEYS})
    if noisy:
        issues.append(issue("noise_keyword", "high", f"키워드/초점에 비직무성 표현이 포함됩니다: {', '.join(noisy)}"))

    all_terms = [focus, *keywords]
    duplicates = [
        term for term, count in Counter(canonical(term) for term in all_terms if canonical(term)).items() if count > 1
    ]
    if duplicates:
        issues.append(issue("duplicate_signal", "medium", "직무초점과 핵심기술 간 중복 신호가 있습니다."))

    if role == "데이터 분석가" and matches_any(text, CLINICAL_SCIENCE_PATTERNS):
        issues.append(issue("clinical_scientist_as_analyst", "high", "임상/clinical research scientist 신호가 데이터 분석가로 분류되었습니다."))
    if role == "데이터 분석가" and matches_any(text, DEEPTECH_PATTERNS):
        severity = "medium" if matches_any(dominance_text, BUSINESS_DOMINANCE_PATTERNS) else "high"
        issues.append(issue("deeptech_as_analyst", severity, "로보틱스/비전/LLM 등 딥테크 신호가 데이터 분석가에 섞였습니다."))
    if role in {"인공지능 엔지니어", "인공지능 리서처"}:
        has_data_engineering_title = matches_any(title, DATA_ENGINEERING_TITLE_PATTERNS)
        has_business_dominance = matches_any(dominance_text, BUSINESS_DOMINANCE_PATTERNS)
        has_business_context = matches_any(text, BUSINESS_CONTEXT_PATTERNS)
        has_ai_title_anchor = matches_any(title, AI_DOMINANCE_PATTERNS)
        has_ai_dominance = matches_any(ai_evidence_text, AI_DOMINANCE_PATTERNS)

        if matches_any(title, DATA_ANALYTICS_TITLE_PATTERNS) and not has_ai_title_anchor:
            issues.append(issue("analytics_engineering_as_ai_role", "high", "Data Analytics/BI/Analyst 제목이 AI 직군으로 분류되었습니다."))
        elif has_data_engineering_title and not has_ai_title_anchor and not has_ai_dominance:
            issues.append(issue("data_engineering_as_ai_role", "high", "Data Engineer/Analytics Engineer/Data Platform 제목이 AI 직군으로 분류되었습니다."))
        elif has_data_engineering_title and has_ai_title_anchor:
            issues.append(issue("data_engineering_ai_title_context", "info", "AI/딥테크 앵커가 있는 데이터 엔지니어링 제목입니다."))
        elif has_data_engineering_title:
            issues.append(issue("data_engineering_ai_context", "info", "AI/ML/MLOps 신호가 지배적인 데이터 엔지니어링 제목입니다."))
        elif has_business_dominance and not has_ai_dominance:
            issues.append(issue("business_role_as_ai_role", "high", "CRM/CX/PMO/Growth/제품분석 신호가 제목·초점에서 지배적인데 AI 직군으로 분류되었습니다."))
        elif has_business_dominance:
            issues.append(issue("business_focus_in_ai_role", "medium", "AI 직군 안에서 비즈니스 분석형 초점이 지배적으로 붙어 직무초점 재검증이 필요합니다."))
        elif has_business_context:
            issues.append(issue("business_context_in_ai_role", "info", "AI 직군 상세본문에 비즈니스/지표/대시보드 문맥이 있으나 지배 신호는 아닙니다."))

    if summary and len(canonical(summary)) <= 4:
        issues.append(issue("summary_too_short", "low", "구분요약이 지나치게 짧습니다."))
    return issues


def compare_stage2(stage1: dict, stage2: dict | None) -> list[dict]:
    if not stage2:
        return []
    issues = []
    comparisons = [
        ("role_diff", "분류직무", stage1_role(stage1), stage2_role(stage2)),
        ("focus_diff", "직무초점", stage1_focus(stage1), stage2_focus(stage2)),
        ("keywords_diff", "핵심기술", stage1_keywords(stage1), stage2_keywords(stage2)),
        ("summary_diff", "구분요약", stage1_summary(stage1), stage2_summary(stage2)),
    ]
    for code, label, left, right in comparisons:
        if right and canonical(left) != canonical(right):
            issues.append(issue(code, "info", f"1차와 2차 {label} 값이 다릅니다."))
    return issues


def priority_for(issues: list[dict], state_code: str) -> str:
    severities = {item["severity"] for item in issues}
    if "high" in severities or state_code in {"stage2_missing", "stage2_stale", "stage2_unreadable"}:
        return "high"
    if "medium" in severities:
        return "medium"
    if issues:
        return "low"
    return "pass"


def status_for(
    *,
    stage2_access_error: str,
    stage2_row: dict | None,
    stage1_hash: str,
    stage2_hash: str,
    blocking_issues: list[dict],
) -> tuple[str, str]:
    if stage2_access_error:
        return "needs_review", "stage2_unreadable"
    if not stage2_row:
        return "needs_review", "stage2_missing"
    if stage1_hash and stage2_hash and stage1_hash != stage2_hash:
        return "needs_review", "stage2_stale"
    approved = clean(stage2_row.get("승인여부", "")).lower() in {"true", "y", "yes", "approved", "승인"}
    if blocking_issues:
        return "needs_review", "quality_issue"
    return ("approved", "stage2_approved") if approved else ("pending", "stage2_pending")


def build_candidate_rows(stage1_rows: list[dict], stage2_rows: list[dict], stage2_error: str) -> tuple[list[dict], dict]:
    stage2_by_id = {row_id(row): row for row in stage2_rows if row_id(row)}
    stage1_by_id = {row_id(row): row for row in stage1_rows if row_id(row)}
    candidates = []
    issue_counts = Counter()
    blocking_issue_counts = Counter()
    severity_counts = Counter()
    state_counts = Counter()

    for row in stage1_rows:
        job_id = row_id(row)
        stage2_row = stage2_by_id.get(job_id)
        quality_issues = validate_stage1_row(effective_validation_row(row, stage2_row))
        diff_issues = compare_stage2(row, stage2_row)
        issues = quality_issues + diff_issues
        blocking_issues = [item for item in issues if item.get("severity") in {"high", "medium"}]
        stage1_hash = row_hash(row)
        stage2_hash = row_hash(stage2_row or {})
        status, state_code = status_for(
            stage2_access_error=stage2_error,
            stage2_row=stage2_row,
            stage1_hash=stage1_hash,
            stage2_hash=stage2_hash,
            blocking_issues=blocking_issues,
        )
        issue_counts.update(item["code"] for item in issues)
        blocking_issue_counts.update(item["code"] for item in blocking_issues)
        severity_counts.update(item["severity"] for item in issues)
        state_counts[state_code] += 1
        priority = priority_for(issues, state_code)
        candidates.append(
            {
                "공고키": job_id,
                "변경해시": stage1_hash,
                "검증상태": status,
                "검증우선순위": priority,
                "이슈코드": " | ".join([state_code, *[item["code"] for item in issues]]),
                "이슈요약": " / ".join(item["message"] for item in issues)[:500],
                "stage1_분류직무": stage1_role(row),
                "stage2_분류직무": stage2_role(stage2_row or {}),
                "stage1_직무초점": stage1_focus(row),
                "stage2_직무초점": stage2_focus(stage2_row or {}),
                "stage1_핵심기술": stage1_keywords(row),
                "stage2_핵심기술": stage2_keywords(stage2_row or {}),
                "stage1_구분요약": stage1_summary(row),
                "stage2_구분요약": stage2_summary(stage2_row or {}),
                "회사명_표시": pick(row, "회사명_표시", "회사명", "company_name"),
                "공고제목_표시": pick(row, "공고제목_표시", "공고제목_raw", "job_title_raw"),
                "공고URL": pick(row, "공고URL", "job_url"),
                "최종발견시각": pick(row, "최종발견시각", "last_seen_at"),
                "검증메모": clean((stage2_row or {}).get("검증메모", "")),
                "승인여부": clean((stage2_row or {}).get("승인여부", "")),
            }
        )

    removed_ids = sorted(set(stage2_by_id) - set(stage1_by_id))
    return candidates, {
        "stateCounts": dict(state_counts),
        "issueCounts": dict(issue_counts),
        "blockingIssueCounts": dict(blocking_issue_counts),
        "severityCounts": dict(severity_counts),
        "removedFromStage1": len(removed_ids),
        "removedFromStage1Ids": removed_ids[:100],
    }


def write_csv(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=STAGE2_FIELDNAMES, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def quote_sheet_title(title: str) -> str:
    return "'" + title.replace("'", "''") + "'"


def candidate_sheet_values(rows: list[dict]) -> list[list[str]]:
    values = [STAGE2_FIELDNAMES]
    for row in rows:
        values.append([clean(row.get(field, "")) for field in STAGE2_FIELDNAMES])
    return values


def write_stage2_sheet(
    *,
    spreadsheet_id: str,
    service_account_json: str,
    sheet_title: str,
    rows: list[dict],
) -> dict:
    quoted_title = quote_sheet_title(sheet_title)
    clear_result = clear_sheet_values(
        spreadsheet_id,
        service_account_json,
        f"{quoted_title}!A:Z",
    )
    update_result = update_sheet_values(
        spreadsheet_id,
        service_account_json,
        f"{quoted_title}!A1",
        candidate_sheet_values(rows),
    )
    return {
        "clear": clear_result,
        "update": update_result,
        "rowsWritten": len(rows),
        "columnsWritten": len(STAGE2_FIELDNAMES),
        "sheetTitle": sheet_title,
    }


def render_md(report: dict) -> str:
    metrics = report["metrics"]
    lines = [
        "# Stage2 Validation Latest",
        "",
        f"- generatedAt: `{report['generatedAt']}`",
        f"- stage1Rows: `{metrics['stage1Rows']}`",
        f"- stage2Rows: `{metrics['stage2Rows']}`",
        f"- candidateRows: `{metrics['candidateRows']}`",
        f"- stage2Access: `{'blocked' if report['stage2AccessError'] else 'ok'}`",
    ]
    if report["stage2AccessError"]:
        lines.append(f"- stage2AccessError: `{report['stage2AccessError']}`")
    lines.extend(
        [
            "",
            "## State Counts",
            "",
        ]
    )
    for key, value in sorted(report["stateCounts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Issue Counts", ""])
    for key, value in sorted(report["issueCounts"].items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Blocking Issue Counts", ""])
    for key, value in sorted(report.get("blockingIssueCounts", {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Severity Counts", ""])
    for key, value in sorted(report.get("severityCounts", {}).items()):
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Outputs", ""])
    for key, value in report["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    stage2_write = report.get("stage2Write")
    if stage2_write:
        lines.extend(["", "## Stage2 Write", ""])
        lines.append(f"- status: `{stage2_write.get('status')}`")
        if stage2_write.get("error"):
            lines.append(f"- error: `{stage2_write.get('error')}`")
        if stage2_write.get("rowsWritten") is not None:
            lines.append(f"- rowsWritten: `{stage2_write.get('rowsWritten')}`")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare stage1 increment sheet against stage2 validation sheet.")
    parser.add_argument("--stage1-spreadsheet-id", default=DEFAULT_STAGE1_SPREADSHEET_ID)
    parser.add_argument("--stage1-gid", default=DEFAULT_STAGE1_GID)
    parser.add_argument("--stage1-title", default=DEFAULT_STAGE1_TITLE)
    parser.add_argument("--stage2-spreadsheet-id", default=DEFAULT_STAGE2_SPREADSHEET_ID)
    parser.add_argument("--stage2-gid", default=DEFAULT_STAGE2_GID)
    parser.add_argument("--stage2-title", default=DEFAULT_STAGE2_TITLE)
    parser.add_argument("--service-account-json", default=DEFAULT_SERVICE_ACCOUNT_JSON)
    parser.add_argument("--output-json", type=Path, default=OUTPUT_JSON)
    parser.add_argument("--output-csv", type=Path, default=OUTPUT_CSV)
    parser.add_argument("--output-md", type=Path, default=OUTPUT_MD)
    parser.add_argument(
        "--write-stage2",
        action="store_true",
        help="Write the generated candidate table into the configured stage2 sheet.",
    )
    parser.add_argument(
        "--allow-overwrite-stage2",
        action="store_true",
        help="Allow writing even when the stage2 sheet already has rows.",
    )
    parser.add_argument(
        "--allow-missing-stage2",
        action="store_true",
        help="Generate a local candidate CSV even if the stage2 sheet cannot be read.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    stage1_rows, stage1_source, stage1_error = safe_read_sheet(
        spreadsheet_id=args.stage1_spreadsheet_id,
        gid=args.stage1_gid,
        title=args.stage1_title,
        service_account_json=args.service_account_json,
        label="stage1",
    )
    if stage1_error:
        raise SystemExit(f"Stage1 sheet is unreadable: {stage1_error}")

    stage2_rows, stage2_source, stage2_error = safe_read_sheet(
        spreadsheet_id=args.stage2_spreadsheet_id,
        gid=args.stage2_gid,
        title=args.stage2_title,
        service_account_json=args.service_account_json,
        label="stage2",
    )
    if stage2_error and not args.allow_missing_stage2:
        raise SystemExit(
            "Stage2 sheet is unreadable. Share it with the configured service account "
            f"or rerun with --allow-missing-stage2 for a local candidate export. Error: {stage2_error}"
        )

    candidates, comparison = build_candidate_rows(stage1_rows, stage2_rows, stage2_error)
    stage2_write = None
    if args.write_stage2:
        if stage2_error:
            stage2_write = {"status": "blocked", "error": f"stage2 sheet unreadable: {stage2_error}"}
        elif stage2_rows and not args.allow_overwrite_stage2:
            stage2_write = {
                "status": "blocked",
                "error": "stage2 sheet already has rows; rerun with --allow-overwrite-stage2 after confirming.",
                "existingRows": len(stage2_rows),
            }
        else:
            try:
                write_result = write_stage2_sheet(
                    spreadsheet_id=args.stage2_spreadsheet_id,
                    service_account_json=args.service_account_json,
                    sheet_title=stage2_source.get("sheetTitle") or args.stage2_title,
                    rows=candidates,
                )
                stage2_write = {"status": "written", **write_result}
            except Exception as error:
                stage2_write = {"status": "failed", "error": str(error)}

    report = {
        "generatedAt": now_iso(),
        "stage1Source": stage1_source,
        "stage2Source": stage2_source,
        "stage2AccessError": stage2_error,
        "metrics": {
            "stage1Rows": len(stage1_rows),
            "stage2Rows": len(stage2_rows),
            "candidateRows": len(candidates),
            "removedFromStage1": comparison["removedFromStage1"],
        },
        "stateCounts": comparison["stateCounts"],
        "issueCounts": comparison["issueCounts"],
        "blockingIssueCounts": comparison["blockingIssueCounts"],
        "severityCounts": comparison["severityCounts"],
        "removedFromStage1Ids": comparison["removedFromStage1Ids"],
        "stage2Write": stage2_write,
        "outputs": {
            "json": str(args.output_json),
            "csv": str(args.output_csv),
            "md": str(args.output_md),
        },
    }

    write_json(args.output_json, report)
    write_csv(args.output_csv, candidates)
    args.output_md.parent.mkdir(parents=True, exist_ok=True)
    args.output_md.write_text(render_md(report), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
