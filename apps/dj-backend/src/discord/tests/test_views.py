from django.test import TestCase
from django.shortcuts import reverse
from rest_framework.test import APIClient
from rest_framework import status

from unittest import mock
from model_bakery import baker
from django.contrib.auth import get_user_model

from backend.test_utils import internal_client
from discord.models import DiscordUser, DiscordGuild, GuildQueue, GuildQueueItem
from youtube.models import YoutubeVideo

User = get_user_model()


class DiscordProfileViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.discord_user = baker.make(DiscordUser, user=self.user, discord_id="123", global_name="Test User")
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_get_profile(self):
        response = self.client.get(reverse("discord:profile"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["discord_id"], "123")
        self.assertEqual(response.data["global_name"], "Test User")

    def test_get_profile_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("discord:profile"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class DiscordGuildViewTests(TestCase):
    def setUp(self):
        self.user = baker.make(User)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)
        self.guild = baker.make(DiscordGuild, guild_id="guild_123")

    def test_get_guild(self):
        response = self.client.get(reverse("discord:guild", kwargs={"guild_id": "guild_123"}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["guild_id"], "guild_123")

    def test_get_guild_not_found(self):
        response = self.client.get(reverse("discord:guild", kwargs={"guild_id": "nonexistent"}))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)

    def test_get_guild_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(reverse("discord:guild", kwargs={"guild_id": "guild_123"}))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class GuildQueueViewTests(TestCase):
    def setUp(self):
        self.client = internal_client()
        self.guild = baker.make(DiscordGuild, guild_id="guild_123")
        self.queue = baker.make(GuildQueue, guild=self.guild)

    def test_get_queue(self):
        response = self.client.get(reverse("discord:guild-queue", kwargs={"guild_id": "guild_123"}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_queue_creates_guild_and_queue_if_missing(self):
        response = self.client.get(reverse("discord:guild-queue", kwargs={"guild_id": "new_guild"}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(DiscordGuild.objects.filter(guild_id="new_guild").exists())
        self.assertTrue(GuildQueue.objects.filter(guild__guild_id="new_guild").exists())

    def test_clear_queue(self):
        video = baker.make(YoutubeVideo)
        baker.make(GuildQueueItem, queue=self.queue, video=video, order=1)
        baker.make(GuildQueueItem, queue=self.queue, video=video, order=2)

        response = self.client.delete(reverse("discord:guild-queue", kwargs={"guild_id": "guild_123"}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.queue.items.count(), 0)

    def test_requires_internal_key(self):
        client = APIClient()
        response = client.get(reverse("discord:guild-queue", kwargs={"guild_id": "guild_123"}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_wrong_internal_key_rejected(self):
        client = APIClient()
        client.credentials(HTTP_X_INTERNAL_KEY="wrong-key")
        response = client.get(reverse("discord:guild-queue", kwargs={"guild_id": "guild_123"}))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class GuildQueueItemViewTests(TestCase):
    def setUp(self):
        self.client = internal_client()
        self.discord_user = baker.make(DiscordUser, discord_id="user_123")
        self.guild = baker.make(DiscordGuild, guild_id="guild_123")
        self.queue = baker.make(GuildQueue, guild=self.guild)
        self.video = baker.make(YoutubeVideo, youtube_id="vid_1")

    def test_add_existing_video(self):
        response = self.client.post(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"youtube_id": self.video.youtube_id, "discord_id": self.discord_user.discord_id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.queue.items.count(), 1)
        self.assertEqual(GuildQueueItem.objects.count(), 1)

    def test_add_video_sets_added_by(self):
        response = self.client.post(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"youtube_id": self.video.youtube_id, "discord_id": self.discord_user.discord_id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        item = GuildQueueItem.objects.get()
        self.assertEqual(item.added_by, self.discord_user)

    def test_add_video_missing_youtube_id(self):
        response = self.client.post(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"discord_id": self.discord_user.discord_id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GuildQueueItem.objects.count(), 0)
        self.assertIn("error", response.data)

    def test_add_video_missing_discord_id(self):
        response = self.client.post(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"youtube_id": self.video.youtube_id},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(GuildQueueItem.objects.count(), 0)
        self.assertIn("error", response.data)

    def test_add_video_unauthenticated_discord_user(self):
        response = self.client.post(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"youtube_id": self.video.youtube_id, "discord_id": "unknown_user"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(GuildQueueItem.objects.count(), 0)
        self.assertIn("error", response.data)

    @mock.patch("discord.models.YouTubeService.fetch_and_cache_video")
    def test_add_video_auto_fetches_if_not_in_db(self, mock_fetch):
        mock_fetch.side_effect = lambda youtube_id: baker.make(YoutubeVideo, youtube_id=youtube_id)

        response = self.client.post(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"youtube_id": "unseen_vid", "discord_id": self.discord_user.discord_id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(GuildQueueItem.objects.count(), 1)
        mock_fetch.assert_called_once_with("unseen_vid")

    @mock.patch("discord.models.YouTubeService.fetch_and_cache_video")
    def test_add_video_returns_502_if_fetch_fails(self, mock_fetch):
        mock_fetch.side_effect = Exception("fetch failed")

        response = self.client.post(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"youtube_id": "bad_vid", "discord_id": self.discord_user.discord_id},
        )
        self.assertEqual(response.status_code, status.HTTP_502_BAD_GATEWAY)
        self.assertEqual(GuildQueueItem.objects.count(), 0)
        self.assertIn("error", response.data)

    def test_add_video_order_increments(self):
        baker.make(GuildQueueItem, queue=self.queue, video=self.video, order=1)
        video2 = baker.make(YoutubeVideo, youtube_id="vid_2")

        response = self.client.post(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"youtube_id": video2.youtube_id, "discord_id": self.discord_user.discord_id},
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        new_item = GuildQueueItem.objects.get(video=video2)
        self.assertEqual(new_item.order, 2)

    def test_remove_item(self):
        item = baker.make(GuildQueueItem, queue=self.queue, video=self.video, order=1)

        response = self.client.delete(
            reverse("discord:guild-queue-item", kwargs={"guild_id": "guild_123", "item_id": item.id})
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(GuildQueueItem.objects.count(), 0)
        self.assertFalse(GuildQueueItem.objects.filter(id=item.id).exists())

    def test_remove_item_not_found(self):
        response = self.client.delete(
            reverse("discord:guild-queue-item", kwargs={"guild_id": "guild_123", "item_id": 99999})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(GuildQueueItem.objects.count(), 0)

    def test_remove_item_wrong_guild(self):
        other_guild = baker.make(DiscordGuild, guild_id="other_guild")
        other_queue = baker.make(GuildQueue, guild=other_guild)
        item = baker.make(GuildQueueItem, queue=other_queue, video=self.video, order=1)

        response = self.client.delete(
            reverse("discord:guild-queue-item", kwargs={"guild_id": "guild_123", "item_id": item.id})
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_reorder_items(self):
        item1 = baker.make(GuildQueueItem, queue=self.queue, video=self.video, order=1)
        video2 = baker.make(YoutubeVideo, youtube_id="vid_2")
        item2 = baker.make(GuildQueueItem, queue=self.queue, video=video2, order=2)

        response = self.client.patch(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"order": [item2.id, item1.id]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        item1.refresh_from_db()
        item2.refresh_from_db()
        self.assertEqual(item2.order, 1)
        self.assertEqual(item1.order, 2)

    def test_reorder_missing_order(self):
        response = self.client.patch(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_reorder_invalid_item_ids(self):
        response = self.client.patch(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"order": [99999, 88888]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)

    def test_reorder_items_from_wrong_guild_rejected(self):
        other_guild = baker.make(DiscordGuild, guild_id="other_guild")
        other_queue = baker.make(GuildQueue, guild=other_guild)
        other_item = baker.make(GuildQueueItem, queue=other_queue, video=self.video, order=1)

        response = self.client.patch(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"order": [other_item.id]},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_requires_internal_key(self):
        client = APIClient()
        response = client.post(
            reverse("discord:guild-queue-items", kwargs={"guild_id": "guild_123"}),
            {"youtube_id": "vid_1"},
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
