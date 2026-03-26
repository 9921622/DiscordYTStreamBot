from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import YoutubeVideoViewSet, YoutubePlaylistViewSet, YoutubeSearchView

router = DefaultRouter()
router.register(r"videos", YoutubeVideoViewSet, basename="video")
router.register(r"playlists", YoutubePlaylistViewSet, basename="playlist")

app_name = "youtube"
urlpatterns = [
    path("", include(router.urls)),
    path("search", YoutubeSearchView.as_view(), name="search"),
]
