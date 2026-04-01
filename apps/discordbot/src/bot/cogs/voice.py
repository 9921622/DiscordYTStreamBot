import os
import sys
import asyncio

import discord
from discord.ext import commands

from bot.decorators import voice_channel_only


class VoiceCog(commands.Cog, name="voice"):
    """All voice related commands go here"""

    def __init__(self, bot: commands.bot):
        self.bot = bot

    @commands.group(name="voice", invoke_without_command=True)
    async def voice_group(self, ctx: commands.Context):
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
                    await self.bot._emit("on_disconnect", member.guild.id)
                    self.bot._delete_playback(member.guild.id)

    @voice_group.command(name="connect")
    async def connect(self, ctx: commands.Context):
        if not (ctx.author.voice and ctx.author.voice.channel):
            await ctx.send("Error: you must be in a voice channel")
            return
        await self.bot.vc_connect(ctx.author.voice.channel)

    @voice_group.command(name="disconnect")
    async def disconnect(self, ctx: commands.Context):
        await self.bot.vc_disconnect(ctx.guild.id)
        await ctx.send("Disconnected.")


async def setup(bot):
    await bot.add_cog(VoiceCog(bot))
