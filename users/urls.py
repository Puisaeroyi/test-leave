"""
User & Authentication API URLs
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserMeView,
    OnboardingView,
    UserListView,
    UserDetailView,
    setup_user,
    adjust_balance,
    create_user,
)

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserMeView.as_view(), name='user_me'),
    path('onboarding/', OnboardingView.as_view(), name='onboarding'),

    # User Management
    path('', UserListView.as_view(), name='user_list'),
    path('create/', create_user, name='user_create'),
    path('<uuid:user_id>/', UserDetailView.as_view(), name='user_detail'),
    path('<uuid:user_id>/setup/', setup_user, name='user_setup'),
    path('<uuid:user_id>/balance/adjust/', adjust_balance, name='adjust_balance'),
]
