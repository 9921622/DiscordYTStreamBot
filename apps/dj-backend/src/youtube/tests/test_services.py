from django.test import TestCase
from unittest import mock
from unittest.mock import MagicMock

from youtube.services import YouTubeService
from youtube.models import YoutubeVideo


class TestYouTubeService(TestCase):

    # ----------------------------------------
    # get_info
    # ----------------------------------------
    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_get_info_calls_yt_dlp(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"id": "123"}
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        result = YouTubeService.get_info("https://youtube.com/watch?v=123")

        mock_ydl.extract_info.assert_called_once_with(
            "https://youtube.com/watch?v=123",
            download=False,
        )
        self.assertEqual(result, {"id": "123"})

    # ----------------------------------------
    # extract_source_url
    # ----------------------------------------
    def test_extract_source_url_direct(self):
        info = {"url": "http://audio.url"}
        result = YouTubeService.extract_source_url(info)
        self.assertEqual(result, "http://audio.url")

    def test_extract_source_url_requested_formats(self):
        info = {"requested_formats": [{"url": "http://format.url"}]}
        result = YouTubeService.extract_source_url(info)
        self.assertEqual(result, "http://format.url")

    def test_extract_source_url_none(self):
        info = {}
        result = YouTubeService.extract_source_url(info)
        self.assertIsNone(result)

    # ----------------------------------------
    # get_source_url
    # ----------------------------------------
    @mock.patch("youtube.services.YouTubeService.get_info")
    def test_get_source_url(self, mock_get_info):
        mock_get_info.return_value = {"url": "http://audio.url"}

        result = YouTubeService.get_source_url("some_url")

        mock_get_info.assert_called_once_with("some_url")
        self.assertEqual(result, "http://audio.url")

    # ----------------------------------------
    # search
    # ----------------------------------------
    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_search_returns_simplified_results(self, mock_ydl_class):
        mock_ydl = MagicMock()

        mock_ydl.extract_info.return_value = {
            "entries": [
                {
                    "id": "abc",
                    "title": "Test Video",
                    "uploader": "Creator",
                    "thumbnails": [{"url": "thumb.jpg"}],
                    "duration": 120,
                },
                None,  # should be skipped
            ]
        }

        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        results = YouTubeService.search("test query", max_results=5)

        mock_ydl.extract_info.assert_called_once_with(
            "ytsearch5:test query",
            download=False,
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0],
            {
                "youtube_id": "abc",
                "title": "Test Video",
                "creator": "Creator",
                "thumbnail": "thumb.jpg",
                "duration": 120,
            },
        )

    # ----------------------------------------
    # max_results cap
    # ----------------------------------------
    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_search_respects_max_limit(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"entries": []}
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        YouTubeService.search("query", max_results=999)

        mock_ydl.extract_info.assert_called_once_with(
            f"ytsearch{YouTubeService.MAX_RESULTS}:query",
            download=False,
        )

    # ----------------------------------------
    # fetch_and_cache
    # ----------------------------------------

    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_fetch_and_cache_creates_video(self, mock_ydl_class):
        """Test that fetch_and_cache_video stores a new YoutubeVideo in the DB."""
        mock_info = {
            "id": "abc123",
            "title": "Test Video",
            "uploader": "Test Creator",
            "duration": 300,
            "thumbnails": [{"url": "https://example.com/thumb.jpg"}],
            "url": "https://example.com/video.mp4",
        }

        # Mock yt_dlp extract_info to return our fake video info
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = mock_info

        video = YouTubeService.fetch_and_cache_video("abc123")

        self.assertEqual(video.youtube_id, "abc123")
        self.assertEqual(video.title, "Test Video")
        self.assertEqual(video.creator, "Test Creator")
        self.assertEqual(video.duration, 300)
        self.assertEqual(video.thumbnail, "https://example.com/thumb.jpg")
        self.assertEqual(video.source_url, "https://example.com/video.mp4")

        # Confirm it was saved in the database
        db_video = YoutubeVideo.objects.get(youtube_id="abc123")
        self.assertEqual(db_video.youtube_id, video.youtube_id)

    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_fetch_and_cache_updates_existing_video(self, mock_ydl_class):
        """Test that fetch_and_cache_video updates an existing video."""
        # Existing video
        existing = YoutubeVideo.objects.create(
            youtube_id="abc123",
            title="Old Title",
            creator="Old Creator",
            source_url="https://old.com/video.mp4",
            duration=100,
            thumbnail="https://old.com/thumb.jpg",
        )

        mock_info = {
            "id": "abc123",
            "title": "New Title",
            "uploader": "New Creator",
            "duration": 200,
            "thumbnails": [{"url": "https://new.com/thumb.jpg"}],
            "url": "https://new.com/video.mp4",
        }

        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = mock_info

        video = YouTubeService.fetch_and_cache_video("abc123")

        self.assertEqual(video.youtube_id, existing.youtube_id)
        self.assertEqual(video.title, "New Title")
        self.assertEqual(video.creator, "New Creator")
        self.assertEqual(video.duration, 200)
        self.assertEqual(video.thumbnail, "https://new.com/thumb.jpg")
        self.assertEqual(video.source_url, "https://new.com/video.mp4")

    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_fetch_and_cache_raises_exception_for_invalid_info(self, mock_ydl_class):
        """Test that fetch_and_cache_video raises an exception if info is missing ID."""
        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = {"title": "No ID Video"}

        with self.assertRaises(Exception) as context:
            YouTubeService.fetch_and_cache_video("missing_id")

        self.assertIn("Invalid YouTube response", str(context.exception))
