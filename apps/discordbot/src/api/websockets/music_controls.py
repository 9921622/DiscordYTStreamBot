import httpx
from bot.bot import bot
import api.api_backend_wrapper as backend
from api.websockets.ws_router import WSRouter

ws = WSRouter()


@ws.command(prefix="play", broadcast_status=True)
async def handle_play(websocket, guild_id: int, data: dict):
    """
    {"type": "play", "guild_id": 123, "video_id": "abc", "offset": 0.0, "volume": 0.5}
    """
    video_id = data.get("video_id")
    if not video_id:
        return {"error": "missing 'video_id'"}

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.get(backend.play_url(video_id=video_id))
        if response.status_code != 200:
            return {"error": "failed to resolve source url", "detail": response.json()}
        source_url = response.json()["source_url"]

    try:
        await bot.vc_play(
            guild_id,
            video_id,
            source_url,
            offset=data.get("offset", 0.0),
            volume=data.get("volume", 0.5),
        )
    except RuntimeError:
        return {"error": "bot not connected to a voice channel"}

    return {"type": "play", "video_id": video_id}


@ws.command(prefix="pause", broadcast=True)
async def handle_pause(websocket, guild_id: int, data: dict):
    """
    {"type": "pause", "guild_id": 123}
    Toggles pause/resume.
    """
    vc = bot.get_voice_client(guild_id)
    if not vc:
        return {"error": "not connected to a voice channel"}

    if vc.is_paused():
        vc.resume()
    elif vc.is_playing():
        vc.pause()
    else:
        return {"error": "nothing is playing"}

    return {"type": "pause", "paused": vc.is_paused()}


@ws.command(prefix="stop", broadcast=True)
async def handle_stop(websocket, guild_id: int, data: dict):
    """
    {"type": "stop", "guild_id": 123}
    """
    await bot.vc_stop(guild_id)
    return {"type": "stop"}


@ws.command(prefix="seek", broadcast_status=True)
async def handle_seek(websocket, guild_id: int, data: dict):
    """
    {"type": "seek", "guild_id": 123, "position": 42.0}
    """
    position = data.get("position")
    if position is None:
        return {"error": "missing 'position'"}

    try:
        await bot.vc_seek(guild_id, float(position))
    except RuntimeError:
        return {"error": "nothing is playing"}

    return {"type": "seek", "position": position}


@ws.command(prefix="status", broadcast=True)
async def handle_status(websocket, guild_id: int, data: dict):
    """
    {"type": "status", "guild_id": 123}
    """
    return {"type": "status", "playback": bot.vc_get_status(guild_id)}


@ws.command(prefix="volume", broadcast_status=True)
async def handle_volume(websocket, guild_id: int, data: dict):
    """
    {"type": "volume", "guild_id": 123}             -- get
    {"type": "volume", "guild_id": 123, "level": 0.8} -- set
    """
    level = data.get("level")  # None = get only
    result = await bot.vc_volume(guild_id, level)
    if result is None:
        return {"error": "no active audio source"}

    return {"type": "volume", "volume": result}
