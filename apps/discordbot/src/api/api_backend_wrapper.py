from settings import settings

""" this is an api wrapper for the backend """


def auth_headers():
    return {"X-Internal-Key": settings.INTERNAL_API_KEY}


def play_url(video_id):
    return f"{settings.BACKEND_HOST}/api/youtube/videos/{video_id}/get-source/"


def guild_queue_url(guild_id):
    return f"{settings.BACKEND_HOST}/api/discord/guild/{guild_id}/queue/"


def guild_queue_item_url(guild_id, item_id):
    return f"{settings.BACKEND_HOST}/api/discord/guild/{guild_id}/queue/items/{item_id}/"


def guild_queue_items_url(guild_id):
    return f"{settings.BACKEND_HOST}/api/discord/guild/{guild_id}/queue/items/"
