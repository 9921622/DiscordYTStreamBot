from fastapi import APIRouter, Request
from bot.discord_service import discord_service

router = APIRouter(prefix="/music-control", tags=["music-control"])


@router.get("/play")
async def play(request: Request, song_id: str | None = None):
    """Play a song (or resume if no song_id)"""
    await discord_service.send(407313499090321409, f"Play called for song_id: {song_id}")
    # TODO: implement actual play/resume logic
    return {"ok": True}


@router.get("/pause")
async def pause(request: Request):
    """Pause the currently playing song"""
    await discord_service.send(407313499090321409, "Pause called")
    # TODO: implement pause logic
    return {"ok": True}


@router.get("/stop")
async def stop(request: Request):
    """Stop playback completely"""
    await discord_service.send(407313499090321409, "Stop called")
    # TODO: implement stop logic
    return {"ok": True}


@router.get("/seek")
async def seek(request: Request, time: int):
    """Seek to a specific time in the current song (seconds)"""
    await discord_service.send(407313499090321409, f"Seek called: {time}s")
    # TODO: implement seek logic
    return {"ok": True, "time": time}


@router.get("/volume")
async def volume(request: Request, level: int | None = None):
    """
    Get or set volume.
    If level is provided, set volume; otherwise, return current volume.
    """
    await discord_service.send(407313499090321409, f"Volume called: {level}")
    # TODO: implement get/set volume logic
    return {"ok": True, "level": level}
