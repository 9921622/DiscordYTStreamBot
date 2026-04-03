import pytest
import httpx
from unittest.mock import MagicMock
from contextlib import contextmanager


from utils.api_backend_wrapper import ResponseWrapper


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
