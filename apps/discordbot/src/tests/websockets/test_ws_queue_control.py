import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from api import app
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


def make_mock_response(status_code: int = 200, json_data: dict = None):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = json_data or {}
    mock.raise_for_status = MagicMock()
    return mock


def patch_httpx(get=None, post=None, delete=None, patch_=None):
    """Patches httpx.AsyncClient with configurable responses per method."""
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    if get:
        mock_client.get = AsyncMock(return_value=get)
    if post:
        mock_client.post = AsyncMock(return_value=post)
    if delete:
        mock_client.delete = AsyncMock(return_value=delete)
    if patch_:
        mock_client.patch = AsyncMock(return_value=patch_)
    return patch("httpx.AsyncClient", return_value=mock_client)


# ---------------------------------------------------------------------------
# queue-get
# ---------------------------------------------------------------------------


class TestQueueGet:
    def test_queue_get_returns_queue(self, client):
        with patch_httpx(get=make_mock_response(200, MOCK_QUEUE)):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-get"})
                data = ws.receive_json()
        assert data["type"] == "queue-get"
        assert data["queue"] == MOCK_QUEUE

    def test_queue_get_not_broadcast(self, client):
        """queue-get is read-only — only sender receives it."""
        with patch_httpx(get=make_mock_response(200, MOCK_QUEUE)):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "queue-get"})
                    data = ws1.receive_json()
                    assert data["type"] == "queue-get"
                    with pytest.raises(Exception):
                        ws2.receive_json(timeout=0.1)

    def test_queue_get_backend_error_propagates(self, client):
        mock_response = make_mock_response(500)
        mock_response.raise_for_status.side_effect = Exception("backend error")
        with patch_httpx(get=mock_response):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-get"})
                data = ws.receive_json()
        assert "error" in data


# ---------------------------------------------------------------------------
# queue-add
# ---------------------------------------------------------------------------


class TestQueueAdd:
    def test_queue_add_success(self, client):
        with patch_httpx(
            post=make_mock_response(201),
            get=make_mock_response(200, MOCK_QUEUE),
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
        with patch_httpx(post=make_mock_response(502, {"detail": "upstream error"})):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-add", "youtube_id": "abc"})
                data = ws.receive_json()
        assert "error" in data

    def test_queue_add_broadcasts_to_guild(self, client):
        with patch_httpx(
            post=make_mock_response(201),
            get=make_mock_response(200, MOCK_QUEUE),
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "queue-add", "youtube_id": "abc"})
                    ws1.receive_json()  # ack to sender
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
        with patch_httpx(
            delete=make_mock_response(204),
            get=make_mock_response(200, MOCK_QUEUE),
        ):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-remove", "item_id": 1})
                data = ws.receive_json()
        assert data["type"] == "queue-remove"
        assert data["queue"] == MOCK_QUEUE

    def test_queue_remove_missing_item_id(self, client):
        with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
            ws.send_json({"type": "queue-remove"})
            data = ws.receive_json()
        assert "error" in data
        assert "item_id" in data["error"]

    def test_queue_remove_backend_failure(self, client):
        with patch_httpx(delete=make_mock_response(404, {"error": "not found"})):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-remove", "item_id": 99})
                data = ws.receive_json()
        assert "error" in data

    def test_queue_remove_broadcasts_to_guild(self, client):
        with patch_httpx(
            delete=make_mock_response(204),
            get=make_mock_response(200, MOCK_QUEUE),
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
        with patch_httpx(
            patch_=make_mock_response(200),
            get=make_mock_response(200, MOCK_QUEUE),
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
        with patch_httpx(patch_=make_mock_response(400, {"error": "invalid ids"})):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-reorder", "order": [99, 98]})
                data = ws.receive_json()
        assert "error" in data

    def test_queue_reorder_broadcasts_to_guild(self, client):
        with patch_httpx(
            patch_=make_mock_response(200),
            get=make_mock_response(200, MOCK_QUEUE),
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
        with patch_httpx(delete=make_mock_response(204)):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-clear"})
                data = ws.receive_json()
        assert data["type"] == "queue-clear"
        assert data["queue"] == []

    def test_queue_clear_backend_failure(self, client):
        with patch_httpx(delete=make_mock_response(500)):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws:
                ws.send_json({"type": "queue-clear"})
                data = ws.receive_json()
        assert "error" in data

    def test_queue_clear_broadcasts_to_guild(self, client):
        with patch_httpx(delete=make_mock_response(204)):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "queue-clear"})
                    ws1.receive_json()  # ack
                    data = ws2.receive_json()
        assert data["type"] == "queue-clear"
        assert data["queue"] == []

    def test_queue_clear_error_not_broadcast(self, client):
        with patch_httpx(delete=make_mock_response(500)):
            with client.websocket_connect(f"/ws/{GUILD_ID}") as ws1:
                with client.websocket_connect(f"/ws/{GUILD_ID}") as ws2:
                    ws1.send_json({"type": "queue-clear"})
                    data = ws1.receive_json()
                    assert "error" in data
                    with pytest.raises(Exception):
                        ws2.receive_json(timeout=0.1)
