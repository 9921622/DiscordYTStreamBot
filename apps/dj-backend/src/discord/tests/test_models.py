from django.test import TestCase
from unittest import mock
from model_bakery import baker

from discord.models import DiscordUser, DiscordGuild, GuildQueue, GuildQueueItem
from youtube.models import YoutubeVideo


class GuildQueueManagerGetForGuildTests(TestCase):

    def test_creates_guild_and_queue_if_missing(self):
        queue = GuildQueue.objects.get_for_guild("new_guild")
        self.assertIsInstance(queue, GuildQueue)
        self.assertTrue(DiscordGuild.objects.filter(guild_id="new_guild").exists())

    def test_returns_existing_queue(self):
        guild = baker.make(DiscordGuild, guild_id="guild_123")
        existing_queue = baker.make(GuildQueue, guild=guild)

        queue = GuildQueue.objects.get_for_guild("guild_123")
        self.assertEqual(queue.pk, existing_queue.pk)

    def test_does_not_duplicate_queue(self):
        baker.make(DiscordGuild, guild_id="guild_123")
        GuildQueue.objects.get_for_guild("guild_123")
        GuildQueue.objects.get_for_guild("guild_123")
        self.assertEqual(GuildQueue.objects.filter(guild__guild_id="guild_123").count(), 1)


class GuildQueueManagerAddItemTests(TestCase):

    def setUp(self):
        self.guild = baker.make(DiscordGuild, guild_id="guild_123")
        self.queue = baker.make(GuildQueue, guild=self.guild)
        self.video = baker.make(YoutubeVideo, youtube_id="vid_1")
        self.discord_user = baker.make(DiscordUser)

    def test_adds_existing_video(self):
        item = GuildQueue.objects.add_item("guild_123", "vid_1")
        self.assertIsInstance(item, GuildQueueItem)
        self.assertEqual(item.video, self.video)
        self.assertEqual(self.queue.items.count(), 1)

    def test_order_starts_at_one(self):
        item = GuildQueue.objects.add_item("guild_123", "vid_1")
        self.assertEqual(item.order, 1)

    def test_order_increments(self):
        video2 = baker.make(YoutubeVideo, youtube_id="vid_2")
        baker.make(GuildQueueItem, queue=self.queue, video=self.video, order=1)

        item = GuildQueue.objects.add_item("guild_123", "vid_2")
        self.assertEqual(item.order, 2)

    def test_added_by_is_set(self):
        item = GuildQueue.objects.add_item("guild_123", "vid_1", added_by=self.discord_user)
        self.assertEqual(item.added_by, self.discord_user)

    def test_added_by_defaults_to_none(self):
        item = GuildQueue.objects.add_item("guild_123", "vid_1")
        self.assertIsNone(item.added_by)

    def test_raises_if_video_not_found_and_no_fetch(self):
        with self.assertRaises(YoutubeVideo.DoesNotExist):
            GuildQueue.objects.add_item("guild_123", "nonexistent")

    @mock.patch("discord.models.YouTubeService.fetch_and_cache_video")
    def test_fetches_and_caches_video_when_fetch_true(self, mock_fetch):
        mock_fetch.side_effect = lambda youtube_id: baker.make(YoutubeVideo, youtube_id=youtube_id)

        item = GuildQueue.objects.add_item("guild_123", "new_vid", fetch=True)
        self.assertIsInstance(item, GuildQueueItem)
        mock_fetch.assert_called_once_with("new_vid")

    @mock.patch("discord.models.YouTubeService.fetch_and_cache_video")
    def test_fetch_exception_propagates(self, mock_fetch):
        mock_fetch.side_effect = Exception("yt-dlp failed")

        with self.assertRaises(Exception, msg="yt-dlp failed"):
            GuildQueue.objects.add_item("guild_123", "bad_vid", fetch=True)


class GuildQueueManagerRemoveItemTests(TestCase):

    def setUp(self):
        self.guild = baker.make(DiscordGuild, guild_id="guild_123")
        self.queue = baker.make(GuildQueue, guild=self.guild)
        self.video = baker.make(YoutubeVideo, youtube_id="vid_1")

    def test_removes_item(self):
        item = baker.make(GuildQueueItem, queue=self.queue, video=self.video, order=1)
        GuildQueue.objects.remove_item("guild_123", item.id)
        self.assertFalse(GuildQueueItem.objects.filter(id=item.id).exists())

    def test_raises_if_item_not_found(self):
        with self.assertRaises(GuildQueueItem.DoesNotExist):
            GuildQueue.objects.remove_item("guild_123", 99999)

    def test_raises_if_item_belongs_to_different_guild(self):
        other_guild = baker.make(DiscordGuild, guild_id="other_guild")
        other_queue = baker.make(GuildQueue, guild=other_guild)
        item = baker.make(GuildQueueItem, queue=other_queue, video=self.video, order=1)

        with self.assertRaises(GuildQueueItem.DoesNotExist):
            GuildQueue.objects.remove_item("guild_123", item.id)


class GuildQueueManagerReorderItemsTests(TestCase):

    def setUp(self):
        self.guild = baker.make(DiscordGuild, guild_id="guild_123")
        self.queue = baker.make(GuildQueue, guild=self.guild)
        self.video = baker.make(YoutubeVideo, youtube_id="vid_1")

    def test_reorders_items(self):
        item1 = baker.make(GuildQueueItem, queue=self.queue, video=self.video, order=1)
        video2 = baker.make(YoutubeVideo, youtube_id="vid_2")
        item2 = baker.make(GuildQueueItem, queue=self.queue, video=video2, order=2)

        GuildQueue.objects.reorder_items("guild_123", [item2.id, item1.id])

        item1.refresh_from_db()
        item2.refresh_from_db()
        self.assertEqual(item2.order, 1)
        self.assertEqual(item1.order, 2)

    def test_raises_if_item_id_invalid(self):
        with self.assertRaises(ValueError, msg="One or more item IDs are invalid"):
            GuildQueue.objects.reorder_items("guild_123", [99999])

    def test_raises_if_item_belongs_to_different_guild(self):
        other_guild = baker.make(DiscordGuild, guild_id="other_guild")
        other_queue = baker.make(GuildQueue, guild=other_guild)
        item = baker.make(GuildQueueItem, queue=other_queue, video=self.video, order=1)

        with self.assertRaises(ValueError):
            GuildQueue.objects.reorder_items("guild_123", [item.id])

    def test_single_item_gets_order_one(self):
        item = baker.make(GuildQueueItem, queue=self.queue, video=self.video, order=5)
        GuildQueue.objects.reorder_items("guild_123", [item.id])
        item.refresh_from_db()
        self.assertEqual(item.order, 1)
