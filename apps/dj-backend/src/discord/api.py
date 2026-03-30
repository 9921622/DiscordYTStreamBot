import requests
from django.conf import settings


DISCORD_API_BASE = "https://discord.com/api/v10"
DISCORD_CDN_BASE = "https://cdn.discordapp.com"


class DiscordAPIClient:
    """Wrapper around the Discord API using a user's bearer token."""

    def __init__(self, access_token: str):
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
        )

    def _get(self, endpoint: str) -> dict:
        response = self.session.get(f"{DISCORD_API_BASE}{endpoint}")
        response.raise_for_status()
        return response.json()

    def get_current_user(self) -> dict:
        """GET /users/@me"""
        return self._get("/users/@me")

    def get_current_user_guilds(self) -> list:
        """GET /users/@me/guilds"""
        return self._get("/users/@me/guilds")


class DiscordCDNAPI:

    def build_avatar_url(discord_id: str, avatar_hash: str, size: int = 128) -> str | None:
        """Constructs the CDN URL for a user's avatar.
        avatars/user_id/user_avatar.png *

        https://discord.com/developers/docs/reference#image-formatting
        Returns None if the user has no avatar (use default avatar instead).
        """
        if not avatar_hash:
            return None
        return f"{DISCORD_CDN_BASE}/avatars/{discord_id}/{avatar_hash}.png?size={size}"
