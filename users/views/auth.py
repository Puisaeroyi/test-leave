"""Authentication views."""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db import IntegrityError
import logging

from ..utils import build_user_response
from ..services.google_oauth import validate_google_id_token, extract_user_info

User = get_user_model()
logger = logging.getLogger(__name__)


class GoogleOAuthRateThrottle(AnonRateThrottle):
    """Rate limit for Google OAuth endpoint to prevent abuse."""
    rate = '10/minute'


class RegisterView(generics.CreateAPIView):
    """
    User registration endpoint (includes onboarding)
    POST /api/v1/auth/register/
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        from users.serializers import RegisterSerializer
        from users.utils import create_initial_leave_balance

        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create initial leave balances (all 4 types)
        create_initial_leave_balance(user)

        return Response({
            'user': build_user_response(user, include_tokens=True)
        }, status=status.HTTP_201_CREATED)


class LoginView(generics.GenericAPIView):
    """
    User login endpoint
    POST /api/v1/auth/login/
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        from users.serializers import LoginSerializer

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']

        # Update last login (no session needed — JWT handles auth)
        user.last_login = timezone.now()
        user.save(update_fields=['last_login'])

        return Response({
            'user': build_user_response(user, include_tokens=True)
        }, status=status.HTTP_200_OK)


class ChangePasswordView(generics.GenericAPIView):
    """
    Change password endpoint (first login only).
    POST /api/v1/auth/change-password/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from users.serializers import ChangePasswordSerializer

        user = request.user

        # Only allow password change on first login
        if not user.first_login:
            return Response(
                {'error': 'Password has already been changed. Contact HR to reset.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user.set_password(serializer.validated_data['password'])
        user.first_login = False
        user.save(update_fields=['password', 'first_login'])

        return Response({
            'message': 'Password changed successfully',
            'user': build_user_response(user, include_tokens=True)
        }, status=status.HTTP_200_OK)


class LogoutView(generics.GenericAPIView):
    """
    User logout endpoint (blacklist refresh token)
    POST /api/v1/auth/logout/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception:
            return Response(
                {'error': 'Invalid token or already logged out'},
                status=status.HTTP_400_BAD_REQUEST
            )


class GoogleOAuthView(generics.GenericAPIView):
    """
    Google OAuth 2.0 login endpoint.
    POST /api/v1/auth/google/

    Accepts a Google ID token from the frontend, validates it server-side,
    and authenticates the user if their email is already registered.
    """
    permission_classes = [AllowAny]
    throttle_classes = [GoogleOAuthRateThrottle]

    def post(self, request, *args, **kwargs):
        id_token = request.data.get('id_token')

        if not id_token:
            return Response(
                {'error': 'ID token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate token with Google
            token_data = validate_google_id_token(id_token)
            user_info = extract_user_info(token_data)

            # Verify email is verified by Google
            if not user_info.get('email_verified'):
                logger.warning(f"Unverified Google email attempt: {user_info.get('email')}")
                return Response(
                    {'error': 'Email must be verified with Google'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Find user by email (whitelist approach)
            try:
                user = User.objects.get(email=user_info['email'])
            except User.DoesNotExist:
                logger.info(f"Unregistered email OAuth attempt: {user_info.get('email')}")
                return Response(
                    {'error': 'This email is not registered. Please contact HR.'},
                    status=status.HTTP_403_FORBIDDEN
                )

            # Link Google account on first OAuth login
            update_fields = ['last_login']
            if not user.google_id:
                user.google_id = user_info['google_id']
                update_fields.append('google_id')

            # Set avatar from Google if empty
            if not user.avatar_url and user_info.get('picture'):
                user.avatar_url = user_info['picture']
                update_fields.append('avatar_url')

            # OAuth users bypass first_login requirement
            if user.first_login:
                user.first_login = False
                update_fields.append('first_login')

            user.last_login = timezone.now()

            # Handle race condition for google_id (another user might have claimed it)
            try:
                user.save(update_fields=update_fields)
            except IntegrityError:
                logger.warning(f"Google ID already linked to another user: {user_info['google_id']}")
                return Response(
                    {'error': 'This Google account is already linked to another user'},
                    status=status.HTTP_409_CONFLICT
                )

            # Audit logging
            logger.info(
                f"Google OAuth login successful: user={user.email}, "
                f"google_id={user_info['google_id']}, ip={self.get_client_ip(request)}"
            )

            return Response({
                'user': build_user_response(user, include_tokens=True)
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            logger.warning(f"Google OAuth validation error: {str(e)}")
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Google OAuth unexpected error: {str(e)}")
            return Response(
                {'error': 'Authentication failed. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_client_ip(self, request):
        """Extract client IP for audit logging."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
