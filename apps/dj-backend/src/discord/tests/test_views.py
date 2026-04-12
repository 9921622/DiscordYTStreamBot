from django.test import TestCase
from django.urls import reverse
from unittest import mock
from rest_framework.test import APIClient
from model_bakery import baker

from backend.test_utils import internal_client

from discord.models import GuildPlaylist, GuildPlaylistItem, DiscordUser
from youtube.models import YoutubeVideo

GUILD_ID = "123456789"


# ---------------------------------------------------------------------------
# GuildPlaylistView  (GET, DELETE)
# ---------------------------------------------------------------------------


class GuildPlaylistViewTests(TestCase):

    def setUp(self):
        self.client = internal_client()
        self.url = reverse("discord:guild-playlist", kwargs={"guild_id": GUILD_ID})

    @mock.patch("discord.views.GuildPlaylistSerializer")
    @mock.patch("discord.views.GuildPlaylist.objects.get_playlist")
    def test_get_returns_queue(self, mock_get_playlist, mock_serializer):
        mock_queue = mock.Mock()
        mock_get_playlist.return_value = mock_queue
        mock_serializer.return_value.data = {"items": []}

        response = self.client.get(self.url)

        mock_get_playlist.assert_called_once_with(GUILD_ID)
        mock_serializer.assert_called_once_with(mock_queue)
        self.assertEqual(response.status_code, 200)

    @mock.patch("discord.views.GuildPlaylistSerializer")
    @mock.patch("discord.views.GuildPlaylist.objects.get_playlist")
    @mock.patch("discord.views.GuildPlaylist.objects.clear")
    def test_delete_clears_and_returns_queue(self, mock_clear, mock_get_playlist, mock_serializer):
        mock_queue = mock.Mock()
        mock_get_playlist.return_value = mock_queue
        mock_serializer.return_value.data = {"items": []}

        response = self.client.delete(self.url)

        mock_clear.assert_called_once_with(GUILD_ID)
        mock_get_playlist.assert_called_once_with(GUILD_ID)
        self.assertEqual(response.status_code, 200)

    def test_get_requires_internal_auth(self):
        response = APIClient().get(self.url)
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# GuildPlaylistAddSongView  (PATCH)
# ---------------------------------------------------------------------------


