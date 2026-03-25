from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import YoutubeVideoViewSet, YoutubePlaylistViewSet

router = DefaultRouter()
router.register(r"videos", YoutubeVideoViewSet, basename="video")
router.register(r"playlists", YoutubePlaylistViewSet, basename="playlist")

app_name = "youtube"
urlpatterns = [
    path("", include(router.urls)),
]
