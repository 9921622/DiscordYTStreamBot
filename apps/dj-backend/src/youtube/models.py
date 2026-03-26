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

    # ==========================================
    # FACTORY METHODS
    # ==========================================
    @classmethod
    def from_ydl_info(cls, info_dict, save=False):
        tag_names = info_dict.get("tags", [])

        instance = cls(
            youtube_id=info_dict.get("id"),
            title=info_dict.get("title") or info_dict.get("fulltitle", "Unknown title"),
            creator=info_dict.get("uploader", "Unknown channel"),
            source_url=cls.extract_source_url(info_dict),
            duration=info_dict.get("duration") or 0,
            thumbnail=info_dict.get("thumbnail"),
        )

        if save:
            instance.save()
            # Add tags after saving (required for ManyToManyField)
            for tag_name in tag_names:
                tag, _ = YoutubeTag.objects.get_or_create(name=tag_name.lower())
                instance.tags.add(tag)

        return instance

    @classmethod
    def from_url(cls, url, ydl_opts=None, save=False):
        info = cls.get_info(url, ydl_opts)
        return cls.from_ydl_info(info, save=save)

    @classmethod
    async def from_url_async(cls, url, ydl_opts=None, save=False):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, lambda: cls.from_url(url, ydl_opts, save))


class YoutubePlaylist(models.Model):
    """Represents a user's YouTube playlist.

    Manages playlists created by users, storing metadata about the playlist
    and its association with the authenticated user. Playlists can be classified
    as permanent or temporary based on their intended lifespan.

    Attributes:
        name (str): Display name of the playlist.
        playlist_type (str): Type of playlist - PUBLIC or PRIVATE.
        user (User): Foreign key to the authenticated user who owns the playlist.
        created_at (datetime): Timestamp when the playlist was created.
        updated_at (datetime): Timestamp of the last modification.
        youtube_playlist_id (str, optional): External YouTube playlist identifier.
    """

    class PlaylistType(models.TextChoices):
        PUBLIC = "public", "Public"
        PRIVATE = "private", "Private"

    name = models.CharField(max_length=255)
    playlist_type = models.CharField(
        max_length=10,
        choices=PlaylistType.choices,
        default=PlaylistType.PUBLIC,
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="playlists")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    youtube_playlist_id = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.playlist_type})"


class YoutubePlaylistItem(models.Model):
    """Represents a link between a playlist and a video.

    Junction model that associates videos with playlists, maintaining the order
    of videos within each playlist and preventing duplicate video entries.

    Attributes:
        playlist (YoutubePlaylist): Foreign key to the parent playlist.
        video (YoutubeVideo): Foreign key to the video in the playlist.
        order (int): Position of the video within the playlist (0-indexed).
        added_at (datetime): Timestamp when the video was added to the playlist.
    """

    playlist = models.ForeignKey(YoutubePlaylist, on_delete=models.CASCADE, related_name="items")
    video = models.ForeignKey(YoutubeVideo, on_delete=models.CASCADE)
    order = models.PositiveIntegerField(default=0)  # position in the playlist
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order"]
        unique_together = [["playlist", "video"]]

    def __str__(self):
        return f"{self.video.title} in {self.playlist.name}"
