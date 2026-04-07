from django.db import models
from django.contrib.auth.models import User
from django.conf import settings

from discord.api import DiscordCDNAPI
from youtube.services import YouTubeService
from youtube.models import YoutubeVideo, AbstractPlaylist, AbstractPlaylistItem


class DiscordUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="discord")
    discord_id = models.CharField(max_length=64, unique=True, primary_key=True)

    username = models.CharField(max_length=64)
    global_name = models.CharField(max_length=64, null=True, blank=True)
    avatar = models.CharField(max_length=256, null=True, blank=True)

    access_token = models.CharField(max_length=256)
    refresh_token = models.CharField(max_length=256)
    token_expires_at = models.DateTimeField()

    scope = models.CharField(max_length=256)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username} ({self.discord_id})"

    def get_avatar_uri(self):
        return DiscordCDNAPI.build_avatar_url(self.discord_id, self.avatar)


class DiscordGuild(models.Model):
    guild_id = models.CharField(max_length=64, unique=True, primary_key=True)
    name = models.CharField(max_length=255, blank=True, default="")

    def __str__(self):
        return self.name or "Guild"


class GuildPlaylistManager(models.Manager):

    def get_playlist(self, guild_id: str) -> "GuildPlaylist":
        guild, _ = DiscordGuild.objects.get_or_create(guild_id=guild_id)
        playlist, _ = self.get_or_create(guild=guild)
        # Refresh to ensure current_item FK is up to date after recent saves
        playlist.refresh_from_db()
        return playlist

    def add_item(
        self, guild_id: str, youtube_id: str, added_by: DiscordUser | None = None, fetch: bool = False
    ) -> "GuildPlaylistItem":
        playlist = self.get_playlist(guild_id)

        if fetch:
            video = YouTubeService.fetch_and_cache_video(youtube_id)
        else:
            video = YoutubeVideo.objects.get(youtube_id=youtube_id)

        last_order = playlist.items.aggregate(models.Max("order"))["order__max"] or 0
        return GuildPlaylistItem.objects.create(playlist=playlist, video=video, order=last_order + 1, added_by=added_by)

    def remove_item(self, guild_id: str, item_id: int) -> None:
        item = GuildPlaylistItem.objects.get(id=item_id, playlist__guild__guild_id=guild_id)
        playlist = item.playlist

        if playlist.current_item_id == item.id:
            next_item = playlist.items.filter(order__gt=item.order).first()
            playlist.current_item = next_item
            playlist.save(update_fields=["current_item"])

        item.delete()

    def reorder_items(self, guild_id: str, item_ids: list[int]) -> None:
        playlist = self.get_playlist(guild_id)

        items = GuildPlaylistItem.objects.filter(id__in=item_ids, playlist=playlist)
        if items.count() != len(item_ids):
            raise ValueError("One or more item IDs are invalid")

        updates = [GuildPlaylistItem(id=item_id, order=i + 1) for i, item_id in enumerate(item_ids)]
        GuildPlaylistItem.objects.bulk_update(updates, ["order"])

    def next_item(self, guild_id: str, playlist_item: "GuildPlaylistItem | None" = None) -> "GuildPlaylistItem | None":
        """sets the current item as the next item in order.
        Or if playlist_item is not None; the playlist_item"""
        playlist = self.get_playlist(guild_id)

        if playlist_item:
            next_item = playlist_item
        else:
            items = playlist.items.order_by("order")
            next_item = (
                items.first()
                if playlist.current_item is None
                else items.filter(order__gt=playlist.current_item.order).first()
            )

        playlist.current_item = next_item
        playlist.save(update_fields=["current_item", "updated_at"])
        return next_item

    def next_item_as_video(self, guild_id: str, video: YoutubeVideo, added_by: DiscordUser):
        item = self.add_item(guild_id, youtube_id=video.youtube_id, added_by=added_by, fetch=False)
        result = self.next_item(guild_id, item)

        assert result is not None, f"next_item returned None after adding item {item.id}"
        return result

    def prev_item(self, guild_id: str) -> "GuildPlaylistItem | None":
        playlist = self.get_playlist(guild_id)
        items = playlist.items.order_by("-order")

        prev_item = (
            items.first()
            if playlist.current_item is None
            else items.filter(order__lt=playlist.current_item.order).first()
        )

        playlist.current_item = prev_item
        playlist.save(update_fields=["current_item", "updated_at"])
        return prev_item

    def clear(self, guild_id: str) -> None:
        playlist = self.get_playlist(guild_id)
        playlist.current_item = None
        playlist.save(update_fields=["current_item"])
        playlist.items.all().delete()


class GuildPlaylist(AbstractPlaylist):
    """
    Ephemeral playback playlist for a guild. One playlist per guild.
    Designed for Redis migration: all mutations go through the manager,
    instance methods are intentionally minimal.
    """

    guild = models.OneToOneField(DiscordGuild, on_delete=models.CASCADE, related_name="playlist")
    current_item = models.ForeignKey(
        "GuildPlaylistItem",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="+",
    )

    objects = GuildPlaylistManager()

    def __str__(self):
        return f"Playlist for {self.guild.name}"


class GuildPlaylistItem(AbstractPlaylistItem):
    """A video in a guild's ephemeral playback playlist."""

    playlist = models.ForeignKey(GuildPlaylist, on_delete=models.CASCADE, related_name="items")
    added_by = models.ForeignKey(
        DiscordUser, on_delete=models.SET_NULL, null=True, blank=True, related_name="playlist_items"
    )

    def __str__(self):
        return f"{self.video.title} in {self.playlist.guild.name}"
