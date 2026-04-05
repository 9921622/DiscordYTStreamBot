from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

from ws.ws_commands_router import get_registered_commands
from utils.api_backend_wrapper import QueueAPI, GuildQueueSchema

from tests.test_case import CommandTestCase
from tests.ws.test_case import WebSocketTestCase
from tests.utils.factories import GuildQueueSchemaFactory
from tests.mocks import make_mock_httpx_response
from tests.utils.mocks import make_mock_response_wrapper

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GUILD_ID = 123213
DISCORD_ID = 987654


@contextmanager
def patch_queue_get(mock_queue: GuildQueueSchema):
    with patch.object(
        QueueAPI,
        "get",
        new=AsyncMock(return_value=make_mock_response_wrapper(200, mock_queue)),
    ):
        yield


@contextmanager
def patch_queue_get_error(status: int = 500, detail: dict | None = None):
    with patch.object(
        QueueAPI,
        "get",
        new=AsyncMock(return_value=make_mock_response_wrapper(status, detail or {})),
    ):
        yield


@contextmanager
def patch_queue_add(status: int = 201):
    with patch.object(QueueAPI, "add", new=AsyncMock(return_value=make_mock_response_wrapper(status))):
        yield


@contextmanager
def patch_queue_add_error(status: int = 502, detail: dict | None = None):
    with patch.object(
        QueueAPI,
        "add",
        new=AsyncMock(return_value=make_mock_response_wrapper(status, detail or {})),
    ):
        yield


@contextmanager
def patch_queue_remove(status: int = 204):
    with patch.object(
        QueueAPI,
        "remove",
        new=AsyncMock(return_value=make_mock_response_wrapper(status)),
    ):
        yield


@contextmanager
def patch_queue_remove_error(status: int = 404, detail: dict | None = None):
    with patch.object(
        QueueAPI,
        "remove",
        new=AsyncMock(return_value=make_mock_response_wrapper(status, detail or {"error": "not found"})),
    ):
        yield


@contextmanager
def patch_queue_reorder(status: int = 200):
    with patch.object(
        QueueAPI,
        "reorder",
        new=AsyncMock(return_value=make_mock_response_wrapper(status)),
    ):
        yield


@contextmanager
def patch_queue_reorder_error(status: int = 400, detail: dict | None = None):
    with patch.object(
        QueueAPI,
        "reorder",
        new=AsyncMock(return_value=make_mock_httpx_response(status, detail or {"error": "invalid ids"})),
    ):
        yield


@contextmanager
def patch_queue_clear(status: int = 204):
    with patch.object(
        QueueAPI,
        "clear",
        new=AsyncMock(return_value=make_mock_response_wrapper(status)),
    ):
        yield


@contextmanager
def patch_queue_clear_error(status: int = 500, detail: dict | None = None):
    with patch.object(
        QueueAPI,
        "clear",
        new=AsyncMock(return_value=make_mock_response_wrapper(status, detail or {"detail": "db error"})),
    ):
        yield


class TestQueue(CommandTestCase, WebSocketTestCase):
    """Mixin for queue command tests — combines command helpers with queue assertions."""

    def assert_queue_response(self, data: dict, expected_type: str, expected_queue):
        """Assert a successful queue response with the correct type and queue payload."""
        res = self.to_response(data)

        assert res.success
        assert res.type == expected_type
        assert res.data is not None
        assert res.data.get("queue") == expected_queue


# ---------------------------------------------------------------------------
# queue-get
# ---------------------------------------------------------------------------


