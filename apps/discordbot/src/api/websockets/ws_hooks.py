from functools import wraps
from bot.bot import bot


def hook(name: str):
    def decorator(func):
        bot.on(name, func)
        return func

    return decorator
