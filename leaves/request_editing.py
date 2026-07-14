"""Shared edit eligibility, canonicalization, and version helpers for PATCH flows."""

from datetime import date, datetime, time
from decimal import Decimal

from django.utils import timezone
from django.utils.dateparse import parse_datetime

from .models import LeaveRequest


LEAVE_EDITABLE_FIELDS = (
    'leave_category',
    'start_date',
    'end_date',
    'shift_type',
    'start_time',
    'end_time',
    'start_day_offset',
    'end_day_offset',
    'reason',
    'attachment_url',
)

LEAVE_MATERIAL_FIELDS = frozenset({
    'leave_category',
    'start_date',
    'end_date',
    'shift_type',
    'start_time',
    'end_time',
    'start_day_offset',
    'end_day_offset',
})

LEAVE_AUDIT_EXTRA_FIELDS = frozenset({'total_hours', 'leave_breakdown', 'balance_type_snapshot'})

TRIP_EDITABLE_FIELDS = (
    'city',
    'country',
    'start_date',
    'end_date',
    'note',
    'attachment_url',
)

# Keys accepted on leave PATCH besides editable model fields
LEAVE_PATCH_META_KEYS = frozenset({'expected_updated_at'})
TRIP_PATCH_META_KEYS = frozenset({'expected_updated_at'})

# Protected / never-writable leave keys (explicit rejection)
LEAVE_PROTECTED_KEYS = frozenset({
    'id', 'user', 'user_id', 'status', 'total_hours', 'leave_breakdown',
    'balance_type_snapshot', 'approved_by', 'approved_at', 'rejection_reason',
    'approver_comment', 'first_approver', 'final_approver', 'current_approval_step',
    'first_approval_status', 'final_approval_status', 'first_approval_comment',
    'final_approval_comment', 'first_approval_at', 'final_approval_at',
    'created_at', 'updated_at', 'can_edit',
})

TRIP_PROTECTED_KEYS = frozenset({
    'id', 'user', 'user_id', 'created_at', 'updated_at', 'can_edit',
})


def can_edit_leave_request(actor, leave_request) -> bool:
    """Owner may edit only while overall and both peer decisions remain PENDING."""
    if not actor or not leave_request:
        return False
    if leave_request.user_id != getattr(actor, 'id', None):
        return False
    if leave_request.status != LeaveRequest.Status.PENDING:
        return False
    if leave_request.first_approval_status != LeaveRequest.ApprovalDecision.PENDING:
        return False
    if leave_request.final_approval_status != LeaveRequest.ApprovalDecision.PENDING:
        return False
    return True


def can_edit_business_trip(actor, trip, owner_today: date) -> bool:
    """Owner may edit only when owner-local today is before persisted start date."""
    if not actor or not trip:
        return False
    if trip.user_id != getattr(actor, 'id', None):
        return False
    return owner_today < trip.start_date


def canonicalize_edit_value(field: str, value):
    """Normalize values so omitted/empty equivalents compare equal."""
    if field in {'attachment_url', 'reason', 'note', 'city', 'country'}:
        if value is None:
            return ''
        return str(value).strip() if field in {'city', 'country'} else (str(value) if value is not None else '')

    if field in {'start_date', 'end_date'}:
        if isinstance(value, date) and not isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, datetime):
            return value.date().isoformat()
        if value is None:
            return None
        return str(value)

    if field in {'start_time', 'end_time'}:
        if value is None or value == '':
            return None
        if isinstance(value, time):
            return value.strftime('%H:%M:%S')
        text = str(value)
        # Normalize HH:MM -> HH:MM:00 for stable compare
        if len(text) == 5 and text[2] == ':':
            return f'{text}:00'
        return text

    if field in {'start_day_offset', 'end_day_offset'}:
        if value is None or value == '':
            return 0
        return int(value)

    if field == 'leave_category':
        if value is None or value == '':
            return None
        return str(getattr(value, 'id', value))

    if field == 'total_hours':
        if value is None:
            return None
        return str(Decimal(str(value)).quantize(Decimal('0.01')))

    if field == 'balance_type_snapshot':
        return value or 'NONE'

    if field == 'leave_breakdown':
        return value if value is not None else []

    return value


