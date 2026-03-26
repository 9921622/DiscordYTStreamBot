from bot.bot import bot

"""  creates a global instance to use discord bot """


class DiscordServiceVCMixin:

    async def connect(self):
        await self.bot.wait_until_ready()

    async def disconnect(self):
        await self.bot.wait_until_ready()


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
