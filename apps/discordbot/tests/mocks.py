import httpx
from unittest.mock import MagicMock


def make_mock_httpx_response(status_code: int, json_data: dict = {}) -> MagicMock:
    response = MagicMock(spec=httpx.Response)
    response.status_code = status_code
    response.is_success = status_code < 400
    response.json.return_value = json_data
    return response
