"""Tests for collapsing old leave balance rows into new buckets."""
import importlib
from datetime import date
from decimal import Decimal

import pytest
from django.contrib.auth import get_user_model

from leaves.models import LeaveBalance
from organizations.models import Department, Entity, Location

User = get_user_model()


@pytest.fixture
def organization():
    entity = Entity.objects.create(entity_name='Merge Entity', code='MERGE')
    location = Location.objects.create(
        entity=entity,
        location_name='Merge Location',
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


def create_user(email, organization, **kwargs):
    entity, location, department = organization
    return User.objects.create_user(
        email=email,
        password='TestPass123!',
        entity=entity,
        location=location,
        department=department,
        **kwargs,
    )


@pytest.mark.django_db
def test_merge_leave_balances_preserves_old_vacation_usage(organization):
    user = create_user(
        'merge@example.com',
        organization=organization,
        join_date=date(2020, 1, 1),
    )
    LeaveBalance.objects.filter(user=user, year=2026).delete()
    LeaveBalance.objects.create(
        user=user,
        year=2026,
        balance_type='EXEMPT_VACATION',
        allocated_hours=Decimal('80.00'),
        used_hours=Decimal('12.00'),
    )
    LeaveBalance.objects.create(
        user=user,
        year=2026,
        balance_type='NON_EXEMPT_VACATION',
        allocated_hours=Decimal('40.00'),
        used_hours=Decimal('0.00'),
    )

    migration = importlib.import_module('leaves.migrations.0014_merge_leave_balances')

    class Apps:
        @staticmethod
        def get_model(app_label, model_name):
            if (app_label, model_name) == ('leaves', 'LeaveBalance'):
                return LeaveBalance
            if (app_label, model_name) == ('users', 'User'):
                return User
            raise LookupError(app_label, model_name)

    migration.merge_leave_balances(Apps(), None)

    vacation = LeaveBalance.objects.get(
        user=user,
        year=2026,
        balance_type='VACATION',
    )
    assert vacation.used_hours == Decimal('12.00')
    assert not LeaveBalance.objects.filter(
        user=user,
        year=2026,
        balance_type__in=['EXEMPT_VACATION', 'NON_EXEMPT_VACATION'],
    ).exists()
