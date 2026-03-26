from bot.bot import bot

"""  creates a global instance to use discord bot """


class DiscordService:
    """wrapper to simplify commands"""

    def __init__(self):
        self.bot = bot

    async def send(self, channel_id: int, msg: str):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send(msg)


discord_service = DiscordService()
