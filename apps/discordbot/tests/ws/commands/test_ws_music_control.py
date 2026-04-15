import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import contextmanager

from ws.ws_commands_router import get_registered_commands
from utils.api_backend_wrapper import VideoAPI, GuildPlaylistAPI

from tests.test_case import CommandTestCase
from tests.ws.test_case import WebSocketTestCase
from tests.bot.factories import PlaybackStatusFactory
from tests.utils.mocks import make_mock_video_response
from tests.utils.factories import GuildPlaylistSchemaFactory

GUILD_ID = 123878273492
DISCORD_ID = 123456789


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@contextmanager
def patch_bot():
    with patch("ws.commands.music_controls.bot") as mock_bot:
        mock_bot.vc_play = AsyncMock()
        yield mock_bot


@contextmanager
def patch_voice_client(vc: MagicMock | None):
    with patch_bot() as mock_bot:
        mock_bot.get_voice_client.return_value = vc
        yield mock_bot


@contextmanager
def patch_video_source(status_code: int = 200):
    from tests.mocks import make_mock_httpx_response
    from utils.api_backend_wrapper import ResponseWrapper, VideoSourceSchema

    data = VideoSourceSchema(source_url="https://example.com/audio.mp3") if status_code == 200 else None
    rw = ResponseWrapper(
        response=make_mock_httpx_response(status_code, {}),
        data=data,
    )
    with patch.object(VideoAPI, "get_source", new=AsyncMock(return_value=rw)):
        yield


def _make_playlist_rw(playlist=None, error=None):
    from tests.mocks import make_mock_httpx_response
    from utils.api_backend_wrapper import ResponseWrapper

    if error:
        return ResponseWrapper(
            response=make_mock_httpx_response(500, {"detail": str(error)}),
            data=None,
        )
    return ResponseWrapper(
        response=make_mock_httpx_response(200, {}),
        data=playlist or GuildPlaylistSchemaFactory.build(),
    )


@contextmanager
def patch_playlist_get(playlist=None, error=None):
    """Patch GuildPlaylistAPI.get used by PlayCommand._resume_current."""
    with patch.object(GuildPlaylistAPI, "get", new=AsyncMock(return_value=_make_playlist_rw(playlist, error))):
        yield


@contextmanager
def patch_playlist_next(playlist=None, error=None):
    """Patch GuildPlaylistAPI.next used by PlayCommand._advance_and_play."""
    with patch.object(GuildPlaylistAPI, "next", new=AsyncMock(return_value=_make_playlist_rw(playlist, error))):
        yield


@contextmanager
def patch_playlist_play_now(playlist=None, error=None):
    """Patch GuildPlaylistAPI.play_now used by PlayNowCommand."""
    with patch.object(GuildPlaylistAPI, "play_now", new=AsyncMock(return_value=_make_playlist_rw(playlist, error))):
        yield


@contextmanager
def patch_bot_status(status):
    with patch_bot() as mock_bot:
        mock_bot.vc_get_status.return_value = status
        yield mock_bot


@contextmanager
def patch_bot_seek(status=None, error: Exception | None = None):
    with patch_bot() as mock_bot:
        mock_bot.vc_seek = AsyncMock(side_effect=error) if error else AsyncMock()
        if status is not None:
            mock_bot.vc_get_status.return_value = status
        yield mock_bot


@contextmanager
def patch_bot_loop(status=None, error: Exception | None = None):
    with patch_bot() as mock_bot:
        mock_bot.vc_loop = AsyncMock(side_effect=error) if error else AsyncMock()
        if status is not None:
            mock_bot.vc_get_status.return_value = status
        yield mock_bot


@contextmanager
def patch_bot_volume(return_value=None, error: Exception | None = None):
    with patch_bot() as mock_bot:
        mock_bot.vc_volume = AsyncMock(side_effect=error) if error else AsyncMock(return_value=return_value)
        yield mock_bot


class TestCaseMusic(CommandTestCase, WebSocketTestCase):
    pass


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


class TestStatusCommand(TestCaseMusic):

    def test_exists(self):
        assert "status" in get_registered_commands()

    def test_status_returns_playback(self, client):
        mock_status = PlaybackStatusFactory.build()
        with patch_bot_status(mock_status):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "status", discord_id=DISCORD_ID)
                data = ws.receive_json()

        self.assert_success(data, "status")
        assert data["data"]
        assert data["data"]["playback"] == mock_status.model_dump()

    def test_status_not_broadcast(self, client):
        """Status is read-only — only the sender should receive a response."""
        mock_status = PlaybackStatusFactory.build()
        with patch_bot_status(mock_status):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                self.send_json(ws1, "status", discord_id=DISCORD_ID)
                self.assert_success(ws1.receive_json(), "status")
                self.assert_not_broadcast(ws2)


