from fastapi import APIRouter, Request
from bot.discord_service import discord_service

router = APIRouter(prefix="/misc", tags=["Misc"])


@router.get("/ping", name="misc-ping")
async def ping(request: Request):
    await discord_service.send(407313499090321409, "Hello 👀")
    return {"ok": True}
