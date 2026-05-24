from __future__ import annotations

import requests

from src.config import Settings
from src.kimi_client import DigestItem, DigestResult

CATEGORY_LABELS = {
    "meeting_scheduled": "Meeting",
    "invoice_finance": "Invoice / Finance",
    "action_required": "Action required",
    "fyi": "FYI",
}

URGENCY_EMOJI = {"high": ":red_circle:", "medium": ":large_yellow_circle:", "low": ":white_circle:"}


def _format_item(item: DigestItem) -> str:
    label = CATEGORY_LABELS.get(item.category.value, item.category.value)
    urgency = URGENCY_EMOJI.get(item.urgency, "")
    return (
        f"{urgency} *<{item.gmail_link}|{item.title}>*\n"
        f"_{label}_ · {item.sender} · {item.urgency}\n"
        f"{item.summary}"
    )


def build_slack_blocks(digest: DigestResult, email_count: int) -> list[dict]:
    blocks: list[dict] = [
        {"type": "header", "text": {"type": "plain_text", "text": "Morning Gmail digest", "emoji": True}},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Overview* ({email_count} unread scanned)\n{digest.summary}",
            },
        },
        {"type": "divider"},
    ]

    if not digest.items:
        blocks.append(
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "_No important emails flagged in this batch._",
                },
            }
        )
        return blocks

    by_category: dict[str, list[DigestItem]] = {}
    for item in digest.items:
        key = item.category.value
        by_category.setdefault(key, []).append(item)

    for cat_key, items in by_category.items():
        label = CATEGORY_LABELS.get(cat_key, cat_key)
        lines = "\n\n".join(_format_item(i) for i in items)
        blocks.append(
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{label}*\n{lines}"},
            }
        )
        blocks.append({"type": "divider"})

    if blocks and blocks[-1].get("type") == "divider":
        blocks.pop()

    return blocks


def _post_webhook(webhook_url: str, blocks: list[dict], fallback_text: str) -> None:
    payload = {"text": fallback_text, "blocks": blocks}
    resp = requests.post(webhook_url, json=payload, timeout=30)
    resp.raise_for_status()


def _post_bot(token: str, channel: str, blocks: list[dict], fallback_text: str) -> None:
    resp = requests.post(
        "https://slack.com/api/chat.postMessage",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "channel": channel,
            "text": fallback_text,
            "blocks": blocks,
        },
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if not data.get("ok"):
        raise RuntimeError(f"Slack API error: {data.get('error', data)}")


def send_digest(settings: Settings, digest: DigestResult, email_count: int) -> None:
    settings.validate_slack()
    blocks = build_slack_blocks(digest, email_count)
    fallback = f"Morning Gmail digest: {digest.summary}"

    if len(blocks) > 45:
        blocks = blocks[:45]

    if settings.slack_webhook_url:
        _post_webhook(settings.slack_webhook_url, blocks, fallback)
    else:
        _post_bot(
            settings.slack_bot_token,
            settings.slack_channel_id,
            blocks,
            fallback,
        )
