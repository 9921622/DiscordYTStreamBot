from bot.bot import bot
from api.api_backend_wrapper import VideoAPI
from api.websockets.ws_command import WebsocketCommand, WSCommandFlags


class PlayCommand(WebsocketCommand):
    prefix = "play"
    flags = WSCommandFlags.BROADCAST_STATUS

    async def handle(self):
        video_id = self.data.get("video_id")
        if not video_id:
            return self.response_error("missing 'video_id'")

        rw = await VideoAPI.get_source(video_id)

        if not rw.response.is_success:
            return self.response_error("bot not connected to a voice channel", detail=rw.response.json())

        try:
            await bot.vc_play(
                self.guild_id,
                video_id,
                rw.data.source_url,
                offset=self.data.get("offset", 0.0),
                volume=self.data.get("volume", 0.5),
            )
        except RuntimeError:
            return self.response_error("bot not connected to a voice channel")

        return self.response(video_id=video_id)


class PauseCommand(WebsocketCommand):
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


class StopCommand(WebsocketCommand):
    prefix = "stop"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        await bot.vc_stop(self.guild_id)
        return self.response()


class LoopCommand(WebsocketCommand):
    prefix = "loop"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        try:
            await bot.vc_loop(self.guild_id)
        except RuntimeError as e:
            return self.response_error(str(e))

        status = bot.vc_get_status(self.guild_id)
        return self.response(loop=status.loop)


class SeekCommand(WebsocketCommand):
    prefix = "seek"
    flags = WSCommandFlags.BROADCAST_STATUS

    async def handle(self):
        position = self.data.get("position")

        if position is None:
            return self.response_error("missing 'position'")

        try:
            await bot.vc_seek(self.guild_id, float(position))
        except RuntimeError:
            return self.response_error("nothing is playing")

        return self.response(position=position)


class StatusCommand(WebsocketCommand):
    prefix = "status"
    flags = WSCommandFlags.BROADCAST

    async def handle(self):
        return self.response(playback=bot.vc_get_status(self.guild_id).model_dump())


class VolumeCommand(WebsocketCommand):
    prefix = "volume"
    flags = WSCommandFlags.BROADCAST_STATUS

    async def handle(self):
        level = self.data.get("level")
        result = await bot.vc_volume(self.guild_id, level)

        if result is None:
            return self.response_error("no active audio source")
        return self.response(volume=result)
