"""
Tests for the leave request hours preview endpoint.

The preview endpoint must return the real deductible hours (excluding Off days,
non-working weekends, and holidays) and stay in lock-step with the value the
create endpoint persists.
"""
import pytest
from decimal import Decimal
from datetime import date

from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from organizations.models import Department, Entity, Location, WorkShift
from leaves.models import LeaveCategory, LeaveBalance, PublicHoliday

User = get_user_model()

PREVIEW_URL = '/api/v1/leaves/requests/preview/'


@pytest.fixture
def soc_user():
    """Rotating SOC-shift user (Morning/Evening/Night/Off) with a vacation balance."""
    entity = Entity.objects.create(entity_name='Preview Entity', code='PRV')
    location = Location.objects.create(
        entity=entity, location_name='Preview Loc', city='City',
        country='Test Country', timezone='UTC',
    )
    department = Department.objects.create(
        entity=entity, location=location, department_name='SOC', code='SOC',
    )
    user = User.objects.create_user(
        email='soc@example.com', password='TestPass123!',
        first_name='Soc', last_name='Analyst',
        entity=entity, location=location, department=department,
        role=User.Role.EMPLOYEE,
    )
    approver = User.objects.create_user(
        email='soc-approver@example.com', password='ApproverPass123!',
        role=User.Role.MANAGER,
    )
    user.approver_1 = approver
    user.work_shift = WorkShift.objects.create(
        department=department,
        name='SOC Four Day Rotation',
        pattern_type=WorkShift.PatternType.ROTATING_CYCLE,
        start_time='06:00',
        end_time='14:00',
        includes_weekends=True,
        cycle_days=[
            {'name': 'Morning', 'start_time': '06:00', 'end_time': '14:00', 'is_working': True},
            {'name': 'Evening', 'start_time': '14:00', 'end_time': '22:00', 'is_working': True},
            {'name': 'Night', 'start_time': '22:00', 'end_time': '06:00', 'is_working': True},
            {'name': 'Off', 'is_working': False},
        ],
    )
    user.shift_cycle_start_date = date(2026, 7, 11)  # index 0 = Morning
    user.save(update_fields=['approver_1', 'work_shift', 'shift_cycle_start_date'])

    LeaveBalance.objects.get_or_create(
        user=user, year=2026, balance_type='VACATION',
        defaults={'allocated_hours': Decimal('96.00'), 'used_hours': Decimal('0.00')},
    )
    category = LeaveCategory.objects.create(
        category_name='Annual Leave', code='ANNUAL', balance_bucket='VACATION',
    )
    return {'user': user, 'category': category, 'department': department,
            'entity': entity, 'location': location}


@pytest.mark.django_db
class TestLeaveRequestPreview:

    def test_off_day_excluded_from_preview(self, soc_user):
        """2-day range covering 1 working (Night) + 1 Off day => 8h, Off row at 0h."""
        client = APIClient()
        client.force_authenticate(user=soc_user['user'])

        response = client.post(PREVIEW_URL, {
            'start_date': '2026-07-13',  # Night (working)
            'end_date': '2026-07-14',    # Off
            'shift_type': 'FULL_DAY',
        })

        assert response.status_code == 200, response.data
        assert response.data['total_hours'] == 8.0
        assert response.data['breakdown'] == [
            {'date': '2026-07-13', 'shift_name': 'Night', 'start_time': '22:00',
             'end_time': '06:00', 'hours': 8.0, 'reason': 'WORK'},
            {'date': '2026-07-14', 'shift_name': 'Off', 'start_time': None,
             'end_time': None, 'hours': 0.0, 'reason': 'OFF'},
        ]

    def test_preview_matches_create_total(self, soc_user):
        """Parity guard: preview total must equal the persisted create total."""
        client = APIClient()
        client.force_authenticate(user=soc_user['user'])
        payload_dates = {'start_date': '2026-07-13', 'end_date': '2026-07-15'}

        preview = client.post(PREVIEW_URL, {**payload_dates, 'shift_type': 'FULL_DAY'})
        created = client.post('/api/v1/leaves/requests/', {
            **payload_dates,
            'shift_type': 'FULL_DAY',
            'leave_category': str(soc_user['category'].id),
            'reason': 'Parity check',
        })

        assert preview.status_code == 200, preview.data
        assert created.status_code == 201, created.data
        assert preview.data['total_hours'] == created.data['total_hours']
        assert preview.data['breakdown'] == created.data['leave_breakdown']

    def test_holiday_excluded_from_preview(self, soc_user):
        """A published holiday on a working day shows 0h / HOLIDAY in the breakdown."""
        PublicHoliday.objects.create(
            entity=soc_user['entity'],
            location=soc_user['location'],
            holiday_name='Test Holiday',
            start_date=date(2026, 7, 13),  # Night working day
            end_date=date(2026, 7, 13),
            year=2026,
            is_active=True,
            status=PublicHoliday.Status.PUBLISHED,
        )
        client = APIClient()
        client.force_authenticate(user=soc_user['user'])

        response = client.post(PREVIEW_URL, {
            'start_date': '2026-07-13',
            'end_date': '2026-07-13',
            'shift_type': 'FULL_DAY',
        })

        assert response.status_code == 200, response.data
        assert response.data['total_hours'] == 0.0
        assert response.data['breakdown'][0]['reason'] == 'HOLIDAY'
        assert response.data['breakdown'][0]['hours'] == 0.0

    def test_requires_authentication(self, soc_user):
        response = APIClient().post(PREVIEW_URL, {
            'start_date': '2026-07-13', 'end_date': '2026-07-14',
            'shift_type': 'FULL_DAY',
        })
        assert response.status_code in (401, 403)

    def test_bad_date_format_returns_400(self, soc_user):
        client = APIClient()
        client.force_authenticate(user=soc_user['user'])
        response = client.post(PREVIEW_URL, {
            'start_date': '13-07-2026', 'end_date': '2026-07-14',
            'shift_type': 'FULL_DAY',
        })
        assert response.status_code == 400
