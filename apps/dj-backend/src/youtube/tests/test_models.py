from django.test import TestCase
from unittest import mock
from model_bakery import baker

from django.contrib.auth import get_user_model
from youtube.models import YoutubeVideo, YoutubePlaylist, YoutubePlaylistItem, YoutubeTag

User = get_user_model()


class YoutubeVideoModelTests(TestCase):

    def test_youtube_video_creation(self):
        """Test creating a YoutubeVideo instance with valid data."""
        video = baker.make(
            YoutubeVideo,
            youtube_id="abc123",
            title="Test Video",
            creator="Test Creator",
            source_url="https://youtube.com/watch?v=abc123",
            duration=300,
            thumbnail="https://img.youtube.com/vi/abc123/hqdefault.jpg",
        )
        self.assertEqual(video.youtube_id, "abc123")
        self.assertEqual(str(video), "Test Video (Test Creator)")

    def test_from_ydl_info_creates_instance(self):
        """Test that from_ydl_info correctly creates a YoutubeVideo instance from ydl info."""
        mock_info = {
            "title": "Mock Video",
            "uploader": "Mock Channel",
            "url": "https://youtube.com/mockvideo",
            "duration": 123,
            "thumbnail": "https://example.com/thumb.jpg",
        }

        video = YoutubeVideo.from_ydl_info(mock_info, save=False)
        self.assertEqual(video.title, "Mock Video")
        self.assertEqual(video.creator, "Mock Channel")
        self.assertEqual(video.source_url, "https://youtube.com/mockvideo")
        self.assertEqual(video.duration, 123)
        self.assertEqual(video.thumbnail, "https://example.com/thumb.jpg")

    @mock.patch("youtube.models.YoutubeVideo.get_info")
    def test_from_url_calls_get_info(self, mock_get_info):
        """Test that from_url calls get_info and creates a video instance."""
        mock_info = {"title": "Mock", "uploader": "Uploader", "url": "http://mock"}
        mock_get_info.return_value = mock_info

        video = YoutubeVideo.from_url("https://fake.url", save=False)
        mock_get_info.assert_called_once_with("https://fake.url", None)
        self.assertEqual(video.title, "Mock")
        self.assertEqual(video.source_url, "http://mock")

    def test_real(self):
        """Test that from_url can create a real video instance from an actual YouTube URL."""
        url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        video = YoutubeVideo.from_url(url, save=False)

        self.assertEqual(video.youtube_id, "dQw4w9WgXcQ")
        self.assertEqual(video.title, "Rick Astley - Never Gonna Give You Up (Official Video) (4K Remaster)")
        self.assertEqual(video.creator, "Rick Astley")
        self.assertTrue(video.source_url.startswith("https://"))
        self.assertGreater(video.duration, 0)
        self.assertTrue(video.thumbnail.startswith("https://"))

    def test_tags_lowercase_enforcement(self):
        """Test that tags are stored in lowercase."""
        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "url": "https://example.com/video",
            "duration": 100,
            "tags": ["Music", "POP", "Rock"],
        }

        video = YoutubeVideo.from_ydl_info(mock_info, save=True)
        tags = video.tags.all()

        self.assertEqual(tags.count(), 3)
        tag_names = sorted([tag.name for tag in tags])
        self.assertEqual(tag_names, ["music", "pop", "rock"])

    def test_tag_deduplication(self):
        """Test that duplicate tags are deduplicated."""
        mock_info = {
            "title": "Test Video",
            "uploader": "Test Channel",
            "url": "https://example.com/video",
            "duration": 100,
            "tags": ["Music", "music", "MUSIC"],
        }

        video = YoutubeVideo.from_ydl_info(mock_info, save=True)
        tags = video.tags.all()

        self.assertEqual(tags.count(), 1)
        self.assertEqual(tags.first().name, "music")


class YoutubePlaylistModelTests(TestCase):

    def setUp(self):
        self.user = baker.make(User)

    def test_playlist_creation(self):
        """Test creating a playlist with valid data."""
        playlist = baker.make(YoutubePlaylist, name="My Playlist", user=self.user)
        self.assertEqual(playlist.name, "My Playlist")
        self.assertEqual(playlist.user, self.user)
        self.assertIn(playlist.playlist_type, [t[0] for t in YoutubePlaylist.PlaylistType.choices])
        self.assertEqual(str(playlist), f"My Playlist ({playlist.playlist_type})")

    def test_add_video_to_playlist(self):
        """Test adding videos to a playlist and the order is maintained."""
        playlist = baker.make(YoutubePlaylist, name="Test Playlist", user=self.user)
        video1 = baker.make(YoutubeVideo, youtube_id="v1")
        video2 = baker.make(YoutubeVideo, youtube_id="v2")

        item1 = YoutubePlaylistItem.objects.create(playlist=playlist, video=video1, order=1)
        item2 = YoutubePlaylistItem.objects.create(playlist=playlist, video=video2, order=2)

        items = playlist.items.all()
        self.assertEqual(items.count(), 2)
        self.assertEqual(items[0].video.youtube_id, "v1")
        self.assertEqual(items[1].video.youtube_id, "v2")

    def test_playlist_item_unique_constraint(self):
        """Test that a video can only be added once to a playlist."""
        playlist = baker.make(YoutubePlaylist, name="Playlist Order", user=self.user)
        video = baker.make(YoutubeVideo, youtube_id="v1")

        # first addition succeeds
        YoutubePlaylistItem.objects.create(playlist=playlist, video=video, order=1)

        # duplicate video in same playlist should raise exception
        with self.assertRaises(Exception):
            YoutubePlaylistItem.objects.create(playlist=playlist, video=video, order=2)
