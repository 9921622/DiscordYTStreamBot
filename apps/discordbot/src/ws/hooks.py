from bot.bot import bot
from utils.api_backend_wrapper import GuildPlaylistAPI, VideoAPI, GuildPlaylistSchema, GuildPlaylistItemSchema
from ws.ws_hook import WebsocketHook
from ws.models import WSResponse
from ws.ws_manager import ws_manager


class OnDisconnect(WebsocketHook):
    """event for when bot disconnects"""

    events = ["on_disconnect"]

    async def handle(self):
        await self.send(WSResponse(type="on_disconnect", success=True))
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
                type="song_start", success=True, data={"playback": bot.vc_get_status(self.guild_id).model_dump()}
            )
        )


class OnSongEnd(WebsocketHook):
    """Will send to every websocket that song has ended"""

    events = ["on_song_end"]

    async def handle(self):
        next_item = await self._advance_playlist()
        has_next = next_item is not None

        await self.send(
            WSResponse(
                type="song_end",
                success=True,
                data={"next_song": has_next},
            )
        )

        if has_next:
            await self._play_current(next_item)

    async def _advance_playlist(self) -> GuildPlaylistItemSchema | None:
        """Advance playlist and return next item (not full playlist anymore)."""
        response = await GuildPlaylistAPI.next(self.guild_id)
        if not response.response.is_success or not response.data:
            return None
        return response.data.current_item

    async def _play_current(self, item: GuildPlaylistItemSchema):
        """Play a specific playlist item."""

        youtube_id = item.video.youtube_id

        source_response = await VideoAPI.get_source(youtube_id)
        if not source_response.response.is_success or not source_response.data.source_url:
            return

        # Fetch updated playlist for queue sync
        playlist_response = await GuildPlaylistAPI.get(self.guild_id)
        playlist = playlist_response.data if playlist_response.response.is_success else None

        if playlist:
            await self.send(
                WSResponse(
                    type="play",
                    success=True,
                    data={"video_id": youtube_id, "playlist": playlist.model_dump() if playlist else None},
                )
            )

        await self.send(
            WSResponse(
                type="play",
                success=True,
                data={"video_id": youtube_id},
            )
        )

        await bot.vc_play(
            self.guild_id,
            youtube_id,
            source_response.data.source_url,
        )
