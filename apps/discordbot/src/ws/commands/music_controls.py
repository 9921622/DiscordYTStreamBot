import asyncio

from bot.bot import bot
from utils.api_backend_wrapper import VideoAPI, GuildPlaylistAPI
from ws.ws_command import WebsocketCommand, WSCommandFlags
from .mixins import DiscordUserMixin


class BasePlayCommand(DiscordUserMixin, WebsocketCommand):
    """Base class for commands that resolve a playlist item and play it in the voice channel."""

    def get_objects(self):
        super().get_objects()
        self.offset = self.data.get("offset", 0.0)

    async def _get_source_and_play(self, current_item):
        """Fetch the stream source for a playlist item and start playback in the voice channel."""
        rw_source = await VideoAPI.get_source(current_item.video.youtube_id)
        if not rw_source.response.is_success:
            return self.response_error("failed to get video source", detail=rw_source.response.json())

        try:
            await bot.vc_play(
                self.guild_id,
                current_item.video.youtube_id,
                rw_source.data.source_url,
                offset=self.offset,
            )
        except RuntimeError:
            return self.response_error("bot not connected to a voice channel")

        return None


class PlayCommand(BasePlayCommand):
    """Advance to the next item in the queue, or jump to a specific item by item_id."""

    prefix = "play"
    flags = WSCommandFlags.BROADCAST

    def get_objects(self):
        super().get_objects()
        self.item_id = self.data.get("item_id")

    async def handle(self):
        """Route to resume or advance depending on bot and request state."""
        vc = bot.get_voice_client(self.guild_id)
        is_idle = not vc or (not vc.is_playing() and not vc.is_paused())

        if is_idle and self.item_id is None:
            return await self._resume_current()
        else:
            return await self._advance_and_play()

    async def _resume_current(self):
        """
        Resume playback of the playlist's current item without advancing the queue.
        Used when the bot is idle but the playlist already has a current item set.
        """
        rw = await GuildPlaylistAPI.get(guild_id=self.guild_id)
        if not rw.response.is_success:
            return self.response_error("failed to get playlist", detail=rw.response.json())

        current_item = rw.data.current_item
        if current_item is None:
            return self.response_error("no current item to resume")

        error = await self._get_source_and_play(current_item)
        if error:
            return error

        return self.response(playlist=rw.data.model_dump())

    async def _advance_and_play(self):
        """
        Advance the queue to the next item (or jump to a specific item by item_id)
        and start playback. Used for normal skip/next and explicit item selection.
        """
        rw = await GuildPlaylistAPI.next(guild_id=self.guild_id, item_id=self.item_id)
        if not rw.response.is_success:
            return self.response_error("failed to advance queue", detail=rw.response.json())

        current_item = rw.data.current_item
        if current_item is None:
            return self.response_error("playlist has no current item after next()")

        error = await self._get_source_and_play(current_item)
        if error:
            return error

        return self.response(playlist=rw.data.model_dump())


class PlayNowCommand(BasePlayCommand):
    """Immediately play an existing queue item or add a new video and play it."""

    prefix = "play_now"
    flags = WSCommandFlags.BROADCAST

    def get_objects(self):
        super().get_objects()
        self.item_id = self.data.get("item_id")
        self.youtube_id = self.data.get("video_id")

    def get_errors(self):
        if not self.item_id and not self.youtube_id:
            return self.response_error("either 'item_id' or 'video_id' is required")
        return super().get_errors()

    async def handle(self):
        """Jump to an existing item or add a new video and play it immediately."""
        rw = await GuildPlaylistAPI.play_now(
            guild_id=self.guild_id,
            item_id=self.item_id,
            video_id=self.youtube_id,
            discord_id=self.user_id,
        )
        if not rw.response.is_success:
            return self.response_error("failed to play now", detail=rw.response.json())

        current_item = rw.data.current_item
        if current_item is None:
            return self.response_error("playlist has no current item after play_now()")

        error = await self._get_source_and_play(current_item)
        if error:
            return error

        return self.response(playlist=rw.data.model_dump())


class PauseCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "pause"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        vc = bot.get_voice_client(self.guild_id)

        if not vc:
            return self.response_error("not connected to a voice channel")

        if vc.is_paused():
            vc.resume()
        elif vc.is_playing():
            vc.pause()
            await asyncio.sleep(0.1)  # let ffmpeg actually stop
        else:
            return self.response_error("nothing is playing")

        return self.response(paused=vc.is_paused())


class StopCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "stop"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        await bot.vc_stop(self.guild_id)
        return self.response()


class LoopCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "loop"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        try:
            await bot.vc_loop(self.guild_id)
        except RuntimeError as e:
            return self.response_error(str(e))

        status = bot.vc_get_status(self.guild_id)
        return self.response(loop=status.loop)


class SeekCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "seek"
    flags = WSCommandFlags.BROADCAST_STATUS

    def get_objects(self):
        super().get_objects()
        self.position = self.data.get("position")

    def get_errors(self):
        if self.position is None:
            return self.response_error("missing 'position'")
        return super().get_errors()

    async def handle(self):
        try:
            await bot.vc_seek(self.guild_id, float(self.position))
        except RuntimeError:
            return self.response_error("nothing is playing")

        return self.response(position=self.position)


class StatusCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "status"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        return self.response(playback=bot.vc_get_status(self.guild_id).model_dump())


class VolumeCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "volume"
    flags = WSCommandFlags.BROADCAST

    def get_objects(self):
        super().get_objects()
        self.level = self.data.get("level")

    async def handle(self):
        result = await bot.vc_volume(self.guild_id, self.level)

        if result is None:
            return self.response_error("no active audio source")
        return self.response(volume=result)
