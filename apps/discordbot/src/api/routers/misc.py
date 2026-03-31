from fastapi import APIRouter, Request
from bot.bot import bot

router = APIRouter(prefix="/misc", tags=["Misc"])


@router.get("/ping", name="misc-ping")
async def ping(request: Request, channel_id: int):
    await bot.send(channel_id, "Hello 👀")
    return {"ok": True}
