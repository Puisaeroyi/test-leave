"""
Tests for Audit Log API (Phase 6)
"""
import pytest
import uuid
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from core.models import AuditLog

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
