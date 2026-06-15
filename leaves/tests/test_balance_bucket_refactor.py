"""Tests for category-driven leave balance buckets."""
from datetime import date
from decimal import Decimal
from io import StringIO

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from rest_framework.test import APIClient

from leaves.models import LeaveBalance, LeaveCategory, LeaveRequest
from leaves.services import BalanceCalculationService, LeaveApprovalService
from organizations.models import Department, Entity, Location

User = get_user_model()


@pytest.fixture
def organization():
    entity = Entity.objects.create(entity_name='Test Entity', code='TEST')
    location = Location.objects.create(
        entity=entity,
        location_name='Test Location',
        city='Test City',
        country='USA',
        timezone='UTC',
    )
    department = Department.objects.create(
        entity=entity,
        location=location,
        department_name='Engineering',
        code='ENG',
    )
    return entity, location, department


def create_user(email, organization=None, **kwargs):
    if organization:
        entity, location, department = organization
        kwargs.setdefault('entity', entity)
        kwargs.setdefault('location', location)
        kwargs.setdefault('department', department)
    return User.objects.create_user(
        email=email,
        password='TestPass123!',
        **kwargs,
    )


def get_category(code, name, bucket):
    category, _ = LeaveCategory.objects.update_or_create(
        code=code,
        defaults={
            'category_name': name,
            'balance_bucket': bucket,
            'requires_document': False,
            'is_active': True,
        },
    )
    return category


@pytest.mark.django_db
def test_calculate_balance_type_uses_category_bucket():
    vacation = get_category('VACATION', 'Vacation', 'VACATION')
    sick = get_category('SICK', 'Sick Leave', 'SICK')
    fmla = get_category('FMLA', 'FMLA Leave', 'NONE')

    assert BalanceCalculationService.calculate_balance_type(vacation) == 'VACATION'
    assert BalanceCalculationService.calculate_balance_type(sick) == 'SICK'
    assert BalanceCalculationService.calculate_balance_type(fmla) == 'NONE'
    assert BalanceCalculationService.calculate_balance_type(None) == 'NONE'


@pytest.mark.django_db
def test_none_bucket_request_submits_and_approves_without_balance_rows():
    manager = create_user('manager@example.com', role=User.Role.MANAGER)
    employee = create_user('employee@example.com', role=User.Role.EMPLOYEE)
    employee.approver_1 = manager
    employee.save()
    fmla = get_category('FMLA', 'FMLA Leave', 'NONE')

    client = APIClient()
    client.force_authenticate(user=employee)
    response = client.post('/api/v1/leaves/requests/', {
        'start_date': '2027-01-20',
        'end_date': '2027-01-20',
        'shift_type': 'FULL_DAY',
        'leave_category': str(fmla.id),
        'reason': 'Protected leave',
    })

    assert response.status_code == 201
    leave_request = LeaveRequest.objects.get(id=response.data['id'])
    assert LeaveBalance.objects.filter(user=employee, year=2027).count() == 0

    LeaveApprovalService.approve_leave_request(
        leave_request,
        manager,
        comment='Approved',
    )

    leave_request.refresh_from_db()
    assert leave_request.status == LeaveRequest.Status.APPROVED
    assert LeaveBalance.objects.filter(user=employee, year=2027).count() == 0

    history = client.get('/api/v1/leaves/requests/my/')
    assert history.status_code == 200
    assert str(leave_request.id) in [item['id'] for item in history.data]


@pytest.mark.django_db
def test_vacation_and_sick_buckets_deduct_their_own_balances():
    manager = create_user('approver@example.com', role=User.Role.MANAGER)
    employee = create_user('worker@example.com', role=User.Role.EMPLOYEE)
    employee.approver_1 = manager
    employee.save()
    vacation = get_category('VACATION', 'Vacation', 'VACATION')
    sick = get_category('SICK', 'Sick Leave', 'SICK')
    vacation_balance = LeaveBalance.objects.create(
        user=employee,
        year=2027,
        balance_type='VACATION',
        allocated_hours=Decimal('80.00'),
    )
    sick_balance = LeaveBalance.objects.create(
        user=employee,
        year=2027,
        balance_type='SICK',
        allocated_hours=Decimal('40.00'),
    )

    for category in (vacation, sick):
        leave_request = LeaveRequest.objects.create(
            user=employee,
            leave_category=category,
            start_date=date(2027, 2, 1),
            end_date=date(2027, 2, 1),
            shift_type='FULL_DAY',
            total_hours=Decimal('8.00'),
            status='PENDING',
            first_approver=manager,
        )
        LeaveApprovalService.approve_leave_request(leave_request, manager)

    vacation_balance.refresh_from_db()
    sick_balance.refresh_from_db()
    assert vacation_balance.used_hours == Decimal('8.00')
    assert sick_balance.used_hours == Decimal('8.00')


