from bot.bot import bot
from api.api_backend_wrapper import VideoAPI
from api.websockets.ws_router import WSRouter

ws = WSRouter()


@ws.command(prefix="play", broadcast_status=True)
async def handle_play(websocket, guild_id: int, data: dict):
    video_id = data.get("video_id")
    if not video_id:
        return {"error": "missing 'video_id'"}

    rw = await VideoAPI.get_source(video_id)
    if not rw.response.is_success:
        return {"error": "failed to resolve source url", "detail": rw.response.json()}

    try:
        await bot.vc_play(
            guild_id,
            video_id,
            rw.data.source_url,
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


@ws.command(prefix="loop", broadcast=True)
async def handle_loop(websocket, guild_id: int, data: dict):
    """
    {"type": "loop", "guild_id": 123}
    """
    await bot.vc_loop(guild_id)
    status = bot.vc_get_status(guild_id)
    return {"type": "loop", "loop": status.loop}


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
    return {"type": "status", "playback": bot.vc_get_status(guild_id).model_dump()}


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
