# BaseSettings — a Pydantic model that reads from the environment

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    app_name: str = "Library API"
    debug: bool = False
    cors_origins_raw: str = "http://localhost:3000"
    secret_key: str  # no default

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()


# "Never hardcode secrets" — proven, not just stated

secret_key: str   # no default value