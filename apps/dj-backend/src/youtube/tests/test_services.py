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
    # search - YouTube URL cleaning
    # ----------------------------------------
    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_search_strips_extra_params_from_youtube_url(self, mock_ydl_class):
        """YouTube URLs passed as query should have tracking/playlist params stripped."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"entries": []}
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        YouTubeService.search(
            "https://www.youtube.com/watch?v=abc123&list=PLxxx&si=tracking&t=30",
            max_results=5,
        )

        mock_ydl.extract_info.assert_called_once_with(
            "ytsearch5:https://www.youtube.com/watch?v=abc123",
            download=False,
        )

    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_search_plain_text_query_unchanged(self, mock_ydl_class):
        """Non-URL queries should pass through to yt-dlp unmodified."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"entries": []}
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        YouTubeService.search("lofi hip hop", max_results=5)

        mock_ydl.extract_info.assert_called_once_with(
            "ytsearch5:lofi hip hop",
            download=False,
        )

    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_search_youtube_url_without_extra_params_unchanged(self, mock_ydl_class):
        """A clean YouTube URL (v= only) should pass through as-is."""
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = {"entries": []}
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl

        YouTubeService.search("https://www.youtube.com/watch?v=abc123", max_results=5)

        mock_ydl.extract_info.assert_called_once_with(
            "ytsearch5:https://www.youtube.com/watch?v=abc123",
            download=False,
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

    @mock.patch("youtube.services.requests.head")
    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_fetch_and_cache_creates_video(self, mock_ydl_class, mock_head):
        """Test that fetch_and_cache_video stores a new YoutubeVideo in the DB."""
        mock_info = {
            "id": "abc123",
            "title": "Test Video",
            "uploader": "Test Creator",
            "duration": 300,
            "thumbnails": [
                {"url": "https://example.com/thumb_low.jpg"},
                {"url": "https://example.com/thumb_high.jpg"},
            ],
            "url": "https://example.com/video.mp4",
        }

        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = mock_info
        mock_head.return_value.status_code = 200

        video = YouTubeService.fetch_and_cache_video("abc123")

        self.assertEqual(video.youtube_id, "abc123")
        self.assertEqual(video.title, "Test Video")
        self.assertEqual(video.creator, "Test Creator")
        self.assertEqual(video.duration, 300)
        # Highest quality (last in list) is tried first and succeeds
        self.assertEqual(video.thumbnail, "https://example.com/thumb_high.jpg")
        self.assertEqual(video.source_url, "https://example.com/video.mp4")

        db_video = YoutubeVideo.objects.get(youtube_id="abc123")
        self.assertEqual(db_video.youtube_id, video.youtube_id)

    @mock.patch("youtube.services.requests.head")
    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_fetch_and_cache_updates_existing_video(self, mock_ydl_class, mock_head):
        """Test that fetch_and_cache_video updates an existing video."""
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
            "thumbnails": [
                {"url": "https://new.com/thumb_low.jpg"},
                {"url": "https://new.com/thumb_high.jpg"},
            ],
            "url": "https://new.com/video.mp4",
        }

        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = mock_info
        mock_head.return_value.status_code = 200

        video = YouTubeService.fetch_and_cache_video("abc123")

        self.assertEqual(video.youtube_id, existing.youtube_id)
        self.assertEqual(video.title, "New Title")
        self.assertEqual(video.creator, "New Creator")
        self.assertEqual(video.duration, 200)
        self.assertEqual(video.thumbnail, "https://new.com/thumb_high.jpg")
        self.assertEqual(video.source_url, "https://new.com/video.mp4")

    @mock.patch("youtube.services.requests.head")
    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_fetch_and_cache_falls_back_on_404(self, mock_ydl_class, mock_head):
        """Test that _resolve_thumbnail skips 404 URLs and falls back to the next."""
        mock_info = {
            "id": "abc123",
            "title": "Test Video",
            "uploader": "Test Creator",
            "duration": 300,
            "thumbnails": [
                {"url": "https://example.com/thumb_low.jpg"},
                {"url": "https://example.com/thumb_high.jpg"},  # 404
            ],
            "url": "https://example.com/video.mp4",
        }

        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = mock_info
        # High quality 404s, low quality succeeds
        mock_head.side_effect = [
            mock.Mock(status_code=404),
            mock.Mock(status_code=200),
        ]

        video = YouTubeService.fetch_and_cache_video("abc123")
        self.assertEqual(video.thumbnail, "https://example.com/thumb_low.jpg")

    @mock.patch("youtube.services.requests.head")
    @mock.patch("youtube.services.yt_dlp.YoutubeDL")
    def test_fetch_and_cache_thumbnail_none_when_all_404(self, mock_ydl_class, mock_head):
        """Test that thumbnail is None when all thumbnail URLs return 404."""
        mock_info = {
            "id": "abc123",
            "title": "Test Video",
            "uploader": "Test Creator",
            "duration": 300,
            "thumbnails": [
                {"url": "https://example.com/thumb_low.jpg"},
                {"url": "https://example.com/thumb_high.jpg"},
            ],
            "url": "https://example.com/video.mp4",
        }

        mock_ydl_instance = mock_ydl_class.return_value.__enter__.return_value
        mock_ydl_instance.extract_info.return_value = mock_info
        mock_head.return_value.status_code = 404

        video = YouTubeService.fetch_and_cache_video("abc123")
        self.assertIsNone(video.thumbnail)