class GuildPlaylistAddSongViewTests(TestCase):

    def setUp(self):
        self.client = internal_client()
        self.url = reverse("discord:guild-playlist-add-song", kwargs={"guild_id": GUILD_ID})
        self.user = baker.make(DiscordUser, discord_id="user_001")

    # --- validation errors --------------------------------------------------

    def test_missing_youtube_id_returns_400(self):
        response = self.client.patch(self.url, {"discord_id": self.user.discord_id}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("youtube_id", response.data["error"])

    def test_missing_discord_id_returns_400(self):
        response = self.client.patch(self.url, {"youtube_id": "abc123"}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("discord_id", response.data["error"])

    def test_unknown_discord_user_returns_403(self):
        response = self.client.patch(
            self.url,
            {"youtube_id": "abc123", "discord_id": "nonexistent"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)

    # --- success: video already cached --------------------------------------

    @mock.patch("discord.views.GuildPlaylistSerializer")
    @mock.patch("discord.views.GuildPlaylist.objects.get_playlist")
    @mock.patch("discord.views.GuildPlaylist.objects.add_item")
    def test_add_existing_video_returns_201(self, mock_add_item, mock_get_playlist, mock_serializer):
        mock_get_playlist.return_value = mock.Mock()
        mock_serializer.return_value.data = {"items": []}

        response = self.client.patch(
            self.url,
            {"youtube_id": "abc123", "discord_id": self.user.discord_id},
            format="json",
        )

        mock_add_item.assert_called_once_with(GUILD_ID, "abc123", added_by=self.user)
        self.assertEqual(response.status_code, 201)

    # --- success: video not cached, fetch succeeds --------------------------

    @mock.patch("discord.views.GuildPlaylistSerializer")
    @mock.patch("discord.views.GuildPlaylist.objects.get_playlist")
    @mock.patch("discord.views.GuildPlaylist.objects.add_item")
    def test_add_fetches_video_when_not_cached(self, mock_add_item, mock_get_playlist, mock_serializer):
        mock_add_item.side_effect = [YoutubeVideo.DoesNotExist, None]
        mock_get_playlist.return_value = mock.Mock()
        mock_serializer.return_value.data = {"items": []}

        response = self.client.patch(
            self.url,
            {"youtube_id": "new_vid", "discord_id": self.user.discord_id},
            format="json",
        )

        self.assertEqual(mock_add_item.call_count, 2)
        # second call must include fetch=True
        _, kwargs = mock_add_item.call_args
        self.assertTrue(kwargs.get("fetch"))
        self.assertEqual(response.status_code, 201)

    # --- exception: fetch fails ---------------------------------------------

    @mock.patch("discord.views.GuildPlaylist.objects.add_item")
    def test_youtube_fetch_failure_returns_502(self, mock_add_item):
        mock_add_item.side_effect = [YoutubeVideo.DoesNotExist, Exception("network error")]

        response = self.client.patch(
            self.url,
            {"youtube_id": "bad_vid", "discord_id": self.user.discord_id},
            format="json",
        )

        self.assertEqual(response.status_code, 502)
        self.assertIn("Failed to fetch", response.data["error"])

    def test_requires_internal_auth(self):
        response = APIClient().patch(self.url, {}, format="json")
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# GuildPlaylistRemoveSongView  (PATCH)
# ---------------------------------------------------------------------------


class GuildPlaylistRemoveSongViewTests(TestCase):

    def setUp(self):
        self.client = internal_client()
        self.url = reverse("discord:guild-playlist-remove-song", kwargs={"guild_id": GUILD_ID})

    def test_missing_item_id_returns_400(self):
        response = self.client.patch(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertIn("item_id", response.data["error"])

    @mock.patch("discord.views.GuildPlaylist.objects.remove_item")
    def test_item_not_found_returns_404(self, mock_remove):
        mock_remove.side_effect = GuildPlaylistItem.DoesNotExist

        response = self.client.patch(self.url, {"item_id": 999}, format="json")

        self.assertEqual(response.status_code, 404)
        self.assertIn("not found", response.data["error"])

    @mock.patch("discord.views.GuildPlaylistSerializer")
    @mock.patch("discord.views.GuildPlaylist.objects.get_playlist")
    @mock.patch("discord.views.GuildPlaylist.objects.remove_item")
    def test_remove_success_returns_200(self, mock_remove, mock_get_playlist, mock_serializer):
        mock_get_playlist.return_value = mock.Mock()
        mock_serializer.return_value.data = {"items": []}

        response = self.client.patch(self.url, {"item_id": 1}, format="json")

        mock_remove.assert_called_once_with(GUILD_ID, 1)
        self.assertEqual(response.status_code, 200)

    def test_requires_internal_auth(self):
        response = APIClient().patch(self.url, {}, format="json")
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# GuildPlaylistNextView  (PATCH)
# ---------------------------------------------------------------------------


class GuildPlaylistNextViewTests(TestCase):

    def setUp(self):
        self.client = internal_client()
        self.url = reverse("discord:guild-playlist-next", kwargs={"guild_id": GUILD_ID})

    @mock.patch("discord.views.GuildPlaylistSerializer")
    @mock.patch("discord.views.GuildPlaylist.objects.get_playlist")
    @mock.patch("discord.views.GuildPlaylist.objects.next_item")
    @mock.patch("discord.views.GuildPlaylistItem.objects.get")
    def test_next_by_item_id(self, mock_item_get, mock_next, mock_get_playlist, mock_serializer):
        playlist_item = mock.Mock()
        mock_item_get.return_value = playlist_item
        mock_get_playlist.return_value = mock.Mock()
        mock_serializer.return_value.data = {}

        response = self.client.patch(self.url, {"item_id": 42}, format="json")

        mock_next.assert_called_once_with(GUILD_ID, playlist_item=playlist_item)
        self.assertEqual(response.status_code, 200)

    @mock.patch("discord.views.GuildPlaylistItem.objects.get")
    def test_next_by_item_id_not_found_returns_404(self, mock_item_get):
        mock_item_get.side_effect = GuildPlaylistItem.DoesNotExist

        response = self.client.patch(self.url, {"item_id": 99}, format="json")

        self.assertEqual(response.status_code, 404)

    @mock.patch("discord.views.GuildPlaylistSerializer")
    @mock.patch("discord.views.GuildPlaylist.objects.get_playlist")
    @mock.patch("discord.views.GuildPlaylist.objects.next_item")
    def test_next_natural_advance(self, mock_next, mock_get_playlist, mock_serializer):
        mock_get_playlist.return_value = mock.Mock()
        mock_serializer.return_value.data = {}

        response = self.client.patch(self.url, {}, format="json")

        mock_next.assert_called_once_with(GUILD_ID)
        self.assertEqual(response.status_code, 200)

    def test_requires_internal_auth(self):
        response = APIClient().patch(self.url, {}, format="json")
        self.assertEqual(response.status_code, 403)


class GuildPlaylistPlayNowViewTests(TestCase):

    def setUp(self):
        self.client = internal_client()
        self.discord_user = baker.make(DiscordUser)
        self.url = reverse("discord:guild-playlist-play-now", kwargs={"guild_id": GUILD_ID})

    @mock.patch("discord.views.GuildPlaylistSerializer")
    @mock.patch("discord.views.GuildPlaylist.objects.get_playlist")
    @mock.patch("discord.views.GuildPlaylist.objects.next_item_as_video")
    @mock.patch("discord.views.YouTubeService.get_or_fetch")
    def test_play_now(self, mock_get_or_fetch, mock_next, mock_get_playlist, mock_serializer):
        video = mock.Mock()
        mock_get_or_fetch.return_value = video
        mock_get_playlist.return_value = mock.Mock()
        mock_serializer.return_value.data = {}

        response = self.client.patch(
            self.url, {"video_id": "vid_abc", "discord_id": self.discord_user.discord_id}, format="json"
        )

        mock_next.assert_called_once_with(GUILD_ID, video=video, added_by=self.discord_user)
        self.assertEqual(response.status_code, 200)

    def test_play_now_missing_video_id_returns_400(self):
        response = self.client.patch(self.url, {"discord_id": self.discord_user.discord_id}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_play_now_missing_discord_id_returns_400(self):
        response = self.client.patch(self.url, {"video_id": "vid_abc"}, format="json")
        self.assertEqual(response.status_code, 400)

    @mock.patch("discord.views.YouTubeService.get_or_fetch")
    def test_play_now_discord_user_not_found_returns_404(self, mock_get_or_fetch):
        mock_get_or_fetch.return_value = mock.Mock()

        response = self.client.patch(self.url, {"video_id": "vid_abc", "discord_id": "nonexistent"}, format="json")
        self.assertEqual(response.status_code, 404)

    def test_requires_internal_auth(self):
        response = APIClient().patch(self.url, {}, format="json")
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# GuildPlaylistPrevView  (PATCH)
# ---------------------------------------------------------------------------


class GuildPlaylistPrevViewTests(TestCase):

    def setUp(self):
        self.client = internal_client()
        self.url = reverse("discord:guild-playlist-prev", kwargs={"guild_id": GUILD_ID})

    @mock.patch("discord.views.GuildPlaylistSerializer")
    @mock.patch("discord.views.GuildPlaylist.objects.get_playlist")
    @mock.patch("discord.views.GuildPlaylist.objects.prev_item")
    def test_prev_advances_and_returns_queue(self, mock_prev, mock_get_playlist, mock_serializer):
        mock_get_playlist.return_value = mock.Mock()
        mock_serializer.return_value.data = {}

        response = self.client.patch(self.url)

        mock_prev.assert_called_once_with(GUILD_ID)
        mock_get_playlist.assert_called_once_with(GUILD_ID)
        self.assertEqual(response.status_code, 200)

    def test_requires_internal_auth(self):
        response = APIClient().patch(self.url)
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# GuildPlaylistReorderView  (PATCH)
# ---------------------------------------------------------------------------


class GuildPlaylistReorderViewTests(TestCase):

    def setUp(self):
        self.client = internal_client()
        self.url = reverse("discord:guild-playlist-reorder", kwargs={"guild_id": GUILD_ID})

    def test_missing_order_returns_400(self):
        response = self.client.patch(self.url, {}, format="json")
        self.assertEqual(response.status_code, 400)

    def test_non_list_order_returns_400(self):
        response = self.client.patch(self.url, {"order": "not-a-list"}, format="json")
        self.assertEqual(response.status_code, 400)

    @mock.patch("discord.views.GuildPlaylist.objects.reorder_items")
    def test_invalid_ids_propagate_value_error_as_400(self, mock_reorder):
        mock_reorder.side_effect = ValueError("Item IDs do not match queue")

        response = self.client.patch(self.url, {"order": [1, 2, 3]}, format="json")

        self.assertEqual(response.status_code, 400)
        self.assertIn("Item IDs do not match queue", response.data["error"])

    @mock.patch("discord.views.GuildPlaylistSerializer")
    @mock.patch("discord.views.GuildPlaylist.objects.get_playlist")
    @mock.patch("discord.views.GuildPlaylist.objects.reorder_items")
    def test_reorder_success_returns_200(self, mock_reorder, mock_get_playlist, mock_serializer):
        mock_get_playlist.return_value = mock.Mock()
        mock_serializer.return_value.data = {"items": []}

        response = self.client.patch(self.url, {"order": [3, 1, 2]}, format="json")

        mock_reorder.assert_called_once_with(GUILD_ID, [3, 1, 2])
        self.assertEqual(response.status_code, 200)

    def test_requires_internal_auth(self):
        response = APIClient().patch(self.url, {"order": [1]}, format="json")
        self.assertEqual(response.status_code, 403)
