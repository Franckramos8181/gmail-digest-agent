from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    google_client_id: str = Field(alias="GOOGLE_CLIENT_ID")
    google_client_secret: str = Field(alias="GOOGLE_CLIENT_SECRET")
    gmail_refresh_token: str = Field(default="", alias="GMAIL_REFRESH_TOKEN")

    kimi_api_key: str = Field(alias="KIMI_API_KEY")
    kimi_base_url: str = Field(
        default="https://api.moonshot.cn/v1",
        alias="KIMI_BASE_URL",
    )
    kimi_model: str = Field(default="moonshot-v1-8k", alias="KIMI_MODEL")

    slack_webhook_url: str = Field(default="", alias="SLACK_WEBHOOK_URL")
    slack_bot_token: str = Field(default="", alias="SLACK_BOT_TOKEN")
    slack_channel_id: str = Field(default="", alias="SLACK_CHANNEL_ID")

    max_emails: int = Field(default=50, alias="MAX_EMAILS")
    lookback_hours: int = Field(default=48, alias="LOOKBACK_HOURS")
    timezone: str = Field(default="America/New_York", alias="TIMEZONE")
    include_weekends: bool = Field(default=True, alias="INCLUDE_WEEKENDS")

    checkpoint_path: Path = Field(
        default=Path(".checkpoint.json"),
        alias="CHECKPOINT_PATH",
    )

    def validate_slack(self) -> None:
        if self.slack_webhook_url:
            return
        if self.slack_bot_token and self.slack_channel_id:
            return
        raise ValueError(
            "Set SLACK_WEBHOOK_URL or both SLACK_BOT_TOKEN and SLACK_CHANNEL_ID"
        )


def load_settings() -> Settings:
    return Settings()
