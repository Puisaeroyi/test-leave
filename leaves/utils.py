"""
Leave Management Utilities
Hours calculation logic for leave requests
"""
from datetime import datetime, timedelta, date, time
from decimal import Decimal
import re
import unicodedata

from django.db.models import Q

from .models import PublicHoliday, LeaveRequest

ZERO_DEDUCTIBLE_HOURS_MESSAGE = (
    'No deductible working hours were found for the selected date range. '
    'Choose a scheduled working day that is not a weekend, public holiday, '
    'or cycle off day.'
)


def normalize_country_code(value):
    """Map supported free-text country names to application country codes."""
    text = unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z]", "", text).lower()
    if text in {"us", "usa", "unitedstates", "unitedstatesofamerica"}:
        return "US"
    if text in {"vn", "vietnam"}:
        return "VN"
    return None


def holiday_country_scope_for_user(user):
    """Limit calendar-backed holidays to the user's location country when known."""
    country_code = normalize_country_code(getattr(getattr(user, "location", None), "country", None))
    if not country_code:
        return Q()
    return Q(calendar__country_code=country_code)


def is_working_day(user, day):
    """Return whether this date should deduct full-day leave for the user."""
    resolved = resolve_work_shift_day(user, day)
    if resolved:
        return resolved['is_working']
    shift = getattr(user, 'work_shift', None)
    if not shift:
        return day.weekday() < 5
    return bool(shift and shift.includes_weekends) or day.weekday() < 5


def _time_from_cycle_value(value):
    if isinstance(value, time):
        return value
    hour, minute = map(int, value.split(':'))
    return time(hour, minute)


def _hours_between(start, end):
    start = _time_from_cycle_value(start)
    end = _time_from_cycle_value(end)
    start_dt = datetime.combine(date.min, start)
    end_dt = datetime.combine(date.min, end)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return Decimal(str((end_dt - start_dt).total_seconds() / 3600)).quantize(Decimal('0.01'))


def _shift_hours(start, end, break_start=None, break_end=None):
    hours = _hours_between(start, end)
    if break_start and break_end:
        hours -= _hours_between(break_start, break_end)
    return max(hours, Decimal('0.00'))


def resolve_work_shift_day(user, day):
    """Resolve the user's assigned shift for a work date without materializing schedules."""
    shift = getattr(user, 'work_shift', None)
    if not shift:
        return None
    if shift.pattern_type == 'ROTATING_CYCLE':
        anchor = getattr(user, 'shift_cycle_start_date', None)
        if not anchor:
            raise ValueError('Rotating shift users require a cycle start date')
        cycle_days = shift.cycle_days or []
        if not cycle_days:
            raise ValueError('Rotating shift has no cycle days configured')
        item = cycle_days[(day - anchor).days % len(cycle_days)]
        if not item.get('is_working', True):
            return {
                'date': day,
                'shift_name': item.get('name') or 'Off',
                'is_working': False,
                'hours': Decimal('0.00'),
            }
        start = _time_from_cycle_value(item['start_time'])
        end = _time_from_cycle_value(item['end_time'])
        break_start = (
            _time_from_cycle_value(item['break_start_time'])
            if item.get('break_start_time') else None
        )
        break_end = (
            _time_from_cycle_value(item['break_end_time'])
            if item.get('break_end_time') else None
        )
        return {
            'date': day,
            'shift_name': item.get('name') or shift.name,
            'is_working': True,
            'start_time': start,
            'end_time': end,
            'break_start_time': break_start,
            'break_end_time': break_end,
            'hours': _shift_hours(start, end, break_start, break_end),
        }
    if shift.includes_weekends or day.weekday() < 5:
        return {
            'date': day,
            'shift_name': shift.name,
            'is_working': True,
            'start_time': shift.start_time,
            'end_time': shift.end_time,
            'break_start_time': shift.break_start_time,
            'break_end_time': shift.break_end_time,
            'hours': _shift_hours(
                shift.start_time,
                shift.end_time,
                shift.break_start_time,
                shift.break_end_time,
            ),
        }
    return {
        'date': day,
        'shift_name': 'Off',
        'is_working': False,
        'hours': Decimal('0.00'),
    }


