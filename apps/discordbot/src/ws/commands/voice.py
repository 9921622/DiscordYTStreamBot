from bot.bot import bot
from ws.ws_command import WebsocketCommand
from .mixins import DiscordUserMixin


class UsersCommand(DiscordUserMixin, WebsocketCommand):
    prefix = "users"

    async def handle(self):
        return self.response(members=bot.vc_get_members(self.guild_id).model_dump())
