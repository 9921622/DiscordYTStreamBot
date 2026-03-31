import pytest
from fastapi.testclient import TestClient
from api import app


@pytest.fixture
def client():
    return TestClient(app)


GUILD_ID = 123456


def make_mock_status(
    playing=True,
    paused=False,
    video_id="test_video",
    position=10.0,
    volume=0.5,
):
    """to fake playback mock return for bot.bot_voice.DiscordBotVoice.vc_get_status"""
    return {
        "playing": playing,
        "paused": paused,
        "video_id": video_id,
        "position": position,
        "volume": volume,
    }