def calculate_leave_hours(
    user, start_date, end_date, shift_type, start_time=None, end_time=None,
    exclude_calendar_id=None, start_day_offset=0, end_day_offset=0,
):
    """
    Calculate total leave hours based on shift type, excluding non-working days and holidays

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

        if not is_working_day(user, start_date):
            return Decimal('0.00')
        department = getattr(user, 'department', None)
        holiday_requires_leave = bool(
            department and department.holiday_requires_leave
        )
        if (
            not holiday_requires_leave
            and get_holidays_for_user(
                user,
                start_date,
                start_date,
                exclude_calendar_id,
            ).exists()
        ):
            return Decimal('0.00')

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
        hours = Decimal(str(delta.total_seconds() / 3600)).quantize(Decimal('0.01'))
        shift = getattr(user, 'work_shift', None)
        if shift and shift.break_start_time and shift.break_end_time:
            break_date = start_date
            if (
                shift.end_time <= shift.start_time
                and shift.break_start_time < shift.start_time
            ):
                break_date += timedelta(days=1)
            break_start_dt = datetime.combine(break_date, shift.break_start_time)
            break_end_dt = datetime.combine(break_date, shift.break_end_time)
            if break_end_dt <= break_start_dt:
                break_end_dt += timedelta(days=1)
            overlap_start = max(start_dt, break_start_dt)
            overlap_end = min(end_dt, break_end_dt)
            if overlap_end > overlap_start:
                overlap = Decimal(
                    str((overlap_end - overlap_start).total_seconds() / 3600)
                ).quantize(Decimal('0.01'))
                hours -= overlap
        return max(hours, Decimal('0.00'))

    total_hours, _ = calculate_full_day_leave_breakdown(user, start_date, end_date, exclude_calendar_id)
    return total_hours


def calculate_full_day_leave_breakdown(user, start_date, end_date, exclude_calendar_id=None):
    total_hours = Decimal('0')
    breakdown = []
    current = start_date
    while current <= end_date:
        resolved = resolve_work_shift_day(user, current)
        if not is_working_day(user, current):
            breakdown.append({
                'date': current.isoformat(),
                'shift_name': (resolved or {}).get('shift_name', 'Off'),
                'start_time': None,
                'end_time': None,
                'hours': 0.0,
                'reason': 'OFF',
            })
            current += timedelta(days=1)
            continue
        hours = resolved['hours'] if resolved else Decimal('8')
        if not resolved:
            total_hours += hours
            breakdown.append(_breakdown_row(current, resolved, hours, 'WORK'))
            current += timedelta(days=1)
            continue
        if user.department_id and user.department.holiday_requires_leave:
            total_hours += hours
            breakdown.append(_breakdown_row(current, resolved, hours, 'WORK'))
            current += timedelta(days=1)
            continue
        if not get_holidays_for_user(user, current, current, exclude_calendar_id).exists():
            total_hours += hours
            breakdown.append(_breakdown_row(current, resolved, hours, 'WORK'))
        else:
            breakdown.append(_breakdown_row(current, resolved, Decimal('0.00'), 'HOLIDAY'))
        current += timedelta(days=1)

    return total_hours, breakdown


def _breakdown_row(day, resolved, hours, reason):
    row = {
        'date': day.isoformat(),
        'shift_name': (resolved or {}).get('shift_name', 'Standard day'),
        'start_time': (resolved or {}).get('start_time').strftime('%H:%M') if (resolved or {}).get('start_time') else None,
        'end_time': (resolved or {}).get('end_time').strftime('%H:%M') if (resolved or {}).get('end_time') else None,
        'hours': float(hours),
        'reason': reason,
    }
    if (resolved or {}).get('break_start_time'):
        row['break_start_time'] = resolved['break_start_time'].strftime('%H:%M')
        row['break_end_time'] = resolved['break_end_time'].strftime('%H:%M')
    return row


def infer_custom_hour_offsets(user, start_time, end_time):
    """Infer actual calendar-day offsets from the user's assigned work shift."""
    shift = getattr(user, 'work_shift', None)
    if not shift:
        return 0, 1 if end_time <= start_time else 0
    if shift.end_time <= shift.start_time:
        if start_time < shift.start_time:
            return 1, 1 if end_time >= start_time else 2
        if end_time <= shift.end_time:
            return 0, 1
    return 0, 1 if end_time <= start_time else 0


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
        query & holiday_country_scope_for_user(user),
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
