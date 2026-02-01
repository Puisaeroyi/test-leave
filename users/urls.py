"""
User & Authentication API URLs
"""
from django.urls import path

from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    UserMeView,
)

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('me/', UserMeView.as_view(), name='user_me'),
]
