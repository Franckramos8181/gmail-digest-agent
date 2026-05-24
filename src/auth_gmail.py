"""One-time OAuth flow to obtain GMAIL_REFRESH_TOKEN."""

import os

from dotenv import load_dotenv
from google_auth_oauthlib.flow import InstalledAppFlow

from src.config import Settings

SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def main() -> None:
    load_dotenv()
    settings = Settings()

    if not settings.google_client_id or not settings.google_client_secret:
        raise SystemExit(
            "Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET in .env first."
        )

    client_config = {
        "installed": {
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": ["http://localhost"],
        }
    }

    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")

    if not creds.refresh_token:
        raise SystemExit(
            "No refresh token returned. Revoke app access at "
            "https://myaccount.google.com/permissions and re-run with "
            "prompt=consent (delete any cached token first)."
        )

    print("\nAdd this to your .env file:\n")
    print(f"GMAIL_REFRESH_TOKEN={creds.refresh_token}\n")


if __name__ == "__main__":
    main()
