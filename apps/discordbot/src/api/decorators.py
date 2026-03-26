import functools
from fastapi import Request


def admin_only():
    """prints(output) in the terminal when the attached command is called"""

    def decorator(f):
        @functools.wraps(f)
        async def wrapper(self, request: Request, *args, **kwargs):

            print(f"{f.__name__}: {output}")

            return await f(self, ctx, *args, **kwargs)

        return wrapper

    return decorator
