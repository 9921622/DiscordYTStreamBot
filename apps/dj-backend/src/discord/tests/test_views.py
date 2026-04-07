from django.test import TestCase
from django.urls import reverse
from unittest import mock
from rest_framework.test import APIClient
from model_bakery import baker

from backend.test_utils import internal_client

from discord.models import GuildPlaylist, DiscordUser
from youtube.models import YoutubeVideo

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def playlist_url(guild_id):
    return reverse("discord:guild-playlist", kwargs={"guild_id": guild_id})


def playlist_items_url(guild_id):
    return reverse("discord:guild-playlist-items", kwargs={"guild_id": guild_id})


def playlist_item_url(guild_id, item_id):
    return reverse("discord:guild-playlist-item", kwargs={"guild_id": guild_id, "item_id": item_id})


def playlist_navigate_url(guild_id, direction):
    return reverse("discord:guild-playlist-navigate", kwargs={"guild_id": guild_id, "direction": direction})


# ---------------------------------------------------------------------------
# GuildPlaylistView  GET  /guilds/<guild_id>/playlist/
#                   DELETE /guilds/<guild_id>/playlist/
# ---------------------------------------------------------------------------


class GuildPlaylistViewGetTest(TestCase):
    def setUp(self):
        self.client = internal_client()

    def test_get_returns_200(self):
        response = self.client.get(playlist_url("guild_1"))
        self.assertEqual(response.status_code, 200)

    def test_get_creates_playlist_if_not_exist(self):
        response = self.client.get(playlist_url("new_guild"))
        self.assertEqual(response.status_code, 200)
        self.assertIn("items", response.data)

    def test_get_returns_serialized_queue(self):

        baker.make(YoutubeVideo, youtube_id="vid1")
        GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        response = self.client.get(playlist_url("guild_1"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["items"]), 1)

    def test_get_unauthenticated_returns_403(self):
        response = APIClient().get(playlist_url("guild_1"))
        self.assertEqual(response.status_code, 403)


