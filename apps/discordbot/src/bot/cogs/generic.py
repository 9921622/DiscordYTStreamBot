import discord
from discord.ext import commands


class EventsMixin:

    # GUILDS
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.bot._emit("on_guild_join", guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.bot._emit("on_guild_remove", guild.id)

    # CONNECTION
    @commands.Cog.listener()
    async def on_connect(self):
        await self.bot._emit("on_connect", guild.id)

    @commands.Cog.listener()
    async def on_disconnect(self):
        await self.bot._emit("on_disconnect", guild.id)

    # GATEWAY
    @commands.Cog.listener()
    async def on_ready(self):
        print(f"Logged in as {self.bot.user}")

    # @commands.Cog.listener()
    # async def on_message(self, message):
    #     if self.bot.user.mentioned_in(message):
    #         reaction_path = os.path.join(Settings.instance().ASSET_PATH, 'intrigued.jpg')
    #         file = discord.File(reaction_path, filename="intrigued.jpg")

    #         embed = discord.Embed()
    #         embed.set_image(url="attachment://intrigued.jpg")

    #         await message.channel.send(file=file)


class CommandsMixin:

    @commands.command(name="ping")
    async def ping(self, ctx: commands.Context):
        await ctx.send("pong")


class GenericCog(commands.Cog, CommandsMixin, EventsMixin):
    def __init__(self, bot: commands.bot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(GenericCog(bot))
