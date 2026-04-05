from unittest.mock import MagicMock, AsyncMock


class CogTestCase:

    GUILD_ID = 381273798129

    @classmethod
    def make_cog(cls, bot):
        raise Exception("implement this")

    @classmethod
    def make_member(cls, bot_instance, member_id=9999, is_bot=False, guild_id=None):
        member = MagicMock()
        member.id = bot_instance.user.id if is_bot else member_id
        member.bot = is_bot
        member.guild.id = guild_id if guild_id is not None else cls.GUILD_ID
        return member

    @classmethod
    def make_voice_state(cls, channel=None):
        state = MagicMock()
        state.channel = channel
        return state

    @classmethod
    def make_channel(cls, name="test-channel"):
        channel = MagicMock()
        channel.name = name
        channel.send = AsyncMock()
        return channel
