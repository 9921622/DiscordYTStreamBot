import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from api import app
from conftest import client, GUILD_ID, make_mock_status

# ---------------------------------------------------------------------------
# Status
# ---------------------------------------------------------------------------


class TestStatusCommand:
    def test_status_returns_playback(self, client):
        mock_status = make_mock_status()
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_get_status.return_value = mock_status
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "status"})
                data = ws.receive_json()
        assert data["type"] == "status"
        assert data["playback"] == mock_status

    def test_status_not_broadcast(self, client):
        """Status is read-only — only the sender should receive a response."""
        mock_status = make_mock_status()
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_get_status.return_value = mock_status
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "status"})
                    data = ws1.receive_json()
                    assert data["type"] == "status"
                    # ws2 should not receive anything
                    with pytest.raises(Exception):
                        ws2.receive_json(timeout=0.1)


# ---------------------------------------------------------------------------
# Play
# ---------------------------------------------------------------------------


class TestPlayCommand:
    def test_play_success(self, client):
        with (
            patch("api.websockets.music_controls.bot") as mock_bot,
            patch("api.websockets.music_controls.httpx.AsyncClient") as mock_http,
        ):
            mock_bot.vc_play = AsyncMock()
            mock_bot.vc_get_status.return_value = make_mock_status(video_id="abc")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"source_url": "http://example.com/audio"}
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "play", "video_id": "abc", "offset": 0.0, "volume": 0.5})
                ack = ws.receive_json()
                broadcast = ws.receive_json()

        assert ack["type"] == "play"
        assert ack["video_id"] == "abc"
        assert broadcast["type"] == "status"

    def test_play_missing_video_id(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
            ws.send_json({"type": "play"})
            data = ws.receive_json()
        assert "error" in data
        assert "video_id" in data["error"]

    def test_play_bot_not_in_channel(self, client):
        with (
            patch("api.websockets.music_controls.bot") as mock_bot,
            patch("api.websockets.music_controls.httpx.AsyncClient") as mock_http,
        ):
            mock_bot.vc_play = AsyncMock(side_effect=RuntimeError("not connected"))
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"source_url": "http://example.com/audio"}
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "play", "video_id": "abc"})
                data = ws.receive_json()
        assert "error" in data

    def test_play_source_url_failure(self, client):
        with patch("api.websockets.music_controls.httpx.AsyncClient") as mock_http:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.json.return_value = {"detail": "upstream error"}
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "play", "video_id": "abc"})
                data = ws.receive_json()
        assert "error" in data

    def test_play_broadcasts_status_to_guild(self, client):
        """All connected clients in the guild should receive a status update after play."""
        with (
            patch("api.websockets.music_controls.bot") as mock_bot,
            patch("api.websockets.music_controls.httpx.AsyncClient") as mock_http,
        ):
            mock_bot.vc_play = AsyncMock()
            mock_bot.vc_get_status.return_value = make_mock_status(video_id="abc")
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"source_url": "http://example.com/audio"}
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "play", "video_id": "abc"})
                    ws1.receive_json()  # ack
                    ws1.receive_json()  # status broadcast to sender
                    data = ws2.receive_json()  # status broadcast to guild

        assert data["type"] == "status"


# ---------------------------------------------------------------------------
# Pause
# ---------------------------------------------------------------------------


