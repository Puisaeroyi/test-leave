"""
User & Authentication API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    LoginView,
    ChangePasswordView,
    LogoutView,
    GoogleOAuthView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    PasswordChangeView,
    UserMeView,
    UserBalanceAdjustView,
    AvatarUpdateView,
)
from .viewsets import UserViewSet

# ViewSet router for user management
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # User management (ViewSet)
    path('', include(router.urls)),

    # Authentication
    path('login/', LoginView.as_view(), name='login'),
    path('google/', GoogleOAuthView.as_view(), name='google_oauth'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('password-change/', PasswordChangeView.as_view(), name='password_change'),
    path(
        'password-reset/request/',
        PasswordResetRequestView.as_view(),
        name='password_reset_request',
    ),
    path(
        'password-reset/confirm/',
        PasswordResetConfirmView.as_view(),
        name='password_reset_confirm',
    ),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', UserMeView.as_view(), name='user_me'),
    path('avatar/', AvatarUpdateView.as_view(), name='avatar_update'),

    # User management (HR/Admin)
    path('<uuid:pk>/balance/adjust/', UserBalanceAdjustView.as_view(), name='user_balance_adjust'),
]
