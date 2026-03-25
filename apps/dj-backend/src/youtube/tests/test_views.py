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
