from bot.bot import bot
from api.websockets.ws_router import WSRouter

ws = WSRouter()


@ws.command(prefix="ping")
async def ping(websocket, guild_id: int, data: dict):
    channel_id = int(data.pop("channel_id"))
    await bot.send(channel_id, "pong")
    return {"ok": True}
