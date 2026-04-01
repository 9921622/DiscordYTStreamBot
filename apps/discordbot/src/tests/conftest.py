import pytest
from api.api_backend_wrapper import VideoAPI
from fastapi.testclient import TestClient
from contextlib import asynccontextmanager
from api import app
from unittest.mock import AsyncMock, MagicMock, patch


# TODO: PUT THESE MOCKS IN A UTILS FILE


@pytest.fixture
def client():
    return TestClient(app)


GUILD_ID = 123456


def make_mock_video_response(status_code=200, source_url="http://example.com/audio"):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = {"source_url": source_url} if status_code == 200 else {"detail": "upstream error"}
    return mock


def make_mock_status(
    playing=True,
    paused=False,
    video_id="test_video",
    position=10.0,
    volume=0.5,
    loop=False,
):
    """to fake playback mock return for bot.bot_voice.DiscordBotVoice.vc_get_status"""
    return {
        "playing": playing,
        "paused": paused,
        "video_id": video_id,
        "position": position,
        "volume": volume,
        "loop": loop,
    }
