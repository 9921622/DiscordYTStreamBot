from bot.bot import bot
import time

"""  creates a global instance to use discord bot """


class DiscordServiceVCMixin:

    self.voice_clients: dict[int, discord.VoiceClient] = {}

    async def connect(self, voice_channel: discord.VoiceChannel) -> discord.VoiceClient:
        """Join or move within a guild's voice channel."""
        await self.bot.wait_until_ready()

        guild_id = voice_channel.guild.id
        vc = self.bot.get_voice_client(guild_id)

        if vc and vc.is_connected():
            await vc.move_to(voice_channel)
        else:
            vc = await voice_channel.connect()

        return vc

    async def disconnect(self, guild_id: int):
        """Leave a guild's voice channel and clean up state."""
        await self.bot.wait_until_ready()

        vc = self.bot.get_voice_client(guild_id)

        if vc and vc.is_connected():
            await vc.disconnect()

        self._reset_playback_state(guild_id)

    async def voice_volume(self, guild_id: int):
        pass


class DiscordService(DiscordServiceVCMixin):
    """wrapper to simplify commands"""

    def __init__(self):
        self.bot = bot

    async def send(self, channel_id: int, msg: str):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send(msg)


discord_service = DiscordService()
