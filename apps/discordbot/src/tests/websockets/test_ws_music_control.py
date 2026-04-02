import pytest
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from api import app
from api.api_backend_wrapper import VideoAPI
from conftest import client
from tests.utils import (
    make_mock_video_response,
    TestCaseCommand,
    TestCaseWebSocket,
)
from tests.bot_factories import PlaybackStatusFactory


GUILD_ID = 123878273492


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@contextmanager
def patch_bot():
    with patch("api.websockets.commands.music_controls.bot") as mock_bot:
        yield mock_bot


@contextmanager
def patch_video_source(status_code: int = 200):
    with patch.object(VideoAPI, "get_source", new=AsyncMock(return_value=make_mock_video_response(status_code))):
        yield


@contextmanager
def patch_bot_play(status=None, error: Exception | None = None):
    with patch_bot() as mock_bot:
        mock_bot.vc_play = AsyncMock(side_effect=error) if error else AsyncMock()
        if status is not None:
            mock_bot.vc_get_status.return_value = status
        yield mock_bot


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


@contextmanager
def patch_voice_client(vc: MagicMock | None):
    with patch_bot() as mock_bot:
        mock_bot.get_voice_client.return_value = vc
        yield mock_bot


class TestCaseMusic(TestCaseCommand, TestCaseWebSocket):
    pass


# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


class TestStatusCommand(TestCaseMusic):
    def test_status_returns_playback(self, client):
        mock_status = PlaybackStatusFactory.build()
        with patch_bot_status(mock_status):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "status"})
                data = ws.receive_json()

        self.assert_success(data, "status")
        assert data["data"]
        assert data["data"]["playback"] == mock_status.model_dump()

    def test_status_not_broadcast(self, client):
        """Status is read-only — only the sender should receive a response."""
        mock_status = PlaybackStatusFactory.build()
        with patch_bot_status(mock_status):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                ws1.send_json({"type": "status"})
                self.assert_success(ws1.receive_json(), "status")
                self.assert_not_broadcast(ws2)


# ---------------------------------------------------------------------------
# Play
# ---------------------------------------------------------------------------


class TestPlayCommand(TestCaseMusic):
    def test_play_success(self, client):
        status = PlaybackStatusFactory.build(video_id="abc")

        with patch_bot_play(status=status), patch_video_source():
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "play", "video_id": "abc", "offset": 0.0, "volume": 0.5})

                ack = ws.receive_json()
                self.assert_success(ack, "play")
                assert ack["data"]
                assert ack["data"]["video_id"] == "abc"

                broadcast = ws.receive_json()
                self.assert_success(broadcast, "status")

    def test_play_missing_video_id(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            ws.send_json({"type": "play"})
            data = ws.receive_json()

        self.assert_error(data, "video_id")

    def test_play_bot_not_in_channel(self, client):
        with patch_bot_play(error=RuntimeError("not connected")), patch_video_source():
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "play", "video_id": "abc"})
                data = ws.receive_json()

        self.assert_error(data)

    def test_play_source_url_failure(self, client):
        with patch_video_source(status_code=500):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "play", "video_id": "abc"})
                data = ws.receive_json()

        self.assert_error(data)

    def test_play_broadcasts_status_to_guild(self, client):
        status = PlaybackStatusFactory.build(video_id="abc")
        with patch_bot_play(status=status), patch_video_source():
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                ws1.send_json({"type": "play", "video_id": "abc"})
                ws1.receive_json()  # ack
                ws1.receive_json()  # status broadcast to sender
                data = ws2.receive_json()

        self.assert_success(data, "status")


# ---------------------------------------------------------------------------
# Pause
# ---------------------------------------------------------------------------


class TestPauseCommand(TestCaseMusic):
    def test_resume_while_paused(self, client):
        mock_vc = MagicMock()
        state = {"paused": True}
        mock_vc.is_paused.side_effect = lambda: state["paused"]
        mock_vc.is_playing.return_value = False
        mock_vc.resume.side_effect = lambda: state.update({"paused": False})

        with patch_voice_client(mock_vc) as mock_bot:
            mock_bot.vc_get_status.return_value = PlaybackStatusFactory.build(paused=False)
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "pause"})
                ack = ws.receive_json()

        self.assert_success(ack, "pause")
        assert ack["data"]
        assert ack["data"]["paused"] is False

    def test_pause_not_connected(self, client):
        with patch_voice_client(None):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "pause"})
                data = ws.receive_json()

        self.assert_error(data)

    def test_pause_nothing_playing(self, client):
        mock_vc = MagicMock()
        mock_vc.is_paused.return_value = False
        mock_vc.is_playing.return_value = False
        with patch_voice_client(mock_vc):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "pause"})
                data = ws.receive_json()

        self.assert_error(data)


