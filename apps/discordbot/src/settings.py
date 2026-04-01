from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Discord
    DISCORD_TOKEN: str

    # Backend
    INTERNAL_API_KEY: str

    # App
    APP_HOST: str
    APP_PORT: int
    BACKEND_HOST: str
    CORS_HOSTS: list[str]

    # Flags
    DEBUG: bool = False

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True)


settings = Settings()
