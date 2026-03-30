from django.urls import path, include

from .views import DiscordOAuthView, DiscordLoginView

app_name = "django"
urlpatterns = [
    path("oauth", DiscordOAuthView.as_view(), name="oauth"),
    path("login", DiscordLoginView.as_view(), name="login"),
]