# ---------------------------------------------------------------------------
# Play
# ---------------------------------------------------------------------------


class TestPlayCommand(TestCaseMusic):

    def test_exists(self):
        assert "play" in get_registered_commands()

    # --- _advance_and_play path (bot busy or item_id provided) --------------

    def test_play_advances_queue_when_bot_is_busy(self, client):
        """Bot is playing — should always advance, never resume."""
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_next(playlist=playlist), patch_video_source(), patch_bot() as mock_bot:
            mock_bot.get_voice_client.return_value = MagicMock(is_playing=lambda: True, is_paused=lambda: False)
            mock_bot.vc_play = AsyncMock()
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play", discord_id=DISCORD_ID, video_id="abc", offset=0.0, volume=0.5)
                ack = ws.receive_json()

        self.assert_success(ack, "play")
        assert "playlist" in ack["data"]

    def test_play_advances_queue_when_item_id_provided(self, client):
        """Explicit item_id forces advance regardless of bot state."""
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_next(playlist=playlist), patch_video_source(), patch_bot() as mock_bot:
            mock_bot.get_voice_client.return_value = None  # bot idle
            mock_bot.vc_play = AsyncMock()
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play", discord_id=DISCORD_ID, item_id=42)
                ack = ws.receive_json()

        self.assert_success(ack, "play")
        assert "playlist" in ack["data"]

    def test_play_playlist_next_failure(self, client):
        """If GuildPlaylistAPI.next fails, play should return an error."""
        with patch_playlist_next(error="backend error"), patch_bot() as mock_bot:
            mock_bot.get_voice_client.return_value = MagicMock(is_playing=lambda: True, is_paused=lambda: False)
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play", discord_id=DISCORD_ID, video_id="abc")
                data = ws.receive_json()

        self.assert_error(data)

    def test_play_source_url_failure(self, client):
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_next(playlist=playlist), patch_video_source(status_code=500), patch_bot() as mock_bot:
            mock_bot.get_voice_client.return_value = MagicMock(is_playing=lambda: True, is_paused=lambda: False)
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play", discord_id=DISCORD_ID, video_id="abc")
                data = ws.receive_json()

        self.assert_error(data)

    def test_play_bot_not_in_channel(self, client):
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_next(playlist=playlist), patch_video_source(), patch_bot() as mock_bot:
            mock_bot.get_voice_client.return_value = MagicMock(is_playing=lambda: True, is_paused=lambda: False)
            mock_bot.vc_play = AsyncMock(side_effect=RuntimeError("not connected"))
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play", discord_id=DISCORD_ID, video_id="abc")
                data = ws.receive_json()

        self.assert_error(data)

    def test_play_broadcasts_status_to_guild(self, client):
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_next(playlist=playlist), patch_video_source(), patch_bot() as mock_bot:
            mock_bot.get_voice_client.return_value = MagicMock(is_playing=lambda: True, is_paused=lambda: False)
            mock_bot.vc_play = AsyncMock()
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                self.send_json(ws1, "play", discord_id=DISCORD_ID, video_id="abc")
                ws1.receive_json()
                data = ws2.receive_json()

        self.assert_success(data, "play")

    # --- _resume_current path (bot idle, no item_id) ------------------------

    def test_play_resumes_current_item_when_bot_is_idle(self, client):
        """Bot is idle with no item_id — should resume the playlist's current item."""
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_get(playlist=playlist), patch_video_source(), patch_bot() as mock_bot:
            mock_bot.get_voice_client.return_value = None
            mock_bot.vc_play = AsyncMock()
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play", discord_id=DISCORD_ID)
                ack = ws.receive_json()

        self.assert_success(ack, "play")
        assert "playlist" in ack["data"]

    def test_play_resume_get_playlist_failure(self, client):
        """GuildPlaylistAPI.get fails on the resume path."""
        with patch_playlist_get(error="backend error"), patch_bot() as mock_bot:
            mock_bot.get_voice_client.return_value = None
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play", discord_id=DISCORD_ID)
                data = ws.receive_json()

        self.assert_error(data)

    def test_play_resume_no_current_item_returns_error(self, client):
        """Playlist has no current_item — resume should return an error."""
        playlist = GuildPlaylistSchemaFactory.build(current_item=None)
        with patch_playlist_get(playlist=playlist), patch_bot() as mock_bot:
            mock_bot.get_voice_client.return_value = None
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play", discord_id=DISCORD_ID)
                data = ws.receive_json()

        self.assert_error(data)


# ---------------------------------------------------------------------------
# Play Now
# ---------------------------------------------------------------------------


