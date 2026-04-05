import discord
from discord.ext import commands

from settings import settings


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
        # Handle bot being forcefully disconnected
        if member.id == self.bot.user.id:
            if before.channel is not None and after.channel is None:
                await self.bot._emit("on_disconnect", member.guild.id)
                self.bot._delete_playback(member.guild.id)
            return

        bot_vc = member.guild.voice_client

        # Ignore events if bot isn't in a voice channel
        if not bot_vc:
            return

        user_joined = before.channel is None and after.channel is not None
        user_left = before.channel is not None and after.channel != before.channel

        # Only care about events in the bot's channel
        user_joined_bots_channel = user_joined and after.channel == bot_vc.channel
        user_left_bots_channel = user_left and before.channel == bot_vc.channel

        if user_joined_bots_channel:
            await self.bot._emit("on_voice_connect", member.guild.id)

            embed = discord.Embed(
                title="🎵 Music Session",
                description="A new session is ready! Click below to open the player.",
                color=discord.Color.blurple(),
            )
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Open Player",
                    url=settings.FRONTEND_URL,
                    style=discord.ButtonStyle.link,
                )
            )
            await after.channel.send(embed=embed, view=view)

        if user_left_bots_channel:
            await self.bot._emit("on_voice_disconnect", member.guild.id)

            # Disconnect bot if it's now alone
            if len(bot_vc.channel.members) == 1:
                await self.bot._emit("on_disconnect", member.guild.id)
                self.bot._delete_playback(member.guild.id)
                await bot_vc.disconnect()

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
