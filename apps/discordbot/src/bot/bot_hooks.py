from functools import wraps
from bot.bot import bot

"""
    @hook("on_disconnect")
    async def on_disconnect(guild_id: int):
        do something....
        that requires a different service layer than bot
"""


def hooks(*names: str):
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await func(*args, **kwargs)

        for name in names:
            bot.on(name, wrapper)
        return wrapper

    return decorator
