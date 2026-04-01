import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from api import app
from api.api_backend_wrapper import QueueAPI
from conftest import client, GUILD_ID, make_mock_status

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_QUEUE = {
    "id": 1,
    "guild": str(GUILD_ID),
    "items": [
        {"id": 1, "video": {"youtube_id": "abc"}, "order": 1, "added_by": None, "added_at": "2026-01-01T00:00:00Z"},
        {"id": 2, "video": {"youtube_id": "def"}, "order": 2, "added_by": None, "added_at": "2026-01-01T00:00:00Z"},
    ],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

EMPTY_QUEUE = {**MOCK_QUEUE, "items": []}


def make_mock_response(status_code: int = 200, json_data=None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data if json_data is not None else {}
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# queue-get
# ---------------------------------------------------------------------------


class TestQueueGet:
    def test_queue_get_returns_queue(self, client):
        with patch.object(QueueAPI, "get", new=AsyncMock(return_value=make_mock_response(200, MOCK_QUEUE))):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-get"})
                data = ws.receive_json()
        assert data["type"] == "queue-get"
        assert data["queue"] == MOCK_QUEUE

    def test_queue_get_not_broadcast(self, client):
        with patch.object(QueueAPI, "get", new=AsyncMock(return_value=make_mock_response(200, MOCK_QUEUE))):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "queue-get"})
                    data = ws1.receive_json()
                    assert data["type"] == "queue-get"
                    with pytest.raises(Exception):
                        ws2.receive_json(timeout=0.1)


# ---------------------------------------------------------------------------
# queue-add
# ---------------------------------------------------------------------------