class TestPlayNowCommand(TestCaseMusic):

    def test_exists(self):
        assert "play_now" in get_registered_commands()

    def test_play_now_with_video_id_success(self, client):
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_play_now(playlist=playlist), patch_video_source(), patch_bot() as mock_bot:
            mock_bot.vc_play = AsyncMock()
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play_now", discord_id=DISCORD_ID, video_id="abc")
                ack = ws.receive_json()

        self.assert_success(ack, "play_now")
        assert "playlist" in ack["data"]

    def test_play_now_with_item_id_success(self, client):
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_play_now(playlist=playlist), patch_video_source(), patch_bot() as mock_bot:
            mock_bot.vc_play = AsyncMock()
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play_now", discord_id=DISCORD_ID, item_id=42)
                ack = ws.receive_json()

        self.assert_success(ack, "play_now")
        assert "playlist" in ack["data"]

    def test_play_now_missing_both_ids_returns_error(self, client):
        """Neither item_id nor video_id provided — should fail validation."""
        with self.ws_connect(client, GUILD_ID) as ws:
            self.send_json(ws, "play_now", discord_id=DISCORD_ID)
            data = ws.receive_json()

        self.assert_error(data)

    def test_play_now_api_failure_returns_error(self, client):
        with patch_playlist_play_now(error="backend error"):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play_now", discord_id=DISCORD_ID, video_id="abc")
                data = ws.receive_json()

        self.assert_error(data)

    def test_play_now_no_current_item_after_api_returns_error(self, client):
        """API succeeds but returns a playlist with no current_item."""
        playlist = GuildPlaylistSchemaFactory.build(current_item=None)
        with patch_playlist_play_now(playlist=playlist), patch_video_source():
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play_now", discord_id=DISCORD_ID, video_id="abc")
                data = ws.receive_json()

        self.assert_error(data)

    def test_play_now_source_url_failure(self, client):
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_play_now(playlist=playlist), patch_video_source(status_code=500), patch_bot() as mock_bot:
            mock_bot.vc_play = AsyncMock()
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play_now", discord_id=DISCORD_ID, video_id="abc")
                data = ws.receive_json()

        self.assert_error(data)

    def test_play_now_bot_not_in_channel(self, client):
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_play_now(playlist=playlist), patch_video_source(), patch_bot() as mock_bot:
            mock_bot.vc_play = AsyncMock(side_effect=RuntimeError("not connected"))
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "play_now", discord_id=DISCORD_ID, video_id="abc")
                data = ws.receive_json()

        self.assert_error(data)

    def test_play_now_broadcasts_to_guild(self, client):
        playlist = GuildPlaylistSchemaFactory.build()
        with patch_playlist_play_now(playlist=playlist), patch_video_source(), patch_bot() as mock_bot:
            mock_bot.vc_play = AsyncMock()
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                self.send_json(ws1, "play_now", discord_id=DISCORD_ID, video_id="abc")
                ws1.receive_json()
                data = ws2.receive_json()

        self.assert_success(data, "play_now")


# ---------------------------------------------------------------------------
# Pause
# ---------------------------------------------------------------------------


class TestPauseCommand(TestCaseMusic):
    def test_exists(self):
        assert "pause" in get_registered_commands()

    def test_pause_while_playing(self, client):
        mock_vc = MagicMock()
        mock_vc.is_paused.return_value = False
        mock_vc.is_playing.return_value = True

        with patch_voice_client(mock_vc):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "pause", discord_id=DISCORD_ID)
                ack = ws.receive_json()

        self.assert_success(ack, "pause")
        assert ack["data"]
        mock_vc.pause.assert_called_once()

    def test_resume_while_paused(self, client):
        mock_vc = MagicMock()
        state = {"paused": True}
        mock_vc.is_paused.side_effect = lambda: state["paused"]
        mock_vc.is_playing.return_value = False
        mock_vc.resume.side_effect = lambda: state.update({"paused": False})

        with patch_voice_client(mock_vc):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "pause", discord_id=DISCORD_ID)
                ack = ws.receive_json()

        self.assert_success(ack, "pause")
        assert ack["data"]
        assert ack["data"]["paused"] is False

    def test_pause_not_connected(self, client):
        with patch_voice_client(None):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "pause", discord_id=DISCORD_ID)
                data = ws.receive_json()

        self.assert_error(data)

    def test_pause_nothing_playing(self, client):
        mock_vc = MagicMock()
        mock_vc.is_paused.return_value = False
        mock_vc.is_playing.return_value = False
        with patch_voice_client(mock_vc):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "pause", discord_id=DISCORD_ID)
                data = ws.receive_json()

        self.assert_error(data)


# ---------------------------------------------------------------------------
# Seek
# ---------------------------------------------------------------------------


