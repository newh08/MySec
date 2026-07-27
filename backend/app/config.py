from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    discord_bot_token: str = ""
    discord_channel_id: str = ""
    discord_user_id: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash"
    google_calendar_client_id: str = ""
    google_calendar_client_secret: str = ""
    google_refresh_token: str = ""
    google_calendar_id: str = "primary"
    database_url: str = "sqlite+aiosqlite:///./data/mysecretary.db"
    timezone: str = "Asia/Seoul"
    fixed_question_count: int = 5
    max_follow_ups: int = 3
    cors_origins: list[str] = ["http://localhost:3000", "http://frontend:3000"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
