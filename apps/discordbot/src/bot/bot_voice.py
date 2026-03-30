import discord
import asyncio
import time

from dataclasses import dataclass, field


@dataclass
class Playback:
    video_id: str
    source_url: str
    started_at: float
    offset: float = 0.0
    paused_at: float | None = None
    volume: float = 0.5
    ended: bool = False
    manually_stopped: bool = False


class PlaybackMixin:

    def _create_playback(
        self,
        guild_id: int,
        video_id: str,
        source_url: str,
        offset: float = 0.0,
        volume: float = 0.5,
    ):
        self._playback[guild_id] = Playback(
            video_id=video_id,
            source_url=source_url,
            started_at=time.monotonic(),
            offset=offset,
            volume=volume,
            ended=False,
            manually_stopped=False,
        )

    def _delete_playback(self, guild_id: int):
        self._playback.pop(guild_id, None)

    def _get_position(self, guild_id: int) -> float:
        state = self._playback.get(guild_id)
        if not state:
            return 0.0
        if state.paused_at is not None:
            return state.offset
        return state.offset + (time.monotonic() - state.started_at)

    async def on_song_start(self, guild_id: int):
        """custom event listener. triggered when song starts"""
        pass

    async def on_song_end(self, guild_id: int):
        """custom event listener. triggered when song ends naturally"""
        pass


class ConnectionMixin:

    async def vc_connect(self, voice_channel: discord.VoiceChannel) -> discord.VoiceClient:
        """Join or move within a guild's voice channel."""
        await self.wait_until_ready()

        guild_id = voice_channel.guild.id
        vc = self.get_voice_client(guild_id)

        if vc and vc.is_connected():
            if vc.channel == voice_channel:
                return vc
            await vc.move_to(voice_channel)
        else:
            vc = await voice_channel.connect()

        return vc

    async def vc_disconnect(self, guild_id: int):
        """Leave a guild's voice channel and clean up state."""
        await self.wait_until_ready()

        state = self._playback.get(guild_id)
        if state:
            state.manually_stopped = True

        vc = self.get_voice_client(guild_id)
        if vc:
            if vc.is_playing() or vc.is_paused():
                vc.stop()
            await vc.disconnect(force=True)

        self._delete_playback(guild_id)


class DiscordBotVoice(PlaybackMixin, ConnectionMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._playback: dict[int, Playback] = {}
        self.VOLUME_SCALE = 0.125

    def get_voice_client(self, guild_id: int) -> discord.VoiceClient | None:
        return discord.utils.get(self.voice_clients, guild__id=guild_id)

    def create_audio_source(
        self, source_url: str, offset: float = 0.0, volume: float = 1.0
    ) -> discord.PCMVolumeTransformer:
        return discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                source_url,
                before_options=f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {offset}",
                options="-vn",
            ),
            volume=volume * self.VOLUME_SCALE,
        )

    async def vc_play(
        self,
        guild_id: int,
        video_id: str,
        source_url: str,
        offset: float = 0.0,
        volume: float = 0.5,
    ):
        vc = self.get_voice_client(guild_id)
        if not vc or not vc.is_connected():
            raise RuntimeError("Bot is not connected to a voice channel")

        # mark current as manually stopped before stopping
        state = self._playback.get(guild_id)
        if state:
            state.manually_stopped = True

        if vc.is_playing() or vc.is_paused():
            vc.stop()
            await asyncio.sleep(0.3)

        # create new playback state before playing
        self._create_playback(guild_id, video_id, source_url, offset, volume)

        def _after(error):
            current_state = self._playback.get(guild_id)
            if current_state and not current_state.manually_stopped:
                current_state.ended = True

                async def _run():
                    await self.on_song_end(guild_id)

                asyncio.run_coroutine_threadsafe(_run(), self.loop)

        source = self.create_audio_source(source_url, offset=offset, volume=volume)
        vc.play(source, after=_after)
        await self.on_song_start(guild_id)

    async def vc_stop(self, guild_id: int):
        """Stop playback manually without triggering on_song_end."""
        state = self._playback.get(guild_id)
        if state:
            state.manually_stopped = True

        vc = self.get_voice_client(guild_id)
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()

        self._delete_playback(guild_id)

    async def vc_seek(self, guild_id: int, position: float):
        state = self._playback.get(guild_id)
        if not state:
            raise RuntimeError("Nothing is playing")

        vc = self.get_voice_client(guild_id)
        volume = (
            (vc.source.volume / self.VOLUME_SCALE)
            if vc and isinstance(vc.source, discord.PCMVolumeTransformer)
            else state.volume
        )

        await self.vc_play(guild_id, state.video_id, state.source_url, offset=position, volume=volume)

    async def vc_volume(self, guild_id: int, level: float | None = None) -> float | None:
        """Get or set volume (0.0–1.0). Returns current volume or None if not playing."""
        vc = self.get_voice_client(guild_id)
        if not vc or not isinstance(vc.source, discord.PCMVolumeTransformer):
            return None

        if level is not None:
            vc.source.volume = max(0.0, min(1.0, level)) * self.VOLUME_SCALE
            state = self._playback.get(guild_id)
            if state:
                state.volume = level

        return vc.source.volume / self.VOLUME_SCALE

    def vc_get_status(self, guild_id: int) -> dict:
        """Returns the current playback status."""
        state = self._playback.get(guild_id)
        vc = self.get_voice_client(guild_id)

        if not state or not vc:
            return {
                "playing": False,
                "paused": False,
                "position": 0.0,
                "volume": 0.5,
                "video_id": None,
                "ended": False,
            }

        return {
            "playing": vc.is_playing(),
            "paused": vc.is_paused(),
            "position": self._get_position(guild_id),
            "volume": state.volume,
            "video_id": state.video_id,
            "ended": state.ended,
        }