class TestSeekCommand(TestCaseMusic):
    def test_exists(self):
        assert "seek" in get_registered_commands()

    def test_seek_success(self, client):
        with patch_bot_seek(status=PlaybackStatusFactory.build(position=42.0)):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "seek", discord_id=DISCORD_ID, position=42.0)

                ack = ws.receive_json()
                self.assert_success(ack, "seek")
                assert ack["data"]
                assert ack["data"]["position"] == 42.0

                broadcast = ws.receive_json()
                self.assert_success(broadcast, "status")

    def test_seek_missing_position(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            self.send_json(ws, "seek", discord_id=DISCORD_ID)
            data = ws.receive_json()

        self.assert_error(data, "position")

    def test_seek_nothing_playing(self, client):
        with patch_bot_seek(error=RuntimeError("nothing is playing")):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "seek", discord_id=DISCORD_ID, position=10.0)
                data = ws.receive_json()

        self.assert_error(data)


# ---------------------------------------------------------------------------
# Loop
# ---------------------------------------------------------------------------


class TestLoopCommand(TestCaseMusic):
    def test_exists(self):
        assert "loop" in get_registered_commands()

    def test_loop_toggles_on(self, client):
        with patch_bot_loop(status=PlaybackStatusFactory.build(loop=True)):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "loop", discord_id=DISCORD_ID)
                ack = ws.receive_json()
                broadcast = ws.receive_json()

        self.assert_success(ack, "loop")
        assert ack["data"]
        assert ack["data"]["loop"] is True
        self.assert_success(broadcast, "loop")

    def test_loop_toggles_off(self, client):
        with patch_bot_loop(status=PlaybackStatusFactory.build(loop=False)):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "loop", discord_id=DISCORD_ID)
                ack = ws.receive_json()
                broadcast = ws.receive_json()

        self.assert_success(ack, "loop")
        assert ack["data"]
        assert ack["data"]["loop"] is False
        self.assert_success(broadcast, "loop")

    def test_loop_nothing_playing(self, client):
        with patch_bot_loop(error=RuntimeError("Nothing is playing")):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "loop", discord_id=DISCORD_ID)
                data = ws.receive_json()

        self.assert_error(data)


# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------


class TestVolumeCommand(TestCaseMusic):
    def test_exists(self):
        assert "volume" in get_registered_commands()

    def test_volume_set(self, client):
        with patch_bot_volume(return_value=0.8):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "volume", discord_id=DISCORD_ID, level=0.8)
                ack = ws.receive_json()
                broadcast = ws.receive_json()

        self.assert_success(ack, "volume")
        assert ack["data"]
        assert ack["data"]["volume"] == 0.8
        self.assert_success(broadcast, "volume")

    def test_volume_get(self, client):
        with patch_bot_volume(return_value=0.5):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "volume", discord_id=DISCORD_ID)
                ack = ws.receive_json()

        self.assert_success(ack, "volume")
        assert ack["data"]
        assert ack["data"]["volume"] == 0.5

    def test_volume_no_audio_source(self, client):
        with patch_bot_volume(return_value=None):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "volume", discord_id=DISCORD_ID, level=0.8)
                data = ws.receive_json()

        self.assert_error(data)


# ---------------------------------------------------------------------------
# Stop
# ---------------------------------------------------------------------------


class TestStopCommand(TestCaseMusic):
    def test_exists(self):
        assert "stop" in get_registered_commands()


# ---------------------------------------------------------------------------
# Multi-session isolation
# ---------------------------------------------------------------------------


class TestMultiSession(TestCaseMusic):
    def test_different_guilds_dont_receive_each_others_broadcasts(self, client):
        OTHER_GUILD = 999999
        with patch_bot_seek(status=PlaybackStatusFactory.build()):
            with self.ws_connect(client, GUILD_ID) as ws1:
                with self.ws_connect(client, OTHER_GUILD) as ws2:
                    self.send_json(ws1, "seek", discord_id=DISCORD_ID, position=30.0)
                    ws1.receive_json()  # ack
                    ws1.receive_json()  # status
                    self.assert_not_broadcast(ws2)

    def test_errors_only_go_to_sender(self, client):
        with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
            self.send_json(ws1, "seek", discord_id=DISCORD_ID)  # missing position — will error
            self.assert_error(ws1.receive_json())
            self.assert_not_broadcast(ws2)

    def test_multiple_clients_same_guild_all_receive_broadcast(self, client):
        with patch_bot_seek(status=PlaybackStatusFactory.build(position=99.0)):
            with self.ws_connect(client, GUILD_ID) as ws1:
                with self.ws_connect(client, GUILD_ID) as ws2:
                    with self.ws_connect(client, GUILD_ID) as ws3:
                        self.send_json(ws1, "seek", discord_id=DISCORD_ID, position=99.0)
                        ws1.receive_json()  # ack
                        ws1.receive_json()  # status
                        d2 = ws2.receive_json()
                        d3 = ws3.receive_json()

        self.assert_success(d2, "status")
        self.assert_success(d3, "status")