class TestPauseCommand:
    # def test_pause_while_playing(self, client):
    #     mock_vc = MagicMock()
    #     state = {"paused": False}
    #     mock_vc.is_paused.side_effect = lambda: state["paused"]
    #     mock_vc.is_playing.return_value = True
    #     mock_vc.pause.side_effect = lambda: state.update({"paused": True})

    #     with patch("api.websockets.music_controls.bot") as mock_bot:
    #         mock_bot.get_voice_client.return_value = mock_vc
    #         mock_bot.vc_get_status.return_value = make_mock_status(paused=True)
    #         with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
    #             ws.send_json({"type": "pause"})
    #             ack = ws.receive_json()
    #             broadcast = ws.receive_json()

    #     assert ack["type"] == "pause"
    #     assert ack["paused"] is True
    #     assert broadcast["type"] == "status"

    def test_resume_while_paused(self, client):
        mock_vc = MagicMock()
        state = {"paused": True}
        mock_vc.is_paused.side_effect = lambda: state["paused"]
        mock_vc.is_playing.return_value = False
        mock_vc.resume.side_effect = lambda: state.update({"paused": False})

        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.get_voice_client.return_value = mock_vc
            mock_bot.vc_get_status.return_value = make_mock_status(paused=False)
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "pause"})
                ack = ws.receive_json()

        assert ack["paused"] is False

    def test_pause_not_connected(self, client):
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.get_voice_client.return_value = None
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "pause"})
                data = ws.receive_json()

        assert "error" in data

    def test_pause_nothing_playing(self, client):
        mock_vc = MagicMock()
        mock_vc.is_paused.return_value = False
        mock_vc.is_playing.return_value = False
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.get_voice_client.return_value = mock_vc
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "pause"})
                data = ws.receive_json()
        assert "error" in data

    # def test_pause_broadcasts_status_to_guild(self, client):
    #     mock_vc = MagicMock()
    #     state = {"paused": False}
    #     mock_vc.is_paused.side_effect = lambda: state["paused"]
    #     mock_vc.is_playing.return_value = True
    #     mock_vc.pause.side_effect = lambda: state.update({"paused": True})

    #     with patch("api.websockets.music_controls.bot") as mock_bot:
    #         mock_bot.get_voice_client.return_value = mock_vc
    #         mock_bot.vc_get_status.return_value = make_mock_status(paused=True)
    #         with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
    #             with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
    #                 ws1.send_json({"type": "pause"})
    #                 ws1.receive_json()  # ack
    #                 ws1.receive_json()  # status to sender
    #                 data = ws2.receive_json()

    #     assert data["type"] == "status"


# ---------------------------------------------------------------------------
# Seek
# ---------------------------------------------------------------------------


class TestSeekCommand:
    def test_seek_success(self, client):
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_seek = AsyncMock()
            mock_bot.vc_get_status.return_value = make_mock_status(position=42.0)
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "seek", "position": 42.0})
                ack = ws.receive_json()
                broadcast = ws.receive_json()
        assert ack["type"] == "seek"
        assert ack["position"] == 42.0
        assert broadcast["type"] == "status"

    def test_seek_missing_position(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
            ws.send_json({"type": "seek"})
            data = ws.receive_json()
        assert "error" in data
        assert "position" in data["error"]

    def test_seek_nothing_playing(self, client):
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_seek = AsyncMock(side_effect=RuntimeError("nothing is playing"))
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "seek", "position": 10.0})
                data = ws.receive_json()
        assert "error" in data

    # def test_seek_broadcasts_status_to_guild(self, client):
    #     with patch("api.websockets.music_controls.bot") as mock_bot:
    #         mock_bot.vc_seek = AsyncMock()
    #         mock_bot.vc_get_status.return_value = make_mock_status(position=42.0)
    #         with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
    #             with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
    #                 ws1.send_json({"type": "seek", "position": 42.0})
    #                 ws1.receive_json()  # ack
    #                 ws1.receive_json()  # status to sender
    #                 data = ws2.receive_json()
    #     assert data["type"] == "status"
    #     assert data["playback"]["position"] == 42.0


# ---------------------------------------------------------------------------
# Volume
# ---------------------------------------------------------------------------


