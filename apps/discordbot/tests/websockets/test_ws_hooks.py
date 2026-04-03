import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from utils.api_backend_wrapper import (
    ResponseWrapper,
    GuildQueueSchema,
    GuildQueueItemSchema,
    YoutubeVideoSchema,
    VideoSourceSchema,
    DiscordUserSchema,
)
from ws.hooks import OnDisconnect, OnVoice, OnSongStart, OnSongEnd
from ws.ws_response import WSResponse

from tests.utils import make_mock_httpx_response, make_mock_response_wrapper, TestCaseCommand


GUILD_ID = 1238723


def make_video(youtube_id="vid123", title="Test Video") -> YoutubeVideoSchema:
    return YoutubeVideoSchema(
        youtube_id=youtube_id,
        title=title,
        creator="Creator",
        source_url="http://example.com/audio",
        duration=200,
        thumbnail=None,
    )


def make_queue_item(item_id=1, youtube_id="vid123") -> GuildQueueItemSchema:
    return GuildQueueItemSchema(
        id=item_id,
        video=make_video(youtube_id),
        order=0,
        added_by=None,
    )


def make_queue(items: list[GuildQueueItemSchema] | None = None) -> GuildQueueSchema:
    return GuildQueueSchema(id=GUILD_ID, items=items or [])


class TestHookCase(TestCaseCommand):

    def make_hook(self, cls, guild_id=GUILD_ID):
        hook = cls.__new__(cls)
        hook.guild_id = guild_id
        hook.ws_manager = AsyncMock()
        hook.send = AsyncMock()
        return hook


class TestOnDisconnect(TestHookCase):

    @pytest.mark.asyncio
    async def test_disconnects_all(self):
        hook = self.make_hook(OnDisconnect)
        await hook.handle()
        hook.ws_manager.disconnect_all.assert_called_once_with(GUILD_ID)


class TestOnVoice(TestHookCase):

    @pytest.mark.asyncio
    async def test_sends_members(self):
        hook = self.make_hook(OnVoice)
        mock_members = MagicMock()
        mock_members.model_dump.return_value = {"members": []}

        with patch("ws.hooks.bot") as mock_bot:
            mock_bot.vc_get_members.return_value = mock_members
            await hook.handle()

        hook.send.assert_called_once()
        sent: WSResponse = hook.send.call_args[0][0]
        assert sent.type == "users"
        assert sent.success is True
        assert "members" in sent.data


class TestOnSongStart(TestHookCase):

    @pytest.mark.asyncio
    async def test_sends_song_start_and_status(self):
        hook = self.make_hook(OnSongStart)
        mock_status = MagicMock()
        mock_status.model_dump.return_value = {"playing": True}

        with patch("ws.hooks.bot") as mock_bot:
            mock_bot.vc_get_status.return_value = mock_status
            await hook.handle()

        assert hook.send.call_count == 2
        calls = [c[0][0] for c in hook.send.call_args_list]

        assert calls[0].type == "song_start"
        assert calls[0].success is True

        assert calls[1].type == "status"
        assert calls[1].success is True
        assert "playback" in calls[1].data


class TestOnSongEnd(TestHookCase):

    @pytest.mark.asyncio
    async def test_sends_song_end_no_next(self):
        hook = self.make_hook(OnSongEnd)
        empty_queue = make_queue([])

        with patch("ws.hooks.QueueAPI") as mock_queue:
            mock_queue.get = AsyncMock(return_value=make_mock_response_wrapper(200, empty_queue))
            await hook.handle()

        hook.send.assert_called_once()
        sent: WSResponse = hook.send.call_args[0][0]
        assert sent.type == "song_end"
        assert sent.data["next_song"] is False

    @pytest.mark.asyncio
    async def test_sends_song_end_with_next(self):
        hook = self.make_hook(OnSongEnd)
        item = make_queue_item()
        queue_with_item = make_queue([item])
        empty_queue = make_queue([])

        source_data = VideoSourceSchema(source_url="http://example.com/audio")
        source_wrapper = ResponseWrapper(response=make_mock_httpx_response(200), data=source_data)

        with (
            patch("ws.hooks.QueueAPI") as mock_queue,
            patch("ws.hooks.VideoAPI") as mock_video,
            patch("ws.hooks.bot") as mock_bot,
        ):

            mock_queue.get = AsyncMock(
                side_effect=[
                    make_mock_response_wrapper(200, queue_with_item),
                    make_mock_response_wrapper(200, empty_queue),
                ]
            )
            mock_queue.remove = AsyncMock(return_value=make_mock_response_wrapper(204))
            mock_video.get_source = AsyncMock(return_value=source_wrapper)
            mock_bot.vc_play = AsyncMock()

            await hook.handle()

        types = [c[0][0].type for c in hook.send.call_args_list]
        assert "song_end" in types
        assert "play" in types
        assert "queue-remove" in types

        play_call = next(c[0][0] for c in hook.send.call_args_list if c[0][0].type == "play")
        assert play_call.data["video_id"] == item.video.youtube_id

        mock_queue.remove.assert_called_once_with(GUILD_ID, item.id)
        mock_bot.vc_play.assert_called_once_with(GUILD_ID, item.video.youtube_id, source_data.source_url)

    @pytest.mark.asyncio
    async def test_play_next_skips_on_bad_source(self):
        hook = self.make_hook(OnSongEnd)
        item = make_queue_item()
        queue_with_item = make_queue([item])

        source_wrapper = ResponseWrapper(response=make_mock_httpx_response(500), data=None)

        with (
            patch("ws.hooks.QueueAPI") as mock_queue,
            patch("ws.hooks.VideoAPI") as mock_video,
            patch("ws.hooks.bot") as mock_bot,
        ):

            mock_queue.get = AsyncMock(return_value=make_mock_response_wrapper(200, queue_with_item))
            mock_video.get_source = AsyncMock(return_value=source_wrapper)
            mock_bot.vc_play = AsyncMock()

            await hook.handle()

        mock_bot.vc_play.assert_not_called()
        mock_queue.remove = AsyncMock()
        mock_queue.remove.assert_not_called()

    @pytest.mark.asyncio
    async def test_get_queue_returns_empty_on_failure(self):
        hook = self.make_hook(OnSongEnd)

        with patch("ws.hooks.QueueAPI") as mock_queue:
            mock_queue.get = AsyncMock(return_value=make_mock_response_wrapper(500, None))
            items = await hook._get_queue()

        assert items == []
