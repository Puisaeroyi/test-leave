"""
Leave Management Utilities
Hours calculation logic for leave requests
"""
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from .models import PublicHoliday, LeaveRequest
from django.db.models import Q


def calculate_leave_hours(
    user, start_date, end_date, shift_type, start_time=None, end_time=None,
    exclude_calendar_id=None, start_day_offset=0, end_day_offset=0,
):
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
        if start_day_offset not in (0, 1) or end_day_offset not in (0, 1, 2):
            raise ValueError("Invalid custom-hour calendar day")
        start_dt = datetime.combine(start_date + timedelta(days=start_day_offset), start_time)
        end_dt = datetime.combine(start_date + timedelta(days=end_day_offset), end_time)

        if end_dt <= start_dt and end_day_offset == start_day_offset:
            end_dt += timedelta(days=1)

        delta = end_dt - start_dt
        if delta.total_seconds() <= 0:
            raise ValueError("Custom-hour end must be after start")
        if delta > timedelta(hours=8):
            raise ValueError("Custom leave cannot exceed 8 hours")
        return Decimal(str(delta.total_seconds() / 3600)).quantize(Decimal('0.01'))

    # FULL_DAY: count working days (excludes weekends and holidays)
    holidays = (
        PublicHoliday.objects.none()
        if user.department_id and user.department.holiday_requires_leave
        else get_holidays_for_user(user, start_date, end_date, exclude_calendar_id)
    )
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


def infer_custom_hour_offsets(user, start_time, end_time):
    """Infer actual calendar-day offsets from the employee's assigned overnight shift."""
    shift = getattr(user, 'work_shift', None)
    if not shift:
        return 0, 1 if end_time <= start_time else 0
    shift_start = (
        datetime.strptime(shift.start_time, '%H:%M').time()
        if isinstance(shift.start_time, str) else shift.start_time
    )
    shift_end = (
        datetime.strptime(shift.end_time, '%H:%M').time()
        if isinstance(shift.end_time, str) else shift.end_time
    )
    if shift_end > shift_start:
        return 0, 1 if end_time <= start_time else 0

    start_offset = 1 if start_time < shift_start else 0
    end_offset = 1 if end_time <= shift_end else 0
    if end_time <= start_time and end_offset <= start_offset:
        end_offset = start_offset + 1
    return start_offset, end_offset


def get_holidays_for_user(user, start_date, end_date, exclude_calendar_id=None):
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

    holidays = PublicHoliday.objects.filter(
        query,
        start_date__lte=end_date,
        end_date__gte=start_date,
        is_active=True,
        status=PublicHoliday.Status.PUBLISHED,
    )
    if exclude_calendar_id:
        holidays = holidays.exclude(calendar_id=exclude_calendar_id)
    return holidays


def validate_leave_request_dates(start_date, end_date):
    """
    Validate leave request dates: end >= start and same year.

    Returns:
        tuple: (is_valid, error_message)
    """
    if end_date < start_date:
        return False, "End date must be on or after start date"

    if start_date.year != end_date.year:
        return False, "Leave requests cannot span across years. Please submit separate requests for each year."

    return True, None


def validate_attachment_url(url):
    """
    Validate attachment_url matches expected media path pattern.
    Accepts empty string (no attachment) or /media/attachments/{uuid}.{ext}

    Returns:
        tuple: (is_valid, error_message)
    """
    if not url:
        return True, None

    import re
    pattern = r'^(https?://[^/]+)?/media/attachments/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\.(pdf|jpe?g|png|gif|webp)$'
    if not re.match(pattern, url, re.IGNORECASE):
        return False, "Invalid attachment URL. Must be a file uploaded through the upload endpoint."

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


def custom_hour_datetimes(work_date, start_time, end_time, start_day_offset=0, end_day_offset=0):
    """Return actual calendar datetimes for a custom-hours request."""
    start_dt = datetime.combine(work_date + timedelta(days=start_day_offset), start_time)
    end_dt = datetime.combine(work_date + timedelta(days=end_day_offset), end_time)
    if end_dt <= start_dt and end_day_offset == start_day_offset:
        end_dt += timedelta(days=1)
    return start_dt, end_dt


def check_overlapping_custom_hours(
    user, work_date, start_time, end_time, start_day_offset=0, end_day_offset=0
):
    """Find active custom-hour requests overlapping the actual calendar time range."""
    start_dt, end_dt = custom_hour_datetimes(
        work_date, start_time, end_time, start_day_offset, end_day_offset
    )
    candidates = LeaveRequest.objects.filter(
        user=user,
        shift_type=LeaveRequest.ShiftType.CUSTOM_HOURS,
        status__in=[LeaveRequest.Status.PENDING, LeaveRequest.Status.APPROVED],
        start_date__range=(work_date - timedelta(days=2), work_date + timedelta(days=2)),
    )
    for leave in candidates:
        existing_start, existing_end = custom_hour_datetimes(
            leave.start_date,
            leave.start_time,
            leave.end_time,
            leave.start_day_offset,
            leave.end_day_offset,
        )
        if start_dt < existing_end and end_dt > existing_start:
            return True
    return False


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
