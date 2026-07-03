"""Gmail receipt ingestion for the personal finance tracker."""

from __future__ import annotations

import base64
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from db import get_connection, init_db, insert_transaction


SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]
RM_PATTERN = re.compile(r"(?:RM|MYR)\s?([\d,]+(?:\.\d{1,2})?)", re.IGNORECASE)
DATE_PATTERN = re.compile(r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})")
KNOWN_SENDERS = (
    "no-reply@grab.com",
    "no-reply@shopee.com",
    "no-reply@touchngo.com.my",
)


def authenticate_gmail(credentials_path: str | Path = "credentials.json", token_path: str | Path = "token.json"):
    """Authenticate to Gmail using an installed-app OAuth flow.

    The first run opens a browser window so you can approve access manually.
    Subsequent runs reuse the cached token when possible.
    """
    credentials_path = Path(credentials_path)
    token_path = Path(token_path)

    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(str(credentials_path), SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.write_text(creds.to_json(), encoding="utf-8")

    return build("gmail", "v1", credentials=creds)


def fetch_new_emails(service, hours_back: int = 6) -> list[dict[str, Any]]:
    """Fetch recent Gmail messages from known senders."""
    query = _build_query(hours_back)
    response = service.users().messages().list(userId="me", q=query, maxResults=50).execute()
    messages = response.get("messages", [])
    results: list[dict[str, Any]] = []

    for message in messages:
        msg = service.users().messages().get(userId="me", id=message["id"], format="full").execute()
        payload = msg.get("payload", {})
        headers = _headers_to_dict(payload.get("headers", []))
        sender = headers.get("From", "")
        subject = headers.get("Subject", "")
        body = _extract_body(payload)
        results.append(
            {
                "id": message["id"],
                "sender": sender,
                "subject": subject,
                "body": body,
                "snippet": msg.get("snippet", ""),
                "internal_date": msg.get("internalDate"),
            }
        )

    return results


def parse_grab_email(body: str) -> dict | None:
    text = _clean_html_body(body)
    amount = _extract_amount(text)
    if amount is None:
        return None
    return {
        "description": "Grab transaction",
        "amount": amount,
        "date": _extract_date(text),
        "type": "expense" if amount < 0 else "income",
        "category": "Transport",
        "source": "gmail",
        "raw_text": text,
    }


def parse_shopee_email(body: str) -> dict | None:
    text = _clean_html_body(body)
    amount = _extract_amount(text)
    if amount is None:
        return None
    return {
        "description": "Shopee transaction",
        "amount": amount,
        "date": _extract_date(text),
        "type": "expense" if amount < 0 else "income",
        "category": "Shopping",
        "source": "gmail",
        "raw_text": text,
    }


def parse_tng_email(body: str) -> dict | None:
    text = _clean_html_body(body)
    amount = _extract_amount(text)
    if amount is None:
        return None
    return {
        "description": "Touch 'n Go transaction",
        "amount": amount,
        "date": _extract_date(text),
        "type": "expense" if amount < 0 else "income",
        "category": "E-wallet top-up",
        "source": "gmail",
        "raw_text": text,
    }


def parse_generic_email(subject: str, body: str) -> dict | None:
    text = f"{subject} {_clean_html_body(body)}"
    amount = _extract_amount(text)
    if amount is None:
        return None
    return {
        "description": subject[:120] or "Generic email transaction",
        "amount": amount,
        "date": _extract_date(text),
        "type": "expense" if amount < 0 else "income",
        "category": "Uncategorised",
        "source": "gmail",
        "raw_text": text,
    }


def run_gmail_fetch(db_path: str | Path, credentials_path: str | Path = "credentials.json", token_path: str | Path = "token.json") -> dict[str, int]:
    """Fetch Gmail receipts and insert parsed transactions into SQLite."""
    init_db(db_path)
    service = authenticate_gmail(credentials_path=credentials_path, token_path=token_path)
    messages = fetch_new_emails(service)

    fetched = len(messages)
    inserted = 0
    skipped = 0

    with get_connection(db_path) as conn:
        for message in messages:
            parsed = _parse_message(message["sender"], message["subject"], message["body"])
            if not parsed:
                skipped += 1
                continue

            inserted_now = insert_transaction(
                conn,
                parsed["date"],
                parsed["description"],
                parsed["amount"],
                parsed["type"],
                parsed["category"],
                parsed["source"],
                parsed["raw_text"],
            )
            if inserted_now:
                inserted += 1
            else:
                skipped += 1

    return {"fetched": fetched, "inserted": inserted, "skipped": skipped}


def _parse_message(sender: str, subject: str, body: str) -> dict | None:
    sender_lower = sender.lower()
    subject_lower = subject.lower()
    if "grab" in sender_lower or "grab" in subject_lower:
        return parse_grab_email(body)
    if "shopee" in sender_lower or "shopee" in subject_lower:
        return parse_shopee_email(body)
    if "touch" in sender_lower or "tng" in sender_lower or "touch" in subject_lower:
        return parse_tng_email(body)
    return parse_generic_email(subject, body)


def _build_query(hours_back: int) -> str:
    after = datetime.now(timezone.utc) - timedelta(hours=hours_back)
    unix_ts = int(after.timestamp())
    sender_clause = " OR ".join(f"from:{sender}" for sender in KNOWN_SENDERS)
    return f"({sender_clause}) after:{unix_ts}"


def _clean_html_body(body: str) -> str:
    soup = BeautifulSoup(body, "html.parser")
    return soup.get_text(" ", strip=True)


def _extract_body(payload: dict[str, Any]) -> str:
    mime_type = payload.get("mimeType", "")
    body = payload.get("body", {})
    data = body.get("data")
    if data:
        return _decode_base64url(data)

    parts = payload.get("parts", [])
    for part in parts:
        part_body = part.get("body", {})
        data = part_body.get("data")
        if data:
            return _decode_base64url(data)
    return ""


def _decode_base64url(data: str) -> str:
    decoded = base64.urlsafe_b64decode(data.encode("utf-8") + b"=" * (-len(data) % 4))
    return decoded.decode("utf-8", errors="replace")


def _headers_to_dict(headers: list[dict[str, Any]]) -> dict[str, str]:
    return {header.get("name", ""): header.get("value", "") for header in headers}


def _extract_amount(text: str) -> float | None:
    match = RM_PATTERN.search(text)
    if not match:
        return None
    value = float(match.group(1).replace(",", ""))
    lowered = text.lower()
    if any(keyword in lowered for keyword in ("salary", "gaji", "credited", "transfer in", "payment received", "bank in")):
        return abs(value)
    return -abs(value)


def _extract_date(text: str) -> str:
    match = DATE_PATTERN.search(text)
    if match:
        raw = match.group(1)
        for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%m/%d/%Y", "%m-%d-%Y"):
            try:
                return datetime.strptime(raw, fmt).date().isoformat()
            except ValueError:
                continue
    return datetime.now().date().isoformat()

