from bot.bot import bot

from api.api_backend_wrapper import QueueAPI, VideoAPI

from .ws_manager import ws_manager
from bot.bot_hooks import hooks


@hooks("on_disconnect")
async def on_disconnect(guild_id: int):
    await ws_manager.disconnect_all(guild_id)


@hooks("on_voice_connect", "on_voice_disconnect")
async def on_voice(guild_id: int):
    await ws_manager.send(guild_id, {"type": "users", "members": bot.vc_get_members(guild_id).model_dump()})


@hooks("on_song_start")
async def on_song_start(guild_id: int):
    await ws_manager.send(guild_id, {"type": "song_start"})
    await ws_manager.send(guild_id, {"type": "status", "playback": bot.vc_get_status(guild_id).model_dump()})


@hooks("on_song_end")
async def on_song_end(guild_id: int):
    queue_response = await QueueAPI.get(guild_id)
    queue_data = queue_response.json()
    items = queue_data.get("items", [])

    await ws_manager.send(guild_id, {"type": "song_end", "next_song": bool(items)})
    if not items:
        return

    next_item = items[0]
    video = next_item.get("video", {})

    item_id = next_item.get("id")
    youtube_id = video.get("youtube_id")

    if not youtube_id:
        return

    source_response = await VideoAPI.get_source(youtube_id)
    if source_response.response.status_code != 200:
        return

    source_url = source_response.data.source_url
    if not source_url:
        return

    vc_status = bot.vc_get_status(guild_id)
    vc = bot.get_voice_client(guild_id)

    await QueueAPI.remove(guild_id, item_id)
    await ws_manager.send(guild_id, {"type": "play", "video_id": youtube_id})
    await ws_manager.send(guild_id, {"type": "queue-remove", "queue": (await QueueAPI.get(guild_id)).json()})

    await bot.vc_play(guild_id, youtube_id, source_url)
