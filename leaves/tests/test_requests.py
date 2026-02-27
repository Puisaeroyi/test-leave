"""
Tests for Leave Request API
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from freezegun import freeze_time
from organizations.models import Entity, Location, Department
from leaves.models import LeaveCategory, LeaveBalance, LeaveRequest

User = get_user_model()


@pytest.fixture
def setup_user_with_balance():
    """Create a user with leave balance for testing"""
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
        name='Test Department',
        code='TEST'
    )

    user = User.objects.create_user(
        email='test@example.com',
        password='TestPass123!',
        first_name='Test',
        last_name='User',
        entity=entity,
        location=location,
        department=department,
        role=User.Role.EMPLOYEE,
    )

    # Get or create leave balance (signal may have already created it)
    balance, _ = LeaveBalance.objects.get_or_create(
        user=user,
        year=2026,
        defaults={
            'allocated_hours': Decimal('96.00'),
            'used_hours': Decimal('0.00')
        }
    )

    # Create leave category
    category = LeaveCategory.objects.create(
        name='Annual Leave',
        code='ANNUAL',
        color='#3B82F6'
    )

    return {'user': user, 'balance': balance, 'category': category, 'department': department}


@pytest.mark.django_db
class TestLeaveRequests:
    """Test leave request endpoints"""

    def test_create_full_day_request(self, setup_user_with_balance):
        """Test creating a full day leave request"""
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-01-20',
            'end_date': '2026-01-20',
            'shift_type': 'FULL_DAY',
            'leave_category': str(category.id),
            'reason': 'Personal business',
        })

        assert response.status_code == 201
        assert response.data['total_hours'] == 8.0
        assert LeaveRequest.objects.filter(user=user).count() == 1

    def test_create_multi_day_request(self, setup_user_with_balance):
        """Test creating a multi-day leave request"""
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-01-20',
            'end_date': '2026-01-22',
            'shift_type': 'FULL_DAY',
            'leave_category': str(category.id),
            'reason': 'Vacation',
        })

        assert response.status_code == 201
        # 3 days = 24 hours
        assert response.data['total_hours'] == 24.0

    def test_create_custom_hours_request(self, setup_user_with_balance):
        """Test creating a custom hours leave request"""
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-01-20',
            'end_date': '2026-01-20',
            'shift_type': 'CUSTOM_HOURS',
            'start_time': '09:00',
            'end_time': '13:00',
            'total_hours': 4.0,
            'leave_category': str(category.id),
            'reason': 'Doctor appointment',
        })

        assert response.status_code == 201
        assert response.data['total_hours'] == 4.0

    def test_create_request_insufficient_balance(self, setup_user_with_balance):
        """Test creating request with insufficient balance"""
        user = setup_user_with_balance['user']
        balance = setup_user_with_balance['balance']
        category = setup_user_with_balance['category']

        # Reduce balance to only 8 hours
        balance.allocated_hours = Decimal('8.00')
        balance.save()

        client = APIClient()
        client.force_authenticate(user=user)

        # Try to request 16 hours (2 days)
        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-01-20',
            'end_date': '2026-01-21',
            'shift_type': 'FULL_DAY',
            'leave_category': str(category.id),
            'reason': 'Long vacation',
        })

        assert response.status_code == 400

    def test_list_my_requests(self, setup_user_with_balance):
        """Test listing current user's leave requests"""
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']

        # Create some requests
        LeaveRequest.objects.create(
            user=user,
            leave_category=category,
            start_date=date(2026, 1, 20),
            end_date=date(2026, 1, 20),
            shift_type='FULL_DAY',
            total_hours=Decimal('8.0'),
            status='PENDING'
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/leaves/requests/my/')

        assert response.status_code == 200
        assert len(response.data) == 1

    def test_cancel_my_request(self, setup_user_with_balance):
        """Test cancelling own leave request"""
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']

        request = LeaveRequest.objects.create(
            user=user,
            leave_category=category,
            start_date=date(2026, 1, 20),
            end_date=date(2026, 1, 20),
            shift_type='FULL_DAY',
            total_hours=Decimal('8.0'),
            status='PENDING'
        )

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(f'/api/v1/leaves/requests/{request.id}/cancel/')

        assert response.status_code == 200

        # Refresh and verify status changed
        request.refresh_from_db()
        assert request.status == 'CANCELLED'


@pytest.mark.django_db
class TestLeaveApprovals:
    """Test leave approval endpoints"""

    def test_manager_approve_request(self, setup_user_with_balance):
        """Test manager approving a leave request"""
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']

        # Create manager and assign as user's approver
        manager = User.objects.create_user(
            email='manager@example.com',
            password='Manager123!',
            role=User.Role.MANAGER
        )
        user.approver = manager
        user.save()

        # Create leave request
        leave_request = LeaveRequest.objects.create(
            user=user,
            leave_category=category,
            start_date=date(2026, 1, 20),
            end_date=date(2026, 1, 20),
            shift_type='FULL_DAY',
            total_hours=Decimal('8.0'),
            status='PENDING'
        )

        client = APIClient()
        client.force_authenticate(user=manager)

        response = client.post(f'/api/v1/leaves/requests/{leave_request.id}/approve/', {
            'comment': 'Approved'
        })

        assert response.status_code == 200

        # Refresh and verify
        leave_request.refresh_from_db()
        assert leave_request.status == 'APPROVED'
        assert leave_request.approved_by == manager

    def test_hr_approve_request(self, setup_user_with_balance):
        """Test HR approving a leave request"""
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']

        # Create HR user
        hr = User.objects.create_user(
            email='hr@example.com',
            password='Hr123!',
            role=User.Role.HR
        )

        # Create leave request
        leave_request = LeaveRequest.objects.create(
            user=user,
            leave_category=category,
            start_date=date(2026, 1, 20),
            end_date=date(2026, 1, 20),
            shift_type='FULL_DAY',
            total_hours=Decimal('8.0'),
            status='PENDING'
        )

        client = APIClient()
        client.force_authenticate(user=hr)

        response = client.post(f'/api/v1/leaves/requests/{leave_request.id}/approve/')

        assert response.status_code == 200
        leave_request.refresh_from_db()
        assert leave_request.status == 'APPROVED'

    def test_employee_cannot_approve(self, setup_user_with_balance):
        """Test that regular employees cannot approve requests"""
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']

        # Create another employee
        other_user = User.objects.create_user(
            email='other@example.com',
            password='Other123!',
            role=User.Role.EMPLOYEE
        )

        # Create leave request
        leave_request = LeaveRequest.objects.create(
            user=user,
            leave_category=category,
            start_date=date(2026, 1, 20),
            end_date=date(2026, 1, 20),
            shift_type='FULL_DAY',
            total_hours=Decimal('8.0'),
            status='PENDING'
        )

        client = APIClient()
        client.force_authenticate(user=other_user)

        response = client.post(f'/api/v1/leaves/requests/{leave_request.id}/approve/')

        # Should return forbidden (403) due to permission class
        assert response.status_code == 403

    def test_reject_request(self, setup_user_with_balance):
        """Test rejecting a leave request"""
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']

        # Create manager and assign as user's approver
        manager = User.objects.create_user(
            email='manager@example.com',
            password='Manager123!',
            role=User.Role.MANAGER
        )
        user.approver = manager
        user.save()

        # Create leave request
        leave_request = LeaveRequest.objects.create(
            user=user,
            leave_category=category,
            start_date=date(2026, 1, 20),
            end_date=date(2026, 1, 20),
            shift_type='FULL_DAY',
            total_hours=Decimal('8.0'),
            status='PENDING'
        )

        client = APIClient()
        client.force_authenticate(user=manager)

        response = client.post(f'/api/v1/leaves/requests/{leave_request.id}/reject/', {
            'reason': 'Insufficient staff coverage'
        })

        assert response.status_code == 200
        leave_request.refresh_from_db()
        assert leave_request.status == 'REJECTED'
        assert leave_request.rejection_reason == 'Insufficient staff coverage'


@pytest.mark.django_db
class TestLeaveBalance:
    """Test leave balance endpoints"""

    def test_get_my_balance(self, setup_user_with_balance):
        """Test getting current user's leave balance"""
        user = setup_user_with_balance['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/leaves/balance/my/')

        assert response.status_code == 200
        assert response.data['allocated_hours'] == 96.0

    def test_hr_adjust_balance(self, setup_user_with_balance):
        """Test HR adjusting user balance"""
        user = setup_user_with_balance['user']

        # Create HR user
        hr = User.objects.create_user(
            email='hr@example.com',
            password='Hr123!',
            role=User.Role.HR
        )

        client = APIClient()
        client.force_authenticate(user=hr)

        response = client.post(f'/api/v1/auth/{user.id}/balance/adjust/', {
            'allocated_hours': 120,
            'reason': 'Additional leave granted'
        })

        assert response.status_code == 200
        assert response.data['allocated_hours'] == 120.0

    def test_employee_cannot_adjust_balance(self, setup_user_with_balance):
        """Test that regular employees cannot adjust balance"""
        user = setup_user_with_balance['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post(f'/api/v1/auth/{user.id}/balance/adjust/', {
            'allocated_hours': 200,
            'reason': 'I want more leave'
        })

        assert response.status_code == 403
