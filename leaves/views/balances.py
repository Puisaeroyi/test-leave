"""Leave balance views."""

from decimal import Decimal
from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import LeaveBalance
from ..constants import DEFAULT_YEARLY_ALLOCATION, HOURS_PER_DAY


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
