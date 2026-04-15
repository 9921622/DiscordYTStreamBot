import httpx
from pydantic import BaseModel, field_validator
from typing import Literal, Optional

from dataclasses import dataclass
from settings import settings

""" this is an api wrapper for the backend.

theses schemas should matches the schemas in dj-backend.discord.serializers
"""


class YoutubeVideoSchema(BaseModel):
    youtube_id: str
    title: str
    creator: str
    source_url: str
    duration: int
    thumbnail: str | None
    tags: list[str] = []


class VideoSourceSchema(BaseModel):
    source_url: str


class DiscordUserSchema(BaseModel):
    # dj-backend.discord.serializers
    # ["discord_id", "global_name", "avatar_url"]
    discord_id: str
    global_name: str | None
    avatar_url: str | None


class GuildPlaylistItemSchema(BaseModel):
    # dj-backend.discord.serializers
    # ["id", "video", "order", "added_by", "added_at"]
    id: int
    video: YoutubeVideoSchema
    order: int
    added_by: DiscordUserSchema | None


class GuildPlaylistSchema(BaseModel):
    # dj-backend.discord.serializers
    # ["id", "guild", "current_item", "items", "created_at", "updated_at"]
    id: int
    current_item: GuildPlaylistItemSchema | None = None
    items: list[GuildPlaylistItemSchema] = []


class AbstractAPI:
    HTTPMethod = Literal["GET", "POST", "PATCH", "DELETE"]

    @staticmethod
    def auth_headers():
        return {"X-Internal-Key": settings.INTERNAL_API_KEY}

    @classmethod
    async def request(
        cls,
        method: HTTPMethod,
        url: str,
        *,
        json: dict | None = None,
        params: dict | None = None,
    ) -> httpx.Response:

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=cls.auth_headers(),
            )
        return response


@dataclass
class ResponseWrapper:
    response: httpx.Response
    data: object


class VideoAPI:

    @staticmethod
    def play_url(video_id):
        return f"{settings.BACKEND_HOST}/api/youtube/videos/{video_id}/get-source/"

    @classmethod
    async def get_source(cls, video_id) -> ResponseWrapper:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(cls.play_url(video_id=video_id))
        data = VideoSourceSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)


class GuildPlaylistAPI(AbstractAPI):

    @staticmethod
    def base_url(guild_id: str) -> str:
        return f"{settings.BACKEND_HOST}/api/discord/guilds/{guild_id}/playlist/"

    @staticmethod
    def add_song_url(guild_id: str) -> str:
        return f"{GuildPlaylistAPI.base_url(guild_id)}add-song/"

    @staticmethod
    def remove_song_url(guild_id: str) -> str:
        return f"{GuildPlaylistAPI.base_url(guild_id)}remove-song/"

    @staticmethod
    def next_url(guild_id: str) -> str:
        return f"{GuildPlaylistAPI.base_url(guild_id)}next/"

    @staticmethod
    def play_now_url(guild_id: str) -> str:
        return f"{GuildPlaylistAPI.base_url(guild_id)}play-now/"

    @staticmethod
    def prev_url(guild_id: str) -> str:
        return f"{GuildPlaylistAPI.base_url(guild_id)}prev/"

    @staticmethod
    def reorder_url(guild_id: str) -> str:
        return f"{GuildPlaylistAPI.base_url(guild_id)}reorder/"

    # CORE METHODS

    @classmethod
    async def get(cls, guild_id: str) -> ResponseWrapper:
        response = await cls.request("GET", cls.base_url(guild_id))
        data = GuildPlaylistSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)

    @classmethod
    async def clear(cls, guild_id: str) -> ResponseWrapper:
        response = await cls.request("DELETE", cls.base_url(guild_id))
        data = GuildPlaylistSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)

    # MUTATIONS

    @classmethod
    async def add_song(cls, guild_id: str, youtube_id: str, discord_id: str) -> ResponseWrapper:
        response = await cls.request(
            "PATCH",
            cls.add_song_url(guild_id),
            json={"youtube_id": youtube_id, "discord_id": discord_id},
        )
        data = GuildPlaylistSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)

    @classmethod
    async def remove_song(cls, guild_id: str, item_id: int) -> ResponseWrapper:
        response = await cls.request(
            "PATCH",
            cls.remove_song_url(guild_id),
            json={"item_id": item_id},
        )
        data = GuildPlaylistSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)

    @classmethod
    async def reorder(cls, guild_id: str, order: list[int]) -> ResponseWrapper:
        response = await cls.request(
            "PATCH",
            cls.reorder_url(guild_id),
            json={"order": order},
        )
        data = GuildPlaylistSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)

    # NAVIGATION

    @classmethod
    async def next(cls, guild_id: str, *, item_id: int | None = None) -> ResponseWrapper:
        payload = {"item_id": item_id} if item_id else None
        response = await cls.request("PATCH", cls.next_url(guild_id), json=payload)
        data = GuildPlaylistSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)

    @classmethod
    async def play_now(
        cls,
        guild_id: str,
        discord_id: str,
        *,
        item_id: int | None = None,
        video_id: str | None = None,
    ) -> ResponseWrapper:
        payload: dict = {"discord_id": discord_id}
        if item_id:
            payload["item_id"] = item_id
        if video_id:
            payload["video_id"] = video_id

        response = await cls.request(
            "PATCH",
            cls.play_now_url(guild_id),
            json=payload,
        )
        data = GuildPlaylistSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)

    @classmethod
    async def prev(cls, guild_id: str) -> ResponseWrapper:
        response = await cls.request("PATCH", cls.prev_url(guild_id))
        data = GuildPlaylistSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)
