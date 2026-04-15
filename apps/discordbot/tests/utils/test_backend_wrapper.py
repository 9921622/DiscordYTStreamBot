import pytest
from unittest.mock import AsyncMock, patch

from utils.api_backend_wrapper import (
    VideoAPI,
    GuildPlaylistAPI,
    VideoSourceSchema,
    GuildPlaylistSchema,
    ResponseWrapper,
)

from tests.mocks import make_mock_httpx_response
from tests.utils.factories import GuildPlaylistSchemaFactory

HTTPX_ASYNC_CLIENT = "utils.api_backend_wrapper.httpx.AsyncClient"
GUILD_ID = "123"
VIDEO_ID = "video_id"
ITEM_ID = 23123
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


class TestGuildPlaylistAPI:
    @pytest.mark.asyncio
    async def test_get_success(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.get(GUILD_ID)

        assert isinstance(rw, ResponseWrapper)
        assert isinstance(rw.data, GuildPlaylistSchema)

    @pytest.mark.asyncio
    async def test_get_failure(self):
        mock_response = make_mock_httpx_response(404, {"detail": "not found"})
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.get(GUILD_ID)

        assert rw.data is None
        assert not rw.response.is_success

    @pytest.mark.asyncio
    async def test_add_song_success(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.add_song(GUILD_ID, VIDEO_ID, DISCORD_ID)

        assert isinstance(rw, ResponseWrapper)
        assert isinstance(rw.data, GuildPlaylistSchema)

    @pytest.mark.asyncio
    async def test_add_song_failure(self):
        mock_response = make_mock_httpx_response(400, {"detail": "bad request"})
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.add_song(GUILD_ID, VIDEO_ID, DISCORD_ID)

        assert rw.data is None
        assert not rw.response.is_success

    @pytest.mark.asyncio
    async def test_remove_song_success(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.remove_song(GUILD_ID, ITEM_ID)

        assert isinstance(rw, ResponseWrapper)
        assert isinstance(rw.data, GuildPlaylistSchema)

    @pytest.mark.asyncio
    async def test_remove_song_failure(self):
        mock_response = make_mock_httpx_response(404, {"detail": "not found"})
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.remove_song(GUILD_ID, ITEM_ID)

        assert rw.data is None
        assert not rw.response.is_success

    @pytest.mark.asyncio
    async def test_reorder_success(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.reorder(GUILD_ID, [3, 1, 2])

        assert isinstance(rw, ResponseWrapper)
        assert isinstance(rw.data, GuildPlaylistSchema)

    @pytest.mark.asyncio
    async def test_reorder_failure(self):
        mock_response = make_mock_httpx_response(400, {"detail": "bad request"})
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.reorder(GUILD_ID, [3, 1, 2])

        assert rw.data is None
        assert not rw.response.is_success

    @pytest.mark.asyncio
    async def test_clear_success(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.clear(GUILD_ID)

        assert isinstance(rw, ResponseWrapper)
        assert isinstance(rw.data, GuildPlaylistSchema)

    @pytest.mark.asyncio
    async def test_clear_failure(self):
        mock_response = make_mock_httpx_response(400, {"detail": "bad request"})
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.clear(GUILD_ID)

        assert rw.data is None
        assert not rw.response.is_success

    # --- next ---------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_next_success(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.next(GUILD_ID)

        assert isinstance(rw, ResponseWrapper)
        assert isinstance(rw.data, GuildPlaylistSchema)

    @pytest.mark.asyncio
    async def test_next_with_item_id_sends_item_id_in_payload(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)) as mock_request:
            rw = await GuildPlaylistAPI.next(GUILD_ID, item_id=ITEM_ID)

        assert isinstance(rw.data, GuildPlaylistSchema)
        assert mock_request.call_args[1]["json"]["item_id"] == ITEM_ID

    @pytest.mark.asyncio
    async def test_next_without_item_id_sends_no_payload(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)) as mock_request:
            rw = await GuildPlaylistAPI.next(GUILD_ID)

        assert isinstance(rw.data, GuildPlaylistSchema)
        assert mock_request.call_args[1]["json"] is None

    @pytest.mark.asyncio
    async def test_next_failure(self):
        mock_response = make_mock_httpx_response(400, {"detail": "bad request"})
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.next(GUILD_ID)

        assert rw.data is None
        assert not rw.response.is_success

    # --- play_now -----------------------------------------------------------

    @pytest.mark.asyncio
    async def test_play_now_with_video_id_success(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)) as mock_request:
            rw = await GuildPlaylistAPI.play_now(GUILD_ID, DISCORD_ID, video_id=VIDEO_ID)

        assert isinstance(rw, ResponseWrapper)
        assert isinstance(rw.data, GuildPlaylistSchema)
        payload = mock_request.call_args[1]["json"]
        assert payload["discord_id"] == DISCORD_ID
        assert payload["video_id"] == VIDEO_ID
        assert "item_id" not in payload

    @pytest.mark.asyncio
    async def test_play_now_with_item_id_success(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)) as mock_request:
            rw = await GuildPlaylistAPI.play_now(GUILD_ID, DISCORD_ID, item_id=ITEM_ID)

        assert isinstance(rw, ResponseWrapper)
        assert isinstance(rw.data, GuildPlaylistSchema)
        payload = mock_request.call_args[1]["json"]
        assert payload["discord_id"] == DISCORD_ID
        assert payload["item_id"] == ITEM_ID
        assert "video_id" not in payload

    @pytest.mark.asyncio
    async def test_play_now_always_sends_discord_id(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)) as mock_request:
            await GuildPlaylistAPI.play_now(GUILD_ID, DISCORD_ID, video_id=VIDEO_ID)

        assert mock_request.call_args[1]["json"]["discord_id"] == DISCORD_ID

    @pytest.mark.asyncio
    async def test_play_now_failure(self):
        mock_response = make_mock_httpx_response(400, {"detail": "bad request"})
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.play_now(GUILD_ID, DISCORD_ID, video_id=VIDEO_ID)

        assert rw.data is None
        assert not rw.response.is_success

    # --- prev ---------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_prev_success(self):
        queue = GuildPlaylistSchemaFactory.build()
        mock_response = make_mock_httpx_response(200, queue.model_dump())
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.prev(GUILD_ID)

        assert isinstance(rw, ResponseWrapper)
        assert isinstance(rw.data, GuildPlaylistSchema)

    @pytest.mark.asyncio
    async def test_prev_failure(self):
        mock_response = make_mock_httpx_response(400, {"detail": "bad request"})
        with patch.object(GuildPlaylistAPI, "request", AsyncMock(return_value=mock_response)):
            rw = await GuildPlaylistAPI.prev(GUILD_ID)

        assert rw.data is None
        assert not rw.response.is_success
