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

    def test_from_info_dict_creates_instance_without_save(self):
        """Test that from_info_dict correctly creates a YoutubeVideo instance (unsaved)."""
        info_dict = {
            "id": "vid123",
            "title": "Mock Video",
            "uploader": "Mock Channel",
            "source_url": "https://youtube.com/mockvideo",
            "duration": 123,
            "thumbnail": "https://example.com/thumb.jpg",
            "tags": ["Music", "Pop"],
        }

        video = YoutubeVideo.from_info_dict(info_dict, save=False)

        self.assertEqual(video.youtube_id, "vid123")
        self.assertEqual(video.title, "Mock Video")
        self.assertEqual(video.creator, "Mock Channel")
        self.assertEqual(video.source_url, "https://youtube.com/mockvideo")
        self.assertEqual(video.duration, 123)
        self.assertEqual(video.thumbnail, "https://example.com/thumb.jpg")
        self.assertTrue(video._state.adding)

    def test_from_info_dict_creates_instance_with_save_and_tags(self):
        """Test that from_info_dict saves the instance and adds tags (lowercased, deduplicated)."""
        info_dict = {
            "id": "vid456",
            "title": "Another Video",
            "uploader": "Another Channel",
            "source_url": "https://youtube.com/another",
            "duration": 200,
            "thumbnail": "https://example.com/thumb2.jpg",
            "tags": ["Music", "music", "POP"],
        }

        video = YoutubeVideo.from_info_dict(info_dict, save=True)

        self.assertIsNotNone(video.pk)
        tags = video.tags.all()
        self.assertEqual(tags.count(), 2)
        tag_names = sorted([tag.name for tag in tags])
        self.assertEqual(tag_names, ["music", "pop"])

    def test_get_url_returns_correct_url(self):
        """Test that get_url() generates the correct YouTube URL."""
        video = YoutubeVideo(
            youtube_id="abc123",
            title="Test Video",
            creator="Test Creator",
            source_url="https://youtube.com/watch?v=abc123",
        )
        self.assertEqual(video.get_url(), "https://www.youtube.com/watch?v=abc123")

    def test_str_representation(self):
        """Test the string representation of a video."""
        video = YoutubeVideo(
            youtube_id="abc123",
            title="Test Video",
            creator="Test Creator",
            source_url="https://youtube.com/watch?v=abc123",
        )
        self.assertEqual(str(video), "Test Video (Test Creator)")


class YoutubePlaylistModelTests(TestCase):

    def setUp(self):
        self.user = baker.make(User)

    def test_playlist_creation(self):
        """Test creating a playlist with valid data."""
        playlist = baker.make(YoutubePlaylist, title="My Playlist", owned_by=self.user)
        self.assertEqual(playlist.title, "My Playlist")
        self.assertEqual(playlist.owned_by, self.user)
        self.assertIn(playlist.playlist_type, [t[0] for t in YoutubePlaylist.PlaylistType.choices])

    def test_add_video_to_playlist(self):
        """Test adding videos to a playlist and the order is maintained."""
        playlist = baker.make(YoutubePlaylist, title="Test Playlist", owned_by=self.user)
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
        playlist = baker.make(YoutubePlaylist, title="Playlist Order", owned_by=self.user)
        video = baker.make(YoutubeVideo, youtube_id="v1")

        # first addition succeeds
        YoutubePlaylistItem.objects.create(playlist=playlist, video=video, order=1)

        # duplicate video in same playlist should raise exception
        with self.assertRaises(Exception):
            YoutubePlaylistItem.objects.create(playlist=playlist, video=video, order=2)
