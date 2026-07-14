"""User utility functions."""

import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Dict, Any
from zoneinfo import ZoneInfo

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.utils import timezone as dj_timezone

User = get_user_model()
logger = logging.getLogger(__name__)


# Fixed defaults for non-dynamic balance types.
FIXED_BALANCE_DEFAULTS = {
    'SICK': Decimal('40.00'),
}


def _today_for_user_location(user: User) -> date:
    """Return today's date in the user's office timezone when available."""
    tz_name = getattr(getattr(user, 'location', None), 'timezone', None)
    if not tz_name:
        return dj_timezone.localdate()
    try:
        return datetime.now(ZoneInfo(tz_name)).date()
    except Exception:
        logger.warning("Invalid location timezone for user response: %s", tz_name)
        return dj_timezone.localdate()


def get_user_local_date(user: User) -> date:
    """Public wrapper for owner-local calendar date (trip cutoff / can_edit)."""
    return _today_for_user_location(user)


def _build_work_shift_today(user: User) -> Dict[str, Any] | None:
    """Resolve and serialize the assigned shift for today."""
    if not getattr(user, 'work_shift', None):
        return None

    from leaves.utils import resolve_work_shift_day

    today = _today_for_user_location(user)
    try:
        resolved = resolve_work_shift_day(user, today)
    except (ValueError, KeyError, TypeError, AttributeError):
        return None

    if not resolved:
        return None

    start_time = resolved.get('start_time')
    end_time = resolved.get('end_time')
    return {
        'date': today.isoformat(),
        'shift_name': resolved.get('shift_name'),
        'is_working': resolved.get('is_working', False),
        'start_time': start_time.strftime('%H:%M') if start_time else None,
        'end_time': end_time.strftime('%H:%M') if end_time else None,
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

    # Add assigned work shift (surfaced on the Profile page)
    if getattr(user, 'work_shift', None):
        shift = user.work_shift
        response['work_shift'] = {
            'id': str(shift.id),
            'name': shift.name,
            'pattern_type': shift.pattern_type,
            'start_time': shift.start_time.strftime('%H:%M') if shift.start_time else None,
            'end_time': shift.end_time.strftime('%H:%M') if shift.end_time else None,
            'includes_weekends': shift.includes_weekends,
            'cycle_days': shift.cycle_days,
        }
        work_shift_today = _build_work_shift_today(user)
        if work_shift_today:
            response['work_shift_today'] = work_shift_today

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
