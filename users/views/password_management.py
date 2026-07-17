"""Password reset and authenticated change-password views."""

import logging

from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from core.services.email_service import send_password_reset_email
from users.utils import blacklist_all_refresh_tokens, build_user_response

User = get_user_model()
logger = logging.getLogger(__name__)

GENERIC_RESET_REQUEST_MESSAGE = (
    "If an account exists with this email, a reset link has been sent."
)
INVALID_RESET_LINK_ERROR = "Invalid or expired reset link."


class PasswordResetRequestThrottle(AnonRateThrottle):
    """Limit unauthenticated reset requests: 5 per hour per IP."""

    # Distinct scope so we do not share the global anon throttle cache key.
    scope = "password_reset"
    rate = "5/hour"


class PasswordResetRequestView(generics.GenericAPIView):
    """
    Request a password-reset email (enumeration-safe).
    POST /api/v1/auth/password-reset/request/
    """

    permission_classes = [AllowAny]
    throttle_classes = [PasswordResetRequestThrottle]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        from users.serializers import PasswordResetRequestSerializer

        serializer = PasswordResetRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data["email"]

        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user:
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            reset_url = (
                f"{settings.FRONTEND_BASE_URL}/reset-password"
                f"?uid={uid}&token={token}"
            )
            try:
                send_password_reset_email(user, reset_url)
            except Exception:
                logger.exception(
                    "Password reset email failed for user_id=%s", user.pk
                )

        return Response(
            {"message": GENERIC_RESET_REQUEST_MESSAGE},
            status=status.HTTP_200_OK,
        )


class PasswordResetConfirmView(generics.GenericAPIView):
    """
    Confirm password reset with uid + token + new password.
    POST /api/v1/auth/password-reset/confirm/
    """

    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        from users.serializers import PasswordResetConfirmSerializer

        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid = serializer.validated_data["uid"]
        token = serializer.validated_data["token"]
        password = serializer.validated_data["password"]

        try:
            user_id = force_str(urlsafe_base64_decode(uid))
            user = User.objects.get(pk=user_id)
        except (User.DoesNotExist, ValueError, TypeError, OverflowError):
            return Response(
                {"error": INVALID_RESET_LINK_ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not default_token_generator.check_token(user, token):
            return Response(
                {"error": INVALID_RESET_LINK_ERROR},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(password)
        # Password chosen via reset satisfies first-login requirement.
        update_fields = ["password"]
        if user.first_login:
            user.first_login = False
            update_fields.append("first_login")
        user.save(update_fields=update_fields)
        blacklist_all_refresh_tokens(user)

        return Response(
            {"message": "Password has been reset successfully."},
            status=status.HTTP_200_OK,
        )


class PasswordChangeView(generics.GenericAPIView):
    """
    Authenticated change password (current + new + confirm).
    POST /api/v1/auth/password-change/
    Blacklists all refresh tokens then returns a fresh token pair.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from users.serializers import PasswordChangeSerializer

        user = request.user
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={"user": user},
        )
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data["new_password"])
        user.save(update_fields=["password"])
        # Blacklist before issuing a new pair so the fresh refresh stays valid.
        blacklist_all_refresh_tokens(user)

        return Response(
            {
                "message": "Password changed successfully. Other devices have been signed out.",
                "user": build_user_response(user, include_tokens=True),
            },
            status=status.HTTP_200_OK,
        )
