"""User profile views."""

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..utils import build_user_response


class UserMeView(generics.RetrieveAPIView):
    """
    Get current user info
    GET /api/v1/auth/me/
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        return Response(build_user_response(user))
