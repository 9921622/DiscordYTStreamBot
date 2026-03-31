class DiscordBotGeneric:

    async def send(self, channel_id: int, msg: str):
        await self.wait_until_ready()
        channel = self.get_channel(channel_id)
        if channel:
            await channel.send(msg)
