from bot.bot import bot
from api.websockets.ws_router import WSRouter

ws = WSRouter()


@ws.command("connect")
async def handle_connect(websocket, guild_id: int, data: dict):
    """
    {"type": "connect", "guild_id": 123, "channel_id": 456}
    """
    channel_id = data.get("channel_id")
    if not channel_id:
        return {"error": "missing 'channel_id'"}

    voice_channel = bot.get_channel(int(channel_id))
    if not voice_channel:
        return {"error": f"channel {channel_id} not found"}

    await bot.vc_connect(voice_channel)
    return {"ok": True, "type": "connect"}


@ws.command("disconnect")
async def handle_disconnect(websocket, guild_id: int, data: dict):
    """
    {"type": "disconnect", "guild_id": 123}
    """
    await bot.vc_disconnect(guild_id)
    return {"ok": True, "type": "disconnect"}
