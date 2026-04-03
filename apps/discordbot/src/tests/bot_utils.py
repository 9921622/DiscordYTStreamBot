import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

import discord

from utils.event_handler import EventHandler
from bot.bot_generic import DiscordBotGeneric
from bot.bot_voice import DiscordBotVoice


class FakeBot(EventHandler, DiscordBotGeneric, DiscordBotVoice):

    def __init__(self):
        super().__init__()

        # discord.commands.Bot functions that are used
        self.voice_clients = []
        self.loop = asyncio.get_event_loop()

    def get_guild(self, guild_id):
        return None

    async def wait_until_ready(self):
        pass

    def _inject_vc(self, vc):
        self.voice_clients = [vc]


def make_vc(guild_id=123, playing=False, paused=False):
    vc = MagicMock(spec=discord.VoiceClient)
    vc.guild.id = guild_id
    vc.guild__id = guild_id
    vc.is_connected.return_value = True
    vc.is_playing.return_value = playing
    vc.is_paused.return_value = paused
    vc.stop = MagicMock()
    vc.play = MagicMock()
    vc.disconnect = AsyncMock()
    source = MagicMock(spec=discord.PCMVolumeTransformer)
    source.volume = 0.5 * 0.125
    vc.source = source
    return vc


# ── Fixtures ──────────────────────────────────────────────────────────────────


@pytest.fixture
def bot():
    return FakeBot()


@pytest.fixture
def guild_id():
    return 123


@pytest.fixture
def vc(guild_id):
    return make_vc(guild_id)
