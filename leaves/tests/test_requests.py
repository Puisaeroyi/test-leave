"""
Tests for Leave Request API
"""
import pytest
from decimal import Decimal
from datetime import date, datetime, timedelta
from django.contrib.auth import get_user_model
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient
from freezegun import freeze_time
from organizations.models import Department, Entity, Location, WorkShift
from leaves.models import HolidayCalendar, LeaveCategory, LeaveBalance, LeaveRequest, PublicHoliday

User = get_user_model()


@pytest.fixture
def setup_user_with_balance():
    """Create a user with leave balance for testing"""
    entity = Entity.objects.create(entity_name='Test Entity', code='TEST')
    location = Location.objects.create(
        entity=entity,
        location_name='Test Location',
        city='Test City',
        country='Test Country',
        timezone='UTC'
    )
    department = Department.objects.create(
        entity=entity,
        location=location,
        department_name='Test Department',
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
    approver = User.objects.create_user(
        email='default-approver@example.com',
        password='ApproverPass123!',
        role=User.Role.MANAGER,
    )
    user.approver_1 = approver
    user.save(update_fields=['approver_1'])

    # Get or create leave balance (signal may have already created it)
    balance, _ = LeaveBalance.objects.get_or_create(
        user=user,
        year=2026,
        balance_type='VACATION',
        defaults={
            'allocated_hours': Decimal('96.00'),
            'used_hours': Decimal('0.00')
        }
    )

    # Create leave category
    category = LeaveCategory.objects.create(
        category_name='Annual Leave',
        code='ANNUAL',
        balance_bucket='VACATION',
    )

    return {
        'user': user,
        'balance': balance,
        'category': category,
        'department': department,
        'approver': approver,
    }


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

    def test_create_request_requires_at_least_one_approver(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        user.approver_1 = None
        user.approver_2 = None
        user.save(update_fields=['approver_1', 'approver_2'])
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-01-20',
            'end_date': '2026-01-20',
            'shift_type': 'FULL_DAY',
            'leave_category': str(category.id),
            'reason': 'Personal business',
        })

        assert response.status_code == 400
        assert response.data['error'] == (
            'Cannot submit leave request because no approver is assigned. Please contact HR.'
        )
        assert not LeaveRequest.objects.filter(user=user).exists()

    def test_leave_on_published_holiday_counts_as_normal_workday(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        calendar = HolidayCalendar.objects.create(
            name='US 2026',
            country_code='US',
            year=2026,
            entity=user.entity,
            status=HolidayCalendar.Status.PUBLISHED,
        )
        PublicHoliday.objects.create(
            calendar=calendar,
            entity=user.entity,
            holiday_name='Operations holiday',
            start_date=date(2026, 1, 20),
            end_date=date(2026, 1, 20),
            year=2026,
            status=PublicHoliday.Status.PUBLISHED,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-01-20',
            'end_date': '2026-01-20',
            'shift_type': 'FULL_DAY',
            'leave_category': str(category.id),
            'reason': 'Not working the holiday shift',
        })

        assert response.status_code == 201, response.data
        assert response.data['total_hours'] == 8.0

    def test_hr_cannot_view_leave_request_from_another_entity(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        other_entity = Entity.objects.create(entity_name='Other Entity', code='OTHER')
        hr = User.objects.create_user(
            email='other-entity-hr@example.com',
            password='Hr123!',
            role=User.Role.HR,
            entity=other_entity,
        )
        leave_request = LeaveRequest.objects.create(
            user=user,
            leave_category=category,
            start_date=date(2026, 1, 20),
            end_date=date(2026, 1, 20),
            shift_type=LeaveRequest.ShiftType.FULL_DAY,
            total_hours=Decimal('8.00'),
            status=LeaveRequest.Status.PENDING,
        )
        client = APIClient()
        client.force_authenticate(user=hr)

        response = client.get(f'/api/v1/leaves/requests/{leave_request.id}/')

        assert response.status_code == 403

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

    def test_hr_night_weekly_shift_skips_weekend_days(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        user.work_shift = WorkShift.objects.create(
            department=user.department,
            name='HR Night Weekdays',
            start_time='22:00',
            end_time='06:00',
            includes_weekends=False,
        )
        user.save(update_fields=['work_shift'])
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-07-10',
            'end_date': '2026-07-13',
            'shift_type': 'FULL_DAY',
            'leave_category': str(category.id),
            'reason': 'Family business',
        })

        assert response.status_code == 201, response.data
        assert response.data['total_hours'] == 16.0
        leave = LeaveRequest.objects.get(user=user, start_date=date(2026, 7, 10))
        assert leave.total_hours == Decimal('16.00')

    def test_soc_rotating_shift_uses_employee_cycle_anchor_and_off_days(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        user.department.holiday_requires_leave = True
        user.department.save(update_fields=['holiday_requires_leave'])
        user.work_shift = WorkShift.objects.create(
            department=user.department,
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
        user.shift_cycle_start_date = date(2026, 7, 11)
        user.save(update_fields=['work_shift', 'shift_cycle_start_date'])
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-07-13',
            'end_date': '2026-07-15',
            'shift_type': 'FULL_DAY',
            'leave_category': str(category.id),
            'reason': 'Family business',
        })

        assert response.status_code == 201, response.data
        assert response.data['total_hours'] == 16.0
        assert response.data['leave_breakdown'] == [
            {'date': '2026-07-13', 'shift_name': 'Night', 'start_time': '22:00', 'end_time': '06:00', 'hours': 8.0, 'reason': 'WORK'},
            {'date': '2026-07-14', 'shift_name': 'Off', 'start_time': None, 'end_time': None, 'hours': 0.0, 'reason': 'OFF'},
            {'date': '2026-07-15', 'shift_name': 'Morning', 'start_time': '06:00', 'end_time': '14:00', 'hours': 8.0, 'reason': 'WORK'},
        ]
        leave = LeaveRequest.objects.get(user=user, start_date=date(2026, 7, 13))
        assert leave.total_hours == Decimal('16.00')
        assert leave.leave_breakdown == response.data['leave_breakdown']

    def test_preview_soc_rotation_excludes_cycle_off_day(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        user.department.holiday_requires_leave = True
        user.department.save(update_fields=['holiday_requires_leave'])
        user.work_shift = WorkShift.objects.create(
            department=user.department,
            name='SOC Three On One Off',
            pattern_type=WorkShift.PatternType.ROTATING_CYCLE,
            start_time='06:00',
            end_time='14:00',
            includes_weekends=True,
            cycle_days=[
                {'name': 'Day 1', 'start_time': '06:00', 'end_time': '14:00', 'is_working': True},
                {'name': 'Day 2', 'start_time': '14:00', 'end_time': '22:00', 'is_working': True},
                {'name': 'Day 3', 'start_time': '22:00', 'end_time': '06:00', 'is_working': True},
                {'name': 'Off', 'is_working': False},
            ],
        )
        user.shift_cycle_start_date = date(2026, 7, 11)
        user.save(update_fields=['work_shift', 'shift_cycle_start_date'])
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/preview/', {
            'start_date': '2026-07-13',
            'end_date': '2026-07-15',
            'shift_type': 'FULL_DAY',
        }, format='json')

        assert response.status_code == 200, response.data
        assert response.data['total_hours'] == 16.0
        assert [row['reason'] for row in response.data['leave_breakdown']] == [
            'WORK', 'OFF', 'WORK',
        ]

    def test_preview_custom_hours_on_soc_cycle_off_day_is_zero(
        self, setup_user_with_balance
    ):
        user = setup_user_with_balance['user']
        user.work_shift = WorkShift.objects.create(
            department=user.department,
            name='SOC Three On One Off Custom',
            pattern_type=WorkShift.PatternType.ROTATING_CYCLE,
            start_time='06:00',
            end_time='14:00',
            includes_weekends=True,
            cycle_days=[
                {'name': 'Day 1', 'start_time': '06:00', 'end_time': '14:00', 'is_working': True},
                {'name': 'Day 2', 'start_time': '14:00', 'end_time': '22:00', 'is_working': True},
                {'name': 'Day 3', 'start_time': '22:00', 'end_time': '06:00', 'is_working': True},
                {'name': 'Off', 'is_working': False},
            ],
        )
        user.shift_cycle_start_date = date(2026, 7, 11)
        user.save(update_fields=['work_shift', 'shift_cycle_start_date'])
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/preview/', {
            'start_date': '2026-07-14',
            'end_date': '2026-07-14',
            'shift_type': 'CUSTOM_HOURS',
            'start_time': '06:00',
            'end_time': '10:00',
        }, format='json')

        assert response.status_code == 200, response.data
        assert response.data['total_hours'] == 0.0

    def test_preview_hr_vn_night_shift_excludes_weekends_and_vn_holidays(
        self, setup_user_with_balance
    ):
        user = setup_user_with_balance['user']
        user.location.country = 'Vietnam'
        user.location.save(update_fields=['country'])
        user.work_shift = WorkShift.objects.create(
            department=user.department,
            name='HR VN Night',
            start_time='22:00',
            end_time='06:00',
            includes_weekends=False,
        )
        user.save(update_fields=['work_shift'])
        calendar = HolidayCalendar.objects.create(
            name='VN 2026',
            country_code='VN',
            year=2026,
            entity=user.entity,
            status=HolidayCalendar.Status.PUBLISHED,
        )
        PublicHoliday.objects.create(
            calendar=calendar,
            entity=user.entity,
            holiday_name='VN Holiday',
            start_date=date(2026, 7, 13),
            end_date=date(2026, 7, 13),
            year=2026,
            status=PublicHoliday.Status.PUBLISHED,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/preview/', {
            'start_date': '2026-07-11',
            'end_date': '2026-07-14',
            'shift_type': 'FULL_DAY',
        }, format='json')

        assert response.status_code == 200, response.data
        assert response.data['total_hours'] == 8.0
        assert [row['reason'] for row in response.data['leave_breakdown']] == [
            'OFF', 'OFF', 'HOLIDAY', 'WORK',
        ]
        assert response.data['leave_breakdown'][-1]['start_time'] == '22:00'
        assert response.data['leave_breakdown'][-1]['end_time'] == '06:00'

    def test_preview_us_office_shift_excludes_weekends_and_us_holidays(
        self, setup_user_with_balance
    ):
        user = setup_user_with_balance['user']
        user.location.country = 'USA'
        user.location.save(update_fields=['country'])
        user.work_shift = WorkShift.objects.create(
            department=user.department,
            name='US Office',
            start_time='08:00',
            end_time='17:00',
            break_start_time='12:00',
            break_end_time='13:00',
            includes_weekends=False,
        )
        user.save(update_fields=['work_shift'])
        calendar = HolidayCalendar.objects.create(
            name='US 2026',
            country_code='US',
            year=2026,
            entity=user.entity,
            status=HolidayCalendar.Status.PUBLISHED,
        )
        PublicHoliday.objects.create(
            calendar=calendar,
            entity=user.entity,
            holiday_name='US Holiday',
            start_date=date(2026, 7, 13),
            end_date=date(2026, 7, 13),
            year=2026,
            status=PublicHoliday.Status.PUBLISHED,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/preview/', {
            'start_date': '2026-07-11',
            'end_date': '2026-07-14',
            'shift_type': 'FULL_DAY',
        }, format='json')

        assert response.status_code == 200, response.data
        assert response.data['total_hours'] == 8.0
        assert [row['reason'] for row in response.data['leave_breakdown']] == [
            'OFF', 'OFF', 'HOLIDAY', 'WORK',
        ]
        assert response.data['leave_breakdown'][-1]['start_time'] == '08:00'
        assert response.data['leave_breakdown'][-1]['end_time'] == '17:00'
        assert response.data['leave_breakdown'][-1]['break_start_time'] == '12:00'
        assert response.data['leave_breakdown'][-1]['break_end_time'] == '13:00'

    def test_preview_us_custom_hours_excludes_lunch_break(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        user.location.country = 'USA'
        user.location.save(update_fields=['country'])
        user.work_shift = WorkShift.objects.create(
            department=user.department,
            name='US Office Custom',
            start_time='08:00',
            end_time='17:00',
            break_start_time='12:00',
            break_end_time='13:00',
            includes_weekends=False,
        )
        user.save(update_fields=['work_shift'])
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/preview/', {
            'start_date': '2026-07-14',
            'end_date': '2026-07-14',
            'shift_type': 'CUSTOM_HOURS',
            'start_time': '11:00',
            'end_time': '14:00',
        }, format='json')

        assert response.status_code == 200, response.data
        assert response.data['total_hours'] == 2.0

    def test_create_request_rejects_zero_deductible_hours(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-01-24',
            'end_date': '2026-01-25',
            'shift_type': 'FULL_DAY',
            'leave_category': str(category.id),
            'reason': 'Weekend request',
        })

        assert response.status_code == 400
        assert response.data['error'] == (
            'No deductible working hours were found for the selected date range. '
            'Choose a scheduled working day that is not a weekend, public holiday, '
            'or cycle off day.'
        )
        assert not LeaveRequest.objects.filter(
            user=user,
            start_date=date(2026, 1, 24),
            end_date=date(2026, 1, 25),
        ).exists()

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

    def test_create_request_rejects_invalid_shift_type(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-01-20',
            'end_date': '2026-01-20',
            'shift_type': 'INVALID',
            'leave_category': str(category.id),
            'reason': 'Invalid shift type',
        })

        assert response.status_code == 400
        assert response.data['error'] == 'Invalid shift_type. Must be FULL_DAY or CUSTOM_HOURS'
        assert not LeaveRequest.objects.filter(user=user).exists()

    def test_create_custom_hours_on_next_calendar_day_of_shift(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-06-15',
            'end_date': '2026-06-15',
            'shift_type': 'CUSTOM_HOURS',
            'start_time': '02:00',
            'end_time': '06:00',
            'start_day_offset': 1,
            'end_day_offset': 1,
            'leave_category': str(category.id),
            'reason': 'Second half of night shift',
        })

        assert response.status_code == 201, response.data
        request = LeaveRequest.objects.get(id=response.data['id'])
        assert request.start_date == date(2026, 6, 15)
        assert request.start_day_offset == 1
        assert request.end_day_offset == 1
        assert request.total_hours == Decimal('4.00')

    def test_custom_hours_overlap_uses_actual_calendar_time(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        LeaveRequest.objects.create(
            user=user,
            leave_category=category,
            start_date=date(2026, 6, 15),
            end_date=date(2026, 6, 15),
            shift_type=LeaveRequest.ShiftType.CUSTOM_HOURS,
            start_time='02:00',
            end_time='06:00',
            start_day_offset=1,
            end_day_offset=1,
            total_hours=Decimal('4.00'),
            status=LeaveRequest.Status.PENDING,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-06-16',
            'end_date': '2026-06-16',
            'shift_type': 'CUSTOM_HOURS',
            'start_time': '03:00',
            'end_time': '05:00',
            'start_day_offset': 0,
            'end_day_offset': 0,
            'leave_category': str(category.id),
            'reason': 'Duplicate actual time',
        })

        assert response.status_code == 400
        assert 'overlapping custom-hours' in response.data['error']

    def test_non_overlapping_custom_hours_on_same_work_date_are_allowed(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        LeaveRequest.objects.create(
            user=user,
            leave_category=category,
            start_date=date(2026, 6, 15),
            end_date=date(2026, 6, 15),
            shift_type=LeaveRequest.ShiftType.CUSTOM_HOURS,
            start_time='09:00',
            end_time='11:00',
            total_hours=Decimal('2.00'),
            status=LeaveRequest.Status.PENDING,
        )
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/requests/', {
            'start_date': '2026-06-15',
            'end_date': '2026-06-15',
            'shift_type': 'CUSTOM_HOURS',
            'start_time': '13:00',
            'end_time': '15:00',
            'leave_category': str(category.id),
            'reason': 'Separate appointment',
        })

        assert response.status_code == 201, response.data

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

    def test_list_my_requests_ignores_invalid_year(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/leaves/requests/my/?year=abc')

        assert response.status_code == 200
        assert response.data == []

    def test_list_my_requests_preloads_serializer_relations(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        category = setup_user_with_balance['category']
        for day in range(20, 30):
            LeaveRequest.objects.create(
                user=user,
                leave_category=category,
                start_date=date(2026, 1, day),
                end_date=date(2026, 1, day),
                shift_type=LeaveRequest.ShiftType.FULL_DAY,
                total_hours=Decimal('8.00'),
                status=LeaveRequest.Status.PENDING,
                first_approver=user.approver_1,
            )
        client = APIClient()
        client.force_authenticate(user=user)

        with CaptureQueriesContext(connection) as queries:
            response = client.get('/api/v1/leaves/requests/my/')

        assert response.status_code == 200
        assert len(response.data) == 10
        assert len(queries) <= 7

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
        user.approver_1 = manager
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

    def test_final_approval_rechecks_remaining_balance(self, setup_user_with_balance):
        user = setup_user_with_balance['user']
        balance = setup_user_with_balance['balance']
        category = setup_user_with_balance['category']
        manager = User.objects.create_user(
            email='balance-manager@example.com',
            password='Manager123!',
            role=User.Role.MANAGER,
        )
        user.approver_1 = manager
        user.save(update_fields=['approver_1'])
        leave_request = LeaveRequest.objects.create(
            user=user,
            leave_category=category,
            start_date=date(2026, 1, 20),
            end_date=date(2026, 1, 20),
            shift_type=LeaveRequest.ShiftType.FULL_DAY,
            total_hours=Decimal('8.00'),
            status=LeaveRequest.Status.PENDING,
            first_approver=manager,
        )
        balance.used_hours = balance.allocated_hours
        balance.save(update_fields=['used_hours'])
        client = APIClient()
        client.force_authenticate(user=manager)

        response = client.post(f'/api/v1/leaves/requests/{leave_request.id}/approve/')

        assert response.status_code == 400
        assert 'Insufficient balance' in response.data['error']
        leave_request.refresh_from_db()
        assert leave_request.status == LeaveRequest.Status.PENDING

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
        user.approver_1 = hr
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
        user.approver_1 = manager
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
