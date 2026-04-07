import yt_dlp
from typing import List, Dict, Optional

from youtube.models import YoutubeVideo


class YouTubeService:
    """
    Handles all interactions with YouTube via yt-dlp.

    Responsibilities:
    - Searching YouTube
    - Fetching video info
    - Extracting stream URLs
    """

    MAX_RESULTS = 50

    @staticmethod
    def ydl_audio_opts() -> dict:
        return {
            "format": "bestaudio/best",
            "quiet": True,
            "simulate": True,
            "forceurl": True,
            "noplaylist": True,
        }

    @staticmethod
    def ydl_search_opts() -> dict:
        return {
            "quiet": True,
            "no_warnings": True,
            "default_search": "ytsearch",
            "extract_flat": "in_playlist",
        }

    @classmethod
    def get_info(cls, url: str, ydl_opts: dict | None = None) -> dict:
        """
        Fetch full metadata for a YouTube video.
        """
        ydl_opts = ydl_opts or cls.ydl_audio_opts()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    @staticmethod
    def extract_source_url(info_dict: dict) -> str | None:
        """
        Extract direct audio stream URL from yt-dlp info dict.
        """
        if "url" in info_dict:
            return info_dict["url"]

        if "requested_formats" in info_dict:
            return info_dict["requested_formats"][0].get("url")

        return None

    @classmethod
    def get_source_url(cls, url: str) -> str | None:
        """
        Convenience method: URL -> stream URL
        """
        info = cls.get_info(url)
        return cls.extract_source_url(info)

    @classmethod
    def search(cls, query: str, max_results: int = 10) -> list[dict]:
        """
        Search YouTube and return simplified video data.
        """
        max_results = min(max_results, cls.MAX_RESULTS)

        results = []
        ydl_opts = cls.ydl_search_opts()

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(f"ytsearch{max_results}:{query}", download=False)

            for entry in info.get("entries", []):
                if not entry:
                    continue

                thumbnails = entry.get("thumbnails") or []

                results.append(
                    {
                        "youtube_id": entry.get("id"),
                        "title": entry.get("title"),
                        "creator": entry.get("uploader"),
                        "thumbnail": thumbnails[0]["url"] if thumbnails else None,
                        "duration": entry.get("duration"),
                    }
                )

        return results

    @classmethod
    def fetch_and_cache_video(cls, youtube_id: str) -> YoutubeVideo:
        """
        Fetch video info using service and store in DB.
        """
        youtube_url = YoutubeVideo.URL_TEMPLATE.format(youtube_id=youtube_id)
        info = cls.get_info(youtube_url)
        if not info.get("id"):
            raise Exception("Invalid YouTube response: missing video id")

        video, _ = YoutubeVideo.objects.update_or_create(
            youtube_id=info["id"],
            defaults={
                "title": info.get("title"),
                "creator": info.get("uploader"),
                "duration": info.get("duration"),
                "thumbnail": (info.get("thumbnails") or [{}])[-1].get("url"),
                "source_url": cls.extract_source_url(info),
            },
        )
        return video

    @classmethod
    def get_or_fetch(cls, youtube_id: str) -> YoutubeVideo:
        try:
            vid = YoutubeVideo.objects.get(youtube_id=youtube_id)
        except YoutubeVideo.DoesNotExist:
            vid = cls.fetch_and_cache_video(youtube_id)
        return vid
