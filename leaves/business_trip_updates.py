"""Owner business-trip PATCH orchestration: cutoff, validate, audit (no alerts)."""

from datetime import datetime

from django.db import transaction
from rest_framework import status

from core.models import AuditLog
from users.models import User
from users.utils import get_user_local_date

from .models import BusinessTrip
from .request_editing import (
    TRIP_EDITABLE_FIELDS,
    TRIP_PATCH_META_KEYS,
    TRIP_PROTECTED_KEYS,
    audit_payload_from_changed,
    build_changed_values,
    bump_updated_at,
    can_edit_business_trip,
    reject_unknown_keys,
    snapshot_fields,
    timestamps_match,
)
from .serializers import BusinessTripSerializer, BusinessTripUpdateSerializer
from .utils import (
    check_overlapping_business_trips,
    validate_attachment_url,
    validate_leave_request_dates,
)


class TripUpdateError(Exception):
    def __init__(self, payload, http_status):
        self.payload = payload
        self.http_status = http_status
        super().__init__(str(payload))


def _actor_context(actor):
    return {'actor': actor, 'request': type('R', (), {'user': actor})()}


def serialize_trip(trip, actor):
    return BusinessTripSerializer(trip, context=_actor_context(actor)).data


def update_business_trip(actor, trip_id, raw_data):
    """Owner-only trip PATCH. Returns (response_data, http_status)."""
    allowed = set(TRIP_EDITABLE_FIELDS) | TRIP_PATCH_META_KEYS
    ok, err = reject_unknown_keys(raw_data, allowed, TRIP_PROTECTED_KEYS)
    if not ok:
        raise TripUpdateError({'error': err}, status.HTTP_400_BAD_REQUEST)

    if 'expected_updated_at' not in (raw_data or {}):
        raise TripUpdateError(
            {'error': 'expected_updated_at is required', 'code': 'version_required'},
            status.HTTP_428_PRECONDITION_REQUIRED,
        )

    serializer = BusinessTripUpdateSerializer(data=raw_data, partial=True)
    if not serializer.is_valid():
        raise TripUpdateError(serializer.errors, status.HTTP_400_BAD_REQUEST)
    patch = serializer.validated_data
    expected = patch.pop('expected_updated_at')

    with transaction.atomic():
        # Lock only business_trips row first (avoid FOR UPDATE on nullable outer joins).
        try:
            locked_id = (
                BusinessTrip.objects
                .select_for_update()
                .filter(id=trip_id, user=actor)
                .values_list('id', flat=True)
                .get()
            )
        except BusinessTrip.DoesNotExist:
            raise TripUpdateError(
                {'error': 'Business trip not found'},
                status.HTTP_404_NOT_FOUND,
            )

        trip = (
            BusinessTrip.objects
            .select_related('user', 'user__location')
            .get(id=locked_id)
        )

        if not timestamps_match(expected, trip.updated_at):
            raise TripUpdateError(
                {
                    'error': 'This trip was modified by someone else. Refresh and try again.',
                    'code': 'version_conflict',
                    'trip': serialize_trip(trip, actor),
                },
                status.HTTP_409_CONFLICT,
            )

        # Lock owner + location snapshot for deterministic cutoff
        User.objects.select_for_update().get(id=actor.id)
        owner_today = get_user_local_date(trip.user)

        if not can_edit_business_trip(actor, trip, owner_today):
            raise TripUpdateError(
                {
                    'error': 'This business trip can no longer be edited.',
                    'code': 'edit_locked',
                    'trip': serialize_trip(trip, actor),
                },
                status.HTTP_409_CONFLICT,
            )

        before = snapshot_fields(trip, TRIP_EDITABLE_FIELDS)
        candidate = dict(before)
        for field in TRIP_EDITABLE_FIELDS:
            if field not in patch:
                continue
            val = patch[field]
            if field in {'start_date', 'end_date'}:
                candidate[field] = val.isoformat()
            elif field == 'attachment_url':
                candidate[field] = '' if val is None else val
            else:
                candidate[field] = val

        start_date = datetime.strptime(candidate['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(candidate['end_date'], '%Y-%m-%d').date()

        is_valid, error = validate_leave_request_dates(start_date, end_date)
        if not is_valid:
            raise TripUpdateError({'error': error}, status.HTTP_400_BAD_REQUEST)

        # Effective new start must remain after owner-local today
        if start_date <= owner_today:
            raise TripUpdateError(
                {'error': 'Start date must be after today (in your location timezone).'},
                status.HTTP_400_BAD_REQUEST,
            )

        attachment_url = candidate.get('attachment_url') or ''
        is_valid, error = validate_attachment_url(attachment_url)
        if not is_valid:
            raise TripUpdateError({'error': error}, status.HTTP_400_BAD_REQUEST)

        overlapping = check_overlapping_business_trips(
            actor, start_date, end_date, exclude_trip_id=trip.id
        )
        if overlapping.exists():
            raise TripUpdateError(
                {'error': 'You have an overlapping business trip for these dates'},
                status.HTTP_400_BAD_REQUEST,
            )

        # Blank city/country not allowed
        if not (candidate.get('city') or '').strip():
            raise TripUpdateError(
                {'error': 'City is required'},
                status.HTTP_400_BAD_REQUEST,
            )
        if not (candidate.get('country') or '').strip():
            raise TripUpdateError(
                {'error': 'Country is required'},
                status.HTTP_400_BAD_REQUEST,
            )

        changed = build_changed_values(before, candidate, TRIP_EDITABLE_FIELDS)
        if not changed:
            return serialize_trip(trip, actor), status.HTTP_200_OK

        trip.city = candidate['city'].strip()
        trip.country = candidate['country'].strip()
        trip.start_date = start_date
        trip.end_date = end_date
        trip.note = candidate.get('note') or ''
        trip.attachment_url = attachment_url or None
        bump_updated_at(trip)
        trip.save()

        old_values, new_values = audit_payload_from_changed(changed)
        AuditLog.objects.create(
            user=actor,
            action='UPDATE',
            entity_type='BusinessTrip',
            entity_id=trip.id,
            old_values=old_values,
            new_values=new_values,
        )

        trip.refresh_from_db()
        return serialize_trip(trip, actor), status.HTTP_200_OK
