import functools
from nextcord.ext import commands

# https://stackoverflow.com/a/78668962


def test_print(output="test"):
    """prints(output) in the terminal when the attached command is called"""

    def decorator(f):
        @functools.wraps(f)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):

            print(f"{f.__name__}: {output}")

            return await f(self, ctx, *args, **kwargs)

        return wrapper

    return decorator


def class_decorator():
    """
    applies a method only decorator and applies it to whole Cog class.
        probably self.getcommands????

    d : decorator to attach to class
    method : the name of the method to attach to
    """
    # JUST USE `async def cog_check` and attach decorator to it


def owner_only():
    """asserts if the caller of command is the owner of the bot
    https://stackoverflow.com/questions/56637056/how-do-you-create-a-custom-decorator-for-discord-py
    """

    async def predicate(ctx: commands.Context):
        return await ctx.bot.is_owner(ctx.author)

    return commands.check(predicate)


def voice_channel_only(mode="require"):
    """
    for commands that require the caller to be in a voice channel.
    call inside `commands.Cog` under @command.

    Mode:
        require = blocks command and sends error message
        autojoin = automatically joins the same voice channel as the ctx.author.
    """

    def decorator(f):
        @functools.wraps(f)
        async def wrapper(self, ctx: commands.Context, *args, **kwargs):

            if not (ctx.author.voice and ctx.author.voice.channel):
                await ctx.send("🔊 Please join a voice channel first.")
                return

            bot_vc = ctx.guild.me.voice and ctx.guild.me.voice.channel
            same_vc = bot_vc and ctx.author.voice.channel == ctx.guild.me.voice.channel

            vc = ctx.guild.voice_client
            using_vc = vc and vc.is_playing()

            if mode == "require":
                if not bot_vc:
                    await ctx.send("🔊 The bot is not in a voice channel.")
                    return
                if not same_vc:
                    await ctx.send("🔊 You must be in the same voice channel as the bot.")
                    return

            elif mode == "autojoin":
                if not same_vc and using_vc:
                    await ctx.send("🔊 I'm already streaming in a voice channel.")
                    return

                if not same_vc or not ctx.guild.voice_client:
                    # voice_client is None when bot is restarted and still in a channel
                    vc = await ctx.author.voice.channel.connect()
                    vc.stop()

            return await f(self, ctx, *args, **kwargs)

        return wrapper

    return decorator
