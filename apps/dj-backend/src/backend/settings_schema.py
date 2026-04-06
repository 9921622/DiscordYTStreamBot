from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Django
    DJANGO_SECRET_KEY: str
    DEBUG: bool = False
    FRONTEND_URL: str
    ALLOWED_HOSTS: list[str] = []
    CORS_ALLOWED_ORIGINS: list[str] = []

    # POSTgres DB
    DB_NAME: str
    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str

    # Discord
    DISCORD_OAUTH_REDIRECT_URL: str  # this is the login page where it should redirect after oauth
    DISCORD_CLIENT_SECRET: str
    DISCORD_CLIENT_ID: str

    # Internal
    INTERNAL_API_KEY: str

    @field_validator("ALLOWED_HOSTS", mode="before")
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            import json
            v = json.loads(v)
        return [host.removeprefix("https://").removeprefix("http://") for host in v]

    @field_validator("CORS_ALLOWED_ORIGINS", mode="before")
    @classmethod
    def parse_list(cls, v):
        if isinstance(v, str):
            import json
            return json.loads(v)
        return v


env = AppSettings()
