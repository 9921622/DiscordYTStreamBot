import discord
from discord.ext import commands

from settings import settings

from utils.event_handler import EventHandler

from bot.bot_generic import DiscordBotGeneric
from bot.bot_voice import DiscordBotVoice
from bot.cogs import generic, voice


class DiscordBot(EventHandler, DiscordBotGeneric, DiscordBotVoice, commands.Bot):
    """https://discordpy.readthedocs.io/en/stable/ext/commands/api.html?highlight=commands%20bot#discord.ext.commands.Bot"""

    def __init__(self, token):
        #
        self._token = token

        #
        intents = discord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="$", intents=intents)

    async def setup_hook(self):
        """ """
        await generic.setup(self)
        await voice.setup(self)

    async def on_ready(self):
        # this happens with listener event on_ready
        # gets called multiple times
        pass

    def run_bot(self):
        self.run(token=self._token)


bot = DiscordBot(token=settings.DISCORD_BOT_TOKEN)
