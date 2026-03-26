from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Discord
    DISCORD_TOKEN: str
    DISCORD_DEBUG_SERVER: str | None = None

    # App
    APP_HOST: str
    APP_PORT: int

    # Flags
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
