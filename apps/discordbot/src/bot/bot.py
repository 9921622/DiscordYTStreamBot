import nextcord
from nextcord.ext import commands

from bot.cogs import generic, voice

from settings import settings


class DiscordBot(commands.Bot):
    """https://discordpy.readthedocs.io/en/stable/ext/commands/api.html?highlight=commands%20bot#discord.ext.commands.Bot"""

    def __init__(self, token):
        #
        self._token = token

        #
        intents = nextcord.Intents.default()
        intents.message_content = True
        super().__init__(command_prefix="$", intents=intents)

    async def setup_hook(self):
        """called before the websocket connection
        https://discordpy.readthedocs.io/en/latest/api.html?highlight=setup_hook#discord.Client.setup_hook
        """
        await generic.setup(self)
        await voice.setup(self)

    async def on_ready(self):
        # this happens with listener event on_ready
        # gets called multiple times
        pass

    def run_bot(self):
        self.run(token=self._token)


bot = DiscordBot(token=settings.DISCORD_TOKEN)
