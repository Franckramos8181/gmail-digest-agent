# Gmail Morning Digest Agent

Scans unread Gmail (headers + snippets), classifies important messages with **Kimi (Moonshot)**, and posts a structured digest to **Slack**. Designed to run once each morning via Windows Task Scheduler (or cron).

## Stack

- **Python 3.11+**
- **Gmail API** (OAuth refresh token in `.env`)
- **Kimi** via OpenAI-compatible API (`api.moonshot.cn`)
- **Slack** incoming webhook (default) or bot token + channel ID

## Prerequisites

1. [Python 3.11+](https://www.python.org/downloads/)
2. Google Cloud project with **Gmail API** enabled
3. OAuth 2.0 **Desktop** client credentials
4. [Moonshot / Kimi API key](https://platform.moonshot.cn/)
5. Slack [Incoming Webhook](https://api.slack.com/messaging/webhooks) (or bot with `chat:write`)

## Setup

```powershell
cd d:\Projects\Franck\gmail-digest-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with your credentials.

### 1. Google Cloud / Gmail

1. Go to [Google Cloud Console](https://console.cloud.google.com/).
2. Create or select a project → **APIs & Services** → **Library** → enable **Gmail API**.
3. **Credentials** → **Create credentials** → **OAuth client ID** → Application type **Desktop app**.
4. Copy **Client ID** and **Client secret** into `.env` as `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
5. If the app is in **Testing**, add your Gmail address under **OAuth consent screen** → **Test users**.

Obtain a refresh token (one-time, opens browser):

```powershell
python -m src.auth_gmail
```

Paste the printed `GMAIL_REFRESH_TOKEN` into `.env`.

### 2. Kimi (Moonshot)

1. Create an API key at [Moonshot platform](https://platform.moonshot.cn/).
2. Set `KIMI_API_KEY` in `.env`.
3. Default model: `moonshot-v1-8k`. For larger batches use `moonshot-v1-32k` or `moonshot-v1-128k`.

### 3. Slack

**Option A – Webhook (recommended)**

1. Create an app at [api.slack.com/apps](https://api.slack.com/apps) → **Incoming Webhooks** → On.
2. Add webhook to your channel; copy URL to `SLACK_WEBHOOK_URL`.

**Option B – Bot**

1. Install app to workspace with `chat:write`.
2. Set `SLACK_BOT_TOKEN` and `SLACK_CHANNEL_ID` (channel or DM ID).

## Run manually

```powershell
cd d:\Projects\Franck\gmail-digest-agent
.\.venv\Scripts\Activate.ps1
python -m src.main
```

## Configuration

| Variable | Description |
|----------|-------------|
| `MAX_EMAILS` | Max unread messages per run (default 50) |
| `LOOKBACK_HOURS` | Only unread after this window (default 48) |
| `TIMEZONE` | Used for weekend skip logic |
| `INCLUDE_WEEKENDS` | `true` / `false` – skip Sat/Sun when `false` |
| `CHECKPOINT_PATH` | Tracks processed message IDs to avoid duplicate digests |

Privacy: only **subject, from, date, snippet** are sent to Kimi (no full body in v1).

## Windows Task Scheduler (daily morning)

1. Open **Task Scheduler** → **Create Task**.
2. **General**: name `Gmail Morning Digest`, run whether user is logged on or not (store password if needed).
3. **Triggers** → **New** → Daily, e.g. **8:00 AM**, your timezone.
4. **Actions** → **New**:
   - **Program/script**: `d:\Projects\Franck\gmail-digest-agent\.venv\Scripts\python.exe`
   - **Add arguments**: `-m src.main`
   - **Start in**: `d:\Projects\Franck\gmail-digest-agent`
5. **Conditions**: disable “Start only if on AC power” if on a laptop.
6. Ensure `.env` lives in **Start in** folder (the job loads it from there).

Or use the included script as **Program/script** (set **Start in** to project root):

```text
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "d:\Projects\Franck\gmail-digest-agent\scripts\run_digest.ps1"
```

Alternative one-liner action using PowerShell:

```text
Program: powershell.exe
Arguments: -NoProfile -ExecutionPolicy Bypass -Command "Set-Location 'd:\Projects\Franck\gmail-digest-agent'; .\.venv\Scripts\python.exe -m src.main"
```

### Test the scheduled command

```powershell
Set-Location 'd:\Projects\Franck\gmail-digest-agent'
.\.venv\Scripts\python.exe -m src.main
```

Check **Task Scheduler** → task → **History** if a run fails (often missing `.env` or wrong **Start in** path).

## Digest categories

- **Meeting** – invites, schedule changes
- **Invoice / Finance** – bills, payments
- **Action required** – replies, deadlines, security
- **FYI** – useful low-urgency updates

## Troubleshooting

| Issue | Fix |
|-------|-----|
| `GMAIL_REFRESH_TOKEN is missing` | Run `python -m src.auth_gmail` |
| `invalid_grant` on Gmail | Re-run auth; token revoked |
| Kimi JSON error | Lower `MAX_EMAILS` or use a larger `KIMI_MODEL` |
| Slack `invalid_blocks` | Message too long; reduce items or split manually |
| Empty digest every day | No unread in lookback window, or all IDs in checkpoint |

## Project layout

```
gmail-digest-agent/
  src/
    auth_gmail.py    # OAuth setup
    config.py
    gmail_client.py
    kimi_client.py
    slack_notify.py
    checkpoint.py
    main.py
  requirements.txt
  .env.example
```
