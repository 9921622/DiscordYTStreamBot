import httpx
from pydantic import BaseModel
from typing import Literal, Any

from dataclasses import dataclass
from settings import settings

""" this is an api wrapper for the backend """


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
    discord_id: str
    username: str
    global_name: str | None
    avatar: str | None


class GuildQueueItemSchema(BaseModel):
    id: int
    video: YoutubeVideoSchema
    order: int
    added_by: DiscordUserSchema | None


class GuildQueueSchema(BaseModel):
    id: int
    items: list[GuildQueueItemSchema] = []


class AbstractAPI:
    HTTPMethod = Literal["GET", "POST", "PATCH", "DELETE"]

    @staticmethod
    def auth_headers():
        return {"X-Internal-Key": settings.INTERNAL_API_KEY}

    @classmethod
    async def request(
        cls, method: HTTPMethod, url: str, *, json: dict | None = None, params: dict | None = None
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


class QueueAPI(AbstractAPI):

    @staticmethod
    def guild_queue_url(guild_id):
        return f"{settings.BACKEND_HOST}/api/discord/guild/{guild_id}/queue/"

    @staticmethod
    def guild_queue_item_url(guild_id, item_id):
        return f"{settings.BACKEND_HOST}/api/discord/guild/{guild_id}/queue/items/{item_id}/"

    @staticmethod
    def guild_queue_items_url(guild_id):
        return f"{settings.BACKEND_HOST}/api/discord/guild/{guild_id}/queue/items/"

    @classmethod
    async def get(cls, guild_id) -> ResponseWrapper:
        response = await cls.request("GET", cls.guild_queue_url(guild_id))
        data = GuildQueueSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)

    @classmethod
    async def add(cls, guild_id, youtube_id) -> ResponseWrapper:
        response = await cls.request(
            "POST",
            cls.guild_queue_items_url(guild_id),
            json={"youtube_id": youtube_id},
        )
        data = GuildQueueItemSchema.model_validate(response.json()) if response.is_success else None
        return ResponseWrapper(response=response, data=data)

    @classmethod
    async def remove(cls, guild_id, item_id) -> ResponseWrapper:
        response = await cls.request("DELETE", cls.guild_queue_item_url(guild_id, item_id))
        return ResponseWrapper(response=response, data=None)

    @classmethod
    async def reorder(cls, guild_id, order) -> ResponseWrapper:
        response = await cls.request(
            "PATCH",
            cls.guild_queue_items_url(guild_id),
            json={"order": order},
        )
        return ResponseWrapper(response=response, data=None)

    @classmethod
    async def clear(cls, guild_id) -> ResponseWrapper:
        response = await cls.request("DELETE", cls.guild_queue_url(guild_id))
        return ResponseWrapper(response=response, data=None)
