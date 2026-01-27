"""
Tests for Leave Reports API (Phase 6)
"""
import pytest
from datetime import date
from decimal import Decimal
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from organizations.models import Entity, Location, Department
from leaves.models import LeaveCategory, LeaveBalance, LeaveRequest

User = get_user_model()


@pytest.fixture
def setup_reports_data():
    """Create data for reports testing"""
    entity = Entity.objects.create(name='Test Entity', code='TEST')
    location = Location.objects.create(
        entity=entity,
        name='Test Location',
        city='Test City',
        country='Test Country',
        timezone='UTC'
    )
    department = Department.objects.create(
        entity=entity,
        name='Engineering'
    )

    # Create HR user
    hr_user = User.objects.create_user(
        email='hr@example.com',
        password='TestPass123!',
        role=User.Role.HR
    )

    # Create regular user
    user = User.objects.create_user(
        email='test@example.com',
        password='TestPass123!',
        entity=entity,
        location=location,
        department=department
    )

    # Create category
    category = LeaveCategory.objects.create(
        name='Annual Leave',
        code='AL',
        color='#10B981'
    )

    # Create or get balance (signal may have created one)
    balance, _ = LeaveBalance.objects.get_or_create(
        user=user,
        year=2026,
        defaults={
            'allocated_hours': Decimal('96.00'),
            'used_hours': Decimal('16.00')
        }
    )
    # Update used_hours if balance already existed
    balance.used_hours = Decimal('16.00')
    balance.save()

    # Create some leave requests
    LeaveRequest.objects.create(
        user=user,
        leave_category=category,
        start_date=date(2026, 1, 15),
        end_date=date(2026, 1, 16),
        shift_type='FULL_DAY',
        total_hours=Decimal('16.00'),
        status='APPROVED'
    )
    LeaveRequest.objects.create(
        user=user,
        leave_category=category,
        start_date=date(2026, 2, 10),
        end_date=date(2026, 2, 10),
        shift_type='FULL_DAY',
        total_hours=Decimal('8.00'),
        status='PENDING'
    )

    return {
        'hr_user': hr_user,
        'user': user,
        'entity': entity,
        'department': department,
        'category': category
    }


@pytest.mark.django_db
class TestLeaveReports:
    """Test leave reports endpoints"""

    def test_get_reports_hr(self, setup_reports_data):
        """Test HR can access reports"""
        hr_user = setup_reports_data['hr_user']

        client = APIClient()
        client.force_authenticate(user=hr_user)

        response = client.get('/api/v1/leaves/reports/?year=2026')

        assert response.status_code == 200
        assert 'summary' in response.data
        assert 'balance_utilization' in response.data
        assert 'monthly_breakdown' in response.data
        assert 'by_category' in response.data
        assert response.data['summary']['total_requests'] == 2
        assert response.data['summary']['approved'] == 1
        assert response.data['summary']['pending'] == 1

    def test_get_reports_employee_forbidden(self, setup_reports_data):
        """Test employees cannot access reports"""
        user = setup_reports_data['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/leaves/reports/?year=2026')

        assert response.status_code == 403

    def test_reports_filter_by_department(self, setup_reports_data):
        """Test reports can be filtered by department"""
        hr_user = setup_reports_data['hr_user']
        department = setup_reports_data['department']

        client = APIClient()
        client.force_authenticate(user=hr_user)

        response = client.get(f'/api/v1/leaves/reports/?year=2026&department_id={department.id}')

        assert response.status_code == 200
        assert response.data['summary']['total_requests'] == 2
