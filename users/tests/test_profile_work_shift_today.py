from datetime import date, timedelta
from unittest.mock import patch

from django.test import TestCase

from organizations.models import Department, Entity, Location, WorkShift
from users.models import User
from users.utils import build_user_response


TODAY = date(2026, 6, 15)


class ProfileWorkShiftTodayTests(TestCase):
    def setUp(self):
        self.entity = Entity.objects.create(
            entity_name='Shift Test Company',
            code='SHIFT',
        )
        self.location = Location.objects.create(
            entity=self.entity,
            location_name='Operations Center',
            city='Ho Chi Minh City',
            country='Vietnam',
            timezone='Asia/Ho_Chi_Minh',
        )
        self.department = Department.objects.create(
            entity=self.entity,
            location=self.location,
            department_name='SOC',
            code='SOC',
        )
        self.rotating_shift = WorkShift.objects.create(
            department=self.department,
            name='SOC',
            pattern_type=WorkShift.PatternType.ROTATING_CYCLE,
            start_time='06:00',
            end_time='14:00',
            includes_weekends=True,
            cycle_days=[
                {'name': 'Morning', 'start_time': '06:00', 'end_time': '14:00', 'is_working': True},
                {'name': 'Off', 'is_working': False},
            ],
        )

    def make_user(self, **extra_fields):
        fields = {
            'email': f"profile-shift-{User.objects.count()}@example.com",
            'password': 'TestPass123!',
            'entity': self.entity,
            'location': self.location,
            'department': self.department,
        }
        fields.update(extra_fields)
        return User.objects.create_user(**fields)

    def test_working_day_returns_resolved_shift_for_today(self):
        user = self.make_user(
            work_shift=self.rotating_shift,
            shift_cycle_start_date=TODAY,
        )

        with patch('users.utils._today_for_user_location', return_value=TODAY):
            data = build_user_response(user)

        self.assertEqual(data['work_shift_today']['date'], TODAY.isoformat())
        self.assertEqual(data['work_shift_today']['shift_name'], 'Morning')
        self.assertTrue(data['work_shift_today']['is_working'])
        self.assertEqual(data['work_shift_today']['start_time'], '06:00')
        self.assertEqual(data['work_shift_today']['end_time'], '14:00')
        self.assertEqual(data['work_shift']['name'], 'SOC')

    def test_off_day_returns_non_working_payload(self):
        user = self.make_user(
            work_shift=self.rotating_shift,
            shift_cycle_start_date=TODAY - timedelta(days=1),
        )

        with patch('users.utils._today_for_user_location', return_value=TODAY):
            data = build_user_response(user)

        self.assertEqual(data['work_shift_today']['shift_name'], 'Off')
        self.assertFalse(data['work_shift_today']['is_working'])
        self.assertIsNone(data['work_shift_today']['start_time'])
        self.assertIsNone(data['work_shift_today']['end_time'])

    def test_rotating_shift_without_anchor_omits_today_payload(self):
        user = self.make_user()
        User.objects.filter(pk=user.pk).update(
            work_shift=self.rotating_shift,
            shift_cycle_start_date=None,
        )
        user.refresh_from_db()

        with patch('users.utils._today_for_user_location', return_value=TODAY):
            data = build_user_response(user)

        self.assertIn('work_shift', data)
        self.assertNotIn('work_shift_today', data)

    def test_malformed_cycle_data_omits_today_payload(self):
        user = self.make_user(
            work_shift=self.rotating_shift,
            shift_cycle_start_date=TODAY,
        )
        WorkShift.objects.filter(pk=self.rotating_shift.pk).update(cycle_days=['bad-data'])
        user.work_shift.refresh_from_db()

        with patch('users.utils._today_for_user_location', return_value=TODAY):
            data = build_user_response(user)

        self.assertIn('work_shift', data)
        self.assertNotIn('work_shift_today', data)

    def test_invalid_location_timezone_falls_back_without_error(self):
        user = self.make_user(
            work_shift=self.rotating_shift,
            shift_cycle_start_date=TODAY,
        )
        Location.objects.filter(pk=self.location.pk).update(timezone='Bad/Timezone')
        user.location.refresh_from_db()

        with patch('users.utils.dj_timezone.localdate', return_value=TODAY):
            data = build_user_response(user)

        self.assertEqual(data['work_shift_today']['date'], TODAY.isoformat())

    def test_user_without_work_shift_omits_shift_payloads(self):
        user = self.make_user()

        data = build_user_response(user)

        self.assertNotIn('work_shift', data)
        self.assertNotIn('work_shift_today', data)
