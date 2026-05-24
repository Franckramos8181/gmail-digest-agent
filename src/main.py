"""Daily Gmail digest: unread scan -> Kimi analysis -> Slack notification."""

from __future__ import annotations

import sys
from datetime import datetime
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

from src.checkpoint import CheckpointStore
from src.config import Settings, load_settings
from src.gmail_client import fetch_unread_messages
from src.kimi_client import analyze_emails
from src.slack_notify import send_digest


def _should_run_today(settings: Settings) -> bool:
    if settings.include_weekends:
        return True
    tz = ZoneInfo(settings.timezone)
    weekday = datetime.now(tz).weekday()
    return weekday < 5


def run() -> int:
    load_dotenv()
    settings = load_settings()

    if not _should_run_today(settings):
        print("Skipped: weekends disabled in INCLUDE_WEEKENDS=false")
        return 0

    settings.validate_slack()

    checkpoint = CheckpointStore(settings.checkpoint_path)
    all_emails = fetch_unread_messages(settings)
    emails = [e for e in all_emails if not checkpoint.is_processed(e.id)]

    print(f"Fetched {len(all_emails)} unread; {len(emails)} new since last run.")

    digest = analyze_emails(settings, emails)
    send_digest(settings, digest, email_count=len(all_emails))

    if emails:
        checkpoint.mark_processed([e.id for e in emails])
        checkpoint.save()

    print("Digest sent to Slack.")
    return 0


def main() -> None:
    try:
        raise SystemExit(run())
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc


if __name__ == "__main__":
    main()