@pytest.mark.django_db
def test_pending_request_uses_balance_bucket_snapshot_when_category_changes():
    manager = create_user('snapshot-manager@example.com', role=User.Role.MANAGER)
    employee = create_user('snapshot-employee@example.com', role=User.Role.EMPLOYEE)
    employee.approver_1 = manager
    employee.save(update_fields=['approver_1'])
    vacation = get_category('SNAPSHOT_VACATION', 'Snapshot Vacation', 'VACATION')
    vacation_balance = LeaveBalance.objects.create(
        user=employee,
        year=2027,
        balance_type='VACATION',
        allocated_hours=Decimal('80.00'),
    )

    client = APIClient()
    client.force_authenticate(user=employee)
    response = client.post('/api/v1/leaves/requests/', {
        'start_date': '2027-03-01',
        'end_date': '2027-03-01',
        'shift_type': 'FULL_DAY',
        'leave_category': str(vacation.id),
        'reason': 'Snapshot category before approval',
    })
    assert response.status_code == 201

    vacation.balance_bucket = LeaveCategory.BalanceBucket.NONE
    vacation.save(update_fields=['balance_bucket'])
    leave_request = LeaveRequest.objects.get(id=response.data['id'])
    LeaveApprovalService.approve_leave_request(leave_request, manager)

    vacation_balance.refresh_from_db()
    assert vacation_balance.used_hours == Decimal('8.00')


@pytest.mark.django_db
def test_approved_request_restores_snapshot_bucket_after_category_deleted():
    manager = create_user('deleted-category-manager@example.com', role=User.Role.MANAGER)
    employee = create_user('deleted-category-employee@example.com', role=User.Role.EMPLOYEE)
    employee.approver_1 = manager
    employee.save(update_fields=['approver_1'])
    vacation = get_category('DELETED_VACATION', 'Deleted Vacation', 'VACATION')
    vacation_balance = LeaveBalance.objects.create(
        user=employee,
        year=2027,
        balance_type='VACATION',
        allocated_hours=Decimal('80.00'),
    )

    client = APIClient()
    client.force_authenticate(user=employee)
    response = client.post('/api/v1/leaves/requests/', {
        'start_date': '2027-04-01',
        'end_date': '2027-04-01',
        'shift_type': 'FULL_DAY',
        'leave_category': str(vacation.id),
        'reason': 'Snapshot category before deletion',
    })
    assert response.status_code == 201

    leave_request = LeaveRequest.objects.get(id=response.data['id'])
    LeaveApprovalService.approve_leave_request(leave_request, manager)
    vacation.delete()
    leave_request.refresh_from_db()
    LeaveApprovalService.reject_leave_request(
        leave_request,
        manager,
        'Category was removed after approval',
    )

    vacation_balance.refresh_from_db()
    assert vacation_balance.used_hours == Decimal('0.00')


@pytest.mark.django_db
def test_recalculate_command_writes_only_vacation_and_sick(organization):
    user = create_user(
        'onboarded@example.com',
        organization=organization,
        join_date=date(2020, 1, 1),
    )
    LeaveBalance.objects.filter(user=user, year=2026).delete()

    call_command(
        'recalculate_exempt_vacation',
        year=2026,
        stdout=StringIO(),
    )

    assert set(
        LeaveBalance.objects.filter(user=user, year=2026)
        .values_list('balance_type', flat=True)
    ) == {'VACATION', 'SICK'}
    assert not LeaveBalance.objects.filter(
        user=user,
        year=2026,
        balance_type__in=[
            'EXEMPT_VACATION',
            'NON_EXEMPT_VACATION',
            'EXEMPT_SICK',
            'NON_EXEMPT_SICK',
        ],
    ).exists()