class TestVolumeCommand:
    def test_volume_set(self, client):
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_volume = AsyncMock(return_value=0.8)
            mock_bot.vc_get_status.return_value = make_mock_status(volume=0.8)
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "volume", "level": 0.8})
                ack = ws.receive_json()
                broadcast = ws.receive_json()
        assert ack["type"] == "volume"
        assert ack["volume"] == 0.8
        assert broadcast["type"] == "status"

    def test_volume_get(self, client):
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_volume = AsyncMock(return_value=0.5)
            mock_bot.vc_get_status.return_value = make_mock_status(volume=0.5)
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "volume"})  # no level = get
                ack = ws.receive_json()
        assert ack["volume"] == 0.5

    def test_volume_no_audio_source(self, client):
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_volume = AsyncMock(return_value=None)
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "volume", "level": 0.8})
                data = ws.receive_json()
        assert "error" in data

    # def test_volume_broadcasts_status_to_guild(self, client):
    #     with patch("api.websockets.music_controls.bot") as mock_bot:
    #         mock_bot.vc_volume = AsyncMock(return_value=0.8)
    #         mock_bot.vc_get_status.return_value = make_mock_status(volume=0.8)
    #         with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
    #             with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
    #                 ws1.send_json({"type": "volume", "level": 0.8})
    #                 ws1.receive_json()  # ack
    #                 ws1.receive_json()  # status to sender
    #                 data = ws2.receive_json()
    #     assert data["type"] == "status"
    #     assert data["playback"]["volume"] == 0.8


# ---------------------------------------------------------------------------
# Stop
# ---------------------------------------------------------------------------


class TestStopCommand:
    # def test_stop_success(self, client):
    #     with patch("api.websockets.music_controls.bot") as mock_bot:
    #         mock_bot.vc_stop = AsyncMock()
    #         mock_bot.vc_get_status.return_value = make_mock_status(playing=False)
    #         with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
    #             ws.send_json({"type": "stop"})
    #             ack = ws.receive_json()
    #             broadcast = ws.receive_json()
    #     assert ack["type"] == "stop"
    #     assert broadcast["type"] == "status"

    # def test_stop_broadcasts_status_to_guild(self, client):
    #     with patch("api.websockets.music_controls.bot") as mock_bot:
    #         mock_bot.vc_stop = AsyncMock()
    #         mock_bot.vc_get_status.return_value = make_mock_status(playing=False)
    #         with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
    #             with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
    #                 ws1.send_json({"type": "stop"})
    #                 ws1.receive_json()  # ack
    #                 ws1.receive_json()  # status to sender
    #                 data = ws2.receive_json()
    #     assert data["type"] == "status"
    #     assert data["playback"]["playing"] is False
    pass


# ---------------------------------------------------------------------------
# Multi-session isolation
# ---------------------------------------------------------------------------


class TestMultiSession:
    def test_different_guilds_dont_receive_each_others_broadcasts(self, client):
        OTHER_GUILD = 999999
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_seek = AsyncMock()
            mock_bot.vc_get_status.return_value = make_mock_status()
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{OTHER_GUILD}") as ws2:
                    ws1.send_json({"type": "seek", "position": 30.0})
                    ws1.receive_json()  # ack
                    ws1.receive_json()  # status
                    with pytest.raises(Exception):
                        ws2.receive_json(timeout=0.1)

    def test_errors_only_go_to_sender(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                ws1.send_json({"type": "seek"})  # missing position — will error
                data = ws1.receive_json()
                assert "error" in data
                with pytest.raises(Exception):
                    ws2.receive_json(timeout=0.1)

    def test_multiple_clients_same_guild_all_receive_broadcast(self, client):
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_seek = AsyncMock()
            mock_bot.vc_get_status.return_value = make_mock_status(position=99.0)
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    with client.websocket_connect(f"/ws/{GUILD_ID}") as ws3:
                        ws1.send_json({"type": "seek", "position": 99.0})
                        ws1.receive_json()  # ack
                        ws1.receive_json()  # status
                        d2 = ws2.receive_json()
                        d3 = ws3.receive_json()
        assert d2["type"] == "status"
        assert d3["type"] == "status"
