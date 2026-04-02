import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch
from contextlib import contextmanager

from api.api_backend_wrapper import ResponseWrapper


def make_mock_video_response(status_code=200, source_url="http://example.com/audio") -> MagicMock:
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = {"source_url": source_url} if status_code == 200 else {"detail": "upstream error"}
    return mock


def make_mock_httpx_response(status_code: int, json_data: dict = {}) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.is_success = status_code < 400
    response.json.return_value = json_data
    return response


def make_mock_response_wrapper(status_code: int, data: object = None) -> ResponseWrapper:
    response = make_mock_httpx_response(status_code, data)
    return ResponseWrapper(response=response, data=data)


class TestCaseWebSocket:

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


class TestCaseCommand:
    """Abstract base class providing shared assertion helpers for command tests."""

    def assert_success(self, data: dict, expected_type: str):
        """Assert a successful websocket response with the correct type."""
        assert "error" not in data, f"Unexpected error: {data.get('error')}"
        assert data["type"] == expected_type

    def assert_error(self, data: dict, key: str | None = None):
        """Assert an error response, optionally checking the error mentions a specific key."""
        assert "error" in data
        if key:
            assert key in data["error"]

    def assert_queue_response(self, data: dict, expected_type: str, expected_queue):
        """Assert a successful queue response with the correct type and queue payload."""
        self.assert_success(data, expected_type)
        assert data["queue"] == expected_queue
