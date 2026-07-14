"""Owner leave-request PATCH orchestration: lock, validate, recalc, audit, notify."""

from datetime import datetime
from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.response import Response

from core.models import AuditLog
from core.services.email_service import send_leave_updated_email_safe
from core.services.notification_service import (
    FRIENDLY_LEAVE_FIELD_LABELS,
    create_leave_updated_notification,
)
from users.models import User

from .models import LeaveBalance, LeaveCategory, LeaveRequest
from .request_editing import (
    LEAVE_AUDIT_EXTRA_FIELDS,
    LEAVE_EDITABLE_FIELDS,
    LEAVE_MATERIAL_FIELDS,
    LEAVE_PATCH_META_KEYS,
    LEAVE_PROTECTED_KEYS,
    audit_payload_from_changed,
    build_changed_values,
    bump_updated_at,
    can_edit_leave_request,
    has_material_leave_changes,
    reject_unknown_keys,
    snapshot_fields,
    timestamps_match,
)
from .serializers import LeaveRequestSerializer, LeaveRequestUpdateSerializer
from .services import BalanceCalculationService, LeaveApprovalService
from .utils import (
    calculate_full_day_leave_breakdown,
    calculate_leave_hours,
    check_overlapping_custom_hours,
    check_overlapping_requests,
    infer_custom_hour_offsets,
    validate_attachment_url,
    validate_leave_request_dates,
)


class LeaveUpdateError(Exception):
    """Carry HTTP status + payload for the view layer."""

    def __init__(self, payload, http_status):
        self.payload = payload
        self.http_status = http_status
        super().__init__(str(payload))


def _actor_context(actor):
    return {'actor': actor, 'request': type('R', (), {'user': actor})()}


def serialize_leave(leave_request, actor):
    return LeaveRequestSerializer(leave_request, context=_actor_context(actor)).data


def _version_required_response():
    return LeaveUpdateError(
        {
            'error': 'expected_updated_at is required',
            'code': 'version_required',
        },
        status.HTTP_428_PRECONDITION_REQUIRED,
    )


def _version_conflict_response(leave_request, actor):
    return LeaveUpdateError(
        {
            'error': 'This request was modified by someone else. Refresh and try again.',
            'code': 'version_conflict',
            'request': serialize_leave(leave_request, actor),
        },
        status.HTTP_409_CONFLICT,
    )


def _locked_response(leave_request, actor):
    return LeaveUpdateError(
        {
            'error': 'This leave request can no longer be edited.',
            'code': 'edit_locked',
            'request': serialize_leave(leave_request, actor),
        },
        status.HTTP_409_CONFLICT,
    )


def resolve_snapshotted_approvers(leave_request):
    """
    Distinct non-null snapshotted approvers.
    Legacy null snapshot rows fall back to current profile approvers and persist.
    """
    first = leave_request.first_approver
    final = leave_request.final_approver
    dirty = False
    if first is None and leave_request.user.approver_1_id:
        first = leave_request.user.approver_1
        leave_request.first_approver = first
        dirty = True
    if final is None and leave_request.user.approver_2_id:
        final = leave_request.user.approver_2
        leave_request.final_approver = final
        dirty = True
    if dirty:
        # Do not bump updated_at here — caller owns the version token
        leave_request.save(update_fields=['first_approver', 'final_approver'])

    seen = set()
    result = []
    for peer in (first, final):
        if peer is None:
            continue
        if peer.id in seen:
            continue
        # Skip inactive recipients for email/notify; still count as assigned for audit
        if not peer.is_active:
            continue
        seen.add(peer.id)
        result.append(peer)
    return result


def _friendly_display(field, value):
    if value is None or value == '':
        return '—'
    if field == 'leave_category':
        cat = LeaveCategory.objects.filter(id=value).first() if value else None
        return cat.category_name if cat else str(value)
    if field == 'shift_type':
        return str(value).replace('_', ' ').title()
    if field in {'start_time', 'end_time'} and value:
        text = str(value)
        return text[:5] if len(text) >= 5 else text
    if field == 'attachment_url':
        return 'Attached' if value not in (None, '') else 'None'
    if field == 'reason':
        return '[updated]' if value not in (None, '') else '—'
    return str(value)


