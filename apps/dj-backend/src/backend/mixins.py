from rest_framework_simplejwt.tokens import RefreshToken


class RefreshTokenMixin:

    def get_tokens_for_user(cls, user):
        refresh = RefreshToken.for_user(user)
        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
