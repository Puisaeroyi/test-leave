"""
User & Authentication API URLs
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    RegisterView,
    LoginView,
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
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', UserMeView.as_view(), name='user_me'),

    # User management (HR/Admin)
    path('<uuid:pk>/balance/adjust/', UserBalanceAdjustView.as_view(), name='user_balance_adjust'),
]
