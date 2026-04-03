import pytest
from contextlib import contextmanager
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from tests.conftest import client
from utils.api_backend_wrapper import QueueAPI, GuildQueueSchema

from tests.utils import (
    make_mock_video_response,
    make_mock_response_wrapper,
    make_mock_httpx_response,
    TestCaseCommand,
    TestCaseWebSocket,
)
from tests.bot_factories import PlaybackStatusFactory
from tests.backend_factories import GuildQueueSchemaFactory

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

GUILD_ID = 123213


@contextmanager
def patch_queue_get(mock_queue: GuildQueueSchema):
    with patch.object(QueueAPI, "get", new=AsyncMock(return_value=make_mock_response_wrapper(200, mock_queue))):
        yield


@contextmanager
def patch_queue_get_error(status: int = 500, detail: dict | None = None):
    with patch.object(QueueAPI, "get", new=AsyncMock(return_value=make_mock_response_wrapper(status, detail or {}))):
        yield


@contextmanager
def patch_queue_add(status: int = 201):
    with patch.object(QueueAPI, "add", new=AsyncMock(return_value=make_mock_response_wrapper(status))):
        yield


@contextmanager
def patch_queue_add_error(status: int = 502, detail: dict | None = None):
    with patch.object(QueueAPI, "add", new=AsyncMock(return_value=make_mock_response_wrapper(status, detail or {}))):
        yield


@contextmanager
def patch_queue_remove(status: int = 204):
    with patch.object(QueueAPI, "remove", new=AsyncMock(return_value=make_mock_response_wrapper(status))):
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
    with patch.object(QueueAPI, "reorder", new=AsyncMock(return_value=make_mock_response_wrapper(status))):
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
    with patch.object(QueueAPI, "clear", new=AsyncMock(return_value=make_mock_response_wrapper(status))):
        yield


@contextmanager
def patch_queue_clear_error(status: int = 500, detail: dict | None = None):
    with patch.object(
        QueueAPI,
        "clear",
        new=AsyncMock(return_value=make_mock_response_wrapper(status, detail or {"detail": "db error"})),
    ):
        yield


class TestQueue(TestCaseCommand, TestCaseWebSocket):
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
    def test_queue_get_returns_queue(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_get(mock_queue):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "queue-get"})
                data = ws.receive_json()

        self.assert_queue_response(data, "queue-get", mock_queue.model_dump())

    def test_queue_get_not_broadcast(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_get(mock_queue):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                ws1.send_json({"type": "queue-get"})
                self.assert_success(ws1.receive_json(), "queue-get")
                self.assert_not_broadcast(ws2)


# ---------------------------------------------------------------------------
# queue-add
# ---------------------------------------------------------------------------


class TestQueueAdd(TestQueue):
    def test_queue_add_success(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_add(), patch_queue_get(mock_queue):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "queue-add", "youtube_id": "abc"})
                data = ws.receive_json()

        self.assert_queue_response(data, "queue-add", mock_queue.model_dump())

    def test_queue_add_missing_youtube_id(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            ws.send_json({"type": "queue-add"})
            data = ws.receive_json()
        self.assert_error(data, "youtube_id")

    def test_queue_add_backend_failure(self, client):
        with patch_queue_add_error(502, {"detail": "upstream error"}):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "queue-add", "youtube_id": "abc"})
                data = ws.receive_json()
        self.assert_error(data)

    def test_queue_add_broadcasts_to_guild(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_add(), patch_queue_get(mock_queue):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                ws1.send_json({"type": "queue-add", "youtube_id": "abc"})
                ws1.receive_json()  # ack
                data = ws2.receive_json()
        self.assert_queue_response(data, "queue-add", mock_queue.model_dump())

    def test_queue_add_error_not_broadcast(self, client):
        with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
            ws1.send_json({"type": "queue-add"})  # missing youtube_id
            self.assert_error(ws1.receive_json(), "youtube_id")
            self.assert_not_broadcast(ws2)


# ---------------------------------------------------------------------------
# queue-remove
# ---------------------------------------------------------------------------


class TestQueueRemove(TestQueue):
    def test_queue_remove_success(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_remove(), patch_queue_get(mock_queue):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "queue-remove", "item_id": 1})
                data = ws.receive_json()

        self.assert_queue_response(data, "queue-remove", mock_queue.model_dump())

    def test_queue_remove_missing_item_id(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            ws.send_json({"type": "queue-remove"})
            data = ws.receive_json()
        self.assert_error(data, "item_id")

    def test_queue_remove_backend_failure(self, client):
        with patch_queue_remove_error(404, {"error": "not found"}):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "queue-remove", "item_id": 99})
                data = ws.receive_json()
        self.assert_error(data)

    def test_queue_remove_broadcasts_to_guild(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_remove(), patch_queue_get(mock_queue):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                ws1.send_json({"type": "queue-remove", "item_id": 1})
                ws1.receive_json()  # ack
                data = ws2.receive_json()
        self.assert_success(data, "queue-remove")


# ---------------------------------------------------------------------------
# queue-reorder
# ---------------------------------------------------------------------------


class TestQueueReorder(TestQueue):
    def test_queue_reorder_success(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_reorder(), patch_queue_get(mock_queue):
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "queue-reorder", "order": [2, 1]})
                data = ws.receive_json()
        self.assert_queue_response(data, "queue-reorder", mock_queue.model_dump())

    def test_queue_reorder_missing_order(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            ws.send_json({"type": "queue-reorder"})
            data = ws.receive_json()
        self.assert_error(data)

    def test_queue_reorder_invalid_order_not_list(self, client):
        with self.ws_connect(client, GUILD_ID) as ws:
            ws.send_json({"type": "queue-reorder", "order": "not-a-list"})
            data = ws.receive_json()
        self.assert_error(data)

    def test_queue_reorder_broadcasts_to_guild(self, client):
        mock_queue = GuildQueueSchemaFactory.build()
        with patch_queue_reorder(), patch_queue_get(mock_queue):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                ws1.send_json({"type": "queue-reorder", "order": [2, 1]})
                ws1.receive_json()  # ack
                data = ws2.receive_json()
        self.assert_success(data, "queue-reorder")


# ---------------------------------------------------------------------------
# queue-clear
# ---------------------------------------------------------------------------


class TestQueueClear(TestQueue):
    def test_queue_clear_success(self, client):
        with patch_queue_clear():
            with self.ws_connect(client, GUILD_ID) as ws:
                ws.send_json({"type": "queue-clear"})
                data = ws.receive_json()

        self.assert_success(data, "queue-clear")
        assert data["data"]
        assert data["data"]["queue"] == []

    def test_queue_clear_error_not_broadcast(self, client):
        with patch_queue_clear_error(500, {"detail": "db error"}):
            with self.ws_connect_pair(client, GUILD_ID) as (ws1, ws2):
                ws1.send_json({"type": "queue-clear"})
                self.assert_error(ws1.receive_json())
                self.assert_not_broadcast(ws2)
