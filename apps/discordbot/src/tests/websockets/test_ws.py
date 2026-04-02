import pytest
from unittest.mock import AsyncMock, patch
from api import app
from conftest import client
from tests.utils import TestCaseWebSocket
from tests.bot_factories import PlaybackStatusFactory


GUILD_ID = 12938027349


class TestWebSocketConnection(TestCaseWebSocket):
    def test_connects_successfully(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            assert ws is not None

    def test_disconnects_cleanly(self, client):
        with self.ws_connect(client, GUILD_ID):
            pass


class TestWebSocketRouting(TestCaseWebSocket):
    def test_missing_type_returns_error(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            ws.send_json({"guild_id": GUILD_ID})
            data = ws.receive_json()
        assert "error" in data
        assert "type" in data["error"]

    def test_unknown_command_returns_error(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            ws.send_json({"type": "not_a_real_command", "guild_id": GUILD_ID})
            data = ws.receive_json()
        assert "error" in data
        assert "not_a_real_command" in data["error"]

    def test_guild_id_injected_from_url(self, client):
        """guild_id in the URL should be used, ignoring any guild_id in the payload."""
        mock_status = PlaybackStatusFactory.build()
        with patch("api.websockets.commands.music_controls.bot") as mock_bot:
            mock_bot.vc_get_status.return_value = mock_status
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "status", "guild_id": 999})
                ws.receive_json()
        mock_bot.vc_get_status.assert_called_with(GUILD_ID)


class TestMultiSession(TestCaseWebSocket):
    def test_different_guilds_dont_receive_each_others_broadcasts(self, client):
        OTHER_GUILD = 999999
        with patch("api.websockets.commands.music_controls.bot") as mock_bot:
            mock_bot.vc_seek = AsyncMock()
            mock_bot.vc_get_status.return_value = PlaybackStatusFactory.build()
            with self.ws_connect(client, GUILD_ID) as ws1:
                with client.websocket_connect(f"/ws/{OTHER_GUILD}") as ws2:
                    ws1.send_json({"type": "seek", "position": 30.0})
                    ws1.receive_json()  # ack
                    ws1.receive_json()  # status
                    self.assert_not_broadcast(ws2)

    def test_errors_only_go_to_sender(self, client):
        with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
            ws1.send_json({"type": "seek"})  # missing position — will error
            data = ws1.receive_json()
            assert "error" in data
            self.assert_not_broadcast(ws2)

    def test_multiple_clients_same_guild_all_receive_broadcast(self, client):
        with patch("api.websockets.commands.music_controls.bot") as mock_bot:
            mock_bot.vc_seek = AsyncMock()
            mock_bot.vc_get_status.return_value = PlaybackStatusFactory.build(position=99.0)
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                with self.ws_connect(client, GUILD_ID) as ws3:
                    ws1.send_json({"type": "seek", "position": 99.0})
                    ws1.receive_json()  # ack
                    ws1.receive_json()  # status
                    d2 = ws2.receive_json()
                    d3 = ws3.receive_json()
        assert d2["type"] == "status"
        assert d3["type"] == "status"
