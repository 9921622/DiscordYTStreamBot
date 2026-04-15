from django.test import TestCase
from unittest import mock
from model_bakery import baker

from youtube.models import YoutubeVideo
from discord.models import GuildPlaylist, GuildPlaylistItem, DiscordUser, DiscordGuild


class GuildPlaylistManagerGetForGuildTest(TestCase):
    def test_creates_guild_and_playlist_if_not_exist(self):
        playlist = GuildPlaylist.objects.get_playlist("guild_123")

        self.assertIsNotNone(playlist)
        self.assertEqual(playlist.guild.guild_id, "guild_123")

    def test_returns_existing_playlist(self):
        playlist1 = GuildPlaylist.objects.get_playlist("guild_123")
        playlist2 = GuildPlaylist.objects.get_playlist("guild_123")

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

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        GuildPlaylist.objects.remove_item("guild_1", item1.id)

        playlist.refresh_from_db()
        self.assertEqual(playlist.current_item, item2)

    def test_remove_current_item_sets_none_if_no_next(self):
        from discord.models import GuildPlaylist

        baker.make(YoutubeVideo, youtube_id="vid1")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
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
    def setUp(self):
        self.user = baker.make(DiscordUser)

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

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        result = GuildPlaylist.objects.next_item("guild_1")

        self.assertEqual(result, item2)

    def test_next_item_at_end_returns_none(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        result = GuildPlaylist.objects.next_item("guild_1")

        self.assertIsNone(result)

    def test_next_item_updates_current_item(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        GuildPlaylist.objects.next_item("guild_1")

        playlist.refresh_from_db()
        self.assertEqual(playlist.current_item, item2)

    def test_next_item_as_video_creates(self):
        video = baker.make(YoutubeVideo, youtube_id="vid1")
        playlist = GuildPlaylist.objects.get_playlist("guild_1")

        item = GuildPlaylist.objects.next_item_as_video("guild_1", video, self.user)

        playlist.refresh_from_db()
        self.assertEqual(playlist.current_item, item)
        self.assertEqual(playlist.items.count(), 1)

    def test_next_item_with_explicit_playlist_item(self):
        """Passing a playlist_item directly sets that item as current, ignoring order."""
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        baker.make(YoutubeVideo, youtube_id="vid3")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)
        item3 = GuildPlaylist.objects.add_item("guild_1", "vid3", fetch=False)

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        # Skip item2, jump directly to item3
        result = GuildPlaylist.objects.next_item("guild_1", playlist_item=item3)

        self.assertEqual(result, item3)
        playlist.refresh_from_db()
        self.assertEqual(playlist.current_item, item3)

    def test_next_item_explicit_playlist_item_updates_db(self):
        """Explicit playlist_item is persisted to current_item in the DB."""
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        result = GuildPlaylist.objects.next_item("guild_1", playlist_item=item2)

        self.assertIsNotNone(result)
        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        self.assertEqual(playlist.current_item, item2)

    def test_next_item_empty_playlist_returns_none(self):
        """next_item on an empty playlist returns None and sets current_item to None."""
        result = GuildPlaylist.objects.next_item("guild_1")

        self.assertIsNone(result)
        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        self.assertIsNone(playlist.current_item)

    def test_next_item_as_video_is_not_none(self):
        """next_item_as_video never returns None — asserts internally and returns the item."""
        video = baker.make(YoutubeVideo, youtube_id="vid1")

        result = GuildPlaylist.objects.next_item_as_video("guild_1", video, self.user)

        self.assertIsNotNone(result)

    def test_next_item_as_video_appends_to_existing(self):
        """next_item_as_video adds a new item even when the playlist already has items."""
        baker.make(YoutubeVideo, youtube_id="vid1")
        GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        video2 = baker.make(YoutubeVideo, youtube_id="vid2")

        item = GuildPlaylist.objects.next_item_as_video("guild_1", video2, self.user)

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        self.assertEqual(playlist.items.count(), 2)
        self.assertEqual(playlist.current_item, item)
        self.assertIsNotNone(playlist.current_item)

    def test_next_item_as_video_current_item_is_not_none_after_call(self):
        """current_item is never None after next_item_as_video, regardless of prior state."""
        video = baker.make(YoutubeVideo, youtube_id="vid1")
        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        self.assertIsNone(playlist.current_item)  # confirm starting state

        GuildPlaylist.objects.next_item_as_video("guild_1", video, self.user)

        playlist.refresh_from_db()
        self.assertIsNotNone(playlist.current_item)

    def test_next_item_as_video_inserts_after_current_in_middle(self):
        """With 5 items and current on 2nd, new video is inserted at 3rd position."""
        [baker.make(YoutubeVideo, youtube_id=f"vid{i}") for i in range(1, 6)]
        items = [GuildPlaylist.objects.add_item("guild_1", f"vid{i}", fetch=False) for i in range(1, 6)]

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = items[1]  # 2nd item
        playlist.save(update_fields=["current_item"])

        new_video = baker.make(YoutubeVideo, youtube_id="vid_new")
        result = GuildPlaylist.objects.next_item_as_video("guild_1", new_video, self.user)

        playlist.refresh_from_db()
        self.assertEqual(playlist.current_item, result)
        self.assertEqual(result.video.youtube_id, "vid_new")
        self.assertEqual(result.order, 3)  # inserted at 3rd position

    def test_next_item_as_video_shifts_existing_items_up(self):
        """Items after the insertion point have their order incremented."""
        [baker.make(YoutubeVideo, youtube_id=f"vid{i}") for i in range(1, 4)]
        items = [GuildPlaylist.objects.add_item("guild_1", f"vid{i}", fetch=False) for i in range(1, 4)]

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = items[0]  # 1st item
        playlist.save(update_fields=["current_item"])

        new_video = baker.make(YoutubeVideo, youtube_id="vid_new")
        GuildPlaylist.objects.next_item_as_video("guild_1", new_video, self.user)

        items[1].refresh_from_db()
        items[2].refresh_from_db()
        self.assertEqual(items[1].order, 3)  # was 2, now 3
        self.assertEqual(items[2].order, 4)  # was 3, now 4

    def test_next_item_as_video_inserts_at_end_when_current_is_last(self):
        """When current is the last item, new video is appended at the end."""
        [baker.make(YoutubeVideo, youtube_id=f"vid{i}") for i in range(1, 4)]
        items = [GuildPlaylist.objects.add_item("guild_1", f"vid{i}", fetch=False) for i in range(1, 4)]

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = items[2]  # last item
        playlist.save(update_fields=["current_item"])

        new_video = baker.make(YoutubeVideo, youtube_id="vid_new")
        result = GuildPlaylist.objects.next_item_as_video("guild_1", new_video, self.user)

        self.assertEqual(result.order, 4)
        self.assertEqual(playlist.items.count(), 4)

    def test_next_item_as_video_inserts_at_start_when_no_current(self):
        """When current_item is None, new video is inserted at order 1."""
        [baker.make(YoutubeVideo, youtube_id=f"vid{i}") for i in range(1, 4)]
        items = [GuildPlaylist.objects.add_item("guild_1", f"vid{i}", fetch=False) for i in range(1, 4)]

        new_video = baker.make(YoutubeVideo, youtube_id="vid_new")
        result = GuildPlaylist.objects.next_item_as_video("guild_1", new_video, self.user)

        # No current item, so appended at end
        self.assertEqual(result.video.youtube_id, "vid_new")
        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        self.assertEqual(playlist.current_item, result)
        self.assertEqual(playlist.items.count(), 4)


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

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = item2
        playlist.save(update_fields=["current_item"])

        result = GuildPlaylist.objects.prev_item("guild_1")

        self.assertEqual(result, item1)

    def test_prev_item_at_start_returns_none(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = item1
        playlist.save(update_fields=["current_item"])

        result = GuildPlaylist.objects.prev_item("guild_1")

        self.assertIsNone(result)

    def test_prev_item_updates_current_item(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        baker.make(YoutubeVideo, youtube_id="vid2")
        item1 = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
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

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.clear()
        playlist.refresh_from_db()

        self.assertIsNone(playlist.current_item)
        self.assertEqual(playlist.items.count(), 0)

    def test_next_returns_current_item(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        playlist = GuildPlaylist.objects.get_playlist("guild_1")
        playlist.current_item = item
        playlist.save(update_fields=["current_item"])

        self.assertEqual(playlist.next(), item)

    def test_next_returns_none_when_no_current(self):
        playlist = GuildPlaylist.objects.get_playlist("guild_1")

        self.assertIsNone(playlist.next())


class GuildPlaylistItemModelTest(TestCase):
    def test_str(self):
        baker.make(YoutubeVideo, youtube_id="vid1", title="Cool Video")
        item = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        item.playlist.guild.name = "My Guild"
        item.playlist.guild.save()

        self.assertIn("Cool Video", str(item))
        self.assertIn("My Guild", str(item))
