from settings import settings

""" this is an api wrapper for the backend """


def play_url(video_id):
    return f"{settings.BACKEND_HOST}/api/youtube/videos/{video_id}/get-source/"
