from __future__ import annotations

import json
from enum import Enum

from openai import OpenAI
from pydantic import BaseModel, field_validator

from src.config import Settings
from src.gmail_client import EmailMessage, emails_to_prompt_payload

SYSTEM_PROMPT = """You analyze unread email metadata (subject, sender, date, snippet only).
Identify important emails for a morning digest.

Categories (use exactly these values):
- meeting_scheduled: calendar invites, meeting confirmations, schedule changes
- invoice_finance: invoices, receipts, payments, billing
- action_required: needs reply, deadline, approval, security alert
- fyi: useful but low urgency news/updates
- skip: newsletters, promotions, automated noise

Return ONLY valid JSON matching this schema:
{
  "summary": "one sentence overview of the inbox",
  "items": [
    {
      "message_id": "gmail message id from input",
      "category": "meeting_scheduled|invoice_finance|action_required|fyi",
      "title": "short title",
      "summary": "1-2 sentence summary",
      "sender": "sender",
      "urgency": "high|medium|low",
      "gmail_link": "url from input"
    }
  ]
}

Include only emails worth attention (exclude skip). If nothing important, return empty items array with an appropriate summary."""


class EmailCategory(str, Enum):
    MEETING_SCHEDULED = "meeting_scheduled"
    INVOICE_FINANCE = "invoice_finance"
    ACTION_REQUIRED = "action_required"
    FYI = "fyi"


class DigestItem(BaseModel):
    message_id: str
    category: EmailCategory
    title: str
    summary: str
    sender: str
    urgency: str = "medium"
    gmail_link: str

    @field_validator("urgency", mode="before")
    @classmethod
    def normalize_urgency(cls, value: object) -> str:
        normalized = str(value).lower().strip()
        if normalized in ("high", "medium", "low"):
            return normalized
        return "medium"


class DigestResult(BaseModel):
    summary: str
    items: list[DigestItem]


def _client(settings: Settings) -> OpenAI:
    return OpenAI(api_key=settings.kimi_api_key, base_url=settings.kimi_base_url)


def analyze_emails(settings: Settings, emails: list[EmailMessage]) -> DigestResult:
    if not emails:
        return DigestResult(
            summary="No unread emails in the lookback window.",
            items=[],
        )

    client = _client(settings)
    user_content = (
        "Analyze these unread emails and produce the JSON digest:\n\n"
        + emails_to_prompt_payload(emails)
    )

    response = client.chat.completions.create(
        model=settings.kimi_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Kimi returned invalid JSON: {raw[:200]}") from exc

    return DigestResult.model_validate(data)
