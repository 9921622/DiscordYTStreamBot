import pytest
from contextlib import contextmanager


class WebSocketTestCase:

    @contextmanager
    def ws_connect(self, client, guild_id: int):
        with client.websocket_connect(f"/ws/{guild_id}") as ws:
            yield ws

    @contextmanager
    def ws_connect_pair(self, client, guild_id: int):
        with client.websocket_connect(f"/ws/{guild_id}") as ws1:
            with client.websocket_connect(f"/ws/{guild_id}") as ws2:
                yield ws1, ws2

    def assert_not_broadcast(self, ws, timeout: float = 0.1):
        """Assert that a websocket did NOT receive a message (i.e. it was not broadcast to)."""
        with pytest.raises(Exception):
            ws.receive_json(timeout=timeout)