def snapshot_fields(obj, fields) -> dict:
    """Build a canonical field snapshot from a model instance or dict-like."""
    result = {}
    for field in fields:
        if hasattr(obj, field):
            raw = getattr(obj, field)
            if field == 'leave_category':
                raw = getattr(obj, 'leave_category_id', None)
            result[field] = canonicalize_edit_value(field, raw)
        elif isinstance(obj, dict):
            result[field] = canonicalize_edit_value(field, obj.get(field))
    return result


def build_changed_values(before: dict, after: dict, fields) -> dict:
    """Return {field: (old, new)} for fields that actually changed."""
    changed = {}
    for field in fields:
        old = canonicalize_edit_value(field, before.get(field))
        new = canonicalize_edit_value(field, after.get(field))
        if old != new:
            changed[field] = (old, new)
    return changed


def has_material_leave_changes(changed: dict) -> bool:
    return bool(LEAVE_MATERIAL_FIELDS.intersection(changed.keys()))


def reject_unknown_keys(raw_data, allowed_keys, protected_keys=None):
    """
    Reject any raw payload key outside the allowed set.
    DRF's default ignore of unknown fields is not acceptable for PATCH.
    Returns (ok, error_message).
    """
    if raw_data is None:
        return True, None
    try:
        keys = set(raw_data.keys())
    except AttributeError:
        return False, 'Invalid request body'
    protected = protected_keys or set()
    unknown = keys - set(allowed_keys)
    if unknown:
        bad = sorted(unknown)
        if any(k in protected for k in bad):
            return False, f'Protected or unknown fields are not allowed: {", ".join(bad)}'
        return False, f'Unknown fields are not allowed: {", ".join(bad)}'
    return True, None


def parse_expected_updated_at(raw):
    """Parse client version token to aware datetime, or None if missing/invalid."""
    if raw is None or raw == '':
        return None
    if isinstance(raw, datetime):
        dt = raw
    else:
        text = str(raw).strip()
        dt = parse_datetime(text)
        if dt is None:
            # Accept "YYYY-MM-DDTHH:MM:SS.ffffffZ"
            if text.endswith('Z'):
                dt = parse_datetime(text[:-1] + '+00:00')
    if dt is None:
        return None
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone.get_current_timezone())
    return dt


def timestamps_match(expected, actual, tolerance_ms: int = 1) -> bool:
    """Compare version tokens with small tolerance for serialization rounding."""
    if expected is None or actual is None:
        return False
    exp = expected
    act = actual
    if timezone.is_naive(exp):
        exp = timezone.make_aware(exp, timezone.get_current_timezone())
    if timezone.is_naive(act):
        act = timezone.make_aware(act, timezone.get_current_timezone())
    delta = abs((exp - act).total_seconds())
    return delta <= (tolerance_ms / 1000.0)


def bump_updated_at(instance):
    """Explicitly advance updated_at so version tokens are monotonic on actual edits."""
    now = timezone.now()
    instance.updated_at = now
    return now


def redact_audit_values(values: dict) -> dict:
    """
    Store safe audit markers only — never raw medical reason text or attachment URLs.
    """
    if not values:
        return values
    redacted = {}
    for key, value in values.items():
        if key == 'reason':
            redacted[key] = '[changed]' if value not in (None, '') else '[empty]'
        elif key == 'attachment_url':
            redacted[key] = '[set]' if value not in (None, '') else '[removed]'
        elif key == 'leave_category':
            # Prefer readable name when caller already resolved it
            redacted[key] = value
        else:
            redacted[key] = value
    return redacted


def audit_payload_from_changed(changed: dict, extra_before=None, extra_after=None) -> tuple:
    """Build old/new audit dicts from changed field map {(field): (old, new)}."""
    old_values = {}
    new_values = {}
    for field, (old, new) in changed.items():
        old_values[field] = old
        new_values[field] = new
    if extra_before:
        old_values.update(extra_before)
    if extra_after:
        new_values.update(extra_after)
    return redact_audit_values(old_values), redact_audit_values(new_values)
