import time
import discord
import asyncio
from abc import abstractmethod

from bot.models import MemberList, Member, Playback, PlaybackStatus


class PlaybackHandler:
    """Manages Playback state"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._playback: dict[int, Playback] = {}

        # Incremented each time a new track starts for a guild. The current
        # generation is captured in the vc.play(after=...) closure, so when
        # the audio thread fires the callback we can detect whether it belongs
        # to the track that is still active or a previous one that was
        # interrupted. A mismatch means the callback is stale and should be discarded
        self._generation: dict[int, int] = {}

    def _create_playback(
        self,
        guild_id: int,
        video_id: str,
        source_url: str,
        offset: float = 0.0,
        volume: float = 0.5,
        loop: bool = False,
    ) -> tuple[Playback, int]:
        state = Playback(
            video_id=video_id,
            source_url=source_url,
            started_at=time.monotonic(),
            offset=offset,
            volume=volume,
            ended=False,
            manually_stopped=False,
            loop=loop,
        )
        generation = self._generation.get(guild_id, 0) + 1
        self._playback[guild_id] = state
        self._generation[guild_id] = generation
        return state, generation

    def _delete_playback(self, guild_id: int):
        self._playback.pop(guild_id, None)

    def _stop_playback(self, guild_id: int):
        """Mark current playback as manually stopped and delete it."""
        state = self._playback.get(guild_id)
        if state:
            state.manually_stopped = True
        self._delete_playback(guild_id)

    def _get_position(self, guild_id: int) -> float:
        state = self._playback.get(guild_id)
        return state.get_position() if state else 0.0

    def _build_playback_status(self, vc: discord.VoiceClient, state: Playback) -> PlaybackStatus:
        return PlaybackStatus(
            playing=vc.is_playing(),
            paused=vc.is_paused(),
            position=state.get_position(),
            volume=state.volume,
            video_id=state.video_id,
            ended=state.ended,
            loop=state.loop,
        )


class VoiceEventsMixin:
    """Translates internal playback lifecycle into named events via _emit."""

    @abstractmethod
    async def _emit(self, event: str, guild_id: int) -> None:
        """Implemented by the EventHandler base (e.g. ws_manager dispatch)."""
        ...

    async def on_song_start(self, guild_id: int):
        await self._emit("on_song_start", guild_id)

    async def on_song_end(self, guild_id: int):
        await self._emit("on_song_end", guild_id)


class ConnectionMixin:
    """Handles joining and leaving voice channels."""

    async def vc_connect(self, voice_channel: discord.VoiceChannel) -> discord.VoiceClient:
        """Join or move within a guild's voice channel."""
        await self.wait_until_ready()

        guild_id = voice_channel.guild.id
        vc = self.get_voice_client(guild_id)

        if vc and vc.is_connected():
            if vc.channel != voice_channel:
                await vc.move_to(voice_channel)
            return vc

        return await voice_channel.connect()

    async def vc_disconnect(self, guild_id: int):
        """Leave a guild's voice channel and clean up state."""
        await self.wait_until_ready()

        vc = self.get_voice_client(guild_id)
        if vc:
            if vc.is_playing() or vc.is_paused():
                vc.stop()
            await vc.disconnect(force=True)

        self._stop_playback(guild_id)
        await self._emit("on_disconnect", guild_id)


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


class VoiceControlMixin:
    """Higher-level playback controls and status queries."""

    async def vc_seek(self, guild_id: int, position: float):
        state = self._playback.get(guild_id)
        if not state:
            raise RuntimeError("Nothing is playing")

        vc = self.get_voice_client(guild_id)
        volume = (
            vc.source.volume / self.VOLUME_SCALE
            if vc and isinstance(vc.source, discord.PCMVolumeTransformer)
            else state.volume
        )
        await self.vc_play(guild_id, state.video_id, state.source_url, offset=position, volume=volume)

    async def vc_volume(self, guild_id: int, level: float | None = None) -> float | None:
        """Get or set volume (0.0–1.0). Returns None if nothing is playing."""
        vc = self.get_voice_client(guild_id)
        if not vc or not isinstance(vc.source, discord.PCMVolumeTransformer):
            return None

        if level is not None:
            clamped = max(0.0, min(1.0, level))
            vc.source.volume = clamped * self.VOLUME_SCALE
            state = self._playback.get(guild_id)
            if state:
                state.volume = clamped

        return vc.source.volume / self.VOLUME_SCALE

    async def vc_loop(self, guild_id: int) -> bool | None:
        state = self._playback.get(guild_id)
        if not state:
            return None
        state.loop = not state.loop
        return state.loop

    def vc_get_status(self, guild_id: int) -> PlaybackStatus:
        state = self._playback.get(guild_id)
        vc = self.get_voice_client(guild_id)

        if not state or not vc:
            return PlaybackStatus(
                playing=False,
                paused=False,
                position=0.0,
                volume=0.5,
                video_id=None,
                ended=False,
                loop=False,
            )

        return self._build_playback_status(vc, state)

    def vc_get_members(self, guild_id: int) -> MemberList:
        guild = self.get_guild(guild_id)
        if not guild or not guild.voice_client or not guild.voice_client.channel:
            return MemberList([])

        return MemberList(
            [
                Member(
                    discord_id=str(m.id),
                    username=m.name,
                    global_name=m.display_name,
                    avatar=str(m.display_avatar.url),
                )
                for m in guild.voice_client.channel.members
                if not m.bot
            ]
        )


class DiscordBotVoice(
    VoiceControlMixin,
    AudioMixin,
    ConnectionMixin,
    VoiceEventsMixin,
    PlaybackHandler,
):
    """
    Composition root. Inherits all voice functionality from focused mixins.
    MRO (left to right): VoiceControlMixin → AudioMixin → ConnectionMixin
                       → VoiceEventsMixin → PlaybackHandler
    """

    pass
