import discord
from discord.ext import commands
from discord import client

import time
from dataclasses import dataclass

from settings import settings


@dataclass
class Playback:
    source_url: str
    started_at: float
    offset: int
    paused_at: float | None = None
    volume: float = 0.5


class PlaybackMixin:

    def _create_playback(self, guild_id: int, source_url: str, offset: float = 0.0, volume: float = 0.5):
        self._playback[guild_id] = Playback(
            source_url=source_url,
            started_at=time.monotonic(),
            offset=offset,
            volume=volume,
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
        """custom event listener. triggered when song ends"""
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

        vc.stop()
        return vc

    async def vc_disconnect(self, guild_id: int):
        """Leave a guild's voice channel and clean up state."""
        await self.wait_until_ready()

        vc = self.get_voice_client(guild_id)
        if vc:
            await vc.disconnect(force=True)

        self._delete_playback(guild_id)


class DiscordBotVoice(PlaybackMixin, ConnectionMixin):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._playback: dict[int, Playback] = {}

    def create_audio_source(
        self, source_url: str, offset: float = 0.0, volume: float = 1.0
    ) -> discord.PCMVolumeTransformer:
        return discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                source_url,
                before_options=f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {offset}",
                options="-vn",
            ),
            volume=volume,
        )

    def get_voice_client(self, guild_id: int) -> discord.VoiceClient:
        return discord.utils.get(self.voice_clients, guild__id=guild_id)

    async def vc_play(self, guild_id: int, source_url: str, offset: float = 0.0, volume: float = 0.5, after=None):
        vc = self.get_voice_client(guild_id)
        if not vc or not vc.is_connected():
            raise RuntimeError("Bot is not connected to a voice channel")

        if vc.is_playing():
            vc.stop()

        def _after(error):
            async def _run():
                await self.on_song_end(guild_id)
                if after:
                    after(error)

            asyncio.run_coroutine_threadsafe(_run(), self.loop)

        source = self.create_audio_source(source_url, offset=offset, volume=volume)
        vc.play(source, after=_after)
        self._create_playback(guild_id, source_url, offset, volume)
        await self.on_song_start(guild_id)

    async def vc_volume(self, guild_id: int, level: float | None = None) -> float | None:
        """Get or set volume (0.0–1.0). Returns current volume, or None if not playing."""
        vc = self.get_voice_client(guild_id)
        if not vc or not isinstance(vc.source, discord.PCMVolumeTransformer):
            return None

        if level is not None:
            vc.source.volume = max(0.0, min(1.0, level))

        return vc.source.volume

    async def vc_seek(self, guild_id: int, position: float):
        state = self._playback.get(guild_id)
        if not state:
            raise RuntimeError("Nothing is playing")
        vc = self.get_voice_client(guild_id)
        volume = vc.source.volume if vc and isinstance(vc.source, discord.PCMVolumeTransformer) else 1.0
        await self.vc_play(guild_id, state.source_url, offset=position, volume=volume)

    def vc_get_status(self, guild_id: int) -> dict:
        """returns the status of playback"""
        state = self._playback.get(guild_id)
        vc = self.get_voice_client(guild_id)
        if not state or not vc:
            return {"playing": False, "position": 0.0}
        return {
            "playing": vc.is_playing(),
            "paused": vc.is_paused(),
            "position": self._get_position(guild_id),
            "source_url": state.source_url,
            "volume": vc.source.volume,
        }
