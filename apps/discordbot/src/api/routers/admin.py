from fastapi import APIRouter, Request
from api.decorators import admin_only
from bot.bot import bot

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/leave", name="admin-leave")
@admin_only()
async def leave(request: Request):
    return {"ok": True}


@router.get("/chat", name="admin-chat")
@admin_only()
async def chat(request: Request):
    return {"ok": True}


@router.get("/guilds", name="admin-guilds")
@admin_only()
async def guilds(request: Request):
    """returns all servers bot is in"""
    return {"ok": True}


@router.get("/channels", name="admin-channels")
@admin_only()
async def channels(request: Request, guild_id: int | None):
    """returns all channels bot is in given server"""
    return {"ok": True}