class TestQueueAdd:
    def test_queue_add_success(self, client):
        with (
            patch.object(QueueAPI, "add", new=AsyncMock(return_value=make_mock_response(201))),
            patch.object(QueueAPI, "get", new=AsyncMock(return_value=make_mock_response(200, MOCK_QUEUE))),
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-add", "youtube_id": "abc"})
                data = ws.receive_json()
        assert data["type"] == "queue-add"
        assert data["queue"] == MOCK_QUEUE

    def test_queue_add_missing_youtube_id(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
            ws.send_json({"type": "queue-add"})
            data = ws.receive_json()
        assert "error" in data
        assert "youtube_id" in data["error"]

    def test_queue_add_backend_failure(self, client):
        with patch.object(
            QueueAPI, "add", new=AsyncMock(return_value=make_mock_response(502, {"detail": "upstream error"}))
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-add", "youtube_id": "abc"})
                data = ws.receive_json()
        assert "error" in data

    def test_queue_add_broadcasts_to_guild(self, client):
        with (
            patch.object(QueueAPI, "add", new=AsyncMock(return_value=make_mock_response(201))),
            patch.object(QueueAPI, "get", new=AsyncMock(return_value=make_mock_response(200, MOCK_QUEUE))),
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "queue-add", "youtube_id": "abc"})
                    ws1.receive_json()  # ack
                    data = ws2.receive_json()
        assert data["type"] == "queue-add"
        assert data["queue"] == MOCK_QUEUE

    def test_queue_add_error_not_broadcast(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                ws1.send_json({"type": "queue-add"})  # missing youtube_id
                data = ws1.receive_json()
                assert "error" in data
                with pytest.raises(Exception):
                    ws2.receive_json(timeout=0.1)


# ---------------------------------------------------------------------------
# queue-remove
# ---------------------------------------------------------------------------


class TestQueueRemove:
    def test_queue_remove_success(self, client):
        with (
            patch.object(QueueAPI, "remove", new=AsyncMock(return_value=make_mock_response(204))),
            patch.object(QueueAPI, "get", new=AsyncMock(return_value=make_mock_response(200, MOCK_QUEUE))),
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-remove", "item_id": 1})
                data = ws.receive_json()

        assert "error" not in data
        assert data["type"] == "queue-remove"
        assert data["queue"] == MOCK_QUEUE

    def test_queue_remove_missing_item_id(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
            ws.send_json({"type": "queue-remove"})
            data = ws.receive_json()
        assert "error" in data
        assert "item_id" in data["error"]

    def test_queue_remove_backend_failure(self, client):
        with patch.object(
            QueueAPI, "remove", new=AsyncMock(return_value=make_mock_response(404, {"error": "not found"}))
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-remove", "item_id": 99})
                data = ws.receive_json()
        assert "error" in data

    def test_queue_remove_broadcasts_to_guild(self, client):
        with (
            patch.object(QueueAPI, "remove", new=AsyncMock(return_value=make_mock_response(204))),
            patch.object(QueueAPI, "get", new=AsyncMock(return_value=make_mock_response(200, MOCK_QUEUE))),
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "queue-remove", "item_id": 1})
                    ws1.receive_json()  # ack
                    data = ws2.receive_json()
        assert data["type"] == "queue-remove"


# ---------------------------------------------------------------------------
# queue-reorder
# ---------------------------------------------------------------------------


class TestQueueReorder:
    def test_queue_reorder_success(self, client):
        with (
            patch.object(QueueAPI, "reorder", new=AsyncMock(return_value=make_mock_response(200))),
            patch.object(QueueAPI, "get", new=AsyncMock(return_value=make_mock_response(200, MOCK_QUEUE))),
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-reorder", "order": [2, 1]})
                data = ws.receive_json()
        assert data["type"] == "queue-reorder"
        assert data["queue"] == MOCK_QUEUE

    def test_queue_reorder_missing_order(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
            ws.send_json({"type": "queue-reorder"})
            data = ws.receive_json()
        assert "error" in data

    def test_queue_reorder_invalid_order_not_list(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
            ws.send_json({"type": "queue-reorder", "order": "not-a-list"})
            data = ws.receive_json()
        assert "error" in data

    def test_queue_reorder_backend_failure(self, client):
        with patch.object(
            QueueAPI, "reorder", new=AsyncMock(return_value=make_mock_response(400, {"error": "invalid ids"}))
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-reorder", "order": [99, 98]})
                data = ws.receive_json()
        assert "error" in data

    def test_queue_reorder_broadcasts_to_guild(self, client):
        with (
            patch.object(QueueAPI, "reorder", new=AsyncMock(return_value=make_mock_response(200))),
            patch.object(QueueAPI, "get", new=AsyncMock(return_value=make_mock_response(200, MOCK_QUEUE))),
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "queue-reorder", "order": [2, 1]})
                    ws1.receive_json()  # ack
                    data = ws2.receive_json()
        assert data["type"] == "queue-reorder"


# ---------------------------------------------------------------------------
# queue-clear
# ---------------------------------------------------------------------------


class TestQueueClear:
    def test_queue_clear_success(self, client):
        with patch.object(QueueAPI, "clear", new=AsyncMock(return_value=make_mock_response(204))):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-clear"})
                data = ws.receive_json()
        assert data["type"] == "queue-clear"
        assert data["queue"] == []

    def test_queue_clear_backend_failure(self, client):
        with patch.object(
            QueueAPI, "clear", new=AsyncMock(return_value=make_mock_response(500, {"detail": "db error"}))
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-clear"})
                data = ws.receive_json()
        assert "error" in data

    def test_queue_clear_broadcasts_to_guild(self, client):
        with patch.object(QueueAPI, "clear", new=AsyncMock(return_value=make_mock_response(204))):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "queue-clear"})
                    ws1.receive_json()  # ack
                    data = ws2.receive_json()
        assert data["type"] == "queue-clear"
        assert data["queue"] == []

    def test_queue_clear_error_not_broadcast(self, client):
        with patch.object(
            QueueAPI, "clear", new=AsyncMock(return_value=make_mock_response(500, {"detail": "db error"}))
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "queue-clear"})
                    data = ws1.receive_json()
                    assert "error" in data
                    with pytest.raises(Exception):
                        ws2.receive_json(timeout=0.1)
