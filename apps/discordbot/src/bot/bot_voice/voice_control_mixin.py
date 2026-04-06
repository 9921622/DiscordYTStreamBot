import discord

from bot.models import DiscordUserList, DiscordUser, PlaybackStatus


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

    def vc_get_members(self, guild_id: int) -> DiscordUser:
        guild = self.get_guild(guild_id)
        if not guild or not guild.voice_client or not guild.voice_client.channel:
            return DiscordUserList([])

        return DiscordUserList(
            [
                DiscordUser(
                    discord_id=str(m.id),
                    global_name=m.display_name,
                    avatar_url=str(m.display_avatar.url),
                )
                for m in guild.voice_client.channel.members
                if not m.bot
            ]
        )