# ---------------------------------------------------------------------------
# Seek
# ---------------------------------------------------------------------------


class TestSeekCommand(TestCaseMusic):
    def test_seek_success(self, client):
        with patch_bot_seek(status=PlaybackStatusFactory.build(position=42.0)):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "seek", "position": 42.0})

                ack = ws.receive_json()
                self.assert_success(ack, "seek")
                assert ack["data"]
                assert ack["data"]["position"] == 42.0

                broadcast = ws.receive_json()
                self.assert_success(broadcast, "status")

    def test_seek_missing_position(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            ws.send_json({"type": "seek"})
            data = ws.receive_json()

        self.assert_error(data, "position")

    def test_seek_nothing_playing(self, client):
        with patch_bot_seek(error=RuntimeError("nothing is playing")):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "seek", "position": 10.0})
                data = ws.receive_json()

        self.assert_error(data)


# ---------------------------------------------------------------------------
# Loop
# ---------------------------------------------------------------------------


class TestLoopCommand(TestCaseMusic):
    def test_loop_toggles_on(self, client):
        with patch_bot_loop(status=PlaybackStatusFactory.build(loop=True)):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "loop"})
                ack = ws.receive_json()
                broadcast = ws.receive_json()

        self.assert_success(ack, "loop")
        assert ack["data"]
        assert ack["data"]["loop"] is True
        self.assert_success(broadcast, "loop")

    def test_loop_toggles_off(self, client):
        with patch_bot_loop(status=PlaybackStatusFactory.build(loop=False)):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "loop"})
                ack = ws.receive_json()
                broadcast = ws.receive_json()

        self.assert_success(ack, "loop")
        assert ack["data"]
        assert ack["data"]["loop"] is False
        self.assert_success(broadcast, "loop")

    def test_loop_nothing_playing(self, client):
        with patch_bot_loop(error=RuntimeError("Nothing is playing")):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "loop"})
                data = ws.receive_json()

        self.assert_error(data)


# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------


class TestVolumeCommand(TestCaseMusic):
    def test_volume_set(self, client):
        with patch_bot_volume(return_value=0.8) as mock_bot:
            mock_bot.vc_get_status.return_value = PlaybackStatusFactory.build(volume=0.8)
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "volume", "level": 0.8})
                ack = ws.receive_json()
                broadcast = ws.receive_json()

        self.assert_success(ack, "volume")
        assert ack["data"]
        assert ack["data"]["volume"] == 0.8
        self.assert_success(broadcast, "volume")

    def test_volume_get(self, client):
        with patch_bot_volume(return_value=0.5) as mock_bot:
            mock_bot.vc_get_status.return_value = PlaybackStatusFactory.build(volume=0.5)
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "volume"})  # no level = get
                ack = ws.receive_json()

        self.assert_success(ack, "volume")
        assert ack["data"]
        assert ack["data"]["volume"] == 0.5

    def test_volume_no_audio_source(self, client):
        with patch_bot_volume(return_value=None):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "volume", "level": 0.8})
                data = ws.receive_json()

        self.assert_error(data)


# ---------------------------------------------------------------------------
# Stop
# ---------------------------------------------------------------------------


class TestStopCommand(TestCaseMusic):
    pass


# ---------------------------------------------------------------------------
# Multi-session isolation
# ---------------------------------------------------------------------------


class TestMultiSession(TestCaseMusic):
    def test_different_guilds_dont_receive_each_others_broadcasts(self, client):
        OTHER_GUILD = 999999
        with patch_bot_seek(status=PlaybackStatusFactory.build()):
            with self.ws_connect(client, GUILD_ID) as ws1:
                with self.ws_connect(client, OTHER_GUILD) as ws2:
                    ws1.send_json({"type": "seek", "position": 30.0})
                    ws1.receive_json()  # ack
                    ws1.receive_json()  # status
                    self.assert_not_broadcast(ws2)

    def test_errors_only_go_to_sender(self, client):
        with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
            ws1.send_json({"type": "seek"})  # missing position — will error
            self.assert_error(ws1.receive_json())
            self.assert_not_broadcast(ws2)

    def test_multiple_clients_same_guild_all_receive_broadcast(self, client):
        with patch_bot_seek(status=PlaybackStatusFactory.build(position=99.0)):
            with self.ws_connect(client, GUILD_ID) as ws1:
                with self.ws_connect(client, GUILD_ID) as ws2:
                    with self.ws_connect(client, GUILD_ID) as ws3:
                        ws1.send_json({"type": "seek", "position": 99.0})
                        ws1.receive_json()  # ack
                        ws1.receive_json()  # status
                        d2 = ws2.receive_json()
                        d3 = ws3.receive_json()

        self.assert_success(d2, "status")
        self.assert_success(d3, "status")
