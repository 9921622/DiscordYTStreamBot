import discord


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
