"""Leave balance views."""

import logging
from decimal import Decimal
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import LeaveBalance
from ..constants import DEFAULT_YEARLY_ALLOCATION, HOURS_PER_DAY
from core.models import Notification

logger = logging.getLogger(__name__)


class LeaveBalanceMeView(generics.RetrieveAPIView):
    """Get current user's leave balance."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/balances/me/?year=2026"""
        year = int(request.query_params.get('year', timezone.now().year))
        user = request.user

        # Get or create balance for this year
        balance, created = LeaveBalance.objects.get_or_create(
            user=user,
            year=year,
            defaults={'allocated_hours': Decimal(str(DEFAULT_YEARLY_ALLOCATION))}
        )

        return Response({
            'id': str(balance.id),
            'year': balance.year,
            'allocated_hours': float(balance.allocated_hours),
            'used_hours': float(balance.used_hours),
            'adjusted_hours': float(balance.adjusted_hours),
            'remaining_hours': float(balance.remaining_hours),
            'remaining_days': float(balance.remaining_hours) / HOURS_PER_DAY,
        })


class LeaveBalanceListView(generics.ListAPIView):
    """List all leave balances (HR/Admin)."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/balances/?year=2026"""
        # Check HR/Admin permission
        if request.user.role not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR/Admin can view all balances'},
                status=status.HTTP_403_FORBIDDEN
            )

        year = int(request.query_params.get('year', timezone.now().year))
        balances = LeaveBalance.objects.filter(year=year).select_related('user')

        data = [
            {
                'id': str(b.id),
                'user_id': str(b.user.id),
                'user_email': b.user.email,
                'user_name': f"{b.user.first_name} {b.user.last_name}".strip() or b.user.email,
                'year': b.year,
                'allocated_hours': float(b.allocated_hours),
                'used_hours': float(b.used_hours),
                'adjusted_hours': float(b.adjusted_hours),
                'remaining_hours': float(b.remaining_hours),
            }
            for b in balances
        ]
        return Response(data)


class LeaveBalanceAdjustView(generics.GenericAPIView):
    """Adjust user leave balance (HR only)."""

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        """POST /api/v1/leaves/balances/{user_id}/adjust/"""
        # Check HR/Admin permission
        if request.user.role not in ['HR', 'ADMIN']:
            return Response(
                {'error': 'Only HR/Admin can adjust balances'},
                status=status.HTTP_403_FORBIDDEN
            )

        user_id = kwargs.get('user_id')
        year = int(request.data.get('year', timezone.now().year))
        reason = request.data.get('reason', '')

        if not reason:
            return Response(
                {'error': 'Reason is required for adjustment'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            balance = LeaveBalance.objects.get(user_id=user_id, year=year)
        except LeaveBalance.DoesNotExist:
            return Response(
                {'error': 'Balance not found for this user/year'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Adjust allocated hours if provided
        if 'allocated_hours' in request.data:
            balance.allocated_hours = Decimal(str(request.data['allocated_hours']))

        # Add adjustment hours if provided
        if 'adjustment_hours' in request.data:
            balance.adjusted_hours += Decimal(str(request.data['adjustment_hours']))

        balance.save()

        # Create notification
        try:
            Notification.objects.create(
                user_id=user_id,
                type='BALANCE_ADJUSTED',
                title='Leave Balance Adjusted',
                message=f'Your leave balance has been adjusted. Reason: {reason}',
                link='/leaves/balance'
            )
        except Exception as e:
            logger.warning(f"Notification not created: {e}")

        return Response({
            'id': str(balance.id),
            'year': balance.year,
            'allocated_hours': float(balance.allocated_hours),
            'used_hours': float(balance.used_hours),
            'adjusted_hours': float(balance.adjusted_hours),
            'remaining_hours': float(balance.remaining_hours),
        })
