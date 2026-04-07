from django.urls import path

from .views import (
    DiscordOAuthView,
    DiscordLoginView,
    DiscordProfileView,
    DiscordUserView,
    DiscordGuildView,
    GuildPlaylistView,
    GuildPlaylistAddSongView,
    GuildPlaylistRemoveSongView,
    GuildPlaylistNextView,
    GuildPlaylistPrevView,
    GuildPlaylistReorderView,
)

app_name = "discord"
# fmt: off
urlpatterns = [
    path("oauth", DiscordOAuthView.as_view(), name="oauth"),
    path("login", DiscordLoginView.as_view(), name="login"),
    path("profile", DiscordProfileView.as_view(), name="profile"),
    path("user/<str:user_id>/", DiscordUserView.as_view(), name="user"),
    path("guilds/<str:guild_id>/", DiscordGuildView.as_view(), name="guild"),
    path("guilds/<str:guild_id>/playlist/", GuildPlaylistView.as_view(), name="guild-playlist"),
    path("guilds/<str:guild_id>/playlist/add-song/", GuildPlaylistAddSongView.as_view(), name="guild-playlist-add-song"),
    path("guilds/<str:guild_id>/playlist/remove-song/", GuildPlaylistRemoveSongView.as_view(), name="guild-playlist-remove-song"),
    path("guilds/<str:guild_id>/playlist/next/", GuildPlaylistNextView.as_view(), name="guild-playlist-next"),
    path("guilds/<str:guild_id>/playlist/prev/", GuildPlaylistPrevView.as_view(), name="guild-playlist-prev"),
    path("guilds/<str:guild_id>/playlist/reorder/", GuildPlaylistReorderView.as_view(), name="guild-playlist-reorder"),
]
# fmt: on
