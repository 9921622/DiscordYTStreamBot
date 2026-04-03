import time
import discord

from bot.models import Playback, PlaybackStatus


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
