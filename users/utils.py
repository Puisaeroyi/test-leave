"""User utility functions."""

import logging
from datetime import date
from decimal import Decimal
from typing import Dict, Any

from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()
logger = logging.getLogger(__name__)


# Fixed defaults for non-dynamic balance types.
FIXED_BALANCE_DEFAULTS = {
    'SICK': Decimal('40.00'),
}


def create_initial_leave_balance(user):
    """Create initial leave balances for a new user.

    - VACATION: dynamic by years of service
    - SICK: fixed 40h
    """
    from leaves.models import LeaveBalance
    from leaves.services import calculate_vacation_hours

    current_year = date.today().year
    join_date = user.join_date or date.today()

    vacation_hours = calculate_vacation_hours(
        join_date=join_date,
        reference_date=date(current_year, 1, 1)
    )

    LeaveBalance.objects.get_or_create(
        user=user,
        year=current_year,
        balance_type=LeaveBalance.BalanceType.VACATION,
        defaults={
            'allocated_hours': vacation_hours,
            'used_hours': Decimal('0.00'),
            'adjusted_hours': Decimal('0.00'),
        }
    )

    for balance_type, hours in FIXED_BALANCE_DEFAULTS.items():
        LeaveBalance.objects.get_or_create(
            user=user,
            year=current_year,
            balance_type=balance_type,
            defaults={
                'allocated_hours': hours,
                'used_hours': Decimal('0.00'),
                'adjusted_hours': Decimal('0.00'),
            }
        )


def build_user_response(user: User, include_tokens: bool = False) -> Dict[str, Any]:
    """Build standardized user response dict.

    Args:
        user: User instance
        include_tokens: Whether to include JWT tokens in response

    Returns:
        Dictionary with user data matching API response format
    """
    response = {
        'id': str(user.id),
        'employee_code': user.employee_code,
        'email': user.email,
        'role': user.role,
        'status': user.status,
        'entity_id': str(user.entity.id) if user.entity else None,
        'entity_name': user.entity.entity_name if user.entity else None,
        'location_id': str(user.location.id) if user.location else None,
        'location_name': f"{user.location.location_name}, {user.location.city}" if user.location else None,
        'department_id': str(user.department.id) if user.department else None,
        'department_name': user.department.department_name if user.department else None,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'first_login': user.first_login,
    }

    # Add optional fields for specific endpoints
    if hasattr(user, 'join_date') and user.join_date:
        response['join_date'] = user.join_date.isoformat()
    if hasattr(user, 'avatar_url') and user.avatar_url:
        response['avatar_url'] = user.avatar_url

    # Add approver information (for all users)
    if hasattr(user, 'approver_1') and user.approver_1:
        approver = user.approver_1
        response['approver'] = {
            'id': str(approver.id),
            'email': approver.email,
            'first_name': approver.first_name,
            'last_name': approver.last_name,
            'full_name': f"{approver.first_name or ''} {approver.last_name or ''}".strip() or approver.email,
        }
    if hasattr(user, 'approver_2') and user.approver_2:
        final_approver = user.approver_2
        response['final_approver'] = {
            'id': str(final_approver.id),
            'email': final_approver.email,
            'first_name': final_approver.first_name,
            'last_name': final_approver.last_name,
            'full_name': f"{final_approver.first_name or ''} {final_approver.last_name or ''}".strip() or final_approver.email,
        }

    # Check if user is an approver for anyone (controls Manager Ticket visibility)
    from users.models import User as UserModel
    subordinates = UserModel.objects.filter(
        Q(approver_1=user) | Q(approver_2=user),
        is_active=True
    ).distinct()
    response['is_approver'] = subordinates.exists()

    if subordinates.exists():
        response['subordinates'] = [
            {
                'id': str(sub.id),
                'email': sub.email,
                'first_name': sub.first_name,
                'last_name': sub.last_name,
                'full_name': f"{sub.first_name or ''} {sub.last_name or ''}".strip() or sub.email,
                'entity': sub.entity.entity_name if sub.entity else None,
            }
            for sub in subordinates
        ]

    if include_tokens:
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)
        response['tokens'] = {
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }

    return response
