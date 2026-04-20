import yt_dlp
import requests
from typing import List, Dict, Optional

from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

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

    @staticmethod
    def _resolve_thumbnail(thumbnails: list[dict]) -> str | None:
        """
        Walk thumbnails from highest quality to lowest, returning the first
        URL that doesn't 404. Returns None if all fail or list is empty.

        yt-dlp orders thumbnails ascending by quality, so we reverse.
        """
        for thumb in reversed(thumbnails):
            url = thumb.get("url")
            if not url:
                continue
            try:
                resp = requests.head(url, timeout=5, allow_redirects=True)
                if resp.status_code != 404:
                    return url
            except requests.RequestException:
                continue
        return None

    @staticmethod
    def _clean_youtube_url(query: str) -> str:
        """
        If the query is a YouTube URL, strip all search params except `v`
        (the video ID) to avoid playlist or tracking params influencing results.
        """
        parsed = urlparse(query)
        if parsed.scheme in ("http", "https") and "youtube.com" in parsed.netloc:
            params = parse_qs(parsed.query)
            cleaned = {k: v for k, v in params.items() if k == "v"}
            clean_query = parsed._replace(query=urlencode(cleaned, doseq=True))
            return urlunparse(clean_query)
        return query

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
        query = cls._clean_youtube_url(query)
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
                "thumbnail": cls._resolve_thumbnail(info.get("thumbnails") or []),
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
