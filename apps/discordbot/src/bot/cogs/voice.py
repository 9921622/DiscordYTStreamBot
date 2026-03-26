import os
import sys
import asyncio

import nextcord
from nextcord.ext import commands

from bot.decorators import voice_channel_only


class VoiceCog(commands.Cog):
    """All voice related commands go here"""

    def __init__(self, bot: commands.bot):
        self.bot = bot

    @commands.group(name="voice", invoke_without_command=True)
    async def voice(self, ctx: commands.Context):
        pass

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """
        Triggered whenever a member joins, leaves, or moves between voice channels.
        """

        # Only care about members leaving a channel
        if before.channel is not None and after.channel != before.channel:
            # Check if the channel the bot is in is now empty
            bot_vc = member.guild.voice_client
            if bot_vc and bot_vc.channel == before.channel:
                if len(bot_vc.channel.members) == 1:  # only the bot remains
                    await bot_vc.disconnect()
                    self.bot.vc_cache.delete(member.guild.id)

    @voice.command(name="connect")
    async def connect(self, ctx: commands.Context):
        if not (ctx.author.voice and ctx.author.voice.channel):
            await ctx.send("Error: could not connect")
            return

        vc = await ctx.author.voice.channel.connect()
        vc.stop()

    @voice.command(name="disconnect")
    @voice_channel_only()
    async def disconnect(self, ctx: commands.Context):
        await ctx.guild.voice_client.disconnect()


async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
