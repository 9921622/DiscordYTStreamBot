from bot.bot import bot
from utils.api_backend_wrapper import QueueAPI, VideoAPI, GuildQueueItemSchema
from ws.ws_hook import WebsocketHook
from ws.models import WSResponse
from ws.ws_manager import ws_manager


class OnDisconnect(WebsocketHook):
    """event for when bot disconnects"""

    events = ["on_disconnect"]

    async def handle(self):
        await ws_manager.disconnect_all(self.guild_id)


class OnVoice(WebsocketHook):
    """general event for when user joins or disconnects"""

    events = ["on_voice_connect", "on_voice_disconnect"]

    async def handle(self):
        await self.send(
            WSResponse(
                type="users",
                success=True,
                data={
                    "members": bot.vc_get_members(self.guild_id).model_dump(),
                },
            )
        )


class OnVoiceDisconnect(WebsocketHook):
    """event for when user disconnects"""

    events = ["on_voice_disconnect"]

    async def handle(self):
        # validate all websocket connects with the current members
        pass


class OnSongStart(WebsocketHook):
    events = ["on_song_start"]

    async def handle(self):
        await self.send(
            WSResponse(
                type="song_start",
                success=True,
            )
        )
        await self.send(
            WSResponse(type="status", success=True, data={"playback": bot.vc_get_status(self.guild_id).model_dump()})
        )


class OnSongEnd(WebsocketHook):
    events = ["on_song_end"]

    async def handle(self):
        items = await self._get_queue()
        await self.send(WSResponse(type="song_end", success=True, data={"next_song": bool(items)}))
        if items:
            await self._play_next(items[0])

    async def _get_queue(self) -> list[GuildQueueItemSchema]:
        response = await QueueAPI.get(self.guild_id)
        return response.data.items if response.data else []

    async def _play_next(self, item: GuildQueueItemSchema):
        youtube_id = item.video.youtube_id

        source_response = await VideoAPI.get_source(youtube_id)
        if not source_response.response.is_success:
            return

        source_url = source_response.data.source_url
        if not source_url:
            return

        await QueueAPI.remove(self.guild_id, item.id)
        await self.send(WSResponse(type="play", success=True, data={"video_id": youtube_id}))

        queue_response = await QueueAPI.get(self.guild_id)
        await self.send(
            WSResponse(
                type="queue-remove",
                success=True,
                data={"queue": queue_response.data.model_dump() if queue_response.data else {}},
            )
        )
        await bot.vc_play(self.guild_id, youtube_id, source_url)
