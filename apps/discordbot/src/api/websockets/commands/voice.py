from bot.bot import bot
from api.websockets.ws_command import WebsocketCommand


class UsersCommand(WebsocketCommand):
    prefix = "users"

    async def handle(self):
        await bot.vc_stop(self.guild_id)
        return self.response(members=bot.vc_get_members(self.guild_id).model_dump())
