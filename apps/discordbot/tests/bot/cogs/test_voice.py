import pytest
from unittest.mock import MagicMock, AsyncMock, patch
import discord

from bot.cogs.voice import VoiceCog
from tests.bot.cogs.test_case import CogTestCase
from tests.bot.bot_utils import bot, guild_id, vc  # NOQA

GUILD_ID = 2327328


class VoiceCogTestCase(CogTestCase):

    GUILD_ID = GUILD_ID

    @classmethod
    def make_cog(cls, bot):
        return VoiceCog(bot)


# ── Bot forced disconnect ──────────────────────────────────────────────────────


class TestOnVoiceStateUpdate_BotDisconnect(VoiceCogTestCase):

    @pytest.mark.asyncio
    async def test_bot_forced_disconnect_emits_and_deletes(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()
        bot._delete_playback = MagicMock()

        member = self.make_member(bot, is_bot=True)
        before = self.make_voice_state(channel=MagicMock())
        after = self.make_voice_state(channel=None)

        await cog.on_voice_state_update(member, before, after)

        bot._emit.assert_awaited_once_with("on_disconnect", GUILD_ID)
        bot._delete_playback.assert_called_once_with(GUILD_ID)

    @pytest.mark.asyncio
    async def test_bot_moving_channels_does_not_emit(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()

        member = self.make_member(bot, is_bot=True)
        before = self.make_voice_state(channel=MagicMock())
        after = self.make_voice_state(channel=MagicMock())

        await cog.on_voice_state_update(member, before, after)

        bot._emit.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_early_after_bot_event(self, bot):
        """No further processing should happen after handling the bot's own event."""
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()

        member = self.make_member(bot, is_bot=True)
        channel = MagicMock()
        before = self.make_voice_state(channel=channel)
        after = self.make_voice_state(channel=None)
        member.guild.voice_client = MagicMock()

        await cog.on_voice_state_update(member, before, after)

        # only on_disconnect, never on_voice_connect/disconnect
        bot._emit.assert_awaited_once_with("on_disconnect", GUILD_ID)


# ── Bot not in channel ─────────────────────────────────────────────────────────


class TestOnVoiceStateUpdate_BotNotInChannel(VoiceCogTestCase):

    @pytest.mark.asyncio
    async def test_ignores_event_when_bot_not_in_vc(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()

        member = self.make_member(bot)
        member.guild.voice_client = None
        before = self.make_voice_state(channel=None)
        after = self.make_voice_state(channel=MagicMock())

        await cog.on_voice_state_update(member, before, after)

        bot._emit.assert_not_called()


# ── User joins bot's channel ───────────────────────────────────────────────────


class TestOnVoiceStateUpdate_UserJoins(VoiceCogTestCase):

    @pytest.mark.asyncio
    async def test_user_joining_bots_channel_emits_voice_connect(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()

        channel = self.make_channel()
        member = self.make_member(bot)
        member.guild.voice_client = MagicMock(channel=channel)

        before = self.make_voice_state(channel=None)
        after = self.make_voice_state(channel=channel)

        await cog.on_voice_state_update(member, before, after)

        bot._emit.assert_awaited_once_with("on_voice_connect", GUILD_ID)

    @pytest.mark.asyncio
    async def test_user_joining_bots_channel_sends_embed(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()

        channel = self.make_channel()
        member = self.make_member(bot)
        member.guild.voice_client = MagicMock(channel=channel)

        before = self.make_voice_state(channel=None)
        after = self.make_voice_state(channel=channel)

        await cog.on_voice_state_update(member, before, after)

        channel.send.assert_awaited_once()
        _, kwargs = channel.send.call_args
        assert "embed" in kwargs
        assert isinstance(kwargs["embed"], discord.Embed)

    @pytest.mark.asyncio
    async def test_user_joining_different_channel_does_not_emit(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()

        bots_channel = self.make_channel("bots-channel")
        other_channel = self.make_channel("other-channel")
        member = self.make_member(bot)
        member.guild.voice_client = MagicMock(channel=bots_channel)

        before = self.make_voice_state(channel=None)
        after = self.make_voice_state(channel=other_channel)

        await cog.on_voice_state_update(member, before, after)

        bot._emit.assert_not_called()


# ── User leaves bot's channel ──────────────────────────────────────────────────


class TestOnVoiceStateUpdate_UserLeaves(VoiceCogTestCase):

    @pytest.mark.asyncio
    async def test_user_leaving_bots_channel_emits_voice_disconnect(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()

        channel = self.make_channel()
        bot_vc = MagicMock(channel=channel)
        bot_vc.channel.members = [MagicMock(), MagicMock()]  # bot + someone else
        bot_vc.disconnect = AsyncMock()

        member = self.make_member(bot)
        member.guild.voice_client = bot_vc

        before = self.make_voice_state(channel=channel)
        after = self.make_voice_state(channel=MagicMock())

        await cog.on_voice_state_update(member, before, after)

        bot._emit.assert_awaited_once_with("on_voice_disconnect", GUILD_ID)

    @pytest.mark.asyncio
    async def test_bot_disconnects_when_alone(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()
        bot._delete_playback = MagicMock()

        channel = self.make_channel()
        bot_vc = MagicMock(channel=channel)
        bot_vc.channel.members = [MagicMock()]  # only the bot remains
        bot_vc.disconnect = AsyncMock()

        member = self.make_member(bot)
        member.guild.voice_client = bot_vc

        before = self.make_voice_state(channel=channel)
        after = self.make_voice_state(channel=MagicMock())

        await cog.on_voice_state_update(member, before, after)

        bot_vc.disconnect.assert_awaited_once()
        bot._delete_playback.assert_called_once_with(GUILD_ID)

    @pytest.mark.asyncio
    async def test_on_disconnect_emitted_when_bot_left_alone(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()
        bot._delete_playback = MagicMock()

        channel = self.make_channel()
        bot_vc = MagicMock(channel=channel)
        bot_vc.channel.members = [MagicMock()]
        bot_vc.disconnect = AsyncMock()

        member = self.make_member(bot)
        member.guild.voice_client = bot_vc

        before = self.make_voice_state(channel=channel)
        after = self.make_voice_state(channel=MagicMock())

        await cog.on_voice_state_update(member, before, after)

        emitted_events = [call.args[0] for call in bot._emit.await_args_list]
        assert "on_disconnect" in emitted_events
        assert "on_voice_disconnect" in emitted_events

    @pytest.mark.asyncio
    async def test_bot_does_not_disconnect_when_others_remain(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()

        channel = self.make_channel()
        bot_vc = MagicMock(channel=channel)
        bot_vc.channel.members = [MagicMock(), MagicMock(), MagicMock()]  # bot + 2 users
        bot_vc.disconnect = AsyncMock()

        member = self.make_member(bot)
        member.guild.voice_client = bot_vc

        before = self.make_voice_state(channel=channel)
        after = self.make_voice_state(channel=MagicMock())

        await cog.on_voice_state_update(member, before, after)

        bot_vc.disconnect.assert_not_called()

    @pytest.mark.asyncio
    async def test_user_leaving_different_channel_does_not_emit(self, bot):
        cog = self.make_cog(bot)
        bot._emit = AsyncMock()

        bots_channel = self.make_channel("bots-channel")
        other_channel = self.make_channel("other-channel")
        bot_vc = MagicMock(channel=bots_channel)
        bot_vc.disconnect = AsyncMock()

        member = self.make_member(bot)
        member.guild.voice_client = bot_vc

        before = self.make_voice_state(channel=other_channel)
        after = self.make_voice_state(channel=MagicMock())

        await cog.on_voice_state_update(member, before, after)

        bot._emit.assert_not_called()


# ── connect command ────────────────────────────────────────────────────────────


class TestConnectCommand(VoiceCogTestCase):

    @pytest.mark.asyncio
    async def test_connect_calls_vc_connect(self, bot):
        cog = self.make_cog(bot)
        bot.vc_connect = AsyncMock()

        ctx = MagicMock()
        ctx.author.voice.channel = MagicMock()

        await cog.connect.callback(cog, ctx)

        bot.vc_connect.assert_awaited_once_with(ctx.author.voice.channel)

    @pytest.mark.asyncio
    async def test_connect_sends_error_when_not_in_channel(self, bot):
        cog = self.make_cog(bot)
        bot.vc_connect = AsyncMock()

        ctx = MagicMock()
        ctx.author.voice = None
        ctx.send = AsyncMock()

        await cog.connect.callback(cog, ctx)

        ctx.send.assert_awaited_once()
        bot.vc_connect.assert_not_called()


# ── disconnect command ─────────────────────────────────────────────────────────


class TestDisconnectCommand(VoiceCogTestCase):

    @pytest.mark.asyncio
    async def test_disconnect_calls_vc_disconnect(self, bot):
        cog = self.make_cog(bot)
        bot.vc_disconnect = AsyncMock()

        ctx = MagicMock()
        ctx.guild.id = GUILD_ID
        ctx.send = AsyncMock()

        await cog.disconnect.callback(cog, ctx)

        bot.vc_disconnect.assert_awaited_once_with(GUILD_ID)

    @pytest.mark.asyncio
    async def test_disconnect_sends_confirmation(self, bot):
        cog = self.make_cog(bot)
        bot.vc_disconnect = AsyncMock()

        ctx = MagicMock()
        ctx.guild.id = GUILD_ID
        ctx.send = AsyncMock()

        await cog.disconnect.callback(cog, ctx)

        ctx.send.assert_awaited_once_with("Disconnected.")
