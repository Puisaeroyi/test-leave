"""Authentication views."""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import login

from ..utils import build_user_response


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

        # Update last login
        login(request, user)

        return Response({
            'user': build_user_response(user, include_tokens=True)
        }, status=status.HTTP_200_OK)


class ChangePasswordView(generics.GenericAPIView):
    """
    Change password endpoint (used for first login and general password change)
    POST /api/v1/auth/change-password/
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        from users.serializers import ChangePasswordSerializer

        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user
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
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                from rest_framework_simplejwt.tokens import RefreshToken
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({'message': 'Successfully logged out'}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {'error': 'Invalid token or already logged out'},
                status=status.HTTP_400_BAD_REQUEST
            )
