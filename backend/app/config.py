from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    discord_bot_token: str = ""
    discord_channel_id: str = ""
    gemini_api_key: str = ""
    google_calendar_client_id: str = ""
    google_calendar_client_secret: str = ""
    google_refresh_token: str = ""
    database_url: str = "sqlite+aiosqlite:///./data/mysecretary.db"
    timezone: str = "Asia/Seoul"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
