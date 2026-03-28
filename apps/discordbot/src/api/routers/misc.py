from fastapi import APIRouter, Request
from bot.bot import bot

router = APIRouter(prefix="/misc", tags=["Misc"])


@router.get("/ping", name="misc-ping")
async def ping(request: Request):
    await bot.send(407313499090321409, "Hello 👀")
    return {"ok": True}
