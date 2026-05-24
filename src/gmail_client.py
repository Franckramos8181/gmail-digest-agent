from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from src.config import Settings

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


@dataclass
class EmailMessage:
    id: str
    thread_id: str
    subject: str
    sender: str
    date: str
    snippet: str
    gmail_link: str


def _build_credentials(settings: Settings) -> Credentials:
    if not settings.gmail_refresh_token:
        raise ValueError(
            "GMAIL_REFRESH_TOKEN is missing. Run: python -m src.auth_gmail"
        )
    return Credentials(
        token=None,
        refresh_token=settings.gmail_refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=SCOPES,
    )


def _header(headers: list[dict], name: str) -> str:
    for h in headers:
        if h.get("name", "").lower() == name.lower():
            return h.get("value", "")
    return ""


def _format_date(raw: str) -> str:
    if not raw:
        return ""
    try:
        dt = parsedate_to_datetime(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    except (TypeError, ValueError):
        return raw


def fetch_unread_messages(settings: Settings) -> list[EmailMessage]:
    creds = _build_credentials(settings)
    service = build("gmail", "v1", credentials=creds, cache_discovery=False)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=settings.lookback_hours)
    after_epoch = int(cutoff.timestamp())
    query = f"is:unread after:{after_epoch}"

    list_resp = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=settings.max_emails)
        .execute()
    )
    message_refs = list_resp.get("messages", [])
    if not message_refs:
        return []

    results: list[EmailMessage] = []
    for ref in message_refs:
        msg = (
            service.users()
            .messages()
            .get(
                userId="me",
                id=ref["id"],
                format="metadata",
                metadataHeaders=["Subject", "From", "Date"],
            )
            .execute()
        )
        headers = msg.get("payload", {}).get("headers", [])
        thread_id = msg.get("threadId", ref["id"])
        subject = _header(headers, "Subject") or "(no subject)"
        sender = _header(headers, "From") or "(unknown)"
        date_raw = _header(headers, "Date")
        snippet = (msg.get("snippet") or "").strip()

        results.append(
            EmailMessage(
                id=ref["id"],
                thread_id=thread_id,
                subject=subject,
                sender=sender,
                date=_format_date(date_raw),
                snippet=snippet[:500],
                gmail_link=f"https://mail.google.com/mail/u/0/#inbox/{thread_id}",
            )
        )

    return results


def emails_to_prompt_payload(emails: list[EmailMessage]) -> str:
    blocks: list[str] = []
    for i, e in enumerate(emails, start=1):
        blocks.append(
            f"--- Email {i} ---\n"
            f"id: {e.id}\n"
            f"thread_id: {e.thread_id}\n"
            f"from: {e.sender}\n"
            f"date: {e.date}\n"
            f"subject: {e.subject}\n"
            f"snippet: {e.snippet}\n"
            f"link: {e.gmail_link}\n"
        )
    return "\n".join(blocks)
