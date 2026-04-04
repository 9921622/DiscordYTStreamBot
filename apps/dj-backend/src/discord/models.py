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


class GuildQueueManager(models.Manager):
    """A Manager is the interface through which database query operations are provided to Django models"""

    def get_for_guild(self, guild_id: str) -> "GuildQueue":
        guild, _ = DiscordGuild.objects.get_or_create(guild_id=guild_id)
        queue, _ = self.get_or_create(guild=guild)
        return queue

    def add_item(self, guild_id: str, youtube_id: str, fetch: bool = False) -> "GuildQueueItem":
        queue = self.get_for_guild(guild_id)

        if fetch:
            video = YouTubeService.fetch_and_cache_video(youtube_id)
        else:
            video = YoutubeVideo.objects.get(youtube_id=youtube_id)

        last_order = queue.items.aggregate(models.Max("order"))["order__max"] or 0
        return GuildQueueItem.objects.create(queue=queue, video=video, order=last_order + 1)

    def remove_item(self, guild_id: str, item_id: int) -> None:
        item = GuildQueueItem.objects.get(id=item_id, queue__guild__guild_id=guild_id)
        item.delete()

    def reorder_items(self, guild_id: str, item_ids: list[int]) -> None:
        queue = self.get_for_guild(guild_id)

        items = GuildQueueItem.objects.filter(id__in=item_ids, queue=queue)
        if items.count() != len(item_ids):
            raise ValueError("One or more item IDs are invalid")

        updates = [GuildQueueItem(id=item_id, order=i + 1) for i, item_id in enumerate(item_ids)]
        GuildQueueItem.objects.bulk_update(updates, ["order"])


class GuildQueue(AbstractPlaylist):
    """Temporary playback queue for a guild. One queue per guild."""

    guild = models.OneToOneField(DiscordGuild, on_delete=models.CASCADE, related_name="queue")

    objects = GuildQueueManager()

    def __str__(self):
        return f"Queue for {self.guild.name}"


class GuildQueueItem(AbstractPlaylistItem):
    """A video in a guild's playback queue."""

    queue = models.ForeignKey(GuildQueue, on_delete=models.CASCADE, related_name="items")

    def __str__(self):
        return f"{self.video.title} in {self.queue.guild.name}"
