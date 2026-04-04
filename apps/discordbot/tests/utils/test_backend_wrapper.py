import pytest
from unittest.mock import AsyncMock, patch

from utils.api_backend_wrapper import (
    VideoAPI,
    QueueAPI,
    VideoSourceSchema,
    GuildQueueSchema,
    GuildQueueItemSchema,
    ResponseWrapper,
)

from tests.mocks import make_mock_httpx_response
from tests.utils.factories import GuildQueueSchemaFactory, GuildQueueItemSchemaFactory

HTTPX_ASYNC_CLIENT = "utils.api_backend_wrapper.httpx.AsyncClient"
GUILD_ID = "123"
VIDEO_ID = "video_id"
ITEM_ID = "23123"
DISCORD_ID = "123213"


class TestVideoAPI:
    @pytest.mark.asyncio
    async def test_get_source_success(self):
        mock_response = make_mock_httpx_response(200, {"source_url": "https://example.com/audio.mp3"})
        with patch(HTTPX_ASYNC_CLIENT) as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            rw = await VideoAPI.get_source(VIDEO_ID)

        assert isinstance(rw, ResponseWrapper)
        assert isinstance(rw.data, VideoSourceSchema)
        assert rw.data.source_url == "https://example.com/audio.mp3"

    @pytest.mark.asyncio
    async def test_get_source_failure(self):
        mock_response = make_mock_httpx_response(404, {"detail": "not found"})
        with patch(HTTPX_ASYNC_CLIENT) as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)
            rw = await VideoAPI.get_source(VIDEO_ID)

        assert rw.data is None
        assert not rw.response.is_success


class TestQueueAPI:
    @pytest.mark.asyncio
    async def test_get(self):
        queue = GuildQueueSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(QueueAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await QueueAPI.get(GUILD_ID)

        assert isinstance(rw.data, GuildQueueSchema)

    @pytest.mark.asyncio
    async def test_add(self):
        item = GuildQueueItemSchemaFactory.build()
        mock_response = make_mock_httpx_response(201, item.model_dump())
        with patch.object(QueueAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await QueueAPI.add(GUILD_ID, VIDEO_ID, DISCORD_ID)

        assert isinstance(rw.data, GuildQueueItemSchema)

    @pytest.mark.asyncio
    async def test_remove(self):
        mock_response = make_mock_httpx_response(204, {})
        with patch.object(QueueAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await QueueAPI.remove(GUILD_ID, ITEM_ID)

        assert rw.data is None
        assert rw.response.is_success

    @pytest.mark.asyncio
    async def test_reorder(self):
        mock_response = make_mock_httpx_response(200, {"ok": True})
        with patch.object(QueueAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await QueueAPI.reorder(GUILD_ID, [3, 1, 2])

        assert rw.data is None
        assert rw.response.is_success

    @pytest.mark.asyncio
    async def test_clear(self):
        mock_response = make_mock_httpx_response(204, {})
        with patch.object(QueueAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await QueueAPI.clear(GUILD_ID)

        assert rw.data is None
        assert rw.response.is_success
