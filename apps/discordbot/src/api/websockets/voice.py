from bot.bot import bot
from api.websockets.ws_router import WSRouter

ws = WSRouter()


@ws.command("users")
async def users(websocket, guild_id: int, data: dict):
    return {"type": "users", "members": bot.vc_get_members(guild_id)}
