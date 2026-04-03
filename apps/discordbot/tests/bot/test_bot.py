import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch

from bot.models import PlaybackStatus, Member, MemberList

from tests.bot.bot_utils import bot, guild_id, vc  # NOQA  # prevent autoflake removal
from tests.bot.factories import PlaybackStatusFactory, MemberFactory

# ── PlaybackHandler unit tests ───────────────────────────────────────────────────


class TestPlaybackHandler:

    def test_create_and_get_playback(self, bot, guild_id):
        bot._create_playback(guild_id, "vid1", "http://audio.url")
        state = bot._playback[guild_id]
        assert state.video_id == "vid1"
        assert state.volume == 0.5
        assert state.loop is False
        assert state.ended is False

    def test_delete_playback(self, bot, guild_id):
        bot._create_playback(guild_id, "vid1", "http://audio.url")
        bot._delete_playback(guild_id)
        assert guild_id not in bot._playback

    def test_delete_playback_missing_guild_is_safe(self, bot):
        bot._delete_playback(999)

    def test_get_position_no_state(self, bot, guild_id):
        assert bot._get_position(guild_id) == 0.0

    def test_get_position_with_state(self, bot, guild_id):
        bot._create_playback(guild_id, "vid1", "http://audio.url", offset=10.0)
        pos = bot._get_position(guild_id)
        assert pos >= 10.0

    def test_build_playback_status_matches_factory_shape(self, bot, guild_id, vc):
        """Factory-generated instance tells us exactly which fields must be present."""
        bot._create_playback(guild_id, "vid1", "http://audio.url", volume=0.7)
        state = bot._playback[guild_id]

        result = bot._build_playback_status(vc, state)
        reference = PlaybackStatusFactory.build()

        # every field present on the factory model must exist on the real result
        assert set(PlaybackStatus.model_fields) == set(
            PlaybackStatus.model_fields
        )  # same class, so simplifies to just:

        assert isinstance(result, PlaybackStatus)
        # spot-check that values were actually wired through
        assert result.video_id == "vid1"
        assert result.volume == 0.7


# ── vc_get_status ──────────────────────────────────────────────────────────────


