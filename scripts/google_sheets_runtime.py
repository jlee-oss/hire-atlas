#!/usr/bin/env python3

import base64
import json
import shutil
import subprocess
import tempfile
import time
import urllib.parse
import urllib.request
from pathlib import Path


GOOGLE_SHEETS_SCOPE = "https://www.googleapis.com/auth/spreadsheets.readonly"
GOOGLE_SHEETS_READWRITE_SCOPE = "https://www.googleapis.com/auth/spreadsheets"


def read_service_account(path: str | Path) -> dict:
    """파일 경로 또는 JSON 문자열 내용을 모두 지원합니다 (Vercel 환경변수 대응)."""
    s = str(path).strip()
    if s.startswith("{"):
        return json.loads(s)
    return json.loads(Path(s).expanduser().read_text(encoding="utf-8"))


def b64url(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def sign_rs256(message: bytes, private_key: str) -> bytes:
    openssl_path = shutil.which("openssl")
    if not openssl_path:
        raise RuntimeError("openssl is required to sign Google service account JWTs")

    key_path = None
    data_path = None
    try:
        with tempfile.NamedTemporaryFile("w", delete=False) as key_file:
            key_file.write(private_key)
            key_path = key_file.name
        with tempfile.NamedTemporaryFile("wb", delete=False) as data_file:
            data_file.write(message)
            data_path = data_file.name
        return subprocess.check_output(
            [
                openssl_path,
                "dgst",
                "-sha256",
                "-sign",
                key_path,
                "-binary",
                data_path,
            ]
        )
    finally:
        for target in [key_path, data_path]:
            if target:
                Path(target).unlink(missing_ok=True)


def create_access_token(service_account: dict, scope: str = GOOGLE_SHEETS_SCOPE) -> str:
    header = {"alg": "RS256", "typ": "JWT"}
    now = int(time.time())
    claim = {
        "iss": service_account["client_email"],
        "scope": scope,
        "aud": service_account["token_uri"],
        "iat": now,
        "exp": now + 3600,
    }

    unsigned = ".".join(
        [
            b64url(json.dumps(header, separators=(",", ":")).encode("utf-8")),
            b64url(json.dumps(claim, separators=(",", ":")).encode("utf-8")),
        ]
    )
    signature = sign_rs256(unsigned.encode("utf-8"), service_account["private_key"])
    assertion = f"{unsigned}.{b64url(signature)}"

    data = urllib.parse.urlencode(
        {
            "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
            "assertion": assertion,
        }
    ).encode("utf-8")
    request = urllib.request.Request(service_account["token_uri"], data=data, method="POST")

    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["access_token"]


def google_api_get(url: str, access_token: str) -> dict:
    request = urllib.request.Request(
        url,
        headers={"Authorization": f"Bearer {access_token}"},
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def google_api_request(url: str, access_token: str, *, method: str, payload: dict | None = None) -> dict:
    data = None
    headers = {"Authorization": f"Bearer {access_token}"}
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json; charset=utf-8"
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8")
    return json.loads(body) if body else {}


def fetch_spreadsheet_metadata(spreadsheet_id: str, service_account_json_path: str | Path) -> dict:
    service_account = read_service_account(service_account_json_path)
    token = create_access_token(service_account)
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
        "?fields=properties.title,sheets.properties"
    )
    return google_api_get(url, token)


def resolve_sheet(metadata: dict, gid: str | int | None = None, title: str | None = None) -> dict:
    sheets = [sheet["properties"] for sheet in metadata.get("sheets", [])]
    if title:
        for props in sheets:
            if props.get("title") == title:
                return props
        raise ValueError(f"Sheet title not found: {title}")

    if gid is not None and gid != "":
        gid_value = int(gid)
        for props in sheets:
            if int(props.get("sheetId", -1)) == gid_value:
                return props
        raise ValueError(f"Sheet gid not found: {gid}")

    if not sheets:
        raise ValueError("Spreadsheet has no sheets")
    return sheets[0]


def fetch_sheet_rows(
    spreadsheet_id: str,
    service_account_json_path: str | Path,
    gid: str | int | None = None,
    sheet_title: str | None = None,
) -> tuple[list[dict[str, str]], dict]:
    service_account = read_service_account(service_account_json_path)
    token = create_access_token(service_account)
    metadata = google_api_get(
        (
            f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}"
            "?fields=properties.title,sheets.properties"
        ),
        token,
    )
    sheet = resolve_sheet(metadata, gid=gid, title=sheet_title)
    encoded_range = urllib.parse.quote(sheet["title"], safe="")
    values_payload = google_api_get(
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}",
        token,
    )
    values = values_payload.get("values", [])
    if not values:
        return [], {
            "spreadsheetTitle": metadata.get("properties", {}).get("title", ""),
            "sheetTitle": sheet["title"],
            "sheetId": str(sheet["sheetId"]),
            "rowCount": 0,
        }

    headers = [str(cell).strip() for cell in values[0]]
    rows = []
    for raw_row in values[1:]:
        padded = list(raw_row) + [""] * max(0, len(headers) - len(raw_row))
        row = {
            header: str(padded[index]).strip()
            for index, header in enumerate(headers)
            if header.strip()
        }
        if any(value for value in row.values()):
            rows.append(row)

    source = {
        "spreadsheetTitle": metadata.get("properties", {}).get("title", ""),
        "sheetTitle": sheet["title"],
        "sheetId": str(sheet["sheetId"]),
        "rowCount": len(rows),
    }
    return rows, source


def clear_sheet_values(
    spreadsheet_id: str,
    service_account_json_path: str | Path,
    range_name: str,
) -> dict:
    service_account = read_service_account(service_account_json_path)
    token = create_access_token(service_account, scope=GOOGLE_SHEETS_READWRITE_SCOPE)
    encoded_range = urllib.parse.quote(range_name, safe="")
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}:clear"
    return google_api_request(url, token, method="POST", payload={})


def update_sheet_values(
    spreadsheet_id: str,
    service_account_json_path: str | Path,
    range_name: str,
    values: list[list[str]],
) -> dict:
    service_account = read_service_account(service_account_json_path)
    token = create_access_token(service_account, scope=GOOGLE_SHEETS_READWRITE_SCOPE)
    encoded_range = urllib.parse.quote(range_name, safe="")
    url = (
        f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}/values/{encoded_range}"
        "?valueInputOption=RAW"
    )
    payload = {
        "range": range_name,
        "majorDimension": "ROWS",
        "values": values,
    }
    return google_api_request(url, token, method="PUT", payload=payload)
