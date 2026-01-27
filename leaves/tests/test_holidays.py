"""
Tests for Public Holidays API
"""
import pytest
from datetime import date
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from organizations.models import Entity, Location
from leaves.models import PublicHoliday

User = get_user_model()


@pytest.fixture
def setup_holidays():
    """Create entity and holidays for testing"""
    entity = Entity.objects.create(name='Test Entity', code='TEST')
    location = Location.objects.create(
        entity=entity,
        name='Test Location',
        city='Test City',
        country='Test Country',
        timezone='UTC'
    )

    # Create user with entity
    user = User.objects.create_user(
        email='test@example.com',
        password='TestPass123!',
        entity=entity,
        location=location
    )

    # Create HR user
    hr_user = User.objects.create_user(
        email='hr@example.com',
        password='TestPass123!',
        role=User.Role.HR
    )

    # Create holidays
    h1 = PublicHoliday.objects.create(
        name='New Year',
        date=date(2026, 1, 1),
        year=2026,
        is_recurring=True,
        is_active=True
    )
    h2 = PublicHoliday.objects.create(
        name='Independence Day',
        date=date(2026, 7, 4),
        year=2026,
        entity=entity,
        is_active=True
    )

    return {
        'user': user,
        'hr_user': hr_user,
        'entity': entity,
        'location': location,
        'holidays': [h1, h2]
    }


@pytest.mark.django_db
class TestPublicHolidays:
    """Test public holiday endpoints"""

    def test_list_holidays(self, setup_holidays):
        """Test listing public holidays"""
        user = setup_holidays['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/leaves/holidays/')

        assert response.status_code == 200
        assert len(response.data) >= 2

    def test_list_holidays_by_year(self, setup_holidays):
        """Test listing holidays filtered by year"""
        user = setup_holidays['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get('/api/v1/leaves/holidays/?year=2026')

        assert response.status_code == 200
        assert all(h['year'] == 2026 for h in response.data)

    def test_get_holiday_detail(self, setup_holidays):
        """Test getting holiday detail"""
        user = setup_holidays['user']
        holiday = setup_holidays['holidays'][0]

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.get(f'/api/v1/leaves/holidays/{holiday.id}/')

        assert response.status_code == 200
        assert response.data['name'] == 'New Year'

    def test_create_holiday_hr(self, setup_holidays):
        """Test HR creating a holiday"""
        hr_user = setup_holidays['hr_user']

        client = APIClient()
        client.force_authenticate(user=hr_user)

        response = client.post('/api/v1/leaves/holidays/', {
            'name': 'Christmas',
            'date': '2026-12-25',
            'year': 2026,
            'is_recurring': True
        })

        assert response.status_code == 201
        assert response.data['name'] == 'Christmas'
        assert PublicHoliday.objects.filter(name='Christmas').exists()

    def test_create_holiday_employee_forbidden(self, setup_holidays):
        """Test that regular employees cannot create holidays"""
        user = setup_holidays['user']

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.post('/api/v1/leaves/holidays/', {
            'name': 'My Holiday',
            'date': '2026-06-15',
        })

        assert response.status_code == 403

    def test_update_holiday_hr(self, setup_holidays):
        """Test HR updating a holiday"""
        hr_user = setup_holidays['hr_user']
        holiday = setup_holidays['holidays'][0]

        client = APIClient()
        client.force_authenticate(user=hr_user)

        response = client.put(f'/api/v1/leaves/holidays/{holiday.id}/', {
            'name': 'New Year Day Updated'
        })

        assert response.status_code == 200
        assert response.data['name'] == 'New Year Day Updated'

    def test_delete_holiday_hr(self, setup_holidays):
        """Test HR deleting a holiday"""
        hr_user = setup_holidays['hr_user']
        holiday = setup_holidays['holidays'][0]

        client = APIClient()
        client.force_authenticate(user=hr_user)

        response = client.delete(f'/api/v1/leaves/holidays/{holiday.id}/')

        assert response.status_code == 204
        assert not PublicHoliday.objects.filter(id=holiday.id).exists()

    def test_delete_holiday_employee_forbidden(self, setup_holidays):
        """Test that regular employees cannot delete holidays"""
        user = setup_holidays['user']
        holiday = setup_holidays['holidays'][0]

        client = APIClient()
        client.force_authenticate(user=user)

        response = client.delete(f'/api/v1/leaves/holidays/{holiday.id}/')

        assert response.status_code == 403
