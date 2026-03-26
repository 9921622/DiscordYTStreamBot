from django.test import TestCase
from django.shortcuts import reverse
from rest_framework.test import APIClient
from rest_framework import status

from unittest import mock
from model_bakery import baker

from django.contrib.auth import get_user_model
from youtube.models import YoutubeVideo, YoutubePlaylist, YoutubePlaylistItem

User = get_user_model()


class YoutubeVideoViewSetTests(TestCase):
    def setUp(self):
        # Create test user and API client
        self.user = baker.make(User)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create some sample videos
        self.video1 = baker.make(YoutubeVideo, youtube_id="v1", title="Video 1")
        self.video2 = baker.make(YoutubeVideo, youtube_id="v2", title="Video 2")

    def test_list_videos(self):
        """Test retrieving a list of videos."""
        response = self.client.get(reverse("youtube:video-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data[0]["youtube_id"], self.video1.youtube_id)

    def test_retrieve_video(self):
        """Test retrieving a single video by its YouTube ID."""
        response = self.client.get(reverse("youtube:video-detail", kwargs={"youtube_id": self.video1.youtube_id}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["title"], self.video1.title)

    @mock.patch("youtube.models.YoutubeVideo.from_url")
    def test_retrieve_video_auto_fetch_from_youtube(self, mock_from_url):
        """Test that retrieving a non-existent video auto-fetches it from YouTube."""
        # Create a video instance to return from the mocked from_url
        # (not saved to database - the mock replaces the actual from_url)
        mock_video = YoutubeVideo(
            youtube_id="new_video_id",
            title="Auto-Fetched Video",
            creator="Auto-Fetched Creator",
            source_url="https://example.com/stream",
            duration=300,
            thumbnail="https://example.com/thumb.jpg",
        )
        mock_from_url.return_value = mock_video

        # Try to retrieve a video that doesn't exist in the database
        response = self.client.get(reverse("youtube:video-detail", kwargs={"youtube_id": "new_video_id"}))

        # Should return 200 and the video data
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["youtube_id"], "new_video_id")
        self.assertEqual(response.data["title"], "Auto-Fetched Video")

        # Verify from_url was called with the correct YouTube URL
        mock_from_url.assert_called_once_with("https://www.youtube.com/watch?v=new_video_id", save=True)

    @mock.patch("youtube.models.YoutubeVideo.from_url")
    def test_retrieve_video_auto_fetch_failure(self, mock_from_url):
        """Test that auto-fetch returns 404 when YouTube fetch fails."""
        # Mock from_url to raise an exception
        mock_from_url.side_effect = Exception("YouTube fetch failed")

        # Try to retrieve a video that doesn't exist and will fail to fetch
        response = self.client.get(reverse("youtube:video-detail", kwargs={"youtube_id": "invalid_id"}))

        # Should return 404 with error message
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn("error", response.data)
        self.assertIn("Failed to fetch video from YouTube", response.data["error"])


class YoutubePlaylistViewSetTests(TestCase):
    def setUp(self):
        # Create test user and API client
        self.user = baker.make(User)
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        # Create some sample videos
        self.video1 = baker.make(YoutubeVideo, youtube_id="v1", title="Video 1")
        self.video2 = baker.make(YoutubeVideo, youtube_id="v2", title="Video 2")

    def test_create_playlist(self):
        """Test creating a new playlist with valid data."""
        data = {"name": "My Playlist"}
        response = self.client.post(reverse("youtube:playlist-list"), data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["name"], "My Playlist")
        self.assertEqual(response.data["user"], str(self.user))

    @mock.patch("youtube.models.YoutubeVideo.get_info")
    def test_add_video_to_playlist(self, mock_get_info):
        """Test adding a video to a playlist and that the video info is fetched correctly."""
        # Mock YouTube fetching
        mock_get_info.return_value = {
            "title": "Mock Video",
            "uploader": "Mock Channel",
            "url": "http://mock",
            "duration": 100,
            "thumbnail": "http://mock/thumb.jpg",
        }

        # Create a playlist
        playlist = baker.make(YoutubePlaylist, name="Test Playlist", user=self.user)

        # Add a video via API
        data = {"youtube_id": "abc123"}
        response = self.client.post(reverse("youtube:playlist-add-video", kwargs={"pk": playlist.pk}), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Verify the video exists in DB
        video = YoutubeVideo.objects.get(youtube_id="abc123")
        item = YoutubePlaylistItem.objects.get(playlist=playlist, video=video)
        self.assertEqual(item.order, 1)
