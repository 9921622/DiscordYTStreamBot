from unittest.mock import AsyncMock, patch

from ws.ws_command import WebsocketCommand, WSCommandFlags
from tests.ws.test_case import WebSocketTestCase
from tests.bot.factories import PlaybackStatusFactory

GUILD_ID = 12938027349


class EchoCommand(WebsocketCommand):
    prefix = "debug_echo"
    flags = WSCommandFlags.NONE

    async def handle(self):
        return self.response(echo=self.data)


class EchoCommandBroadcast(WebsocketCommand):
    prefix = "debug_echo_broadcast"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        return self.response(echo=self.data)


class EchoCommandBroadcastStatus(WebsocketCommand):
    prefix = "debug_echo_status"
    flags = WSCommandFlags.BROADCAST_STATUS

    async def handle(self):
        return self.response(echo=self.data)


class TestWebSocketConnection(WebSocketTestCase):
    def test_connects_successfully(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            assert ws is not None

    def test_disconnects_cleanly(self, client):
        with self.ws_connect(client, GUILD_ID):
            pass


class TestWebSocketRouting(WebSocketTestCase):
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
        with self.ws_connect(client, GUILD_ID) as ws:
            ws.send_json({"type": "debug_echo", "guild_id": 999})
            data = ws.receive_json()
        assert data["data"]["echo"]["guild_id"] == GUILD_ID


class TestMultiSession(WebSocketTestCase):
    def test_different_guilds_dont_receive_each_others_broadcasts(self, client):
        OTHER_GUILD = 999999
        with self.ws_connect(client, GUILD_ID) as ws1:
            with client.websocket_connect(f"/ws/{OTHER_GUILD}") as ws2:
                ws1.send_json({"type": "debug_echo_broadcast"})
                ws1.receive_json()
                self.assert_not_broadcast(ws2)

    def test_errors_only_go_to_sender(self, client):
        with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
            ws1.send_json({"type": "seek", "discord_id": "5"})  # missing position — will error
            data = ws1.receive_json()
            assert "error" in data
            self.assert_not_broadcast(ws2)

    def test_multiple_clients_same_guild_all_receive_broadcast(self, client):
        with patch("ws.commands.music_controls.bot") as mock_bot:
            mock_bot.vc_seek = AsyncMock()
            mock_bot.vc_get_status.return_value = PlaybackStatusFactory.build(position=99.0)