class GuildPlaylistViewDeleteTest(TestCase):
    def setUp(self):
        self.client = internal_client()

    def test_delete_clears_queue(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        response = self.client.delete(playlist_url("guild_1"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"ok": True})

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        self.assertEqual(playlist.items.count(), 0)

    def test_delete_unauthenticated_returns_403(self):
        response = APIClient().delete(playlist_url("guild_1"))
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# GuildPlaylistNavigationView  POST /guilds/<guild_id>/playlist/<direction>/
# ---------------------------------------------------------------------------


class GuildPlaylistNavigationViewTest(TestCase):
    def setUp(self):
        self.client = internal_client()

    def test_next_advances_and_returns_item(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        response = self.client.post(playlist_navigate_url("guild_1", "next"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], item.id)

    def test_prev_returns_item(self):
        for vid in ["vid1", "vid2", "vid3"]:
            baker.make(YoutubeVideo, youtube_id=vid)
        GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)
        item2 = GuildPlaylist.objects.add_item("guild_1", "vid2", fetch=False)
        GuildPlaylist.objects.add_item("guild_1", "vid3", fetch=False)

        # Advance to vid3
        GuildPlaylist.objects.next_item("guild_1")
        GuildPlaylist.objects.next_item("guild_1")
        GuildPlaylist.objects.next_item("guild_1")

        # prev from vid3 goes back to vid2
        response = self.client.post(playlist_navigate_url("guild_1", "prev"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], item2.id)

    def test_next_at_end_returns_null_item(self):
        response = self.client.post(playlist_navigate_url("guild_1", "next"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"ok": True, "item": None})

    def test_prev_at_start_returns_null_item(self):

        baker.make(YoutubeVideo, youtube_id="vid1")
        item = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        playlist = GuildPlaylist.objects.get_for_guild("guild_1")
        playlist.current_item = item
        playlist.save(update_fields=["current_item"])

        response = self.client.post(playlist_navigate_url("guild_1", "prev"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"ok": True, "item": None})

    def test_invalid_direction_returns_400(self):
        response = self.client.post(playlist_navigate_url("guild_1", "sideways"))

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_unauthenticated_returns_403(self):
        response = APIClient().post(playlist_navigate_url("guild_1", "next"))
        self.assertEqual(response.status_code, 403)


# ---------------------------------------------------------------------------
# GuildPlaylistItemView  POST   /guilds/<guild_id>/playlist/items/
#                        DELETE /guilds/<guild_id>/playlist/items/<item_id>/
#                        PATCH  /guilds/<guild_id>/playlist/items/
# ---------------------------------------------------------------------------


class GuildPlaylistItemViewPostTest(TestCase):
    def setUp(self):
        self.client = internal_client()
        self.user = baker.make(DiscordUser, discord_id="user_1")

    def _post(self, guild_id="guild_1", youtube_id="vid1", discord_id="user_1"):
        return self.client.post(
            playlist_items_url(guild_id),
            {"youtube_id": youtube_id, "discord_id": discord_id},
            format="json",
        )

    def test_add_item_returns_201(self):
        baker.make(YoutubeVideo, youtube_id="vid1")

        response = self._post()

        self.assertEqual(response.status_code, 201)
        self.assertIn("id", response.data)

    def test_add_item_fetches_video_if_not_cached(self):
        fake_fetch = lambda youtube_id: baker.make(YoutubeVideo, youtube_id=youtube_id)

        with mock.patch("discord.models.YouTubeService.fetch_and_cache_video", side_effect=fake_fetch) as mock_fetch:
            response = self._post()
            mock_fetch.assert_called_once_with("vid1")

        self.assertEqual(response.status_code, 201)

    def test_add_item_missing_youtube_id_returns_400(self):
        response = self.client.post(
            playlist_items_url("guild_1"),
            {"discord_id": "user_1"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("youtube_id", response.data["error"])

    def test_add_item_missing_discord_id_returns_400(self):
        response = self.client.post(
            playlist_items_url("guild_1"),
            {"youtube_id": "vid1"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("discord_id", response.data["error"])

    def test_add_item_unknown_discord_user_returns_403(self):
        response = self._post(discord_id="unknown_user")

        self.assertEqual(response.status_code, 403)
        self.assertIn("authenticated", response.data["error"])

    def test_add_item_youtube_fetch_failure_returns_502(self):
        with mock.patch(
            "discord.models.YouTubeService.fetch_and_cache_video",
            side_effect=Exception("API down"),
        ):
            response = self._post()

        self.assertEqual(response.status_code, 502)
        self.assertIn("Failed to fetch", response.data["error"])

    def test_add_item_unauthenticated_returns_403(self):
        response = APIClient().post(
            playlist_items_url("guild_1"),
            {"youtube_id": "vid1", "discord_id": "user_1"},
            format="json",
        )
        self.assertEqual(response.status_code, 403)


class GuildPlaylistItemViewDeleteTest(TestCase):
    def setUp(self):
        self.client = internal_client()

    def test_delete_item_returns_200(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        response = self.client.delete(playlist_item_url("guild_1", item.id))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"ok": True})

    def test_delete_nonexistent_item_returns_404(self):
        response = self.client.delete(playlist_item_url("guild_1", 99999))

        self.assertEqual(response.status_code, 404)
        self.assertIn("error", response.data)

    def test_delete_item_wrong_guild_returns_404(self):
        baker.make(YoutubeVideo, youtube_id="vid1")
        item = GuildPlaylist.objects.add_item("guild_1", "vid1", fetch=False)

        response = self.client.delete(playlist_item_url("guild_999", item.id))

        self.assertEqual(response.status_code, 404)

    def test_delete_unauthenticated_returns_403(self):
        response = APIClient().delete(playlist_item_url("guild_1", 1))
        self.assertEqual(response.status_code, 403)


class GuildPlaylistItemViewPatchTest(TestCase):
    def setUp(self):
        self.client = internal_client()

    def _add_items(self, guild_id="guild_1", count=3):
        items = []
        for i in range(1, count + 1):
            baker.make(YoutubeVideo, youtube_id=f"vid{i}")
            items.append(GuildPlaylist.objects.add_item(guild_id, f"vid{i}", fetch=False))
        return items

    def test_reorder_returns_200(self):
        items = self._add_items()
        new_order = [items[2].id, items[0].id, items[1].id]

        response = self.client.patch(
            playlist_items_url("guild_1"),
            {"order": new_order},
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {"ok": True})

    def test_reorder_missing_order_returns_400(self):
        response = self.client.patch(
            playlist_items_url("guild_1"),
            {},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("order", response.data["error"])

    def test_reorder_order_not_a_list_returns_400(self):
        response = self.client.patch(
            playlist_items_url("guild_1"),
            {"order": "not-a-list"},
            format="json",
        )

        self.assertEqual(response.status_code, 400)

    def test_reorder_invalid_ids_returns_400(self):
        response = self.client.patch(
            playlist_items_url("guild_1"),
            {"order": [99998, 99999]},
            format="json",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.data)

    def test_reorder_unauthenticated_returns_403(self):
        response = APIClient().patch(
            playlist_items_url("guild_1"),
            {"order": [1, 2]},
            format="json",
        )
        self.assertEqual(response.status_code, 403)
