"""Tests for owner leave-request PATCH, version locks, audit, and alerts."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import AuditLog, Notification
from leaves.models import LeaveBalance, LeaveCategory, LeaveRequest
from organizations.models import Entity, Location, Department

User = get_user_model()


@pytest.fixture
def leave_edit_setup(db):
    entity = Entity.objects.create(entity_name='Edit Co', code='EDIT')
    location = Location.objects.create(
        entity=entity,
        location_name='HQ',
        city='Austin',
        country='US',
        timezone='America/Chicago',
    )
    department = Department.objects.create(
        entity=entity,
        location=location,
        department_name='Eng',
        code='ENG',
    )
    a1 = User.objects.create_user(
        email='a1-edit@example.com', password='Pass123!', role=User.Role.MANAGER,
        entity=entity, location=location, department=department,
    )
    a2 = User.objects.create_user(
        email='a2-edit@example.com', password='Pass123!', role=User.Role.MANAGER,
        entity=entity, location=location, department=department,
    )
    employee = User.objects.create_user(
        email='emp-edit@example.com', password='Pass123!',
        entity=entity, location=location, department=department,
        approver_1=a1, approver_2=a2,
    )
    category = LeaveCategory.objects.create(
        category_name='Vacation Edit',
        code='VAC_EDIT',
        balance_bucket='VACATION',
        is_active=True,
    )
    LeaveBalance.objects.update_or_create(
        user=employee, year=2026, balance_type='VACATION',
        defaults={
            'allocated_hours': Decimal('80.00'),
            'used_hours': Decimal('0.00'),
        },
    )
    leave = LeaveRequest.objects.create(
        user=employee,
        leave_category=category,
        start_date=date(2026, 8, 10),
        end_date=date(2026, 8, 10),
        shift_type=LeaveRequest.ShiftType.FULL_DAY,
        total_hours=Decimal('8.00'),
        status=LeaveRequest.Status.PENDING,
        reason='Original reason',
        first_approver=a1,
        final_approver=a2,
        balance_type_snapshot='VACATION',
    )
    return {
        'employee': employee,
        'a1': a1,
        'a2': a2,
        'category': category,
        'leave': leave,
        'entity': entity,
    }


def _client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def _version(leave):
    leave.refresh_from_db()
    return leave.updated_at.isoformat()


@pytest.mark.django_db
class TestLeaveRequestPatch:
    def test_owner_can_patch_reason_only_audits_without_alerts(self, leave_edit_setup):
        leave = leave_edit_setup['leave']
        emp = leave_edit_setup['employee']
        client = _client(emp)
        before_updated = leave.updated_at
        before_notifs = Notification.objects.count()

        resp = client.patch(
            f'/api/v1/leaves/requests/{leave.id}/',
            {
                'reason': 'Updated medical note',
                'expected_updated_at': _version(leave),
            },
            format='json',
        )
        assert resp.status_code == 200
        leave.refresh_from_db()
        assert leave.reason == 'Updated medical note'
        assert leave.updated_at > before_updated
        assert resp.data['can_edit'] is True
        assert Notification.objects.count() == before_notifs
        audit = AuditLog.objects.filter(
            entity_type='LeaveRequest', entity_id=leave.id, action='UPDATE'
        ).latest('created_at')
        # Redacted reason — no raw medical text
        assert 'medical' not in str(audit.new_values).lower()
        assert audit.new_values.get('reason') in ('[changed]', '[empty]')

    def test_material_edit_notifies_both_approvers(self, leave_edit_setup):
        leave = leave_edit_setup['leave']
        emp = leave_edit_setup['employee']
        client = _client(emp)
        new_end = date(2026, 8, 11)

        with patch('core.services.email_service._send') as mock_send:
            resp = client.patch(
                f'/api/v1/leaves/requests/{leave.id}/',
                {
                    'end_date': new_end.isoformat(),
                    'expected_updated_at': _version(leave),
                },
                format='json',
            )
        assert resp.status_code == 200
        leave.refresh_from_db()
        assert leave.end_date == new_end
        updated = Notification.objects.filter(type='LEAVE_UPDATED')
        assert updated.count() == 2
        recipients = {n.user_id for n in updated}
        assert recipients == {
            leave_edit_setup['a1'].id,
            leave_edit_setup['a2'].id,
        }

    def test_protected_fields_rejected(self, leave_edit_setup):
        leave = leave_edit_setup['leave']
        client = _client(leave_edit_setup['employee'])
        resp = client.patch(
            f'/api/v1/leaves/requests/{leave.id}/',
            {
                'status': 'APPROVED',
                'reason': 'x',
                'expected_updated_at': _version(leave),
            },
            format='json',
        )
        assert resp.status_code == 400
        leave.refresh_from_db()
        assert leave.status == 'PENDING'
        assert leave.reason == 'Original reason'

    def test_missing_version_returns_428(self, leave_edit_setup):
        leave = leave_edit_setup['leave']
        client = _client(leave_edit_setup['employee'])
        resp = client.patch(
            f'/api/v1/leaves/requests/{leave.id}/',
            {'reason': 'no version'},
            format='json',
        )
        assert resp.status_code == 428

    def test_stale_version_returns_409(self, leave_edit_setup):
        leave = leave_edit_setup['leave']
        client = _client(leave_edit_setup['employee'])
        stale = leave.updated_at.isoformat()
        # First real edit
        client.patch(
            f'/api/v1/leaves/requests/{leave.id}/',
            {'reason': 'first', 'expected_updated_at': stale},
            format='json',
        )
        resp = client.patch(
            f'/api/v1/leaves/requests/{leave.id}/',
            {'reason': 'second', 'expected_updated_at': stale},
            format='json',
        )
        assert resp.status_code == 409
        assert resp.data['code'] == 'version_conflict'

    def test_noop_returns_200_without_audit(self, leave_edit_setup):
        leave = leave_edit_setup['leave']
        client = _client(leave_edit_setup['employee'])
        before_count = AuditLog.objects.filter(
            entity_type='LeaveRequest', entity_id=leave.id, action='UPDATE'
        ).count()
        version = _version(leave)
        resp = client.patch(
            f'/api/v1/leaves/requests/{leave.id}/',
            {
                'reason': leave.reason,
                'expected_updated_at': version,
            },
            format='json',
        )
        assert resp.status_code == 200
        leave.refresh_from_db()
        assert leave.updated_at.isoformat() == version or str(leave.updated_at) in version
        after_count = AuditLog.objects.filter(
            entity_type='LeaveRequest', entity_id=leave.id, action='UPDATE'
        ).count()
        assert after_count == before_count

    def test_non_owner_gets_404(self, leave_edit_setup):
        leave = leave_edit_setup['leave']
        client = _client(leave_edit_setup['a1'])
        resp = client.patch(
            f'/api/v1/leaves/requests/{leave.id}/',
            {'reason': 'hack', 'expected_updated_at': _version(leave)},
            format='json',
        )
        assert resp.status_code == 404

    def test_peer_approved_locks_edit(self, leave_edit_setup):
        leave = leave_edit_setup['leave']
        leave.first_approval_status = LeaveRequest.ApprovalDecision.APPROVED
        leave.save()
        client = _client(leave_edit_setup['employee'])
        resp = client.patch(
            f'/api/v1/leaves/requests/{leave.id}/',
            {'reason': 'too late', 'expected_updated_at': _version(leave)},
            format='json',
        )
        assert resp.status_code == 409
        assert resp.data['code'] == 'edit_locked'

    def test_my_list_exposes_can_edit(self, leave_edit_setup):
        emp = leave_edit_setup['employee']
        client = _client(emp)
        resp = client.get('/api/v1/leaves/requests/my/')
        assert resp.status_code == 200
        row = next(r for r in resp.data if r['id'] == str(leave_edit_setup['leave'].id))
        assert row['can_edit'] is True
        assert 'updated_at' in row

    def test_approve_requires_version(self, leave_edit_setup):
        leave = leave_edit_setup['leave']
        client = _client(leave_edit_setup['a1'])
        resp = client.post(
            f'/api/v1/leaves/requests/{leave.id}/approve/',
            {'comment': 'ok'},
            format='json',
        )
        assert resp.status_code == 428

    def test_approve_stale_version_conflict(self, leave_edit_setup):
        leave = leave_edit_setup['leave']
        stale = leave.updated_at.isoformat()
        # Owner edits first
        _client(leave_edit_setup['employee']).patch(
            f'/api/v1/leaves/requests/{leave.id}/',
            {'reason': 'changed', 'expected_updated_at': stale},
            format='json',
        )
        resp = _client(leave_edit_setup['a1']).post(
            f'/api/v1/leaves/requests/{leave.id}/approve/',
            {'comment': 'ok', 'expected_updated_at': stale},
            format='json',
        )
        assert resp.status_code == 409

    def test_non_approver_stale_approve_does_not_leak_request(self, leave_edit_setup):
        """Authz must run before version so 409 cannot IDOR-leak leave detail."""
        leave = leave_edit_setup['leave']
        outsider = User.objects.create_user(
            email='outsider-edit@example.com',
            password='Pass123!',
            entity=leave_edit_setup['entity'],
        )
        resp = _client(outsider).post(
            f'/api/v1/leaves/requests/{leave.id}/approve/',
            {
                'comment': 'nope',
                'expected_updated_at': '2000-01-01T00:00:00Z',
            },
            format='json',
        )
        assert resp.status_code == 403
        body = str(resp.data)
        assert 'Original reason' not in body
        assert 'request' not in resp.data
