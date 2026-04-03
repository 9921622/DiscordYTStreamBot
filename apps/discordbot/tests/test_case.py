from ws.models import WSResponse


class TestCaseCommand:
    """Abstract base class providing shared assertion helpers for command tests."""

    def to_response(self, data: dict | WSResponse) -> WSResponse:
        if isinstance(data, WSResponse):
            return data
        return WSResponse.model_validate(data)

    def assert_success(self, data: dict, expected_type: str):
        """Assert a successful websocket response with the correct type."""
        res = self.to_response(data)

        assert res.success, f"Unexpected error: {res.error}"
        assert res.type == expected_type

    def assert_error(self, data: dict, key: str | None = None):
        """Assert an error response, optionally checking the error mentions a specific key."""
        res = self.to_response(data)

        assert not res.success
        assert res.error is not None

        if key:
            # check inside message or detail
            msg = res.error.get("message", "")
            detail = str(res.error.get("detail", ""))
            assert key in msg or key in detail
