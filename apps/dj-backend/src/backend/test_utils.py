from django.conf import settings
from rest_framework.test import APIClient


def internal_client():
    client = APIClient()
    client.credentials(HTTP_X_INTERNAL_KEY=settings.INTERNAL_API_KEY)
    return client
