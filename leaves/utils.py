"""
Leave Management Utilities
Hours calculation logic for leave requests
"""
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from .models import PublicHoliday, LeaveRequest
from django.db.models import Q


def calculate_leave_hours(user, start_date, end_date, shift_type, start_time=None, end_time=None):
    """
    Calculate total leave hours based on shift type, excluding weekends and holidays

    Args:
        user: User instance
        start_date: date object
        end_date: date object
        shift_type: 'FULL_DAY' or 'CUSTOM_HOURS'
        start_time: time object (required for CUSTOM_HOURS)
        end_time: time object (required for CUSTOM_HOURS)

    Returns:
        Decimal: Total hours
    """
    if shift_type == 'CUSTOM_HOURS':
        if not start_time or not end_time:
            raise ValueError("start_time and end_time required for CUSTOM_HOURS")

        # For custom hours, calculate time difference on start_date only
        start_dt = datetime.combine(start_date, start_time)
        end_dt = datetime.combine(start_date, end_time)

        # Handle case where end time is before start time (e.g., 23:00 to 01:00 next day)
        if end_dt < start_dt:
            end_dt = datetime.combine(start_date + timedelta(days=1), end_time)

        delta = end_dt - start_dt
        return Decimal(str(delta.total_seconds() / 3600)).quantize(Decimal('0.01'))

    # FULL_DAY: count working days (excludes weekends and holidays)
    holidays = get_holidays_for_user(user, start_date, end_date)
    # Expand multi-day holidays into individual dates
    holiday_dates = set()
    for h in holidays:
        current = h.start_date
        while current <= h.end_date:
            holiday_dates.add(current)
            current += timedelta(days=1)

    working_days = 0
    current = start_date

    while current <= end_date:
        # Skip weekends (5=Saturday, 6=Sunday)
        if current.weekday() < 5 and current not in holiday_dates:
            working_days += 1
        current += timedelta(days=1)

    # 8 hours per working day
    return Decimal(str(working_days * 8))


def get_holidays_for_user(user, start_date, end_date):
    """
    Get holidays applicable to user's entity/location

    Scope logic (in priority order):
    1. entity + location specific
    2. entity only (location=null)
    3. global (entity=null, location=null)

    Args:
        user: User instance
        start_date: date object
        end_date: date object

    Returns:
        QuerySet of PublicHoliday
    """
    # Build Q objects for holiday scoping
    queries = []

    # Global holidays
    queries.append(Q(entity__isnull=True, location__isnull=True))

    # Entity-specific holidays
    if user.entity:
        queries.append(Q(entity=user.entity, location__isnull=True))

    # Location-specific holidays
    if user.entity and user.location:
        queries.append(Q(entity=user.entity, location=user.location))

    # Combine with OR
    if queries:
        query = queries[0]
        for q in queries[1:]:
            query |= q
    else:
        query = Q(entity__isnull=True, location__isnull=True)

    return PublicHoliday.objects.filter(
        query,
        start_date__lte=end_date,
        end_date__gte=start_date,
        is_active=True
    )


def validate_leave_request_dates(start_date, end_date):
    """
    Validate that end_date is >= start_date

    Args:
        start_date: date object
        end_date: date object

    Returns:
        tuple: (is_valid, error_message)
    """
    if end_date < start_date:
        return False, "End date must be on or after start date"

    return True, None


def check_overlapping_requests(user, start_date, end_date, exclude_request_id=None):
    """
    Check for overlapping leave requests

    Args:
        user: User instance
        start_date: date object
        end_date: date object
        exclude_request_id: UUID of request to exclude (for updates)

    Returns:
        QuerySet of overlapping requests
    """
    overlapping = LeaveRequest.objects.filter(
        user=user,
        status__in=['PENDING', 'APPROVED'],
        start_date__lte=end_date,
        end_date__gte=start_date,
    )

    if exclude_request_id:
        overlapping = overlapping.exclude(id=exclude_request_id)

    return overlapping


def check_overlapping_business_trips(user, start_date, end_date, exclude_trip_id=None):
    """
    Check for overlapping business trips

    Args:
        user: User instance
        start_date: date object
        end_date: date object
        exclude_trip_id: UUID of trip to exclude (for updates)

    Returns:
        QuerySet of overlapping trips
    """
    from .models import BusinessTrip

    overlapping = BusinessTrip.objects.filter(
        user=user,
        start_date__lte=end_date,
        end_date__gte=start_date,
    )

    if exclude_trip_id:
        overlapping = overlapping.exclude(id=exclude_trip_id)

    return overlapping


def can_modify_request(request):
    """
    Check if a leave request can be modified (edited/cancelled)

    Args:
        request: LeaveRequest instance

    Returns:
        tuple: (can_modify, error_message)
    """
    if request.status not in ['PENDING']:
        return False, f"Only pending requests can be modified. Current status: {request.status}"

    return True, None
