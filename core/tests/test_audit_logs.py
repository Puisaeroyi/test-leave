"""
Tests for Audit Log API (Phase 6)
"""
import pytest
import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from core.models import AuditLog
from leaves.models import LeaveRequest

User = get_user_model()


@pytest.fixture
def setup_audit_logs():
    """Create audit log data for testing"""
    # Create admin user
    admin_user = User.objects.create_user(
        email='admin@example.com',
        password='TestPass123!',
        role=User.Role.ADMIN
    )

    # Create regular user
    user = User.objects.create_user(
        email='test@example.com',
        password='TestPass123!'
    )

    # Create audit logs
    log1 = AuditLog.objects.create(
        user=admin_user,
        action='CREATE',
        entity_type='LeaveRequest',
        entity_id=uuid.uuid4(),
        new_values={'status': 'PENDING'},
        ip_address='127.0.0.1'
    )
    log2 = AuditLog.objects.create(
        user=admin_user,
        action='APPROVE',
        entity_type='LeaveRequest',
        entity_id=uuid.uuid4(),
        old_values={'status': 'PENDING'},
        new_values={'status': 'APPROVED'},
        ip_address='127.0.0.1'
    )

    return {
        'admin_user': admin_user,
        'user': user,
        'logs': [log1, log2]
    }


@pytest.mark.django_db
class TestAuditLogs:
    """Test audit log endpoints"""

    def test_list_audit_logs_admin(self, setup_audit_logs):
        """Test admin can list audit logs"""
        admin_user = setup_audit_logs['admin_user']

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get('/api/v1/notifications/audit-logs/')

        assert response.status_code == 200
        assert response.data['count'] == 2
        assert len(response.data['results']) == 2

    def test_list_audit_logs_employee_forbidden(self, setup_audit_logs):
        """Test regular employees cannot list audit logs"""
        user = setup_audit_logs['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/notifications/audit-logs/')

        assert response.status_code == 403

    def test_filter_audit_logs_by_action(self, setup_audit_logs):
        """Test filtering audit logs by action"""
        admin_user = setup_audit_logs['admin_user']

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get('/api/v1/notifications/audit-logs/?action=APPROVE')

        assert response.status_code == 200
        assert response.data['count'] == 1
        assert response.data['results'][0]['action'] == 'APPROVE'

    def test_filter_audit_logs_by_entity_type(self, setup_audit_logs):
        """Test filtering audit logs by entity type"""
        admin_user = setup_audit_logs['admin_user']

        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get('/api/v1/notifications/audit-logs/?entity_type=LeaveRequest')

        assert response.status_code == 200
        assert response.data['count'] == 2

    def test_audit_logs_can_be_ordered_oldest_first(self, setup_audit_logs):
        admin_user = setup_audit_logs['admin_user']
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get('/api/v1/notifications/audit-logs/?ordering=oldest&page_size=1')

        assert response.status_code == 200
        assert response.data['count'] == 2
        assert response.data['page'] == 1
        assert response.data['total_pages'] == 2
        assert response.data['results'][0]['id'] == str(setup_audit_logs['logs'][0].id)

    def test_successful_authenticated_mutation_is_logged_automatically(self, setup_audit_logs):
        admin_user = setup_audit_logs['admin_user']
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(admin_user).access_token}')

        response = client.post(
            '/api/v1/notifications/announcements/',
            {'title': 'Audit me', 'body': 'Mutation body'},
            format='json',
        )

        assert response.status_code == 201
        log = AuditLog.objects.filter(
            user=admin_user,
            entity_type='APIRequest',
            new_values__path='/api/v1/notifications/announcements/',
        ).latest('created_at')
        assert log.action == 'CREATE'
        assert log.new_values['method'] == 'POST'
        assert log.new_values['status_code'] == 201

    def test_failed_mutation_is_not_logged_automatically(self, setup_audit_logs):
        user = setup_audit_logs['user']
        client = APIClient()
        client.credentials(HTTP_AUTHORIZATION=f'Bearer {RefreshToken.for_user(user).access_token}')

        response = client.post(
            '/api/v1/notifications/announcements/',
            {'title': 'Forbidden', 'body': 'No access'},
            format='json',
        )

        assert response.status_code == 403
        assert not AuditLog.objects.filter(
            user=user,
            entity_type='APIRequest',
            new_values__path='/api/v1/notifications/announcements/',
        ).exists()

    def test_audit_logs_are_retained_when_actor_is_deleted(self, setup_audit_logs):
        admin_user = setup_audit_logs['admin_user']
        log_id = setup_audit_logs['logs'][0].id

        admin_user.delete()

        log = AuditLog.objects.get(id=log_id)
        assert log.user is None

    def test_leave_request_audit_log_has_human_readable_target_and_changes(self, setup_audit_logs):
        admin_user = setup_audit_logs['admin_user']
        employee = setup_audit_logs['user']
        leave = LeaveRequest.objects.create(
            user=employee,
            start_date='2026-06-08',
            end_date='2026-06-09',
            shift_type=LeaveRequest.ShiftType.FULL_DAY,
            total_hours='16.00',
            status=LeaveRequest.Status.APPROVED,
        )
        AuditLog.objects.create(
            user=admin_user,
            action='APPROVE',
            entity_type='LeaveRequest',
            entity_id=leave.id,
            old_values={'status': 'PENDING', 'step': 'FIRST'},
            new_values={
                'status': 'APPROVED',
                'step': 'FIRST',
                'approved_by': str(admin_user.id),
                'approved_at': '2026-06-08T02:28:11.712168+00:00',
                'comment': 'Looks good',
            },
        )
        client = APIClient()
        client.force_authenticate(user=admin_user)

        response = client.get('/api/v1/notifications/audit-logs/?action=APPROVE')

        row = response.data['results'][0]
        assert row['target_label'] == 'test@example.com leave, 2026-06-08 to 2026-06-09'
        assert row['summary'] == 'Approved leave request for test@example.com'
        assert {'field': 'Status', 'before': 'Pending', 'after': 'Approved'} in row['changes']
        assert {'field': 'Comment', 'before': None, 'after': 'Looks good'} in row['changes']
        approved_by_change = next(change for change in row['changes'] if change['field'] == 'Approved by')
        approved_at_change = next(change for change in row['changes'] if change['field'] == 'Approved at')
        assert approved_by_change['after'] == 'admin@example.com'
        assert approved_at_change['after'] == '2026-06-08T02:28:11.712168+00:00'
