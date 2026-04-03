from unittest.mock import MagicMock
from utils.api_backend_wrapper import ResponseWrapper

from tests.mocks import make_mock_httpx_response


def make_mock_video_response(status_code=200, source_url="http://example.com/audio") -> MagicMock:
    """mocks the video response from backend.
    VideoAPI.get_source()
    """
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = {"source_url": source_url} if status_code == 200 else {"detail": "upstream error"}
    return mock


def make_mock_response_wrapper(status_code: int, data: object = None) -> ResponseWrapper:
    response = make_mock_httpx_response(status_code, data)
    return ResponseWrapper(response=response, data=data)
