from django.test import TestCase
from unittest import mock
from model_bakery import baker

from youtube.models import YoutubeVideo
from discord.models import GuildPlaylist, GuildPlaylistItem, DiscordUser, DiscordGuild


class GuildPlaylistManagerGetForGuildTest(TestCase):
    def test_creates_guild_and_playlist_if_not_exist(self):
        playlist = GuildPlaylist.objects.get_for_guild("guild_123")

        self.assertIsNotNone(playlist)
        self.assertEqual(playlist.guild.guild_id, "guild_123")

    def test_returns_existing_playlist(self):
        playlist1 = GuildPlaylist.objects.get_for_guild("guild_123")
        playlist2 = GuildPlaylist.objects.get_for_guild("guild_123")

        self.assertEqual(playlist1.pk, playlist2.pk)


class GuildPlaylistManagerAddItemTest(TestCase):
    def test_add_item_without_fetch(self):
        video = baker.make(YoutubeVideo, youtube_id="abc123")
        item = GuildPlaylist.objects.add_item("guild_1", "abc123", fetch=False)

        self.assertEqual(item.video, video)
        self.assertEqual(item.order, 1)
        self.assertIsNone(item.added_by)

    def test_add_item_sets_added_by(self):
        baker.make(YoutubeVideo, youtube_id="abc123")
        user = baker.make(DiscordUser)
        item = GuildPlaylist.objects.add_item("guild_1", "abc123", added_by=user, fetch=False)

        self.assertEqual(item.added_by, user)

    def test_add_item_increments_order(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")

        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        self.assertEqual(item1.order, 1)
        self.assertEqual(item2.order, 2)

    def test_add_item_with_fetch_calls_youtube_service(self):
        video = baker.make(YoutubeVideo, youtube_id="abc123")

        with mock.patch("discord.models.YouTubeService.fetch_and_cache_video", return_value=video) as mock_fetch:
            item = GuildPlaylist.objects.add_item("guild_1", "abc123", fetch=True)
            mock_fetch.assert_called_once_with("abc123")

        self.assertEqual(item.video, video)


class GuildPlaylistManagerRemoveItemTest(TestCase):
    def test_remove_item_deletes_it(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item_id = item.id

        GuildPlaylist.objects.remove_item("guild_1", item_id)

        self.assertFalse(GuildPlaylistItem.objects.filter(id=item_id).exists())

    def test_remove_current_item_advances_to_next(self):

        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")

        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        GuildPlaylist.objects.remove_item("guild_1", item1.id)

        playlist.refresh_from_db()
        self.assertEqual(playlist.current_item, item2)

    def test_remove_current_item_sets_none_if_no_next(self):
        from discord.models import GuildPlaylist

        baker.make(YoutubeVideo, youtube_id="vid1")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        GuildPlaylist.objects.remove_item("guild_1", item1.id)

        playlist.refresh_from_db()
        self.assertIsNone(playlist.current_item)

    def test_remove_item_wrong_guild_raises(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        with self.assertRaises(GuildPlaylistItem.DoesNotExist):
            GuildPlaylist.objects.remove_item("guild_999", item.id)


class GuildPlaylistManagerReorderItemsTest(TestCase):
    def test_reorder_items(self):

        for vid in ["vid1", "vid2", "vid3"]:
            baker.make(YoutubeVideo, youtube_id=vid)

        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)
        item3 = GuildPlaylist.objects.add_item("guild_1", "vid3", fetch=False)

        GuildPlaylist.objects.reorder_items("guild_1", [item3.id, item1.id, item2.id])

        item1.refresh_from_db()
        item2.refresh_from_db()
        item3.refresh_from_db()

        self.assertEqual(item3.order, 1)
        self.assertEqual(item1.order, 2)
        self.assertEqual(item2.order, 3)

    def test_reorder_invalid_ids_raises(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        with self.assertRaises(ValueError):
            GuildPlaylist.objects.reorder_items("guild_1", [99999])


class GuildPlaylistManagerNextItemTest(TestCase):
    def test_next_item_from_none_returns_first(self):

        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        result = GuildPlaylist.objects.next_item("guild_1")

        self.assertEqual(result, item1)

    def test_next_item_advances_to_next(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        result = GuildPlaylist.objects.next_item("guild_1")

        self.assertEqual(result, item2)

    def test_next_item_at_end_returns_none(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        result = GuildPlaylist.objects.next_item("guild_1")

        self.assertIsNone(result)

    def test_next_item_updates_current_item(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        GuildPlaylist.objects.next_item("guild_1")

        playlist.refresh_from_db()
        self.assertEqual(playlist.current_item, item2)


class GuildPlaylistManagerPrevItemTest(TestCase):
    def test_prev_item_from_none_returns_last(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        result = GuildPlaylist.objects.prev_item("guild_1")

        self.assertEqual(result, item2)

    def test_prev_item_goes_back(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.current_item = item2
        playlist.save(update_fields=["current_item"])

        result = GuildPlaylist.objects.prev_item("guild_1")

        self.assertEqual(result, item1)

    def test_prev_item_at_start_returns_none(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        result = GuildPlaylist.objects.prev_item("guild_1")

        self.assertIsNone(result)

    def test_prev_item_updates_current_item(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.current_item = item2
        playlist.save(update_fields=["current_item"])

        GuildPlaylist.objects.prev_item("guild_1")

        playlist.refresh_from_db()
        self.assertEqual(playlist.current_item, item1)


class GuildPlaylistModelTest(TestCase):
    def test_str(self):
        guild = baker.make(DiscordGuild, name="My Server")
        playlist = baker.make(GuildPlaylist, guild=guild)

        self.assertEqual(str(playlist), "Playlist for My Server")

    def test_clear_removes_all_items_and_resets_current(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)
        GuildPlaylist.objects.next_item("guild_1")  # set a current item

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.clear()
        playlist.refresh_from_db()

        self.assertIsNone(playlist.current_item)
        self.assertEqual(playlist.items.count(), 0)

    def test_next_returns_current_item(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.current_item = item
        playlist.save(update_fields=["current_item"])

        self.assertEqual(playlist.next(), item)

    def test_next_returns_none_when_no_current(self):
        playlist = GuildPlaylist.objects.get_for_guild("guild_1")

        self.assertIsNone(playlist.next())


class GuildPlaylistItemModelTest(TestCase):
    def test_str(self):
        baker.make(YoutubeVideo, youtube_id="vid1", title="Cool Video")
        item = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        item.playlist.guild.name = "My Guild"
        item.playlist.guild.save()

        self.assertIn("Cool Video", str(item))
        self.assertIn("My Guild", str(item))