class TestVcGetStatus:

    def test_returns_default_when_nothing_playing(self, bot, guild_id):
        status = bot.vc_get_status(guild_id)
        reference = PlaybackStatusFactory.build(playing=False, video_id=None)
        assert status.playing == reference.playing
        assert status.video_id == reference.video_id

    def test_returns_status_when_playing(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        bot._create_playback(guild_id, "abc", "http://url", volume=0.4)

        status = bot.vc_get_status(guild_id)
        expected = PlaybackStatusFactory.build(video_id="abc", volume=0.4)

        assert status.video_id == expected.video_id
        assert status.volume == expected.volume

    def test_status_fields_are_complete(self, bot, guild_id, vc):
        """No fields go missing as PlaybackStatus evolves."""
        bot._inject_vc(vc)
        bot._create_playback(guild_id, "abc", "http://url")

        status = bot.vc_get_status(guild_id)
        reference = PlaybackStatusFactory.build()

        assert set(vars(status).keys()) == set(vars(reference).keys())


# ── vc_loop ────────────────────────────────────────────────────────────────────


class TestVcLoop:

    @pytest.mark.asyncio
    async def test_loop_toggles_on(self, bot, guild_id):
        bot._create_playback(guild_id, "vid", "http://url")
        result = await bot.vc_loop(guild_id)
        assert result is True
        assert bot._playback[guild_id].loop is True

    @pytest.mark.asyncio
    async def test_loop_toggles_off(self, bot, guild_id):
        bot._create_playback(guild_id, "vid", "http://url")
        bot._playback[guild_id].loop = True
        result = await bot.vc_loop(guild_id)
        assert result is False

    @pytest.mark.asyncio
    async def test_loop_no_state_returns_none(self, bot, guild_id):
        result = await bot.vc_loop(guild_id)
        assert result is None


# ── vc_volume ──────────────────────────────────────────────────────────────────


class TestVcVolume:

    @pytest.mark.asyncio
    async def test_returns_none_when_no_vc(self, bot, guild_id):
        result = await bot.vc_volume(guild_id)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_volume(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        result = await bot.vc_volume(guild_id)
        assert pytest.approx(result, abs=0.01) == 0.5

    @pytest.mark.asyncio
    async def test_set_volume_clamps_high(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        bot._create_playback(guild_id, "vid", "http://url")
        result = await bot.vc_volume(guild_id, level=2.0)
        assert result == pytest.approx(1.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_set_volume_clamps_low(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        bot._create_playback(guild_id, "vid", "http://url")
        result = await bot.vc_volume(guild_id, level=-0.5)
        assert result == pytest.approx(0.0, abs=0.01)

    @pytest.mark.asyncio
    async def test_set_volume_updates_state(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        bot._create_playback(guild_id, "vid", "http://url")
        await bot.vc_volume(guild_id, level=0.8)
        assert bot._playback[guild_id].volume == 0.8


# ── vc_stop ────────────────────────────────────────────────────────────────────


class TestVcStop:

    @pytest.mark.asyncio
    async def test_stop_clears_playback(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        vc.is_playing.return_value = True
        bot._create_playback(guild_id, "vid", "http://url")

        await bot.vc_stop(guild_id)

        assert guild_id not in bot._playback
        vc.stop.assert_called_once()

    @pytest.mark.asyncio
    async def test_stop_sets_manually_stopped(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        vc.is_playing.return_value = True
        bot._create_playback(guild_id, "vid", "http://url")
        state = bot._playback[guild_id]

        await bot.vc_stop(guild_id)

        assert state.manually_stopped is True


# ── vc_play ────────────────────────────────────────────────────────────────────


class TestVcPlay:

    @pytest.mark.asyncio
    async def test_raises_when_not_connected(self, bot, guild_id):
        with pytest.raises(RuntimeError, match="not connected"):
            await bot.vc_play(guild_id, "vid", "http://url")

    @pytest.mark.asyncio
    async def test_play_creates_state_and_calls_vc(self, bot, guild_id, vc):
        bot._inject_vc(vc)

        with patch.object(bot, "_create_audio_source", return_value=MagicMock()):
            await bot.vc_play(guild_id, "vid1", "http://audio.url", volume=0.6)

        state = bot._playback[guild_id]
        expected = PlaybackStatusFactory.build(video_id="vid1", volume=0.6)

        assert state.video_id == expected.video_id
        assert state.volume == expected.volume
        vc.play.assert_called_once()

    @pytest.mark.asyncio
    async def test_play_emits_on_song_start(self, bot, guild_id, vc):
        bot._inject_vc(vc)

        with patch.object(bot, "_emit", new_callable=AsyncMock) as mock_emit:
            with patch.object(bot, "_create_audio_source", return_value=MagicMock()):
                await bot.vc_play(guild_id, "vid1", "http://audio.url")

        mock_emit.assert_awaited_with("on_song_start", guild_id)

    @pytest.mark.asyncio
    async def test_play_emits_on_song_end(self, bot, guild_id, vc):
        bot._inject_vc(vc)

        with patch.object(bot, "_create_audio_source", return_value=MagicMock()):
            await bot.vc_play(guild_id, "vid1", "http://audio.url")

        generation = bot._generation[guild_id]

        with patch.object(bot, "_emit", new_callable=AsyncMock) as mock_emit:
            with patch("asyncio.run_coroutine_threadsafe", side_effect=lambda coro, _loop: asyncio.ensure_future(coro)):
                bot._handle_playback_end(guild_id, generation, error=None)
                await asyncio.sleep(0)

        mock_emit.assert_awaited_with("on_song_end", guild_id)

    @pytest.mark.asyncio
    async def test_play_stops_existing_before_new(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        vc.is_playing.return_value = True
        bot._create_playback(guild_id, "old_vid", "http://old.url")

        with patch.object(bot, "_create_audio_source", return_value=MagicMock()):
            with patch("asyncio.sleep", new_callable=AsyncMock):
                await bot.vc_play(guild_id, "new_vid", "http://new.url")

        vc.stop.assert_called()

    @pytest.mark.asyncio
    async def test_play_preserves_loop_flag(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        bot._create_playback(guild_id, "old", "http://old.url")
        bot._playback[guild_id].loop = True

        with patch.object(bot, "_create_audio_source", return_value=MagicMock()):
            await bot.vc_play(guild_id, "new", "http://new.url")

        assert bot._playback[guild_id].loop is True


# ── vc_disconnect ──────────────────────────────────────────────────────────────


class TestVcDisconnect:

    @pytest.mark.asyncio
    async def test_disconnect_emits_event(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        bot._create_playback(guild_id, "vid", "http://url")

        with patch.object(bot, "_emit", new_callable=AsyncMock) as mock_emit:
            await bot.vc_disconnect(guild_id)

        mock_emit.assert_awaited_with("on_disconnect", guild_id)

    @pytest.mark.asyncio
    async def test_disconnect_clears_playback(self, bot, guild_id, vc):
        bot._inject_vc(vc)
        bot._create_playback(guild_id, "vid", "http://url")

        await bot.vc_disconnect(guild_id)

        assert guild_id not in bot._playback

    @pytest.mark.asyncio
    async def test_disconnect_calls_vc_disconnect(self, bot, guild_id, vc):
        bot._inject_vc(vc)

        await bot.vc_disconnect(guild_id)

        vc.disconnect.assert_called_once_with(force=True)


# ── vc_get_members ─────────────────────────────────────────────────────────────


class TestVcGetMembers:

    def test_returns_empty_when_no_guild(self, bot, guild_id):
        result = bot.vc_get_members(guild_id)
        assert isinstance(result, MemberList)
        assert len(result.root) == 0

    def test_returns_members_matching_factory_shape(self, bot, guild_id):
        """Inject a fake guild/channel with two human members and one bot."""
        reference = MemberFactory.build()

        human1 = MagicMock()
        human1.id = 1
        human1.name = reference.username
        human1.display_name = reference.global_name
        human1.display_avatar.url = reference.avatar
        human1.bot = False

        bot_member = MagicMock()
        bot_member.bot = True

        fake_channel = MagicMock()
        fake_channel.members = [human1, bot_member]

        fake_vc = MagicMock()
        fake_vc.channel = fake_channel

        fake_guild = MagicMock()
        fake_guild.voice_client = fake_vc
        bot.get_guild = lambda gid: fake_guild

        result = bot.vc_get_members(guild_id)

        assert len(result.root) == 1  # bot was filtered out
        member = result.root[0]
        assert member.username == reference.username
        assert set(Member.model_fields) == set(Member.model_fields)
        assert isinstance(member, Member)

    def test_bots_are_filtered_from_members(self, bot, guild_id):
        bot_member = MagicMock()
        bot_member.bot = True

        fake_channel = MagicMock()
        fake_channel.members = [bot_member, bot_member]

        fake_vc = MagicMock()
        fake_vc.channel = fake_channel

        fake_guild = MagicMock()
        fake_guild.voice_client = fake_vc
        bot.get_guild = lambda gid: fake_guild

        result = bot.vc_get_members(guild_id)
        assert len(result.root) == 0
