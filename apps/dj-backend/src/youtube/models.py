from django.db import models
from django.conf import settings

import asyncio
import yt_dlp


class YoutubeTag(models.Model):
    """Represents a tag associated with a YouTube video.

    Stores individual tags that can be linked to videos for categorization
    and search purposes. Tags are simple text labels that describe the content
    of the video.

    Attributes:
        name (str): The text of the tag, unique across all tags.
    """

    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        self.name = self.name.lower()
        super().save(*args, **kwargs)


class YoutubeVideo(models.Model):
    """Represents a YouTube video.

    Stores metadata about YouTube videos including title, creator, duration,
    and streaming URL. Provides utilities for extracting video information
    from YouTube using yt_dlp.

    Attributes:
        youtube_id (str): Unique YouTube video identifier (primary key).
        title (str): Display title of the video.
        creator (str): Channel name or uploader of the video.
        source_url (str): Direct URL to the video stream.
        duration (int): Video duration in seconds.
        thumbnail (str, optional): URL to the video thumbnail image.
        created_at (datetime): Timestamp when the record was created.
    """

    URL_TEMPLATE = "https://www.youtube.com/watch?v={youtube_id}"

    youtube_id = models.CharField(primary_key=True, max_length=20, unique=True)  # primary key
    title = models.CharField(max_length=255)
    creator = models.CharField(max_length=255)
    source_url = models.URLField()
    duration = models.PositiveIntegerField(default=0)
    thumbnail = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.ManyToManyField(YoutubeTag, related_name="videos", blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["youtube_id"]),
            models.Index(fields=["creator"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.creator})"

    def get_url(self):
        return self.URL_TEMPLATE.format(youtube_id=self.youtube_id)

    # ==========================================
    # HELPERS
    # ==========================================
    @staticmethod
    def ydl_audio_opts():
        return {
            "format": "bestaudio/best",
            "quiet": True,
            "simulate": True,
            "forceurl": True,
            "noplaylist": True,
        }

    @staticmethod
    def get_info(url, ydl_opts=None):
        ydl_opts = ydl_opts or YoutubeVideo.ydl_audio_opts()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    @staticmethod
    def extract_source_url(info_dict):
        if "url" in info_dict:
            return info_dict["url"]
        if "requested_formats" in info_dict:
            return info_dict["requested_formats"][0].get("url")
        return None

    @classmethod
    def get_source_url(cls, url):
        info_dict = cls.get_info(url)
        return cls.extract_source_url(info_dict)

    # ==========================================
    # FACTORY METHODS
    # ==========================================
    @classmethod
    def from_ydl_info(cls, info_dict, save=False):
        tag_names = info_dict.get("tags", []) or []
        source_url = cls.extract_source_url(info_dict) or ""
        youtube_id = info_dict.get("id")

        if save:
            instance, _ = cls.objects.get_or_create(
                youtube_id=youtube_id,
                defaults={
                    "title": info_dict.get("title") or info_dict.get("fulltitle", "Unknown title"),
                    "creator": info_dict.get("uploader", "Unknown channel"),
                    "source_url": source_url,
                    "duration": info_dict.get("duration") or 0,
                    "thumbnail": info_dict.get("thumbnail"),
                },
            )
            for tag_name in tag_names:
                tag, _ = YoutubeTag.objects.get_or_create(name=tag_name.lower())
                instance.tags.add(tag)
            return instance

        return cls(
            youtube_id=youtube_id,
            title=info_dict.get("title") or info_dict.get("fulltitle", "Unknown title"),
            creator=info_dict.get("uploader", "Unknown channel"),
            source_url=source_url,
            duration=info_dict.get("duration") or 0,
            thumbnail=info_dict.get("thumbnail"),
        )

    @classmethod
    def from_url(cls, url, ydl_opts=None, save=False):
        info = cls.get_info(url, ydl_opts)
        return cls.from_ydl_info(info, save=save)

    @classmethod
    async def from_url_async(cls, url, ydl_opts=None, save=False):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: cls.from_url(url, ydl_opts, save))


class AbstractPlaylist(models.Model):
    """Abstract base for any ordered collection of videos."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def clear(self):
        self.items.all().delete()

    def next(self) -> "AbstractPlaylistItem | None":
        return self.items.order_by("order").first()


class AbstractPlaylistItem(models.Model):
    """Abstract base for a single video entry in a playlist."""

    video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)
    added_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ["order"]


class YoutubePlaylist(AbstractPlaylist):
    """A saved playlist sourced from or mirroring a YouTube playlist."""

    class PlaylistType(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    youtube_playlist_id = models.BigAutoField(primary_key=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    thumbnail = models.URLField(null=True, blank=True)
    channel_title = models.CharField(max_length=255, blank=True, default="")
    owned_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="youtube_playlists",
    )
    playlist_type = models.CharField(
        max_length=10,
        choices=PlaylistType.choices,
        default=PlaylistType.PUBLIC,
    )

    def __str__(self):
        return self.title or self.youtube_playlist_id


class YoutubePlaylistItem(AbstractPlaylistItem):
    """A video entry in a YoutubePlaylist."""

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(
                fields=["playlist", "video"],
                name="unique_video_per_playlist",
            )
        ]

    playlist = models.ForeignKey(YoutubePlaylist, on_delete=models.CASCADE, related_name="items")

    def __str__(self):
        return f"{self.video.title} in {self.playlist.title}"
