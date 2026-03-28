from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Discord
    DISCORD_TOKEN: str
    DISCORD_DEBUG_SERVER: int | None = None
    DISCORD_DEBUG_VC: int | None = None
    DISCORD_DEBUG_CHANNEL: int | None = None

    # App
    APP_HOST: str
    APP_PORT: int
    BACKEND_HOST: str
    CORS_HOSTS: list[str]

    # Flags
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
