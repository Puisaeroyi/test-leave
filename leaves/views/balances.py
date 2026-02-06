"""Leave balance views."""

from datetime import date
from decimal import Decimal

from django.utils import timezone
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from ..models import LeaveBalance
from ..services import calculate_exempt_vacation_hours

# Default allocated hours for non-dynamic balance types
DEFAULT_BALANCE_ALLOCATION = {
    LeaveBalance.BalanceType.EXEMPT_VACATION: Decimal('80.00'),  # fallback only
    LeaveBalance.BalanceType.NON_EXEMPT_VACATION: Decimal('40.00'),
    LeaveBalance.BalanceType.EXEMPT_SICK: Decimal('40.00'),
    LeaveBalance.BalanceType.NON_EXEMPT_SICK: Decimal('40.00'),
}


class LeaveBalanceMeView(generics.RetrieveAPIView):
    """Get current user's leave balance - 4 separate balances."""

    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """GET /api/v1/leaves/balances/me/?year=2026"""
        year = int(request.query_params.get('year', timezone.now().year))
        user = request.user
        reference_date = date(year, 1, 1)

        balances = []
        for balance_type, default_hours in DEFAULT_BALANCE_ALLOCATION.items():
            # Use dynamic calculation for EXEMPT_VACATION
            if balance_type == LeaveBalance.BalanceType.EXEMPT_VACATION:
                default_hours = calculate_exempt_vacation_hours(
                    user.join_date, reference_date
                )

            balance, created = LeaveBalance.objects.get_or_create(
                user=user,
                year=year,
                balance_type=balance_type,
                defaults={'allocated_hours': default_hours},
            )

            balances.append({
                'type': balance_type,
                'label': balance.get_balance_type_display(),
                'allocated_hours': float(balance.allocated_hours),
                'used_hours': float(balance.used_hours),
                'adjusted_hours': float(balance.adjusted_hours),
                'remaining_hours': float(balance.remaining_hours),
            })

        return Response({'balances': balances})
