import time
import discord
import asyncio
from abc import abstractmethod

from bot.models import MemberList, Member, Playback, PlaybackStatus


class AudioMixin:
    """Raw Discord audio operations: source creation, play, stop."""

    VOLUME_SCALE = 0.125

    def get_voice_client(self, guild_id: int) -> discord.VoiceClient | None:
        return discord.utils.get(self.voice_clients, guild__id=guild_id)

    def _create_audio_source(
        self, source_url: str, offset: float = 0.0, volume: float = 1.0
    ) -> discord.PCMVolumeTransformer:
        return discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(
                source_url,
                before_options=(f"-reconnect 1 -reconnect_streamed 1 " f"-reconnect_delay_max 5 -ss {offset}"),
                options="-vn",
            ),
            volume=volume * self.VOLUME_SCALE,
        )

    def _handle_playback_end(self, guild_id: int, generation: int, error):
        """Sync callback passed to vc.play(after=...). Discards stale callbacks."""
        state = self._playback.get(guild_id)
        if not state or self._generation.get(guild_id) != generation:
            return

        state.ended = True

        async def _run():
            if state.loop:
                await self.vc_play(
                    guild_id,
                    state.video_id,
                    state.source_url,
                    offset=0.0,
                    volume=state.volume,
                )
            else:
                await self.on_song_end(guild_id)

        asyncio.run_coroutine_threadsafe(_run(), self.loop)

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

        prior = self._playback.get(guild_id)
        loop = prior.loop if prior else False

        if prior:
            prior.manually_stopped = True

        if vc.is_playing() or vc.is_paused():
            vc.stop()

        state, generation = self._create_playback(guild_id, video_id, source_url, offset, volume, loop=loop)

        source = self._create_audio_source(source_url, offset=offset, volume=volume)
        vc.play(source, after=lambda err: self._handle_playback_end(guild_id, generation, err))
        await self.on_song_start(guild_id)

    async def vc_stop(self, guild_id: int):
        """Stop playback without triggering on_song_end."""
        self._stop_playback(guild_id)
        vc = self.get_voice_client(guild_id)
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()
