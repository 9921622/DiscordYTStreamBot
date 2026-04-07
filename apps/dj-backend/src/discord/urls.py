from django.urls import path, include

from .views import (
    DiscordOAuthView,
    DiscordLoginView,
    DiscordProfileView,
    DiscordUserView,
    DiscordGuildView,
    GuildPlaylistView,
    GuildPlaylistItemView,
    GuildPlaylistNavigationView,
)

app_name = "discord"
urlpatterns = [
    path("oauth", DiscordOAuthView.as_view(), name="oauth"),
    path("login", DiscordLoginView.as_view(), name="login"),
    path("profile", DiscordProfileView.as_view(), name="profile"),
    path("user/<str:user_id>/", DiscordUserView.as_view(), name="user"),
    path("guilds/<str:guild_id>/", DiscordGuildView.as_view(), name="guild"),
    path("guilds/<str:guild_id>/playlist/", GuildPlaylistView.as_view(), name="guild-playlist"),
    path("guilds/<str:guild_id>/playlist/items/", GuildPlaylistItemView.as_view(), name="guild-playlist-items"),
    path(
        "guilds/<str:guild_id>/playlist/items/<int:item_id>/",
        GuildPlaylistItemView.as_view(),
        name="guild-playlist-item",
    ),
    path(
        "guilds/<str:guild_id>/playlist/<str:direction>/",
        GuildPlaylistNavigationView.as_view(),
        name="guild-playlist-navigate",
    ),
]
