"""
User ViewSet for HR/Admin user management
"""
from rest_framework import viewsets, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import User
from .serializers.serializers import UserSerializer, UserUpdateSerializer


class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for user management (HR/Admin only)

    - list: GET /api/v1/auth/users/ - List all users
    - retrieve: GET /api/v1/auth/users/{id}/ - Get user details
    - update: PUT/PATCH /api/v1/auth/users/{id}/ - Update user (including approver)
    - subordinates: GET /api/v1/auth/users/my-subordinates/ - Get current user's subordinates
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    # Disable pagination to return all users at once
    pagination_class = None

    def get_queryset(self):
        """
        HR/Admin can see all users, Managers see their subordinates,
        Employees see only themselves
        """
        user = self.request.user

        if user.role in [User.Role.HR, User.Role.ADMIN]:
            return User.objects.all().select_related('entity', 'location', 'department', 'approver')
        elif user.role == User.Role.MANAGER:
            return User.objects.filter(approver=user).select_related('entity', 'location', 'department', 'approver')
        else:
            # Employees can only see themselves
            return User.objects.filter(id=user.id).select_related('entity', 'location', 'department', 'approver')

    def get_serializer_class(self):
        """Use UserUpdateSerializer for update operations"""
        if self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def update(self, request, *args, **kwargs):
        """
        Update user (HR/Admin only for most fields)

        Only HR/Admin can change:
        - approver
        - status
        """
        user = request.user

        # Only HR/Admin can update other users
        if user.role not in [User.Role.HR, User.Role.ADMIN]:
            return Response(
                {'error': 'Only HR and Admin can update users.'},
                status=status.HTTP_403_FORBIDDEN
            )

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        Delete user (Admin only)

        Only Admin can delete users, and cannot delete themselves
        """
        user = request.user
        target_user = self.get_object()

        # Only Admin can delete users
        if user.role != User.Role.ADMIN:
            return Response(
                {'error': 'Only Admin can delete users.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Cannot delete yourself
        if target_user.id == user.id:
            return Response(
                {'error': 'You cannot delete your own account.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='my-subordinates')
    def my_subordinates(self, request):
        """
        GET /api/v1/users/my-subordinates/

        Returns list of users who have the current user as their approver
        """
        subordinates = User.objects.filter(
            approver=request.user,
            is_active=True
        ).select_related('entity', 'location', 'department')

        serializer = UserSerializer(subordinates, many=True)
        return Response(serializer.data)
