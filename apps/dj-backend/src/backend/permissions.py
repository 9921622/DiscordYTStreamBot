from rest_framework.permissions import BasePermission
from django.conf import settings


class IsInternalService(BasePermission):
    """permission for an internal service"""

    def has_permission(self, request, view):
        return request.headers.get("X-Internal-Key") == settings.INTERNAL_API_KEY
