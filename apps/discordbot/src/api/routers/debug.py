from fastapi import APIRouter, Request
from bot.bot import bot

router = APIRouter(prefix="/debug", tags=["debug"])


@router.get("/voice-clients", name="debug-voice-clients")
async def play(request: Request):
    await bot.wait_until_ready()
    return {"voice_clients": len(bot.voice_clients)}


@router.get("/playbacks", name="debug-playbacks")
async def play(request: Request):
    await bot.wait_until_ready()
    return {"playbacks": len(bot._playback)}
