import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from api import app
from conftest import client
from tests.utils import GUILD_ID
from tests.bot_factories import PlaybackStatusFactory


class TestWebSocketConnection:
    def test_connects_successfully(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
            assert ws is not None

    def test_disconnects_cleanly(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}"):
            pass  # no exception = clean disconnect


class TestWebSocketRouting:
    def test_missing_type_returns_error(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
            ws.send_json({"guild_id": GUILD_ID})
            data = ws.receive_json()
        assert "error" in data
        assert "type" in data["error"]

    def test_unknown_command_returns_error(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
            ws.send_json({"type": "not_a_real_command", "guild_id": GUILD_ID})
            data = ws.receive_json()
        assert "error" in data
        assert "not_a_real_command" in data["error"]

    def test_guild_id_injected_from_url(self, client):
        """guild_id in the URL should be used, ignoring any guild_id in the payload."""
        mock_status = PlaybackStatusFactory.build()
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_get_status.return_value = mock_status
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "status", "guild_id": 999})  # wrong guild_id
                ws.receive_json()
        mock_bot.vc_get_status.assert_called_with(GUILD_ID)  # URL guild_id wins


class TestMultiSession:
    def test_different_guilds_dont_receive_each_others_broadcasts(self, client):
        OTHER_GUILD = 999999
        with patch("api.websockets.music_controls.bot") as mock_bot:
            mock_bot.vc_seek = AsyncMock()
            mock_bot.vc_get_status.return_value = PlaybackStatusFactory.build()
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
            mock_bot.vc_get_status.return_value = PlaybackStatusFactory.build(position=99.0)
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
