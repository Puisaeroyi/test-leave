"""
User & Authentication API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    ChangePasswordView,
    LogoutView,
    UserMeView,
    UserBalanceAdjustView,
)
from .viewsets import UserViewSet

# ViewSet router for user management
router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # User management (ViewSet)
    path('', include(router.urls)),

    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change_password'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', UserMeView.as_view(), name='user_me'),

    # User management (HR/Admin)
    path('<uuid:pk>/balance/adjust/', UserBalanceAdjustView.as_view(), name='user_balance_adjust'),
]
