import httpx
from typing import Literal, Any

from settings import settings

""" this is an api wrapper for the backend """


def auth_headers():
    return {"X-Internal-Key": settings.INTERNAL_API_KEY}


def play_url(video_id):
    return f"{settings.BACKEND_HOST}/api/youtube/videos/{video_id}/get-source/"


def guild_queue_url(guild_id):
    return f"{settings.BACKEND_HOST}/api/discord/guild/{guild_id}/queue/"


def guild_queue_item_url(guild_id, item_id):
    return f"{settings.BACKEND_HOST}/api/discord/guild/{guild_id}/queue/items/{item_id}/"


def guild_queue_items_url(guild_id):
    return f"{settings.BACKEND_HOST}/api/discord/guild/{guild_id}/queue/items/"


class AbstractAPI:
    HTTPMethod = Literal["GET", "POST", "PATCH", "DELETE"]

    async def request(
        method: HTTPMethod, url: str, *, json: dict | None = None, params: dict | None = None
    ) -> httpx.Response:

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=auth_headers(),
            )
        return response


class VideoAPI:

    async def get_source(video_id):
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(play_url(video_id=video_id))
        return response


class QueueAPI(AbstractAPI):

    @classmethod
    async def get(cls, guild_id):
        return await cls.request(
            "GET",
            guild_queue_url(guild_id),
        )

    @classmethod
    async def add(cls, guild_id, youtube_id):
        return await cls.request(
            "POST",
            guild_queue_items_url(guild_id),
            json={"youtube_id": youtube_id},
        )

    @classmethod
    async def remove(cls, guild_id, item_id):
        return await cls.request(
            "DELETE",
            guild_queue_item_url(guild_id, item_id),
        )

    @classmethod
    async def reorder(cls, guild_id, order):
        return await cls.request(
            "PATCH",
            guild_queue_items_url(guild_id),
            json={"order": order},
        )

    @classmethod
    async def clear(cls, guild_id):
        return await cls.request(
            "DELETE",
            guild_queue_url(guild_id),
        )
