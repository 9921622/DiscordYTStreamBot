import pytest
from fastapi.testclient import TestClient
from api import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_ws_manager():
    """ws_manager as singleton. reset for tests"""
    from ws.ws_manager import ws_manager

    ws_manager._connections.clear()
    yield
    ws_manager._connections.clear()
