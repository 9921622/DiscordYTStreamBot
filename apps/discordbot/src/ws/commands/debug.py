from bot.bot import bot
from ws.ws_command import WebsocketCommand
from .mixins import DiscordUserMixin


class PingCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "ping"

    async def handle(self):
        channel_id = int(self.data.pop("channel_id"))
        await bot.send(channel_id, "pong")
        return self.response(ok=True)
