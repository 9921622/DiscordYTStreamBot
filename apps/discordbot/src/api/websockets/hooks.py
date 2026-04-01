from bot.bot import bot

from .ws_manager import ws_manager
from .ws_hooks import hook


@hook("on_song_start")
async def on_song_start(guild_id: int):
    await ws_manager.send(guild_id, {"type": "song_start"})
    await ws_manager.send(guild_id, {"type": "status", "playback": bot.vc_get_status(guild_id)})


@hook("on_song_end")
async def on_song_end(guild_id: int):
    await ws_manager.send(guild_id, {"type": "song_end"})
