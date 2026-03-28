class DiscordBotGeneric:

    async def send(self, channel_id: int, msg: str):
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(channel_id)
        if channel:
            await channel.send(msg)
