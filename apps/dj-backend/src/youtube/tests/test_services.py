from django.test import TestCase
from unittest.mock import patch, MagicMock

from youtube.services import YouTubeService


class TestYouTubeService(TestCase):

    # ----------------------------------------
    # get_info
    # ----------------------------------------
    @patch("youtube.services.yt_dlp.YoutubeDL")
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
    @patch("youtube.services.YouTubeService.get_info")
    def test_get_source_url(self, mock_get_info):
        mock_get_info.return_value = {"url": "http://audio.url"}

        result = YouTubeService.get_source_url("some_url")

        mock_get_info.assert_called_once_with("some_url")
        self.assertEqual(result, "http://audio.url")

    # ----------------------------------------
    # search
    # ----------------------------------------
    @patch("youtube.services.yt_dlp.YoutubeDL")
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
    @patch("youtube.services.yt_dlp.YoutubeDL")
    def test_search_respects_max_limit(self, mock_ydl_class):
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"entries": []}
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        YouTubeService.search("query", max_results=999)

        mock_ydl.extract_info.assert_called_once_with(
            f"ytsearch{YouTubeService.MAX_RESULTS}:query",
            download=False,
        )
