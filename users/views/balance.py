"""User balance adjustment view (HR/Admin only)."""

from decimal import Decimal
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from users.permissions import IsHROrAdmin
from leaves.models import LeaveBalance
from leaves.constants import DEFAULT_YEARLY_ALLOCATION
from core.services.notification_service import create_balance_adjusted_notification


class UserBalanceAdjustView(generics.GenericAPIView):
    """
    Adjust user's leave balance (HR/Admin only).
    PUT /api/v1/auth/{id}/balance/adjust/
    """

    permission_classes = [IsAuthenticated, IsHROrAdmin]

    def put(self, request, *args, **kwargs):
        """Adjust a user's leave balance allocation."""
        user_id = kwargs.get('pk')
        hr_admin = request.user

        # Get target user
        from users.models import User
        try:
            target_user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get parameters
        allocated_hours = request.data.get('allocated_hours')
        reason = request.data.get('reason', '')

        if allocated_hours is None:
            return Response(
                {'error': 'allocated_hours is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            allocated_hours = Decimal(str(allocated_hours))
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid allocated_hours value'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get year (default to current year)
        from django.utils import timezone
        year = request.data.get('year', timezone.now().year)

        # Get or create balance
        balance, created = LeaveBalance.objects.get_or_create(
            user=target_user,
            year=year,
            defaults={'allocated_hours': Decimal(str(DEFAULT_YEARLY_ALLOCATION))}
        )

        # Calculate adjustment
        old_allocated = balance.allocated_hours
        balance.allocated_hours = allocated_hours
        balance.save()

        # Calculate adjustment amount
        adjustment = float(allocated_hours - old_allocated)

        # Create notification for the user
        if adjustment != 0:
            create_balance_adjusted_notification(target_user, adjustment, year)

        return Response({
            'id': str(balance.id),
            'user_id': str(target_user.id),
            'year': balance.year,
            'allocated_hours': float(balance.allocated_hours),
            'used_hours': float(balance.used_hours),
            'adjusted_hours': float(balance.adjusted_hours),
            'remaining_hours': float(balance.remaining_hours),
            'message': f'Balance adjusted by {adjustment:+.1f} hours'
        }, status=status.HTTP_200_OK)