def _build_email_change_rows(changed):
    rows = []
    for field, (old, new) in changed.items():
        if field in {'reason', 'attachment_url'}:
            continue
        label = FRIENDLY_LEAVE_FIELD_LABELS.get(field, field.replace('_', ' ').title())
        rows.append({
            'field': label,
            'before': _friendly_display(field, old),
            'after': _friendly_display(field, new),
        })
    return rows


def _category_audit_name(category_id):
    if not category_id:
        return None
    cat = LeaveCategory.objects.filter(id=category_id).first()
    return cat.category_name if cat else str(category_id)


def update_leave_request(actor, request_id, raw_data):
    """
    Owner-only leave PATCH. Returns (response_data, http_status).
    Raises LeaveUpdateError for controlled HTTP errors.
    """
    allowed = set(LEAVE_EDITABLE_FIELDS) | LEAVE_PATCH_META_KEYS
    ok, err = reject_unknown_keys(raw_data, allowed, LEAVE_PROTECTED_KEYS)
    if not ok:
        raise LeaveUpdateError({'error': err}, status.HTTP_400_BAD_REQUEST)

    if 'expected_updated_at' not in (raw_data or {}):
        raise _version_required_response()

    serializer = LeaveRequestUpdateSerializer(data=raw_data, partial=True)
    if not serializer.is_valid():
        raise LeaveUpdateError(serializer.errors, status.HTTP_400_BAD_REQUEST)
    patch = serializer.validated_data
    expected = patch.pop('expected_updated_at')

    email_jobs = []

    with transaction.atomic():
        # Lock only leave_requests row first. select_for_update + select_related on
        # nullable FKs produces OUTER JOINs; PostgreSQL rejects FOR UPDATE on those.
        try:
            locked_id = (
                LeaveRequest.objects
                .select_for_update()
                .filter(id=request_id, user=actor)
                .values_list('id', flat=True)
                .get()
            )
        except LeaveRequest.DoesNotExist:
            # Uniform 404 for non-owned / missing
            raise LeaveUpdateError(
                {'error': 'Leave request not found'},
                status.HTTP_404_NOT_FOUND,
            )

        leave = (
            LeaveRequest.objects
            .select_related(
                'user', 'user__approver_1', 'user__approver_2', 'user__entity',
                'leave_category', 'first_approver', 'final_approver',
            )
            .get(id=locked_id)
        )

        if not timestamps_match(expected, leave.updated_at):
            raise _version_conflict_response(leave, actor)

        if not can_edit_leave_request(actor, leave):
            raise _locked_response(leave, actor)

        if actor.entity and not actor.entity.is_active:
            raise LeaveUpdateError(
                {'error': 'Your entity has been deactivated. Cannot edit leave requests.'},
                status.HTTP_403_FORBIDDEN,
            )

        # Lock employee row when range validation may run
        User.objects.select_for_update().get(id=actor.id)

        before = snapshot_fields(leave, LEAVE_EDITABLE_FIELDS)
        before_extra = snapshot_fields(leave, LEAVE_AUDIT_EXTRA_FIELDS)

        # Merge candidate
        candidate = dict(before)
        for field in LEAVE_EDITABLE_FIELDS:
            if field in patch:
                val = patch[field]
                if field == 'leave_category':
                    candidate[field] = str(val) if val else None
                elif field == 'attachment_url':
                    candidate[field] = '' if val is None else val
                elif field in {'start_time', 'end_time'}:
                    candidate[field] = val.strftime('%H:%M:%S') if val is not None else None
                elif field in {'start_date', 'end_date'}:
                    candidate[field] = val.isoformat() if val else None
                else:
                    candidate[field] = val

        # Resolve shift / full-day normalization
        shift_type = candidate.get('shift_type') or leave.shift_type
        if shift_type == LeaveRequest.ShiftType.FULL_DAY:
            candidate['start_time'] = None
            candidate['end_time'] = None
            candidate['start_day_offset'] = 0
            candidate['end_day_offset'] = 0
        else:
            # Preserve existing offsets unless explicitly patched
            if 'start_day_offset' not in patch:
                candidate['start_day_offset'] = leave.start_day_offset
            if 'end_day_offset' not in patch:
                candidate['end_day_offset'] = leave.end_day_offset

        start_date = datetime.strptime(candidate['start_date'], '%Y-%m-%d').date()
        end_date = datetime.strptime(candidate['end_date'], '%Y-%m-%d').date()
        is_valid, error = validate_leave_request_dates(start_date, end_date)
        if not is_valid:
            raise LeaveUpdateError({'error': error}, status.HTTP_400_BAD_REQUEST)

        start_time = None
        end_time = None
        start_day_offset = int(candidate.get('start_day_offset') or 0)
        end_day_offset = int(candidate.get('end_day_offset') or 0)

        if shift_type == LeaveRequest.ShiftType.CUSTOM_HOURS:
            st = candidate.get('start_time')
            et = candidate.get('end_time')
            if not st or not et:
                raise LeaveUpdateError(
                    {'error': 'start_time and end_time required for CUSTOM_HOURS'},
                    status.HTTP_400_BAD_REQUEST,
                )
            start_time = datetime.strptime(st[:5], '%H:%M').time() if isinstance(st, str) else st
            end_time = datetime.strptime(et[:5], '%H:%M').time() if isinstance(et, str) else et
            # Match create: work_shift users always get server-inferred offsets
            # (never trust client offsets — frontend hour-only inference is incomplete).
            if actor.work_shift_id:
                if 'start_time' in patch or 'end_time' in patch or 'shift_type' in patch:
                    start_day_offset, end_day_offset = infer_custom_hour_offsets(
                        actor, start_time, end_time
                    )
                else:
                    # Preserve stored offsets when times unchanged
                    start_day_offset = leave.start_day_offset
                    end_day_offset = leave.end_day_offset
                candidate['start_day_offset'] = start_day_offset
                candidate['end_day_offset'] = end_day_offset

        attachment_url = candidate.get('attachment_url') or ''
        is_valid, error = validate_attachment_url(attachment_url)
        if not is_valid:
            raise LeaveUpdateError({'error': error}, status.HTTP_400_BAD_REQUEST)

        # Category: inactive current preserved; new selection must be active
        category_id = candidate.get('leave_category')
        leave_category = None
        if category_id:
            leave_category = LeaveCategory.objects.filter(id=category_id).first()
            if leave_category is None:
                raise LeaveUpdateError(
                    {'error': 'Invalid leave category'},
                    status.HTTP_400_BAD_REQUEST,
                )
            if (
                not leave_category.is_active
                and str(leave.leave_category_id) != str(category_id)
            ):
                raise LeaveUpdateError(
                    {'error': 'Cannot select an inactive leave category'},
                    status.HTTP_400_BAD_REQUEST,
                )

        # Overlaps (exclude self)
        overlapping = check_overlapping_requests(
            actor, start_date, end_date, exclude_request_id=leave.id
        )
        has_date_conflict = (
            overlapping.exists()
            if shift_type != LeaveRequest.ShiftType.CUSTOM_HOURS
            else overlapping.exclude(shift_type=LeaveRequest.ShiftType.CUSTOM_HOURS).exists()
        )
        if has_date_conflict:
            raise LeaveUpdateError(
                {'error': 'You have an overlapping leave request for these dates'},
                status.HTTP_400_BAD_REQUEST,
            )
        if shift_type == LeaveRequest.ShiftType.CUSTOM_HOURS:
            if check_overlapping_custom_hours(
                actor, start_date, start_time, end_time,
                start_day_offset, end_day_offset,
                exclude_request_id=leave.id,
            ):
                raise LeaveUpdateError(
                    {'error': 'You have an overlapping custom-hours leave request'},
                    status.HTTP_400_BAD_REQUEST,
                )

        # Recalculate derived
        try:
            if shift_type == LeaveRequest.ShiftType.FULL_DAY:
                total_hours, leave_breakdown = calculate_full_day_leave_breakdown(
                    actor, start_date, end_date,
                )
            else:
                total_hours = calculate_leave_hours(
                    actor, start_date, end_date, shift_type, start_time, end_time,
                    start_day_offset=start_day_offset, end_day_offset=end_day_offset,
                )
                leave_breakdown = []
        except ValueError as e:
            raise LeaveUpdateError({'error': str(e)}, status.HTTP_400_BAD_REQUEST)

        balance_type = BalanceCalculationService.calculate_balance_type(leave_category)
        year = start_date.year
        if balance_type != 'NONE':
            default_hours = BalanceCalculationService.calculate_default_allocation(
                balance_type, actor, year
            )
            balance, _ = LeaveBalance.objects.select_for_update().get_or_create(
                user=actor,
                year=year,
                balance_type=balance_type,
                defaults={'allocated_hours': default_hours},
            )
            if total_hours > balance.remaining_hours:
                raise LeaveUpdateError(
                    {
                        'error': (
                            f'Insufficient balance. Requested: {total_hours}h, '
                            f'Available: {balance.remaining_hours}h'
                        )
                    },
                    status.HTTP_400_BAD_REQUEST,
                )

        after = dict(candidate)
        after['leave_category'] = str(category_id) if category_id else None
        changed = build_changed_values(before, after, LEAVE_EDITABLE_FIELDS)

        # Also track derived diffs for audit only (when user fields actually change)
        derived_after = {
            'total_hours': str(Decimal(str(total_hours)).quantize(Decimal('0.01'))),
            'leave_breakdown': leave_breakdown,
            'balance_type_snapshot': balance_type,
        }
        derived_changed = build_changed_values(before_extra, derived_after, LEAVE_AUDIT_EXTRA_FIELDS)

        if not changed:
            # Canonical no-op: stable version, no audit (ignore derived-only drift)
            return serialize_leave(leave, actor), status.HTTP_200_OK

        # Apply fields
        leave.leave_category = leave_category
        leave.start_date = start_date
        leave.end_date = end_date
        leave.shift_type = shift_type
        leave.start_time = start_time
        leave.end_time = end_time
        leave.start_day_offset = start_day_offset
        leave.end_day_offset = end_day_offset
        leave.reason = after.get('reason') or ''
        leave.attachment_url = attachment_url or None
        leave.total_hours = total_hours
        leave.leave_breakdown = leave_breakdown
        leave.balance_type_snapshot = balance_type
        bump_updated_at(leave)
        leave.save()

        # Readable category names in audit
        audit_changed = dict(changed)
        if 'leave_category' in audit_changed:
            old_c, new_c = audit_changed['leave_category']
            audit_changed['leave_category'] = (
                _category_audit_name(old_c),
                _category_audit_name(new_c),
            )
        for field, pair in derived_changed.items():
            if field == 'leave_breakdown':
                continue  # skip large breakdown in audit JSON
            audit_changed[field] = pair

        old_values, new_values = audit_payload_from_changed(audit_changed)
        AuditLog.objects.create(
            user=actor,
            action='UPDATE',
            entity_type='LeaveRequest',
            entity_id=leave.id,
            old_values=old_values,
            new_values=new_values,
        )

        material = has_material_leave_changes(changed)
        if material:
            recipients = resolve_snapshotted_approvers(leave)
            notify_fields = [f for f in changed if f in LEAVE_MATERIAL_FIELDS]
            if 'total_hours' in derived_changed:
                notify_fields.append('total_hours')
            employee_name = leave.user.get_full_name() or leave.user.email
            category_name = (
                leave.leave_category.category_name if leave.leave_category else 'Leave'
            )
            email_rows = _build_email_change_rows(
                {**{k: changed[k] for k in changed if k in LEAVE_MATERIAL_FIELDS},
                 **({k: derived_changed[k] for k in derived_changed if k == 'total_hours'})}
            )
            for peer in recipients:
                create_leave_updated_notification(peer, leave, notify_fields)
                snapshot = {
                    'employee_name': employee_name,
                    'category': category_name,
                    'start_date': str(leave.start_date),
                    'end_date': str(leave.end_date),
                    'recipient_email': peer.email,
                }
                email_jobs.append((snapshot, email_rows))

            for snapshot, rows in email_jobs:
                transaction.on_commit(
                    lambda s=snapshot, r=rows: send_leave_updated_email_safe(None, s, r)
                )

        leave.refresh_from_db()
        response_data = serialize_leave(leave, actor)

    return response_data, status.HTTP_200_OK


def check_action_version(leave_request, expected_updated_at, actor):
    """Shared guard for approve/reject. Raises LeaveUpdateError on mismatch/missing."""
    if expected_updated_at is None:
        raise _version_required_response()
    if not timestamps_match(expected_updated_at, leave_request.updated_at):
        raise _version_conflict_response(leave_request, actor)
