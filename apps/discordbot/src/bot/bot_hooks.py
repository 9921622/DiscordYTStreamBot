from functools import wraps
from bot.bot import bot


"""
    @hook("on_disconnect")
    async def on_disconnect(guild_id: int):
        do something....
        that requires a different service layer than bot
"""


def hook(name: str):
    def decorator(func):
        bot.on(name, func)
        return func

    return decorator