class TestQueueGet(TestQueue):
    def test_exists(self):
        assert "queue-get" in get_registered_commands()

    def test_queue_get_returns_queue(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_get(mock_queue):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "queue-get", discord_id=DISCORD_ID)
                data = ws.receive_json()

        self.assert_queue_response(data, "queue-get", mock_queue.model_dump())

    def test_queue_get_not_broadcast(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_get(mock_queue):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                self.send_json(ws1, "queue-get", discord_id=DISCORD_ID)
                self.assert_success(ws1.receive_json(), "queue-get")
                self.assert_not_broadcast(ws2)


# ---------------------------------------------------------------------------
# queue-add
# ---------------------------------------------------------------------------


class TestQueueAdd(TestQueue):
    def test_exists(self):
        assert "queue-add" in get_registered_commands()

    def test_queue_add_success(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_add(), patch_queue_get(mock_queue):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "queue-add", youtube_id="abc", discord_id=DISCORD_ID)
                data = ws.receive_json()

        self.assert_queue_response(data, "queue-add", mock_queue.model_dump())

    def test_queue_add_missing_youtube_id(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            self.send_json(ws, "queue-add", discord_id=DISCORD_ID)
            data = ws.receive_json()
        self.assert_error(data, "youtube_id")

    def test_queue_add_backend_failure(self, client):
        with patch_queue_add_error(502, {"detail": "upstream error"}):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "queue-add", youtube_id="abc", discord_id=DISCORD_ID)
                data = ws.receive_json()
        self.assert_error(data)

    def test_queue_add_broadcasts_to_guild(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_add(), patch_queue_get(mock_queue):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                self.send_json(ws1, "queue-add", youtube_id="abc", discord_id=DISCORD_ID)
                ws1.receive_json()  # ack
                data = ws2.receive_json()
        self.assert_queue_response(data, "queue-add", mock_queue.model_dump())

    def test_queue_add_error_not_broadcast(self, client):
        with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
            self.send_json(ws1, "queue-add", discord_id=DISCORD_ID)  # missing youtube_id
            self.assert_error(ws1.receive_json(), "youtube_id")
            self.assert_not_broadcast(ws2)


# ---------------------------------------------------------------------------
# queue-remove
# ---------------------------------------------------------------------------


class TestQueueRemove(TestQueue):
    def test_exists(self):
        assert "queue-remove" in get_registered_commands()

    def test_queue_remove_success(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_remove(), patch_queue_get(mock_queue):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "queue-remove", item_id=1, discord_id=DISCORD_ID)
                data = ws.receive_json()

        self.assert_queue_response(data, "queue-remove", mock_queue.model_dump())

    def test_queue_remove_missing_item_id(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            self.send_json(ws, "queue-remove", discord_id=DISCORD_ID)
            data = ws.receive_json()
        self.assert_error(data, "item_id")

    def test_queue_remove_backend_failure(self, client):
        with patch_queue_remove_error(404, {"error": "not found"}):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "queue-remove", item_id=99, discord_id=DISCORD_ID)
                data = ws.receive_json()
        self.assert_error(data)

    def test_queue_remove_broadcasts_to_guild(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_remove(), patch_queue_get(mock_queue):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                self.send_json(ws1, "queue-remove", item_id=1, discord_id=DISCORD_ID)
                ws1.receive_json()  # ack
                data = ws2.receive_json()
        self.assert_success(data, "queue-remove")


# ---------------------------------------------------------------------------
# queue-reorder
# ---------------------------------------------------------------------------


class TestQueueReorder(TestQueue):
    def test_exists(self):
        assert "queue-reorder" in get_registered_commands()

    def test_queue_reorder_success(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_reorder(), patch_queue_get(mock_queue):
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "queue-reorder", order=[2, 1], discord_id=DISCORD_ID)
                data = ws.receive_json()
        self.assert_queue_response(data, "queue-reorder", mock_queue.model_dump())

    def test_queue_reorder_missing_order(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            self.send_json(ws, "queue-reorder", discord_id=DISCORD_ID)
            data = ws.receive_json()
        self.assert_error(data)

    def test_queue_reorder_invalid_order_not_list(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            self.send_json(ws, "queue-reorder", order="not-a-list", discord_id=DISCORD_ID)
            data = ws.receive_json()
        self.assert_error(data)

    def test_queue_reorder_broadcasts_to_guild(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_reorder(), patch_queue_get(mock_queue):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                self.send_json(ws1, "queue-reorder", order=[2, 1], discord_id=DISCORD_ID)
                ws1.receive_json()  # ack
                data = ws2.receive_json()
        self.assert_success(data, "queue-reorder")


# ---------------------------------------------------------------------------
# queue-clear
# ---------------------------------------------------------------------------


class TestQueueClear(TestQueue):
    def test_exists(self):
        assert "queue-clear" in get_registered_commands()

    def test_queue_clear_success(self, client):
        with patch_queue_clear():
            with self.ws_connect(client, GUILD_ID) as ws:
                self.send_json(ws, "queue-clear", discord_id=DISCORD_ID)
                data = ws.receive_json()

        self.assert_success(data, "queue-clear")
        assert data["data"]
        assert data["data"]["queue"] == []

    def test_queue_clear_error_not_broadcast(self, client):
        with patch_queue_clear_error(500, {"detail": "db error"}):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                self.send_json(ws1, "queue-clear", discord_id=DISCORD_ID)
                self.assert_error(ws1.receive_json())
                self.assert_not_broadcast(ws2)
