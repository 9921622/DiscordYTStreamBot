from bot.bot import bot
from utils.api_backend_wrapper import VideoAPI
from ws.ws_command import WebsocketCommand, WSCommandFlags
from .mixins import DiscordUserMixin


class PlayCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "play"
    flags = WSCommandFlags.BROADCAST_STATUS

    def get_objects(self):
        super().get_objects()
        self.video_id = self.data.get("video_id")
        self.offset = self.data.get("offset", 0.0)
        self.volume = self.data.get("volume", 0.5)

    def get_errors(self):
        if not self.video_id:
            return self.response_error("missing 'video_id'")
        return super().get_errors()

    async def handle(self):
        rw = await VideoAPI.get_source(self.video_id)

        if not rw.response.is_success:
            return self.response_error("bot not connected to a voice channel", detail=rw.response.json())

        try:
            await bot.vc_play(
                self.guild_id,
                self.video_id,
                rw.data.source_url,
                offset=self.offset,
                volume=self.volume,
            )
        except RuntimeError:
            return self.response_error("bot not connected to a voice channel")

        return self.response(video_id=self.video_id)


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
