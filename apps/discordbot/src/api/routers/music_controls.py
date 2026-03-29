from fastapi import APIRouter, Request, HTTPException
import httpx

import api.api_backend_wrapper as backend
from bot.bot import bot

router = APIRouter(prefix="/music-control", tags=["music-control"])


@router.get("/play", name="mc-play")
async def play(request: Request, guild_id: int, video_id: str, offset: float = 0.0, volume: float = 0.5):
    """Play a song by video ID"""
    async with httpx.AsyncClient() as client:
        response = await client.get(backend.play_url(video_id=video_id))
        if response.status_code != 200:
            raise HTTPException(status_code=502, detail="Failed to fetch source URL")
        source_url = response.json()["source_url"]

    try:
        await bot.vc_play(guild_id, source_url, offset=offset, volume=volume)
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail="Bot not connected to vc")

    return {"ok": True}


@router.get("/pause", name="mc-pause")
async def pause(request: Request, guild_id: int):
    """Toggle pause/resume"""
    vc = bot.get_voice_client(guild_id)
    if not vc:
        raise HTTPException(status_code=400, detail="Not connected to a voice channel")

    if vc.is_paused():
        vc.resume()
    elif vc.is_playing():
        vc.pause()
    else:
        raise HTTPException(status_code=400, detail="Nothing is playing")

    return {"ok": True, "paused": vc.is_paused()}


@router.get("/stop", name="mc-stop")
async def stop(request: Request, guild_id: int):
    """Stop playback completely"""
    vc = bot.get_voice_client(guild_id)
    if not vc:
        raise HTTPException(status_code=400, detail="Not connected")
    vc.stop()
    bot._delete_playback(guild_id)
    return {"ok": True}


@router.get("/seek", name="mc-seek")
async def seek(request: Request, guild_id: int, time: float):
    """Seek to a specific time in the current song (seconds)"""
    await bot.vc_seek(guild_id, time)
    return {"ok": True, "position": time}


@router.get("/status", name="mc-status")
async def status(request: Request, guild_id: int):
    """Get current playback position and state"""
    return bot.vc_get_status(guild_id)


@router.get("/volume", name="mc-volume")
async def volume(request: Request, guild_id: int, level: float | None = None):
    """Get or set volume (0.0–1.0)"""
    result = await bot.vc_volume(guild_id, level)
    if result is None:
        raise HTTPException(status_code=400, detail="No active audio source")
    return {"ok": True, "volume": result}
