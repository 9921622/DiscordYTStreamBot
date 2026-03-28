from fastapi import APIRouter, Request
from bot.bot import bot

router = APIRouter(prefix="/voice", tags=["voice"])


@router.get("/connect", name="voice-connect")
async def connect(request: Request, channel_id: int):
    """connect to a voice channel given an id"""
    voice_channel = bot.get_channel(channel_id)
    await bot.vc_connect(voice_channel)
    return {"ok": True}


@router.get("/disconnect", name="voice-disconnect")
async def disconnect(request: Request, guild_id: int):
    """disconnect from a guild"""
    await bot.vc_disconnect(guild_id)
    return {"ok": True}
