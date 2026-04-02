from bot.bot import bot
from api.websockets.ws_router import WebsocketCommand


class PingCommand(WebsocketCommand):
    prefix = "ping"

    async def handle(self):
        channel_id = int(self.data.pop("channel_id"))
        await bot.send(channel_id, "pong")
        return self.response(ok=True)
