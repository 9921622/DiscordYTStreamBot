from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Discord
    DISCORD_BOT_TOKEN: str

    # Backend
    INTERNAL_API_KEY: str

    # Frontend
    FRONTEND_URL: str

    # App
    APP_HOST: str = "0.0.0.0"  # change this. change Dockerfile
    APP_PORT: int = 8080  # change this. change Dockerfile
    BACKEND_HOST: str
    CORS_ALLOWED_ORIGINS: list[str]

    # Flags
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
