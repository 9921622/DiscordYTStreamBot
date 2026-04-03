from abc import abstractmethod


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
