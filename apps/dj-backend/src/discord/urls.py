from django.urls import path, include

from .views import (
    DiscordOAuthView,
    DiscordLoginView,
    DiscordProfileView,
    DiscordUserView,
    DiscordGuildView,
    GuildQueueView,
    GuildQueueItemView,
)

app_name = "discord"
urlpatterns = [
    path("oauth", DiscordOAuthView.as_view(), name="oauth"),
    path("login", DiscordLoginView.as_view(), name="login"),
    path("profile", DiscordProfileView.as_view(), name="profile"),
    path("user/<str:user_id>/", DiscordUserView.as_view(), name="user"),
    path("guild/<str:guild_id>/", DiscordGuildView.as_view(), name="guild"),
    path("guild/<str:guild_id>/queue/", GuildQueueView.as_view(), name="guild-queue"),
    path(
        "guild/<str:guild_id>/queue/items/",
        GuildQueueItemView.as_view(),
        name="guild-queue-items",
    ),
    path(
        "guild/<str:guild_id>/queue/items/<int:item_id>/",
        GuildQueueItemView.as_view(),
        name="guild-queue-item",
    ),
]
