"""Tests for business trip create/read/update with owner cutoff and audit."""

from datetime import date, timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

from core.models import AuditLog, Notification
from leaves.models import BusinessTrip
from organizations.models import Entity, Location, Department

User = get_user_model()


@pytest.fixture
def trip_setup(db):
    entity = Entity.objects.create(entity_name='Trip Co', code='TRIP')
    location = Location.objects.create(
        entity=entity,
        location_name='Office',
        city='Tokyo',
        country='Japan',
        timezone='Asia/Tokyo',
    )
    department = Department.objects.create(
        entity=entity, location=location, department_name='Ops', code='OPS',
    )
    employee = User.objects.create_user(
        email='trip-emp@example.com', password='Pass123!',
        entity=entity, location=location, department=department,
    )
    other = User.objects.create_user(
        email='trip-other@example.com', password='Pass123!',
        entity=entity, location=location, department=department,
    )
    future_start = date.today() + timedelta(days=10)
    trip = BusinessTrip.objects.create(
        user=employee,
        city='Osaka',
        country='Japan',
        start_date=future_start,
        end_date=future_start + timedelta(days=2),
        note='Client visit',
    )
    return {
        'employee': employee,
        'other': other,
        'trip': trip,
        'future_start': future_start,
    }


def _client(user):
    c = APIClient()
    c.force_authenticate(user=user)
    return c


def _version(trip):
    trip.refresh_from_db()
    return trip.updated_at.isoformat()


@pytest.mark.django_db
class TestBusinessTripPatch:
    def test_owner_can_patch_note(self, trip_setup):
        trip = trip_setup['trip']
        client = _client(trip_setup['employee'])
        resp = client.patch(
            f'/api/v1/leaves/business-trips/{trip.id}/',
            {
                'note': 'Updated note',
                'expected_updated_at': _version(trip),
            },
            format='json',
        )
        assert resp.status_code == 200
        trip.refresh_from_db()
        assert trip.note == 'Updated note'
        assert resp.data['can_edit'] is True
        assert AuditLog.objects.filter(
            entity_type='BusinessTrip', entity_id=trip.id, action='UPDATE'
        ).exists()
        assert Notification.objects.count() == 0

    def test_started_trip_locked(self, trip_setup):
        trip = trip_setup['trip']
        trip.start_date = date.today()
        trip.end_date = date.today() + timedelta(days=1)
        trip.save()
        client = _client(trip_setup['employee'])
        with patch('users.utils._today_for_user_location', return_value=date.today()):
            resp = client.patch(
                f'/api/v1/leaves/business-trips/{trip.id}/',
                {
                    'note': 'nope',
                    'expected_updated_at': _version(trip),
                },
                format='json',
            )
        assert resp.status_code == 409
        assert resp.data['code'] == 'edit_locked'

    def test_started_trip_cannot_bypass_with_future_start(self, trip_setup):
        trip = trip_setup['trip']
        trip.start_date = date.today() - timedelta(days=1)
        trip.end_date = date.today() + timedelta(days=1)
        trip.save()
        client = _client(trip_setup['employee'])
        future = date.today() + timedelta(days=20)
        with patch('users.utils._today_for_user_location', return_value=date.today()):
            resp = client.patch(
                f'/api/v1/leaves/business-trips/{trip.id}/',
                {
                    'start_date': future.isoformat(),
                    'end_date': (future + timedelta(days=1)).isoformat(),
                    'expected_updated_at': _version(trip),
                },
                format='json',
            )
        assert resp.status_code == 409

    def test_non_owner_404(self, trip_setup):
        trip = trip_setup['trip']
        client = _client(trip_setup['other'])
        resp = client.patch(
            f'/api/v1/leaves/business-trips/{trip.id}/',
            {'note': 'hack', 'expected_updated_at': _version(trip)},
            format='json',
        )
        assert resp.status_code == 404

    def test_missing_version_428(self, trip_setup):
        trip = trip_setup['trip']
        client = _client(trip_setup['employee'])
        resp = client.patch(
            f'/api/v1/leaves/business-trips/{trip.id}/',
            {'note': 'x'},
            format='json',
        )
        assert resp.status_code == 428

    def test_protected_user_field_rejected(self, trip_setup):
        trip = trip_setup['trip']
        client = _client(trip_setup['employee'])
        resp = client.patch(
            f'/api/v1/leaves/business-trips/{trip.id}/',
            {
                'user': str(trip_setup['other'].id),
                'note': 'x',
                'expected_updated_at': _version(trip),
            },
            format='json',
        )
        assert resp.status_code == 400
        trip.refresh_from_db()
        assert trip.user_id == trip_setup['employee'].id

    def test_noop_no_audit(self, trip_setup):
        trip = trip_setup['trip']
        client = _client(trip_setup['employee'])
        before = AuditLog.objects.filter(entity_type='BusinessTrip').count()
        resp = client.patch(
            f'/api/v1/leaves/business-trips/{trip.id}/',
            {
                'city': trip.city,
                'expected_updated_at': _version(trip),
            },
            format='json',
        )
        assert resp.status_code == 200
        assert AuditLog.objects.filter(entity_type='BusinessTrip').count() == before

    def test_list_includes_can_edit(self, trip_setup):
        client = _client(trip_setup['employee'])
        resp = client.get('/api/v1/leaves/business-trips/')
        assert resp.status_code == 200
        row = resp.data['results'][0]
        assert 'can_edit' in row
        assert row['can_edit'] is True

    def test_new_start_must_be_future(self, trip_setup):
        trip = trip_setup['trip']
        client = _client(trip_setup['employee'])
        today = date.today()
        with patch('users.utils.get_user_local_date', return_value=today):
            with patch('users.utils._today_for_user_location', return_value=today):
                resp = client.patch(
                    f'/api/v1/leaves/business-trips/{trip.id}/',
                    {
                        'start_date': today.isoformat(),
                        'end_date': (today + timedelta(days=1)).isoformat(),
                        'expected_updated_at': _version(trip),
                    },
                    format='json',
                )
        assert resp.status_code == 400
