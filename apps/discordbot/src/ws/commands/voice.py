from bot.bot import bot
from ws.ws_command import WebsocketCommand


class UsersCommand(WebsocketCommand):
    prefix = "users"

    async def handle(self):
        return self.response(members=bot.vc_get_members(self.guild_id).model_dump())
